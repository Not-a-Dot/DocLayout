"""
Property editor widget for Line item.
"""

from PySide6.QtWidgets import QWidget, QFormLayout, QDoubleSpinBox, QPushButton, QComboBox
from PySide6.QtGui import QColor

class LinePropertiesWidget(QWidget):
    """
    Widget for editing Line specific properties.
    """
    def __init__(self, item, parent: QWidget = None) -> None:
        """
        Initialize properties widget.

        Args:
            item (LineEditorItem): The item to edit.
            parent (QWidget): Parent widget.
        """
        super().__init__(parent)
        self.item = item
        self.model = item.model
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.w_width = QDoubleSpinBox()
        self.w_width.setRange(0.1, 50.0)
        self.w_width.setValue(float(self.model.props.get("stroke_width", 2.0)))
        self.w_width.setSuffix(" pt")
        self.w_width.valueChanged.connect(self._on_width_changed)
        layout.addRow("Thickness:", self.w_width)
        
        self.btn_color = QPushButton()
        color = self.model.props.get("stroke_color", "#000000")
        self.btn_color.setStyleSheet(f"background-color: {color};")
        self.btn_color.clicked.connect(self._on_color_clicked)
        layout.addRow("Color:", self.btn_color)
        
        self.cmb_style = QComboBox()
        self.cmb_style.addItems(["Solid", "Dash", "Dot", "DashDot"])
        self.cmb_style.setCurrentText(self.model.props.get("stroke_style", "Solid"))
        self.cmb_style.currentTextChanged.connect(self._on_style_changed)
        layout.addRow("Style:", self.cmb_style)
        
        self.cmb_start_arrow = QComboBox()
        self.cmb_start_arrow.addItems(["None", "Triangle"])
        self.cmb_start_arrow.setCurrentText(self.model.props.get("start_arrow", "None"))
        self.cmb_start_arrow.currentTextChanged.connect(lambda t: self._on_arrow_changed("start_arrow", t))
        layout.addRow("Start Tip:", self.cmb_start_arrow)

        self.cmb_end_arrow = QComboBox()
        self.cmb_end_arrow.addItems(["None", "Triangle"])
        self.cmb_end_arrow.setCurrentText(self.model.props.get("end_arrow", "None"))
        self.cmb_end_arrow.currentTextChanged.connect(lambda t: self._on_arrow_changed("end_arrow", t))
        layout.addRow("End Tip:", self.cmb_end_arrow)

    def _on_arrow_changed(self, prop: str, value: str) -> None:
        self.model.props[prop] = value
        self.item.update()

    def _on_width_changed(self, val: float) -> None:
        self.model.props["stroke_width"] = val
        self.item.update_pen()

    def _on_color_clicked(self) -> None:
        from PySide6.QtWidgets import QColorDialog
        current = self.model.props.get("stroke_color", "#000000")
        color = QColorDialog.getColor(QColor(current), self, "Select Stroke Color")
        if color.isValid():
            hex_color = color.name()
            self.model.props["stroke_color"] = hex_color
            self.btn_color.setStyleSheet(f"background-color: {hex_color};")
            self.item.update_pen()

    def _on_style_changed(self, text: str) -> None:
        self.model.props["stroke_style"] = text
        self.item.update_pen()
