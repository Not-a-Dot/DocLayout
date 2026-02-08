"""
Action definitions for the Main Window.
"""

import sys
from PySide6.QtGui import QAction, QIcon, QActionGroup
from PySide6.QtCore import Qt
from doclayout.core.i18n import tr

class ActionManager:
    """
    Manages creation and grouping of user actions.
    """
    def __init__(self, parent) -> None:
        """
        Initialize actions for the parent window.

        Args:
            parent (MainWindow): The window that owns these actions.
        """
        self.parent = parent
        self._create_file_actions()
        self._create_view_actions()
        self._create_tool_actions()
        self._create_layout_actions()

    def _create_file_actions(self) -> None:
        p = self.parent
        self.new_action = QAction(QIcon.fromTheme("document-new"), tr('menu.file.new'), p)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(p.new_file)
        
        self.open_action = QAction(QIcon.fromTheme("document-open"), tr('menu.file.open'), p)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(p.open_file)
        
        self.save_action = QAction(QIcon.fromTheme("document-save"), tr('menu.file.save'), p)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(p.save_file)
        
        self.preview_action = QAction(QIcon.fromTheme("document-print-preview"), tr('menu.file.preview'), p)
        self.preview_action.setShortcut("Ctrl+P")
        self.preview_action.triggered.connect(p.preview_pdf)

        self.export_pdf_action = QAction(QIcon.fromTheme("application-pdf"), tr('menu.file.export_pdf'), p)
        self.export_pdf_action.triggered.connect(p.export_pdf)
        
        self.exit_action = QAction(QIcon.fromTheme("application-exit"), tr('menu.file.exit'), p)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(p.close)

    def _create_view_actions(self) -> None:
        p = self.parent
        self.zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), tr('menu.view.zoom_in'), p)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.triggered.connect(p.view.zoom_in)
        
        self.zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), tr('menu.view.zoom_out'), p)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.triggered.connect(p.view.zoom_out)

    def _create_tool_actions(self) -> None:
        p = self.parent
        self.tool_select_action = QAction(QIcon.fromTheme("edit-select"), tr('toolbar.select'), p)
        self.tool_select_action.setCheckable(True)
        self.tool_select_action.setChecked(True)
        
        self.tool_rect_action = QAction(tr('toolbar.rectangle'), p)
        self.tool_rect_action.setCheckable(True)
        
        self.tool_text_action = QAction(tr('toolbar.text'), p)
        self.tool_text_action.setCheckable(True)
        
        self.tool_textbox_action = QAction("Text Box", p) # Using direct string to ensure visibility if translation missing
        self.tool_textbox_action.setCheckable(True)
        
        self.tool_line_action = QAction(tr('toolbar.line'), p)
        self.tool_line_action.setCheckable(True)
        
        self.tool_image_action = QAction(tr('toolbar.image'), p)
        self.tool_image_action.setCheckable(True)
        
        self.tool_kvbox_action = QAction(tr('toolbar.kv_box'), p)
        self.tool_kvbox_action.setCheckable(True)
        
        self.tool_container_action = QAction(tr('toolbar.container'), p)
        self.tool_container_action.setCheckable(True)

        self.tool_table_action = QAction(tr('toolbar.table'), p)
        self.tool_table_action.setCheckable(True)

        self.group_action = QAction(tr('menu.arrange.bring_front'), p)
        self.group_action.setShortcut("Ctrl+G")
        self.group_action.triggered.connect(lambda: p.scene.group_selected())
        
        self.tool_group = QActionGroup(p)
        for act in [self.tool_select_action, self.tool_rect_action, self.tool_text_action, self.tool_textbox_action,
                    self.tool_image_action, self.tool_line_action, self.tool_kvbox_action,
                    self.tool_container_action, self.tool_table_action]:
            self.tool_group.addAction(act)
        
        self.tool_select_action.triggered.connect(lambda: p.scene.set_tool("select"))
        self.tool_rect_action.triggered.connect(lambda: p.scene.set_tool("rect"))
        self.tool_text_action.triggered.connect(lambda: p.scene.set_tool("text"))
        self.tool_textbox_action.triggered.connect(lambda: p.scene.set_tool("textbox"))
        self.tool_image_action.triggered.connect(lambda: p.scene.set_tool("image"))
        self.tool_line_action.triggered.connect(lambda: p.scene.set_tool("line"))
        self.tool_kvbox_action.triggered.connect(lambda: p.scene.set_tool("kvbox"))
        self.tool_container_action.triggered.connect(lambda: p.scene.set_tool("container"))
        self.tool_table_action.triggered.connect(lambda: p.scene.set_tool("table"))

    def _create_layout_actions(self) -> None:
        p = self.parent
        self.reset_layout_action = QAction("Reset Layout", p)
        self.reset_layout_action.triggered.connect(p._reset_layout)
        
        self.save_layout_action = QAction("Save Layout...", p)
        self.save_layout_action.triggered.connect(p._save_layout_named)

        self.load_layout_action = QAction("Load Layout...", p)
        self.load_layout_action.triggered.connect(p._load_layout_named)
