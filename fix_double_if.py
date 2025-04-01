#!/usr/bin/env python3

with open('app.py', 'r') as f:
    content = f.read()

# Find and fix the double if statement
search_text = '        # IPSS-M/R Risk data section\n        if calculate_button or (mode == "ai" and free_text_input_value):\n        if mode == "ai" and free_text_input_value):'
replacement = '        # IPSS-M/R Risk data section\n        if calculate_button or (mode == "ai" and free_text_input_value):'

if search_text in content:
    fixed_content = content.replace(search_text, replacement)
    with open('app.py', 'w') as f:
        f.write(fixed_content)
    print("Fixed double if statement issue")
else:
    # Try another pattern
    search_text2 = '        # IPSS-M/R Risk data section\n        if calculate_button or (mode == "ai" and free_text_input_value):\n        if mode == "ai" and free_text_input_value:'
    if search_text2 in content:
        fixed_content = content.replace(search_text2, replacement)
        with open('app.py', 'w') as f:
            f.write(fixed_content)
        print("Fixed double if statement issue - second pattern")
    else:
        print("Could not find the double if statement pattern") 