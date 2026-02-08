from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush
from .base import BaseEditorItem
from doclayout.core.models import BaseElement

class ContainerEditorItem(BaseEditorItem, QGraphicsRectItem):
    """
    A container item that groups other items.
    Handles auto-flow logic: moving siblings when resized.
    """
    def __init__(self, model: BaseElement):
        QGraphicsRectItem.__init__(self, 0, 0, model.width, model.height)
        BaseEditorItem.__init__(self, model)
        
        self.setPos(model.x, model.y)
        self.update()
        
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
        
        # Track previous height for delta calculation
        self._last_height = model.height

    def paint(self, painter, option, widget):
        # Set stroke width if enabled
        show_outline = self.model.props.get("show_outline", False)
        if show_outline:
            from doclayout.core.geometry import PT_TO_MM
            width_pt = float(self.model.props.get("stroke_width", 1.0))
            width_mm = width_pt * PT_TO_MM
            
            pen = QPen()
            stroke_color = self.model.props.get("stroke_color", "#000000")
            pen.setColor(QColor(stroke_color))
            pen.setWidthF(width_mm)
            pen.setStyle(Qt.SolidLine)
            pen.setCosmetic(False)
            painter.setPen(pen)
        else:
            # Guide mode
            pen = QPen(QColor(100, 100, 100))
            pen.setStyle(Qt.DashLine)
            pen.setWidthF(0.2)
            painter.setPen(pen)

        # Fill
        bg_type = self.model.props.get("bg_type", "transparent")
        if bg_type == "solid":
            color = QColor(self.model.props.get("fill_color", "#ffffff"))
            color.setAlpha(self.model.props.get("opacity", 255))
            painter.setBrush(QBrush(color))
        else:
            painter.setBrush(Qt.NoBrush)

        super().paint(painter, option, widget)
        self.paint_lock_icons(painter)

    def setRect(self, x, y, w, h):
        """Called by ResizeHandle."""
        old_h = self.rect().height()
        
        super().setRect(0, 0, w, h)
        self.model.width = w
        self.model.height = h
        self.update_handles()
        
        # Auto-Flow Logic
        # If height changed, find siblings below and move them
        delta_h = h - old_h
        if abs(delta_h) > 0.1: # Threshold
             self._apply_auto_flow(delta_h)
             
        self._last_height = h

    def _apply_auto_flow(self, delta_h):
        """
        Move sibling items that are visually below this container.
        """
        scene = self.scene()
        if not scene:
            return
            
        my_y = self.scenePos().y() if self.scenePos() else self.model.y
        old_bottom = my_y + (self.rect().height() - delta_h)
        
        siblings = []
        parent_item = self.parentItem()
        if parent_item:
            siblings = parent_item.childItems()
        else:
            siblings = scene.items()
            
        for item in siblings:
            if item == self: 
                continue
            if not isinstance(item, BaseEditorItem):
                continue
            # Avoid moving parent or unrelated
            if item.parentItem() != self.parentItem():
                continue
                
            # Check if item is below
            item_y = item.scenePos().y()
            
            # If item top was at or below my old bottom (roughly)
            # Add a small tolerance
            if item_y >= (old_bottom - 1.0):
                # Move it
                item.moveBy(0, delta_h)
                # Update model
                item.model.y += delta_h



    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QCheckBox, QComboBox, QPushButton, QDoubleSpinBox, QSpinBox, QLabel
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        
        lbl = QLineEdit("Container")
        lbl.setReadOnly(True)
        layout.addRow("Type:", lbl)
        
        lock_box = QCheckBox("Lock Children")
        lock_box.setChecked(self.model.props.get("lock_children", False))
        lock_box.toggled.connect(lambda v: self.model.props.update({"lock_children": v}))
        layout.addRow("Selection:", lock_box)
        
        return widget

    def _update_btn_color(self, btn, color_hex):
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid gray;")

    def _on_bg_type_changed(self, text):
        self.model.props["bg_type"] = text
        self.update()

    def _on_show_outline_toggled(self, checked):
        self.model.props["show_outline"] = checked
        self.update()

    def _on_stroke_width_changed(self, val):
        self.model.props["stroke_width"] = val
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

    def get_bindable_properties(self):
        return ["fill_color", "stroke_color", "stroke_width", "show_outline"]

