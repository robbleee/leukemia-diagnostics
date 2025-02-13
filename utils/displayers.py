import streamlit as st

##################################
# CLASSIFICATION DISPLAY HELPERS
##################################
def display_aml_classification_results(
    parsed_fields,
    classification_who,
    who_derivation,
    classification_icc,
    icc_derivation,
    mode="manual",
    show_parsed_fields: bool = False
):
    """
    Displays AML classification results in Streamlit.

    Args:
        parsed_fields (dict): The raw parsed data values (if you wish to show them).
        classification_who (str): WHO 2022 classification result.
        who_derivation (list): Step-by-step derivation for WHO 2022.
        classification_icc (str): ICC 2022 classification result.
        icc_derivation (list): Step-by-step derivation for ICC 2022.
        mode (str): Typically 'manual' or whatever mode your app uses.
        show_parsed_fields (bool): Whether to show the "View Parsed AML Values" expander.
    """



    ##########################################
    # 3. Display WHO & ICC Classifications Side-by-Side
    ##########################################
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **WHO 2022 Classification**")
        st.markdown(f"**Classification:** {classification_who}")
    with col2:
        st.markdown("### **ICC 2022 Classification**")
        st.markdown(f"**Classification:** {classification_icc}")

    ##########################################
    # 4. Display Derivations Side-by-Side
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
    # 1. (Optional) Show JSON of parsed fields
    ##########################################
    if show_parsed_fields:
        with st.expander("View Parsed AML Values", expanded=False):
            st.json(parsed_fields)

def display_mds_classification_results(parsed_fields, classification_who, derivation_who,
                                       classification_icc, derivation_icc, mode="manual"):
    """
    Displays MDS classification results WITHOUT automatically calling the AI review.
    """
    with st.expander("View Parsed MDS Values", expanded=False):
        st.json(parsed_fields)
    




    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **WHO 2022 Classification**")
        st.write(classification_who)
    with col2:
        st.markdown("### **ICC 2022 Classification**")
        st.write(classification_icc)

    col_who, col_icc = st.columns(2)
    with col_who:
        with st.expander("🔍 WHO 2022 Derivation", expanded=False):
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_who, start=1)]
            )
            st.markdown(derivation_text)
    with col_icc:
        with st.expander("🔍 ICC 2022 Derivation", expanded=False):
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_icc, start=1)]
            )
            st.markdown(derivation_text)
   
def display_aml_response_results(parsed_data, response, derivation, mode="manual"):
    with st.expander("### **View Parsed AML Response Values**", expanded=False):
        st.json(parsed_data)

    
    st.markdown("""
    <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>AML Response Assessment Result</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### **{response}**")

    with st.expander("🔍 Derivation Steps", expanded=False):
        derivation_text = "\n\n".join([f"**Step {i}**: {step}" for i, step in enumerate(derivation, start=1)])
        st.markdown(derivation_text)

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
    # 2. Display Derivation Logs Side-by-Side
    ##########################################
    st.markdown("## Detailed Derivation")
    col3, col4 = st.columns(2)
    with col3:
        with st.expander("View IPSS-R Derivation", expanded=False):
            ipssr_deriv = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(ipssr_result.get("derivation", []), start=1)]
            )
            st.markdown(ipssr_deriv)
    with col4:
        with st.expander("View IPSS-M Derivation", expanded=False):
            ipssm_deriv = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(ipssm_result.get("derivation", []), start=1)]
            )
            st.markdown(ipssm_deriv)

    ##########################################
    # 3. Optionally, Show Parsed Input Fields
    ##########################################
    if show_parsed_fields:
        with st.expander("View Parsed IPSS Input", expanded=False):
            st.json(parsed_fields)

