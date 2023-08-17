import random
from ..imperial import si_to_imperial, si_unit_to_imperial_unit

class Param:
    is_internal = False

    def __init__(self, decimals, min, max, unit=None, v=None):
        self.decimals = decimals
        self.min = min
        self.max = max
        self.limit = max
        self.unit = unit
        self.v = v if v is not None else min

    def __str__(self):
        return str(self.v if self.v is not None else '')

    def assign_random(self):
        limit = min(self.max, self.limit)
        self.v = random.uniform(self.min, limit)

    def set_limit(self, limit):
        self.limit = min(self.max, limit)

    def apply_limits(self):
        self.v = min(self.limit, self.max, self.v)
        self.v = max(self.min, self.v)

    def reset_limit(self):
        self.limit = self.max

    def get_percent_of_max(self):
        return self.v/self.max

    def get_percent_of_limit(self):
        if self.min < 0:
            return abs(1-abs(self.v)/abs(self.min))
        return self.v/min(self.max, self.limit)

    def within_minmax(self):
        return self.v >= self.min and self.v <= self.max

    def get_error_distance(self):
        if self.v > self.max:
            return self.v-self.max
        elif self.v > self.limit:
            return self.v-self.limit
        elif self.v < self.min:
            return self.min-self.v
        return 0

    def get_error_distance_percent(self):
        limit = min(self.max, self.limit)
        dist = self.get_error_distance()
        diff = abs(limit-self.min)
        return dist/diff if dist else 0

    def _format_value(self, value, decimals=None):
        fmt = "{{:.{}f}}".format(self.decimals if decimals is None else decimals)
        value = fmt.format(value) if isinstance(value, float) else str(value)
        if self.unit:
            if self.unit != '°':
                value += ' '
            value += self.unit
        return value

    def format(self):
        return self._format_value(self.v)

    def to_string(self, decimals=None):
        percent = self.get_percent_of_limit()*100
        value = self._format_value(self.v, decimals)
        min_value = self._format_value(self.min, decimals)
        max_value = self._format_value(self.max, decimals)
        limit = self._format_value(self.limit, decimals)
        return f"{value} ({percent:.0f}%) (min {min_value}, max {max_value}, limit {limit})"

    def get_imperial(self, unit=None):
        if self.unit is None:
             return self.v, unit
        if self.v is None:
             unit = unit if unit else si_unit_to_imperial_unit(self.unit)
             return None, unit
        return si_to_imperial(self.v, self.unit, unit)

class UncheckedParam(Param):
    def get_error_distance(self):
        return 0

class InputParam(Param):
    pass

class Const(Param):
    is_internal = True
