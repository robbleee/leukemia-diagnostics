import re; # Will replace the Risk section

import re

# Read the app.py file
with open('app.py', 'r') as f:
    content = f.read()

# Define the new Risk section
new_risk_section = '''    elif sub_tab == "Risk":
        # Opening introduction for the Risk section
        st.markdown("### Risk Assessment")
        st.markdown("This section provides risk stratification based on established prognostic models.")
        
        # ------------------- ELN RISK SECTION -------------------
        st.markdown("## ELN Risk Assessment")
        st.markdown("European LeukemiaNet risk stratification for AML.")
        
        # Create two columns for ELN risk display
        eln_col1, eln_col2 = st.columns(2)
        
        # Left Column: ELN 2022 Risk Classification using full classifier
        with eln_col1:
            st.markdown("#### ELN 2022 Risk Classification")
            # Use the full ELN parsing function as requested
            risk_eln2022, median_os_eln2022, derivation_eln2022 = classify_full_eln2022(res["parsed_data"])
            st.markdown(f"**Risk Category:** {risk_eln2022}")
            st.markdown(f"**Median OS:** {median_os_eln2022}")
            with st.expander("ELN 2022 Derivation", expanded=False):
                # Use derivation_eln2022 directly since we just calculated it
                derivation = derivation_eln2022
                
                if isinstance(derivation, list):
                    for step in derivation:
                        st.markdown(f"- {step}")
                else:
                    # For backwards compatibility with old format
                    st.markdown(derivation)
        
        # Right Column: Revised ELN24 Non-Intensive Risk Classification
        with eln_col2:
            st.markdown("#### Revised ELN24 (Non-Intensive) Risk")
            eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
            risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
            st.markdown(f"**Risk Category:** {risk_eln24}")
            # Format OS display with proper unit
            os_display = str(median_os_eln24) + " months" if isinstance(median_os_eln24, (int, float)) else str(median_os_eln24)
            st.markdown(f"**Median OS:** {os_display}")
            with st.expander("Revised ELN24 Derivation", expanded=False):
                for step in eln24_derivation:
                    st.markdown(f"- {step}")
        
        # Divider between risk sections
        st.markdown("---")
        
        # ------------------- IPSS RISK SECTION -------------------
        st.markdown("## IPSS Risk Assessment")
        st.markdown("International Prognostic Scoring System for myelodysplastic syndromes.")
        
        # IPSS-M/R Risk data section
        if mode == "ai" and free_text_input_value:
            # Parse the free text input for IPCC risk if we have AI-processed input
            from parsers.mds_ipcc_parser import parse_ipcc_report
            from classifiers.mds_ipssm_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
            
            with st.spinner("Calculating IPSS-M/R Risk scores..."):
                # Parse the free text for IPCC risk parameters
                ipcc_data = parse_ipcc_report(free_text_input_value)
                
                if ipcc_data:
                    # Display IPSS-M and IPSS-R in two columns
                    ipcc_col1, ipcc_col2 = st.columns(2)
                    
                    # Left column for IPSS-M
                    with ipcc_col1:
                        st.markdown("#### IPSS-M Risk Assessment")
                        
                        # Calculate IPSS-M scores
                        ipssm_result = calculate_ipssm(patient_data=ipcc_data)
                        
                        if ipssm_result:
                            # Display mean scenario results
                            mean_result = ipssm_result.get("means", {})
                            st.markdown(f"**Risk Category:** {mean_result.get('risk_cat', 'Unable to calculate')}")
                            st.markdown(f"**Risk Score:** {mean_result.get('risk_score', 'N/A')}")
                            
                            with st.expander("IPSS-M Details", expanded=False):
                                st.markdown("##### Risk Scenarios")
                                st.markdown(f"- **Best Case:** {ipssm_result.get('best', {}).get('risk_cat', 'N/A')}")
                                st.markdown(f"- **Mean Case:** {mean_result.get('risk_cat', 'N/A')}")
                                st.markdown(f"- **Worst Case:** {ipssm_result.get('worst', {}).get('risk_cat', 'N/A')}")
                                
                                st.markdown("##### Patient Values")
                                for key, value in ipcc_data.items():
                                    if not key.startswith("__") and isinstance(value, (int, float, str)) and key not in ["IPSSM_CAT", "IPSSM_SCORE"]:
                                        st.markdown(f"- **{key}:** {value}")
                    
                    # Right column for IPSS-R
                    with ipcc_col2:
                        st.markdown("#### IPSS-R Risk Assessment")
                        
                        # Calculate IPSS-R scores
                        ipssr_result = calculate_ipssr(patient_data=ipcc_data)
                        
                        if ipssr_result:
                            st.markdown(f"**Risk Category:** {ipssr_result.get('IPSSR_CAT', 'Unable to calculate')}")
                            st.markdown(f"**Risk Score:** {ipssr_result.get('IPSSR_SCORE', 'N/A')}")
                            
                            if ipssr_result.get('IPSSRA_SCORE'):
                                st.markdown(f"**Age-Adjusted Category:** {ipssr_result.get('IPSSRA_CAT', 'N/A')}")
                                st.markdown(f"**Age-Adjusted Score:** {ipssr_result.get('IPSSRA_SCORE', 'N/A')}")
                            
                            with st.expander("IPSS-R Details", expanded=False):
                                if "components" in ipssr_result:
                                    st.markdown("##### Score Components")
                                    for component, value in ipssr_result["components"].items():
                                        st.markdown(f"- **{component}:** {value}")
                                
                                st.markdown("##### Patient Values")
                                for key in ["HB", "PLT", "ANC", "BM_BLAST", "AGE", "CYTO_IPSSR"]:
                                    if key in ipcc_data:
                                        st.markdown(f"- **{key}:** {ipcc_data[key]}")
                else:
                    st.warning("Insufficient data to calculate IPSS-M/R risk scores. The free text may not contain all necessary information for risk assessment.")
        else:
            st.info("IPSS-M/R Risk assessment requires free text input. This feature is only available when using the AI-assisted mode with free text input.")
            st.markdown("""
            Consider using the dedicated IPSS-M/R Risk Tool page for more detailed classification.
            """)
        
        # End of Risk tab content'''

# Use regex to replace the entire Risk section
pattern = re.compile(r'elif sub_tab == "Risk":.*?elif sub_tab == "Differentiation":', re.DOTALL)
modified_content = pattern.sub(new_risk_section + '\n\n    elif sub_tab == "Differentiation":', content)

# Write the modified content back to app.py
with open('app.py', 'w') as f:
    f.write(modified_content)

print("Risk section updated successfully.")
