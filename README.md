# DocLayout

A drag-and-drop visual editor for creating PDF templates and reusable blocks, built with Python, PySide6, and ReportLab.

## Project Structure

The project follows a modular architecture:

- `doclayout/core`: Pure Python domain models and logic (No Qt, No ReportLab).
- `doclayout/engine`: Layout engine that processes templates and blocks.
- `doclayout/adapters`: Adapters for external libraries (e.g., ReportLab).
- `doclayout/gui`: The visual editor built with PySide6.
- `doclayout/themes`: UI theme definitions and styling.

## Features

- **Visual Editor**: Drag-and-drop hierarchy for complex layouts.
- **Undo/Redo**: Comprehensive state management (Ctrl+Z / Ctrl+Shift+Z).
- **Responsive Elements**: KV-Boxes and TextBoxes that adapt to content.
- **PDF Export**: High-fidelity generation with ReportLab backend.
- **Reusable Blocks**: Create and instantiate layout components.

- Python 3.10+
- PySide6
- ReportLab
- Pydantic

## Installation

```bash
pip install -r requirements.txt
```

## Running the Editor

```bash
python -m doclayout.main
```

## Documentation

- [API Documentation](docs/API.md): How to use `DocLayout` to generate PDFs.
- [Codebase Overview](docs/CODEBASE.md): Detailed guide to the project structure, files, and classes.
