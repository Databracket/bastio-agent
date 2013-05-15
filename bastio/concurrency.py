# Copyright 2013 Databracket LLC
# See LICENSE file for details.

__author__ = "Amr Ali"
__copyright__ = "Copyright 2013 Databracket LLC"
__license__ = "GPLv3+"

"""
:module: bastio.concurrency
:synopsis: Concurrency utilities.
:author: Amr Ali <amr@databracket.com>

Concurrency
-----------
.. autoclass:: Failure
    :members:

.. autoclass:: Task
    :members:

.. autoclass:: ThreadPool
    :members:

.. autoclass:: GlobalThreadPool
    :inherited-members:
"""

import sys
import random
import hashlib
import threading
import Queue as queue

from bastio.mixin import KindSingletonMeta, public
from bastio.excepts import BastioTaskError
from bastio.configs import GlobalConfigStore
from bastio.log import Logger

@public
class Failure(object):
    """A class to wrap an exception info to pass to the failure callback registered
    on a task to handle it.

    This class must only be instantiated from under an ``except`` clause.
    """

    def __init__(self):
        ex, msg, tb = sys.exc_info()
        self._exception = ex
        self._message = msg
        self._traceback = tb

    @property
    def exception(self):
        return self._exception

    @property
    def message(self):
        return self._message

    @property
    def traceback(self):
        return self._traceback

@public
class Task(object):
    """A class to describe a task to be used by the thread pool.

    An infinite or a blocking task will have to take a kill :class:`threading.Event`
    as the first argument to the function to be able to end operations gracefully
    in case a kill-all workers event was triggered.

    This class takes two callbacks as keyword arguments to handle the cases where
    a task succeeds or fails, called ``success`` and ``failure`` respectively.
    """

    def __init__(self, target, success=None, failure=None, infinite=False,
            *args, **kwargs):
        token = hex(random.getrandbits(128)).strip('0xL').rjust(128 / 4, '0')
        self._id = hashlib.sha1(token.decode('hex')).hexdigest()
        self._target = None
        self._success = None
        self._failure = None
        self._infinite = None
        self._args = None
        self._kwargs = None
        self.target = target
        self.success = success
        self.failure = failure
        self.infinite = infinite
        self.args = args
        self.kwargs = kwargs

    @property
    def id(self):
        return self._id

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        if not callable(value):
            raise BastioTaskError("field target need to be a callable")
        self._target = value

    @property
    def success(self):
        return self._success

    @success.setter
    def success(self, value):
        if not callable(value):
            raise BastioTaskError("field success need to be a callable")
        self._success = value

    @property
    def failure(self):
        return self._failure

    @failure.setter
    def failure(self, value):
        if not callable(value):
            raise BastioTaskError("field failure need to be a callable")
        self._failure = value

    @property
    def infinite(self):
        return self._infinite

    @infinite.setter
    def infinite(self, value):
        self._infinite = bool(value)

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if not (isinstance(value, list) or isinstance(value, tuple)):
            raise BastioTaskError("field args need to be either a list or a tuple")
        self._args = value

    @property
    def kwargs(self):
        return self._kwargs

    @kwargs.setter
    def kwargs(self, value):
        if not isinstance(value, dict):
            raise BastioTaskError("field kwargs need to be a dict")
        self._kwargs = value

@public
class ThreadPool(object):
    """An adaptive thread pool.

    This thread pool adapts to the threads consumption rate by making sure that
    the available number of workers to process tasks is always above the minimum
    number of workers that should be always available.
    """

    ThreadFactory = threading.Thread

    def __init__(self, min_workers = 2):
        stacksize = GlobalConfigStore().stacksize
        threading.stack_size(stacksize * 1024)
        self._logger = Logger()
        self._tasks = queue.Queue()
        self._min_workers = min_workers
        self._workers = 0
        self._avail_workers = 0
        self._countlck = threading.Lock()
        self._killev = threading.Event()
        self._all_died = threading.Event()
        self.add_worker(self._min_workers)

    def run(self, task):
        """Start a task.

        :param task:
            A task to be executed by a worker.
        :type task:
            :class:`Task`
        :returns:
            The task ID of type ``str``
        """
        # If a task should run indefinitely it will get passed
        # a reference to the kill event to check on.
        if task.infinite:
            task.args = (self._killev,) + task.args
        self._tasks.put(task)
        if self._workers < self._min_workers:
            self.add_worker(self._min_workers - self._workers)
        if self._avail_workers < self._min_workers:
            self.add_worker(round(self._min_workers / 2.0))
        if self._avail_workers > self._min_workers:
            self.remove_worker(self._avail_workers - self._min_workers)
        return task.id

    def add_worker(self, num=1):
        """Add worker(s) to the thread pool.

        :param num:
            The number of workers to add to the pool.
        :type num:
            ``int``
        """
        for x in range(int(num)):
            t = self.ThreadFactory(target=self.__worker)
            t.setDaemon(True)
            t.start()

    def remove_worker(self, num=1):
        """Remove worker(s) from the thread pool.

        :param num:
            The number of workers to remove from the pool.
        :type num:
            ``int``
        """
        for x in range(int(num)):
            self._tasks.put("exit")

    def remove_all_workers(self, wait=None):
        """Remove all workers from the pool.

        Remove all active workers from the pool and wait ``wait`` seconds
        until last worker ends, or wait forever if ``wait`` is None.

        :param wait:
            Number of seconds to wait or None to wait forever.
        :type wait:
            ``int``
        """
        self._killev.set()
        self.remove_worker(self._workers)
        self._all_died.wait(wait)
        self._killev.clear()

    def __worker(self):
        with self._countlck:
            self._workers += 1
            self._avail_workers += 1
            self._all_died.clear()
        while not self._killev.is_set(): # Main thread body
            task = self._tasks.get()
            if task == 'exit': # "exit" is a sentinel task to kill the thread
                break

            with self._countlck:
                self._avail_workers -= 1

            # Execute target function here
            try:
                ret = task.target(*task.args, **task.kwargs)
                if task.success:
                    task.success(ret)
            except Exception as ex:
                if task.failure:
                    task.failure(Failure())
                else:
                    msg = "error occurred in thread (%s): %s" % (task.id, ex.message)
                    self._logger.critical(msg, exc_info=True)

            if task.infinite:
                self._tasks.put(task)
            with self._countlck:
                self._avail_workers += 1
        with self._countlck:
            self._workers -= 1
            self._avail_workers -= 1
            if not self._workers:
                self._all_died.set()

@public
class GlobalThreadPool(ThreadPool):
    """A singleton of :class:`bastio.concurrency.ThreadPool`."""
    __metaclass__ = KindSingletonMeta

