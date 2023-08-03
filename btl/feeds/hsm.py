# Equations from:
# WIDIA - https://www.itc-ltd.co.uk/wp-content/uploads/2019/02/WIDIA-TROCHOIDAL-MILLING.pdf
import math

SLOTTING_SPEED_MULTIPLIER = 0.83 # WIDIA: 90% tooth cutting speed for slotting minus ~10% which is added back in our interpolation equation.
HSM_SPEED_MULTIPLIER      = 4.0  # WIDIA
SLOTTING_CHIP_MULTIPLIER  = 0.73 # WIDIA: 80% chipload for slotting minus ~10% which is added back in our interpolation equation.
HSM_CHIP_MULTIPLIER       = 4.4  # WIDIA

def get_hsm_factors(doc, woc, diameter, corner, lead):
    """
    Given the depth of cut, width of cut, diameter, and corner or lead angle,
    this function returns some factors to apply for an optimized speed.

    Metric inputs:
    - doc in mm
    - woc in mm
    - diameter in mm
    - corner in mm
    - lead in mm

    Metric returns:
    - speed factor (float)
    - chip factor (float)
    - feed factor (float)
    """
    # ASSUME: LEAD angle is angle between the workpiece and the cutting edge (flutes parallel to axis = 90-degree lead)
    # ASSUME: Helix angle is angle between the axis of the tool to the slope of the helical flutes. Flutes parallel to axis = 0-degree helix

    # Radial chip thinning: Use WOC & diameter
    radial_engagement = woc/diameter # SANDVIK
    # WIDIA -- This is an approximation of average chip thickness. Nice because it is 1.0 at full-slot, and valid through the entire range.
    radial_chip_thinning_factor = 1/math.sqrt(radial_engagement)

    # WIDIA: Speed & Chipload Multipliers for HSM
    # Speed Multiplier: Full Slot = 0.9, 50% WOC = 1, 40% WOC = 1.1, 30% = 1.2, 20% = 1.3, 10% = 1.4, 5% = 2.5, 4% = 3, 2% = 4
    # Feed(chipload?) Multiplier: Full Slot = 0.9, 50% WOC = 1, 40% WOC = 1, 30% = 1.1, 20% = 1.4, 10% = 2.0, 5% = 2.5, 4% = 3, 2% = 4.4
    #   (but WIDIA also says reduce chipload by 20% for full slot.. I'm choosing 0.8 for slotting chipload)

    # Equations designed by Bryan Turner (based on WIDIA suggested multipliers for Speed & Chipload)
    speed_factor = SLOTTING_SPEED_MULTIPLIER + (HSM_SPEED_MULTIPLIER - SLOTTING_SPEED_MULTIPLIER) / (radial_engagement * 50)
    chip_factor = SLOTTING_CHIP_MULTIPLIER + (HSM_CHIP_MULTIPLIER - SLOTTING_CHIP_MULTIPLIER) / (radial_engagement * 50)

    # Axial chip thinning: Use DOC & corner-radius
    if corner and corner > 0 and doc < corner:
        # TODO: This factor is for BALLNOSE end mills -- check that it is valid for corner-rounded end mills.
        axial_chip_thinning_factor = 1 / math.sqrt(1 - math.pow(1 - (doc/corner), 2))
    elif lead and lead != 90:
        # ASSUME: LEAD angle is angle between the cutting edge and the workpiece (straight end-mill = 90-degree lead)
        axial_chip_thinning_factor = 1 / (math.cos(math.radians(lead)) * math.tan(math.radians(lead)))
    else:
        axial_chip_thinning_factor = 1
    feed_factor = axial_chip_thinning_factor*radial_chip_thinning_factor

    return speed_factor, chip_factor, feed_factor
