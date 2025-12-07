
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from qtpy.QtCore import *

from datetime import datetime
import time
import traceback
import sys
from loguru import logger
import threading


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        `tuple` (exctype, value, traceback.format_exc() )

    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(int, int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = lambda n, t: self.signals.progress.emit(n, t)

        # Cancellation event
        self.cancel_event = threading.Event()
        self.kwargs['cancel_event'] = self.cancel_event

        self.completed = False
        self.result = None

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            self.result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(traceback.format_exc())
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # Return the result of the processing
            self.signals.result.emit(self.result)
        finally:
            if self.signals.finished:
                self.signals.finished.emit()  # Done

            # self.completed is guaranteed to not cause a race condition self.result if checked first.
            self.completed = True

    def cancel(self):
        '''
        Set the cancel event to indicate that the task should be cancelled.
        '''
        self.cancel_event.set()

    @staticmethod
    def wait_for_all(workers, timeout=None):
        """
        Wait for a collection of workers to complete.

        :returns: True if the workers complete, false if a timeout is set and exceeded.
        """

        start_time = datetime.now()

        def is_timed_out():
            nonlocal start_time
            if timeout is None:
                return False
            else:
                return (datetime.now() - start_time).total_seconds() > timeout

        while not is_timed_out():
            if all(w.completed for w in workers):
                return True

            time.sleep(0.1)

        return False
