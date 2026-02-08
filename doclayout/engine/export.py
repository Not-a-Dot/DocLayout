"""
Centralized Export logic for DocLayout.
"""
from typing import List, Dict, Any, Optional
from doclayout.core.models import Template, ElementType, BaseElement
from doclayout.core.geometry import mm_to_pt
from doclayout.engine.layout import LayoutEngine
from doclayout.engine.renderer_api import Renderer
from reportlab.pdfbase.pdfmetrics import stringWidth

class TemplateExporter:
    """
    Bridge between Layout Engine and Renderers.
    """
    def __init__(self, block_provider: Optional[Dict[str, Any]] = None):
        self.engine = LayoutEngine(block_provider or {})

    def export(self, template: Template, renderer: Renderer, output_path: str):
        """
        Compile and render a template to the given output path.
        """
        elements = self.engine.compile(template)
        
        # Calculate dynamic height for thermal paper
        page_w = template.page_size.width
        actual_height = template.page_size.height
        
        if page_w in [58, 80]:
            max_y = 0
            for elem in elements:
                max_y = max(max_y, elem.y + elem.height)
            actual_height = max_y + 10 # 10mm margin
        
        # Setup renderer
        renderer.set_page_size(mm_to_pt(page_w), mm_to_pt(actual_height))
        renderer.initialize(output_path)
        renderer.start_page()
        
        for elem in elements:
            self._render_element(elem, renderer)
            
        renderer.end_page()
        renderer.save(output_path)
        return output_path

    def _resolve_rl_font(self, font_name: str, bold: bool, italic: bool) -> str:
        # Standard mapping
        mapping = {
            "Arial": "Helvetica",
            "Helvetica": "Helvetica",
            "Times New Roman": "Times-Roman",
            "Times": "Times-Roman",
            "Courier New": "Courier",
            "Courier": "Courier"
        }
        base = mapping.get(font_name, "Helvetica")
        
        if base == "Helvetica":
            if bold and italic: return "Helvetica-BoldOblique"
            if bold: return "Helvetica-Bold"
            if italic: return "Helvetica-Oblique"
            return "Helvetica"
        elif base == "Times-Roman":
            if bold and italic: return "Times-BoldItalic"
            if bold: return "Times-Bold"
            if italic: return "Times-Italic"
            return "Times-Roman"
        elif base == "Courier":
            if bold and italic: return "Courier-BoldOblique"
            if bold: return "Courier-Bold"
            if italic: return "Courier-Oblique"
            return "Courier"
        return base

    def _render_element(self, elem: BaseElement, renderer: Renderer):
        x = mm_to_pt(elem.x)
        y = mm_to_pt(elem.y)
        w = mm_to_pt(elem.width)
        h = mm_to_pt(elem.height)
        
        if elem.type == ElementType.RECT:
            stroke = "black" if elem.props.get("show_outline", False) else None
            stroke_w = elem.props.get("stroke_width", 1.0)
            renderer.draw_rect(x, y, w, h, stroke_color=stroke, stroke_width=stroke_w)
        elif elem.type == ElementType.TEXT:
            font_name = elem.props.get("font_family", "Helvetica")
            font_size = elem.props.get("font_size", 12)
            color = elem.props.get("color", "black")
            align = elem.props.get("text_align", "left")
            bold = elem.props.get("font_bold", False)
            italic = elem.props.get("font_italic", False)
            renderer.draw_text(x, y, elem.props.get("text", ""), 
                               font_name=font_name, font_size=font_size, 
                               color=color, alignment=align, width=w,
                               bold=bold, italic=italic, wrap=True)
        elif elem.type == ElementType.IMAGE:
            renderer.draw_image(x, y, w, h, elem.props.get("image_path", ""))
        elif elem.type == ElementType.LINE:
            x2 = mm_to_pt(elem.props.get("x2", 0))
            y2 = mm_to_pt(elem.props.get("y2", 0))
            renderer.draw_line(x, y, x2, y2)
        elif elem.type == ElementType.KV_BOX:
            props = elem.props
            stype = props.get("split_type", "ratio")
            
            font_family = props.get("font_family", "Helvetica")
            font_size = props.get("font_size", 10)
            bold = props.get("font_bold", False)
            italic = props.get("font_italic", False)
            
            if stype == "fixed":
                split = mm_to_pt(props.get("split_fixed", 20.0))
            elif stype == "auto":
                # Auto logic: measure key text
                rl_font = self._resolve_rl_font(font_family, bold, italic)
                key_txt = props.get("key_text", "Label:")
                try:
                    txt_w = stringWidth(key_txt, rl_font, font_size)
                except:
                    txt_w = stringWidth(key_txt, "Helvetica", font_size)
                
                # Add 1.5mm padding (Editor uses 1.0mm, but PDF might need a tad more to be safe)
                split = txt_w + mm_to_pt(1.5)
            else: # ratio
                ratio = props.get("split_ratio", 0.4)
                split = w * ratio

            show_outline = props.get("show_outline", True)
            stroke_w = props.get("stroke_width", 0.5)
            border_color = props.get("border_color", "black")
            divider_color = props.get("divider_color", "black")

            # Outer rect
            if show_outline:
                renderer.draw_rect(x, y, w, h, stroke_color=border_color, stroke_width=stroke_w)
                # Split line
                renderer.draw_line(x + split, y, x + split, y + h, color=divider_color, stroke_width=stroke_w)
            
            color = props.get("color", "black")
            v_offset = (h - font_size) / 2
            
            # Key Label
            renderer.draw_text(x + mm_to_pt(0.5), y + v_offset, props.get("key_text", "Label:"), 
                               font_name=font_family, font_size=font_size, color=color,
                               width=split - mm_to_pt(0.5), bold=bold, italic=italic, wrap=True, auto_scale=True)
            
            # Value Label
            renderer.draw_text(x + split + mm_to_pt(0.5), y + v_offset, props.get("text", "[Value]"), 
                               font_name=font_family, font_size=font_size, color=color,
                               width=w - split - mm_to_pt(0.5), bold=bold, italic=italic, wrap=True, auto_scale=True)
                               
        elif elem.type == ElementType.CONTAINER:
            # Draw container background and border like a rectangle
            props = elem.props
            bg_type = props.get("bg_type", "transparent")
            show_outline = props.get("show_outline", False)
            
            fill = props.get("fill_color", "#ffffff") if bg_type == "solid" else None
            stroke = props.get("stroke_color", "black") if show_outline else None
            stroke_w = props.get("stroke_width", 1.0)
            
            # Note: Container might also have opacity/alpha, but renderer_api doesn't 
            # currently expose it directly in draw_rect. We keep it simple.
            if fill or stroke:
                renderer.draw_rect(x, y, w, h, stroke_color=stroke, fill_color=fill, stroke_width=stroke_w)
            
            # Children are already flattened by LayoutEngine, so we don't need to recursively render here.
            pass

        elif elem.type == ElementType.TABLE:
            data = elem.props.get("data", [])
            if data:
                font_size = elem.props.get("font_size", 10)
                show_header = elem.props.get("show_header", True)
                
                # If show_header is True, we highlight the first row
                fill_h = "#f0f0f0" if show_header else None
                
                renderer.draw_table(x, y, w, h, data, 
                                   font_size=font_size,
                                   fill_color_header=fill_h)
            pass
