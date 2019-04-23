"""
A module implementing a pool of threads, each pool
using 8 working threads.
"""
import Queue
from threading import Thread
from task import Task


class ThreadPool:
    """
    Class implementing a pool of 8 threads using a blocking Queue.
    """

    def __init__(self, number_of_threads, master):
        """
        Constructor

        @type number_of_threads: Integer
        @param number_of_threads: Number of threads in the pool

        @type master: Device
        @param master: The device this pool belongs to
        """
        self.number_of_threads = number_of_threads
        self.list_of_threads = []
        self.list_of_tasks = Queue.Queue()
        self.master = master
        self.start_threads()

    def start_threads(self):
        """
        A function which creates number_of_threads threads and starts
        all of them.
        """
        for i in range(self.number_of_threads):
            self.list_of_threads.append(MyThread(self.list_of_tasks,
                                                 self.master))
        for i in range(self.number_of_threads):
            self.list_of_threads[i].start()

    def add_task(self, task):
        """
        Wrapper function for adding a task to the task queue.

        @type task: Task
        @param task: The task which needs to be performed, containing
        all of the necessary data for the thread.
        """
        self.list_of_tasks.put(task)

    def join_threads(self):
        """
        Method which stops all threads by sending them an empty task and
        then waits for them to finish working.
        Also joins the queue.
        """
        for i in range(self.number_of_threads):
            self.add_task(Task())

        for i in range(self.number_of_threads - 1):
            self.list_of_threads[i].join()
            self.list_of_tasks.join()


class MyThread(Thread):
    """
    Class representing the thread doing all the hard work.
    """

    def __init__(self, list_of_tasks, master):
        """
        Constructor

        @type list_of_tasks: Queue of Task
        @param list_of_tasks: Queue of Task which the threads poll from
                              in order to synchronously work together.
        """
        Thread.__init__(self)
        self.master = master
        self.list_of_tasks = list_of_tasks

    def get_semaphore_for_location(self, location):
        """
        Wrapper function for fetching a semaphore for a specific location, as
        it would've otherwise gotten past 79 chars per line. :(

        @type location: Integer
        @param location: The location whose semaphore we want to fetch.

        Returns the requested semaphore.
        """
        return self.master.sync.location_semaphores[location]

    def get_script_data(self, task):
        """
        Method for getting all the data together in a list for a
        specific task by quering neighbours and then itself.

        @type task: Task
        @param task: The specific task we need data for.

        Returns a list of Integers, containing the data.
        """
        script_data = []
        for device in task.list_of_neighbours:
            data = device.get_data(task.location)
            if data:
                script_data.append(data)
        data = self.master.get_data(task.location)

        if data:
            script_data.append(data)
        return script_data

    def update_data_on_neighbours(self, task, new_data):
        """
        Function which updates data for a given location on all neighbours
        and itself. Easier to use task here rather than 2 parameters.

        @type task: Task
        @param task: The Task encapsulating the data we need

        @type new_data: Integer
        @param new_data: The new data we need to have for a specific location
        """
        for device in task.list_of_neighbours:
            device.set_data(task.location, new_data)
        self.master.set_data(task.location, new_data)

    def run(self):
        """
        Overriding the run function from Thread.

        While we're not done yet, fetch a task. If the task is
        empty, we're done here. Otherwise, try to acquire the
        semaphore for a specific location, fetch the data we need,
        compute the new value and update it on all neighbours.
        Release the semaphore and the queue.
        """
        while True:
            task = self.list_of_tasks.get()
            if task.script is None:
                self.list_of_tasks.task_done()
                break

            location_semaphore = self.get_semaphore_for_location(task.location)
            location_semaphore.acquire()
            script_data = self.get_script_data(task)

            if script_data:
                result = task.script.run(script_data)
                self.update_data_on_neighbours(task, result)
            location_semaphore.release()
            self.list_of_tasks.task_done()
