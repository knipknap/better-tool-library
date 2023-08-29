import sys
import numpy as np
from scipy.interpolate import CubicSpline
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QVBoxLayout

def remove_colliding_points(points):
    unique_points = {}
    for point in points:
        if point.x() not in unique_points:
            unique_points[point.x()] = point
    return unique_points.values()

class CurveWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.points = [
            QPoint(50, 200),
            QPoint(150, 50),
            QPoint(250, 200),
            QPoint(450, 200)
        ]
        self.selected_point = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.black, 2))

        # Draw original points
        painter.setBrush(Qt.red)
        for point in self.points:
            painter.drawEllipse(point, 5, 5)

        # Fit and draw the curve
        points = remove_colliding_points(self.points)
        points = sorted(points, key=lambda p: p.x())
        x_values = [point.x() for point in points]
        y_values = [point.y() for point in points]

        # Fit and draw the curve
        cubic_spline = CubicSpline(x_values, y_values)
        xs = np.linspace(min(x_values), max(x_values), 100)
        ys = cubic_spline(xs)

        for i in range(len(xs) - 1):
            x1, y1 = int(xs[i]), int(ys[i])
            x2, y2 = int(xs[i + 1]), int(ys[i + 1])
            painter.drawLine(x1, y1, x2, y2)

        painter.end()

    def mousePressEvent(self, event):
        # Check if an existing point was clicked.
        pos = event.pos()
        for point in self.points:
            if (point-pos).manhattanLength() < 10:
                selected_point = point
                break
        else:
            selected_point = None

        if event.button() == Qt.LeftButton:
            if selected_point is not None:
                self.selected_point = selected_point
                return

            # Create a new point and select it.
            self.points.append(pos)
            self.selected_point = pos
            self.update()
            return

        if event.button() == Qt.RightButton and selected_point:
            idx = self.points.index(selected_point)
            self.points.pop(idx)
            self.update()
            return

    def mouseMoveEvent(self, event):
        pos = event.pos()
        if self.selected_point is not None:
            self.selected_point.setX(pos.x())
            self.selected_point.setY(pos.y())
            self.update()

    def mouseReleaseEvent(self, event):
        self.selected_point = None

if __name__ == '__main__':
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            self.init_ui()

        def init_ui(self):
            self.setWindowTitle('Curve Fitting')
            self.setGeometry(100, 100, 500, 250)

            layout = QVBoxLayout()
            self.curve_widget = CurveFittingWidget()
            layout.addWidget(self.curve_widget)

            central_widget = QWidget()
            central_widget.setLayout(layout)
            self.setCentralWidget(central_widget)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
