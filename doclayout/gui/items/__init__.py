"""
GUI items package.
"""

from .base import BaseEditorItem
from .rect import RectEditorItem
from .text import TextEditorItem
from .textbox import TextBoxEditorItem
from .image import ImageEditorItem
from .line import LineEditorItem, LineHandle
from .kvbox import KVBoxEditorItem
from .table import TableEditorItem

def get_item_for_model(model):
    """
    Factory function to create the appropriate EditorItem for a given model.
    
    Maps BaseElement models to their corresponding QGraphicsItem implementations
    based on the element type.
    
    Args:
        model: A BaseElement or BlockInstance model object. Must have a 'type'
            attribute matching one of the ElementType enum values.
    
    Returns:
        QGraphicsItem subclass instance corresponding to the model type,
        or None if the model type is not recognized or model has no type attribute.
    
    Example:
        >>> from doclayout.core.models import BaseElement, ElementType
        >>> model = BaseElement(type=ElementType.TEXT, x=10, y=20)
        >>> item = get_item_for_model(model)
        >>> isinstance(item, TextEditorItem)
        True
    """
    from doclayout.core.models import ElementType
    item = None
    if model.type == ElementType.RECT:
        item = RectEditorItem(model)
    elif model.type == ElementType.TEXT:
        item = TextEditorItem(model)
    elif model.type == ElementType.TEXT_BOX:
        item = TextBoxEditorItem(model)
    elif model.type == ElementType.IMAGE:
        item = ImageEditorItem(model)
    elif model.type == ElementType.LINE:
        item = LineEditorItem(model)
    elif model.type == ElementType.KV_BOX:
        item = KVBoxEditorItem(model)
    elif model.type == ElementType.CONTAINER:
        from .container import ContainerEditorItem
        item = ContainerEditorItem(model)
    elif model.type == ElementType.TABLE:
        item = TableEditorItem(model)
    
    if item and hasattr(model, 'z'):
        item.setZValue(model.z)
    
    return item
