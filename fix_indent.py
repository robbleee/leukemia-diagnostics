#!/usr/bin/env python3

# Script to fix indentation issues in app.py
with open('app.py', 'r') as file:
    lines = file.readlines()

# Fix the indentation after the else: statement at line 551
if len(lines) > 551:
    # Add proper indentation to the 'for' loop after the 'else:' statement
    for i in range(551, min(565, len(lines))):
        if i == 551 and 'else:' in lines[i]:
            continue  # Keep the 'else:' line unchanged
        elif i == 552 and 'for k in' in lines[i]:
            # Add 4 spaces to the 'for' line
            lines[i] = '                    ' + lines[i].lstrip()
        elif i >= 553 and i <= 559:
            # Add 8 spaces to the list items
            lines[i] = '                        ' + lines[i].lstrip()
        elif i == 560 and ']:' in lines[i]:
            # Add 8 spaces to the closing bracket
            lines[i] = '                        ' + lines[i].lstrip()
        elif i == 561 and 'st.session_state.pop' in lines[i]:
            # Add 8 spaces to the statement inside the loop
            lines[i] = '                        ' + lines[i].lstrip()
        # Don't modify lines after the block

# Write the fixed content back to app.py
with open('app.py', 'w') as file:
    file.writelines(lines)

print("Indentation issue fixed in app.py")
