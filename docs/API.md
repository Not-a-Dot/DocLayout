# DocLayout API Documentation

The `DocLayout` library provides tools for generating PDFs from JSON-based templates with support for data binding.

## Core Module

### `doclayout.api`

This module exposes the primary interface for generating documents.

#### Functions

**`generate_pdf(template_path: str, data: Dict[str, Any], output_path: str)`**

A convenience function to generate a PDF from a template file and a data dictionary.

- **Parameters:**
    - `template_path` (str): Path to the `.json` template file created by the editor.
    - `data` (dict): A dictionary mapping variable names (used in the template) to their values.
    - `output_path` (str): The file path where the resulting PDF will be saved.

**Example:**
```python
from doclayout.api import generate_pdf

data = {
    "client_name": "John Doe",
    "invoice_id": "INV-2023-001"
}

generate_pdf("invoice_template.json", data, "invoice.pdf")
```

#### Classes

**`DocGenerator(template_source: Union[str, Template])`**

A class for managing document generation, useful when reusing a loaded template or generating multiple documents.

- **Constructor**: `__init__(self, template_source)`
    - `template_source`: Can be a file path (str) or a `Template` object loaded via `doclayout.core.io`.

- **Methods**:
    - `generate(data: Dict[str, Any], output_path: str)`: Generates a PDF.
        - `data`: Dictionary of data to bind to the template.
        - `output_path`: Destination path for the PDF file.

**Example:**
```python
from doclayout.api import DocGenerator

generator = DocGenerator("report_template.json")

# Generate multiple reports
users = [{"name": "Alice"}, {"name": "Bob"}]
for user in users:
    generator.generate(user, f"report_{user['name']}.pdf")
```

## Data Binding

Templates support binding data to element properties.

- **Variables**: Use variable names in the "Data Binding" section of the editor (e.g., `client_name`).
- **Text Substitution**: If an element has a variable name assigned (e.g., `client_name`), the value from the `data` dictionary will replace the element's text content.
- **Image Paths**: If an Image element has a variable, the value from `data` will be treated as the file path for the image.
