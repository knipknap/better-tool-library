
#############
# Base types
#############
class Base(object):
    name = None
    label = None
    unit = ''
    fmt = '{}'
    type = str

    def format(self, value):
        return self.fmt.format(value)

    def validate(self, value):
        return isinstance(value, self.type)

class EnumBase(Base):
    choices = []

    def validate(self, value):
        return value in self.choices

class BoolBase(Base):
    type = bool

class IntBase(Base):
    type = int

class FloatBase(Base):
    type = float

class DistanceBase(FloatBase):
    unit = 'mm'
    fmt = '{}mm'

class AngleBase(FloatBase):
    unit = '°'
    fmt = '{}°'

#################
# Specific types
#################
class Diameter(DistanceBase):
    name = 'diameter'
    label = 'Diameter'
    fmt = 'D{}mm'

class Shaft(DistanceBase):
    name = 'shaft'
    label = 'Shaft Diameter'
    fmt = 'Shaft {}mm'

class Length(DistanceBase):
    name = 'length'
    label = 'Length'
    fmt = 'L{}mm'

class Flutes(IntBase):
    name = 'flutes'
    label = 'Flutes'
    fmt = '{}-flute'

class Pocket(IntBase):
    name = 'pocket'
    label = 'Pocket'

class Material(EnumBase):
    name = 'material'
    label = 'Material'
    choices = 'HSS', 'Carbide'

class SpindleDirection(EnumBase):
    name = 'spindledirection'
    label = 'Spindle Direction'
    choices = 'Forward', 'Reverse', 'None'

# The parameters need to be ordered by importance; this order is
# used to prioritize which paramaters to show when there is limited
# space.
# E.g. when generating Tool.get_param_summary() creates a summary
# description of the tool, it shows the important parameters first.
known_types = [Diameter(),
               Shaft(),
               Length(),
               Flutes(),
               Material()]
