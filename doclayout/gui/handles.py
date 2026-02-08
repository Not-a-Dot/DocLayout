"""
Resize Handle Graphics Item.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QCursor, QPainter

class ResizeHandle(QGraphicsRectItem):
    """
    A handle for resizing items.
    """
    SIZE = 2.0 # Smaller size for better aesthetics (mm)
    
    # Position constants
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_RIGHT = 2
    BOTTOM_LEFT = 3
    TOP = 4
    RIGHT = 5
    BOTTOM = 6
    LEFT = 7

    def __init__(self, position: int, parent: QGraphicsItem):
        super().__init__(0, 0, self.SIZE, self.SIZE, parent)
        self._position = position
        
        # Professional look: Semi-transparent White fill, Blue border
        self.setBrush(QBrush(QColor(255, 255, 255, 180)))
        self.setPen(QPen(QColor("#1a73e8"), 0.3)) # Google Blue
        
        self.setFlags(QGraphicsItem.ItemIsMovable) 
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        self.setCursor(self._get_cursor())
        self._update_position()

    def paint(self, painter, option, widget):
        """Draw as a professional square with antialiasing."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRect(self.rect())

    def _get_cursor(self):
        if self._position in (self.TOP_LEFT, self.BOTTOM_RIGHT):
            return QCursor(Qt.SizeFDiagCursor)
        elif self._position in (self.TOP_RIGHT, self.BOTTOM_LEFT):
            return QCursor(Qt.SizeBDiagCursor)
        elif self._position in (self.TOP, self.BOTTOM):
            return QCursor(Qt.SizeVerCursor)
        elif self._position in (self.LEFT, self.RIGHT):
            return QCursor(Qt.SizeHorCursor)
        return QCursor(Qt.ArrowCursor)

    def _update_position(self):
        parent = self.parentItem()
        if not parent:
            return
            
        rect = parent.boundingRect()
        s = self.SIZE
        
        if self._position == self.TOP_LEFT:
            self.setPos(rect.left() - s/2, rect.top() - s/2)
        elif self._position == self.TOP_RIGHT:
            self.setPos(rect.right() - s/2, rect.top() - s/2)
        elif self._position == self.BOTTOM_RIGHT:
            self.setPos(rect.right() - s/2, rect.bottom() - s/2)
        elif self._position == self.BOTTOM_LEFT:
            self.setPos(rect.left() - s/2, rect.bottom() - s/2)
        elif self._position == self.TOP:
            self.setPos(rect.center().x() - s/2, rect.top() - s/2)
        elif self._position == self.BOTTOM:
            self.setPos(rect.center().x() - s/2, rect.bottom() - s/2)
        elif self._position == self.LEFT:
            self.setPos(rect.left() - s/2, rect.center().y() - s/2)
        elif self._position == self.RIGHT:
            self.setPos(rect.right() - s/2, rect.center().y() - s/2)
            
    def mousePressEvent(self, event):
        # Start resize - Store reference state
        self._start_pos = event.scenePos()
        self._start_item_pos = self.parentItem().pos()
        self._start_rect = self.parentItem().boundingRect()
        
        # Save snapshot BEFORE resize starts
        if self.scene() and hasattr(self.scene(), "save_snapshot"):
            self.scene().save_snapshot()
            
        event.accept()

    def mouseMoveEvent(self, event):
        item = self.parentItem()
        if not item:
            return
            
        pos = event.scenePos()
        scene = self.scene()
        if scene and scene.alignment.snap_enabled:
             pos.setX(round(pos.x() / scene.alignment.grid_size) * scene.alignment.grid_size)
             pos.setY(round(pos.y() / scene.alignment.grid_size) * scene.alignment.grid_size)
        
        # Calculate Delta from START position to current SNAPPED position
        delta = pos - self._start_pos
        
        # Reference values
        base_rect = self._start_rect
        base_pos = self._start_item_pos
        
        new_rect = QRectF(base_rect)
        new_pos = QPointF(base_pos)
        
        min_size = scene.alignment.grid_size if scene else 5.0
        
        # Fixed logic: Apply delta to the START state
        if self._position == self.BOTTOM_RIGHT:
            new_rect.setWidth(max(min_size, base_rect.width() + delta.x()))
            new_rect.setHeight(max(min_size, base_rect.height() + delta.y()))
            
        elif self._position == self.BOTTOM_LEFT:
            dw = -delta.x()
            if base_rect.width() + dw >= min_size:
                new_pos.setX(base_pos.x() + delta.x())
                new_rect.setWidth(base_rect.width() + dw)
            new_rect.setHeight(max(min_size, base_rect.height() + delta.y()))
            
        elif self._position == self.TOP_RIGHT:
            dh = -delta.y()
            if base_rect.height() + dh >= min_size:
                new_pos.setY(base_pos.y() + delta.y())
                new_rect.setHeight(base_rect.height() + dh)
            new_rect.setWidth(max(min_size, base_rect.width() + delta.x()))
            
        elif self._position == self.TOP_LEFT:
            dw, dh = -delta.x(), -delta.y()
            if base_rect.width() + dw >= min_size:
                new_pos.setX(base_pos.x() + delta.x())
                new_rect.setWidth(base_rect.width() + dw)
            if base_rect.height() + dh >= min_size:
                new_pos.setY(base_pos.y() + delta.y())
                new_rect.setHeight(base_rect.height() + dh)
                
        elif self._position == self.TOP:
            dh = -delta.y()
            if base_rect.height() + dh >= min_size:
                new_pos.setY(base_pos.y() + delta.y())
                new_rect.setHeight(base_rect.height() + dh)
                
        elif self._position == self.BOTTOM:
            new_rect.setHeight(max(min_size, base_rect.height() + delta.y()))
            
        elif self._position == self.LEFT:
            dw = -delta.x()
            if base_rect.width() + dw >= min_size:
                new_pos.setX(base_pos.x() + delta.x())
                new_rect.setWidth(base_rect.width() + dw)
                
        elif self._position == self.RIGHT:
            new_rect.setWidth(max(min_size, base_rect.width() + delta.x()))
            
        # Apply changes
        item.setPos(new_pos)
        if hasattr(item, 'setRect'):
            item.setRect(0, 0, new_rect.width(), new_rect.height())

        # Sync model
        if hasattr(item, 'model'):
            item.model.x = new_pos.x()
            item.model.y = new_pos.y()
            item.model.width = new_rect.width()
            item.model.height = new_rect.height()
            
        # Update all handles positions
        if hasattr(item, 'update_handles'):
            item.update_handles()
            
        # Emit move signal
        if item.scene() and hasattr(item.scene(), "itemMoved"):
            item.scene().itemMoved.emit(item)
        
        event.accept()

    def mouseReleaseEvent(self, event):
        # Save snapshot AFTER resize ends
        if self.scene() and hasattr(self.scene(), "save_snapshot"):
            self.scene().save_snapshot()
        super().mouseReleaseEvent(event)
