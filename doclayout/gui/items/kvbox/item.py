"""
KV Box editor item implementation.
"""

from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

from ..base import BaseEditorItem
from .properties import KVBoxPropertiesWidget

class KVBoxEditorItem(BaseEditorItem, QGraphicsRectItem):
    """
    A graphics item that displays a label-value pair in a box.
    """
    def __init__(self, model) -> None:
        """Initialize with model data."""
        QGraphicsRectItem.__init__(self, 0, 0, model.width, model.height)
        BaseEditorItem.__init__(self, model)
        
        self.setPos(model.x, model.y)
        self.key_label = QGraphicsTextItem(self)
        self.val_label = QGraphicsTextItem(self)
        self.key_label.document().setDocumentMargin(0)
        self.val_label.document().setDocumentMargin(0)
        
        self.update_visuals()
        
        from ...handles import ResizeHandle
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)

    def update_visuals(self) -> None:
        """Sync visual state from model properties."""
        from doclayout.core.geometry import PT_TO_MM
        props = self.model.props
        
        self.key_label.setPlainText(str(props.get("key_text", "Label:")))
        self.val_label.setPlainText(str(props.get("text", "[Value]")))
        
        font = self.key_label.font()
        target_pt = props.get("font_size", 10)
        font.setPixelSize(target_pt * PT_TO_MM)
        font.setFamily(props.get("font_family", "Arial"))
        font.setBold(props.get("font_bold", False))
        font.setItalic(props.get("font_italic", False))
        
        self.key_label.setFont(font)
        self.val_label.setFont(font)
        
        color = props.get("color", "black")
        self.key_label.setDefaultTextColor(QColor(color))
        self.val_label.setDefaultTextColor(QColor(color))
        
        w, h = self.model.width, self.model.height
        stype = props.get("split_type", "ratio")
        
        if stype == "auto":
            self.key_label.setTextWidth(-1)
            split = self.key_label.boundingRect().width() + 1.0
        elif stype == "fixed":
            split = props.get("split_fixed", 20.0)
        else:
            split = w * props.get("split_ratio", 0.4)
            
        split = max(1.0, min(w - 1.0, split))
        self.key_label.setTextWidth(split - 0.5)
        self.val_label.setTextWidth(max(1.0, w - split - 0.5))
        
        self.key_label.setPos(0.5, (h - self.key_label.boundingRect().height()) / 2)
        self.val_label.setPos(split + 0.5, (h - self.val_label.boundingRect().height()) / 2)
        self.update()

    def setRect(self, x, y, w, h) -> None:
        """Handle resizing from handles."""
        super().setRect(0, 0, w, h)
        self.model.width, self.model.height = w, h
        self.update_visuals()
        self.update_handles()

    def paint(self, painter, option, widget) -> None:
        """Custom paint logic for borders and dividers."""
        props = self.model.props
        show_outline = props.get("show_outline", True)
        outline_w = props.get("stroke_width", 0.5)
        
        if show_outline:
            painter.setPen(QPen(QColor(props.get("border_color", "black")), outline_w))
        else:
            pen = QPen(QColor(200, 200, 200), 0.2, Qt.DashLine)
            painter.setPen(pen)

        painter.drawRect(self.rect())
        
        if show_outline:
            w, stype = self.model.width, props.get("split_type", "ratio")
            if stype == "fixed":
                 split = props.get("split_fixed", 20.0)
            elif stype == "auto":
                 split = self.key_label.boundingRect().width() + 2.0
            else:
                 split = w * props.get("split_ratio", 0.4)
            
            painter.setPen(QPen(QColor(props.get("divider_color", "black")), outline_w))
            painter.drawLine(split, 0, split, self.model.height)
        
        self.paint_lock_icons(painter)

    def create_properties_widget(self, parent) -> KVBoxPropertiesWidget:
        """Create the UI panel for editing this item."""
        return KVBoxPropertiesWidget(self, parent)

    def get_bindable_properties(self) -> list:
        """Properties that can be linked to data variables."""
        return ["key_text", "text", "font_family", "font_size", "color", 
                "font_bold", "font_italic", "border_color", "divider_color"]
