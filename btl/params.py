import re
from . import const

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

    def get_imperial(self):
        return self.v

class BoolParam(Param):
    type = bool

class IntParam(Param):
    type = int

class FloatParam(Param):
    type = float

class DistanceParam(FloatParam):
    unit = 'mm'
    fmt = '{}'
    metric_to_imperial = const.mmToInch

    def get_imperial(self):
        return self.v*self.metric_to_imperial if self.v is not None else None

class AngleParam(FloatParam):
    unit = '°'
    fmt = '{}'
