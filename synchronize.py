""" This module provides synchronization elements for the devices. """

from threading import Semaphore, Lock
import constants


class ReusableBarrier:
    """
    Class implementing a reentrable barrier using semaphores.
    """

    def __init__(self, num_threads):
        """
        Constructor.

        @type num_threads: Integer
        @param num_threads: Number of threads using the barrier

        """
        self.num_threads = num_threads
        self.count_threads1 = self.num_threads
        self.count_threads2 = self.num_threads
        self.counter_lock = Lock()
        self.threads_sem1 = Semaphore(0)
        self.threads_sem2 = Semaphore(0)

    def wait(self):
        """
        Wait for both phases to complete.
        """
        self.phase1()
        self.phase2()

    def phase1(self):
        """
        Phase one of threads accessing the lock.
        """
        with self.counter_lock:
            self.count_threads1 -= 1
            if self.count_threads1 == 0:
                for _ in range(self.num_threads):
                    self.threads_sem1.release()
                self.count_threads1 = self.num_threads

        self.threads_sem1.acquire()

    def phase2(self):
        """
        Phase two of threads accessing the lock.
        """
        with self.counter_lock:
            self.count_threads2 -= 1
            if self.count_threads2 == 0:
                for _ in range(self.num_threads):
                    self.threads_sem2.release()
                self.count_threads2 = self.num_threads

        self.threads_sem2.acquire()


class Synchronize:
    """
    Class wrapping all synchronization means needed for devices.
    """
    def __init__(self):
        """
        Constructor.

        @type barrier: ReusableBarrierSem
        @param num_threads: Barrier used for waiting on all threads

        @type location_semaphores: List of Semaphore
        @param location_semaphores: List of Semaphore disallowing multiple
                                    accesses to data on the same location.

        """
        self.barrier = None
        self.location_semaphores = []

    def initialize_location_semaphores(self):
        """
        Method which initializes the list of semaphores. The largest test has
        a total of 24 locations, so that's how many semaphores we're using,
        since we can't know how many of them are beforehand.
        """
        for _ in range(constants.NUMBER_OF_POSSIBLE_LOCATIONS):
            self.location_semaphores.append(Semaphore())

    def initialize_barrier(self, number_of_threads):
        """
        Method which initializes the barrier to the number of threads that
        need to be synced at once (which, in our case, is the number of
        threads the ThreadPool class is working with)

        @type number_of_threads: Integer
        @param number_of_threads: The number of threads using the barrier.
        """
        self.barrier = ReusableBarrier(number_of_threads)
