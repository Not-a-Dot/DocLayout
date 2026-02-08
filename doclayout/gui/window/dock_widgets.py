"""
Dock widgets configuration for the Main Window.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class DockManager:
    """
    Handles creation and population of dockable side panels.
    """
    @staticmethod
    def setup_docks(p) -> None:
        """
        Create and attach properties and library docks.

        Args:
            p (MainWindow): The target window.
        """
        # Properties Dock
        p.prop_dock = QDockWidget("Properties", p)
        p.prop_dock.setObjectName("prop_dock")
        p.prop_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        from ..panels import PropertyEditor
        p.prop_widget = PropertyEditor(p.scene)
        p.prop_dock.setWidget(p.prop_widget)
        p.addDockWidget(Qt.RightDockWidgetArea, p.prop_dock)

        # Library Dock (Tools + Structure)
        p.library_dock = QDockWidget("Library", p)
        p.library_dock.setObjectName("library_dock")
        p.library_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from ..panels import BlocksPanel, StructurePanel, ToolsPanel
        p.blocks_panel = BlocksPanel(p.scene)
        p.tools_panel = ToolsPanel(p.scene, p.actions_manager, p.blocks_panel)
        p.structure_panel = StructurePanel(p.scene)
        
        # Tools Panel (Items + Blocks tabs)
        layout.addWidget(p.tools_panel)
        
        # Structure Panel
        layout.addWidget(QLabel("<b>Document Structure</b>"))
        layout.addWidget(p.structure_panel)
        
        p.library_dock.setWidget(container)
        p.addDockWidget(Qt.LeftDockWidgetArea, p.library_dock)
