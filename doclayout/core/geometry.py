"""
Geometry utilities for unit conversions and coordinate management.
"""

MM_TO_PT = 2.83465
PT_TO_MM = 1.0 / MM_TO_PT

def mm_to_pt(mm: float) -> float:
    """
    Convert millimeters to points.

    Args:
        mm (float): Value in millimeters.

    Returns:
        float: Value in points.
    """
    return mm * MM_TO_PT

def pt_to_mm(pt: float) -> float:
    """
    Convert points to millimeters.

    Args:
        pt (float): Value in points.

    Returns:
        float: Value in millimeters.
    """
    return pt / MM_TO_PT
