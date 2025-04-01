#!/usr/bin/env python3

# This script fixes the indentation issue after the for loop at line 552
with open('app.py', 'r') as file:
    lines = file.readlines()

# Find the line with the for loop closing bracket followed by st.session_state.pop
for i in range(len(lines)):
    if "]:" in lines[i] and i+1 < len(lines) and "st.session_state.pop" in lines[i+1]:
        # Add indentation to the statement after the for loop
        lines[i+1] = "                        " + lines[i+1].lstrip()  # 24 spaces (same as items in the list)
        print(f"Fixed indentation at line {i+2}")
        break

# Write the fixed content back to the file
with open('app.py', 'w') as file:
    file.writelines(lines)

print("Indentation fixed in app.py") 