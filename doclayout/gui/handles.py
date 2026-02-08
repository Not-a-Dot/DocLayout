"""
Resize Handle Graphics Item.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QPen, QColor, QCursor

class ResizeHandle(QGraphicsRectItem):
    """
    A handle for resizing items.
    """
    SIZE = 6.0 # Handle size in scene units (mm)
    
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
        self.setBrush(QBrush(Qt.blue))
        self.setPen(QPen(Qt.white))
        self.setFlags(QGraphicsItem.ItemIsMovable) 
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        
        self.setCursor(self._get_cursor())
        self._update_position()

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
        if scene and scene.alignment.snap_enabled:
             pos.setX(round(pos.x() / scene.alignment.grid_size) * scene.alignment.grid_size)
             pos.setY(round(pos.y() / scene.alignment.grid_size) * scene.alignment.grid_size)
        
        # Current logic is simplified
        if self._position == self.BOTTOM_RIGHT:
             # Calculate new width/height relative to item position
             # Item (0,0) is TopLeft. Event Scene Pos - Item Scene Pos = Local Pos
             local_pos = item.mapFromScene(pos)
             new_w = local_pos.x()
             new_h = local_pos.y()
             
             new_w = max(scene.alignment.grid_size, new_w) if scene else max(10, new_w)
             new_h = max(scene.alignment.grid_size, new_h) if scene else max(10, new_h)
             
             # Snap logic meant new_w/new_h are snapped? 
             # pos was already snapped above if enabled.
             
             # Move Handle to new Corner
             # We want the handle CENTER to be at (new_w, new_h)? 
             # Or TopLeft of handle?
             # _update_position sets handle centered on corner.
             # setPos is TopLeft of handle item.
             # In _update_position:
             # self.setPos(rect.right() - s/2, rect.bottom() - s/2)
             # So we should setPos(new_w - s/2, new_h - s/2)
             
             s = self.SIZE
             self.setPos(new_w - s/2, new_h - s/2)
             
             # Update Item Rect
             if hasattr(item, 'setRect'):
                 item.setRect(0, 0, new_w, new_h)
                 # Update model
                 if hasattr(item, 'model'):
                     item.model.width = new_w
                     item.model.height = new_h
                     
                 # NEW: Emit moved signal for live property updates (Resize is a form of geometry change)
                 if item.scene() and hasattr(item.scene(), "itemMoved"):
                     item.scene().itemMoved.emit(item)
        
        # TODO: Implement other handles
        
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
