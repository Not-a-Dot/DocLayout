"""
Ruler Widget.
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QSize

class Ruler(QWidget):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, orientation: int, view):
        super().__init__()
        self._orientation = orientation
        self._view = view
        self._unit_size = 3.78 * 5.0 # Approx pixels per cm (10mm) at scale 1.0 (assuming 96dpi/3.78 scale base)
        # Actually, we should map scene coordinates to viewport.
        # We need to listen to view updates.
        
        self.setFont(QFont("Arial", 8))
        if orientation == self.HORIZONTAL:
            self.setFixedHeight(25)
        else:
            self.setFixedWidth(25)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
        palette = self.palette()
        from PySide6.QtGui import QPalette
        painter.fillRect(rect, palette.color(QPalette.Window).lighter(105))
        painter.setPen(palette.color(QPalette.WindowText))

        # We need to map 0,0 of scene to widget coords
        # Viewport 0,0 maps to Scene ?
        
        # Simpler approach: Iterate scene coords from view top-left to bottom-right
        view_rect = self._view.viewport().rect()
        scene_top_left = self._view.mapToScene(view_rect.topLeft())
        scene_bottom_right = self._view.mapToScene(view_rect.bottomRight())
        
        start_mm = scene_top_left.x() if self._orientation == self.HORIZONTAL else scene_top_left.y()
        end_mm = scene_bottom_right.x() if self._orientation == self.HORIZONTAL else scene_bottom_right.y()
        
        # Round start to nearest 10mm
        start_tick = (int(start_mm) // 10) * 10
        
        tick_val = start_tick
        while tick_val <= end_mm:
            # Map tick val (mm) back to viewport pixels
            if self._orientation == self.HORIZONTAL:
                scene_pt = self._view.mapFromScene(tick_val, 0)
                px = scene_pt.x()
                if px >= -10 and px <= rect.width() + 10:
                    painter.drawLine(px, 15, px, 25)
                    painter.drawText(px + 2, 12, str(int(tick_val/10))) # Show CM
            else:
                scene_pt = self._view.mapFromScene(0, tick_val)
                py = scene_pt.y()
                if py >= -10 and py <= rect.height() + 10:
                    painter.drawLine(15, py, 25, py)
                    painter.drawText(2, py + 12, str(int(tick_val/10))) # Show CM
            
            tick_val += 10 # 10mm increments
