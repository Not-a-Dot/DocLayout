"""
Shape drawing utilities for ReportLab renderer.
"""

from typing import Optional
from reportlab.lib.colors import HexColor, toColor

class ShapeDrawer:
    """
    Draws basic shapes onto a ReportLab canvas.
    """
    @staticmethod
    def get_color(color_str: Optional[str]):
        if not color_str: return None
        try:
            return HexColor(color_str)
        except:
            return toColor(color_str)

    @staticmethod
    def draw_rect(canvas, x: float, y: float, w: float, h: float, page_h: float,
                  stroke: Optional[str], fill: Optional[str], width: float) -> None:
        canvas.saveState()
        canvas.setStrokeColor(ShapeDrawer.get_color(stroke) or toColor("black"))
        if fill:
            canvas.setFillColor(ShapeDrawer.get_color(fill))
            f_bit = 1
        else:
            f_bit = 0
            
        canvas.setLineWidth(width)
        pdf_y = page_h - (y + h)
        canvas.rect(x, pdf_y, w, h, stroke=(1 if stroke else 0), fill=f_bit)
        canvas.restoreState()

    @staticmethod
    def draw_line(canvas, x1: float, y1: float, x2: float, y2: float, page_h: float,
                  color: str, width: float) -> None:
        canvas.saveState()
        canvas.setStrokeColor(ShapeDrawer.get_color(color))
        canvas.setLineWidth(width)
        canvas.line(x1, page_h - y1, x2, page_h - y2)
        canvas.restoreState()
