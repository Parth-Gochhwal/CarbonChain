"""
CarbonChain MVP - JSON Storage Utilities

Provides atomic file operations for JSON persistence.
Uses write-then-rename pattern for atomicity.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

# Storage directory
STORAGE_DIR = Path("backend/app/storage")
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def atomic_write_json(filepath: Path, data: Any) -> None:
    """
    Atomically write JSON data to a file.
    
    Uses write-then-rename pattern to ensure atomicity:
    1. Write to temporary file
    2. Rename temp file to target (atomic on most filesystems)
    
    Args:
        filepath: Path to the JSON file.
        data: Data to serialize (must be JSON-serializable).
    """
    # Ensure parent directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file first
    temp_path = filepath.with_suffix(filepath.suffix + '.tmp')
    
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        
        # Atomic rename (replaces existing file)
        temp_path.replace(filepath)
    except Exception as e:
        # Clean up temp file on error
        if temp_path.exists():
            temp_path.unlink()
        raise e


def read_json(filepath: Path, default: Any = None) -> Any:
    """
    Read JSON data from a file.
    
    Args:
        filepath: Path to the JSON file.
        default: Default value if file doesn't exist.
        
    Returns:
        Parsed JSON data, or default if file doesn't exist.
    """
    if not filepath.exists():
        return default if default is not None else {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If file is corrupted, return default
        print(f"[STORAGE WARNING] Failed to read {filepath}: {e}. Using default.")
        return default if default is not None else {}


def uuid_to_str(obj: Any) -> Any:
    """
    Recursively convert UUID objects to strings in a data structure.
    
    Args:
        obj: Object that may contain UUIDs.
        
    Returns:
        Object with UUIDs converted to strings.
    """
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: uuid_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [uuid_to_str(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(uuid_to_str(item) for item in obj)
    else:
        return obj


def str_to_uuid(obj: Any, uuid_fields: Optional[list[str]] = None) -> Any:
    """
    Recursively convert string UUIDs back to UUID objects.
    
    Args:
        obj: Object that may contain UUID strings.
        uuid_fields: List of field names that should be converted to UUIDs.
        
    Returns:
        Object with UUID strings converted to UUID objects.
    """
    from uuid import UUID
    
    if uuid_fields is None:
        uuid_fields = ['id', 'claim_id', 'verification_id', 'token_id', 'credit_id', 'evidence_id', 'review_id']
    
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in uuid_fields and isinstance(v, str):
                try:
                    result[k] = UUID(v)
                except (ValueError, AttributeError):
                    result[k] = v
            elif k == 'id' and isinstance(v, str):
                # Also handle top-level 'id' fields
                try:
                    result[k] = UUID(v)
                except (ValueError, AttributeError):
                    result[k] = v
            else:
                result[k] = str_to_uuid(v, uuid_fields)
        return result
    elif isinstance(obj, list):
        return [str_to_uuid(item, uuid_fields) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(str_to_uuid(item, uuid_fields) for item in obj)
    else:
        return obj
