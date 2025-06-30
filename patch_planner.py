"""
Patch to fix material ID type mismatch in planner
"""

import sys
from pathlib import Path

# Read the planner file
planner_file = Path("engine/planner.py")
content = planner_file.read_text(encoding='utf-8')

# Find and replace the return statement in _explode_with_style_yarn_bom
old_code = """            return yarn_requirements"""
new_code = """            # Convert all material IDs to strings to match supplier data
            string_key_requirements = {}
            for material_id, req_data in yarn_requirements.items():
                string_key_requirements[str(material_id)] = req_data
                
            return string_key_requirements"""

# Replace the code
if old_code in content:
    content = content.replace(old_code, new_code, 1)
    planner_file.write_text(content, encoding='utf-8')
    print("Successfully patched planner.py")
else:
    print("Could not find the code to patch")
    
# Also check if we need to patch the fallback method
if "material_requirements[material_id] = {" in content:
    print("Note: You may also need to ensure material IDs are strings in the fallback method")