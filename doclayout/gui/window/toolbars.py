"""
Toolbars configuration for the Main Window.
"""

from PySide6.QtWidgets import QToolBar, QLabel, QSpinBox, QComboBox
from PySide6.QtGui import QAction

class ToolbarManager:
    """
    Handles creation and population of the window's toolbars.
    """
    @staticmethod
    def setup_toolbars(parent) -> None:
        """
        Create main and edit toolbars.

        Args:
            parent (MainWindow): The target window.
        """
        ToolbarManager._create_main_toolbar(parent)
        ToolbarManager._create_edit_toolbar(parent)

    @staticmethod
    def _create_main_toolbar(p) -> None:
        acts = p.actions_manager
        toolbar = QToolBar("Main Toolbar")
        toolbar.setObjectName("main_toolbar")
        p.addToolBar(toolbar)
        
        toolbar.addAction(acts.new_action)
        toolbar.addAction(acts.open_action)
        toolbar.addAction(acts.save_action)
        toolbar.addSeparator()
        
        toolbar.addAction(acts.preview_action)
        toolbar.addSeparator()
        
        toolbar.addAction(acts.tool_select_action)
        toolbar.addAction(acts.tool_rect_action)
        toolbar.addAction(acts.tool_text_action)
        toolbar.addAction(acts.tool_image_action)
        toolbar.addAction(acts.tool_line_action)
        toolbar.addAction(acts.tool_kvbox_action)
        toolbar.addAction(acts.tool_container_action)
        toolbar.addAction(acts.tool_table_action)
        toolbar.addSeparator()
        toolbar.addAction(acts.group_action)

    @staticmethod
    def _create_edit_toolbar(p) -> None:
        acts = p.actions_manager
        p.edit_toolbar = QToolBar("Edit Toolbar")
        p.edit_toolbar.setObjectName("edit_toolbar")
        p.addToolBar(p.edit_toolbar)
        
        p.edit_toolbar.addAction(acts.zoom_in_action)
        p.edit_toolbar.addAction(acts.zoom_out_action)
        p.edit_toolbar.addSeparator()
        
        # Grid Controls
        p.grid_size_spin = QSpinBox()
        p.grid_size_spin.setRange(1, 100)
        p.grid_size_spin.setValue(10)
        p.grid_size_spin.setSuffix(" mm")
        p.grid_size_spin.valueChanged.connect(p.scene.set_grid_size)
        
        p.snap_check = QAction("Snap", p)
        p.snap_check.setCheckable(True)
        p.snap_check.setChecked(True)
        p.snap_check.toggled.connect(p.scene.set_snap)
        
        p.edit_toolbar.addWidget(QLabel(" Grid: "))
        p.edit_toolbar.addWidget(p.grid_size_spin)
        p.edit_toolbar.addAction(p.snap_check)
        p.edit_toolbar.addSeparator()
        
        # Page Setup
        p.page_size_combo = QComboBox()
        p.page_size_combo.addItem("A4 (210x297mm)", (210, 297))
        p.page_size_combo.addItem("Letter (216x279mm)", (215.9, 279.4))
        p.page_size_combo.addItem("Thermal 80mm", (80, 297))
        p.page_size_combo.addItem("Thermal 58mm", (58, 297))
        p.page_size_combo.currentIndexChanged.connect(p._on_page_size_changed)
        
        p.edit_toolbar.addWidget(QLabel(" Page: "))
        p.edit_toolbar.addWidget(p.page_size_combo)
