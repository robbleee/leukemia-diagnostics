#!/usr/bin/env python3

# Let's use a more reliable approach by directly setting the indentation level
with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix dictionary indentation structure in the problematic area
lines[671] = '                                "icc_class": icc_class,\n'
lines[672] = '                                "icc_derivation": icc_deriv,\n'
lines[673] = '                                "free_text_input": st.session_state.get("full_text_input", "")\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed additional indentation in app.py") 