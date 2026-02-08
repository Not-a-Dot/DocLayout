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
        self._update_pixmap()
        
        from ..handles import ResizeHandle
        self._handles = [
            ResizeHandle(ResizeHandle.TOP_LEFT, self),
            ResizeHandle(ResizeHandle.TOP_RIGHT, self),
            ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self),
            ResizeHandle(ResizeHandle.BOTTOM_LEFT, self),
            ResizeHandle(ResizeHandle.TOP, self),
            ResizeHandle(ResizeHandle.BOTTOM, self),
            ResizeHandle(ResizeHandle.LEFT, self),
            ResizeHandle(ResizeHandle.RIGHT, self),
        ]
        for h in self._handles:
            h.setVisible(False)

    def paint(self, painter, option, widget):
        props = self.model.props
        bg_type = props.get("bg_type", "transparent")
        
        if bg_type == "image" and self._bg_pixmap:
            painter.drawPixmap(self.rect(), self._bg_pixmap, QRectF(self._bg_pixmap.rect()))
        elif bg_type == "solid":
            color = QColor(props.get("fill_color", "#ffffff"))
            color.setAlpha(props.get("opacity", 255))
            painter.setBrush(QBrush(color))
        else:
            painter.setBrush(Qt.NoBrush)
            
        # Stroke
        show_outline = props.get("show_outline", False)
        if show_outline:
            from doclayout.core.geometry import PT_TO_MM
            width_pt = float(props.get("stroke_width", 1.0))
            width_mm = width_pt * PT_TO_MM
            
            pen = QPen()
            stroke_color = props.get("stroke_color", "#000000")
            pen.setColor(QColor(stroke_color))
            pen.setWidthF(width_mm)
            pen.setCosmetic(False)
            painter.setPen(pen)
        else:
            # Guide mode for editor
            guide_pen = QPen(QColor(200, 200, 200))
            guide_pen.setStyle(Qt.DashLine)
            guide_pen.setWidthF(0.2)
            painter.setPen(guide_pen)
            
        super().paint(painter, option, widget)
        self.paint_lock_icons(painter)

    def _update_pixmap(self):
        """Update background pixmap if using image background."""
        bg_type = self.model.props.get("bg_type", "transparent")
        img_path = self.model.props.get("bg_image")
        if bg_type == "image" and img_path:
            from PySide6.QtGui import QPixmap
            self._bg_pixmap = QPixmap(img_path)
        else:
            self._bg_pixmap = None
        self.update()

    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QComboBox, QPushButton, QHBoxLayout, QSpinBox, QFileDialog, QCheckBox, QDoubleSpinBox
        from PySide6.QtGui import QColor
        
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        layout.setContentsMargins(0,0,0,0)
        
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
        self._update_pixmap()

    def _on_opacity_changed(self, val):
        self.model.props["opacity"] = val
        self.update()

    def _on_color_clicked(self, prop_name, btn):
        from PySide6.QtWidgets import QColorDialog
        from PySide6.QtGui import QColor
        curr = QColor(self.model.props.get(prop_name, "#ffffff"))
        color = QColorDialog.getColor(curr, None, f"Select {prop_name}")
        if color.isValid():
            hex_color = color.name()
            self.model.props[prop_name] = hex_color
            self._update_btn_color(btn, hex_color)
            self.update()

    def _on_bg_image_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(None, "Select BG Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.model.props["bg_image"] = path
            self._update_pixmap()

    def get_bindable_properties(self):
        return ["fill_color", "stroke_color", "stroke_width", "opacity", "show_outline"]

    def setRect(self, *args):
        super().setRect(*args)
        if hasattr(self, 'model'):
            self.model.width = self.rect().width()
            self.model.height = self.rect().height()
        self.update_handles()
