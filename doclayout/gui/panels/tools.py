"""
Tabbed panel containing Items (tools) and Blocks.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QGridLayout, QToolButton, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from doclayout.core.i18n import tr

class ToolsPanel(QWidget):
    """
    Panel with tabs for Items (insertion tools) and Blocks.
    """
    def __init__(self, scene, action_manager, blocks_panel_widget) -> None:
        """
        Initialize the tools panel.
        
        Args:
            scene (EditorScene): The graphics scene.
            action_manager (ActionManager): Action manager with tool actions.
            blocks_panel_widget (BlocksPanel): Existing blocks panel widget.
        """
        super().__init__()
        self.scene = scene
        self.action_manager = action_manager
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Items (Tools)
        self.items_tab = self._create_items_tab()
        self.tabs.addTab(self.items_tab, tr('toolbar.items'))
        
        # Tab 2: Blocks
        self.tabs.addTab(blocks_panel_widget, tr('toolbar.blocks'))
    
    def _create_items_tab(self) -> QWidget:
        """Create the Items tab with tool buttons."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Grid of tool buttons
        grid = QGridLayout()
        grid.setSpacing(4)
        
        tools = [
            (self.action_manager.tool_select_action, 0, 0),
            (self.action_manager.tool_rect_action, 0, 1),
            (self.action_manager.tool_text_action, 1, 0),
            (self.action_manager.tool_textbox_action, 1, 1),
            (self.action_manager.tool_image_action, 2, 0),
            (self.action_manager.tool_line_action, 2, 1),
            (self.action_manager.tool_kvbox_action, 3, 0),
            (self.action_manager.tool_table_action, 3, 1),
            (self.action_manager.tool_container_action, 4, 0),
        ]
        
        for action, row, col in tools:
            btn = QToolButton()
            btn.setDefaultAction(action)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setMinimumHeight(40)
            btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            grid.addWidget(btn, row, col)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return widget
