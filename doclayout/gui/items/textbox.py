"""
Text box editor item implementation - dynamic height text container.
"""

from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption, QPainterPath

from ..base import BaseEditorItem
from ..text.properties import TextPropertiesWidget

class TextBoxEditorItem(BaseEditorItem, QGraphicsTextItem):
    """
    A text box that grows dynamically based on content.
    Similar to TextEditorItem but with dynamic height growth.
    """
    def __init__(self, model) -> None:
        """Initialize with model data."""
        QGraphicsTextItem.__init__(self)
        BaseEditorItem.__init__(self, model)
        
        self.document().setDocumentMargin(0)
        self.setPos(model.x, model.y)
        
        # Default properties
        if "text" not in self.model.props:
            self.model.props["text"] = "Text Box (grows with content)"
        
        if "font_size" not in self.model.props:
            self.model.props["font_size"] = 12
        
        # Store base height from editor for dynamic growth calculation
        if "base_height" not in self.model.props:
            self.model.props["base_height"] = self.model.height
        
        self.setPlainText(model.props.get("text", ""))
        self.setDefaultTextColor(model.props.get("color", "black"))
        self.update_visual_font()
        self.update_alignment(model.props.get("text_align", "left"))
        
        # Set text width to enable wrapping
        self.setTextWidth(model.width)
        
        from ...handles import ResizeHandle
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)
        
    def update_visual_font(self) -> None:
        """Sync font styling from model."""
        from doclayout.core.geometry import PT_TO_MM
        font = self.font()
        target_pt = self.model.props.get("font_size", 12)
        mm_size = target_pt * (25.4 / 72.0)
        font.setPixelSize(mm_size)
        font.setFamily(self.model.props.get("font_family", "Arial"))
        font.setBold(self.model.props.get("font_bold", False))
        font.setItalic(self.model.props.get("font_italic", False))
        self.setFont(font)

    def update_alignment(self, align: str) -> None:
        """Update text alignment."""
        opt = self.document().defaultTextOption()
        alignment_map = {"left": Qt.AlignLeft, "center": Qt.AlignCenter, "right": Qt.AlignRight}
        opt.setAlignment(alignment_map.get(align, Qt.AlignLeft))
        self.document().setDefaultTextOption(opt)

    def shape(self) -> QPainterPath:
        """Force hit-testing on the entire bounding box."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def setRect(self, x, y, w, h) -> None:
        """Handle resizing."""
        self.setTextWidth(w)
        self.model.width = w
        self.model.height = h
        # Update base_height when manually resized
        self.model.props["base_height"] = h
        self.update_handles()

    def itemChange(self, change, value) -> any:
        """Raise selected item to top."""
        if change == QGraphicsItem.ItemSelectedChange:
            self.setZValue(100 if value else 0)
        return super().itemChange(change, value)

    def create_properties_widget(self, parent) -> TextPropertiesWidget:
        return TextPropertiesWidget(self, parent)

    def get_bindable_properties(self) -> list:
        return ["text", "font_family", "font_size", "color", "font_bold", "font_italic", "text_align"]
