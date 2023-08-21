import re
import random
from .imperial import convert, get_default_unit_conversion

class Param(object):
    name = None
    label = None
    unit = ''
    fmt = '{}'
    type = str
    choices = None

    def __init__(self, name=None, unit=None, v=None):
        label = re.sub(r'([A-Z])', r' \1', name or '').strip().capitalize()
        self.name = self.name if name is None else name
        self.label = self.label if name is None else label
        self.unit = self.unit if unit is None else unit
        self.v = v

    def __str__(self):
        return str(self.v if self.v is not None else '')

    def format(self):
        unit = ' '+self.unit if self.unit else ''
        return self.fmt.format(self.v)+unit

    def validate(self):
        if not isinstance(self.v, self.type):
            return False
        if self.choices is not None and value not in self.choices:
            return False
        return True

    def to_dict(self):
        return {
            'objtype': self.__class__.__name__,
            'label': self.label,
            'name': self.name,
            'unit': self.unit,
            'fmt': self.fmt,
            'type': self.type.__name__,
            'choices': self.choices,
        }

    def get_imperial(self, unit=None):
        """Returns a tuple (value, unit)"""
        return self.v, unit

class BoolParam(Param):
    type = bool

class NumericParam(Param):
    def __init__(self,
                 min=None,
                 max=None,
                 decimals=0,
                 unit=None,
                 v=None,
                 name=None):
        super(NumericParam, self).__init__(name=name, unit=unit, v=v)
        self.decimals = decimals
        self.min = min
        self.max = max
        self.limit = max
        self.v = v if v is not None else min

    def set(self, value, unit):
        self.v, self.unit = convert(self.v, unit, self.unit)

    def format(self, value=None, decimals=None):
        value = value if value is not None else self.v
        decimals = decimals if decimals is not None else self.decimals
        if decimals is None:
            return super(NumericParam, self).format()

        fmt = "{{:.{}f}}".format(decimals)
        value = fmt.format(value) if isinstance(value, float) else str(value)
        if self.unit:
            if self.unit != '°':
                value += ' '
            value += self.unit
        return value

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

    def to_string(self, decimals=None):
        percent = self.get_percent_of_limit()*100
        value = self.format(self.v, decimals)
        min_value = self.format(self.min, decimals)
        max_value = self.format(self.max, decimals)
        limit = self.format(self.limit, decimals)
        return f"{value} ({percent:.0f}%) (min {min_value}, max {max_value}, limit {limit})"

    def get_imperial(self, unit=None):
        if self.unit is None:
             return self.v, unit
        if self.v is None:
             unit = unit if unit else get_default_unit_conversion(self.unit)
             return None, unit
        return convert(self.v, self.unit, unit)

class IntParam(NumericParam):
    type = int

class FloatParam(NumericParam):
    type = float

    def __init__(self,
                 min=None,
                 max=None,
                 decimals=2,
                 unit=None,
                 v=None,
                 name=None):
        super(FloatParam, self).__init__(name=name,
                                         unit=unit,
                                         v=v,
                                         min=min,
                                         max=max,
                                         decimals=decimals)

class DistanceParam(FloatParam):
    unit = 'mm'
    fmt = '{}'

class AngleParam(FloatParam):
    unit = '°'
    fmt = '{}'
