from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPixmap, QPainter
from doclayout.core.models import BaseElement
from .base import BaseEditorItem

class ImageEditorItem(BaseEditorItem, QGraphicsRectItem):
    def __init__(self, model: BaseElement):
        QGraphicsRectItem.__init__(self, 0, 0, model.width, model.height)
        BaseEditorItem.__init__(self, model)
        
        self.setPos(model.x, model.y)
        self._pixmap = QPixmap()
        
        # Load Image if exists
        self.load_image(model.props.get("image_path", ""))
        
        # Resize Handle
        from ..handles import ResizeHandle
        self._handle = ResizeHandle(ResizeHandle.BOTTOM_RIGHT, self)
        self._handle.setVisible(False)
        
    def load_image(self, path):
        if not path:
             # Placeholder
             pix = QPixmap(100, 100)
             pix.fill(Qt.lightGray)
             painter = QPainter(pix)
             painter.drawText(pix.rect(), Qt.AlignCenter, "Image")
             painter.end()
             self._pixmap = pix
        else:
             self._pixmap = QPixmap(path)
             
        # Set default size if model is empty
        if self.model.width <= 0 or self.model.height <= 0:
            if not self._pixmap.isNull():
                self.model.width = self._pixmap.width() / 3.78 # px to mm
                self.model.height = self._pixmap.height() / 3.78
            else:
                self.model.width = 40
                self.model.height = 40
        
        self.setRect(0, 0, self.model.width, self.model.height)

    def setRect(self, x, y, w, h):
        """Update both item rect and model dimensions."""
        super().setRect(0, 0, w, h)
        if hasattr(self, 'model'):
            self.model.width = w
            self.model.height = h
        self.update_handles()
        self.update()

    def paint(self, painter, option, widget):
        if not self._pixmap.isNull():
            # Draw pixmap scaled to rect
            painter.drawPixmap(self.rect(), self._pixmap, QRectF(self._pixmap.rect()))
        
        self.paint_lock_icons(painter)
        
        # Draw selection board if selected
        if self.isSelected():
            painter.setPen(Qt.DashLine)
            painter.drawRect(self.rect())

    def create_properties_widget(self, parent):
        from PySide6.QtWidgets import QWidget, QFormLayout, QLineEdit, QHBoxLayout, QPushButton
        from PySide6.QtCore import Qt
        
        widget = QWidget(parent)
        layout = QFormLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Path
        path_layout = QHBoxLayout()
        self._prop_path = QLineEdit()
        self._prop_path.setText(self.model.props.get("image_path", ""))
        self._prop_path.setReadOnly(True)
        
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(30)
        btn_browse.clicked.connect(self._on_prop_browse_clicked)
        
        path_layout.addWidget(self._prop_path)
        path_layout.addWidget(btn_browse)
        layout.addRow("Image Path:", path_layout)
        
        return widget

    def _on_prop_browse_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(None, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self._prop_path.setText(path)
            self.model.props["image_path"] = path
            self.load_image(path)

    def get_bindable_properties(self):
        return ["image_path"]

