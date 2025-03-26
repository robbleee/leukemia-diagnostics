import streamlit as st
# IMPORTANT: Call set_page_config as the very first Streamlit command.
st.set_page_config(
    page_title="Haematologic Classification",
    layout="wide",
    initial_sidebar_state="expanded"
)

import urllib.parse
import bcrypt
import datetime
import jwt
import math
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
import base64
import streamlit.components.v1 as components

# Import the EncryptedCookieManager from streamlit_cookies_manager.
from streamlit_cookies_manager import EncryptedCookieManager

# Initialize the cookie manager using the cookie password from st.secrets.
cookies = EncryptedCookieManager(
    prefix="bloodCancerClassify/",
    password=st.secrets["general"]["cookie_password"]
)
if not cookies.ready():
    st.stop()

from parsers.aml_parser import parse_genetics_report_aml
from parsers.aml_response_parser import parse_aml_response_report
from parsers.mds_parser import parse_genetics_report_mds
from parsers.mds_ipcc_parser import parse_ipcc_report
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022
from classifiers.aml_risk_classifier import classify_ELN2022, eln2024_non_intensive_risk
from classifiers.mds_ipssm_risk_classifier import RESIDUAL_GENES, get_ipssm_survival_data
from reviewers.aml_reviewer import (
    get_gpt4_review_aml_classification,
    get_gpt4_review_aml_genes,
    get_gpt4_review_aml_additional_comments,
    get_gpt4_review_aml_mrd,
    get_gpt4_review_aml_differentiation
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
    create_base_pdf
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
# COOKIE & SESSION INITIALIZATION
##################################
if "jwt_token" not in st.session_state:
    token = cookies.get("jwt_token")
    st.session_state["jwt_token"] = token if token and token != "" else None
if "username" not in st.session_state:
    st.session_state["username"] = ""

##################################
# JWT HELPER FUNCTIONS
##################################
def create_jwt_token(username: str) -> str:
    payload = {
        "username": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token = jwt.encode(payload, st.secrets["jwt"]["secret_key"], algorithm="HS256")
    return token

def verify_jwt_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, st.secrets["jwt"]["secret_key"], algorithms=["HS256"])
        return decoded
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

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
# LOGIN PAGE
##################################
def show_login_page():
    # Remove the default Streamlit padding/margin
    st.markdown("""
    <style>
        /* Remove all containers and backgrounds */
        .stApp {
            background-color: #f5f8fa !important;
        }
        
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin: 0 !important;
        }
        
        /* Hide Streamlit elements */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Logo and title styling */
        .logo-text {
            color: #009688;
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 15px;
            margin-top: 80px;
        }
        
        .logo-subtext {
            color: #555;
            text-align: center;
            font-size: 1.1rem;
            margin-bottom: 30px;
        }
        
        /* Medical icon */
        .medical-icon {
            text-align: center;
            font-size: 60px;
            color: #009688;
            margin-bottom: 15px;
        }
        
        /* Style the input fields */
        .stTextInput > div {
            background-color: transparent !important;
            max-width: 400px;
            margin: 0 auto;
        }
        
        .stTextInput > div > div > input {
            border-radius: 5px;
            border: 1px solid #ddd;
            background-color: white;
            padding: 10px 15px;
        }
        
        .stTextInput > label {
            font-weight: 500;
            max-width: 400px;
            margin: 0 auto;
            display: block;
        }
        
        /* Fix password field eye button spacing */
        .stTextInput > div > div[data-baseweb="input"] {
            width: 100% !important;
        }
        
        .stTextInput > div > div[data-baseweb="input"] > div {
            display: flex !important;
            width: 100% !important;
        }
        
        /* Fix password field container */
        div[data-baseweb="input"] {
            display: flex !important;
            align-items: center !important;
            width: 100% !important;
        }
        
        /* Control width of password eye icon */
        div[data-baseweb="input"] > div:last-child {
            margin-right: 0 !important;
            padding-right: 0 !important;
        }
        
        div[data-baseweb="input"] > div:after {
            content: none !important;
            display: none !important;
            width: 0 !important;
        }
        
        /* Target the password eye icon specifically */
        button[aria-label="Toggle password visibility"] {
            margin-right: 0 !important;
            padding-right: 0 !important;
        }
        
        /* Button styling */
        .stButton > button {
            background-color: #009688;
            color: white;
            border-radius: 6px;
            padding: 10px 15px;
            text-align: center;
            max-width: 400px;
            width: 100%;
            font-weight: 600;
            border: none;
            box-shadow: 0 2px 5px rgba(0, 150, 136, 0.2);
            transition: all 0.3s ease;
            margin: 0 auto;
            display: block;
        }
        
        .stButton > button:hover {
            background-color: #00796b;
            border-color: #00796b;
            color: white;
            box-shadow: 0 4px 8px rgba(0, 150, 136, 0.3);
            transform: translateY(-1px);
        }
        
        /* Error message styling */
        .stAlert {
            background-color: #ffebee;
            color: #c62828;
            border-radius: 5px;
            margin: 15px auto;
            max-width: 400px;
        }
        
        /* Success message styling */
        .element-container:has(.stAlert.success) {
            background-color: #e8f5e9;
            color: #2e7d32;
            border-radius: 5px;
            margin: 15px auto;
            max-width: 400px;
        }
        
        /* Version styling */
        .version {
            text-align: center;
            font-size: 0.8rem;
            color: #888;
            margin-top: 30px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # DNA icon and title
    st.markdown('<div class="medical-icon">🧬</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-text">Haematology Diagnosis</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-subtext">Blood Cancer Classification Support Tool</div>', unsafe_allow_html=True)
    
    # Create simple centered columns for the form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Login form
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        # Login button
        login_button = st.empty()
        if login_button.button("Sign In", key="login_button"):
            if authenticate_user(username, password):
                with login_button:
                    st.markdown('<div style="text-align: center;">Signing in...</div>', unsafe_allow_html=True)
                token = create_jwt_token(username)
                st.session_state["jwt_token"] = token
                st.session_state["username"] = username
                cookies["jwt_token"] = token
                cookies.save()
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password!")
    
    # Version at the bottom
    st.markdown('<div class="version">Version 1.2.0</div>', unsafe_allow_html=True)

##################################
# DATA ENTRY PAGE
##################################
def data_entry_page():
    """
    This page handles:
      - User login check (done in app_main, so not repeated here).
      - Initialization of session state variables.
      - User input toggles (Free-text Mode vs Manual Mode).
      - Data collection.
      - Parsing calls.
      - Transition to the Results page (session_state["page"] = "results").
    """
    
    # Title / Header
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
    
    # Data Entry Page Top Controls
    logout_placeholder = st.empty()

    with st.expander("📋 Instructions", expanded=False):
        # Show different instructions based on which mode is active
        if st.session_state.get("manual_inputs_visible", False):
            st.markdown("""
            ## Manual AML Input Mode - Instructions
            
            This tool allows direct input of diagnostic parameters to classify AML and MDS cases according to WHO 2022 and ICC 2022 guidelines.
            
            ### How to use the Manual Mode:
            
            1. **Clinical Parameters**:
               - Enter blast percentage.
               - Check any relevant clinical features (fibrotic marrow, hypoplasia).
               - Indicate the number of dysplastic lineages.
            
            2. **Genetic Abnormalities**:
               - Select all detected genetic abnormalities from the available options.
               - These selections directly impact classification according to WHO and ICC criteria.
            
            3. **Additional Parameters**:
               - Complete all fields applicable to your case.
               - Pay special attention to driver mutations and cytogenetic findings.
            
            4. **Analyse Genetics**:
               - Click the "Analyse Genetics" button to process the data.
               - The system will classify according to WHO 2022 and ICC 2022 based on your inputs.
               
            5. **Review Results**:
               - The results page will show classifications with detailed derivation steps.
               - You can view risk assessments and additional insights in the different tabs.
            """)
        else:
            st.markdown("""
            ## AML/MDS Classifier - Free Text Mode Instructions
            
            This tool analyses clinical reports to classify AML and MDS cases according to WHO 2022 and ICC 2022 guidelines.
            
            ### How to use the Free Text Mode:
            
            1. **Override Options** (Optional):
               - **Bone Marrow Blasts Override**: Enter a value only if you want to override the blasts percentage detected in the report.
               - **Previous cytotoxic chemotherapy**: Select if the patient has a history of cytotoxic therapy.
               - **Germline predisposition**: Indicate if there are known germline mutations.
               - **Previous MDS/MDS-MPN**: Select if the patient has a history of MDS or MDS/MPN.
            
            2. **Enter Report Data**:
               - Paste your complete report text into the text area.
               - Include clinical information, CBC, bone marrow findings, cytogenetics, and mutations.
               - The more complete the data, the more accurate the classification.
            
            3. **analyse Report**:
               - Click the "Analyse Report" button to process the data.
               - The system will extract relevant parameters and classify according to WHO 2022 and ICC 2022.
               
            4. **Review Results**:
               - The results page will show classifications with detailed derivation steps.
               - You can view risk assessments and additional insights in the different tabs.
            """)

    # Initialize session state variables.
    for key in [
        "expanded_aml_section",
        "expanded_mds_section",
        "expanded_mds_risk_section",
        "aml_free_text_expanded",
        "mds_free_text_expanded",
        "mds_risk_free_text_expanded",
        "blast_percentage_known",
        "manual_inputs_visible"
    ]:
        if key not in st.session_state:
            if key == "blast_percentage_known":
                st.session_state[key] = False
            elif key == "aml_free_text_expanded":
                st.session_state[key] = True
            else:
                st.session_state[key] = None

    # Toggle for free-text vs. manual mode
    aml_mode_toggle = st.toggle("Free-text Mode", key="aml_mode_toggle", value=True)
    if "aml_busy" not in st.session_state:
        st.session_state["aml_busy"] = False

    # -----------------------------------------------------------
    # MANUAL MODE
    # -----------------------------------------------------------
    if not aml_mode_toggle:
        manual_data = build_manual_aml_data()
        if st.button("Analyse Genetics", key="analyse_genetics_manual"):
            st.session_state["aml_manual_expanded"] = False
            st.session_state["aml_busy"] = True
            with st.spinner("Compiling results. Please wait..."):
                # Clear previous results.
                for k in [
                    "aml_manual_result",
                    "aml_ai_result",
                    "aml_class_review",
                    "aml_mrd_review",
                    "aml_gene_review",
                    "aml_additional_comments",
                    "initial_parsed_data",
                    "blast_percentage_known"
                ]:
                    st.session_state.pop(k, None)

                classification_who, who_derivation = classify_combined_WHO2022(manual_data, not_erythroid=False)
                classification_icc, icc_derivation = classify_combined_ICC2022(manual_data)
                # Do not call classify_ELN2022 here.
                st.session_state["aml_manual_result"] = {
                    "parsed_data": manual_data,
                    "who_class": classification_who,
                    "who_derivation": who_derivation,
                    "icc_class": classification_icc,
                    "icc_derivation": icc_derivation,
                    "free_text_input": ""  # For manual mode, you can leave free_text_input empty
                }
                st.session_state["expanded_aml_section"] = "classification"
            st.session_state["aml_busy"] = False
            st.session_state["page"] = "results"
            st.rerun()

    # -----------------------------------------------------------
    # FREE TEXT MODE
    # -----------------------------------------------------------
    else:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("### Input AML/MDS Report")
            
            st.markdown("""
            Enter your report data below. The system will extract relevant parameters for AML/MDS classification.
            """)
            
            with st.container():
                col0, col1, col2, col3 = st.columns(4)
                with col0:
                    bone_marrow_blasts = st.number_input(
                        "Bone Marrow Blasts Override (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=0.0,
                        key="bone_marrow_blasts_initial",
                        help="Leave at 0 to use value from report. Only set if you want to override."
                    )
                with col1:
                    prior_therapy = st.selectbox(
                        "Previous cytotoxic chemotherapy",
                        options=["None", "Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions", "Any combination"],
                        index=0,
                        key="prior_therapy"
                    )
                with col2:
                    germline_status = st.selectbox(
                        "Germline predisposition",
                        options=["Yes", "None", "Undetermined"],
                        index=1,
                        key="germline_status"
                    )
                with col3:
                    previous_mds = st.selectbox(
                        "Previous MDS/MDS-MPN", 
                        options=["None", "Previous MDS", "Previous MDS/MPN"],
                        key="previous_mds"
                    )
            
            if germline_status in ["None", "Undetermined"]:
                st.warning("No germline mutation was indicated, but this should be reviewed at MDT.")
            
            if germline_status == "Yes":
                selected_germline = st.multiselect(
                    "Select known germline mutation(s):",
                    options=[
                        "germline CEBPA mutation",
                        "germline DDX41 mutation",
                        "germline TP53 mutation",
                        "germline RUNX1 mutation",
                        "germline ANKRD26 mutation",
                        "germline ETV6 mutation",
                        "germline GATA2 mutation",
                        "germline SAMD9 mutation",
                        "germline SAMD9L mutation",
                        "RASopathy (including JMML with NF1, JMML with CBL)",
                        "Fanconi anaemia",
                        "Shwachman-Diamond syndrome",
                        "telomere biology disorder",
                        "severe congenital neutropenia",
                        "JMML associated with neurofibromatosis",
                        "Down Syndrome",
                        "germline BLM mutation",
                        "Diamond-Blackfan anemia"
                    ],
                    key="selected_germline"
                )
                
                # Ensure at least one germline mutation is selected when germline is set to "Yes"
                if not selected_germline:
                    st.error("Please select at least one germline mutation when 'Germline predisposition' is set to 'Yes'.")
            
            full_report_text = st.text_area(
                "Enter all relevant AML/MDS data here:",
                placeholder="Paste your AML/MDS report here including: clinical info, CBC, bone marrow findings, cytogenetics, mutations...",
                key="full_text_input",
                height=250
            )
            
            # Moved the Analyse button inside the expander
            analyse_button = st.button("Analyse Report", key="analyse_report", type="primary")
            if analyse_button:
                # Check if germline status is "Yes" but no mutations are selected
                if germline_status == "Yes" and not st.session_state.get("selected_germline"):
                    st.error("Please select at least one germline mutation when 'Germline predisposition' is set to 'Yes'.")
                else:
                    for k in [
                        "aml_ai_result",
                        "aml_class_review",
                        "aml_mrd_review",
                        "aml_gene_review",
                        "aml_additional_comments",
                        "initial_parsed_data",
                        "blast_percentage_known"
                    ]:
                        st.session_state.pop(k, None)

                    if full_report_text.strip():
                        opt_text = ""
                        opt_text += f"Bone Marrow Blasts Override: {bone_marrow_blasts}%. "
                        if germline_status == "Yes":
                            if st.session_state.get("selected_germline"):
                                chosen = ", ".join(st.session_state["selected_germline"])
                                opt_text += f"Germline predisposition: {chosen}. "
                            else:
                                opt_text += "Germline predisposition: Yes. "
                        else:
                            opt_text += "Germline predisposition: None. "

                        if prior_therapy != "None":
                            opt_text += f"Previous cytotoxic chemotherapy: {prior_therapy}. "
                        else:
                            opt_text += "Previous cytotoxic chemotherapy: None. "
                        
                        if previous_mds != "None":
                            opt_text += f"Previous MDS/MDS-MPN: {previous_mds}. "

                        full_text_combined = opt_text + "\n" + full_report_text

                        with st.spinner("Parsing report..."):
                            parsed_data = parse_genetics_report_aml(full_text_combined)
                            if (parsed_data.get("blasts_percentage") == "Unknown" or 
                                parsed_data.get("AML_differentiation") is None or 
                                (parsed_data.get("AML_differentiation") or "").lower() == "ambiguous"):
                                st.session_state["initial_parsed_data"] = parsed_data
                                st.session_state["manual_inputs_visible"] = True
                                st.rerun()
                            else:
                                st.session_state["blast_percentage_known"] = True
                                who_class, who_deriv = classify_combined_WHO2022(parsed_data, not_erythroid=False)
                                icc_class, icc_deriv = classify_combined_ICC2022(parsed_data)
                                # Do not call classify_ELN2022 here
                                st.session_state["aml_ai_result"] = {
                                    "parsed_data": parsed_data,
                                    "who_class": who_class,
                                    "who_derivation": who_deriv,
                                    "icc_class": icc_class,
                                    "icc_derivation": icc_deriv,
                                    "free_text_input": full_text_combined
                                }
                                st.session_state["expanded_aml_section"] = "classification"
                                st.session_state["manual_inputs_visible"] = False

                        st.session_state["page"] = "results"
                        st.rerun()
                    else:
                        st.error("No AML data provided.")

        if st.session_state.get("initial_parsed_data"):
            st.warning("Either the blast percentage could not be automatically determined or the differentiation is ambiguous/missing. Please provide the missing information to proceed with classification.")
            with st.expander("Enter Manual Inputs", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    default_blast = 0.0
                    if st.session_state["initial_parsed_data"].get("blasts_percentage") not in [None, "Unknown"]:
                        default_blast = float(st.session_state["initial_parsed_data"]["blasts_percentage"])
                    manual_blast_percentage = st.number_input(
                        "Enter Blast Percentage (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=default_blast, 
                        key="manual_blast_input"
                    )
                with col2:
                    diff_field = st.session_state["initial_parsed_data"].get("AML_differentiation")
                    if diff_field is None or (diff_field or "").lower() == "ambiguous":
                        diff_map = {
                            "No clear differentiation": "None",
                            "Minimal differentiation": "M0",
                            "Blasts without maturation": "M1",
                            "Blasts with maturation": "M2",
                            "Promyelocytic features": "M3",
                            "Myelomonocytic features": "M4",
                            "Monocytic features": "M5",
                            "Erythroid differentiation": "M6",
                            "Megakaryoblastic features": "M7"
                        }
                        manual_differentiation = st.selectbox(
                            "Select Differentiation", 
                            list(diff_map.keys()),
                            key="manual_differentiation_input"
                        )
                
                # Moved the analyse button inside the expander and made it primary
                submit_button = st.button("Analyse With Manual Inputs", key="submit_manual", type="primary")
                if submit_button:
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
                        st.rerun()


##################################
# 2. RESULTS PAGE
##################################
def back_without_clearing():
    """
    Navigates back to the data entry page without clearing any session state.
    """
    st.session_state["page"] = "data_entry"
    st.rerun()

def results_page():
    """
    This page only displays results if they exist in session state.
    It also includes the sub-tab navigation (Classification, Risk, MRD Review, etc.),
    and the bottom controls (Download Report, Clear Results and Back).
    """
    if "aml_manual_result" not in st.session_state and "aml_ai_result" not in st.session_state:
        st.error("No results available. Please return to the data entry page to input and parse the report.")
        if st.button("Back to Data Entry"):
            st.session_state["page"] = "data_entry"
            st.rerun()
        return

    res = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    mode = "manual" if "aml_manual_result" in st.session_state else "ai"
    free_text_input_value = res.get("free_text_input") if mode == "ai" else None

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
    
    # Add instruction manual expander
    with st.expander("📋 Results Interpretation Guide", expanded=False):
        # Determine which tab is selected
        sub_tab = st.session_state.get("results_sub_tab", "Classification")
        
        if sub_tab == "Classification":
            st.markdown("""
            ## Classification Results - Interpretation Guide
            
            This section displays the classification of the hematologic malignancy according to both WHO 2022 and ICC 2022 criteria.
            
            ### Understanding the Classifications:
            
            1. **WHO 2022 Classification**:
               - The World Health Organization (WHO) classification is widely used for diagnosing hematologic neoplasms.
               - The classification is based on a combination of morphology, cytochemistry, immunophenotype, genetics, and clinical features.
               - The derivation section shows the step-by-step logic used to arrive at the classification.
            
            2. **ICC 2022 Classification**:
               - The International Consensus Classification (ICC) provides an alternative classification system.
               - It often includes additional genetic and molecular insights not fully captured in the WHO system.
               - The derivation section explains the rationale behind the classification.
            
            3. **Classification Review**:
               - This section provides an expert analysis of the classification results.
               - It highlights key findings and potential implications for diagnosis and management.
               - It may reconcile any differences between WHO and ICC classifications.
            """)
        elif sub_tab == "Risk":
            st.markdown("""
            ## Risk Assessment - Interpretation Guide
            
            This section provides risk stratification based on established prognostic models.
            
            ### Understanding the Risk Assessment:
            
            1. **ELN 2022 Risk Classification**:
               - The European LeukemiaNet (ELN) 2022 classification stratifies AML patients into risk categories.
               - Risk categories include Favorable, Intermediate, and Adverse (with qualifiers).
               - The derivation section shows how genetic and clinical factors contributed to the risk assessment.
               - Median overall survival estimates are provided based on the risk category.
            
            2. **Revised ELN24 (Non-Intensive) Risk**:
               - This newer model focuses on patients receiving non-intensive therapies.
               - It incorporates genetic mutations and their impact on outcomes with less intensive treatment approaches.
               - The derivation section explains how specific genetic findings influence the risk category.
               - Median overall survival is reported in months for the assigned risk group.
            """)
        elif sub_tab == "MRD Review":
            st.markdown("""
            ## Minimal Residual Disease (MRD) Review - Interpretation Guide
            
            This section provides guidance on MRD monitoring based on the disease characteristics.
            
            ### Understanding the MRD Review:
            
            1. **MRD Targets**:
               - Identifies specific genetic or immunophenotypic markers that can be used to track disease burden.
               - Highlights the most sensitive and specific markers for monitoring.
            
            2. **Monitoring Recommendations**:
               - Suggests appropriate monitoring techniques (e.g., flow cytometry, PCR, NGS).
               - Provides guidance on monitoring frequency and threshold interpretation.
            
            3. **Clinical Implications**:
               - Explains how MRD results may influence treatment decisions.
               - Discusses the prognostic significance of MRD status in the specific disease context.
            """)
        elif sub_tab == "Gene Review":
            st.markdown("""
            ## Gene Review - Interpretation Guide
            
            This section analyses the genetic findings and their clinical significance.
            
            ### Understanding the Gene Review:
            
            1. **Driver Mutations**:
               - Identifies key driver mutations that define the disease biology.
               - Explains the functional impact of these mutations.
            
            2. **Prognostic Impact**:
               - Discusses how specific mutations influence disease outcome.
               - Stratifies mutations by their favorable, neutral, or adverse prognostic impact.
            
            3. **Therapeutic Implications**:
               - Highlights mutations that may be targeted by specific therapies.
               - Suggests potential clinical trials or treatment approaches based on the genetic profile.
            """)
        elif sub_tab == "AI Comments":
            st.markdown("""
            ## Additional Comments - Interpretation Guide
            
            This section provides supplementary insights not covered in other sections.
            
            ### Understanding the Additional Comments:
            
            1. **Unusual Features**:
               - Highlights any atypical aspects of the case that merit special attention.
               - Discusses rare or complex findings that may influence interpretation.
            
            2. **Diagnostic Challenges**:
               - Addresses potential diagnostic dilemmas or borderline classifications.
               - Suggests additional testing that might clarify ambiguous findings.
            
            3. **Clinical Considerations**:
               - Offers broader context for clinical management.
               - May include references to relevant literature or guidelines.
            """)
        elif sub_tab == "Differentiation":
            st.markdown("""
            ## Differentiation Analysis - Interpretation Guide
            
            This section focuses on the cellular differentiation patterns and their diagnostic significance.
            
            ### Understanding the Differentiation Analysis:
            
            1. **Lineage Assessment**:
               - Identifies the predominant cell lineage(s) involved.
               - Explains morphological, immunophenotypic, and genetic evidence of differentiation.
            
            2. **FAB Classification Context**:
               - Relates findings to the traditional French-American-British (FAB) classification.
               - Maps differentiation patterns to M0-M7 subtypes where applicable.
            
            3. **Clinical Implications**:
               - Discusses how differentiation patterns may influence treatment response.
               - Highlights any prognostic relevance of specific differentiation features.
            """)

    sub_tab = option_menu(
        menu_title=None,
        options=["Classification", "Risk", "MRD Review", "Gene Review", "AI Comments", "Differentiation"],
        icons=["clipboard", "graph-up-arrow", "recycle", "bar-chart", "chat-left-text", "funnel"],
        default_index=0,
        orientation="horizontal"
    )
    
    # Store the current sub_tab in session state to use in the instruction expander
    st.session_state["results_sub_tab"] = sub_tab

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

    if sub_tab == "Classification":
        display_aml_classification_results(
            res["parsed_data"],
            res["who_class"],
            res["who_derivation"],
            res["icc_class"],
            res["icc_derivation"],
            classification_eln="Not computed here",
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

    elif sub_tab == "AI Comments":
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
        
        col1, col2 = st.columns(2)
        
        # Left Column: ELN 2022 Risk Classification (computed on the fly)
        with col1:
            st.markdown("#### ELN 2022 Risk Classification")
            risk_eln2022, median_os_eln2022, derivation_eln2022 = classify_ELN2022(res["parsed_data"])
            st.markdown(f"**Risk Category:** {risk_eln2022}")
            st.markdown(f"**Median OS:** {median_os_eln2022}")
            with st.expander("ELN 2022 Derivation", expanded=False):
                # Check if the derivation is a list of strings (new format) or a single string (old format)
                derivation = st.session_state['eln_derivation']
                if isinstance(derivation, list):
                    for step in derivation:
                        st.markdown(f"- {step}")
                else:
                    # For backwards compatibility with old format
                    st.markdown(derivation)
        
        # Right Column: Revised ELN24 Non-Intensive Risk Classification
        with col2:
            st.markdown("#### Revised ELN24 (Non-Intensive) Risk")
            eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
            risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
            st.markdown(f"**Risk Category:** {risk_eln24}")
            st.markdown(f"**Median OS:** {median_os_eln24} months")
            with st.expander("Revised ELN24 Derivation", expanded=False):
                for step in eln24_derivation:
                    st.markdown(f"- {step}")
        
        # IPCC Risk Section - Optional display based on checkbox
        st.markdown("---")
        show_ipcc_risk = st.checkbox("Show IPSS-M/R Risk Assessment", value=False)
        
        if show_ipcc_risk and mode == "ai" and free_text_input_value:
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
        elif show_ipcc_risk and (mode != "ai" or not free_text_input_value):
            st.info("IPSS-M/R Risk assessment requires free text input. This feature is only available when using the AI-assisted mode with free text input.")

    elif sub_tab == "Differentiation":
        if "differentiation" not in st.session_state:
            with st.spinner("Generating Differentiation Review..."):
                st.session_state["differentiation"] = get_gpt4_review_aml_differentiation(
                    classification_dict,
                    res["parsed_data"],
                    free_text_input=free_text_input_value
                )
        with st.expander("Differentiation", expanded=True):
            st.markdown(st.session_state["differentiation"])

    # Bottom Controls
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] > div:nth-of-type(7) button {
            background-color: #FF4136 !important;
            color: white !important;
            margin-top: 0px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    clear_keys = [
        "expanded_aml_section",
        "expanded_mds_section",
        "expanded_mds_risk_section",
        "aml_free_text_expanded",
        "mds_free_text_expanded",
        "mds_risk_free_text_expanded",
        "blast_percentage_known",
        "manual_inputs_visible",
        "aml_ai_result",
        "aml_manual_result",
        "aml_class_review",
        "aml_mrd_review",
        "aml_gene_review",
        "aml_additional_comments",
        "initial_parsed_data",
        "free_text_input"
    ]

    col_download, col3, col4, col5, col6, col_back, col_clear = st.columns(7)
    with col_download:
        if st.button("Download Report"):
            st.session_state["show_pdf_form"] = True
    with col_clear:
        if st.button("Clear Results", key="clear_and_back"):
            for k in clear_keys:
                st.session_state.pop(k, None)
            st.session_state["page"] = "data_entry"
            st.rerun()
    with col_back:
        if st.button("Back"):
            back_without_clearing()

    if st.session_state.get("show_pdf_form"):
        # [PDF download form code...]
        pass

def ipcc_risk_calculator_page():
    """
    This page handles:
      - Display of form for IPSS-M and IPSS-R data entry
      - Calculation of IPSS-M and IPSS-R risk scores
      - Visualization of results including contribution of each factor
    """
    # Title / Header
    st.markdown(
        """
        <div style="
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            ">
            <h2 style="color: #009688; text-align: left;">
                IPSS-M/R Risk Tool
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # IPCC Risk Calculator Page Top Controls
    logout_placeholder = st.empty()

    with st.expander("📋 Instructions", expanded=False):
        # Show different instructions based on which mode is active
        if st.session_state.get("mds_risk_free_text_expanded", True):
            st.markdown("""
            ## IPSS-M/R Risk Tool - Free Text Mode Instructions
            
            This tool calculates risk scores for MDS patients according to the IPSS-M and IPSS-R risk stratification systems.
            
            ### How to use the Free Text Mode:
            
            1. **Override Options** (Optional):
               - **Hemoglobin**: Enter a value only if you want to override what's detected in the report.
               - **Platelets**: Enter a value only if you want to override what's detected in the report.
               - **ANC (Absolute Neutrophil Count)**: Enter a value only if you want to override what's detected in the report.
               - **Bone Marrow Blasts**: Enter a value only if you want to override what's detected in the report.
               - **Age**: Enter a value only if you want to override what's detected in the report.
               
               Leave override fields at their default values (0 or 18 for age) if you want to use the values extracted from the report.
            
            2. **Enter Report Data**:
               - Paste your complete MDS report text into the text area.
               - Include clinical information, laboratory values, bone marrow findings, cytogenetics, and mutations.
               - The more complete the data, the more accurate the risk calculation.
            
            3. **Calculate Risk Scores**:
               - Click the "Calculate Risk Scores" button to process the data.
               - The system will extract relevant parameters and calculate IPSS-M and IPSS-R scores.
               
            4. **Review Results**:
               - The results will show risk stratification for both IPSS-M and IPSS-R.
               - For IPSS-M, you'll see mean, best-case, and worst-case scenarios.
               - The tool will display detailed breakdown of how each factor contributes to the risk score.
            """)
        else:  # Manual mode
            st.markdown("""
            ## IPSS-M/R Risk Tool - Manual Mode Instructions
            
            This tool calculates risk scores for MDS patients according to the IPSS-M and IPSS-R risk stratification systems.
            
            ### How to use the Manual Mode:
            
            1. **Clinical Parameters**:
               - Enter the patient's age, hemoglobin level, platelet count, neutrophil count, and bone marrow blast percentage.
               - These values directly impact both IPSS-M and IPSS-R calculations.
            
            2. **Cytogenetics**:
               - Select the appropriate cytogenetic risk category.
               - For IPSS-R: Very Good, Good, Intermediate, Poor, or Very Poor.
               - For IPSS-M: Also indicate specific karyotype abnormalities when applicable.
            
            3. **Mutations**:
               - Select all detected gene mutations from the available options.
               - Pay special attention to TP53 status, as it significantly impacts risk calculation.
               - Indicate VAF (Variant Allele Frequency) for mutations when available.
            
            4. **Calculate Risk Scores**:
               - Click the "Calculate Risk Scores" button to process the data.
               - The system will calculate both IPSS-M and IPSS-R scores based on your inputs.
               
            5. **Review Results**:
               - The results will show risk stratification for both IPSS-M and IPSS-R.
               - For IPSS-M, you'll see mean, best-case, and worst-case scenarios.
               - The tool will display detailed breakdown of how each factor contributes to the risk score.
            """)
    
    # Import the calculator functions
    from classifiers.mds_ipssm_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
    
    # Initialize session state for persisting results between tabs
    if 'ipssm_result' not in st.session_state:
        st.session_state['ipssm_result'] = None
    if 'ipssr_result' not in st.session_state:
        st.session_state['ipssr_result'] = None
    if 'ipss_patient_data' not in st.session_state:
        st.session_state['ipss_patient_data'] = None
    if "risk_results_tab" not in st.session_state:
        st.session_state["risk_results_tab"] = "IPSS-M"
    
    # Toggle for free-text vs. manual mode
    ipcc_mode_toggle = st.toggle("Free-text Mode", key="ipcc_mode_toggle", value=True)
    
    patient_data = None
    
    # FREE TEXT MODE
    if ipcc_mode_toggle:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("### Input MDS/IPCC Report")
            
            st.markdown("""
            Enter your MDS report data below. The system will extract relevant parameters for IPSS-M/R risk calculation.
            """)
            
            
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
                    key="hb_override"
                )
                
                plt_override = st.number_input(
                    "Platelets (10^9/L)",
                    min_value=0, 
                    max_value=1000,
                    value=0,
                    step=1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="plt_override"
                )
            
            with col2:
                anc_override = st.number_input(
                    "ANC (10^9/L)",
                    min_value=0.0, 
                    max_value=20.0,
                    value=0.0,
                    step=0.1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="anc_override"
                )
                
                blast_override = st.number_input(
                    "Bone Marrow Blasts (%)",
                    min_value=0.0, 
                    max_value=30.0,
                    value=0.0,
                    step=0.1,
                    help="Leave at 0 to use value from report. Only set if you want to override.",
                    key="blast_override"
                )
            
            with col3:
                age_override = st.number_input(
                    "Age (years)",
                    min_value=18, 
                    max_value=120,
                    value=18,  # Min allowable value to indicate "not set"
                    step=1,
                    help="Leave at 18 to use value from report. Only values > 18 will override.",
                    key="age_override"
                )
                
                # TP53 status will be extracted directly from the report
            
            free_report_text = st.text_area(
                "Enter MDS report data:",
                placeholder="Paste your MDS report here including: lab values, cytogenetics, gene mutations...",
                key="ipcc_free_text_input",
                height=250
            )
            
            # Single calculate button
            calculate_button = st.button("Calculate Risk Scores", key="calculate_ipcc_scores", type="primary")
            if calculate_button:
                # First try to process any text input
                parsed_data = None
                if free_report_text.strip():
                    with st.spinner("Processing report text..."):
                        parsed_data = parse_ipcc_report(free_report_text)
                        if parsed_data:
                            st.info("Report processed successfully.")
                            # Store parsed data for gene mutations and other details
                            st.session_state['original_ipcc_data'] = parsed_data.copy()
                            # We'll display JSON in a dedicated section later
                
                # Start with parsed data as the base, then apply overrides only if set
                with st.spinner("Calculating risk scores..."):
                    # Start with any parsed data we have
                    if parsed_data or 'original_ipcc_data' in st.session_state:
                        original_data = parsed_data or st.session_state.get('original_ipcc_data', {})
                        patient_data = original_data.copy()
                    else:
                        patient_data = {}
                    
                    # Only apply overrides if they're set to non-zero values
                    if hb_override > 0:
                        patient_data["HB"] = hb_override
                    
                    if plt_override > 0:
                        patient_data["PLT"] = plt_override
                    
                    if anc_override > 0:
                        patient_data["ANC"] = anc_override
                    
                    if blast_override > 0:
                        patient_data["BM_BLAST"] = blast_override
                    
                    if age_override > 18:  # Age 18 is the minimum and signals "not set"
                        patient_data["AGE"] = age_override
                    
                    # Default cytogenetic value if not available - normal karyotype
                    if patient_data.get("CYTO_IPSSR") is None:
                        patient_data["CYTO_IPSSR"] = "Good"
                    
                    # TP53 data is now preserved from parser output
                    
                    # TP53multi is calculated based on TP53mut value from parser
                    
                    # Store for calculations but keep the prompts intact
                    if 'original_ipcc_data' in st.session_state and '__prompts' in st.session_state['original_ipcc_data']:
                        # Save the prompts
                        prompts = st.session_state['original_ipcc_data']['__prompts']
                        # Update the original data with new calculation values but keep prompts
                        st.session_state['original_ipcc_data'] = patient_data.copy()
                        st.session_state['original_ipcc_data']['__prompts'] = prompts
                    else:
                        # Just store the new data if no prompts exist
                        st.session_state['original_ipcc_data'] = patient_data.copy()
                    
                    # Always update the calculation data
                    # Remove prompts from the calculation data
                    calculation_data = patient_data.copy()
                    if '__prompts' in calculation_data:
                        del calculation_data['__prompts']
                    st.session_state['ipss_patient_data'] = calculation_data
                    
                    try:
                        # Calculate IPSS-M with contributions and detailed calculations
                        ipssm_result = calculate_ipssm(patient_data, include_contributions=True, include_detailed_calculations=True)
                        
                        # Calculate IPSS-R with return_components=True
                        ipssr_result = calculate_ipssr(patient_data, return_components=True)
                        
                        # Remove debug information now that we have a proper JSON viewer
                        # Format results for display
                        formatted_ipssm = {
                            'means': {
                                'riskScore': ipssm_result['means']['risk_score'],
                                'riskCat': ipssm_result['means']['risk_cat'],
                                'contributions': ipssm_result['means'].get('contributions', {}),
                                'detailed_calculations': ipssm_result['means'].get('detailed_calculations', {})
                            },
                            'worst': {
                                'riskScore': ipssm_result['worst']['risk_score'],
                                'riskCat': ipssm_result['worst']['risk_cat'],
                                'contributions': ipssm_result['worst'].get('contributions', {}),
                                'detailed_calculations': ipssm_result['worst'].get('detailed_calculations', {})
                            },
                            'best': {
                                'riskScore': ipssm_result['best']['risk_score'],
                                'riskCat': ipssm_result['best']['risk_cat'],
                                'contributions': ipssm_result['best'].get('contributions', {}),
                                'detailed_calculations': ipssm_result['best'].get('detailed_calculations', {})
                            },
                            'metadata': ipssm_result.get('metadata', {}),
                            'derivation': []  # Add derivation if needed
                        }
                        
                        formatted_ipssr = {
                            'IPSSR_SCORE': ipssr_result['IPSSR_SCORE'],
                            'IPSSR_CAT': ipssr_result['IPSSR_CAT'],
                            'IPSSRA_SCORE': ipssr_result['IPSSRA_SCORE'],
                            'IPSSRA_CAT': ipssr_result['IPSSRA_CAT'],
                            'components': ipssr_result.get('components', {}),
                            'hb_category': ipssr_result.get('hb_category', ''),
                            'plt_category': ipssr_result.get('plt_category', ''),
                            'anc_category': ipssr_result.get('anc_category', ''),
                            'blast_category': ipssr_result.get('blast_category', ''),
                            'cyto_category': ipssr_result.get('cyto_category', ''),
                            'derivation': []  # Add derivation if needed
                        }
                        
                        # Store results in session state
                        st.session_state['ipssm_result'] = formatted_ipssm
                        st.session_state['ipssr_result'] = formatted_ipssr
                        
                        # Reset to first tab after new calculation
                        st.session_state["risk_results_tab"] = "IPSS-M"
                                                
                    except Exception as e:
                        st.error(f"Error calculating risk scores: {str(e)}")

    # MANUAL MODE
    else:
        # Get patient data using the existing form
        patient_data = build_manual_ipss_data()
        if patient_data and st.button("Calculate Risk Scores", type="primary"):
            with st.spinner("Calculating risk scores..."):
                try:
                    # Store original manual data in session state
                    st.session_state['original_ipcc_data'] = patient_data.copy()
                    
                    # Remove prompts if they exist before storing calculation data
                    calculation_data = patient_data.copy()
                    if '__prompts' in calculation_data:
                        del calculation_data['__prompts']
                    st.session_state['ipss_patient_data'] = calculation_data
                    
                    # Calculate IPSS-M with contributions
                    ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
                    
                    # Calculate IPSS-R with return_components=True
                    ipssr_result = calculate_ipssr(patient_data, return_components=True)
                    
                    # Remove debug information now that we have a proper JSON viewer
                    # Format results for display
                    formatted_ipssm = {
                        'means': {
                            'riskScore': ipssm_result['means']['risk_score'],
                            'riskCat': ipssm_result['means']['risk_cat'],
                            'contributions': ipssm_result['means'].get('contributions', {})
                        },
                        'worst': {
                            'riskScore': ipssm_result['worst']['risk_score'],
                            'riskCat': ipssm_result['worst']['risk_cat'],
                            'contributions': ipssm_result['worst'].get('contributions', {})
                        },
                        'best': {
                            'riskScore': ipssm_result['best']['risk_score'],
                            'riskCat': ipssm_result['best']['risk_cat'],
                            'contributions': ipssm_result['best'].get('contributions', {})
                        },
                        'derivation': []  # Add derivation if needed
                    }
                    
                    formatted_ipssr = {
                        'IPSSR_SCORE': ipssr_result['IPSSR_SCORE'],
                        'IPSSR_CAT': ipssr_result['IPSSR_CAT'],
                        'IPSSRA_SCORE': ipssr_result['IPSSRA_SCORE'],
                        'IPSSRA_CAT': ipssr_result['IPSSRA_CAT'],
                        'components': ipssr_result.get('components', {}),
                        'hb_category': ipssr_result.get('hb_category', ''),
                        'plt_category': ipssr_result.get('plt_category', ''),
                        'anc_category': ipssr_result.get('anc_category', ''),
                        'blast_category': ipssr_result.get('blast_category', ''),
                        'cyto_category': ipssr_result.get('cyto_category', ''),
                        'derivation': []  # Add derivation if needed
                    }
                    
                    # Store results in session state
                    st.session_state['ipssm_result'] = formatted_ipssm
                    st.session_state['ipssr_result'] = formatted_ipssr
                    
                    # Reset to first tab after new calculation
                    st.session_state["risk_results_tab"] = "IPSS-M"
                    
                except Exception as e:
                    st.error(f"Error calculating risk scores: {str(e)}")
    
    # Remove the separate overrides panel, since it's now integrated above
    
    # Add JSON data display expander before the help information
    if 'ipss_patient_data' in st.session_state:
        with st.expander("Data Inspector - View JSON Data", expanded=False):
            # Only show the calculation data - simplified to a single tab
            st.subheader("Data Used for Calculations")
            
            # Check if ipss_patient_data is None before trying to copy it
            patient_data = st.session_state['ipss_patient_data']
            if patient_data is not None:
                # Remove the '__prompts' field if it exists in the JSON to display
                display_data = patient_data.copy()
                if '__prompts' in display_data:
                    del display_data['__prompts']
                st.json(display_data)
            else:
                st.info("No calculation data available yet. Run a calculation first.")
    
    # Remove help information section - moved to sidebar
    
    # Display results only if they exist in session state
    if (st.session_state['ipssm_result'] is not None and 
        st.session_state['ipssr_result'] is not None and
        st.session_state['ipss_patient_data'] is not None):
        # Add CSS for styling the results display
        st.markdown("""
        <style>
            .risk-card {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .risk-header {
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 15px;
                color: #333;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }
            .score-container {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin-bottom: 15px;
            }
            .score-box {
                flex: 1;
                min-width: 120px;
                padding: 15px;
                border-radius: 6px;
                text-align: center;
            }
            .score-label {
                font-size: 0.9rem;
                margin-bottom: 5px;
                font-weight: 500;
            }
            .score-value {
                font-size: 1.5rem;
                font-weight: 700;
            }
            .category-value {
                font-size: 1.2rem;
                padding: 5px 10px;
                border-radius: 4px;
                display: inline-block;
                font-weight: 600;
                margin-top: 5px;
            }
            .risk-very-low {
                background-color: #c8e6c9;
                color: #2e7d32;
            }
            .risk-low {
                background-color: #dcedc8;
                color: #558b2f;
            }
            .risk-moderate {
                background-color: #fff9c4;
                color: #f9a825;
            }
            .risk-high {
                background-color: #ffccbc;
                color: #d84315;
            }
            .risk-very-high {
                background-color: #ffcdd2;
                color: #c62828;
            }
            .corner-ribbon {
                position: absolute;
                top: 0;
                right: 0;
                background-color: #009688;
                color: white;
                padding: 5px 10px;
                font-size: 0.8rem;
                border-radius: 0 8px 0 8px;
            }
            .divider-line {
                height: 1px;
                background-color: #eee;
                margin: 15px 0;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Get formatted results from session state
        formatted_ipssm = st.session_state['ipssm_result']
        formatted_ipssr = st.session_state['ipssr_result']
        patient_data = st.session_state['ipss_patient_data']
        
        # Create a results header
        st.markdown("## Risk Assessment Results")
        
        # Create colored category display helper function
        def get_risk_class_color(category):
            if 'very low' in category.lower():
                return "#c8e6c9"  # Light green
            elif 'low' in category.lower():
                return "#dcedc8"  # Lighter green
            elif 'moderate' in category.lower() or 'intermediate' in category.lower() or 'mod' in category.lower():
                return "#fff9c4"  # Light yellow
            elif 'high' in category.lower() and 'very' not in category.lower():
                return "#ffccbc"  # Light orange/red
            elif 'very high' in category.lower():
                return "#ffcdd2"  # Light red
            else:
                return "#f5f7fa"  # Light gray

        # Navigation menu for results sections (with no header)
        # Store the previous tab so we can detect real changes
        previous_tab = st.session_state.get("risk_results_tab", "IPSS-M")
        
        selected_tab = option_menu(
            menu_title=None,
            options=[
                "IPSS-M", 
                "IPSS-R"
            ],
            icons=[
                "graph-up", 
                "graph-up-arrow"
            ],
            default_index=0 if previous_tab == "IPSS-M" else 1,
            orientation="horizontal",
            key="risk_results_tabs", # Add a unique key to force rerender
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#009688", "font-size": "14px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "center",
                    "margin": "0px",
                    "padding": "10px",
                    "--hover-color": "#eee"
                },
                "nav-link-selected": {"background-color": "#009688", "color": "white"},
            }
        )
        
        # Update session state with the selected tab
        st.session_state["risk_results_tab"] = selected_tab
        
        # Display the selected tab content
        if selected_tab == "IPSS-M":
            # IPSS-M Results section

            
            # Display all risk scenarios in a single row with matching panel styles
            st.markdown("#### Risk Calculations")
            st.markdown("The IPSS-M risk score combines clinical and genetic factors to predict outcomes in myelodysplastic syndromes. The three scenarios below account for possible variations in incomplete data.")
            
            mean_best_worst_cols = st.columns(3)
            
            # Mean risk in a styled panel matching best/worst case
            with mean_best_worst_cols[0]:
                mean_color = get_risk_class_color(formatted_ipssm['means']['riskCat'])
                st.markdown(f"""
                <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                    <div style="font-weight: 500; margin-bottom: 5px;">Mean Risk</div>
                    <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssm['means']['riskScore']:.2f}</div>
                    <div style="background-color: {mean_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                        {formatted_ipssm['means']['riskCat']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Best case panel
            with mean_best_worst_cols[1]:
                best_color = get_risk_class_color(formatted_ipssm['best']['riskCat'])
                st.markdown(f"""
                <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                    <div style="font-weight: 500; margin-bottom: 5px;">Best Case</div>
                    <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssm['best']['riskScore']:.2f}</div>
                    <div style="background-color: {best_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                        {formatted_ipssm['best']['riskCat']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            # Worst case panel
            with mean_best_worst_cols[2]:
                worst_color = get_risk_class_color(formatted_ipssm['worst']['riskCat'])
                st.markdown(f"""
                <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                    <div style="font-weight: 500; margin-bottom: 5px;">Worst Case</div>
                    <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssm['worst']['riskScore']:.2f}</div>
                    <div style="background-color: {worst_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                        {formatted_ipssm['worst']['riskCat']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")  # Add blank line for spacing
            
            # Add Expected Outcomes section based on risk category
            st.markdown("### Expected Outcomes")
            st.markdown("""The following outcomes are associated with this IPSS-M risk category based on clinical data:
            **Note:** Survival times shown represent median values with 25th-75th percentile ranges in parentheses.""")
            
            # Get survival data for the mean risk category
            mean_risk_cat = formatted_ipssm['means']['riskCat']
            survival_data = get_ipssm_survival_data(mean_risk_cat)
            
            # Display in a 3-column layout
            outcome_cols = st.columns(3)

            with outcome_cols[0]:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                    <h4 style="color: #009688; margin-top: 0;">Leukemia-Free Survival</h4>
                    <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 5px;">
                        {survival_data['leukemia_free_survival']}
                    </div>
                    <div style="font-size: 0.9em; color: #444; margin-top: 5px; font-style: italic;">
                        Median with 25th-75th percentile range
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with outcome_cols[1]:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                    <h4 style="color: #009688; margin-top: 0;">Overall Survival</h4>
                    <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 5px;">
                        {survival_data['overall_survival']}
                    </div>
                    <div style="font-size: 0.9em; color: #444; margin-top: 5px; font-style: italic;">
                        Median with 25th-75th percentile range
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with outcome_cols[2]:
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; border: 1px solid #eee;">
                    <h4 style="color: #009688; margin-top: 0;">AML Transformation</h4>
                    <div style="font-size: 1.2em; font-weight: bold; margin-bottom: 5px;">
                        {survival_data['aml_transformation_1yr']}
                    </div>
                    <div style="font-size: 0.9em; color: #444; margin-top: 5px; font-style: italic;">
                        Risk of transformation by 1 year
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # Add a reference note
            st.markdown("""
            <div style="font-size: 0.8em; color: #666; margin-top: 10px; font-style: italic;">
            Data based on IPSS-M validation cohort studies. Individual patient outcomes may vary based on additional factors.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")  # Add blank line for spacing
            
            # Add a reference table with all risk categories
            with st.expander("View Complete IPSS-M Outcome Reference Table", expanded=False):
                # Create reference data for all categories
                st.markdown("""
                <div style="margin-bottom: 15px;">
                This table shows outcomes for each IPSS-M risk category. All survival times represent <b>median values with 25th-75th percentile ranges</b> in parentheses.
                </div>
                """, unsafe_allow_html=True)
                
                ref_data = []
                for category in ["Very Low", "Low", "Moderate Low", "Moderate High", "High", "Very High"]:
                    cat_data = get_ipssm_survival_data(category)
                    ref_data.append({
                        "Risk Category": category,
                        "Typical Score": cat_data["typical_score"],
                        "Leukemia-Free Survival": cat_data["leukemia_free_survival"],
                        "Overall Survival": cat_data["overall_survival"],
                        "AML Transformation (1yr)": cat_data["aml_transformation_1yr"]
                    })
                
                # Convert to DataFrame and display
                df_ref = pd.DataFrame(ref_data)
                st.table(df_ref.set_index("Risk Category"))
                
                # Add citation
                st.markdown("""
                <div style="font-size: 0.8em; color: #666; margin-top: 10px; font-style: italic;">
                Reference: Bernard E, et al. Molecular International Prognostic Scoring System for Myelodysplastic Syndromes. NEJM Evid. 2022.
                </div>
                """, unsafe_allow_html=True)
            
            # Add calculation details table if available
            if 'detailed_calculations' in formatted_ipssm['means'] and formatted_ipssm['means']['detailed_calculations']:
                st.markdown("")  # Add blank line for spacing
                
                st.markdown("### Detailed Calculation Table")
                st.markdown("This table shows how each factor contributes to the IPSS-M risk score:")
                
                # Get the detailed calculations
                detailed_calcs = formatted_ipssm['means']['detailed_calculations']
                
                # Create a DataFrame for the table
                calc_data = []
                for var_name, details in detailed_calcs.items():
                    # Calculate contribution
                    contribution = ((details.get('raw_value', 0) - details.get('reference_value', 0)) * 
                                  details.get('coefficient', 0)) / math.log(2)
                    
                    # Determine impact category
                    if contribution > 0.5:
                        impact = "Strong risk-increasing"
                    elif contribution > 0.2:
                        impact = "Moderate risk-increasing"
                    elif contribution > 0:
                        impact = "Mild risk-increasing"
                    elif contribution < -0.5:
                        impact = "Strong protective"
                    elif contribution < -0.2:
                        impact = "Moderate protective"
                    elif contribution < 0:
                        impact = "Mild protective"
                    else:
                        impact = "Neutral"
                    
                    # Add to data
                    calc_data.append({
                        "Factor": var_name,
                        "Description": details.get('explanation', '').split('.')[0],  # Get first sentence
                        "Value": details.get('raw_value', 0),
                        "Reference": details.get('reference_value', 0),
                        "Coefficient": details.get('coefficient', 0),
                        "Contribution": contribution,
                        "Impact": impact
                    })
                
                # Convert to DataFrame
                df_calcs = pd.DataFrame(calc_data)
                
                # Sort by absolute contribution
                df_calcs = df_calcs.sort_values(by="Contribution", key=abs, ascending=False)
                
                # Split into two DataFrames for display
                genetic_factors = df_calcs[df_calcs['Factor'].str.contains('ASXL1|RUNX1|SF3B1|SRSF2|U2AF1|EZH2|DNMT3A|MLL_PTD|CBL|NRAS|KRAS|IDH2|ETV6|NPM1|TP53|FLT3|Nres2', regex=True)]
                clinical_factors = df_calcs[~df_calcs['Factor'].str.contains('ASXL1|RUNX1|SF3B1|SRSF2|U2AF1|EZH2|DNMT3A|MLL_PTD|CBL|NRAS|KRAS|IDH2|ETV6|NPM1|TP53|FLT3|Nres2', regex=True)]
                
                # Create tabs for different factor types
                calc_tabs = st.tabs(["All Factors", "Genetic Factors", "Clinical Factors"])
                
                with calc_tabs[0]:
                    # Display formatted table with all factors
                    st.dataframe(
                        df_calcs,
                        column_config={
                            "Factor": "Factor",
                            "Description": "Description",
                            "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                            "Reference": st.column_config.NumberColumn("Reference", format="%.3f"),
                            "Coefficient": st.column_config.NumberColumn("Coefficient", format="%.3f"),
                            "Contribution": st.column_config.NumberColumn(
                                "Contribution",
                                format="%.4f",
                                help="Contribution to overall risk score"
                            ),
                            "Impact": "Impact on Risk"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                with calc_tabs[1]:
                    if not genetic_factors.empty:
                        st.dataframe(
                            genetic_factors,
                            column_config={
                                "Factor": "Gene/Mutation",
                                "Description": "Description",
                                "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                                "Reference": st.column_config.NumberColumn("Reference", format="%.3f"),
                                "Coefficient": st.column_config.NumberColumn("Coefficient", format="%.3f"),
                                "Contribution": st.column_config.NumberColumn(
                                    "Contribution",
                                    format="%.4f",
                                    help="Contribution to overall risk score"
                                ),
                                "Impact": "Impact on Risk"
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No genetic factors found.")
                
                with calc_tabs[2]:
                    if not clinical_factors.empty:
                        st.dataframe(
                            clinical_factors,
                            column_config={
                                "Factor": "Clinical Parameter",
                                "Description": "Description",
                                "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                                "Reference": st.column_config.NumberColumn("Reference", format="%.3f"),
                                "Coefficient": st.column_config.NumberColumn("Coefficient", format="%.3f"),
                                "Contribution": st.column_config.NumberColumn(
                                    "Contribution", 
                                    format="%.4f",
                                    help="Contribution to overall risk score"
                                ),
                                "Impact": "Impact on Risk"
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.info("No clinical factors found.")
            
            # Add IPSS-M Contributors section below
            st.markdown("---")
            st.markdown("### IPSS-M Risk Score Contributors")
            if 'contributions' in formatted_ipssm['means']:
                contributions = formatted_ipssm['means']['contributions']
                
                # Sort contributions by absolute value
                sorted_contributions = sorted(
                    contributions.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )
                
                # Convert to DataFrame for easier plotting
                df = pd.DataFrame(sorted_contributions, columns=['Factor', 'Contribution'])
                
                # Create a color map (red for positive/risk-increasing, green for negative/risk-decreasing)
                colors = ['#d62728' if c > 0 else '#2ca02c' for c in df['Contribution']]
                
                # Create the bar chart
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(df['Factor'], df['Contribution'], color=colors)
                
                # Add a vertical line at x=0
                ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
                
                # Set labels and title
                ax.set_xlabel('Contribution to Risk Score')
                ax.set_title('IPSS-M Risk Score Contributors')
                
                # Invert the y-axis so the largest contributors are at the top
                ax.invert_yaxis()
                
                # Show the plot
                st.pyplot(fig)
                


                
                # Display detailed calculation steps if available
                if 'detailed_calculations' in formatted_ipssm['means'] and formatted_ipssm['means']['detailed_calculations']:
                    st.markdown("---")
                    st.markdown("### Detailed Calculation Steps")
                    
                    # Metadata about the calculation process
                    if 'metadata' in formatted_ipssm:
                        metadata = formatted_ipssm['metadata']
                        st.markdown("#### About IPSS-M Calculations")
                        st.markdown(metadata.get('calculation_formula', ""))
                        st.markdown(f"Log(2) value used: {metadata.get('log2_value', '')}")
                        st.markdown(metadata.get('risk_interpretation', ""))
                    
                    # Create expanders for each variable's calculation details
                    st.markdown("#### Individual Variable Calculations")
                    st.markdown("Expand each section to see detailed calculation steps:")
                    
                    # Sort variables by absolute contribution value
                    detailed_calcs = formatted_ipssm['means']['detailed_calculations']
                    sorted_vars = sorted(
                        detailed_calcs.items(),
                        key=lambda x: abs(x[1]['raw_value'] if 'raw_value' in x[1] else 0),
                        reverse=True
                    )
                    
                    # Display each variable's calculation
                    for var_name, details in sorted_vars:
                        with st.expander(f"{var_name}: {details.get('interpretation', '')}"):
                            st.markdown(f"**Description:** {details.get('explanation', '')}")
                            st.markdown(f"**Raw Value:** {details.get('raw_value', '')}")
                            st.markdown(f"**Reference Value:** {details.get('reference_value', '')}")
                            st.markdown(f"**Coefficient:** {details.get('coefficient', '')}")
                            st.markdown(f"**Calculation:** {details.get('calculation', '')}")
                            
                            # Format contribution with color based on whether it increases or decreases risk
                            if 'raw_value' in details and 'reference_value' in details:
                                contribution = ((details['raw_value'] - details['reference_value']) * 
                                              details['coefficient']) / math.log(2)
                                
                                if contribution > 0:
                                    st.markdown(f"**Contribution to Risk Score:** <span style='color:red'>+{contribution:.4f}</span>", unsafe_allow_html=True)
                                elif contribution < 0:
                                    st.markdown(f"**Contribution to Risk Score:** <span style='color:green'>{contribution:.4f}</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"**Contribution to Risk Score:** 0.0000")
        
        elif selected_tab == "IPSS-R":
            # IPSS-R Results section
            st.markdown("### IPSS-R Risk Classification")
            st.markdown("The IPSS-R score evaluates myelodysplastic syndromes based on cytogenetics, bone marrow blasts, and blood counts. The age-adjusted version (IPSS-RA) accounts for the impact of age on risk.")
            
            st.markdown("")  # Add spacing
            
            # Display IPSS-R scores in a single row with matching panel styles
            st.markdown("#### Risk Calculations")
            
            ipssr_cols = st.columns(2)
            
            # IPSS-R Score panel
            with ipssr_cols[0]:
                ipssr_color = get_risk_class_color(formatted_ipssr['IPSSR_CAT'])
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                    <div style="font-weight: 500; margin-bottom: 5px;">Standard IPSS-R</div>
                    <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssr['IPSSR_SCORE']:.2f}</div>
                    <div style="background-color: {ipssr_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                        {formatted_ipssr['IPSSR_CAT']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # IPSS-RA Score panel
            with ipssr_cols[1]:
                ipssra_color = get_risk_class_color(formatted_ipssr['IPSSRA_CAT'])
                st.markdown(f"""
                <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                    <div style="font-weight: 500; margin-bottom: 5px;">Age-Adjusted IPSS-RA</div>
                    <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssr['IPSSRA_SCORE']:.2f}</div>
                    <div style="background-color: {ipssra_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                        {formatted_ipssr['IPSSRA_CAT']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("")  # Add spacing
                
            # IPSS-R Components
            st.markdown("### Score Components")
            st.markdown("This chart shows how each factor contributes to the overall IPSS-R score:")
            
            if 'components' in formatted_ipssr:
                components = formatted_ipssr['components']
                
                # Convert components to DataFrame for plotting
                df_ipssr = pd.DataFrame({
                    'Component': list(components.keys()),
                    'Score': list(components.values())
                })
                
                # Create the bar chart
                fig, ax = plt.subplots(figsize=(10, 6))
                bars = ax.barh(df_ipssr['Component'], df_ipssr['Score'], color='#1f77b4')
                
                # Set labels and title
                ax.set_xlabel('Score Contribution')
                ax.set_title('IPSS-R Score Components')
                
                # Show the plot
                st.pyplot(fig)
                
                st.markdown("")  # Add spacing
                
                # Display parameter categorization table
                st.markdown("### Parameter Categorization")
                st.markdown("This table shows how each clinical parameter is categorized in the IPSS-R scoring system:")
                
                # Create DataFrame for parameter categorization
                param_data = {
                    "Parameter": ["Hemoglobin", "Platelets", "ANC", "Bone Marrow Blasts", "Cytogenetics"],
                    "Value": [patient_data["HB"], patient_data["PLT"], patient_data["ANC"], patient_data["BM_BLAST"], patient_data["CYTO_IPSSR"]],
                    "Category": [
                        f"{formatted_ipssr['hb_category']} ({components['Hemoglobin']} points)",
                        f"{formatted_ipssr['plt_category']} ({components['Platelets']} points)",
                        f"{formatted_ipssr['anc_category']} ({components['ANC']} points)",
                        f"{formatted_ipssr['blast_category']} ({components['Bone Marrow Blasts']} points)",
                        f"{formatted_ipssr['cyto_category']} ({components['Cytogenetics']} points)"
                    ]
                }
                
                df_params = pd.DataFrame(param_data)
                st.table(df_params)
                
                # Add reference note
                st.markdown("""
                <div style="font-size: 0.8em; color: #666; margin-top: 10px; font-style: italic;">
                Reference: Greenberg PL, et al. Revised International Prognostic Scoring System for Myelodysplastic Syndromes. Blood 2012.
                </div>
                """, unsafe_allow_html=True)

def eln_risk_calculator_page():
    """
    This page handles:
      - Display of form for ELN 2022 risk assessment
      - Classification based on ELN 2022 and ELN 2024 (non-intensive) risk stratification
      - Visualization of results with detailed derivation
    """
    # Title / Header
    st.markdown(
        """
        <div style="
            background-color: #FFFFFF;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 20px;
            ">
            <h2 style="color: #009688; text-align: left;">
                ELN Risk Calculator
            </h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Top Controls
    logout_placeholder = st.empty()

    with st.expander("📋 Instructions", expanded=False):
        st.markdown("""
        ## ELN Risk Calculator - Instructions
        
        This tool assesses AML risk according to the European LeukemiaNet (ELN) 2022 risk classification guidelines and 
        the revised ELN 2024 criteria for non-intensive therapy.
        
        ### How to use this tool:
        
        1. **Select Input Method**:
           - **Free-text Mode**: Paste your clinical report text to automatically extract relevant markers.
           - **Manual Mode**: Manually check all cytogenetic and molecular markers present in your case.
        
        2. **Enter Data**:
           - In free-text mode, paste the clinical/genetic report text.
           - In manual mode, check all abnormalities present in the sample.
        
        3. **Calculate Risk**:
           - Click the "Calculate ELN Risk" button to generate the risk assessment.
           
        4. **Review Results**:
           - The results will show risk stratification according to:
              - ELN 2022 standard risk classification
              - ELN 2024 non-intensive therapy risk classification
           - Step-by-step derivation of the risk assessment will be displayed.
           - Median overall survival estimates will be provided based on the risk category.
        """)

    # Import necessary functions
    from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk
    from parsers.eln_parser import parse_eln_report
    from utils.forms import build_manual_eln_data
    
    # Initialize session state for persisting results
    if 'eln_result' not in st.session_state:
        st.session_state['eln_result'] = None
    if 'eln24_result' not in st.session_state:
        st.session_state['eln24_result'] = None
    if 'eln_derivation' not in st.session_state:
        st.session_state['eln_derivation'] = None
    if 'eln24_derivation' not in st.session_state:
        st.session_state['eln24_derivation'] = None
    
    # Toggle for free-text vs. manual mode
    eln_mode_toggle = st.toggle("Free-text Mode", key="eln_mode_toggle", value=True)
    
    eln_data = {}
    
    # FREE TEXT MODE
    if eln_mode_toggle:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("### Input AML/Genetic Report")
            
            st.markdown("""
            Enter your AML report data below. The system will extract relevant genetic and cytogenetic markers 
            for ELN risk classification.
            """)
            
            eln_report_text = st.text_area(
                "Enter report text:",
                placeholder="Paste your genetic/cytogenetic report here including karyotype, FISH results, and molecular mutations...",
                key="eln_free_text_input",
                height=250
            )
            
            # Calculate button
            calculate_button = st.button("Calculate ELN Risk", key="calculate_eln_risk", type="primary")
            if calculate_button:
                if eln_report_text.strip():
                    with st.spinner("Processing report text..."):
                        # Parse the report to extract ELN 2022 markers
                        parsed_eln_data = parse_eln_report(eln_report_text)
                        
                        if parsed_eln_data:
                            st.info("Report processed successfully.")
                            # Store the parsed data
                            st.session_state['original_eln_data'] = parsed_eln_data.copy()
                            
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
                            risk_category, eln22_median_os, derivation = classify_full_eln2022(parsed_eln_data)
                            
                            # Calculate ELN 2024 non-intensive risk
                            try:
                                risk_eln24, median_os_eln24, eln24_deriv = eln2024_non_intensive_risk(eln24_genes)
                            except Exception as e:
                                st.error(f"Error calculating ELN 2024 risk: {str(e)}")
                                risk_eln24 = "Error in calculation"
                                median_os_eln24 = "N/A"
                                eln24_deriv = ["Error in ELN 2024 risk calculation. Please check input data."]
                            
                            # Store results
                            st.session_state['eln_result'] = risk_category
                            st.session_state['eln_derivation'] = derivation
                            st.session_state['eln22_median_os'] = eln22_median_os
                            st.session_state['eln24_result'] = risk_eln24
                            st.session_state['eln24_derivation'] = eln24_deriv
                            st.session_state['median_os_eln24'] = median_os_eln24
                            
                            eln_data = parsed_eln_data
                        else:
                            st.error("Could not extract sufficient data from the report. Please check your input or use manual mode.")
                else:
                    st.error("Please enter report text or switch to manual mode.")

    # MANUAL MODE
    else:
        # Get patient data using the form
        eln_data = build_manual_eln_data()
        
        if st.button("Calculate ELN Risk", key="calculate_eln_manual", type="primary"):
            with st.spinner("Calculating risk..."):
                try:
                    # Store the entered data
                    st.session_state['original_eln_data'] = eln_data.copy()
                    
                    # Prepare data for ELN 2024 non-intensive classification
                    eln24_genes = {
                        "TP53": eln_data.get("tp53_mutation", False),
                        "KRAS": eln_data.get("kras", False),
                        "PTPN11": eln_data.get("ptpn11", False),
                        "NRAS": eln_data.get("nras", False),
                        "FLT3_ITD": eln_data.get("flt3_itd", False),
                        "NPM1": eln_data.get("npm1_mutation", False),
                        "IDH1": eln_data.get("idh1", False),
                        "IDH2": eln_data.get("idh2", False),
                        "DDX41": eln_data.get("ddx41", False)
                    }
                    
                    # Calculate ELN 2022 risk
                    risk_category, eln22_median_os, derivation = classify_full_eln2022(eln_data)
                    
                    # Calculate ELN 2024 non-intensive risk
                    try:
                        risk_eln24, median_os_eln24, eln24_deriv = eln2024_non_intensive_risk(eln24_genes)
                    except Exception as e:
                        st.error(f"Error calculating ELN 2024 risk: {str(e)}")
                        risk_eln24 = "Error in calculation"
                        median_os_eln24 = "N/A"
                        eln24_deriv = ["Error in ELN 2024 risk calculation. Please check input data."]
                    
                    # Store results
                    st.session_state['eln_result'] = risk_category
                    st.session_state['eln_derivation'] = derivation
                    st.session_state['eln22_median_os'] = eln22_median_os
                    st.session_state['eln24_result'] = risk_eln24
                    st.session_state['eln24_derivation'] = eln24_deriv
                    st.session_state['median_os_eln24'] = median_os_eln24
                    
                except Exception as e:
                    st.error(f"Error calculating risk: {str(e)}")
    
    # Add JSON data display expander for transparency
    if 'original_eln_data' in st.session_state:
        with st.expander("Data Inspector - View Extracted Features", expanded=False):
            st.subheader("Features Used for Classification")
            display_data = st.session_state['original_eln_data'].copy()
            if '__prompts' in display_data:
                del display_data['__prompts']
            st.json(display_data)
    
    # Display results if available
    if (st.session_state['eln_result'] is not None and 
        st.session_state['eln24_result'] is not None):
        
        # Style for the results
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
            .risk-subtitle {
                font-size: 1.1rem;
                margin-bottom: 5px;
                font-weight: 500;
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
            .derivation-title {
                font-weight: 600;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 1.2rem;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Get the risk classes
        eln_risk = st.session_state['eln_result']
        eln24_risk = st.session_state['eln24_result']
        
        # Determine CSS class based on risk category
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
        
        eln_class = get_risk_class(eln_risk)
        eln24_class = get_risk_class(eln24_risk)
        
        # Get median OS based on ELN 2022 risk category
        if 'adverse' in eln_risk.lower():
            median_os = "Approximately 8–10 months"
        elif 'favorable' in eln_risk.lower():
            median_os = "Not reached or >60 months"
        else:
            median_os = "Approximately 16–24 months"
        
        # Create a results header
        st.markdown("## Risk Assessment Results")
        
        # Create two columns for the risk displays
        col1, col2 = st.columns(2)
        
        # ELN 2022 Risk
        with col1:
            # Add a default for eln22_median_os in case it's missing from session state
            eln22_median_os = st.session_state.get('eln22_median_os', "Not available")
            
            st.markdown(f"""
            <div class='risk-box {eln_class}'>
                <div class='risk-title'>ELN 2022 Risk</div>
                <div class='risk-value'>{eln_risk}</div>
                <div class='risk-os'>Median OS: {eln22_median_os}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("ELN 2022 Derivation", expanded=False):
                # Check if the derivation is a list of strings (new format) or a single string (old format)
                derivation = st.session_state['eln_derivation']
                if isinstance(derivation, list):
                    for step in derivation:
                        st.markdown(f"- {step}")
                else:
                    # For backwards compatibility with old format
                    st.markdown(derivation)
        
        # ELN 2024 Non-Intensive Risk
        with col2:
            # Add a default for median_os_eln24 in case it's missing from session state
            median_os_eln24 = st.session_state.get('median_os_eln24', "N/A")
            
            # Format the display differently if median_os_eln24 is a string (e.g., "N/A")
            os_display = f"{median_os_eln24} months" if isinstance(median_os_eln24, (int, float)) else median_os_eln24
            
            st.markdown(f"""
            <div class='risk-box {eln24_class}'>
                <div class='risk-title'>ELN 2024 Risk (Non-Intensive Therapy)</div>
                <div class='risk-value'>{eln24_risk}</div>
                <div class='risk-os'>Median OS: {os_display}</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("ELN 2024 Derivation", expanded=False):
                for step in st.session_state['eln24_derivation']:
                    st.markdown(f"- {step}")
        
        # Clinical Implications
        st.markdown("### Clinical Implications")
        
        implications = ""
        if 'adverse' in eln_risk.lower():
            implications = """
            - **Adverse Risk**: Consider enrollment in clinical trials when available.
            - High-risk disease may benefit from intensive induction regimens followed by allogeneic stem cell transplantation (if eligible).
            - Consider novel agent combinations or targeted therapies based on specific mutations.
            - Close monitoring for early relapse is recommended.
            """
        elif 'favorable' in eln_risk.lower():
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
        
        # Notes section with additional clinical considerations
        with st.expander("Additional Notes", expanded=False):
            st.markdown("""
            #### Important Considerations

            - **ELN 2022** is the standard risk stratification for AML patients treated with intensive chemotherapy.
            - **ELN 2024 Non-Intensive** stratification is designed for patients who will receive non-intensive therapy (e.g., venetoclax combinations, HMA therapy).
            - Risk stratification should be considered alongside other clinical factors:
              - Patient age and performance status
              - Comorbidities
              - Prior hematologic disorders (MDS, MPN)
              - History of chemotherapy or radiation (therapy-related AML)
              - Treatment goals (curative vs palliative)
            - Some genetic markers may have treatment implications beyond risk stratification (e.g., IDH1/2 mutations → IDH inhibitors, FLT3 mutations → FLT3 inhibitors).
            """)

##################################
# APP MAIN
##################################
def app_main():
    """
    The main function that manages login checks, sidebar user options,
    and routes between the 'data_entry_page' and 'results_page'.
    """
    token = st.session_state.get("jwt_token")
    user_data = verify_jwt_token(token) if token else None
    if not user_data:
        show_login_page()
        return


    # Add sidebar navigation options
    with st.sidebar:
        selected = option_menu(
            menu_title="Navigation",
            options=["AML/MDS Classifier", "IPSS-M/R Risk Tool", "ELN Risk Calculator"],
            icons=["clipboard-data", "calculator", "graph-up"],
            menu_icon=None,
            default_index=0,
        )
        

    with st.sidebar.expander("User Options", expanded=True):
        st.write("Logged in as:", st.session_state["username"])
        if st.button("Logout"):
            st.session_state["jwt_token"] = None
            st.session_state["username"] = ""
            cookies["jwt_token"] = ""
            cookies.save()
            st.rerun()
        
    if "page" not in st.session_state:
        st.session_state["page"] = "data_entry"
    
    # Handle navigation selection
    if selected == "IPSS-M/R Risk Tool":
        st.session_state["page"] = "ipcc_risk_calculator"
    elif selected == "ELN Risk Calculator":
        st.session_state["page"] = "eln_risk_calculator"
    elif selected == "AML/MDS Classifier" and st.session_state["page"] != "results":
        st.session_state["page"] = "data_entry"

    if st.session_state["page"] == "data_entry":
        data_entry_page()
    elif st.session_state["page"] == "results":
        results_page()
    elif st.session_state["page"] == "ipcc_risk_calculator":
        ipcc_risk_calculator_page()
    elif st.session_state["page"] == "eln_risk_calculator":
        eln_risk_calculator_page()

if __name__ == "__main__":
    app_main()
