"""
Project properties widget for editing project-wide settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QDoubleSpinBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt

class ProjectPropertiesWidget(QWidget):
    """
    Widget for editing project-wide settings.
    
    Displays and allows editing of:
    - Page top margin for split elements
    - Future: other project settings
    """
    
    def __init__(self, template, parent=None):
        """
        Initialize the project properties widget.
        
        Args:
            template: The Template model containing project settings
            parent: Parent widget
        """
        super().__init__(parent)
        self.template = template
        self._setup_ui()
        self._load_values()
    
    def _setup_ui(self):
        """Create the UI layout and widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title = QLabel("Propriedades do Projeto")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        # Page Settings Group
        page_group = QGroupBox("Configurações de Página")
        page_layout = QFormLayout()
        
        # Top Margin
        self.top_margin_spin = QDoubleSpinBox()
        self.top_margin_spin.setRange(0.0, 100.0)
        self.top_margin_spin.setSingleStep(1.0)
        self.top_margin_spin.setSuffix(" mm")
        self.top_margin_spin.setToolTip(
            "Margem superior para elementos divididos em novas páginas"
        )
        self.top_margin_spin.valueChanged.connect(self._on_top_margin_changed)
        page_layout.addRow("Margem Superior:", self.top_margin_spin)
        
        page_group.setLayout(page_layout)
        layout.addWidget(page_group)
        
        # Spacer
        layout.addStretch()
    
    def _load_values(self):
        """Load current values from template settings."""
        self.top_margin_spin.setValue(self.template.settings.page_top_margin_mm)
    
    def _on_top_margin_changed(self, value: float):
        """Handle top margin value change."""
        self.template.settings.page_top_margin_mm = value
