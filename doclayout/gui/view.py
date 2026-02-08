"""
Custom QGraphicsView for the visual editor.
Handles zooming, panning, and coordinate transforms.
"""

from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt, QEvent, Signal
from PySide6.QtGui import QPainter, QWheelEvent, QMouseEvent

class EditorView(QGraphicsView):
    """
    A QGraphicsView optimized for editing documents.
    """

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        # Scale handling
        self._zoom_level = 1.0
        # Start with some scaling to make mm visible (1mm = approx 3.78px on 96dpi screen)
        # Using 5.0 as base visual scale so 1mm is big enough to verify
        self.scale(3.78, 3.78) 


    viewportChanged = Signal()

    def zoom_in(self):
        self.scale(1.2, 1.2)
        self.viewportChanged.emit()

    def zoom_out(self):
        self.scale(1/1.2, 1/1.2)
        self.viewportChanged.emit()

    def wheelEvent(self, event: QWheelEvent):
        """
        Handle zoom with Ctrl+Wheel.
        """
        if event.modifiers() & Qt.ControlModifier:
            zoom_in = event.angleDelta().y() > 0
            factor = 1.1 if zoom_in else 0.9
            self.scale(factor, factor)
            event.accept()
            self.viewportChanged.emit()
        else:
            super().wheelEvent(event)
            self.viewportChanged.emit()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if getattr(self, '_is_panning', False):
            delta = event.pos() - self._last_pan_pos
            self._last_pan_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self.viewportChanged.emit()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton and getattr(self, '_is_panning', False):
            self._is_panning = False
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
