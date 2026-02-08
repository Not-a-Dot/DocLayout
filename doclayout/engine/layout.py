"""
Layout Engine.
Responsible for compiling a Template into a list of absolute renderable elements.
"""

import copy
import re
from typing import List, Dict, Any, Union
from doclayout.core.models import Template, BlockBase, BlockInstance, BaseElement, ElementType

class LayoutEngine:
    """
    The Layout Engine processes a Template and produces a list of resolved elements.
    """

    def __init__(self, block_provider: Dict[str, BlockBase]):
        """
        Args:
            block_provider: A dictionary mapping block_id to BlockBase objects.
        """
        self.block_provider = block_provider

    def compile(self, template: Template) -> List[BaseElement]:
        """
        Flatten the template into a list of absolute elements.
        
        Args:
            template: The Template to process.

        Returns:
            List[BaseElement]: A flat list of elements ready for rendering.
        """
        output_elements: List[BaseElement] = []

        for item in template.items:
            if isinstance(item, BlockInstance):
                resolved = self._resolve_block(item)
                output_elements.extend(resolved)
            elif isinstance(item, BaseElement):
                # Flatten the hierarchy starting from this root element
                # Root elements are relative to the page (0,0)
                output_elements.extend(self._flatten_tree(item, 0, 0))
            else:
                # Should not happen if types are correct
                pass
        
        if hasattr(template, "variables"):
             self.apply_bindings(output_elements, template.variables)
             
        return output_elements

    def apply_bindings(self, elements: List[BaseElement], variables: Dict[str, Any]):
        """Apply property bindings from global variables."""
        for elem in elements:
            for binding in elem.bindings:
                if binding.variable_name in variables:
                    elem.props[binding.target_property] = variables[binding.variable_name]

    def _resolve_block(self, instance: BlockInstance) -> List[BaseElement]:
        """
        Resolve a block instance into a list of elements.
        """
        block_def = self.block_provider.get(instance.block_id)
        if not block_def:
            # Log warning or error? For now, skip.
            return []

        resolved_elements = []
        for elem in block_def.elements:
            # Flatten each potentially hierarchical element in the block
            # Offsets are instance positions
            flattened = self._flatten_tree(elem, instance.x, instance.y)
            
            for flat in flattened:
                # Apply variable substitution to ALL resulting elements
                if flat.type == ElementType.TEXT:
                    self._substitute_text(flat, instance.data)
                resolved_elements.append(flat)
            
        return resolved_elements

    def _flatten_tree(self, element: BaseElement, offset_x: float, offset_y: float) -> List[BaseElement]:
        """
        Recursively flatten an element and its children into a list of absolute elements.
        """
        # Calculate absolute position for this element
        # element.x/y are relative to parent
        abs_x = offset_x + element.x
        abs_y = offset_y + element.y
        
        # Create a deep copy to ensure we don't mutate the original template or block definition
        # We strip children from the copy to create a "flat" element for rendering
        flat_elem = copy.deepcopy(element)
        flat_elem.x = abs_x
        flat_elem.y = abs_y
        flat_elem.children = [] # Remove hierarchy from the flat list item
        
        result = [flat_elem]
        
        # Process children
        # Child coordinates are relative to the parent's new absolute position (top-left)
        for child in element.children:
            result.extend(self._flatten_tree(child, abs_x, abs_y))
            
        return result

    def _substitute_text(self, element: BaseElement, data: Dict[str, Any]) -> None:
        """
        Replace {{variable}} placeholders in text elements.
        """
        # We assume props['text'] holds the content for TEXT elements.
        # This dependency on 'props' structure should be documented or strict in models.
        text_content = element.props.get("text", "")
        if not text_content:
            return

        # Simple regex for {{ key }}
        # Handles {{key}} and {{ key }}
        pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        
        def replacer(match):
            key = match.group(1)
            return str(data.get(key, f"{{{{{key}}}}}")) # Keep original if not found

        new_text = pattern.sub(replacer, text_content)
        element.props["text"] = new_text
