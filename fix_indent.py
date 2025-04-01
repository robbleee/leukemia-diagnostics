#!/usr/bin/env python3
import re

with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the indentation for lines 655-670 (handling all the code that needs to be indented)
for i in range(654, 670):
    if i >= len(lines):
        break
    # Add proper indentation after else statement
    if i >= 654:
        lines[i] = re.sub(r'^                ', '                        ', lines[i])
        # Adjust deeper indentation levels
        lines[i] = re.sub(r'^                        if', '                            if', lines[i])
        lines[i] = re.sub(r'^                        with', '                            with', lines[i])
        lines[i] = re.sub(r'^                            st\.', '                                st\.', lines[i])

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed indentation in app.py") 