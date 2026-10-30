from busproof import Bus, Machine, Topics
from machines.state import State


class Filler(Machine):
    """The filling station: fills each bottle from its tank."""

    def __init__(self, bus: Bus, topics: Topics):
        super().__init__(bus, topics, name="filler", states=State)
        self.online = self.signal("online")
        self.filled_count = self.signal("filled_count")
        self.fill_level = self.signal("fill_level")
        self.tank_level = self.signal("tank_level")
        self.bottle_supply = self.signal("bottle_supply")
