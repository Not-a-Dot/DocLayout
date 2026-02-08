"""
Text drawing and wrapping for ReportLab renderer.
"""

from typing import Optional
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from .shapes import ShapeDrawer

class TextDrawer:
    """
    Handles complex text drawing including wrapping and auto-scaling.
    """
    @staticmethod
    def draw_text(canvas, x: float, y: float, text: str, page_h: float,
                  font_name: str, font_size: float, color: str,
                  alignment: str, width: Optional[float],
                  wrap: bool, auto_scale: bool) -> None:
        
        canvas.saveState()
        canvas.setFillColor(ShapeDrawer.get_color(color))
        
        fs = font_size
        if auto_scale and width and width > 0:
            tw = stringWidth(text, font_name, fs)
            if tw > width:
                fs = fs * (width / tw) * 0.98
        
        canvas.setFont(font_name, fs)
        
        lines = [text]
        if not auto_scale and wrap and width and width > 0:
            # Always wrap if text exceeds width
            if stringWidth(text, font_name, fs) > width:
                lines = simpleSplit(text, font_name, fs, width)
        
        line_h = fs * 1.2
        start_pdf_y = page_h - (y + (fs * 0.8))
        
        for i, line in enumerate(lines):
            draw_y = start_pdf_y - (i * line_h)
            if alignment == "center":
                canvas.drawCentredString(x + (width/2 if width else 0), draw_y, line)
            elif alignment == "right":
                canvas.drawRightString(x + (width if width else 0), draw_y, line)
            else:
                canvas.drawString(x, draw_y, line)
        
        canvas.restoreState()
