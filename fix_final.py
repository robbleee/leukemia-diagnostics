#!/usr/bin/env python3

# This script will fix indentation issues in the app.py file
# Focusing specifically on the manual inputs section with submit_button

with open('app.py', 'r') as f:
    content = f.read()

# Define fixed section with proper indentation
fixed_section = '''                if submit_button:
                    # Check if germline status is "Yes" but no mutations are selected
                    if st.session_state.get("germline_status") == "Yes" and not st.session_state.get("selected_germline"):
                        st.error("Please select at least one germline mutation when 'Germline predisposition' is set to 'Yes'.")
                    else:
                        updated_parsed_data = st.session_state.get("initial_parsed_data") or {}
                        updated_parsed_data["blasts_percentage"] = manual_blast_percentage
                        updated_parsed_data["bone_marrow_blasts_override"] = st.session_state["bone_marrow_blasts_initial"]

                        if updated_parsed_data.get("AML_differentiation") is None or (updated_parsed_data.get("AML_differentiation") or "").lower() == "ambiguous":
                            diff_str = diff_map[manual_differentiation]
                            updated_parsed_data["AML_differentiation"] = diff_str

                        with st.spinner("Re-classifying with manual inputs..."):
                            who_class, who_deriv = classify_combined_WHO2022(updated_parsed_data, not_erythroid=False)
                            icc_class, icc_deriv = classify_combined_ICC2022(updated_parsed_data)
                            # Again, do not call classify_ELN2022 here; let it be computed in results.
                            st.session_state["aml_ai_result"] = {
                                "parsed_data": updated_parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                "free_text_input": st.session_state.get("full_text_input", "")
                            }
                            st.session_state["expanded_aml_section"] = "classification"

                        st.session_state["page"] = "results"
                        st.rerun()'''

# Find the beginning and end of the problematic section
start_marker = "                if submit_button:"
end_marker = "##################################\n# 2. RESULTS PAGE"

# Replace the problematic section
parts = content.split(start_marker)
if len(parts) > 1:
    before = parts[0]
    after_parts = parts[1].split(end_marker)
    if len(after_parts) > 1:
        after = end_marker + after_parts[1]
        fixed_content = before + fixed_section + "\n\n\n" + after
        
        with open('app.py', 'w') as f:
            f.write(fixed_content)
        
        print("Successfully fixed indentation issues in app.py")
    else:
        print("Could not find end marker")
else:
    print("Could not find start marker") 