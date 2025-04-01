#!/usr/bin/env python3

with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the dictionary definition
lines[667] = '                            st.session_state["aml_ai_result"] = {\n'
lines[668] = '                                "parsed_data": updated_parsed_data,\n'
lines[669] = '                                "who_class": who_class,\n'
lines[670] = '                                "who_derivation": who_deriv,\n'
lines[671] = '                                "icc_class": icc_class,\n'
lines[672] = '                                "icc_derivation": icc_deriv,\n'
lines[673] = '                                "free_text_input": st.session_state.get("full_text_input", "")\n'
lines[674] = '                            }\n'
lines[675] = '                            st.session_state["expanded_aml_section"] = "classification"\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed dictionary definition in app.py") 