from busproof import Bus, Machine, Topics
from machines.state import State


class Scu(Machine):
    """The central unit of the line. Its state is a claim, to be compared with the machines."""

    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="scu", states=State)
        self.online = self.signal("online")
        self.in_transit = self.signal("in_transit")
        self.lost = self.signal("lost")
        self.faulted_machine = self.signal("faulted_machine")
