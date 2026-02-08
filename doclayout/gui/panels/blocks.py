"""
Panel for managing and using saved element blocks.
"""

import os
import logging
from uuid import uuid4
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, 
                               QListWidgetItem, QPushButton, QMessageBox)
from PySide6.QtCore import Qt

from doclayout.core.io import load_from_json
from doclayout.core.models import BaseElement

logger = logging.getLogger(__name__)

class BlocksPanel(QWidget):
    """
    Lists saved blocks and allows adding them to the scene via double-click.
    """
    def __init__(self, scene) -> None:
        """
        Initialize the blocks panel.

        Args:
            scene (EditorScene): The target graphics scene.
        """
        super().__init__()
        self.scene = scene
        self.layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        self.btn_refresh = QPushButton("Refresh Library")
        self.btn_refresh.clicked.connect(self.refresh)
        
        self.layout.addWidget(self.btn_refresh)
        self.layout.addWidget(self.list_widget)
        
        self.refresh()

    def refresh(self) -> None:
        """Scan blocks directory and update current list."""
        self.list_widget.clear()
        blocks_dir = "doclayout_blocks"
        if not os.path.exists(blocks_dir):
            return
            
        for f in os.listdir(blocks_dir):
            if f.endswith(".json"):
                name = f[:-5]
                item = QListWidgetItem(name)
                item.setData(Qt.UserRole, os.path.join(blocks_dir, f))
                self.list_widget.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Instantiate a block into the scene."""
        path = item.data(Qt.UserRole)
        try:
            from ..items import get_item_for_model
            
            model_dict = load_from_json(path)
            model = BaseElement.model_validate(model_dict)
            
            # Ensure new unique ID for the instance
            model.id = str(uuid4())
            
            graphics_item = get_item_for_model(model)
            if graphics_item:
                graphics_item.setPos(50, 50) 
                self.scene.addItem(graphics_item)
        except Exception as e:
            logger.error("Failed to load block: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to load block: {e}")
