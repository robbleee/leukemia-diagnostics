import re; # Will replace the Risk section

import re

# Read the app.py file
with open('app.py', 'r') as f:
    content = f.read()

# Define the new Risk section
new_risk_section = '''    elif sub_tab == "Risk":
        # Import necessary functions for ELN risk assessment
        from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk
        from parsers.aml_eln_parser import parse_eln_report
        
        # Opening introduction for the Risk section
        st.markdown("### Risk Assessment")
        st.markdown("This section provides risk stratification based on established prognostic models.")
        
        # Style for the ELN risk boxes - matching the standalone calculator
        st.markdown("""
        <style>
            .risk-box {
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .favorable {
                background-color: #c8e6c9;
                border: 1px solid #2e7d32;
            }
            .intermediate {
                background-color: #fff9c4;
                border: 1px solid #f9a825;
            }
            .adverse {
                background-color: #ffcdd2;
                border: 1px solid #c62828;
            }
            .risk-title {
                font-size: 1.4rem;
                font-weight: 600;
                margin-bottom: 10px;
            }
            .risk-value {
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 10px;
            }
            .risk-os {
                font-style: italic;
                margin-bottom: 5px;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Function to determine CSS class based on risk category
        def get_risk_class(risk):
            risk = risk.lower()
            if 'favorable' in risk:
                return 'favorable'
            elif 'intermediate' in risk:
                return 'intermediate'
            elif 'adverse' in risk:
                return 'adverse'
            else:
                return 'intermediate'
        
        # ------------------- ELN RISK SECTION -------------------
        st.markdown("## ELN Risk Assessment")
        st.markdown("European LeukemiaNet risk stratification for AML.")
        
        # Process free text through ELN parser (if available)
        if free_text_input_value:
            with st.spinner("Processing ELN risk assessment..."):
                # Parse the report to extract ELN markers
                parsed_eln_data = parse_eln_report(free_text_input_value)
                
                if parsed_eln_data:
                    # Prepare data for ELN 2024 non-intensive classification
                    eln24_genes = {
                        "TP53": parsed_eln_data.get("tp53_mutation", False),
                        "KRAS": parsed_eln_data.get("kras", False),
                        "PTPN11": parsed_eln_data.get("ptpn11", False),
                        "NRAS": parsed_eln_data.get("nras", False),
                        "FLT3_ITD": parsed_eln_data.get("flt3_itd", False),
                        "NPM1": parsed_eln_data.get("npm1_mutation", False),
                        "IDH1": parsed_eln_data.get("idh1", False),
                        "IDH2": parsed_eln_data.get("idh2", False),
                        "DDX41": parsed_eln_data.get("ddx41", False)
                    }
                    
                    # Calculate ELN 2022 risk
                    risk_eln2022, eln22_median_os, derivation_eln2022 = classify_full_eln2022(parsed_eln_data)
                    
                    # Calculate ELN 2024 non-intensive risk
                    risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
                    
                    # Store for potential reuse
                    st.session_state['eln_derivation'] = derivation_eln2022
                    st.session_state['eln24_derivation'] = eln24_derivation
                    st.session_state['original_eln_data'] = parsed_eln_data.copy()
                else:
                    # Fall back to using the parsed data from the AML parser
                    risk_eln2022, eln22_median_os, derivation_eln2022 = classify_ELN2022(res["parsed_data"])
                    eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
                    risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
        else:
            # Fall back to using the parsed data from the AML parser
            risk_eln2022, eln22_median_os, derivation_eln2022 = classify_ELN2022(res["parsed_data"])
            eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
            risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
        
        # Get the risk classes
        eln_class = get_risk_class(risk_eln2022)
        eln24_class = get_risk_class(risk_eln24)
        
        # Create two columns for risk displays
        eln_col1, eln_col2 = st.columns(2)
        
        # ELN 2022 Risk Classification
        with eln_col1:
            st.markdown(f"""
            <div class='risk-box {eln_class}'>
                <div class='risk-title'>ELN 2022 Risk</div>
                <div class='risk-value'>{risk_eln2022}</div>
                <div class='risk-os'>Median OS: {eln22_median_os}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("ELN 2022 Derivation", expanded=False):
                # Check if the derivation is a list of strings (new format) or a single string (old format)
                if isinstance(derivation_eln2022, list):
                    for step in derivation_eln2022:
                        st.markdown(f"- {step}")
                else:
                    # For backwards compatibility with old format
                    st.markdown(derivation_eln2022)
        
        # ELN 2024 Non-Intensive Risk Classification
        with eln_col2:
            # Format the display differently if median_os_eln24 is a string (e.g., "N/A")
            os_display = f"{median_os_eln24} months" if isinstance(median_os_eln24, (int, float)) else median_os_eln24
            
            st.markdown(f"""
            <div class='risk-box {eln24_class}'>
                <div class='risk-title'>ELN 2024 Risk (Non-Intensive)</div>
                <div class='risk-value'>{risk_eln24}</div>
                <div class='risk-os'>Median OS: {os_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("ELN 2024 Derivation", expanded=False):
                for step in eln24_derivation:
                    st.markdown(f"- {step}")
        
        # Display the original data for transparency
        if 'original_eln_data' in st.session_state:
            with st.expander("Data Inspector - ELN Features", expanded=False):
                st.subheader("Features Used for ELN Classification")
                display_data = st.session_state['original_eln_data'].copy()
                if '__prompts' in display_data:
                    del display_data['__prompts']
                st.json(display_data)
        
        # Clinical Implications
        with st.expander("Clinical Implications", expanded=False):
            implications = ""
            if 'adverse' in risk_eln2022.lower():
                implications = """
                - **Adverse Risk**: Consider enrollment in clinical trials when available.
                - High-risk disease may benefit from intensive induction regimens followed by allogeneic stem cell transplantation (if eligible).
                - Consider novel agent combinations or targeted therapies based on specific mutations.
                - Close monitoring for early relapse is recommended.
                """
            elif 'favorable' in risk_eln2022.lower():
                implications = """
                - **Favorable Risk**: Standard induction chemotherapy followed by consolidation is typically recommended.
                - Allogeneic transplantation in first remission is generally not recommended.
                - Monitoring for measurable residual disease (MRD) can guide further treatment decisions.
                - Consider targeted therapies for specific mutations (e.g., FLT3 inhibitors if FLT3-ITD present).
                """
            else:
                implications = """
                - **Intermediate Risk**: Consider standard induction chemotherapy.
                - Allogeneic transplantation may be considered based on additional factors (age, comorbidities, donor availability).
                - Monitor for measurable residual disease (MRD) to guide post-remission therapy.
                - Consider clinical trials for novel treatment approaches when available.
                """
            
            st.markdown(implications)
            
            st.markdown("""
            #### Important Considerations

            - **ELN 2022** is the standard risk stratification for AML patients treated with intensive chemotherapy.
            - **ELN 2024 Non-Intensive** stratification is designed for patients who will receive non-intensive therapy (e.g., venetoclax combinations, HMA therapy).
            - Risk stratification should be considered alongside other clinical factors:
              - Patient age and performance status
              - Comorbidities
              - Prior hematologic disorders (MDS, MPN)
              - History of chemotherapy or radiation (therapy-related AML)
            """)
        
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
