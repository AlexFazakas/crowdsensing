"""
A module simulating a device using multiple threads to
collect and parse data imitating a crowdsense environment.
"""

from threading import Thread

import constants
from synchronize import Synchronize
from task import Task
from thread_pool import ThreadPool


class Device(object):
    """
    Class that represents a device.
    """

    def __init__(self, device_id, sensor_data, supervisor):
        """
        Constructor.

        @type device_id: Integer
        @param device_id: the unique id of this node; between 0 and N-1

        @type sensor_data: List of (Integer, Float)
        @param sensor_data: a list containing (location, data)
                                    as measured by this device

        @type supervisor: Supervisor
        @param supervisor: the testing infrastructure's
                                     control and validation component
        """
        self.device_id = device_id
        self.sensor_data = sensor_data
        self.supervisor = supervisor
        self.scripts = []

        self.sync = Synchronize()
        self.thread_pool = ThreadPool(constants.NUMBER_OF_THREADS, self)

        self.thread = DeviceThread(self)
        self.thread.start()

    def __str__(self):
        """
        Pretty prints this device.

        @rtype: String
        @return: a string containing the id of this device
        """
        return "Device %d" % self.device_id

    def setup_devices(self, devices):
        """
        Setup the devices before simulation begins.

        @type devices: List of Device
        @param devices: list containing all devices
        """
        if self.device_id == 0:
            self.sync.initialize_location_semaphores()
            self.sync.initialize_barrier(len(devices))
            for device in devices:
                device.sync.barrier = self.sync.barrier
                device.set_location_semaphores(self.sync.location_semaphores)

    def add_task(self, task):
        """
        Add a task in the worker pool
        """
        self.thread_pool.add_task(task)

    def assign_script(self, script, location):
        """
        Provide a script for the device to execute.

        @type script: Script
        @param script: the script to execute from now on at each timepoint;
                        None if the current timepoint has ended

        @type location: Integer
        @param location: the location for which the script is interested in
        """
        if script:
            self.scripts.append((script, location))

    def get_data(self, location):
        """
        Returns the pollution value this device has for the given location.

        @type location: Integer
        @param location: a location for which obtain the data

        @rtype: Float
        @return: the pollution value
        """
        if location in self.sensor_data:
            return self.sensor_data[location]
        return None

    def set_data(self, location, data):
        """
        Sets the pollution value stored by this device for the given location.

        @type location: Integer
        @param location: a location for which to set the data

        @type data: Float
        @param data: the pollution value
        """
        if location in self.sensor_data:
            self.sensor_data[location] = data

    def shutdown(self):
        """
        Instructs the device to shutdown (terminate all threads). This method
        is invoked by the tester. This method must block until all the threads
        started by this device terminate.
        """
        self.thread.join()

    def set_location_semaphores(self, location_semaphores):
        """
        A wrapper function for setting the list of location semaphores
        since setting it as we usually do took more than 79 chars per line. :(
        @type location_semaphores: List of Semaphore objects
        @param location_semaphores: A list of Semaphore objects we use to
                                    make sure multiple devices are not
                                    accessing the same data concurrently.
        """
        self.sync.location_semaphores = location_semaphores


class DeviceThread(Thread):
    """
    Class that implements the device's worker thread.
    """

    def __init__(self, device):
        """
        Constructor.

        @type device: Device
        @param device: the device which owns this thread
        """
        Thread.__init__(self, name="Device Thread %d" % device.device_id)
        self.device = device

    def run(self):
        while True:
            neighbours = self.device.supervisor.get_neighbours()
            if neighbours is None:
                self.device.thread_pool.join_threads()
                break

            self.device.sync.barrier.wait()

            for (script, location) in self.device.scripts:
                self.device.add_task(Task(neighbours, script, location))

            self.device.sync.barrier.wait()
