"""
Event handlers for EditorScene.
"""

from PySide6.QtCore import Qt
from doclayout.core.models import BaseElement, ElementType
from .tools import ToolManager

class SceneEventHandler:
    """
    Mixin-like class to handle events for EditorScene.
    """
    def handle_mouse_press(self, scene, event) -> None:
        """Process mouse press events based on current tool."""
        pos = event.scenePos()
        x, y = pos.x(), pos.y()

        if scene._current_tool == "select":
            # Selection redirection logic
            items = scene.items(pos, Qt.IntersectsItemShape, Qt.DescendingOrder)
            top_item = items[0] if items else None
            if top_item and hasattr(top_item, 'model') and top_item.model.lock_selection:
                target_item = None
                for it in items:
                    if not (hasattr(it, 'model') and it.model.lock_selection):
                        target_item = it
                        break
                if target_item:
                    scene.clearSelection()
                    target_item.setSelected(True)
                    event.accept()
                    return
            
        elif scene._current_tool in ToolManager.CREATION_TOOLS:
             ToolManager.create_item(scene, scene._current_tool, x, y)
             event.accept()
             return

    def handle_key_press(self, scene, event) -> None:
        """Process keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            scene.delete_selected()
            event.accept()
        elif modifiers & Qt.ControlModifier:
            if key == Qt.Key_C:
                scene.copy_selected()
            elif key == Qt.Key_V:
                scene.paste()
            elif key == Qt.Key_G:
                scene.group_selected()
            event.accept()
