# DocLayout Codebase Overview

This document provides a high-level overview of the `DocLayout` codebase, describing the file structure, key classes, and their responsibilities.

## Directory Structure

### Top Level

- **`doclayout/`**: Source code root.
- **`doclayout/api.py`**: Public API for generating documents programmatically. See `API.md`.
- **`doclayout/main.py`**: Entry point for the graphical editor application.

### `doclayout/core/`

Core definitions, data models, and utilities independent of the GUI.

- **`models.py`**: Contains Pydantic models defining the document structure.
    - `BaseElement`: Base model for all document elements (Rect, Text, etc.).
    - `Template`: Represents a complete document template (pages, items).
    - `ElementType`: Enum defining available element types.
    - `PageSize`: Model for page dimensions.
- **`io.py`**: Functions for loading and saving templates to/from JSON files.
    - `save_template_to_json`: Serializes a `Template` object.
    - `load_template_from_json`: Deserializes a JSON file into a `Template`.
- **`geometry.py`**: Geometric utility functions (e.g., `mm_to_pt` for unit conversion).
- **`variables.py`**: Logic for variable management and data binding.

### `doclayout/engine/`

The engine responsible for processing templates and generating output.

- **`layout.py` (`LayoutEngine`)**: Orchestrates the document compilation process. It resolves data bindings and prepares elements for rendering.
- **`renderer_api.py`**: Abstract base class defining the interface for renderers.

### `doclayout/adapters/`

 implementations of specific rendering backends.

- **`reportlab_adapter.py` (`ReportLabRenderer`)**: A renderer implementation using the `reportlab` library to generate PDFs.

### `doclayout/gui/`

The Graphical User Interface implementation using PySide6 (Qt).

#### Main Components

- **`window.py` (`MainWindow`)**: The main application window.
    - Sets up the UI layout (toolbars, docks, menus).
    - Manages application state, file operations (New, Open, Save), and layout persistence.
    - Initializes the `EditorScene` and `EditorView`.
- **`scene.py` (`EditorScene`)**: A custom `QGraphicsScene`.
    - Manages the document canvas, grid drawing, and item selection.
    - Handles low-level tool logic (creating new items, snapping, alignment guides).
    - Emits signals for item addition, removal, and modification.
- **`view.py` (`EditorView`)**: A custom `QGraphicsView`.
    - Handles user interaction with the scene (zooming, panning).
    - Translates mouse events into scene coordinates.

#### Editor Items (`doclayout/gui/items/`)

Wrapper classes that visualize `core.models` in the Qt Graphics View Framework.

- **`base.py` (`BaseEditorItem`)**: Base class for all editor items. Handles selection, movement, snapping, and locking logic.
- **`rect.py` (`RectEditorItem`)**: Visual representation of Rectangle elements.
- **`text.py` (`TextEditorItem`)**: Visual representation of Text elements.
- **`line.py` (`LineEditorItem`)**: Visual representation of Line elements. Includes custom handles and arrow drawing logic.
- **`image.py` (`ImageEditorItem`)**: Visual representation of Image elements.
- **`kvbox.py` (`KVBoxEditorItem`)**: Specialist item for Key-Value pairs.

#### UI Components

- **`panels.py`**: Implementation of dockable panels.
    - `PropertyEditor`: Inspects and modifies properties of the selected item. Uses `CollapsibleSection` for organization.
    - `LibraryPanel`: Helper panel for dragging new element types onto the canvas.
    - `StructurePanel`: Tree view showing the hierarchy of elements in the scene.
- **`themes.py` (`ThemeManager`)**: Manages application themes (Light, Dark) and applies stylesheets.
- **`rulers.py` (`Ruler`)**: Custom widget for displaying horizontal and vertical rulers.
- **`handles.py` (`ResizeHandle`)**: Graphics items for resizing elements on the canvas.

## Functionality Flow

1.  **Startup**: `main.py` initializes `QApplication` and `MainWindow`.
2.  **Scene Setup**: `MainWindow` creates an `EditorScene` and `EditorView`. Rulers are attached to the view.
3.  **Item Creation**: User selects a tool (e.g., Rectangle). `EditorScene` handles the mouse click, creates a `BaseElement` model, wraps it in a `RectEditorItem`, and adds it to the scene.
4.  **Property Editing**: Selecting an item triggers `PropertyEditor` to update. Changes in the panel update the item's model and visual state directly.
5.  **Saving**: `MainWindow` gathers models from all items in the scene into a `Template` object and uses `core.io` to save it as JSON.
6.  **PDF Generation**: The `generate_pdf` API loads the JSON template, uses `LayoutEngine` to resolve data bindings, and delegates rendering to `ReportLabRenderer`.
