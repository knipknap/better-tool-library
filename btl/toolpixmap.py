import math
import cairo
import matplotlib.pyplot as plt
import numpy as np

class ToolPixmap(object):
    def __init__(self,
                 stickout,        # mm
                 shank_diameter,  # mm
                 diameter):       # mm
        self.stickout = stickout
        self.shank_d = shank_diameter
        self.diameter = diameter

        # Prepare the surface.
        self.size = 500
        self.scale = self.size/max(self.diameter, max(self.shank_d, self.stickout))
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.size, self.size)
        self.ctx = cairo.Context(self.surface)
        self.ctx.set_antialias(cairo.ANTIALIAS_NONE)
        self.ctx.scale(self.scale, self.scale)

        # self.diameter_list is a list containing the diameter of the tool in the
        # given y position.
        # self.area is an array containing for each pixel of the surface
        # the overlap at that position of the tool.
        # Put differently: If the pixel at x/y contains the number 120, that
        # means: if the WOC reaches this pixel, then the overlap is 120.
        self.initialized = False
        self.diameter_list = [0]*self.size
        self.area = np.zeros((self.size+1, self.size+1))

    def paint(self):
        """
        Draws the end mill profile to a Cairo surface.
        """
        raise NotImplementedError

    def show_engagement(self, doc=0, woc=0):
        mask_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.size, self.size)
        mask_ctx = cairo.Context(mask_surface)
        mask_ctx.scale(self.scale, self.scale)

        center = self.size/2/self.scale
        mask_ctx.set_source_rgba(0, 0, 0, 0)
        mask_ctx.paint()
        mask_ctx.rectangle(center+self.diameter/2-woc, self.stickout-doc, woc, doc)
        mask_ctx.set_source_rgba(1, 1, 1, 1)
        mask_ctx.fill()

        self.ctx.identity_matrix() # see https://stackoverflow.com/a/21650227
        self.ctx.set_operator(cairo.Operator.ATOP)
        self.ctx.set_source_rgba(1, 0, 0, 1)
        self.ctx.mask_surface(mask_surface, 0, 0)

        data = self.surface.get_data()
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
                self.area[x, y] = lastArea+self.area[x, y+1]

            # Assign the max diameter of the tool overlapping the workpiece as
            # the effective diameter.
            self.diameter_list[y] = 2 * ((xmax+1) - (self.size/2))/self.scale
        self.initialized = True

    def get_effective_diameter_from_doc(self, doc):
        """
        Returns the tool diameter at the given depth of cut.
        """
        doc = max(0.000001, doc)
        if not self.initialized:
            self._create_width_and_overlap_array()
        scale = self.scale
        lowY = self.stickout - doc
        lowY = int(math.floor(lowY * scale))
        return self.diameter_list[lowY]

    def get_overlap_from_woc(self, doc, woc):
        """
        Returns overlap in mm²
        """
        doc = max(0.000001, doc)
        woc = max(0.000001, woc)
        if not self.initialized:
            self._create_width_and_overlap_array()

        # Select appropriate integration limits
        scale = self.scale
        pixelArea = 1 / (scale * scale)

        # Calculate lowest X position.
        lowX = self.diameter/2 - woc
        lowX = int(max(0, math.floor(lowX*scale) + self.size/2))

        # Calculate lowest Y position.
        lowY = self.stickout - doc
        lowY = int(math.floor(lowY * scale))

        return self.area[lowX][lowY]


class EndmillPixmap(ToolPixmap):
    def __init__(self,
                 stickout,        # mm
                 shank_diameter,  # mm
                 diameter,        # mm
                 cutting_edge):   # mm
        super(EndmillPixmap, self).__init__(stickout, shank_diameter, diameter)
        self.cutting_edge = cutting_edge
        self.paint()

    def paint(self):
        # Draw the shank in light grey.
        center = self.size/2/self.scale
        shaft_length = self.stickout-self.cutting_edge
        self.ctx.rectangle(center-self.shank_d/2, 0, self.shank_d, shaft_length)
        self.ctx.set_source_rgba(.8, .8, .8, 1)
        self.ctx.fill()

        # Draw the cutting edge area in dark grey.
        self.ctx.rectangle(center-self.diameter/2,
                      shaft_length,
                      self.diameter,
                      self.cutting_edge)
        self.ctx.set_source_rgba(.1, .1, .1, 1)
        self.ctx.fill()

    def get_effective_diameter_from_doc(self, doc):
        """
        Returns the tool diameter at the given depth of cut.
        """
        return self.diameter

    def get_overlap_from_woc(self, doc, woc):
        """
        Returns overlap in mm²
        """
        return woc*doc

class BullnosePixmap(ToolPixmap):
    def __init__(self,
                 stickout,         # mm
                 shank_diameter,   # mm
                 diameter,         # mm
                 cutting_edge,     # mm
                 corner_radius=0): # mm
        super(BullnosePixmap, self).__init__(stickout, shank_diameter, diameter)
        self.cutting_edge = cutting_edge

        self.lead_angle = None
        self.corner_radius = corner_radius
        self.tip_w = max(0, self.diameter-2*abs(corner_radius))
        self.tip_h = abs(corner_radius)

        self.paint()

    def paint(self):
        # Draw the shank in light grey.
        center = self.size/2/self.scale
        shaft_length = self.stickout-self.cutting_edge
        self.ctx.rectangle(center-self.shank_d/2, 0, self.shank_d, shaft_length)
        self.ctx.set_source_rgba(.8, .8, .8, 1)
        self.ctx.fill()

        # Draw the cutting edge area in dark grey. Note that we draw a rectangle
        # enclosing the entire area; we will cut away angles/corners later.
        self.ctx.rectangle(center-self.diameter/2,
                      shaft_length,
                      self.diameter,
                      self.cutting_edge-self.tip_h)
        self.ctx.set_source_rgba(.1, .1, .1, 1)
        self.ctx.fill()

        # Draw the tip in medium grey.
        self.ctx.rectangle(center-self.tip_w/2,
                      self.stickout-self.tip_h,
                      self.tip_w,
                      self.tip_h)
        self.ctx.set_source_rgba(.5, .5, .5, 1)
        self.ctx.fill()

        # Draw the corner radius in yet another grey.
        if self.corner_radius and self.corner_radius > 0:
            # Left corner.
            arc_center_x = center-self.diameter/2+self.corner_radius
            arc_center_y = self.stickout-self.corner_radius
            angle_start = 90*math.pi/180
            angle_end = 180*math.pi/180
            self.ctx.move_to(arc_center_x, arc_center_y)
            self.ctx.arc(arc_center_x, arc_center_y, self.corner_radius, angle_start, angle_end)
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.fill()

            # Right corner.
            arc_center_x = center+self.diameter/2-self.corner_radius
            angle_start = 0*math.pi/180
            angle_end = 90*math.pi/180
            self.ctx.move_to(arc_center_x, arc_center_y)
            self.ctx.arc(arc_center_x, arc_center_y, self.corner_radius, angle_start, angle_end)
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.fill()

        elif self.corner_radius and self.corner_radius < 0:
            # Draw a rectangle covering the whole diameter first; we will "subtract"
            # the arcs in the next step.
            abs_radius = abs(self.corner_radius)
            self.ctx.rectangle(center-self.diameter/2, self.stickout-self.tip_h, abs_radius, abs_radius)
            self.ctx.rectangle(center+self.diameter/2-abs_radius, self.stickout-self.tip_h, abs_radius, abs_radius)
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.fill()

            # Left corner.
            arc_center_x = center-self.diameter/2
            arc_center_y = self.stickout
            angle_start = 270*math.pi/180
            angle_end = 0*math.pi/180
            self.ctx.move_to(arc_center_x, arc_center_y)
            self.ctx.arc(arc_center_x, arc_center_y, abs_radius, angle_start, angle_end)
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.ctx.fill()

            # Right corner.
            arc_center_x = center+self.diameter/2
            angle_start = 180*math.pi/180
            angle_end = 270*math.pi/180
            self.ctx.move_to(arc_center_x, arc_center_y)
            self.ctx.arc(arc_center_x, arc_center_y, abs_radius, angle_start, angle_end)
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.fill()


class ChamferPixmap(ToolPixmap):
    def __init__(self,
                 stickout,        # mm
                 shank_diameter,  # mm
                 diameter,        # mm
                 brim,            # mm
                 lead_angle=0,    # degrees (0-90)
                 tip_w=0):        # mm
        super(ChamferPixmap, self).__init__(stickout, shank_diameter, diameter)
        self.brim = brim
        self.lead_angle = lead_angle
        self.tip_w = tip_w
        self.tip_upper_w = diameter
        self.tip_h = ((diameter-tip_w)/2) / math.tan(math.radians(lead_angle))

        self.paint()

    def paint(self):
        """
        Draws the end mill profile to a Cairo surface.
        """
        # Draw the shank in light grey.
        center = self.size/2/self.scale
        shaft_length = self.stickout-self.brim-self.tip_h
        self.ctx.rectangle(center-self.shank_d/2, 0, self.shank_d, shaft_length)
        self.ctx.set_source_rgba(.8, .8, .8, 1)
        self.ctx.fill()

        # Draw the brim area in dark grey.
        # The brim is the length of the area between the angled cutter and the
        # shaft.
        self.ctx.rectangle(center-self.diameter/2,
                      shaft_length,
                      self.diameter,
                      self.brim)
        self.ctx.set_source_rgba(.1, .1, .1, 1)
        self.ctx.fill()

        # Draw the tip in medium grey.
        self.ctx.rectangle(center-self.tip_w/2,
                      self.stickout-self.tip_h,
                      self.tip_w,
                      self.tip_h)
        self.ctx.set_source_rgba(.5, .5, .5, 1)
        self.ctx.fill()

        if self.lead_angle < 90:
            self.ctx.move_to(center-self.tip_upper_w/2, self.stickout-self.tip_h)
            self.ctx.line_to(center-self.tip_w/2, self.stickout)
            self.ctx.line_to(center+self.tip_w/2, self.stickout)
            self.ctx.line_to(center+self.tip_upper_w/2, self.stickout-self.tip_h)
            self.ctx.close_path()
            self.ctx.set_source_rgba(.3, .3, .3, 1)
            self.ctx.fill()
