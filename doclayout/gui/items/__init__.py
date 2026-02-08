"""
GUI items package.
"""

from .base import BaseEditorItem
from .rect import RectEditorItem
from .text import TextEditorItem
from .image import ImageEditorItem
from .line import LineEditorItem, LineHandle
from .kvbox import KVBoxEditorItem
from .table import TableEditorItem

def get_item_for_model(model):
    """Factory to create UI items from models."""
    from doclayout.core.models import ElementType
    if model.type == ElementType.RECT:
        return RectEditorItem(model)
    elif model.type == ElementType.TEXT:
        return TextEditorItem(model)
    elif model.type == ElementType.IMAGE:
        return ImageEditorItem(model)
    elif model.type == ElementType.LINE:
        return LineEditorItem(model)
    elif model.type == ElementType.KV_BOX:
        return KVBoxEditorItem(model)
    elif model.type == ElementType.CONTAINER:
        from .container import ContainerEditorItem
        return ContainerEditorItem(model)
    elif model.type == ElementType.TABLE:
        return TableEditorItem(model)
    return None
