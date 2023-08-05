import inspect

class Operation(object):
    speed_multiplier = 1
    chip_multiplier = 1

    def __str__(self):
        return self.label

class Slotting(Operation):
    label = 'Slotting'
    speed_multiplier = 0.83 # WIDIA: 90% tooth cutting speed for slotting minus ~10% which is added back in our interpolation equation.
    chip_multiplier = 0.73 # WIDIA: 80% chipload for slotting minus ~10% which is added back in our interpolation equation.

class Milling(Operation):
    label = 'Milling'

class HSM(Operation):
    label = 'Adaptive (HSM)'
    speed_multiplier = 4.0  # WIDIA
    chip_multiplier = 4.4  # WIDIA

class Drilling(Operation):
    label = 'Drilling'

#class Turning(Operation):   # unsupported for now
#    label = 'Turning'

#class Parting(Operation):   # unsupported for now
#    label = 'Parting'

operations = [c for c in locals().values()
              if inspect.isclass(c) and issubclass(c, Operation) and c != Operation]
