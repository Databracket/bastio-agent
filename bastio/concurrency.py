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
    in case a stop event was triggered.

    This class takes two callbacks as keyword arguments to handle the cases where
    a task succeeds or fails, called ``success`` and ``failure`` respectively.

    Calling the :func:`Task.stop` method will signal the worker in the thread pool
    to stop execution and exit gracefully.
    """

    def __init__(self, target, success=lambda x: x, failure=lambda x: x, infinite=False,
            *args, **kwargs):
        self._id = random.getrandbits(128)
        self._kill_ev = threading.Event()
        self._infinite = infinite
        self.target = target
        self.success = success
        self.failure = failure
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        """Signal this task to stop as soon as possible."""
        self._infinite = False
        self._kill_ev.set()

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

    @property
    def args(self):
        return self._args

    @args.setter
    def args(self, value):
        if not isinstance(value, (tuple, list)):
            raise BastioTaskError("field args need to be either a list or a tuple")
        value = tuple(value)
        if self.infinite:
            self._args = (self._kill_ev,) + value
        else:
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
        self._running_tasks = []
        self._min_workers = min_workers + 1 # for the monitoring thread
        self._workers = 0
        self._avail_workers = 0
        self._countlck = threading.Lock()
        self._task_added = threading.Event()
        self._killev = threading.Event()
        self._all_died = threading.Event()
        self.add_worker(self._min_workers)
        mt = Task(target=self.__volume_monitor, infinite=True)
        self.run(mt)

    def run(self, task):
        """Start a task.

        :param task:
            A task to be executed by a worker.
        :type task:
            :class:`Task`
        :returns:
            The task that was passed to this method.
        """
        self._task_added.set()
        self._tasks.put(task)
        return task

    def add_worker(self, num=1):
        """Add worker(s) to the thread pool.

        :param num:
            The number of workers to add to the pool.
        :type num:
            int
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
            int
        """
        for x in range(int(num)):
            self._tasks.put("exit")

    def remove_all_workers(self, wait=None):
        """Remove all workers from the pool.

        Remove all active workers from the pool and wait ``wait`` seconds
        until last worker ends, or wait forever if ``wait`` is None. This
        action will also signal all running tasks to stop as soon as possible.

        :param wait:
            Number of seconds to wait or None to wait forever.
        :type wait:
            float
        """
        self._killev.set()
        self.remove_worker(self._workers)
        self._task_added.set()
        for task in self._running_tasks:
            task.stop()
        self._all_died.wait(wait)
        self._killev.clear()

    def __volume_monitor(self, kill_ev):
        while not kill_ev.is_set():
            with self._countlck:
                if self._workers < self._min_workers:
                    self.add_worker(self._min_workers - self._workers)
                if self._avail_workers < self._min_workers:
                    self.add_worker(round(abs(self._workers - self._avail_workers) / 2.0))
            self._task_added.wait(5.0)
            self._task_added.clear()

    def __worker(self):
        with self._countlck:
            self._workers += 1
            self._avail_workers += 1
            self._all_died.clear()
        while not self._killev.is_set(): # Main thread body
            try:
                task = self._tasks.get(timeout=1.0)
            except queue.Empty:
                # Waited for too long
                break
            if task == 'exit': # "exit" is a sentinel task to kill the worker
                break

            with self._countlck:
                self._avail_workers -= 1

            # Execute target function here
            self._running_tasks.append(task)
            try:
                ret = task.target(*task.args, **task.kwargs)
                if task.success:
                    task.success(ret)
            except Exception as ex:
                if task.failure:
                    try:
                        task.failure(Failure())
                    except Exception:
                        msg = 'failure callback raised an error on task ({})'.format(task.id)
                        self._logger.critical(msg, exc_info=True)
                else:
                    msg = "unhandled error occurred on task ({}): {}".format(
                            task.id, ex.message)
                    self._logger.critical(msg, exc_info=True)
            self._running_tasks.remove(task)

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

