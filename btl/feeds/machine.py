import math
from . import const

class Machine(object):
    def __init__(self,
                 label='Machine',
                 max_power=2,          # in kW
                 min_rpm=3000,         # RPM
                 max_rpm=60000,        # RPM
                 peak_torque_rpm=None, # RPM
                 min_feed=1,           # mm/min
                 max_feed=2000):       # mm/min
        self.label = label
        self.max_power = max_power
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.peak_torque_rpm = peak_torque_rpm if peak_torque_rpm else max_rpm/3 # RPM at which we reach peak Torque
        self.min_feed = min_feed
        self.max_feed = max_feed

        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        self.max_torque = self.max_power*9548.8/self.peak_torque_rpm

    def validate(self):
        if not self.label:
            raise AttributeError(f"Machine name is required")
        if self.peak_torque_rpm > self.max_rpm:
            raise AttributeError(f"Peak Torque RPM {self.peak_torque_rpm} must be less than max RPM {self.max_rpm}")

    def get_torque_at_rpm(self, rpm):
        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        return min(self.max_torque, self.max_torque/self.peak_torque_rpm*rpm)

    def set_label(self, label):
        self.label = label

    def set_max_power(self, power):
        self.max_power = power

    def set_min_rpm(self, min_rpm):
        self.min_rpm = min_rpm

    def set_max_rpm(self, max_rpm):
        self.max_rpm = max_rpm

    def set_min_feed(self, min_feed):
        self.min_feed = min_feed

    def set_max_feed(self, max_feed):
        self.max_feed = max_feed

    def set_peak_torque_rpm(self, peak_torque_rpm):
        self.peak_torque_rpm = peak_torque_rpm

    def set_max_torque(self, max_torque):
        self.max_torque = max_torque

    def dump(self):
        print(f"Machine {self.label}:")
        print(f"  Max power: {self.max_power} kW")
        print(f"  RPM: {self.min_rpm} rpm - {self.max_rpm} rpm")
        print(f"  Feed: {self.min_feed} mm/min - {self.max_feed} mm/min")
        print(f"  Peak torque: {self.max_torque} Nm at {self.peak_torque_rpm} rpm")
