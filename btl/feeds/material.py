import inspect
from btl.toolmaterial import HSS, Carbide
from . import operation

# TODO: Load materials from resource files.

# Notes:
# - *_chipload_divisor attributes are defined as chipload = DIAMETER/divisor
# - The power factor originally taken from "Machinery's Handbook 29" (2012) pp1083-1084,
#   originally specified the "width of a chip that 1 HP can make".
#   I converted this to metric. In other words, the original factor was "in³ * fac = HP",
#   which equals "mm³*0.0610237 * fac * 0.745699872 = KW". So below, I multiplied all
#   factors by 0.000061024*0.745699872=0.00004550260618944 to simplify their use in
#   a metric context.
METRIC_POWER_FACTOR=0.04550260618944

class Material(object):
    @classmethod
    def get_speeds(cls, tool_material):
        data = cls.cutting_data[tool_material]
        return data['speeds']

    @classmethod
    def get_chipload_divisor(cls, tool_material):
        data = cls.cutting_data[tool_material]
        return data['chipload_divisor']

    @classmethod
    def dump(cls):
        print(f"Material data for {cls.name}")
        for tool_material, data in cls.cutting_data.items():
            print(f"  {tool_material.name}:")
            print(f"    Chipload divisor: {data['chipload_divisor']}")
            print( "    Speeds:")
            for op, (min_speed, max_speed) in data['speeds'].items():
                print(f"      {op.label}: min {min_speed}, max {max_speed}")

class Aluminium6061(Material):
    name = 'Aluminium Alloy (e.g. 6061)'
    power_factor = 0.33*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 160,  # chipload = DIAMETER/divisor
            'speeds': {
                operation.Milling: (152, 182), # https://littlemachineshop.com/reference/cuttingspeeds.php
                operation.Slotting: (120, 146), # estimated, 80% of milling speed
                operation.Drilling: (106, 122), # https://littlemachineshop.com/reference/cuttingspeeds.php
            }
        },
        Carbide: {
            'chipload_divisor': 80,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=3850
                operation.Milling: (640, 865),
                operation.Slotting: (425, 575),
                operation.Drilling: (215, 290),
                #operation.Turning: (510, 690),
                #operation.Parting: (340, 460),
            }
        },
    }


class Aluminium7075(Material):
    name = 'Aluminium Alloy (7075)'
    power_factor = 0.33*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 160,
            'speeds': {
                operation.Milling: (60, 300), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 240), # estimated, 80% of milling speed
                operation.Drilling: (106, 122), # https://littlemachineshop.com/reference/cuttingspeeds.php
            }
        },
        Carbide: {
            'chipload_divisor': 80,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=3970
                operation.Milling: (400, 545),
                operation.Slotting: (270, 360),
                operation.Drilling: (135, 180),
                #operation.Turning: (320, 435),
                #operation.Parting: (215, 290),
            }
        },
    }

class CopperAlloy(Material):
    name = 'Copper Alloy'
    power_factor = 0.80*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 160,
            'speeds': {
                operation.Milling: (60, 300), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 240), # estimated, 80% of milling speed
                operation.Drilling: (24, 60), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (120, 250), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 80,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=7210
                operation.Milling: (280, 555),
                operation.Slotting: (185, 370),
                operation.Drilling: (95, 185),
                #operation.Turning: (220, 445),
                #operation.Parting: (150, 295),
            }
        },
    }

class Iron(Material):
    name = 'Iron'
    power_factor = 0.85*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 200,
            'speeds': {
                operation.Milling: (60, 250), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 200), # estimated, 80% of milling speed
                operation.Drilling: (15, 30), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (15, 45), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 100,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=3230
                operation.Milling: (225, 305),
                operation.Slotting: (230, 315),
                operation.Drilling: (190, 255),
                #operation.Parting: (165, 225),
                #operation.Turning: (330, 450),
            }
        },
    }

class ToolSteel(Material):
    name = 'Tool Steel (640-670N/mm²)'
    power_factor = 1.0*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 250,
            'speeds': {
                operation.Milling: (60, 100), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 80), # estimated, 80% of milling speed
                operation.Drilling: (7, 15), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (30, 45), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 300,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=1610
                operation.Milling: (95, 130),
                operation.Slotting: (90, 120),
                operation.Drilling: (65, 85),
                #operation.Turning: (155, 210),
                #operation.Parting: (75, 100),
            }
        },
    }

class LowCarbonSteel(Material):
    name = 'Low Carbon Steel (340-690N/mm²)'
    power_factor = 1.0*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 250,
            'speeds': {
                operation.Milling: (60, 100), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 80), # estimated, 80% of milling speed
                operation.Drilling: (6, 18), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (40, 60), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 300,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=960
                operation.Milling: (125, 170),
                operation.Slotting: (115, 155),
                operation.Drilling: (80, 110),
                #operation.Turning: (205, 275),
                #operation.Parting: (100, 135),
            }
        },
    }

class Stainless(Material):
    name = 'Stainless Steel'
    power_factor = 0.80*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 200,
            'speeds': {
                operation.Milling: (60, 80), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (48, 64), # estimated, 80% of milling speed
                operation.Drilling: (7, 15), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (15, 35), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 200,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=1750
                operation.Milling: (100, 135),
                operation.Slotting: (95, 130),
                operation.Drilling: (45, 60),
                #operation.Turning: (160, 215),
                #operation.Parting: (65, 85),
            }
        },
    }

class Titanium(Material):
    name = 'Titanium (900-1200N/mm²)'
    power_factor = 0.80*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 200,
            'speeds': {
                operation.Milling: (5, 7), # https://mae.ufl.edu/designlab/Advanced%20Manufacturing/Speeds%20and%20Feeds/Speeds%20and%20Feeds.htm
                operation.Slotting: (4, 6), # estimated, 80% of milling speed
                operation.Drilling: (6, 15), # https://www.easyspeedsandfeeds.com/
                #operation.Parting: (10, 15), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 250,
            'speeds': { # Source: https://www.machiningdoctor.com/mds/?matId=6640
                operation.Milling: (45, 60),
                operation.Slotting: (50, 70),
                operation.Drilling: (50, 70),
                #operation.Turning: (60, 80),
                #operation.Parting: (35, 50),
            }
        },
    }

class Plastic(Material):
    name = 'Plastic'
    power_factor = 0.20*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 125,
            'speeds': {
                operation.Milling: (200, 300), # https://bekas.sk/files/pdfs/44.pdf
                operation.Slotting: (160, 240), # estimated, 80% of milling speed
                operation.Drilling: (100, 300), # TODO. guesses for now
                #operation.Parting: (100, 150), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
        Carbide: {
            'chipload_divisor': 40,
            'speeds': {
                operation.Milling: (100, 1000), # TODO. guesses for now
                operation.Slotting: (80, 800), # estimated, 80% of milling speed
                operation.Drilling: (100, 1000), # TODO. guesses for now
                #operation.Parting: (150, 300), # https://www.heinrich-meier.de/upload/shoppictures_29/SchnittgeschwindigkeitNutex.pdf
            }
        },
    }

class Softwood(Material):
    name = 'Wood (soft)'
    power_factor = 0.20*METRIC_POWER_FACTOR

    cutting_data = {
        HSS: {
            'chipload_divisor': 100,
            'speeds': {
                operation.Milling: (100, 1300), # TODO. guesses for now
                operation.Slotting: (80, 1040), # estimated, 80% of milling speed
                operation.Drilling: (100, 1000), # TODO. guesses for now
            }
        },
        Carbide: {
            'chipload_divisor': 80,
            'speeds': {
                operation.Milling: (100, 1300), # TODO. guesses for now
                operation.Slotting: (None, None), # will be auto-estimated from milling
                operation.Drilling: (100, 1300), # TODO. guesses for now
            }
        },
    }

class Hardwood(Material):
    name = 'Hardwood'
    power_factor = 0.30*METRIC_POWER_FACTOR # Guess based on softwood

    cutting_data = {
        HSS: {
            'chipload_divisor': 100, # Guess based on softwood
            'speeds': {
                operation.Milling: (100, 1300), # TODO. guesses for now
                operation.Slotting: (80, 1040), # estimated, 80% of milling speed
                operation.Drilling: (100, 1300), # TODO. guesses for now
            }
        },
        Carbide: {
            'chipload_divisor': 80, # Guess based on softwood
            'speeds': {
                operation.Milling: (100, 1300), # TODO. guesses for now
                operation.Slotting: (80, 1040), # estimated, 80% of milling speed
                operation.Drilling: (100, 1300), # TODO. guesses for now
            }
        },
    }

materials = [c for c in locals().values()
             if inspect.isclass(c) and issubclass(c, Material) and c != Material]
