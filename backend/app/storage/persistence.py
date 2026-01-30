"""
CarbonChain MVP - Service Persistence Helpers

Provides decorators and utilities for automatic persistence.
"""

from functools import wraps
from pathlib import Path
from typing import Callable, Any

from backend.app.storage import atomic_write_json, read_json, uuid_to_str, str_to_uuid


def persist_on_mutation(
    storage_file: Path,
    get_data_func: Callable[[], dict],
    uuid_fields: list[str] = None
):
    """
    Decorator to persist data after a mutation function completes.
    
    Args:
        storage_file: Path to the JSON storage file.
        get_data_func: Function that returns the data dict to persist.
        uuid_fields: List of field names that should be converted to UUIDs.
    
    Usage:
        @persist_on_mutation(STORAGE_FILE, lambda: my_db)
        def my_mutation_function(...):
            # Modify my_db
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Persist after mutation
            try:
                data = get_data_func()
                # Convert UUIDs to strings for JSON serialization
                serializable_data = uuid_to_str(data)
                atomic_write_json(storage_file, serializable_data)
            except Exception as e:
                print(f"[PERSISTENCE ERROR] Failed to persist after {func.__name__}: {e}")
                # Don't fail the mutation if persistence fails
            
            return result
        return wrapper
    return decorator


def load_from_disk(
    storage_file: Path,
    target_dict: dict,
    uuid_fields: list[str] = None
) -> None:
    """
    Load data from disk into a target dictionary.
    
    Args:
        storage_file: Path to the JSON storage file.
        target_dict: Dictionary to populate with loaded data.
        uuid_fields: List of field names that should be converted to UUIDs.
    """
    if not storage_file.exists():
        print(f"[STORAGE] {storage_file} does not exist. Starting with empty data.")
        return
    
    try:
        loaded_data = read_json(storage_file, default={})
        
        # Convert UUID strings back to UUID objects
        if uuid_fields:
            loaded_data = str_to_uuid(loaded_data, uuid_fields)
        
        # Update target dict
        target_dict.clear()
        target_dict.update(loaded_data)
        
        print(f"[STORAGE] Loaded {len(target_dict)} items from {storage_file}")
    except Exception as e:
        print(f"[STORAGE ERROR] Failed to load from {storage_file}: {e}")
        # Continue with empty dict on error


