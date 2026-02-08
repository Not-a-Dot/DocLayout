"""
Collapsible section widget for property panels.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton, QFrame, QSizePolicy
from PySide6.QtCore import Qt

class CollapsibleSection(QWidget):
    """
    A widget that can be toggled to show or hide its content.
    
    Attributes:
        toggle_button (QToolButton): The button to toggle visibility.
        content_area (QFrame): The container for the internal widgets.
    """
    def __init__(self, title: str = "", parent: QWidget = None) -> None:
        """
        Initialize the collapsible section.

        Args:
            title (str): The title of the section.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)

        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("CollapsibleHeader")
        self.toggle_button.setStyleSheet("""
            QToolButton#CollapsibleHeader { 
                border: none; 
                font-weight: bold; 
                background-color: palette(button);
                padding: 6px;
                text-align: left;
            }
            QToolButton#CollapsibleHeader:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
        """)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.DownArrow)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.content_area = QFrame()
        self.content_area.setFrameShape(QFrame.NoFrame)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addWidget(self.content_area)

        self.toggle_button.toggled.connect(self.on_toggle)

    def on_toggle(self, checked: bool) -> None:
        """
        Handle toggle button state changes.

        Args:
            checked (bool): New state.
        """
        self.content_area.setVisible(checked)
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)

    def addWidget(self, widget: QWidget) -> None:
        """
        Add a widget to the content area.

        Args:
            widget (QWidget): Widget to add.
        """
        if not self.content_area.layout():
            layout = QVBoxLayout(self.content_area)
            layout.setContentsMargins(5, 5, 5, 5)
        self.content_area.layout().addWidget(widget)

    def setContentLayout(self, layout: QVBoxLayout) -> None:
        """
        Set the layout for the content area.

        Args:
            layout (QVBoxLayout): The layout to set.
        """
        self.content_area.setLayout(layout)
