from busproof import Bus, Machine, Topics
from machines.state import State


class Inspector(Machine):
    """The inspection station at the end of the line: passes the good bottles, rejects the rest."""

    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="inspector", states=State)
        self.pass_count = self.signal("pass_count")
        self.reject_count = self.signal("reject_count")
        self.last_fill_level = self.signal("last_fill_level")
