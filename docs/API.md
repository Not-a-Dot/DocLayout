# DocLayout API Documentation

## Overview

The DocLayout API provides a simple, programmatic interface for generating PDF documents from JSON templates with dynamic data binding. This allows you to design templates visually using the DocLayout Editor and then populate them with data at runtime.

---

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from doclayout.api import generate_pdf

# Define your data
data = {
    "client_name": "John Doe",
    "invoice_id": "INV-2024-001",
    "amount": "$1,250.00"
}

# Generate PDF
generate_pdf("invoice_template.json", data, "output.pdf")
```

---

## Core API

### `generate_pdf()`

**Signature:**
```python
def generate_pdf(
    template_path: str,
    data: Dict[str, Any],
    output_path: str
) -> None
```

Convenience function for one-shot PDF generation from a template file.

**Parameters:**

- **`template_path`** (str): Path to the JSON template file created by the DocLayout Editor.

- **`data`** (dict): Dictionary mapping variable names to their values. Keys should match the variable names defined in the template.

- **`output_path`** (str): File path where the generated PDF will be saved.

**Raises:**
- `FileNotFoundError`: If template file doesn't exist
- `ValidationError`: If template JSON is invalid
- `IOError`: If output path is not writable

**Example:**
```python
from doclayout.api import generate_pdf

data = {
    "title": "Monthly Report",
    "date": "2024-02-08",
    "total_sales": "15,234.50"
}

generate_pdf("report.json", data, "monthly_report.pdf")
```

---

## Advanced API

### `DocGenerator` Class

For scenarios where you need to generate multiple PDFs from the same template, use `DocGenerator` to avoid reloading the template each time.

**Signature:**
```python
class DocGenerator:
    def __init__(
        self,
        template_source: Union[str, Template],
        block_provider: Dict[str, Any] = None
    )
```

**Constructor Parameters:**

- **`template_source`** (str | Template): Either:
  - Path to a JSON template file (str), or
  - A pre-loaded `Template` object from `doclayout.core.io.load_template()`

- **`block_provider`** (dict, optional): Dictionary mapping block IDs to `BlockBase` objects for templates that use reusable blocks.

**Methods:**

#### `generate()`

```python
def generate(
    self,
    data: Dict[str, Any],
    output_path: str
) -> None
```

Generate a PDF with the provided data.

**Parameters:**
- **`data`** (dict): Variable name to value mappings
- **`output_path`** (str): Output PDF file path

**Example: Batch Generation**

```python
from doclayout.api import DocGenerator

# Load template once
generator = DocGenerator("certificate_template.json")

# Generate multiple PDFs
students = [
    {"name": "Alice Smith", "course": "Python 101", "date": "2024-02-08"},
    {"name": "Bob Johnson", "course": "Python 101", "date": "2024-02-08"},
    {"name": "Carol White", "course": "Python 101", "date": "2024-02-08"}
]

for student in students:
    filename = f"certificate_{student['name'].replace(' ', '_')}.pdf"
    generator.generate(student, filename)
    print(f"Generated {filename}")
```

**Example: Using Pre-loaded Template**

```python
from doclayout.api import DocGenerator
from doclayout.core.io import load_template

# Load and inspect template
template = load_template("invoice.json")
print(f"Template: {template.name}")
print(f"Page size: {template.page_size.width}x{template.page_size.height}mm")

# Create generator from template object
generator = DocGenerator(template)

# Generate PDF
data = {"client": "ACME Corp", "total": "$5,000"}
generator.generate(data, "invoice_acme.pdf")
```

---

## Data Binding

### Variable Binding

Templates support two methods of data binding:

#### 1. Simple Variable Binding (Legacy)

Elements can have a `variable_name` property that maps directly to a data key.

**Template Configuration:**
- In the editor, set the element's "Variable Name" property to `client_name`

**Code:**
```python
data = {"client_name": "John Doe"}
generate_pdf("template.json", data, "output.pdf")
```

**Behavior by Element Type:**
- **TEXT**: Replaces the entire text content
- **IMAGE**: Sets the image file path
- **TABLE**: Sets the table data (expects 2D array)

#### 2. Property Bindings (Recommended)

More flexible system allowing multiple properties to be bound to different variables.

**Template Configuration:**
- In the editor, use the "Data Bindings" section
- Add binding: `variable_name` → `target_property`

**Example:**
```python
# Template has bindings:
# - "company_name" → "text"
# - "company_logo" → "image_path"

data = {
    "company_name": "ACME Corporation",
    "company_logo": "/path/to/logo.png"
}

generate_pdf("letterhead.json", data, "letter.pdf")
```

### Supported Data Types

**Strings:**
```python
data = {"name": "John Doe", "title": "Manager"}
```

**Numbers:**
```python
data = {"quantity": 42, "price": 19.99}
# Automatically converted to strings in TEXT elements
```

**Images:**
```python
data = {"photo": "/path/to/image.jpg"}
# Must be valid file path for IMAGE elements
```

**Tables:**
```python
data = {
    "sales_table": [
        ["Product", "Quantity", "Price"],
        ["Widget A", "10", "$100"],
        ["Widget B", "5", "$50"]
    ]
}
# For TABLE elements
```

### Placeholder Syntax (Blocks Only)

When using reusable blocks, text elements support `{{variable}}` placeholder syntax:

**Template Text:**
```
Hello {{customer_name}}, your order #{{order_id}} is ready!
```

**Code:**
```python
data = {"customer_name": "Alice", "order_id": "12345"}
# Output: "Hello Alice, your order #12345 is ready!"
```

**Notes:**
- Placeholders work in BlockInstance data substitution
- Supports whitespace: `{{ variable }}` or `{{variable}}`
- Unknown variables remain as-is: `{{unknown}}` → `{{unknown}}`

---

## Template Structure

### JSON Format

Templates are saved as JSON files with the following structure:

```json
{
  "id": "unique-id",
  "name": "Invoice Template",
  "version": "0.0.2",
  "page_size": {
    "width": 210.0,
    "height": 297.0
  },
  "items": [
    {
      "id": "elem-id",
      "type": "text",
      "x": 10.0,
      "y": 20.0,
      "width": 100.0,
      "height": 10.0,
      "props": {
        "text": "Invoice",
        "font_size": 24,
        "font_bold": true
      },
      "bindings": [
        {
          "variable_name": "invoice_title",
          "target_property": "text"
        }
      ],
      "children": []
    }
  ]
}
```

### Key Fields

- **`version`**: Template format version (auto-updated on save)
- **`page_size`**: Dimensions in millimeters
- **`items`**: Array of elements or block instances
- **`type`**: Element type (`text`, `rect`, `line`, `image`, `kv_box`, `container`, `table`)
- **`x`, `y`, `width`, `height`**: Position and size in mm
- **`props`**: Element-specific properties
- **`bindings`**: Variable to property mappings
- **`children`**: Nested elements (for containers)

---

## Element Types

### TEXT

Text elements display formatted text.

**Bindable Properties:**
- `text`: Text content
- `font_family`: Font name
- `font_size`: Size in points
- `color`: Text color

**Example:**
```python
data = {
    "title": "Annual Report",
    "subtitle_color": "#0066cc"
}
```

### IMAGE

Image elements display pictures from files.

**Bindable Properties:**
- `image_path`: Path to image file

**Supported Formats:**
- JPEG, PNG, GIF (via ReportLab)

**Example:**
```python
data = {
    "company_logo": "/var/logos/acme.png",
    "product_photo": "./images/product_001.jpg"
}
```

### TABLE

Table elements display tabular data.

**Bindable Properties:**
- `data`: 2D array of strings

**Example:**
```python
data = {
    "inventory": [
        ["Item", "Stock", "Price"],
        ["Laptop", "15", "$999"],
        ["Mouse", "120", "$25"],
        ["Keyboard", "80", "$75"]
    ]
}
```

**Table Properties:**
- `show_header`: If true, first row is highlighted
- `font_size`: Text size for all cells

### KV_BOX

Key-value box elements display label-value pairs.

**Bindable Properties:**
- `key_text`: Label text
- `text`: Value text

**Example:**
```python
data = {
    "customer_label": "Customer:",
    "customer_value": "John Doe"
}
```

**Split Types:**
- `ratio`: Split by percentage (e.g., 40% key, 60% value)
- `fixed`: Fixed width in mm for key column
- `auto`: Automatically size based on key text width

### RECT

Rectangle elements for borders and backgrounds.

**Bindable Properties:**
- `fill_color`: Fill color
- `stroke_color`: Border color

**Example:**
```python
data = {
    "status_color": "#00ff00"  # Green for "approved"
}
```

### LINE

Line elements for dividers and connectors.

**Bindable Properties:**
- `color`: Line color
- `stroke_width`: Line thickness

### CONTAINER

Container elements group other elements.

**Features:**
- Children use relative coordinates
- Can have background and border
- Useful for grouping related elements

**Note:** Children are defined in the template, not via data binding.

---

## Working with Blocks

Blocks are reusable template components that can be instantiated multiple times with different data.

### Creating Blocks

1. Design the block in the editor
2. Save as a separate JSON file
3. Load blocks in your code

### Using Blocks

```python
from doclayout.api import DocGenerator
from doclayout.core.io import load_block

# Load block definitions
header_block = load_block("blocks/header.json")
footer_block = load_block("blocks/footer.json")

block_provider = {
    header_block.id: header_block,
    footer_block.id: footer_block
}

# Create generator with blocks
generator = DocGenerator("document.json", block_provider=block_provider)

# Generate with block data
data = {
    "header_company": "ACME Corp",
    "footer_page": "Page 1"
}

generator.generate(data, "output.pdf")
```

---

## Page Sizes

### Standard Sizes

Common page sizes in millimeters:

| Format | Width | Height |
|--------|-------|--------|
| A4 | 210 | 297 |
| Letter | 215.9 | 279.4 |
| Legal | 215.9 | 355.6 |
| A5 | 148 | 210 |

### Thermal Paper

For thermal printers, use standard widths:

| Width | Description |
|-------|-------------|
| 58mm | Small receipts |
| 80mm | Standard receipts |

**Dynamic Height:**
- Thermal paper templates automatically calculate height based on content
- Adds 10mm margin at bottom

**Example:**
```python
# Template with 80mm width
# Height will be calculated based on content
generate_pdf("receipt_80mm.json", data, "receipt.pdf")
```

---

## Error Handling

### Common Errors

**Template Not Found:**
```python
try:
    generate_pdf("missing.json", {}, "out.pdf")
except FileNotFoundError as e:
    print(f"Template not found: {e}")
```

**Invalid Template:**
```python
from pydantic import ValidationError

try:
    generate_pdf("corrupted.json", {}, "out.pdf")
except ValidationError as e:
    print(f"Invalid template structure: {e}")
```

**Missing Image:**
```python
# If image path in data doesn't exist, a red rectangle is drawn
data = {"logo": "/nonexistent/logo.png"}
generate_pdf("template.json", data, "out.pdf")
# PDF will contain red rectangle where image should be
```

**Write Permission:**
```python
try:
    generate_pdf("template.json", {}, "/root/forbidden.pdf")
except IOError as e:
    print(f"Cannot write to output path: {e}")
```

---

## Advanced Features

### Custom Renderers

You can implement custom renderers for different output formats:

```python
from doclayout.engine.renderer_api import Renderer
from doclayout.engine.export import TemplateExporter
from doclayout.core.io import load_template

class SVGRenderer(Renderer):
    # Implement all abstract methods
    def draw_rect(self, x, y, w, h, **kwargs):
        # Custom SVG rendering logic
        pass
    # ... other methods

# Use custom renderer
template = load_template("template.json")
exporter = TemplateExporter()
renderer = SVGRenderer()
exporter.export(template, renderer, "output.svg")
```

### Direct Template Manipulation

```python
from doclayout.core.io import load_template, save_to_json
from doclayout.core.models import BaseElement, ElementType

# Load template
template = load_template("base.json")

# Add element programmatically
new_element = BaseElement(
    type=ElementType.TEXT,
    x=10, y=10, width=50, height=10,
    props={"text": "Added via code", "font_size": 12}
)
template.items.append(new_element)

# Save modified template
save_to_json(template, "modified.json")
```

### Accessing Template Metadata

```python
from doclayout.core.io import load_template

template = load_template("invoice.json")

print(f"Template ID: {template.id}")
print(f"Template Name: {template.name}")
print(f"Version: {template.version}")
print(f"Page: {template.page_size.width}x{template.page_size.height}mm")
print(f"Element Count: {len(template.items)}")

# Inspect elements
for item in template.items:
    if hasattr(item, 'type'):
        print(f"- {item.type}: {item.name or item.id}")
```

---

## Best Practices

### 1. Template Design

- **Use meaningful variable names**: `customer_name` instead of `var1`
- **Test with sample data**: Preview PDFs before production use
- **Keep templates simple**: Complex layouts may be slow to render
- **Use containers**: Group related elements for better organization

### 2. Data Preparation

- **Validate data**: Ensure all required variables are present
- **Format numbers**: Convert to strings with proper formatting
- **Check image paths**: Verify files exist before generation
- **Escape special characters**: In text that might contain markup

### 3. Performance

- **Reuse generators**: Use `DocGenerator` for batch operations
- **Cache templates**: Load once, generate many times
- **Optimize images**: Use appropriately sized images
- **Limit table size**: Very large tables may be slow

### 4. Error Handling

- **Wrap API calls**: Use try-except for production code
- **Log errors**: Keep track of failed generations
- **Provide fallbacks**: Default values for missing data
- **Validate templates**: Test templates before deployment

---

## Examples

### Example 1: Invoice Generator

```python
from doclayout.api import DocGenerator
from datetime import datetime

generator = DocGenerator("invoice_template.json")

invoice_data = {
    "invoice_number": "INV-2024-001",
    "date": datetime.now().strftime("%Y-%m-%d"),
    "client_name": "ACME Corporation",
    "client_address": "123 Business St, City, State 12345",
    "items_table": [
        ["Description", "Qty", "Price", "Total"],
        ["Web Development", "40", "$100/hr", "$4,000"],
        ["Hosting (1 year)", "1", "$500", "$500"],
        ["", "", "Subtotal:", "$4,500"],
        ["", "", "Tax (10%):", "$450"],
        ["", "", "Total:", "$4,950"]
    ],
    "payment_terms": "Net 30",
    "company_logo": "./assets/logo.png"
}

generator.generate(invoice_data, "invoice_001.pdf")
```

### Example 2: Certificate Generator

```python
from doclayout.api import generate_pdf
import csv

# Read student data from CSV
with open("students.csv", "r") as f:
    reader = csv.DictReader(f)
    students = list(reader)

# Generate certificate for each student
for student in students:
    data = {
        "student_name": student["name"],
        "course_name": student["course"],
        "completion_date": student["date"],
        "instructor_signature": "./signatures/instructor.png"
    }
    
    filename = f"certificates/{student['name'].replace(' ', '_')}.pdf"
    generate_pdf("certificate_template.json", data, filename)
    print(f"Generated certificate for {student['name']}")
```

### Example 3: Dynamic Report

```python
from doclayout.api import DocGenerator
from doclayout.core.io import load_template
import json

# Load template and inspect
template = load_template("report_template.json")

# Prepare complex data
with open("sales_data.json", "r") as f:
    sales_data = json.load(f)

report_data = {
    "report_title": "Q1 2024 Sales Report",
    "generated_date": "2024-02-08",
    "summary_text": f"Total sales: ${sales_data['total']:,.2f}",
    "sales_table": [
        ["Month", "Revenue", "Growth"],
        ["January", f"${sales_data['jan']:,.2f}", "+12%"],
        ["February", f"${sales_data['feb']:,.2f}", "+8%"],
        ["March", f"${sales_data['mar']:,.2f}", "+15%"]
    ],
    "chart_image": "./charts/q1_sales.png"
}

generator = DocGenerator(template)
generator.generate(report_data, "q1_report.pdf")
```

---

## API Reference Summary

### Functions

| Function | Description |
|----------|-------------|
| `generate_pdf(template_path, data, output_path)` | Generate PDF from template file |

### Classes

| Class | Description |
|-------|-------------|
| `DocGenerator(template_source, block_provider)` | Reusable PDF generator |
| `DocGenerator.generate(data, output_path)` | Generate PDF with data |

### Core Models (from `doclayout.core.models`)

| Class | Description |
|-------|-------------|
| `Template` | Complete document template |
| `BaseElement` | Visual element (text, rect, etc.) |
| `PageSize` | Page dimensions |
| `VariableBinding` | Variable to property mapping |
| `BlockBase` | Reusable block definition |
| `BlockInstance` | Block instance in template |

### I/O Functions (from `doclayout.core.io`)

| Function | Description |
|----------|-------------|
| `load_template(path)` | Load template from JSON |
| `save_to_json(obj, path)` | Save template/block to JSON |
| `load_block(path)` | Load block from JSON |

---

## Support and Resources

### Documentation
- **Codebase Overview**: See `CODEBASE.md` for architecture details
- **Template Format**: JSON structure documented in this file

### Getting Help
- Check template JSON for validation errors
- Verify data types match element expectations
- Test templates in the editor before API use

### Contributing
- Follow Google Docstring style for new code
- Add tests for new element types
- Update documentation for API changes
