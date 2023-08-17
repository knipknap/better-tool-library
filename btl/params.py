import re
from .imperial import si_to_imperial, si_unit_to_imperial_unit

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

class IntParam(Param):
    type = int

class FloatParam(Param):
    type = float

    def get_imperial(self, unit=None):
        if self.unit is None:
             return self.v, unit
        if self.v is None:
             unit = unit if unit else si_unit_to_imperial_unit(self.unit)
             return None, unit
        return si_to_imperial(self.v, self.unit, unit)

class DistanceParam(FloatParam):
    unit = 'mm'
    fmt = '{}'

class AngleParam(FloatParam):
    unit = '°'
    fmt = '{}'
