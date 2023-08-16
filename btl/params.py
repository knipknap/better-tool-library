import re
from copy import copy
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

    def to_imperial(self):
        return copy(self)

class BoolParam(Param):
    type = bool

class IntParam(Param):
    type = int

class FloatParam(Param):
    type = float

class DistanceParam(FloatParam):
    unit = 'mm'
    fmt = '{}'

    def get_imperial(self):
        obj = copy(self)
        obj.unit = si_unit_to_imperial_unit(self.unit)
        if self.v is not None:
            obj.v = si_to_imperial(self.v, self.unit)
        return obj

class AngleParam(FloatParam):
    unit = '°'
    fmt = '{}'
