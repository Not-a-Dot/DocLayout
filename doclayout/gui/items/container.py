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
        self._update_visuals()
        
        from ..handles import ResizeHandle
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)
        
        # Track previous height for delta calculation
        self._last_height = model.height

    def _update_visuals(self):
        props = self.model.props
        bg_type = props.get("bg_type", "transparent")
        fill_color = props.get("fill_color", "#ffffff")
        outline_color = props.get("stroke_color", "#000000")
        alpha = props.get("opacity", 255)
        
        # Default pen for editor (dashed guide)
        pen = QPen(QColor(100, 100, 100))
        pen.setStyle(Qt.DashLine)
        pen.setWidthF(0.5)
        self.setPen(pen)
        
        # Brush
        if bg_type == "solid":
            color = QColor(fill_color)
            color.setAlpha(alpha)
            self.setBrush(QBrush(color))
        else:
            self.setBrush(Qt.NoBrush)
            
        self.update()

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

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setZValue(50) # Lower than handles but higher than background
            else:
                self.setZValue(10)
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
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
            pen.setStyle(Qt.SolidLine)
            pen.setCosmetic(False)
            painter.setPen(pen)
        else:
            # Guide mode
            pen = QPen(QColor(100, 100, 100))
            pen.setStyle(Qt.DashLine)
            pen.setWidthF(0.2)
            painter.setPen(pen)

        super().paint(painter, option, widget)
        self.paint_lock_icons(painter)

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
        
        # --- Visual Properties ---
        layout.addRow(QLabel("<b>Visuals</b>"), QLabel(""))
        
        # Background Type
        self._prop_bg_type = QComboBox()
        self._prop_bg_type.addItems(["transparent", "solid"])
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
        
        # Outline Toggle
        self._prop_show_outline = QCheckBox("Show Border")
        self._prop_show_outline.setChecked(self.model.props.get("show_outline", False))
        self._prop_show_outline.toggled.connect(self._on_show_outline_toggled)
        layout.addRow("", self._prop_show_outline)
        
        self._prop_stroke_w = QDoubleSpinBox()
        self._prop_stroke_w.setRange(0.1, 20.0)
        self._prop_stroke_w.setSingleStep(0.1)
        self._prop_stroke_w.setValue(self.model.props.get("stroke_width", 1.0))
        self._prop_stroke_w.valueChanged.connect(self._on_stroke_width_changed)
        layout.addRow("Border Width:", self._prop_stroke_w)
        
        return widget

    def _update_btn_color(self, btn, color_hex):
        btn.setStyleSheet(f"background-color: {color_hex}; border: 1px solid gray;")

    def _on_bg_type_changed(self, text):
        self.model.props["bg_type"] = text
        self._update_visuals()

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
            self._update_visuals()

    def get_bindable_properties(self):
        return ["fill_color", "stroke_color", "stroke_width", "show_outline"]

