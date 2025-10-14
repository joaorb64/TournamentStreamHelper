"""
Utility functions for downloading things.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Callable
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper
from urllib.parse import urlparse

import orjson
from loguru import logger
from tqdm import tqdm
import requests


def download_file(
        url,
        filename: Optional[str],
        desc: Optional[str] = None,
        validator: Optional[Callable[[str], bool]] = None,
        assume_size: Optional[int] = None
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
            progress_bar = tqdm(
                    # os.devnull is cross-platform, although windows' mechanism
                    # is not called /dev/null per se
                    file=(sys.__stdout__ if has_stdout else os.devnull),
                    unit="B",
                    unit_scale=True,
                    total=content_length,
                    leave=True
            )
            try:
                # Progress bar is helpful, but loggers have no concept of
                # tty ansi escape codes to reset the cursor position, so we
                # print directly to the console.
                for data in response.iter_content(block_size):
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
            return True
        except Exception:
            logger.opt(exception=True).warning(f"{desc} download failure.")
            success = False
        finally:
            os.unlink(tmp_file.name)

        return success



