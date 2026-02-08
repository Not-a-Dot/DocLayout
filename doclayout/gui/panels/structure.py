"""
Panel for managing scene hierarchy via a tree view.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Qt

class StructurePanel(QWidget):
    """
    Shows a tree representation of all elements in the scene.
    Supports drag and drop for reparenting and hierarchy management.
    """
    def __init__(self, scene) -> None:
        """
        Initialize the structure panel.

        Args:
            scene (EditorScene): The scene to monitor.
        """
        super().__init__()
        self.scene = scene
        self.layout = QVBoxLayout(self)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Elements")
        
        # Setup Tree
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setAcceptDrops(True)
        self.tree_widget.setDragDropMode(QTreeWidget.InternalMove)
        self.tree_widget.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.tree_widget.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.EditKeyPressed)
        
        self.layout.addWidget(self.tree_widget)
        
        # Connections
        self.tree_widget.itemChanged.connect(self.on_tree_item_changed)
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_selection_changed)
        self.tree_widget.model().rowsMoved.connect(self.on_rows_moved)
        
        self.scene.selectionChanged.connect(self.on_scene_selection_changed)
        self.scene.itemAdded.connect(self.on_item_added)
        self.scene.itemRemoved.connect(self.on_item_removed)
        self.scene.sceneRestored.connect(self.refresh)
        
        self.item_map = {} # graphics_item -> tree_item

    def on_rows_moved(self, parent_index, start, end, destination_index, row) -> None:
        """Handle tree items being moved by the user."""
        self.tree_widget.blockSignals(True)
        self.scene.blockSignals(True)
        try:
            self._sync_graphics_hierarchy(self.tree_widget.invisibleRootItem())
        finally:
            self.scene.blockSignals(False)
            self.tree_widget.blockSignals(False)

    def refresh(self) -> None:
        """Full rebuild of the tree from the scene's current hierarchy."""
        if not self.scene: return
        
        self.tree_widget.blockSignals(True)
        self.scene.blockSignals(True)
        try:
            self.clear()
            # items() returns items top-to-bottom. We want only root items.
            for item in self.scene.items():
                if hasattr(item, 'model') and item.parentItem() is None:
                    self._add_item_recursive(item)
        finally:
            self.scene.blockSignals(False)
            self.tree_widget.blockSignals(False)

    def clear(self) -> None:
        """Clear all items from the tree."""
        self.tree_widget.clear()
        self.item_map.clear()

    def _sync_graphics_hierarchy(self, tree_item: QTreeWidgetItem) -> None:
        """Sync graphics item parents to match tree structure."""
        graphics_item = getattr(tree_item, '_graphics_item', None)
        
        if graphics_item:
            graphics_item.model.children = []
        
        for i in range(tree_item.childCount()):
            child_tree_item = tree_item.child(i)
            child_graphics_item = getattr(child_tree_item, '_graphics_item', None)
            
            if child_graphics_item:
                if graphics_item:
                    if child_graphics_item.parentItem() != graphics_item:
                        old_pos = child_graphics_item.scenePos()
                        child_graphics_item.setParentItem(graphics_item)
                        child_graphics_item.setPos(graphics_item.mapFromScene(old_pos))
                    graphics_item.model.children.append(child_graphics_item.model)
                else: 
                    if child_graphics_item.parentItem() is not None:
                        old_pos = child_graphics_item.scenePos()
                        child_graphics_item.setParentItem(None)
                        child_graphics_item.setPos(old_pos)
            
            self._sync_graphics_hierarchy(child_tree_item)

    def on_item_removed(self, graphics_item) -> None:
        """Remove item from tree when removed from scene."""
        if graphics_item in self.item_map:
            tree_item = self.item_map.pop(graphics_item)
            parent = tree_item.parent()
            if parent:
                parent.removeChild(tree_item)
            else:
                index = self.tree_widget.indexOfTopLevelItem(tree_item)
                if index >= 0:
                    self.tree_widget.takeTopLevelItem(index)
        
    def on_item_added(self, graphics_item) -> None:
        """Add item to tree when added to scene."""
        if not hasattr(graphics_item, 'model') or graphics_item in self.item_map:
            return
        self._add_item_recursive(graphics_item)

    def _add_item_recursive(self, graphics_item, parent_tree_item=None) -> None:
        """Recursively add item and its children to the tree."""
        if not hasattr(graphics_item, 'model'):
            return
            
        custom_name = graphics_item.model.name
        label = custom_name if custom_name else f"{graphics_item.model.type.value} ({graphics_item.model.id[:4]})"
            
        tree_item = QTreeWidgetItem([label])
        tree_item.setFlags(tree_item.flags() | Qt.ItemIsEditable)
        tree_item._graphics_item = graphics_item
        
        if parent_tree_item:
            parent_tree_item.addChild(tree_item)
        else:
            self.tree_widget.addTopLevelItem(tree_item)
            
        self.item_map[graphics_item] = tree_item
        for child in graphics_item.childItems():
            if hasattr(child, 'model'):
                self._add_item_recursive(child, tree_item)

    def on_tree_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Update model name when tree item text is edited."""
        graphics_item = getattr(item, '_graphics_item', None)
        if graphics_item and hasattr(graphics_item, 'model'):
            graphics_item.model.name = item.text(0)

    def on_tree_selection_changed(self) -> None:
        """Sync tree selection to graphics scene selection."""
        if self.scene.signalsBlocked():
             return
        
        # Block signals temporarily to avoid recursion
        self.scene.blockSignals(True)
        try:
            self.scene.clearSelection()
            for tree_item in self.tree_widget.selectedItems():
                try:
                    graphics_item = getattr(tree_item, '_graphics_item', None)
                    if graphics_item:
                        graphics_item.setSelected(True)
                except RuntimeError:
                    continue
        finally:
            self.scene.blockSignals(False)
        
        # Manually emit selectionChanged so PropertyEditor gets notified
        self.scene.selectionChanged.emit()

    def on_scene_selection_changed(self) -> None:
        """Sync scene selection to tree selection."""
        if self.tree_widget.signalsBlocked():
            return
        try:
            selected_items = self.scene.selectedItems()
        except RuntimeError:
            return
            
        self.tree_widget.blockSignals(True)
        try:
            self.tree_widget.clearSelection()
            for item in selected_items:
                if item in self.item_map:
                    tree_item = self.item_map[item]
                    try:
                        # Check if internal C++ object is still valid
                        _ = tree_item.text(0)
                        tree_item.setSelected(True)
                        p = tree_item.parent()
                        while p:
                            p.setExpanded(True)
                            p = p.parent()
                    except RuntimeError:
                        # Item was deleted but still in map
                        continue
        finally:
            self.tree_widget.blockSignals(False)
