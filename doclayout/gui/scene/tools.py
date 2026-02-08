"""
Item creation tools for the Editor Scene.
"""

import logging
from typing import Dict, Type
from doclayout.core.models import BaseElement, ElementType

logger = logging.getLogger(__name__)

class ToolManager:
    """
    Manages item creation based on active tools.
    """
    CREATION_TOOLS = ["rect", "text", "line", "image", "kvbox", "container", "table"]

    @staticmethod
    def create_item(scene, tool_name: str, x: float, y: float) -> None:
        """
        Create a new item based on the tool name.

        Args:
            scene (EditorScene): Target scene.
            tool_name (str): Type of tool.
            x (float): Target X coordinate.
            y (float): Target Y coordinate.
        """
        try:
            if hasattr(scene, 'alignment'):
                x = scene.alignment.snap_value(x)
                y = scene.alignment.snap_value(y)
                
            from ..items import get_item_for_model
            
            props = {}
            width, height = 40, 40

            if tool_name == "rect":
                etype = ElementType.RECT
            elif tool_name == "text":
                etype = ElementType.TEXT
                props = {"text": "Label"}
                width, height = 50, 10
            elif tool_name == "textbox":
                etype = ElementType.TEXT_BOX
                props = {"text": "Text Box", "show_border": True}
                width, height = 80, 40
            elif tool_name == "line":
                etype = ElementType.LINE
                width, height = 20, 0
                props = {"x2": x + 20, "y2": y}
            elif tool_name == "image":
                etype = ElementType.IMAGE
                props = {"image_path": ""}
            elif tool_name == "kvbox":
                etype = ElementType.KV_BOX
                width, height = 60, 10
                props = {"key_text": "Label:", "text": "[Value]"}
            elif tool_name == "container":
                etype = ElementType.CONTAINER
                width, height = 100, 50
            elif tool_name == "table":
                etype = ElementType.TABLE
                width, height = 120, 60
            else:
                logger.warning("Unknown tool: %s", tool_name)
                return

            logger.debug("Creating %s at (%s, %s) with size (%s, %s)", tool_name, x, y, width, height)
            model = BaseElement(type=etype, x=x, y=y, width=width, height=height, props=props)
            
            logger.debug("Getting item for model: %s", model)
            item = get_item_for_model(model)
            
            if item:
                logger.debug("Adding item to scene: %s", item)
                scene.addItem(item)
                scene.set_tool("select")
                scene.clearSelection()
                item.setSelected(True)
                logger.info("Successfully created %s item", tool_name)
            else:
                logger.error("Failed to create item for model: %s", model)
                
        except Exception as e:
            logger.error("CRITICAL ERROR creating %s item: %s", tool_name, e, exc_info=True)
            # Don't clear the scene on error - just log it
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None, "Error Creating Item", 
                               f"Failed to create {tool_name}: {str(e)}\n\nCheck console for details.")
