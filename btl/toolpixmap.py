import math
import matplotlib.pyplot as plt
import numpy as np
from PySide.QtCore import Qt, QPoint
from PySide.QtGui import QImage, QPainter, QColor, QPainterPath

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
        self.S = lambda v: round(v*self.scale)
        self.image = QImage(self.size, self.size, QImage.Format_ARGB32)
        self.image.fill(Qt.transparent)
        self.painter = QPainter(self.image)
        self.painter.setPen(Qt.NoPen)
        self.painter.setRenderHint(QPainter.Antialiasing, False)
        # Note: QPainter.scale() has a bug, the scale is applied with rounding
        # errors. To circumvent this, I had to scale everything myself :-(.
        #scalingTransform = QTransform(self.scale-0.01, 0, 0, self.scale-0.01, 0, 0)
        #self.painter.setTransform(scalingTransform)
        #self.painter.scale(self.scale, self.scale)

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

    def render_engagement(self, doc=0, woc=0):
        # Create the mask image
        mask_image = QImage(self.size, self.size, QImage.Format_ARGB32)
        mask_image.fill(QColor(0, 0, 0, 0).rgba())
        mask_painter = QPainter(mask_image)
    
        center = self.size/2/self.scale
        mask_painter.setBrush(QColor(255, 0, 0, 255))
        mask_painter.drawRect(self.S(center+self.diameter/2-woc),
                              self.S(self.stickout-doc),
                              self.S(woc), self.S(doc))
        mask_painter.end()
    
        # Make a copy of our internal surface (assuming it is a QImage).
        surface = self.image.copy()
    
        # Apply the mask to the copy.
        painter = QPainter(surface)
        painter.setCompositionMode(QPainter.CompositionMode_SourceAtop)
        painter.drawImage(0, 0, mask_image)
        painter.end()
    
        # Return the image data as a QByteArray
        return surface.bits().tobytes()

    def show_engagement(self, doc=0, woc=0):
        data = self.render_engagement(doc, woc)
        data = self.image.bits().tobytes()
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
        view = self.image.bits()
        stride = self.image.bytesPerLine()
        pixel_area = (1 / self.scale) ** 2
        xmax = 0
        for y in range(self.size - 1, -1, -1):
            lastArea = 0
            for x in range(self.size - 1, -1, -1):
                offset = (y * stride) + (x * 4)
                alpha = view[offset + 3]
                if alpha > 0:
                    lastArea += pixel_area
                    xmax = max(x, xmax)  # Record the widest point that we found a red pixel
                # Set the overlap for this DOC/WOC combo
                self.area[x, y] = lastArea + self.area[x, y + 1]
    
            # Assign the max diameter of the tool overlapping the workpiece as
            # the effective diameter.
            self.diameter_list[y] = 2 * ((xmax + 1) - (self.size / 2)) / self.scale
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
        lowY = int(max(0, math.floor(lowY * scale)))
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
        lowY = int(max(0, math.floor(lowY * scale)))

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
        self.painter.setBrush(QColor(204, 204, 204, 255))
        self.painter.drawRect((center-self.shank_d/2)*self.scale,
                              0,
                              self.shank_d*self.scale,
                              shaft_length*self.scale)
    
        # Draw the cutting edge area in dark grey.
        self.painter.setBrush(QColor(26, 26, 26, 255))
        self.painter.drawRect((center-self.diameter/2)*self.scale,
                              shaft_length*self.scale,
                              self.diameter*self.scale,
                              self.cutting_edge*self.scale)
    
        # End the painting process
        self.painter.end()

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


class ChamferPixmap(ToolPixmap):
    def __init__(self,
                 stickout,        # mm
                 shank_diameter,  # mm
                 diameter,        # mm
                 brim,            # mm
                 radius):         # mm
        super(ChamferPixmap, self).__init__(stickout, shank_diameter, diameter)
        self.brim = brim
        self.radius = radius
        self.tip_w = max(0, self.diameter-2*radius)
        self.paint()

    def paint(self):
        # Draw the shank in light grey.
        center_x = self.size/2/self.scale
        shaft_length = self.stickout-self.brim-self.radius
        self.painter.fillRect(self.S(center_x-self.shank_d/2),
                              0,
                              self.S(self.shank_d),
                              self.S(shaft_length),
                              QColor(204, 204, 204))

        # Draw the brim area in dark grey.
        self.painter.fillRect(self.S(center_x-self.diameter/2),
                              self.S(shaft_length),
                              self.S(self.diameter),
                              self.S(self.brim),
                              QColor(26, 26, 26))

        # Draw the tip in medium grey.
        self.painter.fillRect(self.S(center_x-self.tip_w/2),
                              self.S(self.stickout-self.radius),
                              self.S(self.tip_w),
                              self.S(self.radius),
                              QColor(128, 128, 128))

        # Left corner.
        arc_center_x = center_x-self.diameter/2
        arc_center_y = self.stickout
        path = QPainterPath()
        path.moveTo(QPoint(self.S(arc_center_x), self.S(self.stickout-self.radius)))
        path.arcTo(self.S(arc_center_x-self.radius),
                   self.S(arc_center_y-self.radius),
                   self.S(2*self.radius),
                   self.S(2*self.radius),
                   90, -90)
        path.lineTo(QPoint(self.S(arc_center_x+self.radius), self.S(self.stickout))) # Fend off some rounding error in Qt
        path.lineTo(QPoint(self.S(arc_center_x+self.radius), self.S(self.stickout-self.radius)))
        path.closeSubpath()
        self.painter.fillPath(path, QColor(77, 77, 77, 255))

        # Right corner.
        arc_center_x = center_x+self.diameter/2
        path = QPainterPath()
        path.moveTo(QPoint(self.S(arc_center_x), self.S(self.stickout-self.radius)))
        path.arcTo(self.S(arc_center_x-self.radius),
                   self.S(arc_center_y-self.radius),
                   self.S(2*self.radius),
                   self.S(2*self.radius),
                   90, 90)
        path.lineTo(QPoint(self.S(arc_center_x-self.radius), self.S(self.stickout))) # Fend off some rounding error in Qt
        path.lineTo(QPoint(self.S(arc_center_x-self.radius), self.S(self.stickout-self.radius)))
        path.closeSubpath()
        self.painter.fillPath(path, QColor(77, 77, 77, 255))


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
        center_x = self.size/2/self.scale
        shaft_length = self.stickout-self.cutting_edge
        self.painter.fillRect(self.S(center_x-self.shank_d/2),
                              0,
                              self.S(self.shank_d),
                              self.S(shaft_length),
                              QColor(204, 204, 204))

        # Draw the cutting edge area in dark grey.
        self.painter.fillRect(self.S(center_x-self.diameter/2),
                              self.S(shaft_length),
                              self.S(self.diameter),
                              self.S(self.cutting_edge-self.tip_h),
                              QColor(26, 26, 26))

        # Draw the tip in medium grey.
        self.painter.fillRect(self.S(center_x-self.tip_w/2),
                              self.S(self.stickout-self.tip_h),
                              self.S(self.tip_w),
                              self.S(self.tip_h),
                              QColor(128, 128, 128))

        # Draw the corner radius in yet another grey.
        # Left corner.
        arc_center_x = center_x - self.diameter/2 + self.corner_radius
        arc_center_y = self.stickout-self.corner_radius
        self.painter.setBrush(QColor(77, 77, 77))
        self.painter.drawPie(self.S(arc_center_x-self.corner_radius),
                             self.S(arc_center_y-self.corner_radius),
                             self.S(self.corner_radius*2),
                             self.S(self.corner_radius*2),
                             180*16, 90*16)

        # Right corner.
        arc_center_x = center_x + self.diameter/2 - self.corner_radius
        self.painter.drawPie(self.S(arc_center_x-self.corner_radius),
                             self.S(arc_center_y-self.corner_radius),
                             self.S(self.corner_radius*2),
                             self.S(self.corner_radius*2),
                             270*16, 90*16)


class VBitPixmap(ToolPixmap):
    def __init__(self,
                 stickout,        # mm
                 shank_diameter,  # mm
                 diameter,        # mm
                 brim,            # mm
                 lead_angle=0,    # degrees (0-90)
                 tip_w=0):        # mm
        super(VBitPixmap, self).__init__(stickout, shank_diameter, diameter)
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
        center_x = self.size/2/self.scale
        shaft_length = self.stickout-self.brim-self.tip_h
        self.painter.fillRect(self.S(center_x-self.shank_d/2),
                              0,
                              self.S(self.shank_d),
                              self.S(shaft_length),
                              QColor(204, 204, 204))

        # Draw the brim area in dark grey.
        # The brim is the length of the area between the angled cutter and the
        # shaft.
        self.painter.fillRect(self.S(center_x-self.diameter/2),
                              self.S(shaft_length),
                              self.S(self.diameter),
                              self.S(self.brim),
                              QColor(26, 26, 26))

        # Draw the tip in medium grey.
        self.painter.fillRect(self.S(center_x-self.tip_w/2),
                              self.S(self.stickout-self.tip_h),
                              self.S(self.tip_w),
                              self.S(self.tip_h),
                              QColor(128, 128, 128))

        if self.lead_angle < 90:
            path = QPainterPath()
            path.moveTo(self.S(center_x-self.tip_upper_w/2), self.S(self.stickout-self.tip_h))
            path.lineTo(self.S(center_x-self.tip_w/2), self.S(self.stickout))
            path.lineTo(self.S(center_x+self.tip_w/2), self.S(self.stickout))
            path.lineTo(self.S(center_x+self.tip_upper_w/2), self.S(self.stickout-self.tip_h))
            path.closeSubpath()
    
            self.painter.setBrush(QColor(77, 77, 77, 255))  # Set fill color (medium grey)
            self.painter.setPen(Qt.NoPen)  # Set the pen width to zero (no border)
            self.painter.drawPath(path)
