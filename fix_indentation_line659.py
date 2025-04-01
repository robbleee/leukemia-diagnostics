#!/usr/bin/env python3

# This script fixes the indentation issue after the else statement at line 658
with open('app.py', 'r') as file:
    lines = file.readlines()

# Find the line with the else statement
for i, line in enumerate(lines):
    if 'else:' in line and i >= 657 and i <= 659:
        else_line = i
        else_indent = len(line) - len(line.lstrip())
        
        # Check how many lines after the else need to be indented
        j = else_line + 1
        lines_to_indent = []
        
        # Find lines that should be indented as part of the else block
        # Continue until we find a line with equal or less indentation
        while j < len(lines):
            if not lines[j].strip():  # Skip empty lines
                j += 1
                continue
                
            current_indent = len(lines[j]) - len(lines[j].lstrip())
            if current_indent <= else_indent:
                break
            lines_to_indent.append(j)
            j += 1
        
        # If no lines to indent, indent the next three non-empty lines
        if not lines_to_indent:
            j = else_line + 1
            count = 0
            while j < len(lines) and count < 3:
                if lines[j].strip():  # If line is not empty
                    lines_to_indent.append(j)
                    count += 1
                j += 1
        
        # Add indentation to the lines after else
        indent_spaces = ' ' * (else_indent + 4)  # Add 4 spaces more than else line
        for line_num in lines_to_indent:
            lines[line_num] = indent_spaces + lines[line_num].lstrip()
            
        print(f"Fixed indentation at lines {else_line+1}-{max(lines_to_indent)+1}")
        break

# Write the fixed content back to the file
with open('app.py', 'w') as file:
    file.writelines(lines)

print("Indentation fixed in app.py") 