"""
Alignment and snapping logic for the Editor Scene.
"""

from typing import List, Tuple, Optional
from PySide6.QtCore import Qt, QLineF
from PySide6.QtGui import QPen, QColor, QPainter

class AlignmentManager:
    """
    Manages grid snapping and alignment guides.
    """
    def __init__(self) -> None:
        """Initialize alignment settings."""
        self.snap_enabled: bool = True
        self.grid_size: int = 10
        self.guide_lines: List[QLineF] = []

    def check_alignment(self, moving_item, all_items: Optional[List] = None) -> None:
        """
        Check for alignments with other items and create guides.

        Args:
            moving_item (QGraphicsItem): The item being moved.
            all_items (List, optional): All other items in the scene.
        """
        if all_items is None:
            scene = moving_item.scene()
            if not scene:
                return
            all_items = scene.items()
            
        self.guide_lines = []
        if not self.snap_enabled:
            return

        m_rect = moving_item.sceneBoundingRect()
        threshold = 2.0

        for other in all_items:
            if other == moving_item or not hasattr(other, 'model'):
                continue
            
            o_rect = other.sceneBoundingRect()
            
            # X Alignment (Vertical Guides)
            if abs(m_rect.left() - o_rect.left()) < threshold:
                self.guide_lines.append(QLineF(o_rect.left(), -10000, o_rect.left(), 10000))
            if abs(m_rect.right() - o_rect.right()) < threshold:
                self.guide_lines.append(QLineF(o_rect.right(), -10000, o_rect.right(), 10000))
            if abs(m_rect.center().x() - o_rect.center().x()) < threshold:
                self.guide_lines.append(QLineF(o_rect.center().x(), -10000, o_rect.center().x(), 10000))

            # Y Alignment (Horizontal Guides)
            if abs(m_rect.top() - o_rect.top()) < threshold:
                self.guide_lines.append(QLineF(-10000, o_rect.top(), 10000, o_rect.top()))
            if abs(m_rect.bottom() - o_rect.bottom()) < threshold:
                self.guide_lines.append(QLineF(-10000, o_rect.bottom(), 10000, o_rect.bottom()))

    def draw_guides(self, painter: QPainter) -> None:
        """
        Draw active alignment guides in red.

        Args:
            painter (QPainter): The painter to use.
        """
        if not self.guide_lines:
            return
            
        painter.save()
        pen = QPen(QColor(255, 50, 50, 180))  # Red color for better visibility
        pen.setWidthF(0.5)
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.drawLines(self.guide_lines)
        painter.restore()

    def snap_value(self, value: float) -> float:
        """
        Snap a coordinate value to the grid.

        Args:
            value (float): Input value.

        Returns:
            float: Snapped value.
        """
        if not self.snap_enabled:
            return value
        return round(value / self.grid_size) * self.grid_size
