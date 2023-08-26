import math
import inspect
from ..i18n import translate
from .util import get_tool_engagement_angle, get_lead_angle_deflection_factor

class Operation(object):
    speed_multiplier = 1
    chip_multiplier = 1

    @classmethod
    def label(cls):
        raise NotImplementedError

    @classmethod
    def prepare(cls, fc):
        """
        Should be used to set limits for the calculator input parameters
        DOC, WOC, speed, and chipload.
        """
        # Width of cut cannot be bigger than the tool diameter.
        fc.woc.set_limit(fc.endmill.shape.get_diameter())

        # Depth of cut cannot be bigger than the tool diameter.
        fc.doc.set_limit(fc.endmill.shape.get_cutting_edge())

        # Set speed and chipload limits according to the workpiece material
        # and the endmill material.
        speed_range = fc.endmill.get_speed_for_material(fc.material, cls)
        fc.speed.set_limit(speed_range[1]*cls.speed_multiplier)
        chipload = fc.endmill.get_chipload_for_material(fc.material)
        fc.chipload.set_limit(chipload*cls.chip_multiplier)

    @classmethod
    def get_overlap(cls, endmill, doc, woc):
        pixmap = endmill.get_pixmap()
        return pixmap.get_overlap_from_woc(doc, woc)

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        """
        This method is supposed to update the DOC, WOC, speed, and chipload
        according to the given endmill and material.
        """
        raise NotImplementedError

    @classmethod
    def get_lead_angle_deflection_factors(cls, doc, woc, diameter):
        return get_lead_angle_deflection_factor(doc, woc, diameter)

class Slotting(Operation):
    speed_multiplier = 0.83 # WIDIA: 90% tooth cutting speed for slotting minus ~10% which is added back in our interpolation equation.
    chip_multiplier = 0.73 # WIDIA: 80% chipload for slotting minus ~10% which is added back in our interpolation equation.

    @classmethod
    def label(cls):
        return translate('btl', 'Slotting')

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        diameter = endmill.shape.get_diameter()

        # In slotting, the width of cut is fixed.
        pixmap = endmill.get_pixmap()
        effective_d = pixmap.get_effective_diameter_from_doc(fc.doc.v)
        fc.effective_diameter.v = effective_d
        fc.woc.v = effective_d
        fc.woc.set_limit(effective_d)

        # Tool Engagement Angle (straight shoulder along a straight path)
        angle = get_tool_engagement_angle(max(0, fc.woc.v), effective_d)
        fc.engagement_angle.v = angle

class Profiling(Operation):
    @classmethod
    def label(cls):
        return translate('btl', 'Profiling')

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        pixmap = endmill.get_pixmap()
        effective_d = pixmap.get_effective_diameter_from_doc(fc.doc.v)
        fc.effective_diameter.v = effective_d
        fc.woc.set_limit(effective_d)

        # Tool Engagement Angle (straight shoulder along a straight path)
        woc = max(0.00001, fc.woc.v)
        fc.engagement_angle.v = get_tool_engagement_angle(woc, effective_d)

class HSM(Operation):
    speed_multiplier = 4.0  # WIDIA
    chip_multiplier = 4.4  # WIDIA

    @classmethod
    def label(cls):
        return translate('btl', 'Adaptive (HSM)')

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        pixmap = endmill.get_pixmap()
        effective_d = pixmap.get_effective_diameter_from_doc(fc.doc.v)
        fc.effective_diameter.v = effective_d
        fc.woc.set_limit(effective_d)

        # Tool Engagement Angle (straight shoulder along a straight path)
        doc = max(0.00001, fc.doc.v)
        woc = max(0.00001, fc.woc.v)
        fc.engagement_angle.v = get_tool_engagement_angle(woc, effective_d)

        # Helix angle is angle between the axis of the tool to the slope
        # of the helical flutes. Flutes parallel to axis = 0-degree helix
        # TODO: calculate the effect of endmill flute helix angle?
        # TODO: Helical Interpolation
        # ------------------------
        # - Adjust WOC and feed
        #woc, feed = interpolate_helical(HELICAL.v, DIAMETER.v, WOC.v)

        # Adjust chipload based on how thin the chips are.
        # WIDIA -- This is an approximation of average chip thickness. Nice
        # because it is 1.0 at full-slot, and valid through the entire range.
        radial_engagement = woc/effective_d # SANDVIK
        radial_chip_thinning_factor = 1/math.sqrt(radial_engagement)

        """
        WIDIA: Speed & Chipload Multipliers for HSM
        Speed Multiplier:
          - Full Slot = 0.9
          - 50% WOC = 1
          - 40% WOC = 1.1
          - 30% WOC = 1.2
          - 20% WOC = 1.3
          - 10% WOC = 1.4
          -  5% WOC = 2.5
          -  4% WOC = 3
          -  2% WOC = 4

        Feed(chipload?) Multiplier:
          - Full Slot = 0.9
          - 50% WOC = 1
          - 40% WOC = 1
          - 30% WOC = 1.1
          - 20% WOC = 1.4
          - 10% WOC = 2.0
          -  5% WOC = 2.5
          -  4% WOC = 3
          -  2% WOC = 4.4

        (but WIDIA also says reduce chipload by 20% for full slot. I'm choosing 0.8 for slotting chipload)
        """
        # Equations designed by Bryan Turner (based on WIDIA suggested multipliers for Speed & Chipload)
        # WIDIA: Speed & Chipload Multipliers for HSM
        # TODO: check the curves resulting from these functions
        fc.speed_factor.v = Slotting.speed_multiplier \
            + (cls.speed_multiplier-Slotting.speed_multiplier)/(radial_engagement*50)

        fc.chip_factor.v = Slotting.chip_multiplier \
            + (cls.chip_multiplier-Slotting.chip_multiplier)/(radial_engagement*50)
    
        # Axial chip thinning: Use DOC & corner-radius
        endmill_corner = endmill.shape.get_corner_radius()
        endmill_angle = endmill.shape.get_cutting_edge_angle()/2
        if endmill_corner and endmill_corner > 0 and doc < endmill_corner:
            # TODO: This factor is for BALLNOSE end mills -- check that it is valid for corner-rounded end mills.
            axial_chip_thinning_factor = 1 / math.sqrt(1 - math.pow(1 - (doc/endmill_corner), 2))

        elif endmill_angle and endmill_angle != 90:
            # Endmill angle is the angle between the workpiece and the cutting edge.
            # (flutes parallel to axis = 90-degree lead)
            axial_chip_thinning_factor = 1 / (math.cos(math.radians(endmill_angle)) \
                                            * math.tan(math.radians(endmill_angle)))

        else:
            axial_chip_thinning_factor = 1

        fc.feed_factor.v = axial_chip_thinning_factor*radial_chip_thinning_factor
        speed_range = endmill.get_speed_for_material(material, Profiling)
        fc.speed.set_limit(speed_range[1]*fc.speed_factor.v)
        chipload = endmill.get_chipload_for_material(material)
        fc.chipload.set_limit(chipload*fc.chip_factor.v)

class Drilling(Operation):
    @classmethod
    def label(cls):
        return translate('btl', 'Drilling')

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        # TODO: Drilling op is not really complete/plausible.

        # ------------------------
        # WOC / DOC -- irrelevant?
        # feed = chipload * rpm
        # MRR = area of drill * feed
        # Radial Force = 0 ?
        # No Helical Interpolation

        diameter = endmill.shape.get_diameter()
        fc.woc.v = diameter
        fc.woc.set_limit(diameter)
        fc.effective_diameter.v = diameter
        fc.engagement_angle.v = 360
        fc.engagement_angle.max = 360
        fc.engagement_angle.set_limit(360)

    @classmethod
    def get_overlap(cls, endmill, doc, woc):
        return math.pi*math.pow(endmill.shape.get_diameter()/2, 2)

    @classmethod
    def get_lead_angle_deflection_factors(cls, doc, woc, diameter):
        return 0, 1 # radial factor, axial factor

"""
class Turning(Operation):   # unsupported for now
    @classmethod
    def label(cls):
        return translate('btl', 'Turning')

    @classmethod
    def optimize_cut(cls, fc, endmill, material):
        # TODO: Turning
        # ------------------------
        # DIAMETER = workpiece diameter
        # TEETH = 1
        # CHIPLOAD? = ?    radial depth?
        # DOC? = ?         irrelevant?
        # WOC? = ?         IPR?
        # MRR = (chipload * rpm) * DOC * Diameter
        # Radial Force = 0 ?
        # No Helical Interpolation
"""

#class Parting(Operation):   # unsupported for now
#    label = 'Parting'

operations = [c for c in locals().values()
              if inspect.isclass(c) and issubclass(c, Operation) and c != Operation]
