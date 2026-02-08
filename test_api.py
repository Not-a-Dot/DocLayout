
import os
from doclayout.api import generate_pdf
from doclayout.core.models import Template, PageSize, BaseElement, ElementType
from doclayout.core.io import save_to_json

def test_api():
    # 1. Create a dummy template
    template = Template(
        name="API Test Template",
        page_size=PageSize(width=210, height=297),
        items=[
            BaseElement(
                type=ElementType.TEXT,
                x=50, y=50, width=100, height=10,
                props={"text": "Client: {{ client }}", "variable_name": "client", "font_size": 20, "color": "blue"}
            ),
            BaseElement(
                type=ElementType.RECT,
                x=50, y=70, width=40, height=40,
                props={"fill_color": "green", "bg_type": "solid", "opacity": 128}
            )
        ]
    )
    
    template_path = "test_template.json"
    save_to_json(template, template_path)
    print(f"Template saved to {template_path}")
    
    # 2. Generate PDF with data
    data = {"client": "Carlos (API Verified)"}
    output_path = "api_output.pdf"
    
    try:
        generate_pdf(template_path, data, output_path)
        print(f"PDF generated successfully at {output_path}")
    except Exception as e:
        print(f"API Error: {e}")

if __name__ == "__main__":
    import traceback
    try:
        test_api()
    except Exception:
        traceback.print_exc()
