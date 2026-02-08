"""
Property editor widget for KV Box item.
"""

from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QSpinBox, 
                               QFontComboBox, QCheckBox, QHBoxLayout, 
                               QPushButton, QDoubleSpinBox, QComboBox)
from PySide6.QtGui import QColor

class KVBoxPropertiesWidget(QWidget):
    """
    Widget for editing KVBox specific properties.
    """
    def __init__(self, item, parent: QWidget = None) -> None:
        """
        Initialize properties widget.

        Args:
            item (KVBoxEditorItem): The item to edit.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.item = item
        self.model = item.model
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        props = self.model.props
        
        self._prop_key = QLineEdit(props.get("key_text", "Label:"))
        self._prop_key.textChanged.connect(self._on_key_changed)
        layout.addRow("Label Text:", self._prop_key)
        
        self._prop_val = QLineEdit(props.get("text", "[Value]"))
        self._prop_val.setPlaceholderText("API bound value...")
        self._prop_val.textChanged.connect(self._on_val_changed)
        layout.addRow("Default Value:", self._prop_val)
        
        # Split Controls
        self._prop_split_type = QComboBox()
        self._prop_split_type.addItems(["Ratio (%)", "Fixed (mm)", "Auto"])
        stype_map = {"ratio": 0, "fixed": 1, "auto": 2}
        self._prop_split_type.setCurrentIndex(stype_map.get(props.get("split_type", "ratio"), 0))
        self._prop_split_type.currentIndexChanged.connect(self._on_split_type_changed)
        layout.addRow("Split Mode:", self._prop_split_type)
        
        self._split_stack = QWidget()
        split_layout = QHBoxLayout(self._split_stack)
        split_layout.setContentsMargins(0, 0, 0, 0)
        
        self._prop_split_ratio = QDoubleSpinBox()
        self._prop_split_ratio.setRange(0.1, 0.9)
        self._prop_split_ratio.setSingleStep(0.05)
        self._prop_split_ratio.setValue(props.get("split_ratio", 0.4))
        self._prop_split_ratio.valueChanged.connect(self._on_split_ratio_changed)
        
        self._prop_split_fixed = QDoubleSpinBox()
        self._prop_split_fixed.setRange(1.0, 500.0)
        self._prop_split_fixed.setSuffix(" mm")
        self._prop_split_fixed.setValue(props.get("split_fixed", 20.0))
        self._prop_split_fixed.valueChanged.connect(self._on_split_fixed_changed)
        
        split_layout.addWidget(self._prop_split_ratio)
        split_layout.addWidget(self._prop_split_fixed)
        layout.addRow("Split Value:", self._split_stack)
        
        self._update_split_ui_visibility()
        
        # Style Controls
        self._prop_font_family = QFontComboBox()
        self._prop_font_family.setCurrentText(props.get("font_family", "Arial"))
        self._prop_font_family.currentFontChanged.connect(self._on_style_changed)
        layout.addRow("Font:", self._prop_font_family)
        
        size_layout = QHBoxLayout()
        self._prop_font_size = QSpinBox()
        self._prop_font_size.setRange(1, 144)
        self._prop_font_size.setValue(props.get("font_size", 10))
        self._prop_font_size.valueChanged.connect(self._on_style_changed)
        size_layout.addWidget(self._prop_font_size)
        
        self._btn_color = QPushButton()
        self._btn_color.setFixedWidth(40)
        self._update_btn_color(self._btn_color, props.get("color", "black"))
        self._btn_color.clicked.connect(self._on_text_color_clicked)
        size_layout.addWidget(self._btn_color)
        layout.addRow("Size/Color:", size_layout)
        
        self._prop_bold = QCheckBox("Bold")
        self._prop_bold.setChecked(props.get("font_bold", False))
        self._prop_bold.toggled.connect(self._on_style_changed)
        
        self._prop_italic = QCheckBox("Italic")
        self._prop_italic.setChecked(props.get("font_italic", False))
        self._prop_italic.toggled.connect(self._on_style_changed)
        
        styles = QHBoxLayout()
        styles.addWidget(self._prop_bold)
        styles.addWidget(self._prop_italic)
        layout.addRow("", styles)
        
        layout.addRow("--- Styling ---", QWidget())
        
        self._prop_show_outline = QCheckBox("Show Outline")
        self._prop_show_outline.setChecked(props.get("show_outline", True))
        self._prop_show_outline.toggled.connect(self._on_outline_toggled)
        layout.addRow("", self._prop_show_outline)
        
        self._prop_stroke_w = QDoubleSpinBox()
        self._prop_stroke_w.setRange(0.1, 5.0)
        self._prop_stroke_w.setSingleStep(0.1)
        self._prop_stroke_w.setValue(props.get("stroke_width", 0.5))
        self._prop_stroke_w.valueChanged.connect(self._on_stroke_changed)
        layout.addRow("Border Width:", self._prop_stroke_w)
        
        color_row = QHBoxLayout()
        self._btn_border_color = QPushButton("Border")
        self._update_btn_color(self._btn_border_color, props.get("border_color", "black"))
        self._btn_border_color.clicked.connect(lambda: self._on_generic_color_clicked("border_color", self._btn_border_color))
        color_row.addWidget(self._btn_border_color)
        
        self._btn_div_color = QPushButton("Divider")
        self._update_btn_color(self._btn_div_color, props.get("divider_color", "black"))
        self._btn_div_color.clicked.connect(lambda: self._on_generic_color_clicked("divider_color", self._btn_div_color))
        color_row.addWidget(self._btn_div_color)
        layout.addRow("Colors:", color_row)

    def _on_key_changed(self, text: str) -> None:
        self.model.props["key_text"] = text
        self.item.update_visuals()

    def _on_val_changed(self, text: str) -> None:
        self.model.props["text"] = text
        self.item.update_visuals()

    def _on_split_type_changed(self, index: int) -> None:
        types = ["ratio", "fixed", "auto"]
        self.model.props["split_type"] = types[index]
        self._update_split_ui_visibility()
        self.item.update_visuals()

    def _update_split_ui_visibility(self) -> None:
        stype = self.model.props.get("split_type", "ratio")
        self._prop_split_ratio.setVisible(stype == "ratio")
        self._prop_split_fixed.setVisible(stype == "fixed")

    def _on_split_ratio_changed(self, val: float) -> None:
        self.model.props["split_ratio"] = val
        self.item.update_visuals()

    def _on_split_fixed_changed(self, val: float) -> None:
        self.model.props["split_fixed"] = val
        self.item.update_visuals()

    def _on_outline_toggled(self, checked: bool) -> None:
        self.model.props["show_outline"] = checked
        self.item.update()

    def _on_stroke_changed(self, val: float) -> None:
        self.model.props["stroke_width"] = val
        self.item.update()

    def _on_style_changed(self) -> None:
        self.model.props["font_family"] = self._prop_font_family.currentFont().family()
        self.model.props["font_size"] = self._prop_font_size.value()
        self.model.props["font_bold"] = self._prop_bold.isChecked()
        self.model.props["font_italic"] = self._prop_italic.isChecked()
        self.item.update_visuals()

    def _update_btn_color(self, btn: QPushButton, hex_color: str) -> None:
        fg = "white" if hex_color in ("black", "#000000") else "black"
        btn.setStyleSheet(f"background-color: {hex_color}; color: {fg};")

    def _on_text_color_clicked(self) -> None:
        from PySide6.QtWidgets import QColorDialog
        curr = QColor(self.model.props.get("color", "black"))
        color = QColorDialog.getColor(curr, self, "Select Text Color")
        if color.isValid():
            hex_color = color.name()
            self.model.props["color"] = hex_color
            self._update_btn_color(self._btn_color, hex_color)
            self.item.update_visuals()

    def _on_generic_color_clicked(self, prop_key: str, btn: QPushButton) -> None:
        from PySide6.QtWidgets import QColorDialog
        curr = QColor(self.model.props.get(prop_key, "black"))
        color = QColorDialog.getColor(curr, self, f"Select {prop_key}")
        if color.isValid():
            hex_color = color.name()
            self.model.props[prop_key] = hex_color
            self._update_btn_color(btn, hex_color)
            self.item.update()
