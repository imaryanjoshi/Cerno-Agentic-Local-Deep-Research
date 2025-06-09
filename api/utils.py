# api/utils.py
import re
import os
from api.config import AGENT_OUTPUT_DIR 

# Ensure this function signature matches how it's called
def update_markdown_plan_checkbox_by_description(
    markdown_plan_filename: str, # Argument 1
    description_to_find: str,    # Argument 2
    success: bool                # Argument 3
) -> bool:
    md_filepath = os.path.join(AGENT_OUTPUT_DIR, markdown_plan_filename)
    if not os.path.exists(md_filepath):
        print(f"Error: {md_filepath} not found for updating checkbox.")
        return False
    try:
        with open(md_filepath, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            updated = False
            for i, line in enumerate(lines):
                if (line.strip().startswith("- [ ]") or \
                    line.strip().startswith("- [x]") or \
                    line.strip().startswith("- [!]")) and \
                    description_to_find in line: # This matching might need to be more robust
                    
                    checkbox_pattern = r"- \[[ x!]\]" # Pattern to find any existing checkbox
                    if success:
                        lines[i] = re.sub(checkbox_pattern, "- [x]", line, 1)
                    else:
                        lines[i] = re.sub(checkbox_pattern, "- [!]", line, 1) # Mark as error/failed
                    updated = True
                    print(f"Updated checkbox in {md_filepath} for task containing: '{description_to_find}' to success={success}")
                    break 
            
            if updated:
                f.seek(0)
                f.writelines(lines)
                f.truncate()
            else:
                print(f"Warning: Task description containing '{description_to_find}' not found or already in desired state in {md_filepath}.")
            return updated
    except Exception as e:
        print(f"Error updating markdown plan {md_filepath}: {e}")
        return False