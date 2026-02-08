"""
Theme Manager.
Handles switching between Light and Dark themes.
"""

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)

class ThemeManager:
    LIGHT = "Light"
    DARK = "Dark"

    @staticmethod
    def get_available_themes() -> list[str]:
        import os
        theme_dir = os.path.join(os.path.dirname(__file__), "..", "themes")
        themes = ["Light", "Dark"] # Built-in themes
        if os.path.exists(theme_dir):
            for f in os.listdir(theme_dir):
                if f.endswith(".json"):
                    name = f.replace(".json", "").replace("_", " ").title()
                    if name not in themes:
                        themes.append(name)
        return sorted(themes)

    @staticmethod
    def apply_theme(app: QApplication, theme_name: str):
        if theme_name == "Light":
            ThemeManager._apply_light_theme(app)
            return

        if theme_name == "Dark":
            ThemeManager._apply_dark_fusion(app)
            return

        # Load from JSON
        import json
        import os
        
        filename = theme_name.lower().replace(" ", "_") + ".json"
        theme_dir = os.path.join(os.path.dirname(__file__), "..", "themes")
        path = os.path.join(theme_dir, filename)
        
        if not os.path.exists(path):
            return

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if "style" in data:
                app.setStyle(data["style"])
                
            if "palette" in data:
                palette = QPalette()
                for role_name, color_hex in data["palette"].items():
                    if hasattr(QPalette, role_name):
                        role = getattr(QPalette, role_name)
                        palette.setColor(role, QColor(color_hex))
                app.setPalette(palette)
            
            if "stylesheet" in data:
                app.setStyleSheet(data["stylesheet"])
                
        except Exception as e:
            logger.error("Error applying theme %s: %s", theme_name, e, exc_info=True)

    @staticmethod
    def _apply_dark_fusion(app: QApplication):
        app.setStyle("Fusion")
        dark_palette = QPalette()

        # Premium Dark Palette colors
        bg_color = QColor(30, 30, 30)
        base_color = QColor(25, 25, 25)
        text_color = QColor(210, 210, 210)
        highlight_color = QColor(0, 120, 215)
        border_color = QColor(60, 60, 60)

        dark_palette.setColor(QPalette.Window, bg_color)
        dark_palette.setColor(QPalette.WindowText, text_color)
        dark_palette.setColor(QPalette.Base, base_color)
        dark_palette.setColor(QPalette.AlternateBase, bg_color)
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, text_color)
        dark_palette.setColor(QPalette.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ButtonText, text_color)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, highlight_color)
        dark_palette.setColor(QPalette.Highlight, highlight_color)
        dark_palette.setColor(QPalette.HighlightedText, Qt.white)
        
        # Editor specific
        dark_palette.setColor(QPalette.Shadow, QColor(0, 0, 0, 0)) # No shadow
        dark_palette.setColor(QPalette.Mid, QColor(80, 80, 80)) # Grid color

        app.setPalette(dark_palette)
        
        # Premium Stylesheet
        app.setStyleSheet(f"""
            QMainWindow, QDockWidget {{
                background-color: #1E1E1E;
            }}
            QMenuBar {{
                background-color: #1E1E1E;
                color: #D2D2D2;
                border-bottom: 1px solid #3C3C3C;
            }}
            QMenuBar::item:selected {{
                background-color: #3C3C3C;
            }}
            QToolBar {{
                background-color: #252525;
                border: none;
                border-bottom: 1px solid #3C3C3C;
                padding: 4px;
                spacing: 6px;
            }}
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background-color: #3C3C3C;
                border: 1px solid #505050;
            }}
            QToolButton:checked {{
                background-color: #0078D7;
            }}
            QStatusBar {{
                background-color: #1E1E1E;
                color: #888888;
                border-top: 1px solid #3C3C3C;
            }}
            QDockWidget {{
                color: #D2D2D2;
                font-weight: bold;
                titlebar-close-icon: url(close.png); /* Placeholder for custom icons */
                titlebar-normal-icon: url(undock.png);
            }}
            QDockWidget::title {{
                background-color: #252525;
                padding: 8px;
                border-bottom: 1px solid #3C3C3C;
            }}
            QScrollArea, QListWidget, QTreeView, QLineEdit, QComboBox, QAbstractSpinBox {{
                background-color: #191919;
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                color: #D2D2D2;
                padding: 2px;
            }}
            QPushButton {{
                background-color: #3C3C3C;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px 12px;
                color: #D2D2D2;
            }}
            QPushButton:hover {{
                background-color: #4C4C4C;
            }}
            QPushButton:pressed {{
                background-color: #2A2A2A;
            }}
            QToolTip {{
                background-color: #3C3C3C;
                color: white;
                border: 1px solid #505050;
            }}
        """)
    @staticmethod
    def _apply_light_theme(app: QApplication):
        app.setStyle("Fusion")
        palette = app.style().standardPalette()
        
        # UI Background (Light Gray)
        bg = QColor(245, 245, 245)
        # Control Background (White)
        base = QColor(255, 255, 255)
        
        palette.setColor(QPalette.Window, bg)
        palette.setColor(QPalette.WindowText, QColor(40, 40, 40))
        palette.setColor(QPalette.Base, base)
        palette.setColor(QPalette.AlternateBase, QColor(250, 250, 250))
        palette.setColor(QPalette.Text, QColor(20, 20, 20))
        palette.setColor(QPalette.Button, QColor(235, 235, 235))
        palette.setColor(QPalette.ButtonText, QColor(20, 20, 20))
        palette.setColor(QPalette.Highlight, QColor(0, 120, 215))
        
        # Zero Shadow
        palette.setColor(QPalette.Shadow, QColor(0, 0, 0, 0))
        # Grid line color stored in Mid
        palette.setColor(QPalette.Mid, QColor(210, 210, 210))
        
        app.setPalette(palette)
        app.setStyleSheet("""
            QMainWindow, QDockWidget { background-color: #F5F5F5; }
            QToolBar { background-color: #FFFFFF; border-bottom: 1px solid #D0D0D0; padding: 2px; }
            QMenuBar { background-color: #FFFFFF; border-bottom: 1px solid #D0D0D0; }
            QDockWidget::title { background-color: #E8E8E8; padding: 6px; border-bottom: 1px solid #D0D0D0; }
            QScrollArea, QListWidget, QTreeView, QLineEdit, QComboBox { 
                background-color: white; 
                border: 1px solid #D0D0D0; 
                border-radius: 2px;
            }
        """)

    @staticmethod
    def get_editor_colors():
        """Returns colors for the graphics scene. ALWAYS PURE WHITE PAGE."""
        palette = QApplication.palette()
        bg = palette.color(QPalette.Window)
        
        # Dynamic grid color based on background lightness
        if bg.lightness() < 128:
            grid = QColor(80, 80, 80) # Dark mode grid
        else:
            grid = QColor(220, 220, 220) # Light mode grid
            
        return {
            "background": bg,
            "page": QColor(255, 255, 255), # PURE WHITE PAGE
            "grid": grid,
            "shadow": QColor(0, 0, 0, 0)   # ZERO SHADOW
        }
