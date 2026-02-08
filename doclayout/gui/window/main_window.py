"""
Main window implementation for the DocLayout editor.
"""

import os
import sys
import logging
import traceback
from PySide6.QtWidgets import (QMainWindow, QWidget, QGridLayout, QStatusBar,
                               QFileDialog, QMessageBox, QInputDialog, QApplication)
from PySide6.QtCore import Qt, QSettings

from doclayout.core.i18n import tr

from ..scene import EditorScene
from ..view import EditorView
from ..rulers import Ruler
from .actions import ActionManager
from .menus import MenuManager
from .toolbars import ToolbarManager
from .dock_widgets import DockManager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """
    The primary window and coordinator of the application.
    """
    def __init__(self) -> None:
        """Initialize and assemble the main window."""
        super().__init__()
        self.setWindowTitle("DocLayout Editor")
        self.resize(1200, 800)
        
        self.scene = EditorScene()
        self.view = EditorView(self.scene)
        
        self._init_ui()
        self.actions_manager = ActionManager(self)
        MenuManager.setup_menus(self)
        ToolbarManager.setup_toolbars(self)
        DockManager.setup_docks(self)
        
        self.scene.toolChanged.connect(self._on_tool_changed)
        self._load_layout()

    def _init_ui(self) -> None:
        """Setup central widget with rulers and view."""
        central_widget = QWidget()
        layout = QGridLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.h_ruler = Ruler(Ruler.HORIZONTAL, self.view)
        self.v_ruler = Ruler(Ruler.VERTICAL, self.view)
        
        corner = QWidget()
        corner.setObjectName("RulerCorner")
        corner.setStyleSheet("QWidget#RulerCorner { background-color: #252525; border-right: 1px solid #3C3C3C; border-bottom: 1px solid #3C3C3C; }")
        
        layout.addWidget(corner, 0, 0)
        layout.addWidget(self.h_ruler, 0, 1)
        layout.addWidget(self.v_ruler, 1, 0)
        layout.addWidget(self.view, 1, 1)
        
        self.setCentralWidget(central_widget)
        
        self.view.viewportChanged.connect(lambda: [self.h_ruler.update(), self.v_ruler.update()])
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr('status.ready'))

    def _on_tool_changed(self, tool_name: str) -> None:
        """Update toolbars when tool changes in scene."""
        # This will be handled by the action group since they are checkable
        pass

    def save_file(self) -> None:
        """Handle save command."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Template", "", "JSON Files (*.json)")
        if not file_path:
            return
            
        if not file_path.lower().endswith(".json"):
            file_path += ".json"
            
        try:
            template = self.scene.to_template()
            from doclayout.core.io import save_to_json
            save_to_json(template, file_path)
            self.status_bar.showMessage(tr('status.file_saved', filename=file_path))
        except Exception as e:
            logger.error("Save error: %s", e)
            QMessageBox.critical(self, "Error", str(e))

    def open_file(self) -> None:
        """Handle open command."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Template", "", "JSON Files (*.json)")
        if not file_path:
            return
            
        try:
            from doclayout.core.io import load_template
            from ..items import get_item_for_model
            
            template = load_template(file_path)
            self._clear_editor()
            
            for item_model in template.items:
                item = get_item_for_model(item_model)
                if item:
                    self.scene.addItem(item)
            
            self.status_bar.showMessage(tr('status.file_loaded', filename=file_path))
        except Exception as e:
            logger.error("Open error: %s", e)
            QMessageBox.critical(self, "Error", str(e))

    def _clear_editor(self) -> None:
        self.scene.clear()
        if hasattr(self, 'structure_panel'):
            self.structure_panel.clear()

    def preview_pdf(self) -> None:
        """Generate and open a PDF preview."""
        try:
            template = self.scene.to_template()
            from doclayout.adapters.reportlab import ReportLabRenderer
            from doclayout.engine.export import TemplateExporter
            import subprocess
            
            exporter = TemplateExporter()
            renderer = ReportLabRenderer()
            output_path = "preview.pdf"
            
            exporter.export(template, renderer, output_path)
            self.status_bar.showMessage(tr('status.preview_generated', filename=output_path))
            
            # Open PDF with default viewer (safe from shell injection)
            if sys.platform == "linux":
                subprocess.run(["xdg-open", output_path], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["open", output_path], check=False)
            elif sys.platform == "win32":
                subprocess.run(["start", output_path], shell=True, check=False)
        except Exception as e:
            logger.error("Preview error: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", str(e))

    def new_file(self) -> None:
        self._clear_editor()
        self.status_bar.showMessage(tr('status.new_document'))

    def export_pdf(self) -> None:
        """Handle export PDF command."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if not file_path:
            return
            
        try:
            template = self.scene.to_template()
            from doclayout.adapters.reportlab import ReportLabRenderer
            from doclayout.engine.export import TemplateExporter
            
            exporter = TemplateExporter()
            renderer = ReportLabRenderer()
            
            exporter.export(template, renderer, file_path)
            self.status_bar.showMessage(tr('status.pdf_exported', filename=file_path))
        except Exception as e:
            logger.error("Export error: %s", e)
            QMessageBox.critical(self, "Error", str(e))

    def set_theme(self, theme_name: str) -> None:
        from ..themes import ThemeManager
        ThemeManager.apply_theme(QApplication.instance(), theme_name)
        self.scene.update()
        self.view.update()

    def _on_page_size_changed(self, index: int) -> None:
        data = self.page_size_combo.currentData()
        if data:
            self.scene.set_page_size(data[0], data[1])

    def _load_layout(self) -> None:
        settings = QSettings("DocLayout", "Editor")
        geometry = settings.value("geometry")
        state = settings.value("windowState")
        if geometry: self.restoreGeometry(geometry)
        if state: self.restoreState(state)
        self.prop_dock.show()
        self.library_dock.show()

    def closeEvent(self, event) -> None:
        settings = QSettings("DocLayout", "Editor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _reset_layout(self) -> None:
        self.addDockWidget(Qt.RightDockWidgetArea, self.prop_dock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_dock)
        self.prop_dock.show()
        self.library_dock.show()

    def _save_layout_named(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Layout", "Layout Name:")
        if ok and name:
            settings = QSettings("DocLayout", "Layouts")
            settings.setValue(f"layout_{name}", self.saveState())

    def _load_layout_named(self) -> None:
        settings = QSettings("DocLayout", "Layouts")
        layouts = [k.replace("layout_", "") for k in settings.allKeys() if k.startswith("layout_")]
        if not layouts: return
        name, ok = QInputDialog.getItem(self, "Load Layout", "Select Layout:", layouts, 0, False)
        if ok and name:
            state = settings.value(f"layout_{name}")
            if state: self.restoreState(state)

    def set_language(self, language_code: str) -> None:
        """Change application language and refresh UI."""
        from doclayout.core.i18n import get_translation_manager
        
        tm = get_translation_manager()
        if tm.set_language(language_code):
            self.status_bar.showMessage(tr('status.ready'))
            self.menuBar().clear()
            from .menus import MenuManager
            MenuManager.setup_menus(self)
            logger.info("Language changed to: %s", language_code)
