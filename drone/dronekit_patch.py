#!/usr/bin/env python3
"""
DroneKit patcher to fix compatibility with Python 3.10+

This script needs to be run before importing DroneKit and it will patch
the DroneKit package directly to use collections.abc instead of collections
for MutableMapping.
"""

import os
import sys
import re
import site
from pathlib import Path

def patch_dronekit_files():
    """
    Patch DroneKit Python files to use collections.abc instead of collections
    for MutableMapping.
    """
    # Find DroneKit install path
    try:
        import dronekit
        print("Error: DroneKit already imported. This script must be run before importing DroneKit.")
        return False
    except AttributeError:
        # This is the error we're trying to fix
        pass
    
    # Try to find dronekit in site-packages
    dronekit_paths = []
    
    # Check standard site-packages locations
    for site_dir in site.getsitepackages() + [site.getusersitepackages()]:
        potential_path = os.path.join(site_dir, "dronekit")
        if os.path.exists(potential_path):
            dronekit_paths.append(potential_path)
    
    # Also check current directory and its parent
    for relative_path in ["dronekit", "../dronekit", "lib/dronekit"]:
        if os.path.exists(relative_path):
            dronekit_paths.append(os.path.abspath(relative_path))
    
    if not dronekit_paths:
        print("Could not find DroneKit installation. Please install it with pip install dronekit")
        return False
    
    patched_files = 0
    
    for dronekit_path in dronekit_paths:
        print(f"Found DroneKit at: {dronekit_path}")
        
        # Find all Python files
        for root, _, files in os.walk(dronekit_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    
                    # Read the file content
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Check if the file uses collections.MutableMapping
                    if "collections.MutableMapping" in content or "collections import MutableMapping" in content:
                        # Replace direct imports
                        modified_content = re.sub(
                            r'from collections import (\w+, )*MutableMapping(, \w+)*', 
                            r'from collections.abc import MutableMapping', 
                            content
                        )
                        
                        # Replace usage in code
                        modified_content = re.sub(
                            r'collections\.MutableMapping', 
                            r'collections.abc.MutableMapping', 
                            modified_content
                        )
                        
                        # Write the modified content back to the file
                        with open(file_path, 'w') as f:
                            f.write(modified_content)
                        
                        print(f"Patched: {file_path}")
                        patched_files += 1
    
    if patched_files > 0:
        print(f"Successfully patched {patched_files} DroneKit files to use collections.abc.MutableMapping")
        return True
    else:
        print("No DroneKit files needed patching or files could not be found.")
        return False

if __name__ == "__main__":
    # Only apply patch for Python 3.10+
    if sys.version_info >= (3, 10):
        success = patch_dronekit_files()
        if success:
            print("DroneKit patched successfully for Python 3.10+ compatibility")
        else:
            print("Failed to patch DroneKit")
    else:
        print(f"Python version {sys.version_info.major}.{sys.version_info.minor} does not require patching") 