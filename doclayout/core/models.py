"""
Core data models for the DocLayout application.
Defines the structure for Elements, Blocks, and Templates using Pydantic.
"""

from enum import Enum
from typing import List, Optional, Union, Any, Dict
from uuid import uuid4
from pydantic import BaseModel, Field

def generate_id() -> str:
    """Generate a unique ID for elements."""
    return str(uuid4())

class ElementType(str, Enum):
    """Enumeration of supported element types."""
    RECT = "rect"
    TEXT = "text"
    LINE = "line"
    IMAGE = "image"
    KV_BOX = "kv_box"
    CONTAINER = "container"
    TABLE = "table"

class VariableBinding(BaseModel):
    """Mapping between a global variable and an element property."""
    variable_name: str
    target_property: str

class BaseElement(BaseModel):
    """
    Base class for all visual elements.
    
    Attributes:
        id (str): Unique identifier.
        type (ElementType): Type of the element.
        x (float): X coordinate in mm.
        y (float): Y coordinate in mm.
        width (float): Width in mm.
        height (float): Height in mm.
        props (Dict[str, Any]): Additional properties (color, font, etc.).
        bindings (List[VariableBinding]): Data bindings for dynamic content.
    """
    id: str = Field(default_factory=generate_id)
    type: ElementType
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    props: Dict[str, Any] = Field(default_factory=dict)
    bindings: List[VariableBinding] = Field(default_factory=list)
    children: List['BaseElement'] = Field(default_factory=list)
    name: Optional[str] = None

    @property
    def lock_children(self) -> bool:
        return self.props.get("lock_children", False)

    @property
    def lock_position(self) -> bool:
        return self.props.get("lock_position", False)

    @property
    def lock_geometry(self) -> bool:
        return self.props.get("lock_geometry", False)

    @property
    def lock_selection(self) -> bool:
        return self.props.get("lock_selection", False)

class BlockBase(BaseModel):
    """
    Base definition of a reusable Block.
    
    Attributes:
        id (str): Unique identifier.
        name (str): Human-readable name of the block.
        width (float): Width of the block canvas in mm.
        height (float): Height of the block canvas in mm.
        elements (List[BaseElement]): List of elements inside the block.
    """
    id: str = Field(default_factory=generate_id)
    name: str
    width: float
    height: float
    elements: List[BaseElement] = Field(default_factory=list)

class BlockInstance(BaseModel):
    """
    An instance of a Block placed within a Template.
    
    Attributes:
        id (str): Unique instance identifier.
        block_id (str): Reference to the original BlockBase definition.
        x (float): X coordinate in mm (relative to page).
        y (float): Y coordinate in mm (relative to page).
        data (Dict[str, Any]): Data to be substituted into placeholders.
    """
    id: str = Field(default_factory=generate_id)
    block_id: str
    x: float = 0.0
    y: float = 0.0
    data: Dict[str, Any] = Field(default_factory=dict)

class PageSize(BaseModel):
    """
    Page dimensions.
    
    Attributes:
        width (float): Width in mm.
        height (float): Height in mm.
    """
    width: float
    height: float

# Current application-level version of the document template format.
# Increment this manally when making breaking changes to the model.
CURRENT_VERSION = "0.0.2"

class Template(BaseModel):
    """
    A document template consisting of a page size and list of items.
    
    Attributes:
        id (str): Unique identifier.
        name (str): Template name.
        version (str): The format version this file was saved with.
        page_size (PageSize): Dimensions of the page.
        items (List[Union[BaseElement, BlockInstance]]): List of elements or block instances.
    """
    id: str = Field(default_factory=generate_id)
    name: str
    version: str = Field(default=CURRENT_VERSION)
    page_size: PageSize
    items: List[Union[BaseElement, BlockInstance]] = Field(default_factory=list)

# Resolve forward references for recursive models
BaseElement.model_rebuild()
