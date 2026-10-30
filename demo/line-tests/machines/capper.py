from busproof import Bus, Machine, Topics
from machines.state import State


class Capper(Machine):
    """The capping station: closes bottles, counts good and rejected ones."""

    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="capper", states=State)
        self.good_count = self.signal("good_count")
        self.reject_count = self.signal("reject_count")
        self.torque = self.signal("torque")
        self.cap_supply = self.signal("cap_supply")
        self.result = self.signal("result")
