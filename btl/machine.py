import math
import uuid
from . import const
from .params import Param, IntParam, FloatParam

class Machine(object):
    def __init__(self,
                 label='Machine',
                 max_power=2,          # FloatParam or kW (float)
                 min_rpm=3000,         # IntParam or RPM (int)
                 max_rpm=60000,        # IntParam or RPM (int)
                 max_torque=None,      # FloatParam or Nm (float)
                 peak_torque_rpm=None, # IntParam or RPM (int)
                 min_feed=1,           # FloatParam or mm/min (float)
                 max_feed=2000,        # FloatParam or mm/min (float)
                 id=None):
        self.id = id or str(uuid.uuid1())
        self.label = label
        self.max_power = FloatParam.from_value('max_power', max_power, 'kW')
        self.min_rpm = IntParam.from_value('min_rpm', min_rpm)
        self.max_rpm = IntParam.from_value('max_rpm', max_rpm)
        ptr = peak_torque_rpm or self.max_rpm.v/3
        self.peak_torque_rpm = IntParam.from_value('peak_torque_rpm', ptr) # RPM at which we reach peak Torque
        self.min_feed = FloatParam.from_value('min_feed', min_feed, 'mm/min')
        self.max_feed = FloatParam.from_value('max_feed', max_feed, 'mm/min')

        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        if isinstance(max_torque, Param):
            self.max_torque = max_torque
        else:
            max_power = self.max_power.value('kW')
            max_torque = max_torque or max_power*9548.8/self.peak_torque_rpm.v
            self.max_torque = FloatParam.from_value('max_torque', max_torque, 'Nm')

    def validate(self):
        if not self.label:
            raise AttributeError(f"Machine name is required")
        if self.peak_torque_rpm > self.max_rpm:
            raise AttributeError(f"Peak Torque RPM {self.peak_torque_rpm} must be less than max RPM {self.max_rpm}")
        if self.max_rpm <= self.min_rpm:
            raise AttributeError(f"Max rpm must be larger than min rpm")
        if self.max_feed <= self.min_feed:
            raise AttributeError(f"Max feed must be larger than min feed")

    def get_torque_at_rpm(self, rpm):
        # TODO: More advanced torque curve: lookup table with linear approximation between entries
        max_torque = self.max_torque.value('Nm')
        return min(max_torque, max_torque/self.peak_torque_rpm.v*rpm)

    def set_label(self, label):
        self.label = label

    def set_max_power(self, power, unit=None):
        self.max_power.v = power
        if unit is not None:
            self.max_power.unit = unit

    def set_min_rpm(self, min_rpm):
        self.min_rpm.v = min_rpm
        if self.min_rpm >= self.max_rpm:
            self.max_rpm = self.min_rpm+1

    def set_max_rpm(self, max_rpm):
        self.max_rpm.v = max_rpm
        if self.max_rpm <= self.min_rpm:
            self.min_rpm = self.max_rpm-1

    def set_min_feed(self, min_feed, unit=None):
        self.min_feed.v = min_feed
        if self.min_feed >= self.max_feed:
            self.max_feed = self.min_feed+1
        if unit is not None:
            self.min_feed.unit = unit

    def set_max_feed(self, max_feed, unit=None):
        self.max_feed.v = max_feed
        if self.max_feed <= self.min_feed:
            self.min_feed = self.max_feed-1
        if unit is not None:
            self.max_feed.unit = unit

    def set_peak_torque_rpm(self, peak_torque_rpm):
        self.peak_torque_rpm.v = peak_torque_rpm

    def set_max_torque(self, max_torque, unit=None):
        self.max_torque.v = max_torque
        if unit is not None:
            self.max_torque.unit = unit

    def dump(self):
        print(f"Machine {self.label}:")
        print(f"  Max power: {self.max_power.format()}")
        print(f"  RPM: {self.min_rpm} rpm - {self.max_rpm} rpm")
        print(f"  Feed: {self.min_feed.format()} - {self.max_feed.format()}")
        print(f"  Peak torque: {self.max_torque.format()} at {self.peak_torque_rpm} rpm")
