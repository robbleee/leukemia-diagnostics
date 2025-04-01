#!/usr/bin/env python3

# This script fixes the indentation issue after the else statement at line 551
with open('app.py', 'r') as file:
    lines = file.readlines()

# Find the line with "else:" followed by "for k in ["
for i in range(len(lines)):
    if "else:" in lines[i] and i+1 < len(lines) and "for k in [" in lines[i+1]:
        # Add indentation to the for loop and the following lines
        lines[i+1] = "                    " + lines[i+1].lstrip()  # 20 spaces (4 more than the else line)
        
        # Also indent the following lines that are part of the for loop list
        j = i + 2
        while j < len(lines) and ('"' in lines[j] or "'" in lines[j]) and "]" not in lines[j]:
            lines[j] = "                        " + lines[j].lstrip()  # 24 spaces (4 more than the for line)
            j += 1
        
        # Indent the closing bracket line if it exists separately
        if j < len(lines) and "]" in lines[j] and ('"' not in lines[j] and "'" not in lines[j]):
            lines[j] = "                    " + lines[j].lstrip()  # Same indent as the for line
        
        print(f"Fixed indentation at lines {i+1}-{j+1}")
        break

# Write the fixed content back to the file
with open('app.py', 'w') as file:
    file.writelines(lines)

print("Indentation fixed in app.py") 