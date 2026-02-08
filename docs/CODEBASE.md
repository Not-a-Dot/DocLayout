# DocLayout Codebase Documentation

## Overview

DocLayout is a visual document template editor and PDF generation library built with Python, PySide6 (Qt), and ReportLab. It provides both a graphical editor for designing templates and a programmatic API for generating PDFs with data binding.

## Architecture

The project follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    GUI Layer (PySide6)                  │
│  Window, Scene, View, Panels, Items, Tools              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    API Layer                            │
│  DocGenerator, generate_pdf()                           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Engine Layer                           │
│  LayoutEngine, TemplateExporter                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  Adapter Layer                          │
│  ReportLabRenderer (implements Renderer interface)      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    Core Layer                           │
│  Models, I/O, Geometry, Variables                       │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

### Root Level

```
doclayout/
├── __init__.py
├── main.py              # GUI application entry point
├── api.py               # Public API for PDF generation
├── core/                # Core data models and utilities
├── engine/              # Template processing and export
├── adapters/            # Rendering backend implementations
├── gui/                 # Graphical editor (PySide6)
├── themes/              # UI theme definitions
└── utils/               # Utility functions
```

---

## Core Module (`doclayout/core/`)

The core module defines fundamental data structures and utilities independent of GUI or rendering backends.

### `models.py`

Defines the complete document structure using Pydantic models.

#### Key Classes

**`ElementType`** (Enum)
- Enumeration of supported element types
- Values: `RECT`, `TEXT`, `LINE`, `IMAGE`, `KV_BOX`, `CONTAINER`, `TABLE`

**`BaseElement`** (BaseModel)
- Base class for all visual elements
- Attributes:
  - `id`: Unique identifier (auto-generated UUID)
  - `type`: ElementType
  - `x`, `y`: Position in mm (relative to parent or page)
  - `width`, `height`: Dimensions in mm
  - `props`: Dictionary of element-specific properties
  - `bindings`: List of VariableBinding for data binding
  - `children`: List of child elements (hierarchical support)
  - `name`: Optional human-readable name
- Properties:
  - `lock_children`: Prevents child selection/modification
  - `lock_position`: Prevents moving the element
  - `lock_geometry`: Prevents resizing the element
  - `lock_selection`: Prevents direct selection in GUI

**`VariableBinding`** (BaseModel)
- Maps a global variable to an element property
- Attributes:
  - `variable_name`: Name of the data variable
  - `target_property`: Property key to bind to (e.g., "text", "image_path")

**`BlockBase`** (BaseModel)
- Reusable block definition (template component)
- Attributes:
  - `id`: Unique identifier
  - `name`: Human-readable name
  - `width`, `height`: Block canvas dimensions in mm
  - `elements`: List of BaseElement instances

**`BlockInstance`** (BaseModel)
- Instance of a BlockBase placed in a template
- Attributes:
  - `id`: Instance identifier
  - `block_id`: Reference to BlockBase
  - `x`, `y`: Position in template
  - `data`: Dictionary for placeholder substitution

**`PageSize`** (BaseModel)
- Page dimensions
- Attributes: `width`, `height` (in mm)

**`Template`** (BaseModel)
- Complete document template
- Attributes:
  - `id`: Unique identifier
  - `name`: Template name
  - `version`: Format version (for migration)
  - `page_size`: PageSize object
  - `items`: List of BaseElement or BlockInstance

#### Version Management

- `CURRENT_VERSION`: Current template format version ("0.0.2")
- Version is automatically set when saving templates

### `io.py`

Handles loading and saving templates with automatic migration support.

#### Functions

**`save_to_json(obj: Union[Template, BlockBase], file_path: str)`**
- Serializes Template or BlockBase to JSON
- Automatically updates version to CURRENT_VERSION
- Creates parent directories if needed

**`load_template(file_path: str) -> Template`**
- Loads and validates a template from JSON
- Automatically migrates legacy formats
- Raises FileNotFoundError or ValidationError on failure

**`load_block(file_path: str) -> BlockBase`**
- Loads a block definition from JSON

**`load_from_json(file_path: str) -> dict`**
- Generic JSON loader returning raw dictionary

#### Migration System

**`_migrate_template_data(data: Dict[str, Any]) -> Dict[str, Any]`**
- Orchestrates migration from old versions to current
- Currently supports migration from 0.0.0/0.0.1 to 0.0.2

**`_migrate_v001_to_v002(data: Dict[str, Any]) -> Dict[str, Any]`**
- Migrates flat structure to hierarchical (parent-child relationships)
- Automatically nests items inside containers based on geometric containment
- Handles container-in-container nesting
- Converts absolute coordinates to relative coordinates for children

### `geometry.py`

Unit conversion utilities for coordinate transformations.

#### Constants

- `MM_TO_PT = 2.83465`: Millimeters to points conversion factor
- `PT_TO_MM = 1.0 / MM_TO_PT`: Points to millimeters conversion factor

#### Functions

**`mm_to_pt(mm: float) -> float`**
- Converts millimeters to points (PDF coordinate system)

**`pt_to_mm(pt: float) -> float`**
- Converts points to millimeters (editor coordinate system)

### `variables.py`

Global variable management system (singleton pattern).

#### Class: `VariableManager`

Manages a global registry of template variables with persistence.

**Methods:**
- `add_variable(name: str, default_value: str = "")`: Register a new variable
- `get_variables() -> List[str]`: Get all variable names
- `get_value(name: str) -> str`: Get variable default value
- `save_variables()`: Persist to `variables.json`

**Storage:**
- Variables are stored in `variables.json` in the project root
- Automatically loaded on first instantiation

---

## Engine Module (`doclayout/engine/`)

The engine processes templates and coordinates rendering.

### `layout.py`

#### Class: `LayoutEngine`

Compiles templates into flat lists of renderable elements.

**Constructor:**
- `__init__(block_provider: Dict[str, BlockBase])`: Initialize with block definitions

**Methods:**

**`compile(template: Template) -> List[BaseElement]`**
- Main compilation method
- Flattens hierarchical structure into absolute-positioned elements
- Resolves BlockInstance references
- Applies variable bindings
- Returns list of BaseElement ready for rendering

**`apply_bindings(elements: List[BaseElement], variables: Dict[str, Any])`**
- Applies VariableBinding mappings to element properties

**`_resolve_block(instance: BlockInstance) -> List[BaseElement]`**
- Expands a BlockInstance into its constituent elements
- Applies instance position offset
- Substitutes {{variable}} placeholders in text

**`_flatten_tree(element: BaseElement, offset_x: float, offset_y: float) -> List[BaseElement]`**
- Recursively flattens element hierarchy
- Converts relative coordinates to absolute
- Returns deep copies to avoid mutating original template

**`_substitute_text(element: BaseElement, data: Dict[str, Any])`**
- Replaces `{{variable}}` placeholders in text elements
- Uses regex pattern: `\{\{\s*(\w+)\s*\}\}`

### `export.py`

#### Class: `TemplateExporter`

Bridges LayoutEngine and Renderer implementations.

**Constructor:**
- `__init__(block_provider: Optional[Dict[str, Any]] = None)`: Initialize with optional blocks

**Methods:**

**`export(template: Template, renderer: Renderer, output_path: str)`**
- Complete export pipeline
- Compiles template using LayoutEngine
- Calculates dynamic page height for thermal paper (58mm, 80mm widths)
- Initializes renderer and renders all elements
- Saves final output

**`_render_element(elem: BaseElement, renderer: Renderer)`**
- Dispatches element rendering based on type
- Handles all element types: RECT, TEXT, IMAGE, LINE, KV_BOX, CONTAINER, TABLE
- Converts mm coordinates to points
- Applies element-specific properties

**`_resolve_rl_font(font_name: str, bold: bool, italic: bool) -> str`**
- Maps generic font names to ReportLab standard fonts
- Handles font style variations (bold, italic, bold-italic)

### `renderer_api.py`

#### Class: `Renderer` (ABC)

Abstract interface for rendering backends. All coordinates in points.

**Abstract Methods:**
- `set_page_size(width: float, height: float)`: Set page dimensions
- `initialize(output_path: str)`: Initialize renderer
- `start_page()`: Begin new page
- `end_page()`: Finish current page
- `draw_rect(...)`: Draw rectangle with optional stroke/fill
- `draw_line(...)`: Draw line
- `draw_image(...)`: Draw image from file
- `draw_text(...)`: Draw text with formatting, alignment, wrapping
- `draw_table(...)`: Draw table with data
- `save(file_path: str)`: Save final output

---

## Adapters Module (`doclayout/adapters/`)

### ReportLab Adapter (`adapters/reportlab/`)

Implementation of the Renderer interface using ReportLab library.

#### `renderer.py`

**Class: `ReportLabRenderer`**

Main renderer implementation.

**Methods:**
- Implements all Renderer abstract methods
- Delegates to specialized helper classes:
  - `FontHelper`: Font resolution
  - `ShapeDrawer`: Shape rendering
  - `TextDrawer`: Text rendering with wrapping/scaling

**Key Features:**
- Coordinate transformation (top-left to bottom-left origin)
- Error handling for missing images (draws red rectangle)
- Table rendering using ReportLab Platypus

#### `font_helper.py`

**Class: `FontHelper`**

Maps generic font names to ReportLab standard fonts.

**Method:**
- `resolve(font_name: str, bold: bool, italic: bool) -> str`
  - Supports: Helvetica, Times-Roman, Courier
  - Handles style variations (Bold, Oblique/Italic, BoldOblique/BoldItalic)

#### `shapes.py`

**Class: `ShapeDrawer`**

Draws basic shapes with coordinate transformation.

**Methods:**
- `get_color(color_str: Optional[str])`: Converts color strings to ReportLab colors
- `draw_rect(...)`: Draws rectangles with stroke/fill
- `draw_line(...)`: Draws lines

#### `text_utils.py`

**Class: `TextDrawer`**

Advanced text rendering with wrapping and auto-scaling.

**Method:**
- `draw_text(...)`: Handles:
  - Auto-scaling to fit width
  - Text wrapping using `simpleSplit`
  - Alignment (left, center, right)
  - Multi-line rendering with line height calculation

---

## API Module (`doclayout/api.py`)

Public interface for programmatic PDF generation.

### Function: `generate_pdf`

**Signature:**
```python
def generate_pdf(template_path: str, data: Dict[str, Any], output_path: str)
```

Convenience function for one-shot PDF generation.

**Parameters:**
- `template_path`: Path to JSON template file
- `data`: Dictionary mapping variable names to values
- `output_path`: Output PDF file path

### Class: `DocGenerator`

Reusable generator for multiple PDFs from same template.

**Constructor:**
```python
def __init__(self, template_source: Union[str, Template], block_provider: Dict[str, Any] = None)
```

**Parameters:**
- `template_source`: File path or Template object
- `block_provider`: Optional block definitions

**Methods:**

**`generate(data: Dict[str, Any], output_path: str)`**
- Generates PDF with data binding
- Deep copies template to avoid mutation
- Applies bindings before export

**`_apply_bindings(item, data)`**
- Recursively applies data bindings
- Supports both official `bindings` list and legacy `variable_name`
- Handles special cases for TEXT, IMAGE, TABLE elements

---

## GUI Module (`doclayout/gui/`)

Visual editor implementation using PySide6 (Qt).

### Window (`gui/window/`)

#### `main_window.py`

**Class: `MainWindow`**

Primary application window and coordinator.

**Initialization:**
- Creates `EditorScene` and `EditorView`
- Sets up rulers, toolbars, menus, dock widgets
- Loads saved layout from QSettings

**Key Methods:**
- `save_file()`: Save template to JSON
- `open_file()`: Load template from JSON
- `preview_pdf()`: Generate and open preview PDF
- `export_pdf()`: Export to PDF file
- `new_file()`: Clear editor
- `set_theme(theme_name)`: Apply UI theme
- `closeEvent()`: Save layout on exit

**Layout Persistence:**
- Uses QSettings for window geometry and dock positions
- Supports named layout presets

#### `actions.py`

**Class: `ActionManager`**

Manages all QAction instances for menu items and toolbar buttons.

#### `menus.py`

**Class: `MenuManager`**

Sets up application menus (File, Edit, View, Tools, Help).

#### `toolbars.py`

**Class: `ToolbarManager`**

Creates toolbars for file operations, tools, and alignment.

#### `dock_widgets.py`

**Class: `DockManager`**

Sets up dockable panels (Properties, Library, Structure, Blocks).

### Scene (`gui/scene/`)

#### `scene.py`

**Class: `EditorScene`**

Core editing coordinator extending QGraphicsScene.

**Signals:**
- `toolChanged`: Active tool changed
- `itemAdded`: Item added to scene
- `itemMoved`: Item geometry changed
- `itemRemoved`: Item deleted
- `hierarchyChanged`: Parent-child relationships changed

**Key Features:**
- Grid and snap-to-grid rendering
- Page boundary visualization
- Tool management (select, rect, text, line, etc.)
- Clipboard operations (copy/paste)
- Grouping/ungrouping
- Template serialization (`to_template()`)

**Methods:**
- `set_tool(tool_name)`: Change active tool
- `set_snap(enabled)`: Toggle snap-to-grid
- `set_grid_size(size)`: Set grid spacing
- `set_page_size(width, height)`: Change page dimensions
- `delete_selected()`: Delete selected items
- `copy_selected()`, `paste()`: Clipboard operations
- `group_selected()`: Group items into container

#### `alignment.py`

**Class: `AlignmentManager`**

Handles snap-to-grid and alignment guides.

**Features:**
- Grid snapping with configurable spacing
- Dynamic alignment guides when moving items
- Visual guide rendering

#### `clipboard.py`

**Class: `SceneClipboard`**

Copy/paste functionality with deep cloning.

#### `grouping.py`

**Class: `GroupingManager`**

Groups selected items into a container element.

#### `handlers.py`

**Class: `SceneEventHandler`**

Processes mouse and keyboard events for tool operations.

#### `tools.py`

Tool-specific logic for creating elements (rectangles, text, lines, etc.).

### View (`gui/view.py`)

**Class: `EditorView`**

Custom QGraphicsView with zoom and pan support.

**Features:**
- Ctrl+Wheel zoom
- Middle-button pan
- Rubber band selection
- Antialiasing
- Initial scale for mm visibility (3.78x for 96 DPI)

**Signals:**
- `viewportChanged`: Emitted on zoom/pan for ruler updates

### Items (`gui/items/`)

Visual representations of core models in Qt Graphics View.

#### `base.py`

**Class: `BaseEditorItem`**

Mixin providing common functionality for all editor items.

**Features:**
- Model synchronization
- Lock state enforcement (position, geometry, selection, children)
- Snap-to-grid during movement
- Handle visibility management
- Lock icon rendering
- Child item creation from model hierarchy

**Methods:**
- `update_locking()`: Apply lock flags
- `update_handles()`: Show/hide resize handles
- `paint_lock_icons()`: Draw lock indicators
- `create_properties_widget()`: Return custom property editor (override)
- `get_bindable_properties()`: Return bindable property list (override)

#### Element-Specific Items

- **`rect.py`**: `RectEditorItem` - Rectangle elements
- **`text/item.py`**: `TextEditorItem` - Text elements with rich formatting
- **`line/item.py`**: `LineEditorItem` - Line elements with arrow support
- **`image.py`**: `ImageEditorItem` - Image elements
- **`kvbox/item.py`**: `KVBoxEditorItem` - Key-value box elements
- **`container.py`**: `ContainerEditorItem` - Container elements for grouping
- **`table.py`**: `TableEditorItem` - Table elements

Each item type:
- Extends QGraphicsItem and BaseEditorItem
- Implements `boundingRect()` and `paint()`
- Provides custom property editor widget
- Handles element-specific interactions

### Panels (`gui/panels/`)

#### `properties.py`

**Class: `PropertyEditor`**

Dockable panel for editing selected item properties.

**Features:**
- Dynamic property widgets based on item type
- Collapsible sections for organization
- Real-time model updates
- Data binding configuration UI

#### `structure.py`

**Class: `StructurePanel`**

Tree view showing document hierarchy.

**Features:**
- Drag-and-drop reparenting
- Selection synchronization with scene
- Hierarchical visualization

#### `blocks.py`

**Class: `BlocksPanel`**

Manages reusable block definitions.

#### `collapsible.py`

**Class: `CollapsibleSection`**

Expandable/collapsible widget container for property organization.

### Other GUI Components

#### `rulers.py`

**Class: `Ruler`**

Horizontal and vertical rulers with mm markings.

**Features:**
- Synchronized with view transform
- Dynamic scale based on zoom level
- Major/minor tick marks

#### `handles.py`

**Class: `ResizeHandle`**

Visual handles for resizing elements.

**Features:**
- 8 resize positions (corners and edges)
- Aspect ratio preservation (Shift key)
- Snap-to-grid during resize

#### `themes.py`

**Class: `ThemeManager`**

Manages application themes (Light/Dark).

**Methods:**
- `apply_theme(app, theme_name)`: Apply stylesheet
- `get_editor_colors()`: Get theme-specific colors for scene rendering

---

## Main Entry Point (`doclayout/main.py`)

Application launcher for the GUI editor.

**Function: `main()`**
- Initializes QApplication
- Sets up global exception handler
- Creates and shows MainWindow
- Starts Qt event loop

**Platform-Specific:**
- Sets `QT_QPA_PLATFORMTHEME=""` on Linux to avoid DBus portal errors

---

## Data Flow

### Template Creation (GUI)

1. User creates elements via tools in `EditorScene`
2. Each tool creates a `BaseElement` model
3. Model is wrapped in appropriate `EditorItem` subclass
4. Item added to scene, triggers `itemAdded` signal
5. `StructurePanel` updates hierarchy view
6. `PropertyEditor` shows properties when selected

### Template Saving

1. `MainWindow.save_file()` called
2. `EditorScene.to_template()` collects all root items
3. `_sync_model_hierarchy()` updates model children from GUI state
4. `save_to_json()` serializes to JSON with version update

### Template Loading

1. `MainWindow.open_file()` called
2. `load_template()` reads and migrates JSON
3. For each item model, `get_item_for_model()` creates corresponding EditorItem
4. Items added to scene, hierarchy reconstructed

### PDF Generation (API)

1. `generate_pdf()` or `DocGenerator.generate()` called
2. Template loaded via `load_template()`
3. Data bindings applied to template copy
4. `TemplateExporter.export()` called:
   - `LayoutEngine.compile()` flattens hierarchy
   - Resolves BlockInstances
   - Applies variable bindings
5. For each element, `_render_element()` dispatches to renderer
6. `ReportLabRenderer` draws to PDF canvas
7. `renderer.save()` writes final PDF

---

## Element Types Reference

### RECT (Rectangle)

**Properties:**
- `show_outline` (bool): Draw border
- `stroke_width` (float): Border width in points
- `stroke_color` (str): Border color
- `fill_color` (str): Fill color

### TEXT

**Properties:**
- `text` (str): Text content
- `font_family` (str): Font name
- `font_size` (float): Size in points
- `font_bold` (bool): Bold style
- `font_italic` (bool): Italic style
- `color` (str): Text color
- `text_align` (str): Alignment (left, center, right)

### LINE

**Properties:**
- `x2`, `y2` (float): End point coordinates in mm
- `stroke_width` (float): Line width in points
- `color` (str): Line color
- `start_arrow`, `end_arrow` (bool): Arrow heads

### IMAGE

**Properties:**
- `image_path` (str): Path to image file
- Can be bound to variable for dynamic images

### KV_BOX (Key-Value Box)

**Properties:**
- `key_text` (str): Label text
- `text` (str): Value text
- `split_type` (str): "ratio", "fixed", or "auto"
- `split_ratio` (float): Ratio for split (0.0-1.0)
- `split_fixed` (float): Fixed width in mm for key column
- `font_family`, `font_size`, `font_bold`, `font_italic`
- `show_outline` (bool): Draw borders
- `stroke_width` (float): Border width
- `border_color`, `divider_color` (str): Colors

### CONTAINER

**Properties:**
- `bg_type` (str): "transparent" or "solid"
- `fill_color` (str): Background color
- `show_outline` (bool): Draw border
- `stroke_color` (str): Border color
- `stroke_width` (float): Border width

**Special:**
- Can contain children elements
- Children coordinates are relative to container origin

### TABLE

**Properties:**
- `data` (list[list[str]]): Table data (2D array)
- `font_size` (float): Text size
- `show_header` (bool): Highlight first row
- `col_widths`, `row_heights` (list[float]): Optional size constraints

---

## Testing

### Manual Testing

**GUI Editor:**
1. Run `python -m doclayout.main`
2. Create elements using toolbar tools
3. Test property editing in right panel
4. Test save/load with JSON files
5. Test PDF preview and export

**API:**
1. Create template in editor and save as JSON
2. Use `test_api.py` as reference
3. Test data binding with various data types
4. Verify PDF output matches template

### Test Files

- `test_api.py`: Basic API usage example
- `test_template.json`: Sample template
- `table_test_template.json`: Table element example

---

## Extension Points

### Adding New Element Types

1. Add new `ElementType` enum value in `core/models.py`
2. Create EditorItem subclass in `gui/items/`
3. Implement rendering in `engine/export.py` `_render_element()`
4. Add tool logic in `gui/scene/tools.py`
5. Create property widget in item's `create_properties_widget()`

### Adding New Renderers

1. Implement `Renderer` interface from `engine/renderer_api.py`
2. Handle coordinate transformations as needed
3. Register in `adapters/` module
4. Update `DocGenerator` to support new renderer

### Custom Themes

1. Add theme definition in `gui/themes.py`
2. Define stylesheet and editor colors
3. Register in `ThemeManager`

---

## Dependencies

### Core
- `pydantic`: Data validation and models
- `reportlab`: PDF generation backend

### GUI
- `PySide6`: Qt bindings for Python

### Development
- Standard library only for core functionality

---

## Configuration

### Settings Storage

**QSettings Locations:**
- Organization: "DocLayout"
- Application: "Editor"
- Stores: window geometry, dock positions, named layouts

**Variables:**
- Stored in `variables.json` in project root
- Managed by `VariableManager` singleton

---

## Performance Considerations

### Template Compilation

- Deep copying prevents template mutation but uses memory
- Large hierarchies may slow compilation
- Consider caching compiled templates for repeated generation

### GUI Rendering

- Qt Graphics View uses scene caching
- Large documents may benefit from level-of-detail rendering
- Grid rendering disabled when snap is off

### PDF Generation

- ReportLab is generally fast for simple documents
- Image embedding can be slow for large files
- Table rendering uses Platypus (may be slower for large tables)

---

## Known Limitations

1. **Fonts**: Limited to ReportLab standard fonts (Helvetica, Times, Courier)
2. **Images**: No image transformation (rotation, skew) in PDF output
3. **Text**: No rich text formatting (mixed styles within single element)
4. **Tables**: Limited styling options compared to full spreadsheet applications
5. **Undo/Redo**: Not implemented in current version
6. **Multi-page**: Templates are single-page (thermal paper uses dynamic height)

---

## Future Enhancements

- Custom font support via TTF embedding
- Rich text editing with inline formatting
- Multi-page template support
- Undo/redo system
- Template variables panel in GUI
- Block library management UI
- Export to formats beyond PDF (HTML, SVG)
- Collaborative editing features
## Internationalization\n\nDocLayout supports multiple languages via JSON translation files. See [I18N.md](I18N.md) for complete documentation.\n\n**Quick Start:**\n```python\nfrom doclayout.core.i18n import tr\ntitle = tr('menu.file.new')  # Auto-translated\n```\n\n**Supported Languages:** pt-BR (default), en-US
