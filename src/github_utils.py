import os
import sys
from typing import Optional

def get_input(name: str, required: bool = True, default: Optional[str] = None) -> Optional[str]:
    """Gets the action input value from environment variables."""
    env_name = f"INPUT_{name.upper()}"
    value = os.environ.get(env_name)
    
    if (value is None or value == "") and required:
        set_failed(f"Input required and not supplied: {name}")
    
    return value if value is not None else default

def set_failed(message: str):
    """Sets the failure message for GitHub Actions and terminates the script."""
    print(f"::error::{message}")
    sys.exit(1)

def info(message: str):
    """Sets an informational message for GitHub Actions."""
    print(f"::notice::{message}")
