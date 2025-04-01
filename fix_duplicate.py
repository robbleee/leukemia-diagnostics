#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the duplicated dictionary assignment (remove line 667)
# Lines 666-667 both have statements trying to set st.session_state["aml_ai_result"]
# We'll remove line 667 and keep the correctly indented dictionary on lines 668-674
if 'st.session_state["aml_ai_result"]' in lines[666] and 'st.session_state["aml_ai_result"]' in lines[667]:
    lines[667] = ''  # Remove the duplicated line

# Write the fixed file
with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed duplicate dictionary assignment in app.py") 