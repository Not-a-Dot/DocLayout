"""
Font resolution utilities for ReportLab renderer.
"""

class FontHelper:
    """
    Handles mapping from generic font names to ReportLab's standard fonts.
    """
    FONT_MAPPING = {
        "Arial": "Helvetica",
        "Helvetica": "Helvetica",
        "Times New Roman": "Times-Roman",
        "Times": "Times-Roman",
        "Courier New": "Courier",
        "Courier": "Courier"
    }

    @staticmethod
    def resolve(font_name: str, bold: bool = False, italic: bool = False) -> str:
        """
        Map a font name and style to a ReportLab standard font name.

        Args:
            font_name (str): The requested font family.
            bold (bool): If true, use bold version.
            italic (bool): If true, use oblique/italic version.

        Returns:
            str: The ReportLab font identifier.
        """
        base = FontHelper.FONT_MAPPING.get(font_name, "Helvetica")
        
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
