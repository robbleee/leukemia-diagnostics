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
            
            # Mark the erythroid form as submitted in session state
            st.session_state["erythroid_form_submitted"] = True

            # Display the new classification results
            st.markdown(f"**Classification:** {new_class}")

def display_mds_confirmation_form(classification: str, disease_type: str, session_key: str):
    """
    If disease_type is 'MDS', display a form for confirming MDS diagnostic criteria:
      - Persistent cytopenia in at least one lineage for >4 months without clear alternative cause
      - Check for absolute exclusions of MDS diagnosis (persistent cytoses)

    Upon submission, the form disappears and displays appropriate warnings based on user selections.
    
    Args:
        classification (str): The current classification result
        disease_type (str): The disease type (MDS, AML, etc.)
        session_key (str): A unique key for storing the form's state in session (e.g., "mds_who_confirmation")
    """
    # This function is kept for backward compatibility but will redirect to the combined form
    # in the case where it's called directly
    st.warning("Please use the combined MDS confirmation form at the top of the page instead.")

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
    # Determine disease types
    ##########################################
    who_disease_type = "Unknown"
    if "aml_manual_result" in st.session_state:
        who_disease_type = st.session_state["aml_manual_result"].get("who_disease_type", "Unknown")
    elif "aml_ai_result" in st.session_state:
        who_disease_type = st.session_state["aml_ai_result"].get("who_disease_type", "Unknown")
    
    icc_disease_type = "Unknown"
    if "aml_manual_result" in st.session_state:
        icc_disease_type = st.session_state["aml_manual_result"].get("icc_disease_type", "Unknown")
    elif "aml_ai_result" in st.session_state:
        icc_disease_type = st.session_state["aml_ai_result"].get("icc_disease_type", "Unknown")
    
    # Determine if MDS confirmation form should be shown
    show_mds_form = who_disease_type == "MDS" or icc_disease_type == "MDS"
    mds_form_submitted = "mds_confirmation" in st.session_state and st.session_state["mds_confirmation"].get("submitted", False)
    
    ##########################################
    # Display single MDS confirmation form if applicable
    ##########################################
    if show_mds_form:
        session_key = "mds_confirmation"
        # Display the MDS confirmation form just once above the classification columns
        st.markdown("### **MDS Confirmation**")
        
        # Call a modified confirmation form that handles both classifications
        display_combined_mds_confirmation_form(
            who_classification=classification_who if who_disease_type == "MDS" else None,
            icc_classification=classification_icc if icc_disease_type == "MDS" else None,
            session_key=session_key
        )
    
    ##########################################
    # 1. Display WHO & ICC Classifications Side-by-Side
    # Only show classifications if:
    # - No MDS form is needed, OR
    # - MDS form has been submitted
    ##########################################
    if not show_mds_form or mds_form_submitted:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### **WHO 2022 Classification**")
            
            # If classification mentions erythroid, show the evaluation form
            if "erythroid" in classification_who.lower():
                display_erythroid_form_for_classification(classification_who, parsed_fields)
            else:
                # If we already showed the MDS form, just display the classification or modified classification
                if show_mds_form and who_disease_type == "MDS" and mds_form_submitted:
                    # Check if exclusions apply to this classification
                    if st.session_state["mds_confirmation"].get("has_exclusions", False):
                        st.markdown(f"**Classification:** Not MDS - consider other diagnostic pathways")
                    else:
                        st.markdown(f"**Classification:** {classification_who}")
                else:
                    # For non-MDS or if confirmation form is not submitted yet
                    st.markdown(f"**Classification:** {classification_who}")
                
        with col2:
            st.markdown("### **ICC 2022 Classification**")
            
            if "erythroid" in classification_icc.lower():
                display_erythroid_form_for_classification(classification_icc, parsed_fields)
            else:
                # If we already showed the MDS form, just display the classification or modified classification
                if show_mds_form and icc_disease_type == "MDS" and mds_form_submitted:
                    # Check if exclusions apply to this classification
                    if st.session_state["mds_confirmation"].get("has_exclusions", False):
                        st.markdown(f"**Classification:** Not MDS - consider other diagnostic pathways")
                    else:
                        st.markdown(f"**Classification:** {classification_icc}")
                else:
                    # For non-MDS or if confirmation form is not submitted yet
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

def display_combined_mds_confirmation_form(who_classification, icc_classification, session_key):
    """
    Displays a single MDS confirmation form that applies to both WHO and ICC classifications.
    
    Args:
        who_classification (str): WHO 2022 classification result (or None if not MDS)
        icc_classification (str): ICC 2022 classification result (or None if not MDS)
        session_key (str): A unique key for storing the form's state in session
    """
    # Get parsed data from session state
    parsed_data = None
    if "aml_manual_result" in st.session_state:
        parsed_data = st.session_state["aml_manual_result"].get("parsed_data", {})
    elif "aml_ai_result" in st.session_state:
        parsed_data = st.session_state["aml_ai_result"].get("parsed_data", {})
    
    # Check for cytogenetic exceptions in the parsed data
    has_del5q = False
    has_inv3_t33 = False
    
    if parsed_data and "MDS_related_cytogenetics" in parsed_data:
        has_del5q = parsed_data["MDS_related_cytogenetics"].get("del_5q", False)
        has_inv3_t33 = parsed_data["MDS_related_cytogenetics"].get("inv3_t33", False)
    
    # Check for MDS-defining cytogenetic changes
    has_mds_defining_cytogenetics = False
    has_minus_7 = False
    has_del_7q = False
    has_complex_karyotype = False
    
    if parsed_data and "MDS_related_cytogenetics" in parsed_data:
        has_del5q = parsed_data["MDS_related_cytogenetics"].get("del_5q", False)
        has_minus_7 = parsed_data["MDS_related_cytogenetics"].get("-7", False)
        has_del_7q = parsed_data["MDS_related_cytogenetics"].get("del_7q", False)
        has_complex_karyotype = parsed_data["MDS_related_cytogenetics"].get("Complex_karyotype", False)
    
    # Check for MDS-defining genetic changes
    has_sf3b1 = False
    has_multi_hit_tp53 = False
    
    if parsed_data:
        if "MDS_related_mutation" in parsed_data:
            has_sf3b1 = parsed_data["MDS_related_mutation"].get("SF3B1", False)
        
        if "Biallelic_TP53_mutation" in parsed_data:
            has_multi_hit_tp53 = (
                parsed_data["Biallelic_TP53_mutation"].get("2_x_TP53_mutations", False) or
                parsed_data["Biallelic_TP53_mutation"].get("1_x_TP53_mutation_del_17p", False) or
                parsed_data["Biallelic_TP53_mutation"].get("1_x_TP53_mutation_LOH", False) or
                parsed_data["Biallelic_TP53_mutation"].get("1_x_TP53_mutation_10_percent_vaf", False) or
                parsed_data["Biallelic_TP53_mutation"].get("1_x_TP53_mutation_50_percent_vaf", False)
            )
    
    # Determine if any MDS-defining genetic/cytogenetic changes are present
    has_mds_defining_genetic_cytogenetic = (
        has_del5q or has_minus_7 or has_del_7q or has_complex_karyotype or
        has_sf3b1 or has_multi_hit_tp53
    )
    
    # Check for eosinophilia-related gene rearrangements
    eosinophilia_rearrangements = []
    
    if parsed_data:
        # Check AML_defining_recurrent_genetic_abnormalities
        if "AML_defining_recurrent_genetic_abnormalities" in parsed_data:
            if parsed_data["AML_defining_recurrent_genetic_abnormalities"].get("FIP1L1::PDGFRA", False):
                eosinophilia_rearrangements.append("FIP1L1::PDGFRA")
            if parsed_data["AML_defining_recurrent_genetic_abnormalities"].get("ETV6::ABL1", False):
                eosinophilia_rearrangements.append("ETV6::ABL1")
            if parsed_data["AML_defining_recurrent_genetic_abnormalities"].get("ETV6::SYK", False):
                eosinophilia_rearrangements.append("ETV6::SYK")
            if parsed_data["AML_defining_recurrent_genetic_abnormalities"].get("FGR1", False):
                eosinophilia_rearrangements.append("FGR1")
            if parsed_data["AML_defining_recurrent_genetic_abnormalities"].get("FLT3", False):
                eosinophilia_rearrangements.append("FLT3")
        
        # Check for JAK2 in MDS_related_mutation
        if "MDS_related_mutation" in parsed_data and parsed_data["MDS_related_mutation"].get("JAK2", False):
            eosinophilia_rearrangements.append("JAK2")
    
    # Create a flag for whether eosinophilia is an absolute exclusion
    has_eosinophilia_rearrangements = len(eosinophilia_rearrangements) > 0
    
    # Initialize session state for this specific form if not already present
    if session_key not in st.session_state:
        st.session_state[session_key] = {
            "cytopenia_confirmed": False,
            "morphological_dysplasia": False,
            "wbc_cytosis": False,
            "eosinophil_cytosis": False,
            "monocyte_cytosis": False,
            "platelet_cytosis": False,
            "submitted": False,
            "has_exclusions": False
        }
    
    # Show classification info only if the form hasn't been submitted yet
    if not st.session_state[session_key].get("submitted", False):
        st.markdown("#### Classifications under review:")
        if who_classification:
            st.markdown(f"- **WHO 2022:** {who_classification}")
        if icc_classification:
            st.markdown(f"- **ICC 2022:** {icc_classification}")
    
    # If the form has already been submitted, just display the results
    if st.session_state[session_key].get("submitted", False):
        # Get form data
        cytopenia_confirmed = st.session_state[session_key].get("cytopenia_confirmed", False)
        morphological_dysplasia = st.session_state[session_key].get("morphological_dysplasia", False)
        wbc_cytosis = st.session_state[session_key].get("wbc_cytosis", False)
        monocyte_cytosis = st.session_state[session_key].get("monocyte_cytosis", False)
        platelet_cytosis = st.session_state[session_key].get("platelet_cytosis", False)
        eosinophil_cytosis = st.session_state[session_key].get("eosinophil_cytosis", False)
        
        # Check if any exclusions apply
        has_exclusions = False
        
        # Evaluate all possible exclusion conditions
        if not cytopenia_confirmed:
            has_exclusions = True
        
        # Check if MDS-defining features are present (either morphological dysplasia or specific genetic/cytogenetic changes)
        has_mds_defining_features = morphological_dysplasia or has_mds_defining_genetic_cytogenetic
        if not has_mds_defining_features:
            has_exclusions = True
        
        if wbc_cytosis:
            has_exclusions = True
        
        if monocyte_cytosis:
            has_exclusions = True
        
        if platelet_cytosis and not (has_del5q or has_inv3_t33):
            has_exclusions = True
        
        if eosinophil_cytosis and has_eosinophilia_rearrangements:
            has_exclusions = True
        
        # Store exclusion result in session state
        st.session_state[session_key]["has_exclusions"] = has_exclusions
        
        # Display warnings based on form data
        if not cytopenia_confirmed:
            st.warning("⚠️ **MDS Diagnostic Criteria Not Met**: Persistent cytopenia (>4 months) in at least one lineage without alternative cause is required for MDS diagnosis.", icon="⚠️")
        
        # Warning if no MDS-defining features are present
        if not has_mds_defining_features:
            st.warning("⚠️ **MDS Diagnostic Criteria Not Met**: At least one MDS-defining feature must be present - either morphologically defined dysplasia or specific genetic/cytogenetic changes (del 5q-, -7, del 7q, complex karyotype, SF3B1 mutation, or multi-hit TP53).", icon="⚠️")
        
        # Cytoses warnings based on whether exceptions apply
        has_cytosis = wbc_cytosis or monocyte_cytosis or platelet_cytosis or eosinophil_cytosis
        
        if has_cytosis:
            if platelet_cytosis and (has_del5q or has_inv3_t33):
                st.warning("⚠️ **EXCEPTION APPLIES**: Thrombocytosis with del(5q) or inv(3)/t(3;3) can still be classified as MDS, but consideration of a myeloproliferative pathway is recommended.", icon="⚠️")
                
                # Add a new message to explicitly state we're allowing MDS diagnosis despite thrombocytosis
                st.info(f"ℹ️ **MDS Diagnosis Allowed**: Despite thrombocytosis ≥ 450 × 10^9/L being present, MDS diagnosis is still permitted due to the presence of {' and '.join([x for x in ['del(5q)' if has_del5q else '', 'inv(3)/t(3;3)' if has_inv3_t33 else ''] if x])} cytogenetic abnormality. This is a recognized exception to the absolute exclusion rule.", icon="ℹ️")
            elif eosinophil_cytosis and has_eosinophilia_rearrangements:
                st.error(f"❌ **ABSOLUTE EXCLUSION - EOSINOPHILIA WITH GENE REARRANGEMENTS**: Eosinophilia with {', '.join(eosinophilia_rearrangements)} detected. This excludes MDS diagnosis. Consider 'myeloid/lymphoid neoplasms with eosinophilia and tyrosine kinase gene fusions'.", icon="❌")
            else:
                # General cytoses exclusion
                exclusion_list = []
                if wbc_cytosis:
                    exclusion_list.append("WBC > 13 × 10^9/L (requires MPN pathway)")
                if monocyte_cytosis:
                    exclusion_list.append("Monocytosis ≥ 10% and ≥ 0.5 × 10^9/L (requires CMML pathway)")
                if platelet_cytosis and not (has_del5q or has_inv3_t33):
                    exclusion_list.append("Thrombocytosis ≥ 450 × 10^9/L (requires consideration of MPN pathway)")
                # Only add eosinophilia to exclusion list if specific rearrangements are present
                if eosinophil_cytosis and has_eosinophilia_rearrangements:
                    exclusion_list.append(f"Eosinophilia > 0.5 × 10^9/L with {', '.join(eosinophilia_rearrangements)} (requires consideration of myeloid/lymphoid neoplasms with eosinophilia)")
                
                if exclusion_list:
                    st.error(f"❌ **ABSOLUTE EXCLUSION - PERSISTENT CYTOSES**: The following unexplained cytoses exclude MDS diagnosis: {', '.join(exclusion_list)}", icon="❌")
    else:
        # Create a placeholder to hold the form
        form_placeholder = st.empty()
        
        with form_placeholder.form(f"{session_key}_form"):
            st.markdown(
                "<h4 style='margin-bottom: 0px;'>MDS Diagnostic Criteria & Exclusions</h4>",
                unsafe_allow_html=True
            )
            
            # Cytopenia confirmation checkbox
            cytopenia_confirmed = st.checkbox(
                "Confirm persistent cytopenia in at least one lineage for >4 months without clear alternative cause",
                value=st.session_state[session_key].get("cytopenia_confirmed", False),
                help="Cytopenia must be persistent and not explained by other conditions such as vitamin deficiency, drug effect, or other disease."
            )
            
            # Morphological dysplasia checkbox
            st.markdown("##### MDS-Defining Features (at least one required)")
            
            # Display info on which genetic/cytogenetic changes are already detected
            if has_mds_defining_genetic_cytogenetic:
                mds_defining_changes = []
                if has_del5q:
                    mds_defining_changes.append("del(5q)")
                if has_minus_7:
                    mds_defining_changes.append("-7")
                if has_del_7q:
                    mds_defining_changes.append("del(7q)")
                if has_complex_karyotype:
                    mds_defining_changes.append("complex karyotype")
                if has_sf3b1:
                    mds_defining_changes.append("SF3B1 mutation")
                if has_multi_hit_tp53:
                    mds_defining_changes.append("multi-hit TP53")
                
                st.info(f"ℹ️ MDS-defining genetic/cytogenetic changes detected: {', '.join(mds_defining_changes)}", icon="ℹ️")
            
            # Add checkbox for morphological dysplasia
            morphological_dysplasia = st.checkbox(
                "Please confirm that morphological criteria for dysplasia are met: at least 10% cells of at least one lineage have significant dysplastic features and no alternative cause for dysplasia is present",
                value=st.session_state[session_key].get("morphological_dysplasia", False),
                help="Dysplasia must be significant and affect at least 10% of cells in at least one lineage, with no alternative explanation."
            )
            
            # Cytoses assessment using individual checkboxes
            st.markdown("##### Persistent Cytoses (unexplained by other conditions)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                wbc_cytosis = st.checkbox(
                    "WBC > 13 × 10^9/L",
                    value=st.session_state[session_key].get("wbc_cytosis", False),
                    help="Any WBC > 13 × 10^9/L that cannot be explained by other conditions excludes MDS and requires a myeloproliferative neoplasm (MPN) pathway."
                )
                
                eosinophil_cytosis = st.checkbox(
                    "Eosinophilia > 0.5 × 10^9/L",
                    value=st.session_state[session_key].get("eosinophil_cytosis", False),
                    help="Eosinophilia excludes MDS diagnosis only when specific gene rearrangements are present."
                )
            
            with col2:
                monocyte_cytosis = st.checkbox(
                    "Monocytosis ≥ 10% and ≥ 0.5 × 10^9/L",
                    value=st.session_state[session_key].get("monocyte_cytosis", False),
                    help="Monocytosis excludes MDS diagnosis and requires consideration of chronic myelomonocytic leukemia (CMML)."
                )
                
                platelet_cytosis = st.checkbox(
                    "Thrombocytosis ≥ 450 × 10^9/L",
                    value=st.session_state[session_key].get("platelet_cytosis", False),
                    help="Thrombocytosis usually excludes MDS diagnosis except when del(5q) or inv(3)/t(3;3) is present."
                )
            
            # If eosinophilia is checked, display info about detected gene rearrangements
            if eosinophil_cytosis or st.session_state[session_key].get("eosinophil_cytosis", False):
                if has_eosinophilia_rearrangements:
                    st.error(f"⚠️ {', '.join(eosinophilia_rearrangements)} detected. If eosinophilia is present, this EXCLUDES MDS diagnosis and requires consideration of 'myeloid/lymphoid neoplasms with eosinophilia and tyrosine kinase gene fusions'.", icon="⚠️")
                else:
                    st.info("ℹ️ No eosinophilia-related gene rearrangements detected. Eosinophilia alone is not an absolute exclusion for MDS diagnosis.", icon="ℹ️")
            
            submit = st.form_submit_button("Confirm MDS Criteria")
        
        if submit:
            # Remove the form from the interface
            form_placeholder.empty()
            
            # Store form data in session state
            st.session_state[session_key] = {
                "cytopenia_confirmed": cytopenia_confirmed,
                "morphological_dysplasia": morphological_dysplasia,
                "wbc_cytosis": wbc_cytosis,
                "eosinophil_cytosis": eosinophil_cytosis,
                "monocyte_cytosis": monocyte_cytosis,
                "platelet_cytosis": platelet_cytosis,
                "submitted": True
            }
            
            # Check if any exclusions apply
            has_exclusions = False
            
            # Evaluate all possible exclusion conditions
            if not cytopenia_confirmed:
                has_exclusions = True
            
            # Check if MDS-defining features are present (either morphological dysplasia or specific genetic/cytogenetic changes)
            has_mds_defining_features = False
            if st.session_state[session_key].get("morphological_dysplasia", False):
                has_mds_defining_features = True
            if has_mds_defining_genetic_cytogenetic:
                has_mds_defining_features = True
            
            if not has_mds_defining_features:
                has_exclusions = True
            
            if wbc_cytosis:
                has_exclusions = True
            
            if monocyte_cytosis:
                has_exclusions = True
            
            if platelet_cytosis and not (has_del5q or has_inv3_t33):
                has_exclusions = True
            
            if eosinophil_cytosis and has_eosinophilia_rearrangements:
                has_exclusions = True
            
            # Store exclusion result in session state
            st.session_state[session_key]["has_exclusions"] = has_exclusions
            
            # Update derivations in the main session state with MDS confirmation information
            _update_session_state_derivations_with_mds_confirmation(st.session_state[session_key])
            
            # Refresh the page to show the results
            st.rerun()

def _update_session_state_derivations_with_mds_confirmation(mds_confirmation: dict):
    """
    Update the derivations in session state with MDS confirmation information.
    
    Args:
        mds_confirmation (dict): MDS confirmation form data
    """
    # Generate the MDS confirmation derivation steps
    confirmation_steps = _generate_mds_confirmation_derivation_steps(mds_confirmation)
    
    # Update AML results if they exist and contain MDS classifications
    if "aml_manual_result" in st.session_state:
        data = st.session_state["aml_manual_result"]
        who_is_mds = "MDS" in (data.get("who_class", "") or "")
        icc_is_mds = "MDS" in (data.get("icc_class", "") or "")
        
        if who_is_mds:
            st.session_state["aml_manual_result"]["who_derivation"].extend(confirmation_steps)
            if mds_confirmation.get("has_exclusions", False):
                st.session_state["aml_manual_result"]["who_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            else:
                st.session_state["aml_manual_result"]["who_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
        
        if icc_is_mds:
            st.session_state["aml_manual_result"]["icc_derivation"].extend(confirmation_steps)
            if mds_confirmation.get("has_exclusions", False):
                st.session_state["aml_manual_result"]["icc_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            else:
                st.session_state["aml_manual_result"]["icc_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
    
    elif "aml_ai_result" in st.session_state:
        data = st.session_state["aml_ai_result"]
        who_is_mds = "MDS" in (data.get("who_class", "") or "")
        icc_is_mds = "MDS" in (data.get("icc_class", "") or "")
        
        if who_is_mds:
            st.session_state["aml_ai_result"]["who_derivation"].extend(confirmation_steps)
            if mds_confirmation.get("has_exclusions", False):
                st.session_state["aml_ai_result"]["who_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            else:
                st.session_state["aml_ai_result"]["who_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
        
        if icc_is_mds:
            st.session_state["aml_ai_result"]["icc_derivation"].extend(confirmation_steps)
            if mds_confirmation.get("has_exclusions", False):
                st.session_state["aml_ai_result"]["icc_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            else:
                st.session_state["aml_ai_result"]["icc_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
    
    # Update MDS results if they exist
    if "mds_manual_result" in st.session_state:
        st.session_state["mds_manual_result"]["who_derivation"].extend(confirmation_steps)
        st.session_state["mds_manual_result"]["icc_derivation"].extend(confirmation_steps)
        if mds_confirmation.get("has_exclusions", False):
            st.session_state["mds_manual_result"]["who_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            st.session_state["mds_manual_result"]["icc_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
        else:
            st.session_state["mds_manual_result"]["who_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
            st.session_state["mds_manual_result"]["icc_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
    
    elif "mds_ai_result" in st.session_state:
        st.session_state["mds_ai_result"]["who_derivation"].extend(confirmation_steps)
        st.session_state["mds_ai_result"]["icc_derivation"].extend(confirmation_steps)
        if mds_confirmation.get("has_exclusions", False):
            st.session_state["mds_ai_result"]["who_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
            st.session_state["mds_ai_result"]["icc_derivation"].append("Final result: MDS diagnosis excluded due to above criteria.")
        else:
            st.session_state["mds_ai_result"]["who_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")
            st.session_state["mds_ai_result"]["icc_derivation"].append("Final result: MDS diagnosis confirmed by clinical review.")

def _generate_mds_confirmation_derivation_steps(mds_confirmation: dict) -> list:
    """
    Generate derivation steps based on MDS confirmation form results.
    
    Args:
        mds_confirmation (dict): MDS confirmation form data from session state
        
    Returns:
        list: List of derivation step strings describing the confirmation process
    """
    steps = []
    
    # Add header for MDS confirmation review
    steps.append("MDS Diagnostic Criteria Review:")
    
    # Check cytopenia confirmation
    cytopenia_confirmed = mds_confirmation.get("cytopenia_confirmed", False)
    if cytopenia_confirmed:
        steps.append("✓ Persistent cytopenia (>4 months) in at least one lineage confirmed")
    else:
        steps.append("✗ Persistent cytopenia requirement NOT met - lacking cytopenia >4 months without alternative cause")
    
    # Check morphological dysplasia
    morphological_dysplasia = mds_confirmation.get("morphological_dysplasia", False)
    if morphological_dysplasia:
        steps.append("✓ Morphologically defined dysplasia confirmed")
    else:
        steps.append("✗ Morphologically defined dysplasia NOT confirmed")
    
    # Check for cytoses
    wbc_cytosis = mds_confirmation.get("wbc_cytosis", False)
    monocyte_cytosis = mds_confirmation.get("monocyte_cytosis", False)
    platelet_cytosis = mds_confirmation.get("platelet_cytosis", False)
    eosinophil_cytosis = mds_confirmation.get("eosinophil_cytosis", False)
    
    cytoses = []
    if wbc_cytosis:
        cytoses.append("WBC > 13 × 10^9/L")
    if monocyte_cytosis:
        cytoses.append("Monocytosis ≥ 10% and ≥ 0.5 × 10^9/L")
    if platelet_cytosis:
        cytoses.append("Thrombocytosis ≥ 450 × 10^9/L")
    if eosinophil_cytosis:
        cytoses.append("Eosinophilia > 0.5 × 10^9/L")
    
    if cytoses:
        steps.append(f"✗ Exclusionary cytoses present: {', '.join(cytoses)}")
    else:
        steps.append("✓ No exclusionary cytoses detected")
    
    return steps

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

