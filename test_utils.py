import threading
import traceback
from unittest import TestCase

import sys


class CountDownLatch(object):
    def __init__(self, count=1):
        self.__count = count
        self.lock = threading.Condition()

    def count_down(self):
        self.lock.acquire()
        self.__count -= 1
        if self.__count == 0:
            self.lock.notifyAll()
        self.lock.release()

    def await(self, timeout_in_millis=None):
        ret = True
        self.lock.acquire()
        if self.__count > 0:
            if timeout_in_millis is None:
                self.lock.wait()
            else:
                self.lock.wait(timeout_in_millis / 1000.0)
                if self.__count > 0:
                    ret = False
        self.lock.release()
        return ret


class ConcurrentTestCase(TestCase):
    def assertConcurrent(self, test_name, task_list, timeout_in_seconds):
        """
        :param test_name:
        :type test_name: str
        :param task_list:
        :type task_list: list of callable
        :param timeout_in_seconds:
        :type timeout_in_seconds: int
        """
        thread_count = len(task_list)
        exception_lock = threading.Lock()
        exception_list = []
        all_threads_ready = CountDownLatch(thread_count)
        run_threads = CountDownLatch(1)
        all_threads_done = CountDownLatch(thread_count)

        class TaskThread(threading.Thread):
            def __init__(self, task):
                threading.Thread.__init__(self)
                self.task = task

            def run(self):
                all_threads_ready.count_down()
                run_threads.await()
                try:
                    self.task()
                except Exception as e:
                    exception_lock.acquire()
                    exception_list.append(
                        '\n\n========================================================================\n' +
                        traceback.format_exc())
                    exception_lock.release()
                all_threads_done.count_down()

        for task in task_list:
            TaskThread(task).start()
        self.assertTrue(all_threads_ready.await(thread_count * 10), 'Timeout initializing threads!')
        run_threads.count_down()
        self.assertTrue(all_threads_done.await(timeout_in_seconds * 1000),
                        test_name + ' timeout! More than ' + str(timeout_in_seconds) + ' seconds')
        self.assertTrue(len(exception_list) == 0,
                        test_name + ' failed with following exception(s):' + '\n\n'.join(exception_list))
