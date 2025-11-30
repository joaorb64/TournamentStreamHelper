"""
Utility functions for downloading things.
"""
import collections
import dataclasses
import datetime
import os
import sys
import threading

from pathlib import Path
from typing import Optional, Callable
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

from loguru import logger
from tqdm import tqdm
import requests

from qtpy.QtCore import *
from qtpy.QtWidgets import *

from ..Workers import Worker


def download_file(
        url,
        filename: Optional[str],
        desc: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        assume_size: Optional[int] = None,
        progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
        validating_event: Optional[threading.Event] = None,
        cancel_event: Optional[threading.Event] = None,
):
    if filename:
        basename = Path(filename).name
    else:
        basename = Path(urlparse(url).path).name

    if desc is None:
        desc = basename

    response = requests.get(
        url,
        allow_redirects=True,
        stream=True,
    )

    if response.status_code >= 400:
        logger.warning(f"Failed to download {desc} [status_code={response.status_code}]: {response.content.decode()}")
        return False

    content_length = None
    try:
        headerval = response.headers.get('Content-Length', None)
        if headerval is not None and int(headerval):
            content_length = int(headerval)
    except (TypeError, ValueError, AttributeError):
        logger.opt(exception=True).debug(f"Failed to parse content-length for file download. ({response.headers})")

    if content_length is None and assume_size is not None:
        content_length = assume_size

    block_size = 4096
    success = True
    logger.info(f"Downloading {desc}...")
    with NamedTemporaryFile(
        prefix=basename,
        suffix=".tmp",
        mode="wb",
        # Windows needs this specifically. We want the file
        # to be deleted when the context manager exits, but we need
        # to close the file and still be able to re-open it, since
        # windows won't let you open a file that still has a writeable
        # file descriptor open.
        delete=False,
    ) as tmp_file:
        try:
            has_stdout = (sys.__stdout__ is not None)
            if has_stdout:
                progress_bar = tqdm(
                        file=sys.__stdout__,
                        unit="B",
                        unit_scale=True,
                        total=content_length,
                        leave=True
                )
            else:
                progress_bar = NullProgressBar()

            try:
                downloaded = 0
                # Progress bar is helpful, but loggers have no concept of
                # tty ansi escape codes to reset the cursor position, so we
                # print directly to the console.
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    if progress_callback:
                        progress_callback(downloaded, content_length)

                    if cancel_event and cancel_event.is_set():
                        logger.info("Download cancelled by callback.")
                        return False

                    progress_bar.update(len(data))
                    tmp_file.write(data)
                progress_bar.total = progress_bar.n
            finally:
                progress_bar.close()

            tmp_file.close()

            if validator:
                # Test if downloaded JSON is valid
                logger.info(f"Validating {desc}")
                success = validator(tmp_file.name)

            # Remove old file, overwrite with new one
            if filename is not None:
                os.replace(tmp_file.name, filename)

            logger.info(f"{desc} download complete.")
            return success
        except Exception:
            logger.opt(exception=True).warning(f"{desc} download failure.")
            success = False
        finally:
            if os.path.exists(tmp_file.name):
                os.unlink(tmp_file.name)

        return success


class NullProgressBar:
    """
    This class does nothing, but you can call methods on it just fine.
    """
    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return lambda *args, **kwargs: None


@dataclasses.dataclass
class _DlTimingSample:
    num: int
    as_of: datetime.datetime

    @staticmethod
    def avg_throughput(samples: collections.deque["_DlTimingSample"]):
        if len(samples) <= 1:
            return 0

        s = samples[0]
        e = samples[-1]

        return (e.num - s.num) / (e.as_of - s.as_of).total_seconds()


def _format_bytes(n: int, dec=2) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.{dec}f} {unit}"
        n /= 1024
    return f"{n:.{dec}f} PB"


class DownloadDialog(QDialog):
    _MAX_DL_SAMPLES = 500
    _UPDATE_FREQUENCY_SECS = 0.5
    validating = Signal()

    def __init__(
            self,
            url: str,
            filename: Optional[str] = None,
            desc: Optional[str] = None,
            validator: Optional[Callable[[str], bool]] = None,
            assume_size: Optional[int] = None,
            parent=None
    ):
        super().__init__(parent)

        self.url=url
        self.filename=filename
        self.desc = filename or url if desc is None else desc
        self.validator=validator
        self.assume_size = assume_size

        self.setWindowTitle(f"TSH {desc} download")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.worker: Optional[Worker] = None
        self._errored = False

        # UI
        self._label = QLabel(f"Preparing download for {desc}...", self)
        self._progress = QProgressBar(self)
        self._progress.setRange(0, 0)  # unknown at first (indeterminate)
        self._last_update = datetime.datetime.fromtimestamp(0)

        self._close_button = QPushButton("Close", self)
        self._close_button.setEnabled(False)
        self._close_button.clicked.connect(self.close)

        # Optional cancel button (no actual cancellation logic wired in yet)
        self._cancel_button = QPushButton("Cancel", self)
        self._cancel_button.setEnabled(False)  # enable when you wire cancellation
        self._cancel_event: Optional[threading.Event] = None
        self._samples = collections.deque(maxlen=self._MAX_DL_SAMPLES)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch(1)
        btn_layout.addWidget(self._cancel_button)
        btn_layout.addWidget(self._close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)
        layout.addWidget(self._progress)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.resize(400, self.sizeHint().height())

    @Slot(int, int)
    def on_progress(self, num, total):
        self._samples.append(_DlTimingSample(num, datetime.datetime.now()))

        # We store the samples always, but we only update the UI periodically so that it doesn't
        # visually thrash the number and have weird UX.
        now = datetime.datetime.now()
        if (now - self._last_update).total_seconds() < self._UPDATE_FREQUENCY_SECS:
            return
        self._last_update = now

        if self._progress.maximum() != total:
            self._progress.setRange(0, total)
        self._progress.setValue(num)

        speed_str = _format_bytes(_DlTimingSample.avg_throughput(self._samples))
        self._label.setText(
            f"Downloading {self.desc} "
            f"{_format_bytes(self._progress.value(), 0)}"
            "/"
            f"{_format_bytes(self._progress.maximum(), 0)}"
            f" ({speed_str}/s)"
        )

    @Slot()
    def on_finished(self):
        # logger.info("dl dialog finished")

        if self._errored:
            self.reject()
        if self._cancel_event.is_set():
            self.reject()
        else:
            self.accept()

        self.hide()
        self.deleteLater()

    @Slot()
    def on_validating(self):
        # logger.info("dl dialog validating...")
        self._progress.setValue(self._progress.maximum())
        self._label.setText(f"Finishing up {self.desc} download...")
        self._cancel_button.setEnabled(False)

    @Slot()
    def on_error(self):
        self._errored = True

    @Slot()
    def on_cancel_clicked(self):
        # logger.info("dl dialog cancel clicked")
        if self._cancel_event:
            self._cancel_event.set()
        self.hide()
        self._cancel_button.setEnabled(False)

    def exec(
            self,
    ):

        def internal_validator(arg):
            self.validating.emit()
            return self.validator(arg)

        def worker_fn(progress_callback, cancel_event):
            self._cancel_event = cancel_event

            download_file(
                url=self.url,
                filename=self.filename,
                desc=self.desc,
                validator=internal_validator,
                assume_size=self.assume_size,
                progress_callback=progress_callback,
                cancel_event=cancel_event
            )

        self.worker = Worker(worker_fn)

        self._label.setText(f"Downloading {self.desc}...")
        self._progress.setRange(0, 0)  # indeterminate until we know total
        self._close_button.setEnabled(False)

        self.validating.connect(self.on_validating)
        self.worker.signals.progress.connect(self.on_progress)
        self.worker.signals.error.connect(self.on_error)
        self.worker.signals.finished.connect(self.on_finished)

        QThreadPool.globalInstance().start(self.worker)
        self._cancel_button.setEnabled(True)
        self._cancel_button.clicked.connect(self.on_cancel_clicked)

        super().exec()
