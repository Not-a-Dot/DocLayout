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
                  bold=False, italic=False, wrap=False, auto_scale=False,
                  bg_color=None, border_color=None, border_width=0, show_border=False,
                  padding=0) -> None:
        if not self._canvas: return
        
        # Draw background and border if requested
        if (bg_color or show_border) and width:
            # We need height for the background. TextDrawer calculates it, but here we might guess or need return
            # For TEXT_BOX, the height is passed in export.py via draw_textbox logic usually
            # But here draw_text is generic. 
            # In export.py, TEXT_BOX renders via draw_text.
            # We ideally should separate drawing the box and drawing the text.
            # However, for now, let's support drawing the rect if height is implied or handled externally
            pass 

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
                   font_size=10, stroke_color="black", fill_color_header=None,
                   theme="Grid", stripe_colors=None) -> None:
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
        
        # Base Style
        style_cmds = [
            ('FONTSIZE', (0,0), (-1,-1), font_size),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),  # Header bold
        ]
        
        # Theme Logic
        border_color = ShapeDrawer.get_color(stroke_color) or colors.black
        
        if theme == "Simple":
            # Only bottom line on header
            style_cmds.append(('LINEBELOW', (0,0), (-1,0), 1, border_color))
        elif theme == "Grid":
            style_cmds.append(('GRID', (0,0), (-1,-1), 0.5, border_color))
        elif theme == "Striped":
             style_cmds.append(('GRID', (0,0), (-1,-1), 0.5, border_color))
             # Row striping handled below
        elif theme == "Dark":
             style_cmds.append(('GRID', (0,0), (-1,-1), 0.5, colors.white))
             style_cmds.append(('BACKGROUND', (0,0), (-1,-1), colors.darkgrey))
             style_cmds.append(('TEXTCOLOR', (0,0), (-1,-1), colors.white))

        # Overrides
        if fill_color_header:
            style_cmds.append(('BACKGROUND', (0,0), (-1,0), ShapeDrawer.get_color(fill_color_header)))
        elif theme == "Striped":
             style_cmds.append(('BACKGROUND', (0,0), (-1,0), colors.lightgrey))
             
        # Striping for Striped theme
        if theme == "Striped":
             for r in range(1, num_rows):
                 if r % 2 == 0:
                     style_cmds.append(('BACKGROUND', (0,r), (-1,r), colors.whitesmoke))

        table.setStyle(TableStyle(style_cmds))
        table.wrapOn(self._canvas, w, h)
        table.drawOn(self._canvas, x, self._height - (y + h))

    def initialize(self, file_path: str) -> None:
        self._canvas = canvas.Canvas(file_path, pagesize=(self._width, self._height))

    def save(self, file_path: str) -> None:
        if self._canvas: self._canvas.save()
