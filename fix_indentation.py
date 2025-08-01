#!/usr/bin/env python3
"""
Fix indentation errors in working_server.py
"""

# Read the file
with open('working_server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix indentation errors
fixed_lines = []
in_fallback_section = False

for i, line in enumerate(lines):
    # Detect the start of fallback section
    if "# Generate contextual responses (fallback)" in line:
        in_fallback_section = True
        fixed_lines.append(line)
        continue
    
    # Fix indentation in fallback section
    if in_fallback_section:
        # Check if this is an elif/if statement that needs proper indentation
        if line.strip().startswith(('elif ', 'if ')) and not line.startswith('                        '):
            # This is likely a misaligned elif/if
            if line.strip().startswith('elif '):
                fixed_line = '                        ' + line.strip() + '\n'
            else:
                fixed_line = '                            ' + line.strip() + '\n'
            fixed_lines.append(fixed_line)
        # Check if this is a response_text assignment that needs proper indentation
        elif 'response_text = ' in line and not line.startswith('                            '):
            fixed_line = '                            ' + line.strip() + '\n'
            fixed_lines.append(fixed_line)
        # Check if this is a response_text += that needs proper indentation
        elif 'response_text +=' in line and not line.startswith('                            '):
            fixed_line = '                            ' + line.strip() + '\n'
            fixed_lines.append(fixed_line)
        # Check if this is an if/elif inside the response generation
        elif line.strip().startswith(('if ', 'elif ', 'else:')) and 'response_text' not in line and not line.startswith('                            '):
            fixed_line = '                            ' + line.strip() + '\n'
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
        
        # End of fallback section
        if 'response = {' in line:
            in_fallback_section = False
    else:
        fixed_lines.append(line)

# Write the fixed file
with open('working_server.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation errors in working_server.py")