"""
Property editor panel for managing element properties and bindings.
"""

import os
import logging
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QFormLayout, QLineEdit, QDoubleSpinBox, 
                               QSpinBox, QCheckBox, QVBoxLayout, QLabel, 
                               QHBoxLayout, QPushButton, QComboBox, QInputDialog, 
                               QMessageBox, QScrollArea)
from PySide6.QtCore import Qt, Signal

from doclayout.core.models import VariableBinding, BaseElement, ElementType
from doclayout.core.variables import VariableManager
from doclayout.core.io import save_to_json
from .collapsible import CollapsibleSection

logger = logging.getLogger(__name__)

class BindingRow(QWidget):
    """
    A row in the data binding list.
    
    Signals:
        changed: Emitted when binding values change.
        deleted: Emitted when the delete button is clicked.
    """
    changed = Signal()
    deleted = Signal(object)

    def __init__(self, variable_names: List[str], target_properties: List[str], 
                 initial_var: str = "", initial_prop: str = "") -> None:
        """
        Initialize the binding row.

        Args:
            variable_names (List[str]): List of available global variables.
            target_properties (List[str]): List of bindable properties for the item.
            initial_var (str): Initial variable name.
            initial_prop (str): Initial target property.
        """
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 2)
        
        self.var_combo = QComboBox()
        self.var_combo.addItems(variable_names)
        self.var_combo.setEditable(True)
        self.var_combo.setCurrentText(initial_var)
        self.var_combo.currentTextChanged.connect(lambda: self.changed.emit())
        
        self.prop_combo = QComboBox()
        self.prop_combo.addItems(target_properties)
        self.prop_combo.setCurrentText(initial_prop)
        self.prop_combo.currentIndexChanged.connect(lambda: self.changed.emit())
        
        self.btn_del = QPushButton("×")
        self.btn_del.setFixedWidth(24)
        self.btn_del.clicked.connect(lambda: self.deleted.emit(self))
        
        layout.addWidget(self.var_combo, 2)
        layout.addWidget(QLabel("→"), 0)
        layout.addWidget(self.prop_combo, 2)
        layout.addWidget(self.btn_del, 0)

    def get_binding(self) -> VariableBinding:
        """
        Get the binding model from current UI state.

        Returns:
            VariableBinding: The binding configuration.
        """
        return VariableBinding(
            variable_name=self.var_combo.currentText(),
            target_property=self.prop_combo.currentText()
        )

class PropertyEditor(QWidget):
    """
    Panel for editing properties of the currently selected scene items.
    """
    def __init__(self, scene) -> None:
        """
        Initialize the property editor.

        Args:
            scene (EditorScene): The graphics scene to monitor.
        """
        super().__init__()
        self.scene = scene
        self.scene.selectionChanged.connect(self.on_selection_changed)
        if hasattr(self.scene, "itemMoved"):
            self.scene.itemMoved.connect(self.on_item_moved)
        self._selected_items = []
        self._item = None
        self._updating = False
        self._custom_widget = None
        self._setup_ui()
    
    def on_item_moved(self, item) -> None:
        """
        Update UI when item is moved in scene.

        Args:
            item (BaseEditorItem): The item that moved.
        """
        try:
            if item not in self._selected_items or self._updating:
                 return
        except RuntimeError:
            return
             
        self._updating = True
        try:
            if item == self._item:
                self.x_edit.setValue(item.model.x)
                self.y_edit.setValue(item.model.y)
                self.w_edit.setValue(item.model.width)
                self.h_edit.setValue(item.model.height)
        finally:
            self._updating = False

    def _setup_ui(self) -> None:
        """Setup the basic UI layout for properties."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)
        self.scroll.setWidget(self.container)
        
        self.main_layout.addWidget(self.scroll)
        
        # 1. Item Properties Section (Top Priority)
        self.props_section = CollapsibleSection("Item Properties")
        self.custom_props_area = QWidget()
        self.custom_props_layout = QVBoxLayout(self.custom_props_area)
        self.custom_props_layout.setContentsMargins(0, 0, 0, 0)
        self.props_section.addWidget(self.custom_props_area)
        self.container_layout.addWidget(self.props_section)

        # 2. Appearance Section (New)
        self.appearance_section = CollapsibleSection("Appearance")
        loss_layout = QFormLayout()
        
        # Border
        self.chk_border = QCheckBox("Show Border")
        self.chk_border.toggled.connect(lambda v: self._update_model_prop("show_outline", v))
        loss_layout.addRow("", self.chk_border)
        
        self.border_width = QDoubleSpinBox()
        self.border_width.setRange(0.1, 50.0)
        self.border_width.setSuffix(" pt")
        self.border_width.setValue(1.0)
        self.border_width.valueChanged.connect(lambda v: self._update_model_prop("stroke_width", v))
        loss_layout.addRow("Border Width:", self.border_width)
        
        # Colors
        self.border_color = QLineEdit()
        self.border_color.setPlaceholderText("#000000")
        self.border_color.textChanged.connect(lambda v: self._update_model_prop("stroke_color", v))
        loss_layout.addRow("Border Color:", self.border_color)
        
        self.bg_color = QLineEdit()
        self.bg_color.setPlaceholderText("transparent or #FFFFFF")
        self.bg_color.textChanged.connect(lambda v: self._update_model_prop("fill_color", v))
        loss_layout.addRow("Background:", self.bg_color)
        
        self.appearance_section.setContentLayout(loss_layout)
        self.container_layout.addWidget(self.appearance_section)

        # 3. Geometry Section
        self.geo_section = CollapsibleSection("Geometry")
        geo_form = QFormLayout()
        
        self.x_edit = QDoubleSpinBox()
        self.x_edit.setRange(-10000, 10000)
        self.x_edit.setSuffix(" mm")
        self.x_edit.setDecimals(2)
        self.x_edit.valueChanged.connect(self._update_item_geo)
        geo_form.addRow("X:", self.x_edit)
        
        self.y_edit = QDoubleSpinBox()
        self.y_edit.setRange(-10000, 10000)
        self.y_edit.setSuffix(" mm")
        self.y_edit.setDecimals(2)
        self.y_edit.valueChanged.connect(self._update_item_geo)
        geo_form.addRow("Y:", self.y_edit)
        
        self.w_edit = QDoubleSpinBox()
        self.w_edit.setRange(0, 10000)
        self.w_edit.setSuffix(" mm")
        self.w_edit.setDecimals(2)
        self.w_edit.valueChanged.connect(self._update_item_geo)
        geo_form.addRow("Width:", self.w_edit)
        
        self.h_edit = QDoubleSpinBox()
        self.h_edit.setRange(0, 10000)
        self.h_edit.setSuffix(" mm")
        self.h_edit.setDecimals(2)
        self.h_edit.valueChanged.connect(self._update_item_geo)
        geo_form.addRow("Height:", self.h_edit)
        
        self.geo_section.setContentLayout(geo_form)
        self.container_layout.addWidget(self.geo_section)

        # 4. Data Bindings Section
        self.binding_section = CollapsibleSection("Data Bindings")
        binding_container_layout = QVBoxLayout()
        
        self.bindings_container = QWidget()
        self.bindings_layout = QVBoxLayout(self.bindings_container)
        self.bindings_layout.setContentsMargins(0, 0, 0, 0)
        binding_container_layout.addWidget(self.bindings_container)
        
        self.btn_add_binding = QPushButton("+ Add Binding")
        self.btn_add_binding.clicked.connect(lambda: self._add_binding_row())
        binding_container_layout.addWidget(self.btn_add_binding)
        
        self.binding_section.setContentLayout(binding_container_layout)
        self.container_layout.addWidget(self.binding_section)

        # 5. Locking & Grouping Section
        self.lock_section = CollapsibleSection("Locking & Grouping")
        lock_layout = QVBoxLayout()
        
        self.chk_lock_pos = QCheckBox("Lock Position")
        self.chk_lock_pos.toggled.connect(lambda v: self._update_model_prop("lock_position", v))
        lock_layout.addWidget(self.chk_lock_pos)
        
        self.chk_lock_geo = QCheckBox("Lock Geometry")
        self.chk_lock_geo.toggled.connect(self._on_lock_geo_toggled)
        lock_layout.addWidget(self.chk_lock_geo)
        
        self.chk_lock_sel = QCheckBox("Lock Selection (Structure Only)")
        self.chk_lock_sel.toggled.connect(self._on_lock_sel_toggled)
        lock_layout.addWidget(self.chk_lock_sel)
        
        self.chk_lock_children = QCheckBox("Lock Children")
        self.chk_lock_children.toggled.connect(lambda v: self._update_model_prop("lock_children", v))
        lock_layout.addWidget(self.chk_lock_children)
        
        self.btn_save_block = QPushButton("Save as Block...")
        self.btn_save_block.clicked.connect(self._on_save_block_clicked)
        lock_layout.addWidget(self.btn_save_block)
        
        self.lock_section.setContentLayout(lock_layout)
        self.container_layout.addWidget(self.lock_section)
        
        # 6. Project Properties Section (shown when nothing selected)
        self.project_section = CollapsibleSection("Propriedades do Projeto")
        from ..project_properties import ProjectPropertiesWidget
        self.project_props_widget = ProjectPropertiesWidget(self.scene.template)
        self.project_section.addWidget(self.project_props_widget)
        self.container_layout.addWidget(self.project_section)
        self.project_section.setVisible(False)  # Hidden by default
        
        self.container_layout.addStretch()

    def _update_model_prop(self, key: str, val: any) -> None:
        """Update a property for all selected items."""
        if not self._selected_items or self._updating:
            return
            
        for item in self._selected_items:
            item.model.props[key] = val
            if key == "lock_geometry":
                item.update_handles()
            elif key in ("lock_selection", "lock_position"):
                item.update_locking()
            item.update()

    def _on_lock_geo_toggled(self, locked: bool) -> None:
        self._update_model_prop("lock_geometry", locked)

    def _on_lock_sel_toggled(self, locked: bool) -> None:
        if not self._item or self._updating:
            return
        self._item.model.props["lock_selection"] = locked
        if hasattr(self._item, "update_locking"):
            self._item.update_locking()

    def _on_save_block_clicked(self) -> None:
        """Handle saving the primary item as a reusable block."""
        if not self._item:
            return
            
        name, ok = QInputDialog.getText(self, "Save Block", "Block Name:")
        if ok and name:
            try:
                blocks_dir = "doclayout_blocks"
                os.makedirs(blocks_dir, exist_ok=True)
                path = os.path.join(blocks_dir, f"{name}.json")
                save_to_json(self._item.model, path)
                QMessageBox.information(self, "Success", f"Block saved to {path}")
            except Exception as e:
                logger.error("Failed to save block: %s", e)
                QMessageBox.critical(self, "Error", str(e))

    def _add_binding_row(self, initial_var: str = "", initial_prop: str = "") -> None:
        """Add a new binding row to the UI."""
        if not self._item: return
        
        if not isinstance(initial_var, str): initial_var = ""
        if not isinstance(initial_prop, str): initial_prop = ""
        
        global_vars = VariableManager().get_variables()
        target_props = self._item.get_bindable_properties()
        
        row = BindingRow(global_vars, target_props, initial_var, initial_prop)
        row.changed.connect(self._on_bindings_updated)
        row.deleted.connect(self._on_binding_deleted)
        self.bindings_layout.addWidget(row)
        
        if not self._updating:
            self._on_bindings_updated()

    def _on_binding_deleted(self, row: BindingRow) -> None:
        self.bindings_layout.removeWidget(row)
        row.deleteLater()
        self._on_bindings_updated()

    def _on_bindings_updated(self) -> None:
        """Sync UI binding rows to the model."""
        if not self._item or self._updating: return
        
        new_bindings = []
        for i in range(self.bindings_layout.count()):
            widget = self.bindings_layout.itemAt(i).widget()
            if isinstance(widget, BindingRow):
                new_bindings.append(widget.get_binding())
        
        self._item.model.bindings = new_bindings

    def _refresh_bindings(self) -> None:
        """Rebuild binding rows from the model."""
        while self.bindings_layout.count():
            item = self.bindings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self._item: return
        
        for b in self._item.model.bindings:
            self._add_binding_row(b.variable_name, b.target_property)

    def _item_depth(self, item) -> int:
        """Calculate nesting depth of an item."""
        depth = 0
        p = item.parentItem()
        while p:
            depth += 1
            p = p.parentItem()
        return depth

    def on_selection_changed(self) -> None:
        """Update UI based on current scene selection."""
        try:
            items = self.scene.selectedItems()
        except RuntimeError:
            return
            
        if not items:
            self._selected_items = []
            self._item = None
            self._clear_custom_widget()
            # Show project properties when nothing selected
            self.geo_section.setVisible(False)
            self.lock_section.setVisible(False)
            self.binding_section.setVisible(False)
            self.props_section.setVisible(False)
            self.appearance_section.setVisible(False)
            self.project_section.setVisible(True)
            self.setEnabled(True)
            return

        self._updating = True
        self.blockSignals(True)
        
        try:
            # Sort items so that children appear BEFORE parents
            items = sorted(items, key=lambda x: self._item_depth(x), reverse=True)
            self._selected_items = items
            self._item = items[0]
            self.setEnabled(True)
            
            # Hide project properties, show element properties
            self.project_section.setVisible(False)
            self.geo_section.setVisible(True)
            self.lock_section.setVisible(True)
            self.appearance_section.setVisible(True)
            
            self._clear_custom_widget()
            
            model = self._item.model
            
            # Geometry
            self.x_edit.setValue(model.x)
            self.y_edit.setValue(model.y)
            self.w_edit.setValue(model.width)
            self.h_edit.setValue(model.height)
            
            # Appearance
            self.chk_border.setChecked(model.props.get("show_outline", False))
            self.border_width.setValue(float(model.props.get("stroke_width", 1.0)))
            self.border_color.setText(str(model.props.get("stroke_color", "black")))
            self.bg_color.setText(str(model.props.get("fill_color", "")))
            
            # Locking
            self.chk_lock_pos.setChecked(all(it.model.lock_position for it in items))
            self.chk_lock_geo.setChecked(all(it.model.lock_geometry for it in items))
            self.chk_lock_sel.setChecked(all(it.model.lock_selection for it in items))
            
            any_has_modeled_children = any(any(hasattr(c, 'model') for c in it.childItems()) for it in items)
            self.chk_lock_children.setVisible(any_has_modeled_children)
            self.chk_lock_children.setChecked(all(it.model.lock_children for it in items))
            
            if len(items) == 1:
                self.binding_section.setVisible(True)
                self._refresh_bindings()
                if hasattr(self._item, "create_properties_widget"):
                    self._custom_widget = self._item.create_properties_widget(self.custom_props_area)
                    if self._custom_widget:
                        self.custom_props_layout.addWidget(self._custom_widget)
                self.props_section.setVisible(True)
            else:
                self.binding_section.setVisible(False)
                self.props_section.setVisible(False)

        finally:
            self.blockSignals(False)
            self._updating = False

    def _clear_custom_widget(self) -> None:
        if self._custom_widget:
            self.custom_props_layout.removeWidget(self._custom_widget)
            self._custom_widget.deleteLater()
            self._custom_widget = None

    def _update_item_geo(self) -> None:
        """Sync UI geometry fields to scene items."""
        if not self._selected_items or self._updating:
             return
             
        self._updating = True
        try:
            x = self.x_edit.value()
            y = self.y_edit.value()
            w = self.w_edit.value()
            h = self.h_edit.value()
            
            for item in self._selected_items:
                item.setPos(x, y) 
                item.model.x = item.pos().x()
                item.model.y = item.pos().y()
                item.model.width = w
                item.model.height = h
                
                if hasattr(item, "setRect"):
                    item.setRect(0, 0, w, h)
                elif hasattr(item, "setTextWidth") and item.model.type == ElementType.TEXT:
                    item.setTextWidth(w)
                    
                if hasattr(item, "update_handles"):
                    item.update_handles()
                item.update()
                
            final_pos = self._item.pos()
            if final_pos.x() != x: self.x_edit.setValue(final_pos.x())
            if final_pos.y() != y: self.y_edit.setValue(final_pos.y())
                
        finally:
            self._updating = False
