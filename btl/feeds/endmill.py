import math
import cairo
import matplotlib.pyplot as plt
import numpy as np
from . import material
from .const import Operation
from .util import cantilever_deflect_endload, cantilever_deflect_uniload

class AbstractEndmill(object):
    elasticity = 1 # Modulus of elasticity (N/mm²)

    def __init__(self,
                 diameter,        # mm
                 shank_diameter,  # mm
                 stickout,        # mm
                 cutting_edge,    # mm
                 corner_radius=0, # mm
                 lead_angle=0,    # degrees (0-90)
                 flutes=1,        # quantity
                 tip_w=0,         # mm
                 chipload=None):  # mm. taken from material table if not provided
        self.diameter = diameter
        self.shank_d = shank_diameter
        self.stickout = stickout
        self.cutting_edge = cutting_edge
        self.flutes = flutes
        self.chipload = chipload

        # The following general shapes are supported:
        # - Rectangular
        # - With corner radius (positive or negative)
        # - Angled (with a lead angle)
        if corner_radius:
            self.lead_angle = None
            self.corner_radius = corner_radius
            self.tip_w = max(0, self.diameter-2*abs(corner_radius))
            self.tip_h = abs(corner_radius)
        elif lead_angle:
            self.lead_angle = lead_angle
            self.corner_radius = None
            self.tip_w = tip_w
            self.tip_upper_w = diameter
            self.tip_h = ((diameter-tip_w)/2) / math.tan(math.radians(lead))
            if self.tip_h > cutting_edge:
                self.tip_h = cutting_edge
                self.tip_upper_w = tip_w+cutting_edge*math.tan(math.radians(lead))
        else:
            self.lead_angle = None
            self.corner_radius = None
            self.tip_w = diameter
            self.tip_h = 0

        self.size = 500
        self.scale = self.size / max(self.diameter, max(self.shank_d, self.stickout))

        self.surface, self.ctx = self._create_pixmap()
        self.width_list, self.overlap = self._create_width_and_overlap_array()

    def get_speeds_for_material(self, thematerial):
        """
        This method is to be overwritten in subclasses and should return a dict
        mapping the operation to a tuple (min, max).
        """
        raise NotImplemented

    def get_speed_for_material(self, thematerial, operation=Operation.MILLING):
        """
        Returns the min_speed and max_speed in m/min.
        """
        speeds = self.get_speeds_for_material(thematerial)
        min_speed, max_speed = speeds.get(operation, (None, None))
        if not min_speed or not max_speed:
            return None, None
        return min_speed, max_speed

    def get_chipload_for_material(self, thematerial):
        """
        This method is to be overwritten in subclasses and should return a float
        containing the chipload.
        """
        raise NotImplemented

    def get_inertia(self):
        """
        Returns a tuple (solid_inertia, fluted_inertia) (mm⁴)
        """
        # Moment of inertia equation for a SOLID round beam (shank partion of the end mill)
        # https://en.wikipedia.org/wiki/List_of_area_moments_of_inertia
        solid_inertia = (math.pi/4) * (self.shank_d/2)**4

        # Estimated equivalent of the fluted portion = 80% of the fluted diameter
        # "Determination of the Equivalent Diameter of an End Mill Based on its Compliance", L. Kops, D.T. Vo
        fluted_inertia = (math.pi * ((self.diameter*0.8) / 2)**4) / 4

        return solid_inertia, fluted_inertia

    def get_deflection(self, doc, force):
        """
        Assuming a non-plunging/drilling operation, this function returns the deflection
        resulting from the engagement with the given force.

        Returns a single factor, the deflection.

        doc: mm
        force: N
        returns: mm
        """
        # "Metal Cutting Theory and Practice", By David A. Stephenson, John S. Agapiou, p362
        # "Structural modeling of end mills for form error and stability analysis", E.B. Kivanc, E. Budak
        shank_l = self.stickout-self.cutting_edge  # Length of the shank portion
        non_cutting = self.cutting_edge-doc # Length of the non-cutting flute portion
    
        solid_inertia, fluted_inertia = self.get_inertia()

        # Point load at the end of the shank,
        elasticity = self.elasticity*1000
        deflectionShank = cantilever_deflect_endload(force, shank_l, elasticity, solid_inertia)
        # Point load at the end of the fluted section that isn't currently cutting.
        deflectionNonCutting = cantilever_deflect_endload(force, non_cutting, elasticity, fluted_inertia)
        # Uniform load along fluted section in cut,
        deflectionCutting = cantilever_deflect_uniload(force, doc, elasticity, fluted_inertia)
    
        # NOTE: We ignore the contribution from the angle of deflection, which should be negligible for cutting purposes.
        return deflectionShank+deflectionNonCutting+deflectionCutting

    def get_max_deflection(self, force):
        """
        Returns the theoretical maximum deflection, were all forces acting
        on the tip of the endmill.

        force: N
        returns: mm
        """
        solid_inertia, fluted_inertia = self.get_inertia()
        return cantilever_deflect_endload(force,
                                          self.stickout,
                                          self.elasticity*1000,
                                          min(solid_inertia, fluted_inertia))

    def get_bend_limit(self, doc):
        """
        # Returns the maximum force to permanently bend the end mill at the given depth of cut.
        #
        # Yield is the STRESS at which the material deforms permanently
        # stress = F * L * Radius / I
        # F = (I * stress) / (r * l)
        # Returns force in N
        """
        # TODO: Estimate Yield for the fluted portion of the end mill separately
        yield_strength = self.yield_strength
        shank_l = self.stickout - self.cutting_edge
        non_cutting = self.cutting_edge - doc
        solid_inertia, fluted_inertia = self.get_inertia()
        return min((yield_strength*solid_inertia) / ((self.shank_d/2)* shank_l),
                   (yield_strength*fluted_inertia) / ((self.diameter/2) * (shank_l+non_cutting)))

    def get_twist_limit(self):
        """
        # Returns the maximum torque in Nm to shear the end mill
        # http://www.engineeringtoolbox.com/torsion-shafts-d_947.html
        """
        # TODO: Estimate Shear for the fluted portion of the end mill separately
        shear_strength = self.shear_strength
        solid_inertia, fluted_inertia = self.get_inertia()
        return min((shear_strength*solid_inertia) / (self.shank_d/2),
                   (shear_strength*fluted_inertia) / (self.diameter/2))

    def validate(self):
        if self.cutting_edge > self.stickout:
            raise AttributeError(f"Flute Length {self.cutting_edge} must be less than Stickout {self.stickout}")
        if abs(self.corner_radius or 0) > self.diameter/2:
            raise AttributeError(f"Corner Radius {self.corner_radius} must be less than End Mill Radius {self.diameter/2}")
        if self.corner_radius and self.lead_angle:
            raise AttributeError("Choose one: Lead Angle or Corner Radius")
        if self.lead_angle and (self.lead_angle < 0 or self.lead_angle > 90):
            raise AttributeError("Lead Angle must be 0 to 90 degrees")

    def _create_pixmap(self):
        # Draw the end mill profile
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.size, self.size)
        ctx = cairo.Context(surface)
        ctx.set_antialias(cairo.ANTIALIAS_NONE)
        ctx.scale(self.scale, self.scale)

        # Draw the shank in light grey.
        center = self.size/2/self.scale
        shaft_length = self.stickout-self.cutting_edge
        ctx.rectangle(center-self.shank_d/2, 0, self.shank_d, shaft_length)
        ctx.set_source_rgba(.8, .8, .8, 1)
        ctx.fill()

        # Draw the flutes in dark grey.
        ctx.rectangle(center-self.diameter/2,
                      shaft_length,
                      self.diameter,
                      self.cutting_edge-self.tip_h)
        ctx.set_source_rgba(.1, .1, .1, 1)
        ctx.fill()

        # Draw the tip in medium grey.
        ctx.rectangle(center-self.tip_w/2,
                      self.stickout-self.tip_h,
                      self.tip_w,
                      self.tip_h)
        ctx.set_source_rgba(.5, .5, .5, 1)
        ctx.fill()

        # Draw the corner radius in yet another grey.
        if self.corner_radius and self.corner_radius > 0:
            # Left corner.
            arc_center_x = center-self.diameter/2+self.corner_radius
            arc_center_y = self.stickout-self.corner_radius
            angle_start = 90*math.pi/180
            angle_end = 180*math.pi/180
            ctx.move_to(arc_center_x, arc_center_y)
            ctx.arc(arc_center_x, arc_center_y, self.corner_radius, angle_start, angle_end)
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.fill()

            # Right corner.
            arc_center_x = center+self.diameter/2-self.corner_radius
            angle_start = 0*math.pi/180
            angle_end = 90*math.pi/180
            ctx.move_to(arc_center_x, arc_center_y)
            ctx.arc(arc_center_x, arc_center_y, self.corner_radius, angle_start, angle_end)
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.fill()

        elif self.corner_radius and self.corner_radius < 0:
            # Draw a rectangle covering the whole diameter first; we will "subtract"
            # the arcs in the next step.
            abs_radius = abs(self.corner_radius)
            ctx.rectangle(center-self.diameter/2, self.stickout-self.tip_h, abs_radius, abs_radius)
            ctx.rectangle(center+self.diameter/2-abs_radius, self.stickout-self.tip_h, abs_radius, abs_radius)
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.fill()

            # Left corner.
            arc_center_x = center-self.diameter/2
            arc_center_y = self.stickout
            angle_start = 270*math.pi/180
            angle_end = 0*math.pi/180
            ctx.move_to(arc_center_x, arc_center_y)
            ctx.arc(arc_center_x, arc_center_y, abs_radius, angle_start, angle_end)
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.set_operator(cairo.OPERATOR_CLEAR)
            ctx.fill()

            # Right corner.
            arc_center_x = center+self.diameter/2
            angle_start = 180*math.pi/180
            angle_end = 270*math.pi/180
            ctx.move_to(arc_center_x, arc_center_y)
            ctx.arc(arc_center_x, arc_center_y, abs_radius, angle_start, angle_end)
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.fill()

        elif self.lead_angle and self.lead_angle < 90:
            ctx.move_to(center-self.tip_upper_w/2, self.stickout-self.tip_h)
            ctx.line_to(center-self.tip_w/2, self.stickout)
            ctx.line_to(center+self.tip_w/2, self.stickout)
            ctx.line_to(center+self.tip_upper_w/2, self.stickout-self.tip_h)
            ctx.close_path()
            ctx.set_source_rgba(.3, .3, .3, 1)
            ctx.fill()

        return surface, ctx

    def show_engagement(self, doc=0, woc=0):
        surface, ctx = self._create_pixmap()

        mask_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.size, self.size)
        mask_ctx = cairo.Context(mask_surface)
        mask_ctx.scale(self.scale, self.scale)

        center = self.size/2/self.scale
        mask_ctx.set_source_rgba(0, 0, 0, 0)
        mask_ctx.paint()
        mask_ctx.rectangle(center+self.diameter/2-woc, self.stickout-doc, woc, doc)
        mask_ctx.set_source_rgba(1, 1, 1, 1)
        mask_ctx.fill()

        ctx.identity_matrix() # see https://stackoverflow.com/a/21650227
        ctx.set_operator(cairo.Operator.ATOP)
        ctx.set_source_rgba(1, 0, 0, 1)
        ctx.mask_surface(mask_surface, 0, 0)

        data = surface.get_data()
        image_array = np.ndarray(shape=(self.size, self.size, 4), dtype=np.uint8, buffer=data)
        image_array = image_array[:, :, [2, 1, 0, 3]]  # Reorder bytes: BGRA to RGBA
        x_extend = self.size/self.scale
        plt.imshow(image_array,
                   aspect='equal',
                   extent=[-x_extend/2, x_extend/2, self.stickout, 0])
        plt.show()

    def _create_width_and_overlap_array(self):
        """
        Returns a tuple (width_list, overlap), where

        - width_list is a list containing the width for each row of the shape.
        - overlap is an array containing for each pixel the overlap at that position
          of the tool.
          Put differently: If the pixel at x/y contains the number 120, that means: if
          the WOC reaches this pixel, then the overlap is 120.
        """
        view = self.surface.get_data()
        stride = self.surface.get_stride()

        pixel_area = (1/self.scale)**2
        xmax = 0
        diameter_list = [0]*self.size
        area = np.zeros((self.size+1, self.size+1))
        for y in range(self.size-1, -1, -1):
            lastArea = 0
            for x in range(self.size-1, -1, -1):
                offset = (y * stride) + (x * 4)
                blue = view[offset + 0]
                green = view[offset + 1]
                red = view[offset + 2]
                alpha = view[offset + 3]
                if alpha > 0:
                    lastArea += pixel_area
                    xmax = max(x, xmax)  # Record the widest point that we found a red pixel
                # Set the overlap for this DOC/WOC combo
                area[x, y] = lastArea + area[x, y+1]

            # Assign the max diameter of the tool overlapping the workpiece as
            # the effective diameter.
            diameter_list[y] = 2 * ((xmax+1) - (self.size/2))/self.scale

        return diameter_list, area

    def get_effective_diameter_from_doc(self, doc):
        """
        Returns the tool diameter at the given depth of cut.
        """
        if not self.corner_radius and not self.lead_angle: # Square endmill
            return self.diameter
        scale = self.scale
        lowY = self.stickout - doc
        lowY = int(math.floor(lowY * scale))
        return self.width_list[lowY]

    def get_overlap_from_woc(self, doc, woc):
        """
        Returns overlap in mm²
        """
        if not self.corner_radius and not self.lead_angle: # Square endmill
            return woc*doc

        # Select appropriate integration limits
        scale = self.scale
        pixelArea = 1 / (scale * scale)

        # Calculate lowest X position.
        lowX = self.diameter/2 - woc
        lowX = int(max(0, math.floor(lowX*scale) + self.size/2))

        # Calculate lowest Y position.
        lowY = self.stickout - doc
        lowY = int(math.floor(lowY * scale))

        return self.overlap[lowX][lowY]

class HSSEndmill(AbstractEndmill):
    name = "HSS"
    elasticity = 0.186158 # mm⁴
    yield_strength = 1000 # MPa. https://material-properties.org/high-speed-steel-density-strength-hardness-melting-point/
    shear_strength = 1200 # MPa

    def get_speeds_for_material(self, thematerial):
        return thematerial.hss_speeds

    def get_chipload_for_material(self, thematerial):
        if self.chipload:
            return self.chipload
        return self.diameter/thematerial.hss_chipload_divisor

class CarbideEndmill(AbstractEndmill):
    name = "Carbide"
    elasticity = 0.517107 # mm⁴
    yield_strength = 330 # MPa  https://material-properties.org/tungsten-carbide-properties-application-price/
    shear_strength = 370 # MPa

    def get_speeds_for_material(self, thematerial):
        return thematerial.carbide_speeds

    def get_chipload_for_material(self, thematerial):
        if self.chipload:
            return self.chipload
        return self.diameter/thematerial.carbide_chipload_divisor
