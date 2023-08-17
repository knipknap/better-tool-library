import re

meters_to_inch = 39.37007874
meters_to_feet = 3.280839895
meters_to_yards = 1.0936132983
meters_to_miles = 0.00062137119224
m2_to_in2 = 1550.0031
m2_to_ft2 = 10.7639
m2_to_yd2 = 1.19599
m2_to_mi2 = 3.861e-7
m3_to_in3 = 61023.7
m3_to_ft3 = 35.3147
m3_to_yd3 = 1.30795
m3_to_mi3 = 2.3991e-10
kw_to_hp = 1.34102
newton_to_lbf = 0.2248090795
nm_to_lbfin = 8.85075

_symbols = {
    # SI units.
    'nanometer': 'nm',
    'nanometers': 'nm',
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

_to_meter = {
    'nm': 1000000000,
    'um': 1000000,
    'mm': 1000,
    'cm': 100,
    'dm': 10,
    'm': 1,
    'km': .001,

    'nm²': 10000000000,
    'um²': 100000000,
    'mm²': 1000000,
    'cm²': 10000,
    'dm²': 100,
    'm²':  1,
    'km²': 10e-6,

    'nm³': 1000000000000000,
    'um³': 1000000000000,
    'mm³': 1000000000,
    'cm³': 1000000,
    'dm³': 1000,
    'm³':  1,
    'km³': 10e-9,

    'kW': 1,

    'N': 1,
    'Nm': 1,
}

_meter_to_imperial = {
    'in': meters_to_inch,
    'ft': meters_to_feet,
    'yd': meters_to_yards,
    'mi': meters_to_miles,
    'in²': m2_to_in2,
    'ft²': m2_to_ft2,
    'yd²': m2_to_yd2,
    'mi²': m2_to_mi2,
    'in³': m3_to_in3,
    'ft³': m3_to_ft3,
    'yd³': m3_to_yd3,
    'mi³': m3_to_mi3,
    'HP': kw_to_hp,
    'lbf': newton_to_lbf,
    'lbf-in': nm_to_lbfin,
}

_unit_map = {
    'nm': 'nm',    # no conversion
    'um': 'um',    # no conversion
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
    unit = re.sub(r'^([a-z]+)', _symbol_replace, unit)
    return re.sub(r'\^?(\d)', _exponent_replace, unit)

def unit_normalize(unit):
    base_unit, suffix = _suffix_split(unit)
    base_unit = _base_unit_normalize(base_unit)
    return base_unit+'/'+suffix if suffix else base_unit

def _split_exponent(unit):
    match = re.match(r'^([a-z]+)([⁰¹²³⁴⁵⁶⁷⁸⁹]*)$', unit, re.I)
    return match.group(1), match.group(2)

def si_unit_to_imperial_unit(unit):
    base_unit, suffix = _suffix_split(unit)
    base, exponent = _split_exponent(base_unit)
    dest_unit = _unit_map.get(base) + exponent
    return dest_unit+'/'+suffix if suffix else dest_unit

def si_to_imperial(value, source_unit, dest_unit=None):
    # Normalize the source unit and value to meters.
    source_base_unit, source_suffix = _suffix_split(source_unit)
    source_base_unit = _base_unit_normalize(source_base_unit)
    divisor = _to_meter.get(source_base_unit)
    if not divisor:
        raise AttributeError(f'unsupported source unit {source_unit}')
    value /= divisor

    # If a dest unit was not given, choose one.
    if dest_unit is None:
        base, exponent = _split_exponent(source_base_unit)
        dest_unit = _unit_map.get(base) + exponent
        dest_suffix = source_suffix

    # Normalize the destination unit.
    else:
        dest_unit, dest_suffix = _suffix_split(dest_unit)
        dest_unit = _base_unit_normalize(dest_unit)

    # Suffix remains unchanged.
    if source_suffix != dest_suffix:
        raise AttributeError(f'unsupported: "{source_unit}" to "{dest_unit}"')
    suffix = '/'+source_suffix if source_suffix else ''

    # Finally convert.
    if source_unit == dest_unit:
        return value, dest_unit+suffix
    factor = _meter_to_imperial.get(dest_unit)
    if not factor:
        raise AttributeError(f'unsupported target unit {dest_unit}')
    return value*factor, dest_unit+suffix

if __name__ == '__main__':
    import sys

    value = float(sys.argv[1])
    unit = unit_normalize(sys.argv[2])
    print(f"Input interpretation: {value} {unit}")

    try:
        dest_unit = unit_normalize(sys.argv[3])
    except IndexError:
        dest_unit = None
    print(f"Target: {dest_unit or si_unit_to_imperial_unit(unit)}")

    value, unit = si_to_imperial(value, sys.argv[2], dest_unit)
    print(f"{value} {unit}")
