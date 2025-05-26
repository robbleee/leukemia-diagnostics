#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

# Find the TP53 confirmation section
found_section = False
fixed_lines = []

for i, line in enumerate(lines):
    if "if st.button(\"Confirm TP53 Information and Proceed\"" in line:
        # Found the problematic line
        found_section = True
        fixed_line = line.rstrip()
        
        # Check indentation and fix it
        spaces = len(fixed_line) - len(fixed_line.lstrip())
        if spaces > 16:  # This is based on the context - button should be indented with 16 spaces
            fixed_line = ' ' * 16 + fixed_line.lstrip()
        
        fixed_lines.append(fixed_line + '\n')
        
        # Fix the next lines indentation as well
        for j in range(i + 1, min(i + 100, len(lines))):
            next_line = lines[j]
            next_line_content = next_line.lstrip()
            
            # Preserve empty lines
            if not next_line_content:
                fixed_lines.append('\n')
                continue
                
            # Fix indentation of the continued section
            if "# Update the TP53 data" in next_line or "parsed_data" in next_line:
                fixed_lines.append(' ' * 20 + next_line_content + '\n')
            elif "with st.spinner" in next_line:
                fixed_lines.append(' ' * 20 + next_line_content + '\n')
            elif "st.session_state[" in next_line and "blast_percentage_known" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "who_class" in next_line or "icc_class" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "# Check if this is from manual mode" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "is_manual" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "if is_manual" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "# Store in manual result" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif "st.session_state[\"aml_manual_result\"]" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif any(x in next_line for x in ["\"parsed_data\"", "\"who_class\"", "\"who_derivation\"", "\"who_disease_type\"", "\"icc_class\"", "\"icc_derivation\"", "\"icc_disease_type\"", "\"free_text_input\""]):
                fixed_lines.append(' ' * 32 + next_line_content + '\n')
            elif "# Clear manual mode flag" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif "st.session_state.pop" in next_line and "is_manual_mode" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif "else:" in next_line and j > i + 30:  # This should be the else for manual/AI mode
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "# Store in AI result" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif "st.session_state[\"aml_ai_result\"]" in next_line:
                fixed_lines.append(' ' * 28 + next_line_content + '\n')
            elif "st.session_state[\"expanded_aml_section\"]" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "st.session_state[\"aml_busy\"]" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "# Clear the confirmation flags" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "st.session_state.pop" in next_line and any(x in next_line for x in ["tp53_confirmation_needed", "tp53_data_to_confirm", "parsed_data_pre_tp53_confirm"]):
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "# Go to results page" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "st.session_state[\"page\"]" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
            elif "st.rerun()" in next_line:
                fixed_lines.append(' ' * 24 + next_line_content + '\n')
                # After this line, we're done with fixing the section
                found_section = False
                break
            else:
                # Other lines should be added with their original indentation
                fixed_lines.append(next_line)
    elif not found_section:
        # Keep all other lines unchanged
        fixed_lines.append(line)

# Write the fixed file
with open('app_fixed.py', 'w') as f:
    f.writelines(fixed_lines)

print("Indentation fixing completed. Check app_fixed.py") 