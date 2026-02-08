from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt
from doclayout.core.models import BaseElement

class BaseEditorItem:
    """Mixin for common editor item functionality."""
    def __init__(self, model: BaseElement):
        self.model = model
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Initial locking state
        self.update_locking()
        
        # Create children
        self._create_children_items()

    def _create_children_items(self):
        from . import get_item_for_model
        for child_model in self.model.children:
            child_item = get_item_for_model(child_model)
            if child_item:
                child_item.setParentItem(self)

    def mousePressEvent(self, event):
        # If parent is locked, we don't allow selecting children directly?
        # Actually, if we are here, we are the item being clicked.
        # If OUR parent is locked, the parent should have intercepted this?
        # No, child gets event first.
        
        parent = self.parentItem()
        while parent:
            if hasattr(parent, 'model') and parent.model.lock_children:
                # Redirect click to the locked parent
                parent.setSelected(True)
                event.accept()
                return
            parent = parent.parentItem()
            
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Clear alignment guides when mouse is released."""
        super().mouseReleaseEvent(event)
        if self.scene() and hasattr(self.scene(), 'alignment'):
            self.scene().alignment.guide_lines = []
            self.scene().update()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            # value is the new selection state
            self.update_handles(selected=value)
            if value and hasattr(self, '_handle') and self._handle:
                 self._handle._update_position()

        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Respect lock_position
            if self.model.lock_position:
                return self.pos()

            # Snap to grid
            if hasattr(self.scene(), 'alignment') and self.scene().alignment.snap_enabled:
                 grid = self.scene().alignment.grid_size
                 new_pos = value
                 x = round(new_pos.x() / grid) * grid
                 y = round(new_pos.y() / grid) * grid
                 value = type(value)(x, y)
                 
            # Update model with snapped value
            self.model.x = value.x()
            self.model.y = value.y()
            
            # Emit moved signal if scene exists
            if self.scene() and hasattr(self.scene(), "itemMoved"):
                 self.scene().itemMoved.emit(self)

            return value

        return super().itemChange(change, value)

    def update_handles(self, selected=None):
        """Update handle position if it exists."""
        if not hasattr(self, 'model'):
            return
            
        if hasattr(self, '_handle') and self._handle:
            if selected is None:
                selected = self.isSelected()
            # Hide handles if geometry is locked
            self._handle.setVisible(selected and not self.model.lock_geometry)
            self._handle._update_position()

    def update_locking(self):
        """Update flags and visuals based on model lock properties."""
        # lock_selection handled by scene logic to allow tree selection
        self.setFlag(QGraphicsItem.ItemIsMovable, not self.model.lock_position)
        self.update_handles()
        self.update()

    def paint_lock_icons(self, painter):
        """Draw small lock icons if any lock is active."""
        if not (self.model.lock_position or self.model.lock_geometry or self.model.lock_selection):
            return
            
        from PySide6.QtGui import QColor, QBrush, QPen
        from PySide6.QtCore import QPointF, Qt
        
        painter.save()
        s = 2.0 # icon size
        margin = 1.0
        rect = self.boundingRect()
        
        # Color based on lock type
        if self.model.lock_selection:
            color = QColor(255, 0, 0) # Red for selection lock
        elif self.model.lock_position:
            color = QColor(255, 165, 0) # Orange for position lock
        else:
            color = QColor(0, 0, 255) # Blue for geometry lock
            
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.white, 0.5))
        
        # Draw small circle in top-right
        painter.drawEllipse(QPointF(rect.right() - s - margin, rect.top() + margin), s/2, s/2)
        painter.restore()

    def create_properties_widget(self, parent):
        """Return a QWidget for editing this item's specific properties."""
        return None

    def get_bindable_properties(self):
        """Return a list of property keys that can be bound to variables."""
        return []
