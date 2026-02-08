"""
Abstract Base Class for the Renderer.
Defines the interface that any PDF backend must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional

class Renderer(ABC):
    """
    Abstract interface for rendering 2D graphics.
    All coordinates should be provided in points (pt).
    """

    @abstractmethod
    def set_page_size(self, width: float, height: float) -> None:
        """Set the dimensions of the current page."""
        pass

    @abstractmethod
    def initialize(self, output_path: str) -> None:
        """Initialize the renderer with output path."""
        pass

    @abstractmethod
    def start_page(self) -> None:
        """Start a new page."""
        pass

    @abstractmethod
    def end_page(self) -> None:
        """Finish the current page."""
        pass

    @abstractmethod
    def draw_rect(self, x: float, y: float, width: float, height: float, 
                  stroke_color: Optional[str] = None, 
                  fill_color: Optional[str] = None, stroke_width: float = 1.0) -> None:
        """Draw a rectangle."""
        pass

    @abstractmethod
    def draw_line(self, x1: float, y1: float, x2: float, y2: float, 
                  color: str = "black", stroke_width: float = 1.0) -> None:
        """Draw a line."""
        pass
    
    @abstractmethod
    def draw_image(self, x: float, y: float, width: float, height: float, path: str) -> None:
        """Draw an image."""
        pass

    @abstractmethod
    def draw_text(self, x: float, y: float, text: str, 
                  font_name: str = "Helvetica", font_size: float = 12, 
                  color: str = "black", alignment: str = "left",
                  width: Optional[float] = None,
                  bold: bool = False, italic: bool = False,
                  wrap: bool = False, auto_scale: bool = False) -> None:
        """Draw text."""
        pass

    @abstractmethod
    def draw_table(self, x: float, y: float, width: float, height: float, 
                   data: list[list[str]], 
                   col_widths: Optional[list[float]] = None,
                   row_heights: Optional[list[float]] = None,
                   font_size: float = 10,
                   stroke_color: str = "black",
                   fill_color_header: Optional[str] = None) -> None:
        """Draw a table."""
        pass

    @abstractmethod
    def save(self, file_path: str) -> None:
        """Save the rendered document to a file."""
        pass
