"""
Verification script for the DocLayout Core Pipeline.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from doclayout.core.models import BlockBase, Template, BaseElement, ElementType, BlockInstance, PageSize
from doclayout.engine.layout import LayoutEngine
from doclayout.adapters.reportlab_adapter import ReportLabRenderer
from doclayout.core.geometry import mm_to_pt

def main():
    print("Initializing Block...")
    # 1. Define a Block (e.g., a Header)
    header_block = BlockBase(
        id="block_header",
        name="Standard Header",
        width=210,
        height=30,
        elements=[
            BaseElement(
                type=ElementType.RECT,
                x=0, y=0, width=210, height=30,
                props={"fill_color": "#eeeeee", "stroke_color": "black"}
            ),
            BaseElement(
                type=ElementType.TEXT,
                x=10, y=20, width=100, height=10, 
                props={"text": "Company: {{company_name}}", "font_size": 14}
            )
        ]
    )

    print("Initializing Template...")
    # 2. Define a Template that uses the Block
    template = Template(
        name="Invoice Template",
        page_size=PageSize(width=210, height=297), # A4
        items=[
            # Instance of the header block
            BlockInstance(
                block_id="block_header",
                x=0, y=267, # Top of page (assuming y=0 at bottom for now, let's see)
                data={"company_name": "ACME Corp"}
            ),
            # A direct line element
            BaseElement(
                type=ElementType.LINE,
                x=10, y=250, width=190, height=0, # Line from (10, 250) to (200, 250)
                props={"x2": 200, "y2": 250, "stroke_width": 2} # Wait, BaseElement needs x2/y2 props for lines?
                # BaseElement defines x, y, width, height. 
                # For Line, we might interpret width/height as dx/dy or use props. 
                # Let's verify ReportLabAdapter implementation.
                # draw_line(x1, y1, x2, y2).
                # The LayoutEngine flattens it.
                # If BaseElement is generic, we need to decide how to represent a line.
                # Usually x,y is separate from x2,y2. 
                # Let's use props for x2, y2 relative to x,y or absolute?
                # My models.py BaseElement has x, y, width, height.
                # A line is usually defined by start and end. 
                # Let's adopt convention: x,y is start. x+width, y+height is end? 
                # Or use props.
            )
        ]
    )
    # Fix for Line: Let's assume for this test that we update models later or use props.
    # The adapter: draw_line(x1, y1, x2, y2).
    # Does LayoutEngine modify props? No.
    # So the renderer needs to know how to interpret the element.
    # Let's check ReportLabAdapter.
    # It takes x1, y1, x2, y2.
    # But it is called by... who?
    # We haven't implemented the loop that CALLS the renderer yet! 
    # Valid point! The LayoutEngine produces a list of BaseElement.
    # We need a "RenderEngine" or "Driver" that takes list of elements and calls renderer commands.
    
    print("Compiling Layout...")
    # 3. Layout Engine
    block_provider = {header_block.id: header_block}
    engine = LayoutEngine(block_provider)
    flat_elements = engine.compile(template)

    print(f"Generated {len(flat_elements)} elements.")

    # 4. Rendering
    print("Rendering to PDF...")
    renderer = ReportLabRenderer()
    renderer.set_page_size(mm_to_pt(template.page_size.width), mm_to_pt(template.page_size.height))
    renderer.initialize("output.pdf")
    renderer.start_page()

    for elem in flat_elements:
        # Convert mm to pt
        x_pt = mm_to_pt(elem.x)
        y_pt = mm_to_pt(elem.y)
        w_pt = mm_to_pt(elem.width)
        h_pt = mm_to_pt(elem.height)
        
        if elem.type == ElementType.RECT:
            renderer.draw_rect(
                x_pt, y_pt, w_pt, h_pt, 
                stroke_color=elem.props.get("stroke_color"),
                fill_color=elem.props.get("fill_color")
            )
        elif elem.type == ElementType.TEXT:
            # For text, Y is usually baseline.
            renderer.draw_text(
                x_pt, y_pt, 
                text=elem.props.get("text", ""),
                font_size=elem.props.get("font_size", 12)
            )
        elif elem.type == ElementType.LINE:
            # Special handling for line props
            x2 = elem.props.get("x2", elem.x + elem.width) # Fallback
            y2 = elem.props.get("y2", elem.y + elem.height)
            renderer.draw_line(
                x_pt, y_pt, mm_to_pt(x2), mm_to_pt(y2),
                stroke_width=elem.props.get("stroke_width", 1)
            )

    renderer.end_page()
    renderer.save("output.pdf")
    print("Done. Saved to output.pdf")

if __name__ == "__main__":
    main()
