"""
Input/Output operations for loading and saving templates and blocks.
"""

import json
from pathlib import Path
from typing import Union, Dict, Any
from .models import Template, BlockBase

def _increment_version(version: str) -> str:
    """
    Increment version string (x.y.z) following requested logic:
    0.0.9 -> 0.1.0
    0.9.9 -> 1.0.0
    """
    try:
        parts = [int(p) for p in version.split('.')]
        if len(parts) != 3:
            return "0.0.1" # Fallback
            
        major, minor, patch = parts
        
        patch += 1
        if patch > 9:
            patch = 0
            minor += 1
            if minor > 9:
                minor = 0
                major += 1
                
        return f"{major}.{minor}.{patch}"
    except (ValueError, AttributeError):
        return "0.0.1"

def _migrate_v001_to_v002(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate from 0.0.1 (flat) to 0.0.2 (hierarchical).
    Attempts to nest items that are visually inside containers.
    """
    items = data.get("items", [])
    if not items:
        return data
        
    containers = [i for i in items if i.get("type") == "container"]
    others = [i for i in items if i.get("type") != "container"]
    
    if not containers:
        return data
        
    # Sort containers by area (smallest first) to handle nested containers correctly
    containers.sort(key=lambda c: c.get("width", 0) * c.get("height", 0))
    
    # Track items already assigned to a parent to avoid duplicates or cycles
    assigned_ids = set()
    
    for item in others:
        ix, iy = item.get("x", 0), item.get("y", 0)
        iw, ih = item.get("width", 0), item.get("height", 0)
        
        for container in containers:
            cx, cy = container.get("x", 0), container.get("y", 0)
            cw, ch = container.get("width", 0), container.get("height", 0)
            
            if ix >= cx and iy >= cy and (ix + iw) <= (cx + cw) and (iy + ih) <= (cy + ch):
                if "children" not in container:
                    container["children"] = []
                
                item["x"] = ix - cx
                item["y"] = iy - cy
                container["children"].append(item)
                assigned_ids.add(item.get("id"))
                break 
    
    # Filter out assigned items from top level
    new_top_level = [i for i in others if i.get("id") not in assigned_ids]
            
    # Also handle container-in-container nesting
    final_top_level = []
    container_assigned_ids = set()
    
    # Sort containers by area DESCENDING to find parents for smaller containers
    containers.sort(key=lambda c: c.get("width", 0) * c.get("height", 0), reverse=True)
    
    # We'll build a tree. For each container, find the smallest parent it fits in.
    # Actually, sorting DESCENDING means we find the LARGEST parent first? No, we want the SMALLEST parent.
    # So sorting ASCENDING is better, but we need to check LARGER ones.
    containers.sort(key=lambda c: c.get("width", 0) * c.get("height", 0))

    for i, c in enumerate(containers):
        ix, iy = c.get("x", 0), c.get("y", 0)
        iw, ih = c.get("width", 0), c.get("height", 0)
        cid = c.get("id")
        
        parent_found = False
        # Look for a parent in the rest of the containers (which are larger or equal)
        for j, other_c in enumerate(containers):
            if i == j: continue
            if other_c.get("id") == cid: continue # Should not happen with unique IDs
            
            cx, cy = other_c.get("x", 0), other_c.get("y", 0)
            cw, ch = other_c.get("width", 0), other_c.get("height", 0)
            
            if ix >= cx and iy >= cy and (ix + iw) <= (cx + cw) and (iy + ih) <= (cy + ch):
                # Ensure we don't create a cycle (only nest in larger or later-in-list)
                # If areas are equal, only nest if j > i
                if (cw * ch > iw * ih) or (cw * ch == iw * ih and j > i):
                    if "children" not in other_c:
                        other_c["children"] = []
                    
                    c["x"] = ix - cx
                    c["y"] = iy - cy
                    other_c["children"].append(c)
                    container_assigned_ids.add(cid)
                    parent_found = True
                    break
        
        if not parent_found:
            final_top_level.append(c)
            
    data["items"] = final_top_level + new_top_level
    data["version"] = "0.0.2"
    return data

def _migrate_template_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy template data to current version.
    """
    version = data.get("version", "0.0.0")
    
    if version in ("0.0.0", "0.0.1"):
        data = _migrate_v001_to_v002(data)
        version = "0.0.2"
        
    # Add more migration steps here as version increases
        
    return data

def save_to_json(obj: Union[Template, BlockBase], file_path: str) -> None:
    """
    Save a Template or BlockBase object to a JSON file.
    Increments version automatically for Templates.

    Args:
        obj (Union[Template, BlockBase]): The object to save.
        file_path (str): The path to the output file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure version is updated to current app version upon save
    if isinstance(obj, Template):
        from .models import CURRENT_VERSION
        obj.version = CURRENT_VERSION
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(obj.model_dump_json(indent=2))

def load_template(file_path: str) -> Template:
    """
    Load a Template from a JSON file.
    Handles migration of legacy files.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        Template: The loaded template object.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValidationError: If the JSON structure is invalid.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Migrate data before validating
    data = _migrate_template_data(data)
    
    return Template.model_validate(data)

def load_block(file_path: str) -> BlockBase:
    """
    Load a BlockBase from a JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
    return BlockBase.model_validate_json(data)

def load_from_json(file_path: str) -> dict:
    """
    Load a JSON file into a dictionary.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
