import math
from . import const

class Machine(object):
    def __init__(self,
                 max_power=2,          # in kW
                 min_rpm=3000,         # RPM
                 max_rpm=60000,        # RPM
                 peak_torque_rpm=None, # RPM
                 max_feed=2000):       # mm/min
        self.max_power = max_power # in HP for now
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.peak_torque_rpm = peak_torque_rpm if peak_torque_rpm else max_rpm*0.33 # RPM at which we reach peak Torque
        self.max_feed = max_feed

        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        self.max_torque = self.max_power*9548.8/self.peak_torque_rpm

    def validate(self):
        if self.peak_torque_rpm > self.max_rpm:
            raise AttributeError(f"Peak Torque RPM {self.peak_torque_rpm} must be less than max RPM {self.max_rpm}")

    def get_torque_at_rpm(self, rpm):
        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        return min(self.max_torque, self.max_torque/self.peak_torque_rpm*rpm)
