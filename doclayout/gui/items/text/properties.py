"""
Property editor widget for Text item.
"""

from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox, 
                               QFontComboBox, QCheckBox, QHBoxLayout, 
                               QPushButton, QButtonGroup)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class TextPropertiesWidget(QWidget):
    """
    Widget for editing Text specific properties.
    """
    def __init__(self, item, parent: QWidget = None) -> None:
        """
        Initialize properties widget.

        Args:
            item (TextEditorItem): The item to edit.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.item = item
        self.model = item.model
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._prop_text = QLineEdit(self.model.props.get("text", ""))
        self._prop_text.textChanged.connect(self._on_prop_text_changed)
        layout.addRow("Content:", self._prop_text)
        
        self._prop_font_family = QFontComboBox()
        self._prop_font_family.setCurrentText(self.model.props.get("font_family", "Arial"))
        self._prop_font_family.currentFontChanged.connect(lambda f: self._on_prop_font_changed())
        layout.addRow("Font Family:", self._prop_font_family)
        
        self._prop_font_size = QSpinBox()
        self._prop_font_size.setRange(1, 144)
        self._prop_font_size.setValue(self.model.props.get("font_size", 12))
        self._prop_font_size.valueChanged.connect(lambda v: self._on_prop_font_changed())
        layout.addRow("Font Size:", self._prop_font_size)

        self._btn_color = QPushButton()
        self._btn_color.setFixedWidth(40)
        curr_color = self.model.props.get("color", "black")
        self._btn_color.setStyleSheet(f"background-color: {curr_color};")
        self._btn_color.clicked.connect(self._on_prop_color_clicked)
        layout.addRow("Color:", self._btn_color)
        
        styles_layout = QHBoxLayout()
        self._prop_font_bold = QCheckBox("Bold")
        self._prop_font_bold.setChecked(self.model.props.get("font_bold", False))
        self._prop_font_bold.toggled.connect(lambda v: self._on_prop_font_changed())
        
        self._prop_font_italic = QCheckBox("Italic")
        self._prop_font_italic.setChecked(self.model.props.get("font_italic", False))
        self._prop_font_italic.toggled.connect(lambda v: self._on_prop_font_changed())
        
        styles_layout.addWidget(self._prop_font_bold)
        styles_layout.addWidget(self._prop_font_italic)
        layout.addRow("Styles:", styles_layout)
        
        # Alignment
        align_layout = QHBoxLayout()
        self._btn_left = QPushButton("L")
        self._btn_center = QPushButton("C")
        self._btn_right = QPushButton("R")
        for btn in [self._btn_left, self._btn_center, self._btn_right]:
            btn.setCheckable(True)
        
        self._align_group = QButtonGroup(self)
        self._align_group.addButton(self._btn_left)
        self._align_group.addButton(self._btn_center)
        self._align_group.addButton(self._btn_right)
        self._align_group.setExclusive(True)
        
        align = self.model.props.get("text_align", "left")
        if align == "left": self._btn_left.setChecked(True)
        elif align == "center": self._btn_center.setChecked(True)
        elif align == "right": self._btn_right.setChecked(True)
        
        self._btn_left.clicked.connect(lambda: self._on_prop_align_changed("left"))
        self._btn_center.clicked.connect(lambda: self._on_prop_align_changed("center"))
        self._btn_right.clicked.connect(lambda: self._on_prop_align_changed("right"))
        
        align_layout.addWidget(self._btn_left)
        align_layout.addWidget(self._btn_center)
        align_layout.addWidget(self._btn_right)
        layout.addRow("Alignment:", align_layout)

    def _on_prop_color_clicked(self) -> None:
        from PySide6.QtWidgets import QColorDialog
        curr = QColor(self.model.props.get("color", "black"))
        color = QColorDialog.getColor(curr, self, "Select Text Color")
        if color.isValid():
            hex_color = color.name()
            self.model.props["color"] = hex_color
            self._btn_color.setStyleSheet(f"background-color: {hex_color};")
            self.item.setDefaultTextColor(color)

    def _on_prop_text_changed(self, text: str) -> None:
        self.model.props["text"] = text
        self.item.setPlainText(text)
        
    def _on_prop_font_changed(self) -> None:
        self.model.props["font_family"] = self._prop_font_family.currentFont().family()
        self.model.props["font_size"] = self._prop_font_size.value()
        self.model.props["font_bold"] = self._prop_font_bold.isChecked()
        self.model.props["font_italic"] = self._prop_font_italic.isChecked()
        self.item.update_visual_font()
        
    def _on_prop_align_changed(self, align: str) -> None:
        self.model.props["text_align"] = align
        self.item.update_alignment(align)
