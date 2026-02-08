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
        Split elements across multiple pages, dividing large elements when necessary.
        
        Args:
            elements: List of elements to paginate
            page_height: Height of each page in mm
            top_margin: Top margin for split elements on new pages in mm
            
        Returns:
            List of pages, each containing list of elements
        """
        import copy
        
        pages = [[]]
        current_page = 0
        current_y = 0.0  # Current Y position on current page
        
        for elem in elements:
            elem_copy = copy.deepcopy(elem)
            
            # Calculate available space on current page
            available_height = page_height - current_y
            
            # Check if element fits entirely on current page
            if elem_copy.height <= available_height:
                # Element fits, add it to current page
                elem_copy.y = current_y
                pages[current_page].append(elem_copy)
                current_y += elem_copy.height
            else:
                # Element doesn't fit, need to split
                if elem_copy.type == ElementType.TABLE:
                    # Split table by rows
                    remaining_elem = elem_copy
                    
                    while remaining_elem is not None:
                        # Calculate how much space is available
                        available = page_height - current_y
                        
                        # Split the table
                        first_part, remaining_part = self._split_table(remaining_elem, available)
                        
                        if first_part is not None:
                            first_part.y = current_y
                            pages[current_page].append(first_part)
                        
                        # Move to next page for remaining part
                        if remaining_part is not None:
                            current_page += 1
                            pages.append([])
                            current_y = top_margin  # Start with configured top margin
                            remaining_elem = remaining_part
                        else:
                            remaining_elem = None
                            current_y = page_height  # Page is full
                            
                elif elem_copy.type == ElementType.TEXT_BOX:
                    # Split text box by content
                    remaining_elem = elem_copy
                    
                    while remaining_elem is not None:
                        available = page_height - current_y
                        
                        # Split the text box
                        first_part, remaining_part = self._split_textbox(remaining_elem, available)
                        
                        if first_part is not None:
                            first_part.y = current_y
                            pages[current_page].append(first_part)
                        
                        # Move to next page for remaining part
                        if remaining_part is not None:
                            current_page += 1
                            pages.append([])
                            current_y = top_margin  # Start with configured top margin
                            remaining_elem = remaining_part
                        else:
                            remaining_elem = None
                            current_y = page_height
                else:
                    # For other elements, move to next page
                    current_page += 1
                    pages.append([])
                    current_y = 0.0
                    elem_copy.y = current_y
                    pages[current_page].append(elem_copy)
                    current_y += elem_copy.height
        
        return pages

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
        
        font_size = elem.props.get("font_size", 12)
        font_name = elem.props.get("font_family", "Helvetica")
        line_height_mm = font_size * 1.2 / 2.83465  # Convert pt to mm
        
        text = elem.props.get("text", "")
        if not text or available_height < line_height_mm:
            # Not enough space for even one line, move to next page
            return None, elem
        
        # Calculate how many lines fit
        lines_that_fit = int(available_height / line_height_mm)
        
        # Convert width to points for stringWidth
        width_pt = mm_to_pt(elem.width)
        
        # Split text into lines that fit within width
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word exceeds width
            test_line = " ".join(current_line + [word])
            text_width = stringWidth(test_line, font_name, font_size)
            
            if text_width <= width_pt:
                current_line.append(word)
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        # Add remaining words as last line
        if current_line:
            lines.append(" ".join(current_line))
        
        # Check if all lines fit
        if len(lines) <= lines_that_fit:
            # All text fits on current page
            return elem, None
        
        # Split at lines_that_fit
        first_part_lines = lines[:lines_that_fit]
        remaining_lines = lines[lines_that_fit:]
        
        # Create first part
        first_elem = copy.deepcopy(elem)
        first_elem.props["text"] = " ".join(first_part_lines)
        first_elem.height = lines_that_fit * line_height_mm
        
        # Create remaining part
        remaining_elem = copy.deepcopy(elem)
        remaining_elem.props["text"] = " ".join(remaining_lines)
        remaining_elem.height = len(remaining_lines) * line_height_mm
        
        return first_elem, remaining_elem

    def _adjust_dynamic_heights(self, elements: List[BaseElement]) -> List[BaseElement]:
        """
        Calculate dynamic heights for tables and text boxes, and adjust positions of elements below them.
        """
        # Sort elements by Y position to process top-to-bottom
        sorted_elements = sorted(elements, key=lambda e: e.y)
        
        cumulative_offset = 0.0
        
        for elem in sorted_elements:
            # Apply cumulative offset from elements above
            elem.y += cumulative_offset
            
            if elem.type == ElementType.TABLE:
                data = elem.props.get("data", [])
                if not data:
                    continue
                
                # Calculate base row height from editor dimensions
                # Store original height as base_height if not already stored
                if "base_height" not in elem.props:
                    elem.props["base_height"] = elem.height
                
                base_height = elem.props["base_height"]
                num_rows_data = len(data)
                
                # Calculate row height from editor (assuming editor had at least 1 row)
                # Default to 3 rows if not specified
                num_rows_editor = elem.props.get("num_rows_editor", 3)
                row_height = base_height / num_rows_editor
                
                # Store row height for renderer
                elem.props["row_height"] = row_height
                
                # Calculate new height based on actual data
                new_height = row_height * num_rows_data
                height_delta = new_height - elem.height
                
                # Update table height
                elem.height = new_height
                
                # Add delta to cumulative offset for elements below
                cumulative_offset += height_delta
                
            elif elem.type == ElementType.TEXT_BOX:
                text = elem.props.get("text", "")
                if not text:
                    continue
                
                # Calculate base height from editor
                if "base_height" not in elem.props:
                    elem.props["base_height"] = elem.height
                
                base_height = elem.props["base_height"]
                
                # Calculate text height based on content
                font_family = elem.props.get("font_family", "Helvetica")
                font_size = elem.props.get("font_size", 12)
                bold = elem.props.get("font_bold", False)
                italic = elem.props.get("font_italic", False)
                width_mm = elem.width
                
                # Calculate actual text height
                text_height_mm = self._calculate_text_height(
                    text, font_family, font_size, width_mm, bold, italic
                )
                
                # Only grow if text needs more space than base_height
                new_height = max(base_height, text_height_mm)
                height_delta = new_height - elem.height
                
                # Update text box height
                elem.height = new_height
                
                # Add delta to cumulative offset for elements below
                cumulative_offset += height_delta
        
        return sorted_elements

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
            # TEXT_BOX renders exactly like TEXT but with dynamic height
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
            if data:
                font_size = elem.props.get("font_size", 10)
                show_header = elem.props.get("show_header", True)
                
                # If show_header is True, we highlight the first row
                fill_h = "#f0f0f0" if show_header else None
                
                renderer.draw_table(x, y, w, h, data, 
                                   font_size=font_size,
                                   fill_color_header=fill_h)
            pass
