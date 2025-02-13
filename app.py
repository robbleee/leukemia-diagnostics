import streamlit as st
import bcrypt
import json
import datetime
from openai import OpenAI
from streamlit_option_menu import option_menu
from fpdf import FPDF
import re
import base64
import streamlit.components.v1 as components 


from parsers.aml_parser import parse_genetics_report_aml
from parsers.aml_response_parser import parse_aml_response_report
from parsers.mds_parser import parse_genetics_report_mds
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022
from classifiers.aml_risk_classifier import classify_ELN2022
from classifiers.ipss_classifiers import ( 
    compute_ipssr, 
    compute_ipssm, 
    betas, 
    IPSSR_CATEGORIES, 
    IPSSM_CATEGORIES, 
    CYTO_IPSSR_MAP, 
    VARIABLE_CONFIG
)
from reviewers.aml_reviewer import (
    get_gpt4_review_aml_classification,
    get_gpt4_review_aml_genes,
    get_gpt4_review_aml_additional_comments,
    get_gpt4_review_aml_mrd
)
from reviewers.mds_reviewer import (
    get_gpt4_review_mds_classification,
    get_gpt4_review_mds_genes,
    get_gpt4_review_mds_additional_comments
)
from utils.pdf import (
    clean_text,
    write_line_with_keywords,
    output_review_text,
    PDF,
    add_section_title,
    add_classification_section,
    add_risk_section,
    add_diagnostic_section,
    create_beautiful_pdf
)
from utils.forms import (
    build_manual_aml_data,
    build_manual_mds_data_compact,
    build_manual_aml_response_data,
    build_manual_ipss_data
)
from utils.displayers import (
    display_aml_classification_results,
    display_mds_classification_results,
    display_aml_response_results,
    display_ipss_classification_results
)


##################################
# PAGE CONFIG
##################################
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""

if st.session_state["authenticated"]:
    st.set_page_config(
        page_title="Haematologic Classification",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
else:
    st.set_page_config(
        page_title="Haematologic Classification",
        layout="centered",
        initial_sidebar_state="expanded"
    )


##################################
# CUSTOM CSS
##################################
def local_css():
    st.markdown(
        """
        <style>
        /* Toggle Switch Styles */
        .toggle-switch {
            display: flex;
            align-items: center;
            font-size: 18px;
            font-weight: bold;
        }

        .toggle-switch input {
            display: none;
        }

        .toggle-switch-label {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
            margin-right: 10px;
        }

        /* Updated the checked background to teal (#009688) */
        .toggle-switch-label input:checked + span {
            background-color: #009688;
        }

        /* Moves toggle circle on check */
        .toggle-switch-label input:checked + span:before {
            transform: translateX(26px);
        }

        .toggle-switch-label span {
            position: absolute;
            cursor: pointer;
            background-color: #ccc; /* Unchecked color */
            border-radius: 34px;
            top: 0; left: 0; right: 0; bottom: 0;
            transition: 0.4s;
        }

        .toggle-switch-label span:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px; bottom: 4px;
            background-color: white;
            border-radius: 50%;
            transition: 0.4s;
        }

        /* Increase tab text size (only relevant if you still use st.tabs) */
        div[data-baseweb="tabs"] > div > div {
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def add_custom_css():
    st.markdown(
        """
        <style>
        /* Buttons with a teal outline */
        .stButton > button {
            background-color: white;
            color: #009688; /* Teal text */
            border: 2px solid #009688; /* Teal outline */
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }

        .stButton > button:hover {
            background-color: #E0F2F1; /* Light pastel teal on hover */
            color: #00695C;           /* Slightly darker teal text on hover */
            border-color: #00695C;    /* Darker teal outline on hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

local_css()
add_custom_css()


##################################
# AUTH FUNCTIONS
##################################
def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def authenticate_user(username: str, password: str) -> bool:
    users = st.secrets["auth"]["users"]
    for user in users:
        if user["username"] == username:
            return verify_password(user["hashed_password"], password)
    return False

##################################
# LOGIN PAGE (Main Area)
##################################
def show_login_page():
    st.title("Diagnosis Support Tool")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password!")

##################################
# APP MAIN
##################################
def app_main():
    # Initialize expander and section state variables if not present.
    if "expanded_aml_section" not in st.session_state:
        st.session_state["expanded_aml_section"] = None
    if "expanded_mds_section" not in st.session_state:
        st.session_state["expanded_mds_section"] = None
    if "expanded_mds_risk_section" not in st.session_state:
        st.session_state["expanded_mds_risk_section"] = None

    # Session state for free-text expander visibility.
    if "aml_free_text_expanded" not in st.session_state:
        st.session_state["aml_free_text_expanded"] = True
    if "mds_free_text_expanded" not in st.session_state:
        st.session_state["mds_free_text_expanded"] = True
    if "mds_risk_free_text_expanded" not in st.session_state:
        st.session_state["mds_risk_free_text_expanded"] = True

    if st.session_state.get("authenticated", False):


        st.markdown(
            """
            <div style="
                background-color: #FFFFFF;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 20px;
                ">
                <h2 style="color: #009688; text-align: left;">
                    AML/MDS Diagnostic Support Tool
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Toggle switch for 'Free Text Mode'
        aml_mode_toggle = st.toggle("Free Text Mode", key="aml_mode_toggle", value=True)

        if "aml_busy" not in st.session_state:
            st.session_state["aml_busy"] = False

        # --- MANUAL MODE ---
        if not aml_mode_toggle:
            manual_data = build_manual_aml_data()
            if st.button("Analyse Genetics"):
                st.session_state["aml_busy"] = True
                with st.spinner("Compiling results. Please wait..."):
                    # Clear old AML keys.
                    for key in [
                        "aml_manual_result",
                        "aml_ai_result",
                        "aml_class_review",
                        "aml_mrd_review",
                        "aml_gene_review",
                        "aml_additional_comments"
                    ]:
                        st.session_state.pop(key, None)

                    # Classify using dummy functions.
                    classification_who, who_derivation = classify_combined_WHO2022(manual_data)
                    classification_icc, icc_derivation = classify_combined_ICC2022(manual_data)
                    classification_eln, eln_derivation = classify_ELN2022(manual_data)

                    st.session_state["aml_manual_result"] = {
                        "parsed_data": manual_data,
                        "who_class": classification_who,
                        "who_derivation": who_derivation,
                        "icc_class": classification_icc,
                        "icc_derivation": icc_derivation,
                        "eln_class": classification_eln,
                        "eln_derivation": eln_derivation,
                    }
                    st.session_state["expanded_aml_section"] = "classification"
                st.session_state["aml_busy"] = False

        # --- FREE TEXT MODE ---
        else:
            with st.expander("Free Text Input Area", expanded=st.session_state.get("aml_free_text_expanded", True)):
                full_report = st.text_area(
                    "Paste all relevant AML/MDS data here (Blast % is required; everything else is optional):",
                    placeholder=(
                        "Include the blast percentage (mandatory) and any other details you have: "
                        "e.g., AML differentiation, morphology/clinical info, genetics, cytogenetics, etc."
                    ),
                    key="full_text_input",
                    height=200
                )



            if st.button("Analyse Report"):
                # Collapse the free text input area.
                st.session_state["aml_free_text_expanded"] = False

                for key in [
                    "aml_manual_result",
                    "aml_ai_result",
                    "aml_class_review",
                    "aml_mrd_review",
                    "aml_gene_review",
                    "aml_additional_comments"
                ]:
                    st.session_state.pop(key, None)

                full_report_text = st.session_state.get("full_text_input", "")

                if full_report_text.strip():
                    with st.spinner("Parsing & classifying ..."):
                        parsed_data = parse_genetics_report_aml(full_report_text)
                        who_class, who_deriv = classify_combined_WHO2022(parsed_data)
                        icc_class, icc_deriv = classify_combined_ICC2022(parsed_data)
                        eln_class, eln_deriv = classify_ELN2022(parsed_data)

                        st.session_state["aml_ai_result"] = {
                            "parsed_data": parsed_data,
                            "who_class": who_class,
                            "who_derivation": who_deriv,
                            "icc_class": icc_class,
                            "icc_derivation": icc_deriv,
                            "eln_class": eln_class,
                            "eln_derivation": eln_deriv,
                            "free_text_input": full_report_text
                        }
                        st.session_state["expanded_aml_section"] = "classification"
                else:
                    st.error("No AML data provided.")

        # --- If AML results exist, show sub-menu ---
        if "aml_manual_result" in st.session_state or "aml_ai_result" in st.session_state:

            # Priority: manual results take precedence over AI results.
            if "aml_manual_result" in st.session_state:
                res = st.session_state["aml_manual_result"]
                mode = "manual"
            else:
                res = st.session_state["aml_ai_result"]
                mode = "ai"

            classification_dict = {
                "WHO 2022": {
                    "Classification": res["who_class"],
                    "Derivation": res["who_derivation"]
                },
                "ICC 2022": {
                    "Classification": res["icc_class"],
                    "Derivation": res["icc_derivation"]
                }
            }

            free_text_input_value = res.get("free_text_input") if mode == "ai" else None

            sub_tab = option_menu(
                menu_title=None,
                options=["Classification", "Risk", "MRD Review", "Gene Review", "Additional Comments"],
                icons=["clipboard", "graph-up-arrow", "recycle", "bar-chart", "chat-left-text"],
                default_index=0,
                orientation="horizontal"
            )

            if sub_tab == "Classification":
                display_aml_classification_results(
                    res["parsed_data"],
                    res["who_class"],
                    res["who_derivation"],
                    res["icc_class"],
                    res["icc_derivation"],
                    mode=mode
                )

                if "aml_class_review" not in st.session_state:
                    with st.spinner("Generating Classification Review..."):
                        st.session_state["aml_class_review"] = get_gpt4_review_aml_classification(
                            classification_dict,
                            res["parsed_data"],
                            free_text_input=free_text_input_value
                        )

                st.markdown("### Classification Review")
                st.markdown(st.session_state["aml_class_review"])

            elif sub_tab == "MRD Review":
                if "aml_mrd_review" not in st.session_state:
                    with st.spinner("Generating MRD Review..."):
                        st.session_state["aml_mrd_review"] = get_gpt4_review_aml_mrd(
                            classification_dict,
                            res["parsed_data"],
                            free_text_input=free_text_input_value
                        )
                with st.expander("MRD Review", expanded=True):
                    st.markdown(st.session_state["aml_mrd_review"])

            elif sub_tab == "Gene Review":
                if "aml_gene_review" not in st.session_state:
                    with st.spinner("Generating Gene Review..."):
                        st.session_state["aml_gene_review"] = get_gpt4_review_aml_genes(
                            classification_dict,
                            res["parsed_data"],
                            free_text_input=free_text_input_value
                        )
                with st.expander("Gene Review", expanded=True):
                    st.markdown(st.session_state["aml_gene_review"])

            elif sub_tab == "Additional Comments":
                if "aml_additional_comments" not in st.session_state:
                    with st.spinner("Generating Additional Comments..."):
                        st.session_state["aml_additional_comments"] = get_gpt4_review_aml_additional_comments(
                            classification_dict,
                            res["parsed_data"],
                            free_text_input=free_text_input_value
                        )
                with st.expander("Additional Comments", expanded=True):
                    st.markdown(st.session_state["aml_additional_comments"])

            elif sub_tab == "Risk":
                st.markdown("### ELN 2022 Risk Classification")
                st.markdown(f"**Risk Category:** {res['eln_class']}")
                with st.expander("ELN Derivation", expanded=True):
                    for i, step in enumerate(res["eln_derivation"], start=1):
                        st.markdown(f"- {step}")

            if "show_pdf_form" not in st.session_state:
                st.session_state.show_pdf_form = False
            if st.button("Download Report"):
                st.session_state.show_pdf_form = True
            if st.session_state.show_pdf_form:
                with st.form(key="pdf_info_form"):
                    patient_name = st.text_input("Enter Patient Name:")
                    patient_dob = st.date_input("Enter Date of Birth:")
                    submit_pdf = st.form_submit_button("Submit")
                if submit_pdf:
                    if not patient_name:
                        st.error("Please enter the patient name.")
                    else:
                        pdf_bytes = create_beautiful_pdf(patient_name, patient_dob)
                        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                        download_html = f'''
                            <a id="pdf_download" href="data:application/pdf;base64,{pdf_base64}" download="diagnostic_report.pdf"></a>
                            <script>
                                setTimeout(function() {{
                                    document.getElementById("pdf_download").click();
                                }}, 100);
                            </script>
                        '''
                        components.html(download_html, height=0)
                        st.session_state.show_pdf_form = False


    else:
        st.info("🔒 **Log in** to use the classification features.")

##################################
# Main Execution
##################################
if __name__ == "__main__":
    if st.session_state.get("authenticated", False):
        app_main()
    else:
        show_login_page()