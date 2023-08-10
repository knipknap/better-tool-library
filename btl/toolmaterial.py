

class ToolMaterial(object):
    elasticity = 200000 # Modulus of elasticity (N/mm²)
    yield_strength = 1000 # MPa
    shear_strength = 1200 # MPa

class HSS(ToolMaterial):
    name = 'HSS'

    # https://material-properties.org/high-speed-steel-density-strength-hardness-melting-point/
    elasticity = 200000 # Modulus of elasticity (N/mm²)
    yield_strength = 1000 # MPa
    shear_strength = 1200 # MPa

class Carbide(ToolMaterial):
    name = 'Carbide'

    # https://material-properties.org/tungsten-carbide-properties-application-price/
    elasticity = 600000 # Modulus of elasticity (N/mm²)
    yield_strength = 330 # MPa
    shear_strength = 370 # MPa
