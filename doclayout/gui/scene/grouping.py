"""
Grouping logic for scene items.
"""

from PySide6.QtCore import QRectF
from doclayout.core.models import BaseElement, ElementType

class GroupingManager:
    """
    Handles grouping multiple items into a container.
    """
    @staticmethod
    def group_items(scene) -> None:
        """
        Group selected items in the scene into a new Container.

        Args:
            scene (EditorScene): The scene containing the items.
        """
        items = scene.selectedItems()
        if not items:
            return
            
        rect = QRectF()
        valid_items = []
        for item in items:
            if hasattr(item, 'model'):
                 if not rect.isValid():
                     rect = item.sceneBoundingRect()
                 else:
                     rect = rect.united(item.sceneBoundingRect())
                 valid_items.append(item)
        
        if not valid_items:
            return
            
        margin = 5
        rect.adjust(-margin, -margin, margin, margin)
        
        from ..items.container import ContainerEditorItem
        
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        container_model = BaseElement(type=ElementType.CONTAINER, x=x, y=y, width=w, height=h)
        container_item = ContainerEditorItem(container_model)
        scene.addItem(container_item)
        
        for item in valid_items:
            scene_pos = item.scenePos()
            item.setParentItem(container_item)
            local_pos = container_item.mapFromScene(scene_pos)
            item.setPos(local_pos)
            
            item.model.x = local_pos.x()
            item.model.y = local_pos.y()
            container_model.children.append(item.model)
            
        scene.clearSelection()
        container_item.setSelected(True)
