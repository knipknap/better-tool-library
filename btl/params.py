
#############
# Base types
#############
class Base:
    unit = ''
    fmt = '{}'
    type = str

    @classmethod
    def format(cls, value):
        return cls.fmt.format(value)

    @classmethod
    def validate(cls, value):
        return isinstance(value, cls.type)

class EnumBase(Base):
    choices = []

    @classmethod
    def validate(cls, value):
        return value in choices

class IntBase(Base):
    formatter = int
    type = int

class DistanceBase(Base):
    unit = 'mm'
    fmt = '{}mm'
    formatter = float
    type = float

#################
# Specific types
#################
class Diameter(DistanceBase):
    name = 'diameter'
    freecad = ('Diameter',)
    label = 'Diameter'
    fmt = 'D{}mm'

class Shaft(DistanceBase):
    name = 'shaft'
    freecad = 'ShankDiameter', 'ShaftDiameter'
    label = 'Shaft Diameter'
    fmt = 'Shaft {}mm'

class Length(DistanceBase):
    name = 'length'
    freecad = ('Length',)
    label = 'Length'
    fmt = 'L{}mm'

class Flutes(IntBase):
    name = 'flutes'
    freecad = ('Flutes',)
    label = 'Flutes'
    fmt = '{}-flute'

class Pocket(IntBase):
    name = 'pocket'
    freecad = ()
    label = 'Pocket'
    fmt = '{}'

class Material(EnumBase):
    name = 'material'
    freecad = ()
    label = 'Material'
    fmt = '{}'
    choices = 'HSS', 'Carbide'

# The parameters need to be ordered by importance; this order is
# used to prioritize which paramaters to show when there is limited
# space.
# E.g. when generating Tool.get_param_summar() creates a summary
# description of the tool, it shows the important parameters first.
known_types = [Diameter,
               Shaft,
               Length,
               Flutes,
               Material]

# Map freecad shape file parameter names to our internal representation.
fc_property_to_param_type = {}
for param in known_types:
    for alias in param.freecad:
        fc_property_to_param_type[alias] = param

fc_property_to_param_name = dict(
    (a, p.name) for (a, p) in fc_property_to_param_type.items()
)
