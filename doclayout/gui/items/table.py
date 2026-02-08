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
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)

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
            # Convert pt to mm (scene units)
            # Use same logic as TextBox for consistency
            mm_size = font_size_pt * (25.4 / 72.0)
            
            font = QFont("Arial")
            font.setPixelSize(int(mm_size) if int(mm_size) > 0 else 1) # Ensure at least 1 unit if round down to 0
            # Ideally use setPixelSize(mm_size) if PySide handles float, but explicit int is safer against TypeErrors
            # If precision is poor, we might need a transform hack, but let's try this first as TextBox uses it.
            # Wait, checking textbox.py: "font.setPixelSize(mm_size)". mm_size is float.
            # PySide6 likely accepts float and rounds or handles it. I will pass int to be safe or float if tested.
            # Let's try passing the float as in textbox.py, assuming PySide handles it.
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
                        # Handle missing or invalid cell data
                        text = ""
                        
                    # Alignment and padding
                    padding = 1.0
                    painter.drawText(cell_rect.adjusted(padding, padding, -padding, -padding), 
                                     Qt.AlignLeft | Qt.AlignVCenter, text)
                                     
        painter.restore()
        self.paint_lock_icons(painter)

    def setRect(self, x, y, w, h):
        super().setRect(0, 0, w, h)
        if hasattr(self, 'model'):
            self.model.width = w
            self.model.height = h
        self.update_handles()

    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPlainTextEdit, QPushButton, QCheckBox, QSpinBox, QLabel, QComboBox
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        
        # Theme Selector
        theme_combo = QComboBox()
        theme_combo.addItems(["Simple", "Grid", "Striped", "Dark"])
        theme_combo.setCurrentText(self.model.props.get("theme", "Grid"))
        theme_combo.currentTextChanged.connect(lambda v: [self.model.props.update({"theme": v}), self.update()])
        layout.addRow("Theme:", theme_combo)
        
        # Show Header
        chk_header = QCheckBox("Show Header Row")
        chk_header.setChecked(self.model.props.get("show_header", True))
        chk_header.toggled.connect(lambda v: [self.model.props.update({"show_header": v}), self.update()])
        layout.addRow("", chk_header)

        # Font Size
        spin_f = QSpinBox()
        spin_f.setRange(4, 72)
        spin_f.setValue(self.model.props.get("font_size", 10))
        spin_f.valueChanged.connect(lambda v: [self.model.props.update({"font_size": v}), self.update()])
        layout.addRow("Font Size:", spin_f)
        
        # Colors (Overrides)
        header_bg = QLineEdit(self.model.props.get("header_bg_color", ""))
        header_bg.setPlaceholderText("Header BG Color")
        header_bg.textChanged.connect(lambda v: [self.model.props.update({"header_bg_color": v}), self.update()])
        layout.addRow("Header BG:", header_bg)
        
        # Data Editor (Simple CSV-like)
        layout.addRow(QLabel("<b>Table Data (Comma Separated):</b>"), QLabel(""))
        data_edit = QPlainTextEdit()
        data = self.model.props.get("data", [])
        text = "\n".join([", ".join([str(c) for c in row]) for row in data])
        data_edit.setPlainText(text)
        
        def on_data_changed():
            lines = data_edit.toPlainText().strip().split("\n")
            if not lines or (len(lines) == 1 and not lines[0]):
                self.model.props["data"] = []
            else:
                self.model.props["data"] = [l.split(",") for l in lines]
            self.update()
            
        data_edit.textChanged.connect(on_data_changed)
        layout.addRow(data_edit)
        
        return widget
 
    def get_bindable_properties(self):
        return ["data", "font_size", "theme", "header_bg_color", "stroke_color"]
