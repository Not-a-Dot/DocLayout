"""
Text box editor item implementation - dynamic height text container.
"""

from PySide6.QtWidgets import QGraphicsTextItem, QGraphicsItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption, QPainterPath

from .base import BaseEditorItem
from .text.properties import TextPropertiesWidget

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
        
        # Monitor content changes to update model height
        self.document().contentsChange.connect(self.on_contents_change)
        
    def on_contents_change(self, position, charsRemoved, charsAdded):
        """Update model height when text changes."""
        # We need to let the layout update first
        # Use a zero-timer or just check boundingRect?
        # Bounding rect might not be updated immediately in this signal.
        # But let's try calling adjustSize equivalent or relying on scene update loop?
        # QGraphicsTextItem updates layout lazily usually.
        # Let's verify in paint? No, messy.
        # Check logic:
        # We can force an update of the geometry logic.
        self.prepareGeometryChange()
        h = self.boundingRect().height()
        if hasattr(self, 'model'):
             self.model.height = h
             self.model.props["base_height"] = h
             self.update_handles()
             
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


    def paint(self, painter, option, widget=None):
        """Custom paint to draw background and border."""
        # 1. Draw Background & Border matches ReportLabRenderer logic
        props = self.model.props
        show_outline = props.get("show_outline", False)
        bg_color = props.get("fill_color", "")
        
        # Determine if we need to draw anything custom
        if show_outline or bg_color:
            painter.save()
            rect = self.boundingRect()
            
            # Setup Pen (Border)
            if show_outline:
                from PySide6.QtGui import QPen, QColor
                stroke_color = props.get("stroke_color", "black")
                stroke_width = float(props.get("stroke_width", 1.0))
                pen = QPen(QColor(stroke_color))
                pen.setWidthF(stroke_width)
                painter.setPen(pen)
            else:
                painter.setPen(Qt.NoPen)
                
            # Setup Brush (Background)
            if bg_color:
                from PySide6.QtGui import QBrush, QColor
                painter.setBrush(QBrush(QColor(bg_color)))
            else:
                painter.setBrush(Qt.NoBrush)
                
            painter.drawRect(rect)
            painter.restore()
            
            # Update Document Margin for Text
            # 1.0mm padding if styled
            if abs(self.document().documentMargin() - 1.0) > 0.01:
                self.document().setDocumentMargin(1.0)
        else:
            if abs(self.document().documentMargin() - 0.0) > 0.01:
                self.document().setDocumentMargin(0.0)
            
        # 2. Draw Text (super implementation)
        super().paint(painter, option, widget)

    def create_properties_widget(self, parent) -> TextPropertiesWidget:
        # Connect update to trigger repaint
        w = TextPropertiesWidget(self, parent)
        # We hook into the widget updates indirectly via scene.update() which calls paint()
        return w

    def get_bindable_properties(self) -> list:
        return ["text", "font_family", "font_size", "color", "font_bold", "font_italic", "text_align"]
