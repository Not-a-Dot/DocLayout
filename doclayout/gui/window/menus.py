"""
Menu bar configuration for the Main Window.
"""

from PySide6.QtWidgets import QMenu, QApplication
from PySide6.QtGui import QAction, QActionGroup

class MenuManager:
    """
    Handles creation and population of the window's menu bar.
    """
    @staticmethod
    def setup_menus(parent) -> None:
        """
        Create all menus and attach actions.

        Args:
            parent (MainWindow): The target window.
        """
        menubar = parent.menuBar()
        acts = parent.actions_manager
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(acts.new_action)
        file_menu.addSeparator()
        file_menu.addAction(acts.open_action)
        file_menu.addAction(acts.save_action)
        file_menu.addSeparator()
        file_menu.addAction(acts.preview_action)
        file_menu.addAction(acts.export_pdf_action)
        file_menu.addSeparator()
        file_menu.addAction(acts.exit_action)
        
        # Edit Menu
        menubar.addMenu("&Edit")
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(acts.group_action)
        view_menu.addSeparator()
        
        # Themes Submenu
        theme_menu = QMenu("Theme", parent)
        view_menu.addMenu(theme_menu)
        
        from ..themes import ThemeManager
        themes = ThemeManager.get_available_themes()
        theme_group = QActionGroup(parent)
        theme_group.setExclusive(True)
        
        for theme_name in themes:
            action = QAction(theme_name, parent)
            action.setCheckable(True)
            if theme_name == "Dark":
                action.setChecked(True)
            action.triggered.connect(lambda checked=False, name=theme_name: parent.set_theme(name))
            theme_menu.addAction(action)
            theme_group.addAction(action)
            
        # Layout Menu
        layout_menu = menubar.addMenu("&Layout")
        layout_menu.addAction(acts.save_layout_action)
        layout_menu.addAction(acts.load_layout_action)
        layout_menu.addAction(acts.reset_layout_action)
