"""
Interactive handles for Line elements.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPen, QBrush

class LineHandle(QGraphicsRectItem):
    """
    Small box at the end of a line that allows resizing.
    """
    SIZE = 6.0
    START = 0
    END = 1
    
    def __init__(self, position_type: int, parent: QGraphicsItem) -> None:
        """
        Initialize handle.

        Args:
            position_type (int): START or END.
            parent (LineEditorItem): The line being controlled.
        """
        super().__init__(-self.SIZE/2, -self.SIZE/2, self.SIZE, self.SIZE, parent)
        self._type = position_type
        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.white))
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CrossCursor)
    
    def mouseMoveEvent(self, event) -> None:
        """Handle dragging and grid snapping."""
        new_scene_pos = self.mapToScene(event.pos())
        
        # Grid Snap
        if hasattr(self.scene(), 'alignment') and self.scene().alignment.snap_enabled:
             grid = self.scene().alignment.grid_size
             new_scene_pos = QPointF(
                 round(new_scene_pos.x() / grid) * grid,
                 round(new_scene_pos.y() / grid) * grid
             )
        
        parent = self.parentItem()
        new_pos = parent.mapFromScene(new_scene_pos)
        self.setPos(new_pos)
        parent.update_line_from_handles()
