from PySide6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QFont
from .base import BaseEditorItem
from doclayout.core.models import BaseElement

class TableEditorItem(BaseEditorItem, QGraphicsRectItem):
    """
    A Table item that displays grid data.
    Works like a spreadsheet within the editor.
    """
    def __init__(self, model: BaseElement):
        QGraphicsRectItem.__init__(self, 0, 0, model.width, model.height)
        BaseEditorItem.__init__(self, model)
        self.setPos(model.x, model.y)
        
        # Default properties
        if "data" not in self.model.props:
            self.model.props["data"] = [
                ["Item", "Qty", "Price"],
                ["Part A", "1", "10.00"],
                ["Part B", "2", "20.00"]
            ]
        
        if "show_header" not in self.model.props:
            self.model.props["show_header"] = True
            
        if "font_size" not in self.model.props:
            self.model.props["font_size"] = 10
        
        # Store number of rows from editor for dynamic height calculation
        if "num_rows_editor" not in self.model.props:
            data = self.model.props.get("data", [])
            self.model.props["num_rows_editor"] = len(data) if data else 3
            
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
        painter.save()
        
        # Draw background and border
        pen = QPen(QColor(0, 0, 0))
        pen.setWidthF(0.2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRect(self.rect())
        
        data = self.model.props.get("data", [])
        if not data:
             painter.restore()
             return

        rows = len(data)
        cols = len(data[0]) if rows > 0 else 0
        
        if rows > 0 and cols > 0:
            row_h = self.rect().height() / rows
            col_w = self.rect().width() / cols
            
            font_size_pt = float(self.model.props.get("font_size", 10))
            mm_size = font_size_pt * (25.4 / 72.0)
            
            font = QFont("Arial")
            font.setPixelSize(mm_size)
            painter.setFont(font)
            
            for r in range(rows):
                # Header background
                if r == 0 and self.model.props.get("show_header", True):
                    painter.fillRect(QRectF(0, 0, self.rect().width(), row_h), QColor(240, 240, 240))
                
                for c in range(cols):
                    cell_rect = QRectF(c * col_w, r * row_h, col_w, row_h)
                    painter.setPen(QPen(QColor(200, 200, 200), 0.1))
                    painter.drawRect(cell_rect)
                    
                    # Text
                    pen.setColor(QColor(0, 0, 0))
                    painter.setPen(pen)
                    try:
                        text = str(data[r][c])
                    except (IndexError, KeyError, TypeError):
                        text = ""
                        
                    # Alignment and padding
                    padding = 1.0
                    painter.drawText(cell_rect.adjusted(padding, padding, -padding, -padding), 
                                     Qt.AlignLeft | Qt.AlignVCenter, text)
                                     
        painter.restore()
        self.paint_lock_icons(painter)

    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QTextEdit, QLabel
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addRow(QLabel("<b>Table Data (CSV):</b>"))
        data_edit = QTextEdit()
        
        # Convert data list to CSV string
        data = self.model.props.get("data", [])
        csv_text = "\n".join([",".join([str(cell) for cell in row]) for row in data])
        data_edit.setPlainText(csv_text)
        data_edit.setMinimumHeight(100)
        
        def on_data_changed():
            lines = data_edit.toPlainText().strip().split("\n")
            if not lines or (len(lines) == 1 and not lines[0]):
                new_data = []
            else:
                new_data = [l.split(",") for l in lines]
            
            self.model.props["data"] = new_data
            
            # Recalculate height based on new row count if auto-height desired
            # For now, keep current rect but trigger repaint
            self.update()
            
        data_edit.textChanged.connect(on_data_changed)
        layout.addRow(data_edit)
        
        return widget
  
    def get_bindable_properties(self):
        return ["data", "font_size", "theme", "header_bg_color", "stroke_color"]

    def setRect(self, x, y, w, h):
        # Update model dimensions
        if hasattr(self, 'model'):
            self.model.width = w
            self.model.height = h
            
            # Update row_height prop if it exists
            data = self.model.props.get("data", [])
            rows = len(data) if data else 1
            if rows < 1: rows = 1
            self.model.props["row_height"] = h / rows
            
        super().setRect(0, 0, w, h)
        self.update_handles()
