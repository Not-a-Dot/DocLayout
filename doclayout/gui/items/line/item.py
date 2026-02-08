"""
Line editor item implementation.
"""

import math
from PySide6.QtWidgets import QGraphicsLineItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QColor, QPolygonF

from ..base import BaseEditorItem
from .handle import LineHandle
from .properties import LinePropertiesWidget

class LineEditorItem(BaseEditorItem, QGraphicsLineItem):
    """
    A graphics item representing a line with optional arrowheads.
    """
    def __init__(self, model) -> None:
        """Initialize line from model x,y (start) and props x2,y2 (end)."""
        x1, y1 = model.x, model.y
        x2 = model.props.get("x2", x1 + 20)
        y2 = model.props.get("y2", y1)
        
        QGraphicsLineItem.__init__(self, 0, 0, x2 - x1, y2 - y1)
        BaseEditorItem.__init__(self, model)
        
        self.setPos(x1, y1)
        self.start_handle = LineHandle(LineHandle.START, self)
        self.start_handle.setPos(0, 0)
        self.end_handle = LineHandle(LineHandle.END, self)
        self.end_handle.setPos(x2 - x1, y2 - y1)
        
        self.start_handle.setVisible(False)
        self.end_handle.setVisible(False)
        self.update_pen()

    def paint(self, painter, option, widget) -> None:
        """Draw the line and arrowheads."""
        super().paint(painter, option, widget)
        
        start_arrow = self.model.props.get("start_arrow", "None")
        end_arrow = self.model.props.get("end_arrow", "None")
        
        if start_arrow != "None" or end_arrow != "None":
            line = self.line()
            p1, p2 = line.p1(), line.p2()
            angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            arrow_size = float(self.model.props.get("stroke_width", 2.0)) * 3.0
            
            painter.save()
            painter.setBrush(self.pen().color())
            
            if start_arrow == "Triangle":
                self._draw_arrow(painter, p1, angle + math.pi, arrow_size)
            if end_arrow == "Triangle":
                self._draw_arrow(painter, p2, angle, arrow_size)
            painter.restore()

        self.paint_lock_icons(painter)

    def _draw_arrow(self, painter, point: QPointF, angle: float, size: float) -> None:
        p1 = point + QPointF(math.cos(angle - math.pi + math.pi/6) * size,
                             math.sin(angle - math.pi + math.pi/6) * size)
        p2 = point + QPointF(math.cos(angle - math.pi - math.pi/6) * size,
                             math.sin(angle - math.pi - math.pi/6) * size)
        painter.drawPolygon(QPolygonF([point, p1, p2]))

    def update_handles(self, selected: bool = None) -> None:
        """Toggle handle visibility."""
        if not hasattr(self, 'start_handle'):
            return
        if selected is None: selected = self.isSelected()
        self.start_handle.setVisible(selected)
        self.end_handle.setVisible(selected)

    def update_pen(self) -> None:
        """Sync pen styling from model."""
        from doclayout.core.geometry import PT_TO_MM
        props = self.model.props
        width_mm = float(props.get("stroke_width", 2.0)) * PT_TO_MM
        color = QColor(props.get("stroke_color", "#000000"))
        style = getattr(Qt, f"{props.get('stroke_style', 'Solid')}Line", Qt.SolidLine)
        cap = getattr(Qt, f"{props.get('stroke_cap', 'Square')}Cap", Qt.SquareCap)
        
        self.setPen(QPen(color, width_mm, style, cap))
        self.update()

    def update_line_from_handles(self) -> None:
        """Called by handles to update line geometry and model."""
        p1, p2 = self.start_handle.pos(), self.end_handle.pos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())
        
        scene_p1, scene_p2 = self.mapToScene(p1), self.mapToScene(p2)
        self.model.x, self.model.y = scene_p1.x(), scene_p1.y()
        self.model.props.update({"x2": scene_p2.x(), "y2": scene_p2.y()})
        self.model.width = abs(scene_p2.x() - scene_p1.x())
        self.model.height = abs(scene_p2.y() - scene_p1.y())

        if self.scene() and hasattr(self.scene(), "itemMoved"):
             self.scene().itemMoved.emit(self)

    def itemChange(self, change, value) -> any:
        """Handle selection and position changes."""
        if change == QGraphicsItem.ItemSelectedChange:
             self.update_handles(selected=bool(value))
        
        if change == QGraphicsItem.ItemPositionChange:
             new_pos = super().itemChange(change, value)
             old_pos = self.pos()
             line = self.line()
             self.model.props.update({
                 "x2": new_pos.x() + line.dx(),
                 "y2": new_pos.y() + line.dy()
             })
             return new_pos

        return super().itemChange(change, value)

    def create_properties_widget(self, parent) -> LinePropertiesWidget:
        return LinePropertiesWidget(self, parent)

    def get_bindable_properties(self) -> list:
        return ["stroke_color", "stroke_width", "stroke_style", "stroke_cap"]
