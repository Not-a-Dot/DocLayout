"""
DocLayout API.
Simplifies using the library for generating PDFs from Templates with data binding.
"""

from typing import Dict, Any, Union, List
from doclayout.core.models import Template, BlockInstance, BaseElement, ElementType
from doclayout.core.io import load_template
from doclayout.engine.layout import LayoutEngine
from doclayout.engine.export import TemplateExporter
from doclayout.adapters.reportlab_adapter import ReportLabRenderer
from doclayout.core.geometry import mm_to_pt

def generate_pdf(template_path: str, data: Dict[str, Any], output_path: str) -> None:
    """
    Generate a PDF from a template file with data binding.
    
    Convenience function for one-shot PDF generation. For batch operations,
    use DocGenerator class to avoid reloading the template.
    
    Args:
        template_path (str): Path to the JSON template file created by the editor.
        data (Dict[str, Any]): Dictionary mapping variable names to their values.
            Keys should match variable names defined in the template.
        output_path (str): File path where the generated PDF will be saved.
    
    Raises:
        FileNotFoundError: If template file doesn't exist.
        ValidationError: If template JSON structure is invalid.
        IOError: If output path is not writable.
    
    Example:
        >>> data = {"client_name": "John Doe", "invoice_id": "INV-001"}
        >>> generate_pdf("invoice.json", data, "output.pdf")
    """
    gen = DocGenerator(template_path)
    gen.generate(data, output_path)

class DocGenerator:
    """
    Generator class to produce PDFs from templates with data binding.
    """

    def __init__(self, template_source: Union[str, Template], block_provider: Dict[str, Any] = None):
        """
        Args:
            template_source: Path to JSON file or Template object.
            block_provider: Optional dict mapping block IDs to block definitions.
        """
        if isinstance(template_source, str):
            self.template = load_template(template_source)
        else:
            self.template = template_source

        self.block_provider = block_provider or {}
        self.exporter = TemplateExporter(self.block_provider)

    def generate(self, data: Dict[str, Any], output_path: str):
        """
        Generate PDF with data binding.
        
        Args:
            data: Dictionary of data to bind. 
                  Matches 'variable_name' props or 'bindings' list in elements.
            output_path: Output PDF path.
        """
        import copy
        working_template = copy.deepcopy(self.template)
        
        # Apply bindings to the template elements before compilation
        for item in working_template.items:
             self._apply_bindings(item, data)
             
        # Use centralized exporter
        renderer = ReportLabRenderer()
        self.exporter.export(working_template, renderer, output_path)

    def _apply_bindings(self, item, data):
        """Recursively apply bindings to item and its children."""
        if isinstance(item, BlockInstance):
            # BlockInstances might receive data too
            item.data.update(data)
            return

        if not isinstance(item, BaseElement):
            return

        # 1. Official 'bindings' list
        for binding in item.bindings:
            if binding.variable_name in data:
                item.props[binding.target_property] = data[binding.variable_name]
        
        # 2. Legacy/Simple 'variable_name' support
        var_name = item.props.get("variable_name")
        if var_name and var_name in data:
            val = data[var_name]
            if item.type == ElementType.TEXT:
                item.props["text"] = str(val)
            elif item.type == ElementType.IMAGE:
                item.props["image_path"] = str(val)
            elif item.type == ElementType.TABLE:
                item.props["data"] = val
                
        # Recurse for children
        for child in item.children:
            self._apply_bindings(child, data)
