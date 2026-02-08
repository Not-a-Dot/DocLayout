from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QPixmap, QPainter
from doclayout.core.models import BaseElement
from .base import BaseEditorItem

class RectEditorItem(BaseEditorItem, QGraphicsRectItem):
    def __init__(self, model: BaseElement):
        QGraphicsRectItem.__init__(self, 0, 0, model.width, model.height)
        BaseEditorItem.__init__(self, model)
        self.setPos(model.x, model.y)
        
        self._bg_pixmap = None
        self._update_visuals()
        
        from ..handles import ResizeHandle
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)

    def _update_visuals(self):
        props = self.model.props
        bg_type = props.get("bg_type", "transparent")
        fill_color = props.get("fill_color", "#ffffff")
        outline_color = props.get("stroke_color", "#000000")
        alpha = props.get("opacity", 255)
        
        # Pen
        self.setPen(QPen(QColor(outline_color), 1))
        
        # Brush
        if bg_type == "solid":
            color = QColor(fill_color)
            color.setAlpha(alpha)
            self.setBrush(QBrush(color))
        else:
            self.setBrush(Qt.NoBrush)
            
        # Image BG
        img_path = props.get("bg_image")
        if bg_type == "image" and img_path:
            self._bg_pixmap = QPixmap(img_path)
        else:
            self._bg_pixmap = None
            
        self.update()

    def paint(self, painter, option, widget):
        if self.model.props.get("bg_type") == "image" and self._bg_pixmap:
            painter.drawPixmap(self.rect(), self._bg_pixmap, QRectF(self._bg_pixmap.rect()))
            
        # Set stroke width if enabled
        show_outline = self.model.props.get("show_outline", False)
        if show_outline:
            from doclayout.core.geometry import PT_TO_MM
            width_pt = float(self.model.props.get("stroke_width", 1.0))
            width_mm = width_pt * PT_TO_MM
            
            pen = self.pen()
            stroke_color = self.model.props.get("stroke_color", "#000000")
            pen.setColor(QColor(stroke_color))
            pen.setWidthF(width_mm)
            pen.setCosmetic(False)
            painter.setPen(pen)
            
            # Draw rect manually to ensure pen is used? 
            # super().paint() uses self.pen() which we just updated? 
            # No, self.pen() returns a copy or ref? 
            # QGraphicsItem.setPen() updates internal state.
            self.setPen(pen)
        else:
            # Guide mode for editor
            guide_pen = QPen(QColor(200, 200, 200))
            guide_pen.setStyle(Qt.DashLine)
            guide_pen.setWidthF(0.2)
            painter.setPen(guide_pen)
            self.setPen(guide_pen)
            
        # We need to call super paint to draw the brush/rect
        super().paint(painter, option, widget)
        self.paint_lock_icons(painter)

    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QPushButton, QHBoxLayout, QSpinBox, QFileDialog, QCheckBox, QDoubleSpinBox
        from PySide6.QtGui import QColor
        
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        
        # Background Type
        self._prop_bg_type = QComboBox()
        self._prop_bg_type.addItems(["transparent", "solid", "image"])
        self._prop_bg_type.setCurrentText(self.model.props.get("bg_type", "transparent"))
        self._prop_bg_type.currentTextChanged.connect(self._on_bg_type_changed)
        layout.addRow("BG Type:", self._prop_bg_type)
        
        # Fill Color
        self._btn_fill = QPushButton()
        self._btn_fill.setFixedWidth(40)
        self._update_btn_color(self._btn_fill, self.model.props.get("fill_color", "#ffffff"))
        self._btn_fill.clicked.connect(lambda: self._on_color_clicked("fill_color", self._btn_fill))
        layout.addRow("Fill Color:", self._btn_fill)
        
        # Outline Color
        self._btn_outline = QPushButton()
        self._btn_outline.setFixedWidth(40)
        self._update_btn_color(self._btn_outline, self.model.props.get("stroke_color", "#000000"))
        self._btn_outline.clicked.connect(lambda: self._on_color_clicked("stroke_color", self._btn_outline))
        layout.addRow("Outline Color:", self._btn_outline)
        
        # Opacity
        self._prop_opacity = QSpinBox()
        self._prop_opacity.setRange(0, 255)
        self._prop_opacity.setValue(self.model.props.get("opacity", 255))
        self._prop_opacity.valueChanged.connect(self._on_opacity_changed)
        layout.addRow("Opacity:", self._prop_opacity)
        
        # BG Image
        self._btn_bg_img = QPushButton("Select Image...")
        self._btn_bg_img.clicked.connect(self._on_bg_image_clicked)
        layout.addRow("BG Image:", self._btn_bg_img)
        
        # Outline Options
        self._prop_show_outline = QCheckBox("Show Outline")
        self._prop_show_outline.setChecked(self.model.props.get("show_outline", False))
        self._prop_show_outline.toggled.connect(self._on_show_outline_toggled)
        layout.addRow("", self._prop_show_outline)
        
        self._prop_stroke_w = QDoubleSpinBox()
        self._prop_stroke_w.setRange(0.1, 20.0)
        self._prop_stroke_w.setSingleStep(0.1)
        self._prop_stroke_w.setValue(self.model.props.get("stroke_width", 1.0))
        self._prop_stroke_w.valueChanged.connect(self._on_stroke_width_changed)
        layout.addRow("Stroke Width:", self._prop_stroke_w)
        
        return widget

    def _on_show_outline_toggled(self, checked):
        self.model.props["show_outline"] = checked
        self.update()

    def _on_stroke_width_changed(self, val):
        self.model.props["stroke_width"] = val
        self.update()

    def _update_btn_color(self, btn, color_hex):
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid gray;")

    def _on_bg_type_changed(self, text):
        self.model.props["bg_type"] = text
        self._update_visuals()

    def _on_opacity_changed(self, val):
        self.model.props["opacity"] = val
        self._update_visuals()

    def _on_color_clicked(self, prop_name, btn):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        curr = QColor(self.model.props.get(prop_name, "#ffffff"))
        color = QColorDialog.getColor(curr, None, f"Select {prop_name}")
        if color.isValid():
            hex_color = color.name()
            self.model.props[prop_name] = hex_color
            self._update_btn_color(btn, hex_color)
            self._update_visuals()

    def _on_bg_image_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(None, "Select BG Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.model.props["bg_image"] = path
            self._update_visuals()

    def get_bindable_properties(self):
        return ["fill_color", "stroke_color", "stroke_width", "opacity", "show_outline"]

    def setRect(self, *args):
        super().setRect(*args)
        if hasattr(self, 'model'):
            self.model.width = self.rect().width()
            self.model.height = self.rect().height()
        self.update_handles()
