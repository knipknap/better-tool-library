import math
import cairo
import matplotlib.pyplot as plt
import numpy as np

class ToolPixmap(object):
    def __init__(self,
                 diameter,        # mm
                 shank_diameter,  # mm
                 stickout,        # mm
                 cutting_edge,    # mm
                 corner_radius=0, # mm
                 lead_angle=0,    # degrees (0-90)
                 tip_w=0):        # mm
        self.diameter = diameter
        self.shank_d = shank_diameter
        self.stickout = stickout
        self.cutting_edge = cutting_edge

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

        # Draw the cutting edge area in dark grey.
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
