"""
ReportLab Renderer core implementation.
"""

from typing import Optional, List
from reportlab.pdfgen import canvas
from doclayout.engine.renderer_api import Renderer

from .font_helper import FontHelper
from .shapes import ShapeDrawer
from .text_utils import TextDrawer

class ReportLabRenderer(Renderer):
    """
    ReportLab implementation of the Renderer interface.
    """
    def __init__(self) -> None:
        self._canvas: Optional[canvas.Canvas] = None
        self._width = 210.0
        self._height = 297.0

    def set_page_size(self, width: float, height: float) -> None:
        self._width, self._height = width, height

    def start_page(self) -> None:
        if self._canvas: self._canvas.setPageSize((self._width, self._height))

    def end_page(self) -> None:
        if self._canvas: self._canvas.showPage()

    def draw_rect(self, x, y, w, h, stroke_color=None, fill_color=None, stroke_width=1.0) -> None:
        if self._canvas:
            ShapeDrawer.draw_rect(self._canvas, x, y, w, h, self._height, stroke_color, fill_color, stroke_width)

    def draw_line(self, x1, y1, x2, y2, color="black", stroke_width=1.0) -> None:
        if self._canvas:
            ShapeDrawer.draw_line(self._canvas, x1, y1, x2, y2, self._height, color, stroke_width)

    def draw_text(self, x, y, text, font_name="Helvetica", font_size=12, 
                  color="black", alignment="left", width=None,
                  bold=False, italic=False, wrap=False, auto_scale=False) -> None:
        if not self._canvas: return
        resolved = FontHelper.resolve(font_name, bold, italic)
        TextDrawer.draw_text(self._canvas, x, y, text, self._height, resolved, 
                            font_size, color, alignment, width, wrap, auto_scale)

    def draw_image(self, x, y, w, h, path) -> None:
        if not self._canvas or not path: return
        try:
            self._canvas.drawImage(path, x, self._height - (y + h), width=w, height=h)
        except Exception as e:
            self.draw_rect(x, y, w, h, stroke="red")

    def draw_table(self, x, y, w, h, data, col_widths=None, row_heights=None, 
                   font_size=10, stroke_color="black", fill_color_header=None) -> None:
        if not self._canvas or not data: return
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib import colors
        
        # Calculate column widths and row heights based on specified dimensions
        num_rows = len(data)
        num_cols = len(data[0]) if num_rows > 0 else 0
        
        if num_cols == 0 or num_rows == 0:
            return
        
        # If not specified, distribute width and height evenly
        if col_widths is None:
            col_widths = [w / num_cols] * num_cols
        if row_heights is None:
            row_heights = [h / num_rows] * num_rows
        
        table = Table(data, colWidths=col_widths, rowHeights=row_heights)
        style = [('GRID', (0,0), (-1,-1), 0.5, ShapeDrawer.get_color(stroke_color) or colors.black),
                 ('FONTSIZE', (0,0), (-1,-1), font_size),
                 ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]
        if fill_color_header:
            style.append(('BACKGROUND', (0,0), (-1,0), ShapeDrawer.get_color(fill_color_header)))
        table.setStyle(TableStyle(style))
        table.wrapOn(self._canvas, w, h)
        table.drawOn(self._canvas, x, self._height - (y + h))

    def initialize(self, file_path: str) -> None:
        self._canvas = canvas.Canvas(file_path, pagesize=(self._width, self._height))

    def save(self, file_path: str) -> None:
        if self._canvas: self._canvas.save()
