#!/usr/bin/env python3

# This script fixes the over-indentation on line 561
with open('app.py', 'r') as file:
    lines = file.readlines()

# Find the line with excessive indentation
for i, line in enumerate(lines):
    if "st.session_state.pop(k, None)" in line and line.startswith(" " * 20):
        # Correct indentation to be 8 spaces more than the for line (which has 20 spaces)
        lines[i] = " " * 28 + line.lstrip()
        print(f"Fixed over-indentation at line {i+1}")
        break

# Write the fixed content back to the file
with open('app.py', 'w') as file:
    file.writelines(lines)

print("Fixed over-indentation in app.py") 