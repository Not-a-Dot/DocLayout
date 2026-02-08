"""
Clipboard functionality for Graphics Scene.
"""

from typing import List, Dict, Any
from uuid import uuid4
from PySide6.QtWidgets import QGraphicsItem

from doclayout.core.models import BaseElement

class SceneClipboard:
    """
    Handles copy and paste operations for scene items.
    """
    def __init__(self) -> None:
        """Initialize empty clipboard."""
        self._items: List[Dict[str, Any]] = []

    def copy(self, items: List[QGraphicsItem]) -> None:
        """
        Copy selected items to the clipboard.

        Args:
            items (List[QGraphicsItem]): List of items to copy.
        """
        self._items = []
        for item in items:
            if hasattr(item, 'model'):
                # Deep copy via dictionary dump
                self._items.append(item.model.model_dump())

    def paste(self, scene) -> List[QGraphicsItem]:
        """
        Paste items from clipboard into the scene.

        Args:
            scene (EditorScene): Target scene.

        Returns:
            List[QGraphicsItem]: List of newly created items.
        """
        if not self._items:
            return []

        from ..items import get_item_for_model
        new_items = []
        
        for m_dict in self._items:
            model = BaseElement.model_validate(m_dict)
            model.id = str(uuid4())
            # Offset to indicate paste
            model.x += 5
            model.y += 5
            
            item = get_item_for_model(model)
            if item:
                scene.addItem(item)
                new_items.append(item)
        
        return new_items
