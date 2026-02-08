"""
Core Editor Scene implementation.
"""

import logging
from typing import List, Optional
from PySide6.QtWidgets import QGraphicsScene, QGraphicsItem
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

from doclayout.core.models import Template, PageSize, BaseElement, ElementType
from .alignment import AlignmentManager
from .clipboard import SceneClipboard
from .handlers import SceneEventHandler

logger = logging.getLogger(__name__)

class EditorScene(QGraphicsScene):
    """
    The main coordinator for element editing, hierarchy, and tools.
    
    Signals:
        toolChanged: Emitted when the active tool changes.
        itemAdded: Emitted when an item is added to the scene.
        itemMoved: Emitted when an item's geometry changes.
        itemRemoved: Emitted when an item is deleted.
        hierarchyChanged: Emitted when parenting or grouping changes.
    """
    toolChanged = Signal(str)
    itemAdded = Signal(QGraphicsItem)
    itemMoved = Signal(QGraphicsItem)
    itemRemoved = Signal(QGraphicsItem)
    hierarchyChanged = Signal()

    def __init__(self, parent=None) -> None:
        """Initialize the scene with defaults."""
        super().__init__(parent)
        self._current_tool: str = "select"
        self._page_width: float = 210.0 # A4 Default
        self._page_height: float = 297.0
        
        # Template to store project settings
        self.template = Template(
            name="New Template",
            page_size=PageSize(width=self._page_width, height=self._page_height),
            items=[]
        )
        
        self.alignment = AlignmentManager()
        self.clipboard = SceneClipboard()
        
        self.itemMoved.connect(self.alignment.check_alignment)
        self._update_scene_rect()

    def _update_scene_rect(self) -> None:
        # Add margin for view
        margin = 50
        self.setSceneRect(-margin, -margin, self._page_width + 2*margin, self._page_height + 2*margin)

    def drawBackground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw page boundaries and grid based on current theme."""
        super().drawBackground(painter, rect)
        
        from doclayout.gui.themes import ThemeManager
        colors = ThemeManager.get_editor_colors()
        
        # Area outside the document
        painter.fillRect(rect, colors["background"])
        
        # The document page
        page_rect = QRectF(0, 0, self._page_width, self._page_height)
        painter.fillRect(page_rect, colors["page"])
        
        # Border for the page (always visible, replaces shadow)
        painter.save()
        painter.setPen(QPen(colors["grid"], 0.5))
        painter.drawRect(page_rect)
        painter.restore()
        
        # Grid
        if self.alignment.snap_enabled:
            painter.save()
            pen = QPen(colors["grid"])
            pen.setWidthF(0.1)
            painter.setPen(pen)
            
            grid = self.alignment.grid_size
            if grid <= 0: grid = 10
            
            # Use float coordinates to avoid rounding issues with zoom
            left = rect.left() - (rect.left() % grid)
            top = rect.top() - (rect.top() % grid)
            
            # Draw vertical lines
            x = left
            while x <= rect.right():
                painter.drawLine(x, rect.top(), x, rect.bottom())
                x += grid
            
            # Draw horizontal lines
            y = top
            while y <= rect.bottom():
                painter.drawLine(rect.left(), y, rect.right(), y)
                y += grid
            
            painter.restore()

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        """Draw guides over items."""
        super().drawForeground(painter, rect)
        self.alignment.draw_guides(painter)

    def addItem(self, item: QGraphicsItem) -> None:
        """Add item and notify listeners."""
        super().addItem(item)
        self.itemAdded.emit(item)
        self.hierarchyChanged.emit()

    def delete_selected(self) -> None:
        """Delete all currently selected items."""
        for item in self.selectedItems():
            self.removeItem(item)
            self.itemRemoved.emit(item)
        self.hierarchyChanged.emit()

    def set_snap(self, enabled: bool) -> None:
        self.alignment.snap_enabled = enabled
        self.update()

    def set_grid_size(self, size: int) -> None:
        if size <= 0:
            size = 1
        self.alignment.grid_size = size
        self.update()

    def set_page_size(self, width: float, height: float) -> None:
        self._page_width = width
        self._page_height = height
        self._update_scene_rect()
        self.update()

    def _sync_model_hierarchy(self, item: QGraphicsItem) -> None:
        """Update model children list from GUI state."""
        if not hasattr(item, 'model'):
            return
            
        item.model.z = item.zValue()
        item.model.children = []
        for child in item.childItems():
            if hasattr(child, 'model'):
                item.model.children.append(child.model)
                self._sync_model_hierarchy(child)

    def to_template(self) -> Template:
        """Reconstruct template from current scene items."""
        items = []
        for item in self.items():
            if hasattr(item, 'model') and item.parentItem() is None:
                item.model.z = item.zValue()
                self._sync_model_hierarchy(item)
                items.append(item.model)
        
        # Preserve project settings
        self.template.items = items
        self.template.page_size = PageSize(width=self._page_width, height=self._page_height)
        return self.template

    def copy_selected(self) -> None:
        self.clipboard.copy(self.selectedItems())

    def paste(self) -> None:
        new_items = self.clipboard.paste(self)
        self.clearSelection()
        for it in new_items:
            it.setSelected(True)

    def group_selected(self) -> None:
        """Group items into a new container."""
        from .grouping import GroupingManager
        GroupingManager.group_items(self)
        self.hierarchyChanged.emit()

    def bring_to_front(self) -> None:
        """Bring selected items to the front by increasing Z-value."""
        items = self.selectedItems()
        if not items: return
        
        # Find max Z among all items
        max_z = 0.0
        for item in self.items():
            if item.zValue() > max_z:
                max_z = item.zValue()
        
        for item in items:
            item.setZValue(max_z + 1.0)
        self.update()

    def send_to_back(self) -> None:
        """Send selected items to the back by decreasing Z-value."""
        items = self.selectedItems()
        if not items: return
        
        # Find min Z among all items
        min_z = 0.0
        for item in self.items():
            if item.zValue() < min_z:
                min_z = item.zValue()
        
        for item in items:
            item.setZValue(min_z - 1.0)
        self.update()

    def set_tool(self, tool_name: str) -> None:
        self._current_tool = tool_name
        self.alignment.guide_lines = []
        self.update()
        self.toolChanged.emit(tool_name)

    def mousePressEvent(self, event) -> None:
        """Delegate mouse press to handler."""
        SceneEventHandler().handle_mouse_press(self, event)
        super().mousePressEvent(event)

    def keyPressEvent(self, event) -> None:
        """Delegate key press to handler."""
        SceneEventHandler().handle_key_press(self, event)
        super().keyPressEvent(event)
