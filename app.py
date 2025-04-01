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
from parsers.mds_parser import parse_genetics_report_mds
from parsers.mds_ipcc_parser import parse_ipcc_report
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from classifiers.aml_risk_classifier import classify_ELN2022, eln2024_non_intensive_risk
from classifiers.mds_risk_classifier import RESIDUAL_GENES, get_ipssm_survival_data
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

                classification_who, who_derivation, who_disease_type = classify_combined_WHO2022(manual_data, not_erythroid=False)
                classification_icc, icc_derivation, icc_disease_type = classify_combined_ICC2022(manual_data)
                # Do not call classify_ELN2022 here.
                st.session_state["aml_manual_result"] = {
                    "parsed_data": manual_data,
                    "who_class": classification_who,
                    "who_derivation": who_derivation,
                    "who_disease_type": who_disease_type,
                    "icc_class": classification_icc,
                    "icc_derivation": icc_derivation,
                    "icc_disease_type": icc_disease_type,
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
                            who_class, who_deriv, who_disease_type = classify_combined_WHO2022(parsed_data, not_erythroid=False)
                            icc_class, icc_deriv, icc_disease_type = classify_combined_ICC2022(parsed_data)
                            # Do not call classify_ELN2022 here
                            st.session_state["aml_ai_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                    "who_disease_type": who_disease_type,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                    "icc_disease_type": icc_disease_type,
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
                    who_class, who_deriv, who_disease_type = classify_combined_WHO2022(updated_parsed_data, not_erythroid=False)
                    icc_class, icc_deriv, icc_disease_type = classify_combined_ICC2022(updated_parsed_data)
                    # Again, do not call classify_ELN2022 here; let it be computed in results.
                    st.session_state["aml_ai_result"] = {
                        "parsed_data": updated_parsed_data,
                        "who_class": who_class,
                        "who_derivation": who_deriv,
                                "who_disease_type": who_disease_type,
                        "icc_class": icc_class,
                        "icc_derivation": icc_deriv,
                                "icc_disease_type": icc_disease_type,
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
    
    # Get disease types from the classification results
    who_disease_type = res.get("who_disease_type", "Unknown")
    icc_disease_type = res.get("icc_disease_type", "Unknown")
    
    # Determine which risk assessments to show
    show_eln = who_disease_type == "AML" or icc_disease_type == "AML"
    show_ipss = who_disease_type == "MDS" or icc_disease_type == "MDS"
    
    # Set up the options menu based on which risk assessments to show
    if show_eln and show_ipss:
        # If both AML and MDS were diagnosed, show separate risk options
        options = ["Classification", "ELN Risk (AML)", "IPSS Risk (MDS)", "MRD Review", "Gene Review", "AI Comments", "Differentiation"]
        icons = ["clipboard", "graph-up-arrow", "calculator", "recycle", "bar-chart", "chat-left-text", "funnel"]
    else:
        # Just show a single Risk option
        options = ["Classification", "Risk", "MRD Review", "Gene Review", "AI Comments", "Differentiation"]
        icons = ["clipboard", "graph-up-arrow", "recycle", "bar-chart", "chat-left-text", "funnel"]

    sub_tab = option_menu(
        menu_title=None,
        options=options,
        icons=icons,
        default_index=0,
        orientation="horizontal"
    )
    
    # Store the current sub_tab in session state to use in the instruction expander
    st.session_state["results_sub_tab"] = sub_tab

    # If disease types disagree, show a notification at the top
    if show_eln and show_ipss and who_disease_type != icc_disease_type and who_disease_type != "Unknown" and icc_disease_type != "Unknown":
        st.info(f"Note: WHO 2022 classified this as {who_disease_type} while ICC 2022 classified it as {icc_disease_type}. Both risk assessment systems are available in the options above.")

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

    elif sub_tab == "ELN Risk (AML)":
        # Import necessary functions for risk assessment
        from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk
        from parsers.aml_eln_parser import parse_eln_report
        

        
        # Style for risk boxes - needed for risk assessments
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
        
        # Display ELN risk assessment
        show_eln_risk_assessment(res, free_text_input_value)
    
    elif sub_tab == "IPSS Risk (MDS)":
        # Import necessary functions for risk assessment
        from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
        from parsers.mds_ipcc_parser import parse_ipcc_report
        

        # Style for risk boxes - needed for risk assessments
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
        
        # Display IPSS risk assessment
        show_ipss_risk_assessment(res, free_text_input_value)

    elif sub_tab == "Risk":
        # Import necessary functions for risk assessment
        from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk
        from parsers.aml_eln_parser import parse_eln_report
        from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
        from parsers.mds_ipcc_parser import parse_ipcc_report
        

        # Style for risk boxes - needed for both types of risk assessments
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

        # Display the appropriate risk assessment based on the disease type
        if show_eln and show_ipss:
            # This case shouldn't happen anymore as we're showing separate tabs,
            # but keep it as a fallback just in case
            risk_tabs = st.tabs(["ELN Risk (AML)", "IPSS Risk (MDS)"])
            
            with risk_tabs[0]:
                show_eln_risk_assessment(res, free_text_input_value)
                
            with risk_tabs[1]:
                show_ipss_risk_assessment(res, free_text_input_value)
        elif show_eln:
            show_eln_risk_assessment(res, free_text_input_value)
        elif show_ipss:
            show_ipss_risk_assessment(res, free_text_input_value)
        else:
            st.warning("No risk assessment models are applicable for this classification.")

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

    # PDF Download Form
    if st.session_state.get("show_pdf_form"):
        with st.form(key="pdf_info_form"):
            patient_name = st.text_input("Enter patient name (client-side only):")
            patient_dob = st.text_input("Enter patient date of birth (dd/mm/yyyy):", placeholder="dd/mm/yyyy")
            user_comments = st.text_area("Enter user comments (optional):")
            submit_pdf = st.form_submit_button("Submit")

        if submit_pdf:
            if not patient_name:
                st.error("Please enter the patient name.")
            elif not patient_dob:
                st.error("Please enter the patient date of birth.")
            else:
                try:
                    dob = datetime.datetime.strptime(patient_dob, "%d/%m/%Y")
                    dob_str = dob.strftime("%B %d, %Y")
                except Exception:
                    st.error("Date of birth must be in dd/mm/yyyy format.")
                    return
                
                base_pdf_bytes = create_base_pdf(user_comments=user_comments)
                base_pdf_b64 = base64.b64encode(base_pdf_bytes).decode("utf-8")
                js_code = f"""
                <input type="hidden" id="base_pdf" value="{base_pdf_b64}">
                <input type="hidden" id="patient_name" value="{patient_name}">
                <input type="hidden" id="patient_dob" value="{dob_str}">
                <script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>
                <script>
                async function addPatientInfoAndDownload() {{
                    const {{ PDFDocument, rgb }} = PDFLib;
                    const basePdfB64 = document.getElementById("base_pdf").value;
                    const patientName = document.getElementById("patient_name").value;
                    const patientDob = document.getElementById("patient_dob").value;
                    const basePdfBytes = Uint8Array.from(atob(basePdfB64), c => c.charCodeAt(0));
                    const pdfDoc = await PDFDocument.load(basePdfBytes);
                    const pages = pdfDoc.getPages();
                    const firstPage = pages[0];
                    firstPage.drawText("Patient Name: " + patientName, {{
                        x: 50,
                        y: firstPage.getHeight() - 50,
                        size: 12,
                        color: rgb(0, 0, 0)
                    }});
                    firstPage.drawText("Date of Birth: " + patientDob, {{
                        x: 50,
                        y: firstPage.getHeight() - 70,
                        size: 12,
                        color: rgb(0, 0, 0)
                    }});
                    const modifiedPdfBytes = await pdfDoc.save();
                    const blob = new Blob([modifiedPdfBytes], {{ type: "application/pdf" }});
                    const link = document.createElement("a");
                    link.href = URL.createObjectURL(blob);
                    link.download = patientName + "-diagnostic-report.pdf";
                    link.click();
                }}
                addPatientInfoAndDownload();
                </script>
                """
                components.html(js_code, height=0)
                st.session_state.show_pdf_form = False

    # Incorrect Result Form
    if st.session_state.get("show_report_incorrect"):
        incorrect_comment = st.text_area("Please explain why the report is incorrect:")
        if st.button("Generate Email Link"):
            report_pdf_bytes = create_base_pdf(user_comments="")
            base_pdf_b64 = base64.b64encode(report_pdf_bytes).decode("utf-8")
            js_code = f"""
            <input type="hidden" id="base_pdf" value="{base_pdf_b64}">
            <script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>
            <script>
            async function autoDownloadPDF() {{
                const basePdfB64 = document.getElementById("base_pdf").value;
                const basePdfBytes = Uint8Array.from(atob(basePdfB64), c => c.charCodeAt(0));
                const blob = new Blob([basePdfBytes], {{ type: "application/pdf" }});
                const link = document.createElement("a");
                link.href = URL.createObjectURL(blob);
                link.download = "diagnostic-report.pdf";
                link.click();
            }}
            autoDownloadPDF();
            </script>
            """
            components.html(js_code, height=0)
            subject = urllib.parse.quote("Incorrect AML/MDS Diagnostic Report Feedback")
            body = urllib.parse.quote(
                f"User reported an incorrect diagnostic result.\n\nComment:\n{incorrect_comment}\n\n"
                "Please attach the downloaded report PDF manually."
            )
            mailto_link = f"mailto:robbielee543@gmail.com?subject={subject}&body={body}"
            st.markdown(f"[Click here to send your feedback]({mailto_link})", unsafe_allow_html=True)
            st.session_state.show_report_incorrect = False

# Helper function to determine CSS class based on risk category
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

# Helper function for IPSS risk class colors
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

# Function to display ELN risk assessment for AML
def show_eln_risk_assessment(res, free_text_input_value):
    from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk, classify_ELN2022
    from parsers.aml_eln_parser import parse_eln_report
    
    st.markdown("## ELN Risk Assessment")
    st.markdown("European LeukemiaNet risk stratification for AML.")
    
    st.markdown("")  # Add empty line for spacing
    
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
    
    st.markdown("")  # Add empty line for spacing
    
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
    
    st.markdown("")  # Add empty line for spacing
    
    # Display the original data for transparency
    if 'original_eln_data' in st.session_state:
        with st.expander("Data Inspector - ELN Features", expanded=False):
            st.subheader("Features Used for ELN Classification")
            display_data = st.session_state['original_eln_data'].copy()
            if '__prompts' in display_data:
                del display_data['__prompts']
            st.json(display_data)

# Function to display IPSS risk assessment for MDS
def show_ipss_risk_assessment(res, free_text_input_value):
    from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
    from parsers.mds_ipcc_parser import parse_ipcc_report
    
    st.markdown("## IPSS Risk Assessment")
    st.markdown("International Prognostic Scoring System for myelodysplastic syndromes.")
    
    st.markdown("")  # Add empty line for spacing
    
    # Add custom styling to match the dedicated calculator
    st.markdown("""
    <style>
        .score-box {
            background-color: white;
            padding: 15px;
            border: 1px solid #eee;
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
    </style>
    """, unsafe_allow_html=True)
    
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
    
    st.markdown("")  # Add empty line for spacing
    
    # Button to calculate with overrides
    calculate_button = st.button("Calculate IPSS Risk", key="calculate_ipss_with_overrides", type="primary")
    
    # IPSS-M/R Risk data section - Only run when calculate button is pressed
    if calculate_button and free_text_input_value:
        # Parse the free text for IPCC risk parameters
        ipcc_data = parse_ipcc_report(free_text_input_value)
        
        if ipcc_data:
            # Apply overrides if specified by user
            if hb_override > 0:
                ipcc_data["HB"] = hb_override
                st.info(f"Using override for Hemoglobin: {hb_override} g/dL")
            
            if plt_override > 0:
                ipcc_data["PLT"] = plt_override
                st.info(f"Using override for Platelets: {plt_override} × 10^9/L")
            
            if anc_override > 0:
                ipcc_data["ANC"] = anc_override
                st.info(f"Using override for ANC: {anc_override} × 10^9/L")
            
            if blast_override > 0:
                ipcc_data["BM_BLAST"] = blast_override
                st.info(f"Using override for Bone Marrow Blasts: {blast_override}%")
            
            if age_override > 18:  # Age 18 is the minimum and signals "not set"
                ipcc_data["AGE"] = age_override
                st.info(f"Using override for Age: {age_override} years")
            
            if cyto_override != "Use from report":
                ipcc_data["CYTO_IPSSR"] = cyto_override
                st.info(f"Using override for Cytogenetic Risk: {cyto_override}")
            
            st.markdown("")  # Add empty line for spacing
            
            # Create tabs for IPSS-M and IPSS-R, matching the dedicated calculator
            ipcc_tabs = st.tabs(["IPSS-M", "IPSS-R"])
            
            # ------------------- IPSS-M TAB -------------------
            with ipcc_tabs[0]:
                # Calculate IPSS-M scores
                ipssm_result = calculate_ipssm(patient_data=ipcc_data)
                
                if ipssm_result:
                    st.markdown("")  # Add empty line for spacing
                    st.markdown("#### Risk Calculations")
                    st.markdown("The IPSS-M risk score combines clinical and genetic factors to predict outcomes in myelodysplastic syndromes. The three scenarios below account for possible variations in incomplete data.")
                    
                   
                    
                    # Display mean, best, and worst case scenarios in three columns
                    mean_best_worst_cols = st.columns(3)
                    
                    # Mean case
                    with mean_best_worst_cols[0]:
                        mean_result = ipssm_result.get("means", {})
                        mean_color = get_risk_class_color(mean_result.get('risk_cat', 'Intermediate'))
                        st.markdown(f"""
                        <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Mean Risk</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{mean_result.get('risk_score', 'N/A')}</div>
                            <div style="background-color: {mean_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {mean_result.get('risk_cat', 'Unable to calculate')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Best case
                    with mean_best_worst_cols[1]:
                        best_result = ipssm_result.get("best", {})
                        best_color = get_risk_class_color(best_result.get('risk_cat', 'Low'))
                        st.markdown(f"""
                        <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Best Case</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{best_result.get('risk_score', 'N/A')}</div>
                            <div style="background-color: {best_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {best_result.get('risk_cat', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Worst case
                    with mean_best_worst_cols[2]:
                        worst_result = ipssm_result.get("worst", {})
                        worst_color = get_risk_class_color(worst_result.get('risk_cat', 'High'))
                        st.markdown(f"""
                        <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Worst Case</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{worst_result.get('risk_score', 'N/A')}</div>
                            <div style="background-color: {worst_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {worst_result.get('risk_cat', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    

                    st.markdown("")  # Add empty line for spacing
                    # Add Expected Outcomes section based on risk category
                    st.markdown("### Expected Outcomes")
                    st.markdown("""The following outcomes are associated with this IPSS-M risk category based on clinical data:
                    **Note:** Survival times shown represent median values with 25th-75th percentile ranges in parentheses.""")
                    

                    # Get survival data for the mean risk category
                    mean_risk_cat = mean_result.get('risk_cat', 'Intermediate')
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

                    st.markdown("")  # Add empty line for spacing
                    
                    # Add a reference note
                    st.markdown("""
                    <div style="font-size: 0.8em; color: #666; margin-top: 10px; font-style: italic;">
                    Data based on IPSS-M validation cohort studies. Individual patient outcomes may vary based on additional factors.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("")  # Add empty line for spacing
                    
                    # Patient data display
                    with st.expander("View Patient Data", expanded=False):
                        st.markdown("##### Patient Values")
                        for key, value in ipcc_data.items():
                            if not key.startswith("__") and isinstance(value, (int, float, str)) and key not in ["IPSSM_CAT", "IPSSM_SCORE"]:
                                st.markdown(f"- **{key}:** {value}")
                else:
                    st.warning("Insufficient data to calculate IPSS-M risk score.")
            
            # ------------------- IPSS-R TAB -------------------
            with ipcc_tabs[1]:
                # Calculate IPSS-R scores
                ipssr_result = calculate_ipssr(patient_data=ipcc_data)
                
                if ipssr_result:
                    st.markdown("### IPSS-R Risk Classification")
                    st.markdown("The IPSS-R score evaluates myelodysplastic syndromes based on cytogenetics, bone marrow blasts, and blood counts. The age-adjusted version (IPSS-RA) accounts for the impact of age on risk.")
                    
                    st.markdown("")  # Add empty line for spacing
                    
                    # Display IPSS-R scores in a single row with matching panel styles
                    st.markdown("#### Risk Calculations")
                    
                    st.markdown("")  # Add empty line for spacing
                    
                    ipssr_cols = st.columns(2)
                    
                    # IPSS-R Score panel
                    with ipssr_cols[0]:
                        ipssr_cat = ipssr_result.get('IPSSR_CAT', 'Intermediate')
                        ipssr_color = get_risk_class_color(ipssr_cat)
                        ipssr_score = ipssr_result.get('IPSSR_SCORE', 'N/A')
                        st.markdown(f"""
                        <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Standard IPSS-R</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{ipssr_score}</div>
                            <div style="background-color: {ipssr_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {ipssr_cat}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # IPSS-RA Score panel
                    with ipssr_cols[1]:
                        ipssra_cat = ipssr_result.get('IPSSRA_CAT', 'Intermediate')
                        ipssra_color = get_risk_class_color(ipssra_cat)
                        ipssra_score = ipssr_result.get('IPSSRA_SCORE', 'N/A')
                        st.markdown(f"""
                        <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Age-Adjusted IPSS-RA</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{ipssra_score}</div>
                            <div style="background-color: {ipssra_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {ipssra_cat}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("")  # Add empty line for spacing
                    
                    # Score components details
                    with st.expander("IPSS-R Score Components", expanded=False):
                        if "components" in ipssr_result:
                            st.markdown("##### Score Components")
                            for component, value in ipssr_result["components"].items():
                                st.markdown(f"- **{component}:** {value}")
                        
                        st.markdown("##### Patient Values")
                        for key in ["HB", "PLT", "ANC", "BM_BLAST", "AGE", "CYTO_IPSSR"]:
                            if key in ipcc_data:
                                st.markdown(f"- **{key}:** {ipcc_data[key]}")
                        
                        # Add reference note
                        st.markdown("""
                        <div style="font-size: 0.8em; color: #666; margin-top: 10px; font-style: italic;">
                        Reference: Greenberg PL, et al. Revised International Prognostic Scoring System for Myelodysplastic Syndromes. Blood 2012.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("Insufficient data to calculate IPSS-R risk score.")
        else:
            st.warning("Insufficient data to calculate IPSS-M/R risk scores. The free text may not contain all necessary information for risk assessment.")
    else:
        st.info("IPSS-M/R Risk assessment requires free text input with MDS-related data. This feature is only available when using the AI-assisted mode with free text input.")
        st.markdown("""
        Consider using the dedicated IPSS-M/R Risk Tool page for more detailed classification.
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
