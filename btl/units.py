import re

meters_to_inch = 39.37007874
meters_to_feet = 3.280839895
meters_to_yards = 1.0936132983
meters_to_miles = 0.00062137119224
kw_to_hp = 1.34102
newton_to_lbf = 0.2248090795
nm_to_lbfin = 8.85075

_symbols = {
    # SI units.
    'nanometer': 'nm',
    'nanometers': 'nm',
    'um': 'μm',
    'micrometer': 'μm',
    'micrometers': 'μm',
    'millimeter': 'mm',
    'millimeters': 'mm',
    'centimeter': 'cm',
    'centimeters': 'cm',
    'decimeter': 'dm',
    'decimeters': 'dm',
    'meter': 'm',
    'meters': 'm',
    'kilometer': 'km',
    'kilometers': 'km',

    'kw': 'kW',
    'kilowatt': 'kW',
    'kilowatts': 'kW',

    'newton': 'N',
    'newtons': 'N',
    'newton-meter': 'Nm',
    'newton-meters': 'Nm',

    # Imperial.
    '"': 'in',
    'inch': 'in',
    'inches': 'in',
    '′': 'ft',
    "'": 'ft',
    'foot': 'ft',
    'feet': 'ft',
    'yard': 'yd',
    'yards': 'yd',
    'mile': 'mi',
    'miles': 'mi',

    'hp': 'HP',
    'horsepower': 'HP',

    'pound-force': 'lbf',
    'inch-pounds': 'lbf-in',
}

_si_to_imperial = {
    ('μm', 'nm'): 1000,
    ('mm', 'nm'): 1000000,
    ('cm', 'nm'): 10000000,
    ('dm', 'nm'): 100000000,
    ('m', 'nm'):  1000000000,
    ('km', 'nm'): 1000000000000,

    ('mm', 'μm'): 1000,
    ('cm', 'μm'): 10000,
    ('dm', 'μm'): 100000,
    ('m', 'μm'):  1000000,
    ('km', 'μm'): 1000000000,

    ('cm', 'mm'): 10,
    ('dm', 'mm'): 100,
    ('m', 'mm'):  1000,
    ('km', 'mm'): 1000000,

    ('dm', 'cm'): 10,
    ('m', 'cm'):  100,
    ('km', 'cm'): 100000,

    ('m', 'dm'):  10,
    ('km', 'dm'): 10000,

    ('km', 'm'): 1000,

    ('nm', 'in'): 0.000000001*meters_to_inch,
    ('μm', 'in'): 0.000001*meters_to_inch,
    ('mm', 'in'): 0.001*meters_to_inch,
    ('cm', 'in'): 0.01*meters_to_inch,
    ('dm', 'in'): 0.1*meters_to_inch,
    ('m', 'in'): meters_to_inch,
    ('km', 'in'): 1000*meters_to_inch,

    ('nm', 'ft'): 0.000000001*meters_to_feet,
    ('μm', 'ft'): 0.000001*meters_to_feet,
    ('mm', 'ft'): 0.001*meters_to_feet,
    ('cm', 'ft'): 0.01*meters_to_feet,
    ('dm', 'ft'): 0.1*meters_to_feet,
    ('m', 'ft'): meters_to_feet,
    ('km', 'ft'): 1000*meters_to_feet,

    ('nm', 'yd'): 0.000000001*meters_to_yards,
    ('μm', 'yd'): 0.000001*meters_to_yards,
    ('mm', 'yd'): 0.001*meters_to_yards,
    ('cm', 'yd'): 0.01*meters_to_yards,
    ('dm', 'yd'): 0.1*meters_to_yards,
    ('m', 'yd'): meters_to_yards,
    ('km', 'yd'): 1000*meters_to_yards,

    ('nm', 'mi'): 0.000000001*meters_to_miles,
    ('μm', 'mi'): 0.000001*meters_to_miles,
    ('mm', 'mi'): 0.001*meters_to_miles,
    ('cm', 'mi'): 0.01*meters_to_miles,
    ('dm', 'mi'): 0.1*meters_to_miles,
    ('m', 'mi'): meters_to_miles,
    ('km', 'mi'): 1000*meters_to_miles,

    ('kW', 'HP'): kw_to_hp,

    ('N', 'lbf'): newton_to_lbf,
    ('Nm', 'lbf-in'): nm_to_lbfin,
}
unitmap = {}
for (src, dest), factor in _si_to_imperial.items():
    unitmap[(src, src)] = 1
    unitmap[(dest, dest)] = 1
    unitmap[(src, dest)] = factor
    unitmap[(dest, src)] = 1/factor

distance_units = {
    'nm', 'μm', 'mm', 'cm', 'dm', 'm', 'km',
    'in', 'ft', 'yd', 'mi'
}

_default_conversions = {
    'nm': 'nm',    # no conversion
    'μm': 'μm',    # no conversion
    'mm': 'in',
    'cm': 'in',
    'dm': 'in',
    'm':  'yd',
    'km': 'mi',

    'kW': 'HP',
    'N': 'lbf',
    'Nm': 'lbf-in',
}

_exponent_map = {
    '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
    '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
}
_rev_exponent_map = {v: k for k, v in _exponent_map.items()}

def _suffix_split(unit):
    if '/' in unit:
        return unit.split('/', 1)
    return unit, None

def _symbol_replace(match):
    # Replaces units by normalized unit names.
    unit = match.group(1)
    return _symbols.get(unit, unit)

def _exponent_replace(match):
    # Replaces exponents by UTF superscript ones.
    return _exponent_map[match.group(1)]

def _base_unit_normalize(unit):
    assert '/' not in unit
    inputs = '|'.join(_symbols.keys())
    unit = re.sub(f'^({inputs})', _symbol_replace, unit)
    unit = re.sub(r'\^?(\d)', _exponent_replace, unit)
    return re.sub(r'^([μa-z]+)¹$', r'\1', unit) # strip "1" exponent

def unit_normalize(unit):
    base_unit, suffix = _suffix_split(unit)
    base_unit = _base_unit_normalize(base_unit)
    return base_unit+'/'+suffix if suffix else base_unit

def _split_exponent(unit):
    match = re.match(r'^([μa-z]+)([⁰¹²³⁴⁵⁶⁷⁸⁹]*)$', unit, re.I)
    return match.group(1), match.group(2)

def get_default_unit_conversion(unit):
    base_unit, suffix = _suffix_split(unit)
    base, exponent = _split_exponent(base_unit)
    dest_unit = _default_conversions.get(base) + exponent
    return dest_unit+'/'+suffix if suffix else dest_unit

def _superscript_replace(match):
    # Replaces exponents by UTF superscript ones.
    return _rev_exponent_map[match.group(1)]

def _superscript2int(string):
    if not string:
        return None
    intstr = re.sub(r'([⁰¹²³⁴⁵⁶⁷⁸⁹])', _superscript_replace, string)
    try:
        return int(intstr)
    except ValueError:
        return None

def convert(value, source_unit, dest_unit=None):
    # Normalize the source unit.
    source_base_unit, source_suffix = _suffix_split(source_unit)
    source_base_unit = _base_unit_normalize(source_base_unit)
    source_base_unit, source_exponent = _split_exponent(source_base_unit)
    source_exponent_int = _superscript2int(source_exponent) or 1
    source_exponent = '' if source_exponent_int == 1 else source_exponent
    suffix = '/'+source_suffix if source_suffix else ''

    # If a dest unit was not given, choose one.
    if dest_unit is None:
        dest_unit = _default_conversions.get(source_base_unit)
        dest_unit += source_exponent+suffix

    # Normalize the target unit.
    dest_base_unit, dest_suffix = _suffix_split(dest_unit)
    dest_base_unit = _base_unit_normalize(dest_base_unit)
    dest_base_unit, dest_exponent = _split_exponent(dest_base_unit)
    dest_exponent_int = _superscript2int(dest_exponent) or 1
    dest_exponent = '' if dest_exponent_int == 1 else dest_exponent

    # Sanity checks.
    if source_exponent_int != dest_exponent_int:
        raise AttributeError(
            f'exponent conversion unsupported: "{source_unit}" to "{dest_unit}"')
    if source_suffix != dest_suffix:
        raise AttributeError(
            f'suffix conversion unsupported: "{source_unit}" to "{dest_unit}"')

    # Check if this conversion is supported.
    factor = unitmap.get((source_base_unit, dest_base_unit))
    if factor is None:
        raise AttributeError(f'unsupported: "{source_unit}" to "{dest_unit}"')

    return value*10**source_exponent_int*factor**dest_exponent_int/10**dest_exponent_int, \
           dest_base_unit+(dest_exponent or '')+suffix

if __name__ == '__main__':
    import sys

    value = float(sys.argv[1])
    unit = unit_normalize(sys.argv[2])
    print(f"Input interpretation: {value} {unit}")

    try:
        dest_unit = unit_normalize(sys.argv[3])
    except IndexError:
        dest_unit = None
    print(f"Target: {dest_unit or get_default_unit_conversion(unit)}")

    try:
        value, dest_unit = convert(value, unit, dest_unit)
    except AttributeError as e:
        print("Error:", e)
    else:
        print(f"{value} {dest_unit}")
