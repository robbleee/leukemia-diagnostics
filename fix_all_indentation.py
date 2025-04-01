#!/usr/bin/env python3

# This script fixes indentation issues throughout the app.py file
import re

# Read the file content
with open('app.py', 'r') as file:
    content = file.read()

# Let's focus on the specific problem area around line 550-565
pattern1 = re.compile(r'(                else:\s+)(for k in \[[\s\S]*?\]:\s+)(\S.*)')

# The regex captures:
# Group 1: The "else:" line with its indentation
# Group 2: The "for k in [...]:" block with its content
# Group 3: The line after the for loop that needs proper indentation

fixed_content = pattern1.sub(
    lambda m: m.group(1) + m.group(2) + '                        ' + m.group(3).lstrip(),
    content
)

# Write the fixed content back to the file
with open('app.py', 'w') as file:
    file.write(fixed_content)

print("Indentation issues fixed in app.py")

# Let's verify the content
with open('app.py', 'r') as file:
    lines = file.readlines()

# Print the relevant section to verify
start_line = 550
end_line = 565
print(f"\nVerifying lines {start_line}-{end_line}:")
for i in range(start_line - 1, end_line):
    if i < len(lines):
        print(f"{i+1}: {lines[i].rstrip()}") 