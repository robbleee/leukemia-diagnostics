import streamlit as st
from classifiers.aml_mds_combined import classify_combined_WHO2022

def display_erythroid_form_for_classification(classification: str, parsed_fields: dict):
    """
    If 'erythroid' is in the classification (case-insensitive), display a form for user input:
      - % erythroid differentiation
      - % pro erythroblasts

    Upon submission:
      - If differentiation >= 80% and pro erythroblasts >= 30%, call the combined classifier with not_erythroid=False.
      - Otherwise, call it with not_erythroid=True.
    The new results update the session state and the form is removed from the display.
    Additionally, deviation details are appended to the classifier's derivation.
    """
    if "erythroid" in classification.lower():
        # Create a placeholder to hold the form
        form_placeholder = st.empty()

        with form_placeholder.form("erythroid_form"):
            st.markdown(
                "<h4 style='margin-bottom: 0px;'>Further information required for classification</h4>",
                unsafe_allow_html=True
            )
            erythroid_diff = st.number_input(
                "Enter % erythroid differentiation", 
                min_value=0.0, max_value=100.0, step=0.1, format="%.1f"
            )
            pro_erythroblasts = st.number_input(
                "Enter % of pro erythroblasts", 
                min_value=0.0, max_value=100.0, step=0.1, format="%.1f"
            )
            submit = st.form_submit_button("Submit Erythroid Data")

        if submit:
            # Remove the form from the interface
            form_placeholder.empty()

            # Determine the not_erythroid flag and prepare deviation details.
            if erythroid_diff >= 80.0 and pro_erythroblasts >= 30.0:
                not_erythroid_flag = False
                deviation_details = "Erythroid override applied: differentiation >= 80% and pro erythroblasts >= 30%."
            else:
                not_erythroid_flag = True
                deviation_details = "No erythroid override: criteria not met."

            # Call the combined classifier with the flag and properly unpack all three return values
            new_class, new_deriv, disease_type = classify_combined_WHO2022(parsed_fields, not_erythroid=not_erythroid_flag)

            # Append the deviation details to the derivation
            new_deriv.append(deviation_details)

            # Update session state with new classification results
            st.session_state["classification_who"] = new_class
            st.session_state["who_derivation"] = new_deriv

            # Display the new classification results
            st.markdown(f"**Classification:** {new_class}")

def display_aml_classification_results(
    parsed_fields,
    classification_who,
    who_derivation,
    classification_icc,
    icc_derivation,
    classification_eln,  # if needed elsewhere; not shown in these two columns
    mode="manual",
    show_parsed_fields: bool = False
):
    """
    Displays AML classification results in Streamlit.

    Args:
        parsed_fields (dict): The raw parsed data values.
        classification_who (str): WHO 2022 classification result.
        who_derivation (list): Step-by-step derivation for WHO 2022.
        classification_icc (str): ICC 2022 classification result.
        icc_derivation (list): Step-by-step derivation for ICC 2022.
        classification_eln (str): ELN classification result.
        mode (str): Typically 'manual' or other mode.
        show_parsed_fields (bool): Whether to show the "View Parsed AML Values" expander.
    """
    ##########################################
    # 0. Check for missing cytogenetic data and display warning
    ##########################################
    if parsed_fields.get("no_cytogenetics_data", False):
        st.warning("""
        ⚠️ **No cytogenetic data was detected in your report.** 
        
        Cytogenetic information is critical for accurate AML/MDS classification. 
        For more accurate results, please provide a complete report that includes cytogenetic data 
        (karyotype, FISH analysis, or specific cytogenetic abnormalities).
        """)
    
    ##########################################
    # 1. Display WHO & ICC Classifications Side-by-Side
    ##########################################
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **WHO 2022 Classification**")
        # If classification mentions erythroid, show the evaluation form (and not the static text)
        if "erythroid" in classification_who.lower():
            display_erythroid_form_for_classification(classification_who, parsed_fields)
        else:
            st.markdown(f"**Classification:** {classification_who}")
    with col2:
        st.markdown("### **ICC 2022 Classification**")
        if "erythroid" in classification_icc.lower():
            display_erythroid_form_for_classification(classification_icc, parsed_fields)
        else:
            st.markdown(f"**Classification:** {classification_icc}")
    
    ##########################################
    # 2. Display Derivations Side-by-Side
    ##########################################
    col_who, col_icc = st.columns(2)
    with col_who:
        with st.expander("View WHO 2022 Derivation", expanded=False):
            who_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(who_derivation, start=1)]
            )
            st.markdown(who_derivation_markdown)
    with col_icc:
        with st.expander("View ICC 2022 Derivation", expanded=False):
            icc_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(icc_derivation, start=1)]
            )
            st.markdown(icc_derivation_markdown)
    
    ##########################################
    # 3. Display All Form Inputs
    ##########################################
    with st.expander("View All Form Inputs", expanded=False):
        st.markdown("### Form Input Data")
        st.markdown("Below is all the data that was used for classification:")
        
        # Create a nicely formatted display of all inputs
        if parsed_fields:
            # Display clinical parameters first
            clinical_params = ["blast_percentage", "fibrotic", "hypoplasia", "number_of_dysplastic_lineages"]
            clinical_values = {k: v for k, v in parsed_fields.items() if k in clinical_params}
            
            if clinical_values:
                st.markdown("#### Clinical Parameters")
                for key, value in clinical_values.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
            
            # Display genetic abnormalities
            genetic_params = [k for k in parsed_fields.keys() if any(term in k.lower() for term in 
                             ["mutation", "translocation", "inversion", "rearrangement", "deletion", "gene"])]
            genetic_values = {k: v for k, v in parsed_fields.items() if k in genetic_params}
            
            if genetic_values:
                st.markdown("#### Genetic Parameters")
                for key, value in genetic_values.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
            
            # Display all other parameters
            other_params = {k: v for k, v in parsed_fields.items() 
                          if k not in clinical_values and k not in genetic_values}
            
            if other_params:
                st.markdown("#### Other Parameters")
                for key, value in other_params.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
        else:
            st.info("No input data available for display.")
    
    ##########################################
    # 4. (Optional) Show JSON of parsed fields
    ##########################################
    if show_parsed_fields:
        with st.expander("View Parsed AML Values", expanded=False):
            st.json(parsed_fields)

def display_mds_classification_results(parsed_fields, classification_who, derivation_who,
                                       classification_icc, derivation_icc, mode="manual"):
    """
    Displays MDS classification results WITHOUT automatically calling the AI review.
    """
    
    ##########################################
    # 0. Check for missing cytogenetic data and display warning
    ##########################################
    if parsed_fields.get("no_cytogenetics_data", False):
        st.warning("""
        ⚠️ **No cytogenetic data was detected in your report.** 
        
        Cytogenetic information is critical for accurate MDS classification and risk stratification. 
        For more accurate results, please provide a complete report that includes cytogenetic data 
        (karyotype, FISH analysis, or specific cytogenetic abnormalities).
        """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **WHO 2022 Classification**")
        st.write(classification_who)
    with col2:
        st.markdown("### **ICC 2022 Classification**")
        st.write(classification_icc)

    col_who, col_icc = st.columns(2)
    with col_who:
        st.markdown("#### WHO 2022 Derivation")
        with st.container():
            st.markdown("""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f8f9fa;">
            """, unsafe_allow_html=True)
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_who, start=1)]
            )
            st.markdown(derivation_text)
            st.markdown("</div>", unsafe_allow_html=True)
    with col_icc:
        st.markdown("#### ICC 2022 Derivation")
        with st.container():
            st.markdown("""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f8f9fa;">
            """, unsafe_allow_html=True)
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_icc, start=1)]
            )
            st.markdown(derivation_text)
            st.markdown("</div>", unsafe_allow_html=True)

    # Display All Form Inputs
    with st.expander("View All Form Inputs", expanded=False):
        st.markdown("### Form Input Data")
        st.markdown("Below is all the data that was used for classification:")
        
        # Create a nicely formatted display of all inputs
        if parsed_fields:
            # Display clinical parameters first
            clinical_params = ["blast_percentage", "bm_blast", "hb", "plt", "anc", "age", "dysplastic_lineages"]
            clinical_values = {k: v for k, v in parsed_fields.items() if k.lower() in [p.lower() for p in clinical_params]}
            
            if clinical_values:
                st.markdown("#### Clinical Parameters")
                for key, value in clinical_values.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
            
            # Display cytogenetic parameters
            cyto_params = [k for k in parsed_fields.keys() if any(term in k.lower() for term in 
                          ["cytogenetic", "karyotype", "cyto", "deletion", "del", "monosomy", "trisomy"])]
            cyto_values = {k: v for k, v in parsed_fields.items() if k in cyto_params}
            
            if cyto_values:
                st.markdown("#### Cytogenetic Parameters")
                for key, value in cyto_values.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
            
            # Display genetic parameters
            genetic_params = [k for k in parsed_fields.keys() if any(term in k.lower() for term in 
                             ["mutation", "gene", "variant", "sf3b1", "tp53", "asxl1", "runx1"])]
            genetic_values = {k: v for k, v in parsed_fields.items() if k in genetic_params}
            
            if genetic_values:
                st.markdown("#### Genetic Parameters")
                for key, value in genetic_values.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
            
            # Display all other parameters
            other_params = {k: v for k, v in parsed_fields.items() 
                          if k not in clinical_values and k not in cyto_values and k not in genetic_values}
            
            if other_params:
                st.markdown("#### Other Parameters")
                for key, value in other_params.items():
                    formatted_key = key.replace("_", " ").title()
                    st.markdown(f"- **{formatted_key}**: {value}")
        else:
            st.info("No input data available for display.")
    
    # View JSON data (moved this after the new expander but keep it for full raw data viewing)
    with st.expander("View Parsed MDS Values", expanded=False):
        st.json(parsed_fields)

def display_aml_response_results(parsed_data, response, derivation, mode="manual"):
    with st.expander("### **View Parsed AML Response Values**", expanded=False):
        st.json(parsed_data)

    
    st.markdown("""
    <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>AML Response Assessment Result</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### **{response}**")

    st.markdown("#### Derivation Steps")
    with st.container():
        st.markdown("""
        <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; background-color: #f8f9fa;">
        """, unsafe_allow_html=True)
        derivation_text = "\n\n".join([f"**Step {i}**: {step}" for i, step in enumerate(derivation, start=1)])
        st.markdown(derivation_text)
        st.markdown("</div>", unsafe_allow_html=True)

def display_ipss_classification_results(
    parsed_fields: dict,
    ipssr_result: dict,
    ipssm_result: dict,
    show_parsed_fields: bool = False
):
    """
    Displays the IPSS risk stratification results (both IPSS-R and IPSS-M) in Streamlit.

    Args:
        parsed_fields (dict): The input data used for risk calculation.
        ipssr_result (dict): The result from compute_ipssr(), containing:
            - IPSSR_SCORE: Raw IPSS-R score.
            - IPSSR_CAT: Risk category.
            - IPSSRA_SCORE: Age-adjusted score (or None if not provided).
            - IPSSRA_CAT: Age-adjusted risk category.
            - derivation: A list of plain-language steps explaining the IPSS-R calculation.
        ipssm_result (dict): The result from compute_ipssm(), containing:
            - means: A dict with keys "riskScore", "riskCat", "contributions".
            - worst: A dict with keys "riskScore", "riskCat", "contributions".
            - best: A dict with keys "riskScore", "riskCat", "contributions".
            - derivation: A list of plain-language steps explaining the IPSS-M calculation.
        show_parsed_fields (bool): If True, an expander will show the parsed input data.
    """

    ##########################################
    # 1. Display Risk Scores Side-by-Side
    ##########################################
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **IPSS-R Risk Stratification**")
        st.markdown(f"**Risk Score:** {ipssr_result['IPSSR_SCORE']}")
        st.markdown(f"**Risk Category:** {ipssr_result['IPSSR_CAT']}")
        st.markdown(f"**Age-Adjusted Risk Score:** {ipssr_result['IPSSRA_SCORE'] if ipssr_result['IPSSRA_SCORE'] is not None else 'N/A'}")
        st.markdown(f"**Age-Adjusted Risk Category:** {ipssr_result['IPSSRA_CAT'] if ipssr_result['IPSSRA_CAT'] is not None else 'N/A'}")
    with col2:
        st.markdown("### **IPSS-M Risk Stratification**")
        st.markdown("#### Means Scenario")
        st.markdown(f"- **Risk Score:** {ipssm_result['means']['riskScore']}")
        st.markdown(f"- **Risk Category:** {ipssm_result['means']['riskCat']}")
        st.markdown("#### Worst Scenario")
        st.markdown(f"- **Risk Score:** {ipssm_result['worst']['riskScore']}")
        st.markdown(f"- **Risk Category:** {ipssm_result['worst']['riskCat']}")
        st.markdown("#### Best Scenario")
        st.markdown(f"- **Risk Score:** {ipssm_result['best']['riskScore']}")
        st.markdown(f"- **Risk Category:** {ipssm_result['best']['riskCat']}")

    ##########################################
    # 2. Display All Form Inputs
    ##########################################
    with st.expander("View All Form Inputs", expanded=False):
        st.markdown("### IPSS Input Data")
        st.markdown("Below is all the data that was used for IPSS risk calculation:")
        
        # Create a nicely formatted display of all inputs
        if parsed_fields:
            # Display clinical parameters first (most important for IPSS calculations)
            clinical_params = ["HB", "PLT", "ANC", "BM_BLAST", "AGE", "CYTO_IPSSR"]
            clinical_values = {k: v for k, v in parsed_fields.items() if k in clinical_params}
            
            if clinical_values:
                st.markdown("#### Clinical Parameters")
                param_descriptions = {
                    "HB": "Hemoglobin (g/dL)",
                    "PLT": "Platelets (10^9/L)",
                    "ANC": "Absolute Neutrophil Count (10^9/L)",
                    "BM_BLAST": "Bone Marrow Blasts (%)",
                    "AGE": "Age (years)",
                    "CYTO_IPSSR": "Cytogenetic Risk Category"
                }
                
                for key, value in clinical_values.items():
                    display_name = param_descriptions.get(key, key)
                    st.markdown(f"- **{display_name}**: {value}")
            
            # Display cytogenetic detail parameters
            cyto_params = ["del5q", "del7_7q", "del17_17p", "complex", "monosomy7"]
            cyto_values = {k: v for k, v in parsed_fields.items() if k in cyto_params}
            
            if cyto_values:
                st.markdown("#### Cytogenetic Details")
                for key, value in cyto_values.items():
                    formatted_key = key.replace("_", " ").replace("del", "Deletion ").title()
                    if value == 1:
                        display_value = "Present"
                    elif value == 0:
                        display_value = "Absent"
                    else:
                        display_value = value
                    st.markdown(f"- **{formatted_key}**: {display_value}")
            
            # Display TP53 parameters
            tp53_params = ["TP53mut", "TP53loh", "TP53maxvaf", "TP53multi"]
            tp53_values = {k: v for k, v in parsed_fields.items() if k in tp53_params}
            
            if tp53_values:
                st.markdown("#### TP53 Status")
                param_descriptions = {
                    "TP53mut": "TP53 Mutation Count",
                    "TP53loh": "TP53 Loss of Heterozygosity",
                    "TP53maxvaf": "TP53 Maximum Variant Allele Frequency",
                    "TP53multi": "TP53 Multiple Hits"
                }
                
                for key, value in tp53_values.items():
                    display_name = param_descriptions.get(key, key)
                    st.markdown(f"- **{display_name}**: {value}")
            
            # Display gene mutation parameters
            gene_params = [k for k in parsed_fields.keys() if k not in clinical_params + cyto_params + tp53_params and k not in ["__prompts"]]
            gene_values = {k: v for k, v in parsed_fields.items() if k in gene_params}
            
            if gene_values:
                st.markdown("#### Gene Mutations")
                for key, value in sorted(gene_values.items()):
                    if value == "1":
                        display_value = "Mutated"
                    elif value == "0":
                        display_value = "Not Mutated"
                    else:
                        display_value = value
                    st.markdown(f"- **{key}**: {display_value}")
        else:
            st.info("No input data available for display.")
 
    ##########################################
    # 3. Optionally, Show Parsed Input Fields
    ##########################################
    if show_parsed_fields:
        with st.expander("View Parsed IPSS Input", expanded=False):
            st.json(parsed_fields)

