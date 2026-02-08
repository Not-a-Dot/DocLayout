"""
Resize Handle Graphics Item.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF
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
        
        # Professional look: White fill, Blue border
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(QColor("#1a73e8"), 0.3)) # Google Blue
        
        self.setFlags(QGraphicsItem.ItemIsMovable) 
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        self.setCursor(self._get_cursor())
        self._update_position()

    def paint(self, painter, option, widget):
        """Draw as a professional square (fallback to default but with antialiasing)."""
        painter.setRenderHint(QPainter.Antialiasing)
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
        # Start resize
        self._start_pos = event.scenePos()
        self._start_rect = self.parentItem().boundingRect()
        self._start_item_pos = self.parentItem().pos()
        event.accept()

    def mouseMoveEvent(self, event):
        item = self.parentItem()
        if not item:
            return
            
        # Delta calculation needs complex logic for rotation (if any)
        # For now, assuming no rotation.
        
        # Calculate new rect based on handle movement
        # This is tricky because QGraphicsRectItem defines rect from (0,0) usually.
        # If we change X, Y, we move the item. If we change W, H, we resize.
        
        # NOTE: DocLayout model uses (x, y, width, height).
        # Wrapper Item (RectEditorItem) uses QGraphicsRectItem(0, 0, w, h).
        # So Top-Left of item is always (0,0) in local coords.
        # Item Pos is (x,y) in scene.
        
        # If dragging Bottom-Right: Change Width/Height.
        # If dragging Top-Left: Change Pos X/Y AND Change Width/Height.
        
        pos = event.scenePos()
        # Snap logic here? Yes, if we want resize snap.
        # Access scene grid size?
        scene = self.scene()
        pos = event.scenePos()
        scene = self.scene()
        if scene and scene.alignment.snap_enabled:
             pos.setX(round(pos.x() / scene.alignment.grid_size) * scene.alignment.grid_size)
             pos.setY(round(pos.y() / scene.alignment.grid_size) * scene.alignment.grid_size)
        
        # Local position of the mouse in the parent item
        local_pos = item.mapFromScene(pos)
        
        # Initial rect and pos
        rect = item.boundingRect()
        new_rect = QRectF(rect)
        new_pos = item.pos()
        
        min_size = scene.alignment.grid_size if scene else 5.0
        
        # RESIZE LOGIC PER HANDLE
        if self._position == self.BOTTOM_RIGHT:
            new_rect.setWidth(max(min_size, local_pos.x()))
            new_rect.setHeight(max(min_size, local_pos.y()))
            
        elif self._position == self.BOTTOM_LEFT:
            # Shift X (Pos) and Widh (Rect)
            dx = local_pos.x()
            if rect.width() - dx >= min_size:
                new_pos.setX(new_pos.x() + dx)
                new_rect.setWidth(rect.width() - dx)
            new_rect.setHeight(max(min_size, local_pos.y()))
            
        elif self._position == self.TOP_RIGHT:
            # Shift Y (Pos) and Height (Rect)
            dy = local_pos.y()
            if rect.height() - dy >= min_size:
                new_pos.setY(new_pos.y() + dy)
                new_rect.setHeight(rect.height() - dy)
            new_rect.setWidth(max(min_size, local_pos.x()))
            
        elif self._position == self.TOP_LEFT:
            # Shift X, Y (Pos) and Width, Height (Rect)
            dx = local_pos.x()
            dy = local_pos.y()
            if rect.width() - dx >= min_size:
                new_pos.setX(new_pos.x() + dx)
                new_rect.setWidth(rect.width() - dx)
            if rect.height() - dy >= min_size:
                new_pos.setY(new_pos.y() + dy)
                new_rect.setHeight(rect.height() - dy)
                
        elif self._position == self.TOP:
            dy = local_pos.y()
            if rect.height() - dy >= min_size:
                new_pos.setY(new_pos.y() + dy)
                new_rect.setHeight(rect.height() - dy)
                
        elif self._position == self.BOTTOM:
            new_rect.setHeight(max(min_size, local_pos.y()))
            
        elif self._position == self.LEFT:
            dx = local_pos.x()
            if rect.width() - dx >= min_size:
                new_pos.setX(new_pos.x() + dx)
                new_rect.setWidth(rect.width() - dx)
                
        elif self._position == self.RIGHT:
            new_rect.setWidth(max(min_size, local_pos.x()))
            
        # Apply changes
        item.setPos(new_pos)
        if hasattr(item, 'setRect'):
            item.setRect(0, 0, new_rect.width(), new_rect.height())
        elif hasattr(item, 'setX'): # Generic fallback?
             pass 

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
        super().mouseReleaseEvent(event)
