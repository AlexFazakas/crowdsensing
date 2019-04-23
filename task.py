"""
A module representing a wrap for the information we need
when working with a script on a given device.
"""

class Task:
    """
    Wrapper class for the information a thread needs while working.
    """
    def __init__(self, list_of_neighbours=None, script=None, location=None):
        """
        Constructor

        @type list_of_neighbours: List of Device
        @param list_of_neighbours: List of Device currently in the same area
                                   as the thread's master.

        @type script: Script
        @param script: Script to be run on the data

        @type location: Integer
        @param location: The location the data and script are for.
        """
        self.list_of_neighbours = list_of_neighbours
        self.script = script
        self.location = location
