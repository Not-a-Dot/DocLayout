"""
Centralized Export logic for DocLayout.
"""
from typing import List, Dict, Any, Optional
from doclayout.core.models import Template, ElementType, BaseElement
from doclayout.core.geometry import mm_to_pt
from doclayout.engine.layout import LayoutEngine
from doclayout.engine.renderer_api import Renderer
from doclayout.adapters.reportlab.font_helper import FontHelper
from reportlab.pdfbase.pdfmetrics import stringWidth

# Constants for thermal paper and layout
THERMAL_PAPER_58MM = 58
THERMAL_PAPER_80MM = 80
THERMAL_PAPER_BOTTOM_MARGIN_MM = 10
PAGE_TOP_MARGIN_MM = 20  # Top margin for split elements on new pages
KV_BOX_PADDING_MM = 1.5
KV_BOX_TEXT_PADDING_MM = 0.5

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
        
        # Calculate dynamic heights for tables and text boxes, adjust element positions
        elements = self._adjust_dynamic_heights(elements)
        
        # Calculate page height
        page_w = template.page_size.width
        page_h = template.page_size.height
        
        # Check if this is thermal paper (dynamic height)
        is_thermal = page_w in [THERMAL_PAPER_58MM, THERMAL_PAPER_80MM]
        
        if is_thermal:
            # Thermal paper: calculate total height needed
            max_y = 0
            for elem in elements:
                max_y = max(max_y, elem.y + elem.height)
            actual_height = max_y + THERMAL_PAPER_BOTTOM_MARGIN_MM
            
            # Setup renderer for single page
            renderer.set_page_size(mm_to_pt(page_w), mm_to_pt(actual_height))
            renderer.initialize(output_path)
            renderer.start_page()
            
            for elem in elements:
                self._render_element(elem, renderer)
                
            renderer.end_page()
        else:
            # Fixed page size (A4, etc): use pagination with configured top margin
            top_margin = template.settings.page_top_margin_mm
            pages = self._paginate_elements(elements, page_h, top_margin)
            
            # Setup renderer
            renderer.set_page_size(mm_to_pt(page_w), mm_to_pt(page_h))
            renderer.initialize(output_path)
            
            # Render each page
            for page_elements in pages:
                renderer.start_page()
                for elem in page_elements:
                    self._render_element(elem, renderer)
                renderer.end_page()
        
        renderer.save(output_path)
        return output_path

    def _paginate_elements(self, elements: List[BaseElement], page_height: float, top_margin: float) -> List[List[BaseElement]]:
        """
        Split elements across multiple pages based on their absolute Y coordinates.
        Preserves multi-column layouts and absolute positioning.
        """
        import copy
        
        # Sort elements by Y to process top-to-bottom
        # This is important for split logic and queue processing
        sorted_elements = sorted(elements, key=lambda e: e.y)
        
        pages: List[List[BaseElement]] = []
        queue = [copy.deepcopy(e) for e in sorted_elements]
        
        while queue:
            elem = queue.pop(0)
            
            # Determine which page this element starts on
            # We use floor division to find page index (0, 1, 2...)
            start_page_idx = int(elem.y // page_height)
            
            # Ensure we have enough pages in the list
            while len(pages) <= start_page_idx:
                pages.append([])
            
            # Local Y on its start page
            local_y = elem.y % page_height
            
            # Check if element overflows the current page
            if local_y + elem.height > page_height:
                if elem.type == ElementType.TABLE:
                    # Split table
                    available = page_height - local_y
                    first, remaining = self._split_table(elem, available)
                    
                    if first:
                        first.y = local_y
                        pages[start_page_idx].append(first)
                    
                    if remaining:
                        # Move remaining part to start of next page
                        # We project it in absolute space so start_page_idx logic works next loop
                        remaining.y = (start_page_idx + 1) * page_height + top_margin
                        queue.insert(0, remaining)
                
                elif elem.type == ElementType.TEXT_BOX:
                    # Split textbox
                    available = page_height - local_y
                    first, remaining = self._split_textbox(elem, available)
                    
                    if first:
                        first.y = local_y
                        pages[start_page_idx].append(first)
                    
                    if remaining:
                        remaining.y = (start_page_idx + 1) * page_height + top_margin
                        queue.insert(0, remaining)
                
                else:
                    # For non-splittable elements, if most of it is on this page, keep it
                    # otherwise push to next page
                    if local_y > page_height * 0.9: # Very close to bottom
                        elem.y = (start_page_idx + 1) * page_height + top_margin
                        queue.insert(0, elem)
                    else:
                        elem.y = local_y
                        pages[start_page_idx].append(elem)
            else:
                # Fits entirely on its starting page
                elem.y = local_y
                pages[start_page_idx].append(elem)
        
        return pages if pages else [[]]

    def _split_table(self, elem: BaseElement, available_height: float):
        """
        Split a table element into two parts based on available height.
        
        Returns:
            (first_part, remaining_part) - Either can be None
        """
        import copy
        
        row_height = elem.props.get("row_height", 20.0)
        data = elem.props.get("data", [])
        
        if not data or available_height < row_height:
            # Not enough space for even one row, move entire table to next page
            return None, elem
        
        # Calculate how many rows fit
        rows_that_fit = int(available_height / row_height)
        
        if rows_that_fit >= len(data):
            # All rows fit
            return elem, None
        
        # Split the data
        first_part_data = data[:rows_that_fit]
        remaining_data = data[rows_that_fit:]
        
        # Create first part
        first_elem = copy.deepcopy(elem)
        first_elem.props["data"] = first_part_data
        first_elem.height = rows_that_fit * row_height
        
        # Create remaining part
        remaining_elem = copy.deepcopy(elem)
        remaining_elem.props["data"] = remaining_data
        remaining_elem.height = len(remaining_data) * row_height
        
        return first_elem, remaining_elem

    def _split_textbox(self, elem: BaseElement, available_height: float):
        """
        Split a text box element into two parts based on available height.
        
        Uses ReportLab's stringWidth for accurate text measurement.
        
        Returns:
            (first_part, remaining_part) - Either can be None
        """
        import copy
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from doclayout.adapters.reportlab.font_helper import FontHelper
        
        font_size = elem.props.get("font_size", 12)
        font_family = elem.props.get("font_family", "Helvetica")
        bold = elem.props.get("font_bold", False)
        italic = elem.props.get("font_italic", False)
        
        # Resolve font name
        try:
            font_name = FontHelper.resolve(font_family, bold, italic)
        except:
            font_name = "Helvetica"
        
        line_height_mm = font_size * 1.2 / 2.83465  # Convert pt to mm
        
        text = elem.props.get("text", "")
        if not text or available_height < line_height_mm:
            # Not enough space for even one line, move to next page
            return None, elem
        
        # Calculate how many lines fit in available space
        lines_that_fit = int(available_height / line_height_mm)
        
        # Convert width to points for stringWidth
        width_pt = mm_to_pt(elem.width)
        
        # Use simpleSplit for consistent wrapping
        from reportlab.lib.utils import simpleSplit
        
        # simpleSplit does NOT handle newlines, so we must split manually first
        paragraphs = text.split('\n')
        lines = []
        for p in paragraphs:
            if not p:
                lines.append('')  # Keep empty lines
                continue
            lines.extend(simpleSplit(p, font_name, font_size, width_pt))
        
        # Check if all lines fit
        if len(lines) <= lines_that_fit:
            # All text fits on current page
            # Update height to actual text height
            actual_height = len(lines) * line_height_mm
            elem.height = actual_height
            return elem, None
        
        # Split at lines_that_fit
        first_part_lines = lines[:lines_that_fit]
        remaining_lines = lines[lines_that_fit:]
        
        # Create first part - join with newlines to preserve line structure
        first_elem = copy.deepcopy(elem)
        first_elem.props["text"] = "\n".join(first_part_lines)
        first_elem.height = lines_that_fit * line_height_mm
        
        # Create remaining part - join with newlines to preserve line structure
        remaining_elem = copy.deepcopy(elem)
        remaining_elem.props["text"] = "\n".join(remaining_lines)
        remaining_elem.height = len(remaining_lines) * line_height_mm
        
        return first_elem, remaining_elem

    def _adjust_dynamic_heights(self, elements: List[BaseElement]) -> List[BaseElement]:
        """
        Calculate dynamic heights for tables and text boxes, and adjust positions of elements below them.
        Uses a strictly-below logic to allow columns to function correctly.
        """
        # 1. Pre-calculate original geometries to determine "below" relationship
        # We attach temporary attributes to elements to track state
        for elem in elements:
            elem._orig_y = elem.y
            elem._orig_height = elem.height
            elem._orig_bottom = elem.y + elem.height
            elem._y_offset = 0.0

        # 2. Identify growers and calculate their deltas
        # We sort by Y to process usually top-to-bottom, but with the O(N^2) push it matters less
        sorted_elements = sorted(elements, key=lambda e: e.y)
        
        for elem in sorted_elements:
            height_delta = 0.0
            
            if elem.type == ElementType.TABLE:
                data = elem.props.get("data", [])
                if data:
                    if "base_height" not in elem.props:
                        elem.props["base_height"] = elem.height
                    
                    base_height = elem.props["base_height"]
                    num_rows_editor = elem.props.get("num_rows_editor", 3)
                    # Avoid division by zero
                    if num_rows_editor <= 0: num_rows_editor = 1
                    
                    row_height = base_height / num_rows_editor
                    elem.props["row_height"] = row_height
                    
                    new_height = row_height * len(data)
                    height_delta = new_height - elem.height
                    elem.height = new_height
                    
            elif elem.type == ElementType.TEXT_BOX:
                if "base_height" not in elem.props:
                    elem.props["base_height"] = elem.height
                    
                text = elem.props.get("text", "")
                font_family = elem.props.get("font_family", "Helvetica")
                font_size = elem.props.get("font_size", 12)
                bold = elem.props.get("font_bold", False)
                italic = elem.props.get("font_italic", False)
                
                # Padding handling (1.0mm visual padding)
                padding_mm = 1.0 if (elem.props.get("show_border", False) or elem.props.get("background_color")) else 0.0
                content_width = elem.width - (padding_mm * 2)
                
                if content_width > 0:
                    text_height = self._calculate_text_height(text, font_family, font_size, content_width, bold, italic)
                    new_height = text_height + (padding_mm * 2)
                    
                    height_delta = new_height - elem.height
                    elem.height = new_height

            # 3. If this element grew (or shrank), push ONLY elements strictly below it
            if abs(height_delta) > 0.001:
                grower_bottom = elem._orig_bottom
                for victim in elements:
                    if victim is elem: continue
                    
                    # Check if victim starts at or below the grower's original bottom
                    # Use a small epsilon to handle alignment precision
                    if victim._orig_y >= (grower_bottom - 0.1):
                         victim._y_offset += height_delta
        
        # 4. Apply accumulated offsets
        for elem in elements:
            elem.y += elem._y_offset
            # Cleanup temporary attributes
            del elem._orig_y
            del elem._orig_height
            del elem._orig_bottom
            del elem._y_offset
            
        return elements

    def _calculate_text_height(self, text: str, font_family: str, font_size: float, 
                               width_mm: float, bold: bool = False, italic: bool = False) -> float:
        """
        Calculate the height needed to render text with wrapping.
        
        Args:
            text: The text content
            font_family: Font family name
            font_size: Font size in points
            width_mm: Available width in mm
            bold: Whether text is bold
            italic: Whether text is italic
            
        Returns:
            Height in mm needed to render the text
        """
        from reportlab.pdfbase.pdfmetrics import stringWidth
        from doclayout.adapters.reportlab.font_helper import FontHelper
        
        # Convert width to points for ReportLab
        width_pt = mm_to_pt(width_mm)
        
        # Resolve font name
        resolved_font = FontHelper.resolve(font_family, bold, italic)
        
        # Split text into words for wrapping calculation
        words = text.split()
        if not words:
            return font_size * 1.2 / 2.83465  # One line height in mm
        
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            try:
                line_width = stringWidth(test_line, resolved_font, font_size)
            except (KeyError, ValueError, AttributeError):
                # Fallback to Helvetica if font not found
                line_width = stringWidth(test_line, "Helvetica", font_size)
            
            if line_width <= width_pt:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Calculate total height
        line_height_pt = font_size * 1.2  # Standard line spacing
        total_height_pt = len(lines) * line_height_pt
        
        # Convert back to mm
        return total_height_pt / 2.83465




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
        elif elem.type == ElementType.TEXT_BOX:
            # Render background/border first
            bg_color = elem.props.get("background_color", None)
            show_border = elem.props.get("show_border", False)
            border_color = elem.props.get("border_color", "black") if show_border else None
            border_width = float(elem.props.get("border_width", 1.0))
            
            if bg_color or show_border:
                renderer.draw_rect(x, y, w, h, stroke_color=border_color, fill_color=bg_color, stroke_width=border_width)

            # Render text
            font_name = elem.props.get("font_family", "Helvetica")
            font_size = elem.props.get("font_size", 12)
            color = elem.props.get("color", "black")
            align = elem.props.get("text_align", "left")
            bold = elem.props.get("font_bold", False)
            italic = elem.props.get("font_italic", False)
            
            # Apply padding (visual only for now, reducing text width/pos)
            # Use 1.0mm padding consistent with Editor
            padding_pt = mm_to_pt(1.0) if (show_border or bg_color) else 0.0
            
            text_x = x + padding_pt
            text_w = w - (padding_pt * 2) if w else None
            
            renderer.draw_text(text_x, y + padding_pt, elem.props.get("text", ""), 
                               font_name=font_name, font_size=font_size, 
                               color=color, alignment=align, width=text_w,
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
                rl_font = FontHelper.resolve(font_family, bold, italic)
                key_txt = props.get("key_text", "Label:")
                try:
                    txt_w = stringWidth(key_txt, rl_font, font_size)
                except (KeyError, ValueError, AttributeError):
                    # Fallback to Helvetica if font not found or invalid
                    txt_w = stringWidth(key_txt, "Helvetica", font_size)
                
                # Add padding for better visual spacing
                split = txt_w + mm_to_pt(KV_BOX_PADDING_MM)
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
            renderer.draw_text(x + mm_to_pt(KV_BOX_TEXT_PADDING_MM), y + v_offset, props.get("key_text", "Label:"), 
                               font_name=font_family, font_size=font_size, color=color,
                               width=split - mm_to_pt(KV_BOX_TEXT_PADDING_MM), bold=bold, italic=italic, wrap=True, auto_scale=True)
            
            # Value Label
            renderer.draw_text(x + split + mm_to_pt(KV_BOX_TEXT_PADDING_MM), y + v_offset, props.get("text", "[Value]"), 
                               font_name=font_family, font_size=font_size, color=color,
                               width=w - split - mm_to_pt(KV_BOX_TEXT_PADDING_MM), bold=bold, italic=italic, wrap=True, auto_scale=True)
                               
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
            # Also pass new style props
            theme = elem.props.get("theme", "Grid")
            header_bg = elem.props.get("header_bg_color", None)
            stroke_col = elem.props.get("stroke_color", "black")
            
            renderer.draw_table(x, y, w, h, data, 
                                font_size=elem.props.get("font_size", 10),
                                theme=theme,
                                fill_color_header=header_bg,
                                stroke_color=stroke_col)
