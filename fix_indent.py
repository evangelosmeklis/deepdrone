#!/usr/bin/env python3
# Quick script to fix the indentation issue in drone_chat.py

with open('drone/drone_chat.py', 'r') as f:
    lines = f.readlines()

# Check the indentation of problematic lines
fixed_lines = []
in_problematic_section = False

for i, line in enumerate(lines):
    if i >= 1249 and i <= 1280:  # Around the problematic section
        if line.strip().startswith('# Display all messages in history'):
            in_problematic_section = True
        
        if in_problematic_section and line.strip().startswith('elif message["role"] == "system":'):
            # Fix indentation making sure it aligns with the if statement
            indent = ' ' * 12  # Match the indentation of the 'if' statement
            fixed_line = indent + line.strip() + '\n'
            fixed_lines.append(fixed_line)
            continue
        
        # After handling the 'else' part, reset the flag
        if in_problematic_section and line.strip().startswith('else:'):
            in_problematic_section = False
    
    # For all other lines, keep them unchanged
    fixed_lines.append(line)

with open('drone/drone_chat.py', 'w') as f:
    f.writelines(fixed_lines)

print("Fixed indentation in drone_chat.py") 