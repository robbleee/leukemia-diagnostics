#!/usr/bin/env python3

with open('app.py', 'r') as f:
    content = f.read()

# Find position right after the get_risk_class_color function - updated pattern
search_text = '            else:\n                return "#f5f7fa"  # Light gray\n        \n        # IPSS-M/R Risk data section'
if search_text in content:
    # Add our override form at this position
    overrides_code = '''            else:
                return "#f5f7fa"  # Light gray
        
        # Override section for IPSS calculations
        with st.expander("Override Options", expanded=True):
            st.markdown("### Optional Overrides")
            st.markdown("You can override specific values detected in the report. Leave at default values to use data from the report.")
            
            # Create 3 columns for the clinical value inputs
            col1, col2, col3 = st.columns(3)
            
            with col1:
                hb_override = st.number_input(
                    "Hemoglobin (g/dL)", 
                    min_value=0.0, 
                    max_value=20.0,
                    value=0.0,
                    step=0.1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="ipss_hb_override"
                )
                
                plt_override = st.number_input(
                    "Platelets (10^9/L)",
                    min_value=0, 
                    max_value=1000,
                    value=0,
                    step=1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="ipss_plt_override"
                )
            
            with col2:
                anc_override = st.number_input(
                    "ANC (10^9/L)",
                    min_value=0.0, 
                    max_value=20.0,
                    value=0.0,
                    step=0.1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="ipss_anc_override"
                )
                
                blast_override = st.number_input(
                    "Bone Marrow Blasts (%)",
                    min_value=0.0, 
                    max_value=30.0,
                    value=0.0,
                    step=0.1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="ipss_blast_override"
                )
            
            with col3:
                age_override = st.number_input(
                    "Age (years)",
                    min_value=18, 
                    max_value=120,
                    value=18,  # Min allowable value to indicate "not set"
                    step=1,
                    help="Leave at 18 to use value from report. Only values > 18 will override.",
                    key="ipss_age_override"
                )
                
                cyto_options = ["Very Good", "Good", "Intermediate", "Poor", "Very Poor"]
                cyto_override = st.selectbox(
                    "Cytogenetic Risk",
                    ["Use from report"] + cyto_options,
                    index=0,
                    help="Select only if you want to override the cytogenetic risk from the report.",
                    key="ipss_cyto_override"
                )
        
        # Button to calculate with overrides
        calculate_button = st.button("Calculate IPSS Risk", key="calculate_ipss_with_overrides", type="primary")
        
        # IPSS-M/R Risk data section
        if calculate_button or (mode == "ai" and free_text_input_value):'''
    
    # Replace the original section with our updated version
    modified_content = content.replace(search_text, overrides_code)
    
    # Now add the code to apply the overrides to the IPCC data
    # Updated search pattern
    search_text2 = '            # Parse the free text for IPCC risk parameters\n                ipcc_data = parse_ipcc_report(free_text_input_value)\n                \n                if ipcc_data:'
    if search_text2 in modified_content:
        apply_overrides_code = '''            # Parse the free text for IPCC risk parameters
                ipcc_data = parse_ipcc_report(free_text_input_value)
                
                if ipcc_data:
                    # Apply overrides if specified by user
                    if hb_override > 0:
                        ipcc_data["HB"] = hb_override
                    
                    if plt_override > 0:
                        ipcc_data["PLT"] = plt_override
                    
                    if anc_override > 0:
                        ipcc_data["ANC"] = anc_override
                    
                    if blast_override > 0:
                        ipcc_data["BM_BLAST"] = blast_override
                    
                    if age_override > 18:  # Age 18 is the minimum and signals "not set"
                        ipcc_data["AGE"] = age_override
                    
                    if cyto_override != "Use from report":
                        ipcc_data["CYTO_IPSSR"] = cyto_override'''
        
        final_content = modified_content.replace(search_text2, apply_overrides_code)
        
        with open('app.py', 'w') as f:
            f.write(final_content)
        
        print("Successfully updated app.py with IPSS overrides")
    else:
        print("Could not find the position to add override application code")
else:
    print("Could not find the position to add overrides form - search pattern not found in file") 