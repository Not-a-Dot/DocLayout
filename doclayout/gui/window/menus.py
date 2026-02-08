"""
Menu bar configuration for the Main Window.
"""

from PySide6.QtWidgets import QMenu, QApplication
from PySide6.QtGui import QAction, QActionGroup
from doclayout.core.i18n import tr, get_translation_manager

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
        file_menu = menubar.addMenu(tr('menu.file.title'))
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
        edit_menu = menubar.addMenu(tr('menu.edit.title'))
        
        # Language Submenu
        lang_menu = QMenu(tr('settings.language'), parent)
        edit_menu.addMenu(lang_menu)
        
        tm = get_translation_manager()
        languages = tm.get_available_languages()
        lang_group = QActionGroup(parent)
        lang_group.setExclusive(True)
        
        current_lang = tm.get_current_language()
        for lang_code, lang_name in languages.items():
            action = QAction(lang_name, parent)
            action.setCheckable(True)
            if lang_code == current_lang:
                action.setChecked(True)
            action.triggered.connect(lambda checked=False, code=lang_code: parent.set_language(code))
            lang_menu.addAction(action)
            lang_group.addAction(action)
        
        # Arrange Menu
        arrange_menu = menubar.addMenu(tr('menu.arrange.title'))
        arrange_menu.addAction(acts.bring_front_action)
        arrange_menu.addAction(acts.send_back_action)
        arrange_menu.addSeparator()
        arrange_menu.addAction(acts.group_action)
        
        # View Menu
        view_menu = menubar.addMenu(tr('menu.view.title'))
        view_menu.addSeparator()
        
        # Themes Submenu
        theme_menu = QMenu(tr('settings.theme'), parent)
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
        layout_menu = menubar.addMenu(tr('menu.tools.title'))
        layout_menu.addAction(acts.save_layout_action)
        layout_menu.addAction(acts.load_layout_action)
        layout_menu.addAction(acts.reset_layout_action)
