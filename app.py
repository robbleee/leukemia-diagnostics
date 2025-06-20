import streamlit as st
# IMPORTANT: Call set_page_config as the very first Streamlit command.
st.set_page_config(
    page_title="Haem.io",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="public/favicon.svg"
)

# Import base64 early for favicon
import base64

# Add DNA/Gene favicon
favicon_svg = '''
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64px" height="64px">
    <path fill="#009688" d="M32,10c-12.15,0-22,8.58-22,19.09c0,5.68,6.49,12.85,13.3,19.71C27.93,53.56,30.54,57,32,57	c1.46,0,4.07-3.44,8.7-8.2C47.51,41.94,54,34.77,54,29.09C54,18.58,44.15,10,32,10z"/>
    <path fill="#FFFFFF" d="M44,22c0,2-3.18,3-7.09,3S30,24,30,22s3.18-3,7.09-3S44,20,44,22z M44,37c0,2-3.18,3-7.09,3S30,39,30,37s3.18-3,7.09-3S44,35,44,37z M34,29c0,2-3.18,3-7.09,3S20,31,20,29s3.18-3,7.09-3S34,27,34,29z"/>
    <path fill="#FFFFFF" d="M32,48c0,0-11-9.83-11-20c0-5.5,3.5-9.26,11-10c11,1.09,11,10,11,10S43,38.17,32,48z"/>
    <path fill="#009688" d="M35,16c0,1.1-0.9,2-2,2h-2c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h2C34.1,14,35,14.9,35,16L35,16z"/>
    <path fill="#009688" d="M35,44c0,1.1-0.9,2-2,2h-2c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h2C34.1,42,35,42.9,35,44L35,44z"/>
    <path fill="#009688" d="M35,36c0,1.1-0.9,2-2,2h-2c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h2C34.1,34,35,34.9,35,36L35,36z"/>
    <path fill="#009688" d="M35,24c0,1.1-0.9,2-2,2h-2c-1.1,0-2-0.9-2-2l0,0c0-1.1,0.9-2,2-2h2C34.1,22,35,22.9,35,24L35,24z"/>
</svg>
'''
favicon_base64 = base64.b64encode(favicon_svg.encode("utf-8")).decode("utf-8")
st.markdown(
    f'<link rel="icon" href="data:image/svg+xml;base64,{favicon_base64}">',
    unsafe_allow_html=True
)

import urllib.parse
import bcrypt
import datetime
import jwt
import math
import pandas as pd
import matplotlib.pyplot as plt
import yaml
from streamlit_option_menu import option_menu
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

from classifiers.aml_risk_classifier import eln2022_intensive_risk, eln2024_non_intensive_risk
from parsers.aml_eln_parser import parse_eln_report
from utils.forms import build_manual_eln_data
from parsers.aml_parser import parse_genetics_report_aml
from parsers.mds_parser import parse_genetics_report_mds
from parsers.mds_ipss_parser import parse_ipss_report
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from classifiers.aml_risk_classifier import eln2022_intensive_risk, eln2024_non_intensive_risk
from classifiers.mds_risk_classifier import RESIDUAL_GENES, get_ipssm_survival_data
from reviewers.aml_reviewer import (
    get_gpt4_review_aml_classification,
    get_gpt4_review_aml_genes,
    get_gpt4_review_aml_additional_comments,
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
    build_manual_ipss_data,
    build_manual_eln_data
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
    # Remove the default Streamlit padding/margin and apply base styling
    st.markdown("""
    <style>
        /* Base styling */
        .stApp {
            background: linear-gradient(135deg, #f5f8fa 0%, #e8f4f8 100%) !important;
        }
        
        /* Hide Streamlit elements */
        #MainMenu, footer, header {
            visibility: hidden;
        }
        
        /* Style the input fields */
        div[data-testid="stVerticalBlock"] > div:has(section.main) {
            max-width: 500px !important;
            margin: 0 auto !important;
            padding-top: 3rem !important;
        }
        
        /* Label styling */
        .stTextInput label {
            font-weight: 500;
            font-size: 0.9rem;
            color: #546e7a;
        }
        
        /* Input field styling */
        .stTextInput input {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: #f5f8fa;
            padding: 12px 15px;
            font-size: 0.95rem;
            transition: all 0.2s ease;
        }
        
        .stTextInput input:focus {
            border-color: #009688;
            background-color: white;
            box-shadow: 0 0 0 2px rgba(0, 150, 136, 0.2);
        }
        
        /* Button styling */
        .stButton button {
            background: linear-gradient(90deg, #009688, #00897b);
            color: white;
            border-radius: 8px;
            padding: 12px 15px;
            font-size: 1rem;
            font-weight: 600;
            width: 100%;
            border: none;
            box-shadow: 0 4px 12px rgba(0, 150, 136, 0.25);
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stButton button:hover {
            background: linear-gradient(90deg, #00897b, #00796b);
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(0, 150, 136, 0.3);
        }
        
        .stButton button:active {
            transform: translateY(0);
        }
        

        /* Logo and title styling */
        .logo-container {
            text-align: center;
            margin-bottom: 25px;
        }
        
        .app-icon {
            font-size: 42px;
            color: #009688;
            background: rgba(0, 150, 136, 0.1);
            height: 80px;
            width: 80px;
            line-height: 80px;
            border-radius: 50%;
            margin: 0 auto 15px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .app-title {
            color: #00796b;
            font-size: 2.2rem;
            font-weight: 700;
            margin: 10px 0 5px;
            background: linear-gradient(90deg, #00796b, #009688);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .app-subtitle {
            color: #546e7a;
            font-size: 1rem;
            margin-bottom: 0;
            font-weight: 400;
        }
        
        /* Version styling */
        .version-text {
            text-align: center;
            font-size: 0.8rem;
            color: #78909c;
            margin-top: 20px;
        }
        
        /* Add responsive padding */
        @media (max-width: 768px) {
            div[data-testid="stVerticalBlock"] > div:has(section.main) {
                padding: 1rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Use 3 columns to center the login form 
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # Create card container
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # Logo and branding
        st.markdown("""
        <div class="logo-container">
            <h1 class="app-title">Haem.io</h1>
            <p class="app-subtitle">Haematology classification Support tool</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        username = st.text_input("Username", placeholder="Enter your username", key="username_input")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="password_input")
        
        # Login button
        login_button = st.empty()
        if login_button.button("Sign In", key="login_button"):
            if authenticate_user(username, password):
                with login_button:
                    st.success("Signing in...")
                token = create_jwt_token(username)
                st.session_state["jwt_token"] = token
                st.session_state["username"] = username
                cookies["jwt_token"] = token
                cookies.save()
                st.rerun()
            else:
                st.error("Invalid username or password!")
        
        st.markdown('<div class="version-text">Version 1.2.0</div>', unsafe_allow_html=True)
        
        # Close the card container
        st.markdown('</div>', unsafe_allow_html=True)

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
                AML/MDS Classifier
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
    # Check if we have previously saved mode
    previous_mode = st.session_state.get("previous_aml_mode_toggle", True)
    aml_mode_toggle = st.toggle("Free-text Mode", key="aml_mode_toggle", value=previous_mode)
    # Save the current mode for future reference
    st.session_state["previous_aml_mode_toggle"] = aml_mode_toggle
    
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
                    "blast_percentage_known",
                    "erythroid_form_submitted",  # Clear erythroid form submission state
                    "mds_who_confirmation",      # Clear MDS WHO form state
                    "mds_icc_confirmation"       # Clear MDS ICC form state
                ]:
                    st.session_state.pop(k, None)
                
                # Check if TP53 data is present
                biallelic_tp53 = manual_data.get("Biallelic_TP53_mutation", {})
                if biallelic_tp53.get("tp53_mentioned", False) or any(val for key, val in biallelic_tp53.items() if key != "tp53_mentioned" and val):
                    # TP53 information detected, store data and show confirmation dialog
                    st.session_state["tp53_confirmation_needed"] = True
                    st.session_state["tp53_data_to_confirm"] = biallelic_tp53
                    st.session_state["parsed_data_pre_tp53_confirm"] = manual_data
                    st.session_state["is_manual_mode"] = True  # Flag to know it's from manual mode
                else:
                    # No TP53 data, proceed with classification
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
                    st.session_state["page"] = "results"
            st.session_state["aml_busy"] = False
            if not st.session_state.get("tp53_confirmation_needed"):
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
                    # Use saved value if available
                    default_blasts = st.session_state.get("saved_bone_marrow_blasts", 0.0)
                    bone_marrow_blasts = st.number_input(
                        "Agreed blast count(%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=1.0, 
                        value=default_blasts,
                        key="bone_marrow_blasts_initial",
                        help="Leave at 0 to use value from report. Only set if you want to override."
                    )
                    # Save the value for future use
                    st.session_state["saved_bone_marrow_blasts"] = bone_marrow_blasts
                with col1:
                    # Use saved value if available
                    default_therapy = st.session_state.get("saved_prior_therapy", "None")
                    prior_therapy = st.selectbox(
                        "Previous cytotoxic therapy",
                        options=["None", "Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions (ICC)", "Any combination"],
                        index=["None", "Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions (ICC)", "Any combination"].index(default_therapy),
                        key="prior_therapy"
                    )
                    # Save the value for future use
                    st.session_state["saved_prior_therapy"] = prior_therapy
                with col2:
                    # Use saved value if available
                    default_germline = st.session_state.get("saved_germline_status", "None")
                    germline_status = st.selectbox(
                        "Germline predisposition",
                        options=["Yes", "None", "Undetermined"],
                        index=["Yes", "None", "Undetermined"].index(default_germline),
                        key="germline_status"
                    )
                    # Save the value for future use
                    st.session_state["saved_germline_status"] = germline_status
                with col3:
                    # Use saved value if available
                    default_mds = st.session_state.get("saved_previous_mds", "None")
                    previous_mds = st.selectbox(
                        "Previous MDS/MPN History", 
                        options=["None", "Previous MDS", "Previous MDS/MPN", "Previous MPN"],
                        index=["None", "Previous MDS", "Previous MDS/MPN", "Previous MPN"].index(default_mds) if default_mds in ["None", "Previous MDS", "Previous MDS/MPN", "Previous MPN"] else 0,
                        key="previous_mds"
                    )
                    # Save the value for future use
                    st.session_state["saved_previous_mds"] = previous_mds
                    
                # Show warning for Previous MPN selection (outside the column to avoid interference)
                if st.session_state.get("previous_mds") == "Previous MPN":
                    st.error("⚠️ **WARNING**: Do not use this classification system for patients with previous MPN. Please refer to specialist MPN guidelines for classification.")
            
            if germline_status == "Yes":
                # Use saved selected germline mutations if available
                default_germline_selections = st.session_state.get("saved_selected_germline", [])
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
                    default=default_germline_selections,
                    key="selected_germline"
                )
                # Save the selection for future use
                st.session_state["saved_selected_germline"] = selected_germline
                
                # Ensure at least one germline mutation is selected when germline is set to "Yes"
                if not selected_germline:
                    st.error("Please select at least one germline mutation when 'Germline predisposition' is set to 'Yes'.")
            
            # Use saved report text if available
            default_report_text = st.session_state.get("saved_full_text_input", "")
            full_report_text = st.text_area(
                "Enter all relevant AML/MDS data here:",
                value=default_report_text,
                placeholder="Paste your AML/MDS report here including: clinical info, CBC, bone marrow findings, cytogenetics, mutations...",
                key="full_text_input",
                height=250
            )
            # Save the input for future use
            st.session_state["saved_full_text_input"] = full_report_text
            
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
                        "blast_percentage_known",
                        "erythroid_form_submitted",  # Clear erythroid form submission state
                        "mds_who_confirmation",      # Clear MDS WHO form state
                        "mds_icc_confirmation"       # Clear MDS ICC form state
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
                            opt_text += f"Previous hematologic malignancy: {previous_mds}. "

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
                                # Store the parsed data in session state for potential TP53 confirmation
                                st.session_state["parsed_data_pre_tp53_confirm"] = parsed_data
                                
                                # Check if TP53 was mentioned in the report - if so, show confirmation dialog
                                biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
                                if biallelic_tp53.get("tp53_mentioned", False):
                                    st.session_state["tp53_confirmation_needed"] = True
                                    st.session_state["tp53_data_to_confirm"] = biallelic_tp53
                                    st.rerun()
                                else:
                                    # If no TP53 mentioned, proceed directly with classification
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

        # TP53 Confirmation Interface
        if st.session_state.get("tp53_confirmation_needed"):
            st.warning("⚠️ **TP53 information detected!** Due to the critical importance of TP53 in risk assessment, please confirm or modify the detected TP53 information.", icon="⚠️")
            
            with st.expander("TP53 Confirmation", expanded=True):
                st.markdown("### TP53 Information Confirmation")
                st.markdown("TP53 mutations significantly impact prognosis and treatment decisions. Please verify the detected information:")
                
                tp53_data = st.session_state["tp53_data_to_confirm"]
                
                # Create editable fields for each TP53 property
                tp53_mentioned = st.checkbox(
                    "TP53 mentioned in report", 
                    value=tp53_data.get("tp53_mentioned", False),
                    help="Indicates whether TP53 is mentioned anywhere in the report"
                )
                
                multiple_mutations = st.checkbox(
                    "Multiple TP53 mutations (2 or more)", 
                    value=tp53_data.get("2_x_TP53_mutations", False),
                    help="Indicates presence of two or more distinct TP53 mutations"
                )
                
                mutation_with_del17p = st.checkbox(
                    "TP53 mutation with deletion of 17p", 
                    value=tp53_data.get("1_x_TP53_mutation_del_17p", False),
                    help="Indicates one TP53 mutation combined with deletion of chromosome 17p"
                )
                
                mutation_with_loh = st.checkbox(
                    "TP53 mutation with loss of heterozygosity (LOH)", 
                    value=tp53_data.get("1_x_TP53_mutation_LOH", False),
                    help="Indicates one TP53 mutation with loss of heterozygosity"
                )
                
                mutation_with_10pct_vaf = st.checkbox(
                    "TP53 mutation with VAF ≥ 10%", 
                    value=tp53_data.get("1_x_TP53_mutation_10_percent_vaf", False),
                    help="Indicates one TP53 mutation with variant allele frequency of at least 10%"
                )
                
                mutation_with_50pct_vaf = st.checkbox(
                    "TP53 mutation with VAF ≥ 50%", 
                    value=tp53_data.get("1_x_TP53_mutation_50_percent_vaf", False),
                    help="Indicates one TP53 mutation with variant allele frequency of at least 50%"
                )
                
                st.markdown("---")
                
                if st.button("Confirm TP53 Information and Proceed", type="primary"):
                    # Update the TP53 data in the parsed data
                    parsed_data = st.session_state["parsed_data_pre_tp53_confirm"]
                    parsed_data["Biallelic_TP53_mutation"] = {
                        "tp53_mentioned": tp53_mentioned,
                        "2_x_TP53_mutations": multiple_mutations,
                        "1_x_TP53_mutation_del_17p": mutation_with_del17p,
                        "1_x_TP53_mutation_LOH": mutation_with_loh,
                        "1_x_TP53_mutation_10_percent_vaf": mutation_with_10pct_vaf,
                        "1_x_TP53_mutation_50_percent_vaf": mutation_with_50pct_vaf
                    }
                    
                    # Now proceed with classification using the updated data
                    with st.spinner("Classifying with confirmed TP53 data..."):
                        st.session_state["blast_percentage_known"] = True
                        who_class, who_deriv, who_disease_type = classify_combined_WHO2022(parsed_data, not_erythroid=False)
                        icc_class, icc_deriv, icc_disease_type = classify_combined_ICC2022(parsed_data)
                        
                        # Check if this is from manual mode or AI mode
                        is_manual = st.session_state.get("is_manual_mode", False)
                        
                        if is_manual:
                            # Store in manual result state
                            st.session_state["aml_manual_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "who_disease_type": who_disease_type,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                "icc_disease_type": icc_disease_type,
                                "free_text_input": ""  # Empty for manual mode
                            }
                            # Clear manual mode flag
                            st.session_state.pop("is_manual_mode", None)
                        else:
                            # Store in AI result state
                            st.session_state["aml_ai_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "who_disease_type": who_disease_type,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                "icc_disease_type": icc_disease_type,
                                "free_text_input": st.session_state.get("full_text_input", "")
                            }
                        
                        st.session_state["expanded_aml_section"] = "classification"
                        st.session_state["aml_busy"] = False
                        
                        # Clear the confirmation flags
                        st.session_state.pop("tp53_confirmation_needed", None)
                        st.session_state.pop("tp53_data_to_confirm", None)
                        st.session_state.pop("parsed_data_pre_tp53_confirm", None)
                        
                        # Go to results page
                        st.session_state["page"] = "results"
                        st.rerun()
                
        elif st.session_state.get("initial_parsed_data"):
            st.warning("Either the blast percentage could not be automatically determined or the differentiation is ambiguous/missing. Please provide the missing information to proceed with classification.")
            with st.expander("Enter Manual Inputs", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    default_blast = 0.0
                    if st.session_state["initial_parsed_data"].get("blasts_percentage") not in [None, "Unknown"]:
                        default_blast = float(st.session_state["initial_parsed_data"]["blasts_percentage"])
                    # Check for saved value
                    saved_blast = st.session_state.get("saved_manual_blast_input", default_blast)
                    manual_blast_percentage = st.number_input(
                        "Enter Blast Percentage (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=saved_blast, 
                        key="manual_blast_input"
                    )
                    # Save for future use
                    st.session_state["saved_manual_blast_input"] = manual_blast_percentage
                
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
                        # Check for saved value
                        default_diff = list(diff_map.keys())[0]
                        saved_diff = st.session_state.get("saved_manual_differentiation", default_diff)
                        manual_differentiation = st.selectbox(
                            "Select Differentiation", 
                            list(diff_map.keys()),
                            index=list(diff_map.keys()).index(saved_diff) if saved_diff in diff_map.keys() else 0,
                            key="manual_differentiation_input"
                        )
                        # Save for future use
                        st.session_state["saved_manual_differentiation"] = manual_differentiation

                # Moved the analyse button inside the expander and made it primary
                submit_button = st.button("Analyse With Manual Inputs", key="submit_manual", type="primary")
                if submit_button:
                    # Check if germline status is "Yes" but no mutations are selected
                    if st.session_state.get("germline_status") == "Yes" and not st.session_state.get("selected_germline"):
                        st.error("Please select at least one germline mutation when 'Germline predisposition' is set to 'Yes'.")
                    else:
                        # Clear previous results and form states
                        for k in [
                            "aml_ai_result",
                            "aml_class_review",
                            "aml_mrd_review",
                            "aml_gene_review",
                            "aml_additional_comments",
                            "erythroid_form_submitted",  # Clear erythroid form submission state
                            "mds_who_confirmation",      # Clear MDS WHO form state
                            "mds_icc_confirmation"       # Clear MDS ICC form state
                        ]:
                            st.session_state.pop(k, None)
                            
                        updated_parsed_data = st.session_state.get("initial_parsed_data") or {}
                        updated_parsed_data["blasts_percentage"] = manual_blast_percentage
                        updated_parsed_data["bone_marrow_blasts_override"] = st.session_state["bone_marrow_blasts_initial"]

                if updated_parsed_data.get("AML_differentiation") is None or (updated_parsed_data.get("AML_differentiation") or "").lower() == "ambiguous":
                    diff_str = diff_map[manual_differentiation]
                    updated_parsed_data["AML_differentiation"] = diff_str

                with st.spinner("Processing manual inputs..."):
                    # Check if TP53 was mentioned in the data - if so, we'll handle it via the confirmation interface
                    biallelic_tp53 = updated_parsed_data.get("Biallelic_TP53_mutation", {})
                    if biallelic_tp53.get("tp53_mentioned", False):
                        st.session_state["tp53_confirmation_needed"] = True
                        st.session_state["tp53_data_to_confirm"] = biallelic_tp53
                        st.session_state["parsed_data_pre_tp53_confirm"] = updated_parsed_data
                        st.rerun()
                    else:
                        # If no TP53 mentioned, proceed directly with classification
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
def display_treatment_data_explorer(patient_data: dict):
    """
    Display parsed treatment data in an organized, exploratory format.
    """
    if not patient_data:
        st.info("No treatment data available.")
        return
    
    # Create tabs for different data categories
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Clinical History", 
        "🧬 Flow Cytometry", 
        "🔬 Genetic Features", 
        "📊 Cytogenetics", 
        "🔍 All Data"
    ])
    
    with tab1:
        st.markdown("### Clinical History & Qualifiers")
        qualifiers = patient_data.get("qualifiers", {})
        
        if qualifiers:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Disease History:**")
                history_items = []
                if qualifiers.get("therapy_related"):
                    history_items.append("✅ Therapy-related AML")
                if qualifiers.get("previous_chemotherapy"):
                    history_items.append("✅ Previous chemotherapy")
                if qualifiers.get("previous_MDS"):
                    history_items.append("✅ Previous MDS")
                if qualifiers.get("previous_MPN"):
                    history_items.append("✅ Previous MPN")
                if qualifiers.get("previous_CMML"):
                    history_items.append("✅ Previous CMML")
                
                if history_items:
                    for item in history_items:
                        st.markdown(f"• {item}")
                else:
                    st.markdown("• No significant disease history detected")
            
            with col2:
                st.markdown("**Disease Status:**")
                status_items = []
                if qualifiers.get("relapsed_refractory"):
                    status_items.append("✅ Relapsed/refractory disease")
                
                if status_items:
                    for item in status_items:
                        st.markdown(f"• {item}")
                else:
                    st.markdown("• Newly diagnosed (presumed)")
        else:
            st.info("No clinical history qualifiers found.")
    
    with tab2:
        st.markdown("### Flow Cytometry Data")
        
        # CD33 status
        cd33_positive = patient_data.get("cd33_positive")
        cd33_percentage = patient_data.get("cd33_percentage")
        
        if cd33_positive is not None or cd33_percentage is not None:
            st.markdown("**CD33 Expression:**")
            if cd33_positive is not None:
                status = "✅ Positive" if cd33_positive else "❌ Negative"
                st.markdown(f"• Status: {status}")
            if cd33_percentage is not None:
                st.markdown(f"• Percentage: {cd33_percentage}%")
                # Add interpretation
                if cd33_percentage >= 20:
                    st.success(f"CD33 ≥20% - Eligible for gemtuzumab ozogamicin (GO)")
                else:
                    st.warning(f"CD33 <20% - May not be optimal for GO therapy")
        else:
            st.info("No CD33 flow cytometry data found.")
    
    with tab3:
        st.markdown("### Genetic Features")
        
        # AML-defining genetic abnormalities
        aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        if aml_genes:
            st.markdown("**AML-Defining Genetic Abnormalities:**")
            for gene, present in aml_genes.items():
                if present:
                    st.markdown(f"✅ {gene}")
        
        # MDS-related mutations
        mds_mutations = patient_data.get("MDS_related_mutation", {})
        if mds_mutations:
            positive_mutations = [gene for gene, present in mds_mutations.items() if present]
            if positive_mutations:
                st.markdown("**MDS-Related Mutations:**")
                for gene in positive_mutations:
                    st.markdown(f"✅ {gene}")
        
        if not aml_genes and not mds_mutations:
            st.info("No genetic abnormalities detected.")
    
    with tab4:
        st.markdown("### Cytogenetic Abnormalities")
        
        # MDS-related cytogenetics
        mds_cyto = patient_data.get("MDS_related_cytogenetics", {})
        if mds_cyto:
            positive_cyto = [abnorm for abnorm, present in mds_cyto.items() if present]
            if positive_cyto:
                st.markdown("**MDS-Related Cytogenetic Abnormalities:**")
                for abnorm in positive_cyto:
                    st.markdown(f"✅ {abnorm}")
                    
                # Add risk interpretation
                adverse_abnormalities = ["Complex_karyotype", "-5", "del_5q", "-7", "del_7q", "-17", "del_17p"]
                if any(abnorm in adverse_abnormalities for abnorm in positive_cyto):
                    st.warning("⚠️ Adverse risk cytogenetic abnormalities detected")
        
        # Morphologic features
        dysplastic_lineages = patient_data.get("number_of_dysplastic_lineages")
        if dysplastic_lineages is not None:
            st.markdown(f"**Number of Dysplastic Lineages:** {dysplastic_lineages}")
        
        # Cytogenetics data availability
        no_cyto_data = patient_data.get("no_cytogenetics_data")
        if no_cyto_data:
            st.warning("⚠️ No cytogenetics data available")
        
        if not mds_cyto and dysplastic_lineages is None and not no_cyto_data:
            st.info("No cytogenetic abnormalities detected.")
    
    with tab5:
        st.markdown("### Complete Data Structure")
        st.json(patient_data)


def display_streamlined_treatment_recommendations(patient_data: dict, eln_risk: str, patient_age: int):
    """
    Streamlined treatment recommendations display without nested expanders or button conflicts.
    """
    from utils.aml_treatment_recommendations import (
        get_consensus_treatment_recommendation, 
        determine_treatment_eligibility,
        _is_cd33_positive,
        _has_flt3_mutation,
        _is_therapy_related_aml,
        _has_myelodysplasia_related_changes,
        _get_cytogenetic_risk
    )
    
    # Get treatment recommendation
    recommendation = get_consensus_treatment_recommendation(patient_data, patient_age, eln_risk)
    
    # Treatment recommendation box with improved styling
    treatment_color = "#e8f5e8" if "ATRA" in recommendation["recommended_treatment"] else \
                     "#fff3cd" if "CPX-351" in recommendation["recommended_treatment"] else \
                     "#d1ecf1" if "Midostaurin" in recommendation["recommended_treatment"] else "#f8f9fa"
    
    st.markdown(f"""
    <div style="
        background: {treatment_color};
        padding: 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 2px solid #0066cc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0 0 10px 0; color: #0066cc; font-size: 1.5em;">
            🎯 {recommendation['recommended_treatment']}
        </h3>
        <p style="margin: 0; color: #495057; font-style: italic;">
            Recommended treatment based on consensus guidelines
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Rationale and considerations in clean layout
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### 📋 Rationale")
        st.markdown(recommendation["rationale"])
        
        if recommendation["considerations"]:
            st.markdown("### ⚠️ Key Clinical Considerations")
            for consideration in recommendation["considerations"]:
                st.markdown(f"• {consideration}")
    
    with col2:
        # Patient summary with cleaner styling
        st.markdown("### 👤 Patient Summary")
        
        # Patient characteristics in a clean container
        with st.container():
            st.markdown(f"**Age:** {patient_age} years ({recommendation['age_group']})")
            st.markdown(f"**ELN Risk:** {eln_risk}")
            st.markdown(f"**Cytogenetic Risk:** {_get_cytogenetic_risk(patient_data)}")
            
            st.markdown("---")
            st.markdown("**Key Features:**")
            
            # CD33 status
            cd33_positive = _is_cd33_positive(patient_data)
            cd33_percentage = patient_data.get("cd33_percentage")
            if patient_data.get("cd33_positive") is not None:
                cd33_status = "✅ Positive" if cd33_positive else "❌ Negative"
                if cd33_percentage:
                    cd33_status += f" ({cd33_percentage}%)"
            else:
                cd33_status = "❓ Unknown"
            st.markdown(f"**CD33:** {cd33_status}")
            
            # FLT3 status
            flt3_status = "✅ Present" if _has_flt3_mutation(patient_data) else "❌ Not detected"
            st.markdown(f"**FLT3 Mutation:** {flt3_status}")
            
            # Disease characteristics
            disease_features = []
            if _is_therapy_related_aml(patient_data):
                disease_features.append("Therapy-related AML")
            if _has_myelodysplasia_related_changes(patient_data):
                disease_features.append("MDS-related changes")
            
            if disease_features:
                st.markdown("**Disease Features:**")
                for feature in disease_features:
                    st.markdown(f"• {feature}")
    
    # Treatment eligibility in a clean format
    st.markdown("---")
    st.markdown("### 🏥 Treatment Eligibility Analysis")
    
    eligible_treatments = determine_treatment_eligibility(patient_data)
    
    # Display eligible treatments in a simple list format
    st.markdown("**Eligible Treatments:**")
    for treatment in eligible_treatments:
        if treatment == recommendation["recommended_treatment"]:
            st.markdown(f"⭐ **{treatment}** (Recommended)")
        else:
            st.markdown(f"• {treatment}")
    
    # Citation and disclaimer
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        **⚠️ Important Disclaimer:** 
        These recommendations are based on consensus guidelines and should not replace clinical judgment. 
        Treatment decisions should always involve multidisciplinary team discussion.
        """)
    
    with col2:
        with st.container():
            st.markdown("**📚 Reference:**")
            st.markdown("""
            Coats T, et al. *Br J Haematol.* 2022;196:1337–1343.
            [DOI: 10.1111/bjh.18013](https://doi.org/10.1111/bjh.18013)
            """)


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
        options = ["Classification", "ELN Risk (AML)", "IPSS Risk (MDS)", "Treatment", "Clinical Trials", "MRD Review", "Gene Review", "AI Comments", "Differentiation"]
        icons = ["clipboard", "graph-up-arrow", "calculator", "prescription2", "search", "recycle", "bar-chart", "chat-left-text", "funnel"]
    elif show_eln:
        # Show AML-specific options including treatment
        options = ["Classification", "Risk", "Treatment", "Clinical Trials", "MRD Review", "Gene Review", "AI Comments", "Differentiation"]
        icons = ["clipboard", "graph-up-arrow", "prescription2", "search", "recycle", "bar-chart", "chat-left-text", "funnel"]
    else:
        # Just show a single Risk option (MDS only - no treatment tab)
        options = ["Classification", "Risk", "Clinical Trials", "MRD Review", "Gene Review", "AI Comments", "Differentiation"]
        icons = ["clipboard", "graph-up-arrow", "search", "recycle", "bar-chart", "chat-left-text", "funnel"]

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
        # Display classification results - these will be the same regardless of input mode
        from utils.displayers import display_aml_classification_results

        # Get the classification results and display them
        display_aml_classification_results(
            parsed_fields=res["parsed_data"],
            classification_who=res["who_class"],
            who_derivation=res["who_derivation"],
            classification_icc=res["icc_class"],
            icc_derivation=res["icc_derivation"],
            classification_eln=res.get("classification_eln", ""),
            mode=mode,
        )
        
        # Check for UBA1 mutation which indicates VEXAS syndrome
        if res["parsed_data"].get("MDS_related_mutation", {}).get("UBA1", False):
            st.warning("⚠️ **UBA1 MUTATION DETECTED**: UBA1 mutations are pathognomonic for VEXAS syndrome (Vacuoles, E1 enzyme, X-linked, Autoinflammatory, Somatic). Consider this diagnosis if consistent with clinical features.", icon="⚠️")
        
        # Check for JAK2 mutation - may indicate MPN or MDS/MPN overlap
        if res["parsed_data"].get("MDS_related_mutation", {}).get("JAK2", False):
            st.warning("⚠️ **JAK2 MUTATION DETECTED**: JAK2 mutation is most commonly associated with myeloproliferative neoplasms (MPNs). Consider MPN or MDS/MPN overlap syndrome if clinical and morphological features are consistent.", icon="⚠️")
        
        # Check for BCR::ABL1 fusion
        if res["parsed_data"].get("AML_defining_recurrent_genetic_abnormalities", {}).get("BCR::ABL1", False):
            st.warning("⚠️ **BCR::ABL1 FUSION DETECTED**: While this finding does not exclude MDS, BCR::ABL1 fusion is characteristic of chronic myeloid leukemia (CML) and Ph+ acute leukemias. Consider alternative diagnoses and tyrosine kinase inhibitor therapy.", icon="⚠️")
        
        # Check if there are any unsubmitted forms before generating the classification review
        has_pending_forms = False
        
        # Determine WHO disease type
        who_disease_type = "Unknown"
        if "aml_manual_result" in st.session_state:
            who_disease_type = st.session_state["aml_manual_result"].get("who_disease_type", "Unknown")
        elif "aml_ai_result" in st.session_state:
            who_disease_type = st.session_state["aml_ai_result"].get("who_disease_type", "Unknown")
        
        # Determine ICC disease type
        icc_disease_type = "Unknown"
        if "aml_manual_result" in st.session_state:
            icc_disease_type = st.session_state["aml_manual_result"].get("icc_disease_type", "Unknown")
        elif "aml_ai_result" in st.session_state:
            icc_disease_type = st.session_state["aml_ai_result"].get("icc_disease_type", "Unknown")
        
        # Check for erythroid classifications
        who_has_erythroid = "erythroid" in res["who_class"].lower()
        icc_has_erythroid = "erythroid" in res["icc_class"].lower()
        
        # Check for erythroid form submission
        # We need to track erythroid form submissions in session state
        if who_has_erythroid or icc_has_erythroid:
            # Initialize erythroid form tracking in session state if not already present
            if "erythroid_form_submitted" not in st.session_state:
                st.session_state["erythroid_form_submitted"] = False
                has_pending_forms = True
            elif not st.session_state["erythroid_form_submitted"]:
                has_pending_forms = True
        
        # Check if MDS confirmation form is pending submission (combined form)
        if (who_disease_type == "MDS" or icc_disease_type == "MDS") and "mds_confirmation" in st.session_state:
            if not st.session_state["mds_confirmation"].get("submitted", False):
                has_pending_forms = True
        
        # Only generate and display the classification review if there are no pending forms
        if not has_pending_forms and "aml_class_review" not in st.session_state:
            with st.spinner("Generating Classification Review..."):
                st.session_state["aml_class_review"] = get_gpt4_review_aml_classification(
                    classification_dict,
                    res["parsed_data"],
                    free_text_input=free_text_input_value
                )
            st.markdown("### Classification Review")
            st.markdown(st.session_state["aml_class_review"])
        elif not has_pending_forms:
            st.markdown("### Classification Review")
            st.markdown(st.session_state["aml_class_review"])
        else:
            st.info("Please complete all required forms before the classification review is generated.")

    elif sub_tab == "ELN Risk (AML)":
        # Import necessary functions for risk assessment
        from classifiers.aml_risk_classifier import eln2022_intensive_risk, eln2024_non_intensive_risk
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
        from parsers.mds_ipss_parser import parse_ipss_report
        

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
        from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
        from parsers.mds_ipss_parser import parse_ipss_report

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
            # Use the IPSS risk assessment function directly with prepopulated text
            show_ipss_risk_assessment(res, free_text_input_value)
        else:
            st.warning("No risk assessment models are applicable for this classification.")

    elif sub_tab == "Treatment":
        # Import treatment recommendation functions
        from utils.aml_treatment_recommendations import display_treatment_recommendations
        from classifiers.aml_risk_classifier import eln2022_intensive_risk
        from parsers.treatment_parser import parse_treatment_data, display_treatment_parsing_results
        
        # Check if this is an AML case
        if not show_eln:
            st.warning("🔬 **Treatment recommendations are only available for AML diagnoses.**")
            st.info("This case appears to be classified as MDS. Please refer to the Risk tab for IPSS-M/R risk stratification.")
        else:
            # Simple header
            st.markdown("### 💊 AML Treatment Recommendations")
            
            # Get the original report text for treatment parsing
            original_report = ""
            if res.get("free_text_input"):
                original_report = res["free_text_input"]
            elif st.session_state.get("free_text_input"):
                original_report = st.session_state["free_text_input"]
            
            if not original_report.strip():
                st.error("❌ **No original report text available**")
                st.markdown("""
                **Next Steps:**
                1. Return to the **Data Entry** page
                2. Re-enter your report in free-text mode
                3. Navigate back to this Treatment tab
                
                *Treatment recommendations require the original report text for optimal accuracy.*
                """)
                
                if mode == "manual":
                    st.info("💡 **Tip:** This appears to be manual entry mode. For best treatment recommendations, use the free-text report entry mode.")
                return
            
            # Simple data collection
            # Get patient age
            patient_age = st.session_state.get("treatment_age")
            if "age" in res["parsed_data"]:
                try:
                    extracted_age = int(res["parsed_data"]["age"])
                    if patient_age is None:
                        patient_age = extracted_age
                except (ValueError, TypeError):
                    pass
            
            # Age input
            age_input = st.number_input(
                "Patient Age:", 
                min_value=18, 
                max_value=100, 
                value=patient_age if patient_age else 65, 
                step=1
            )
            
            if age_input != patient_age:
                st.session_state["treatment_age"] = age_input
                patient_age = age_input
            
            # Optional CD33 data
            additional_flow_data = {}
            cd33_percentage = st.number_input(
                "CD33 percentage (optional):",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.1,
                help="Leave at 0 if unknown. CD33 ≥20% may qualify for gemtuzumab ozogamicin."
            )
            
            if cd33_percentage > 0:
                additional_flow_data["cd33_percentage"] = cd33_percentage
                additional_flow_data["cd33_positive"] = cd33_percentage >= 20
            
            # Proceed button
            if st.button("Get Treatment Recommendations", type="primary", use_container_width=True):
                if patient_age is None:
                    st.error("Please enter patient age to continue.")
                else:
                    # Store the flow data for use in parsing
                    if additional_flow_data:
                        st.session_state["additional_flow_data"] = additional_flow_data
                    
                    # Process treatment data (always use specialized parser)
                    treatment_data = None
                    patient_data_for_treatment = None
                    
                    # Create cache key that includes additional data
                    cache_components = [original_report]
                    if additional_flow_data:
                        cache_components.append(str(additional_flow_data))
                    cache_key = f"treatment_data_{hash(''.join(cache_components))}"
                    
                    if cache_key in st.session_state:
                        treatment_data = st.session_state[cache_key]
                        st.info("✅ Using cached treatment analysis")
                    else:
                        with st.spinner("🔄 Analyzing report for treatment-specific factors..."):
                            treatment_data = parse_treatment_data(original_report)
                            
                            # Override with additional flow data if provided
                            if treatment_data and additional_flow_data:
                                treatment_data.update(additional_flow_data)
                            
                            if treatment_data:
                                st.session_state[cache_key] = treatment_data
                    
                    if not treatment_data:
                        st.error("❌ Failed to extract treatment data. Falling back to classification data.")
                        from utils.transformation_utils import transform_main_parser_to_treatment_format
                        patient_data_for_treatment = transform_main_parser_to_treatment_format(res["parsed_data"])
                        
                        # Add additional flow data to fallback data
                        if additional_flow_data:
                            patient_data_for_treatment.update(additional_flow_data)
                    else:
                        patient_data_for_treatment = treatment_data
                    
                    # Get ELN risk classification
                    try:
                        source_data = treatment_data if treatment_data else res["parsed_data"]
                        eln_risk, _, _ = eln2022_intensive_risk(source_data)
                    except Exception as e:
                        eln_risk = "Unknown"
                    
                    # Store results for display
                    st.session_state["treatment_results"] = {
                        "patient_data": patient_data_for_treatment,
                        "eln_risk": eln_risk,
                        "patient_age": patient_age,
                        "additional_flow_data": additional_flow_data
                    }
                    
                    st.success("✅ Treatment analysis complete!")
                    st.rerun()
            
            # Display results if available
            if "treatment_results" in st.session_state:
                results = st.session_state["treatment_results"]
                patient_data_for_treatment = results["patient_data"]
                eln_risk = results["eln_risk"]
                patient_age = results["patient_age"]
                additional_flow_data = results.get("additional_flow_data", {})
                
                # Show CD33 data if provided
                if additional_flow_data and "cd33_percentage" in additional_flow_data:
                    st.info(f"ℹ️ Using provided CD33 data: {additional_flow_data['cd33_percentage']}%")
            else:
                st.info("Please enter patient age and click 'Get Treatment Recommendations' to proceed.")
                return
            
            # Add data explorer panel
            with st.expander("🔍 Data Explorer - View Parsed Treatment Data", expanded=False):
                if patient_data_for_treatment:
                    display_treatment_data_explorer(patient_data_for_treatment)
                else:
                    st.warning("No treatment data available to explore.")
            
            # Display treatment recommendations with clean separator
            st.markdown("---")
            
            # Create a custom treatment display that doesn't have button conflicts
            display_streamlined_treatment_recommendations(patient_data_for_treatment, eln_risk, patient_age)

    elif sub_tab == "Clinical Trials":
        # Import clinical trial matching functions
        from parsers.clinical_trial_matcher import (
            format_patient_data_for_matching, 
            run_clinical_trial_matching, 
            display_trial_matches
        )
        
        st.markdown("### 🔬 Clinical Trial Matching")
        st.markdown("Find relevant clinical trials based on the patient's molecular profile and clinical characteristics.")
        
        # Get the original report text
        original_report = ""
        if res.get("free_text_input"):
            original_report = res["free_text_input"]
        elif st.session_state.get("free_text_input"):
            original_report = st.session_state["free_text_input"]
        
        # Additional patient information form
        with st.expander("📋 Additional Patient Information (Optional)", expanded=False):
            st.markdown("Provide additional information to improve trial matching accuracy:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Basic demographics
                patient_age_trials = st.number_input(
                    "Patient Age:", 
                    min_value=18, 
                    max_value=100, 
                    value=st.session_state.get("treatment_age", 65), 
                    step=1,
                    key="trials_age"
                )
                
                ecog_status = st.selectbox(
                    "ECOG Performance Status:",
                    options=[None, 0, 1, 2, 3, 4],
                    format_func=lambda x: "Unknown" if x is None else f"ECOG {x}",
                    key="trials_ecog"
                )
                
                # Disease status
                disease_status = st.selectbox(
                    "Disease Status:",
                    options=["Unknown", "Newly diagnosed", "Relapsed", "Refractory", "In remission"],
                    key="trials_disease_status"
                )
                
                # Prior treatments
                prior_chemo_regimens = st.number_input(
                    "Number of prior chemotherapy regimens:",
                    min_value=0,
                    max_value=10,
                    value=0,
                    step=1,
                    key="trials_prior_chemo"
                )
                
            with col2:
                # Medical conditions
                st.markdown("**Medical Conditions:**")
                hiv_positive = st.checkbox("HIV positive", key="trials_hiv")
                hepatitis_b = st.checkbox("Hepatitis B positive", key="trials_hep_b")
                hepatitis_c = st.checkbox("Hepatitis C positive", key="trials_hep_c")
                heart_failure = st.checkbox("Heart failure", key="trials_heart")
                active_infection = st.checkbox("Active infection", key="trials_infection")
                other_cancers = st.checkbox("Other active cancers", key="trials_other_cancer")
                
                # Reproductive status
                st.markdown("**Reproductive Status:**")
                pregnant = st.checkbox("Pregnant", key="trials_pregnant")
                breastfeeding = st.checkbox("Breastfeeding", key="trials_breastfeeding")
        
        # Prepare additional info dictionary
        additional_info = {
            "age": patient_age_trials,
            "ecog_status": ecog_status,
            "newly_diagnosed": disease_status == "Newly diagnosed",
            "relapsed": disease_status == "Relapsed", 
            "refractory": disease_status == "Refractory",
            "in_remission": disease_status == "In remission",
            "prior_chemotherapy_regimens": prior_chemo_regimens,
            "hiv_positive": hiv_positive,
            "hepatitis_b_positive": hepatitis_b,
            "hepatitis_c_positive": hepatitis_c,
            "heart_failure": heart_failure,
            "active_infection": active_infection,
            "other_cancers": other_cancers,
            "pregnant": pregnant,
            "breastfeeding": breastfeeding
        }
        
        # Determine primary diagnosis from classification results
        who_disease_type = res.get("who_disease_type", "Unknown")
        icc_disease_type = res.get("icc_disease_type", "Unknown")
        
        if who_disease_type == "AML" or icc_disease_type == "AML":
            additional_info["primary_diagnosis"] = "Acute Myeloid Leukemia (AML)"
        elif who_disease_type == "MDS" or icc_disease_type == "MDS":
            additional_info["primary_diagnosis"] = "Myelodysplastic Syndrome (MDS)"
        else:
            additional_info["primary_diagnosis"] = "Blood cancer"
        
        # Button to start trial matching
        if st.button("🔍 Find Matching Clinical Trials", type="primary", use_container_width=True):
            # Format patient data for matching
            patient_data_text = format_patient_data_for_matching(
                parsed_data=res["parsed_data"],
                free_text_input=original_report,
                additional_info=additional_info
            )
            
            # Store the formatted data for debugging
            st.session_state["formatted_patient_data"] = patient_data_text
            
            # Run trial matching
            with st.spinner("🔄 Analyzing patient profile and matching to clinical trials..."):
                try:
                    matched_trials = run_clinical_trial_matching(patient_data_text)
                    st.session_state["matched_trials"] = matched_trials
                    st.success(f"✅ Found {len(matched_trials)} clinical trials to evaluate!")
                except Exception as e:
                    st.error(f"❌ Error during trial matching: {e}")
                    st.session_state["matched_trials"] = []
        
        # Display results if available
        if "matched_trials" in st.session_state:
            matched_trials = st.session_state["matched_trials"]
            display_trial_matches(matched_trials)
        
        # Debug section
        if st.checkbox("🔧 Show Debug Information", value=False):
            st.markdown("### Debug Information")
            
            if "formatted_patient_data" in st.session_state:
                with st.expander("Formatted Patient Data Sent to AI"):
                    st.text(st.session_state["formatted_patient_data"])
            
            st.markdown("**Parsed Data Summary:**")
            st.json({
                "WHO Classification": res.get("who_class", "Unknown"),
                "ICC Classification": res.get("icc_class", "Unknown"),
                "Disease Type": additional_info.get("primary_diagnosis", "Unknown"),
                "Age": additional_info.get("age", "Unknown"),
                "Disease Status": disease_status,
                "Prior Treatments": prior_chemo_regimens
            })

    elif sub_tab == "MRD Review":
        st.markdown("### Minimal Residual Disease (MRD) Monitoring Recommendations")
        
        # Extract genetic data from parsed data
        patient_genetic_data = []
        
        # Check AML defining genetic abnormalities
        if "AML_defining_recurrent_genetic_abnormalities" in res["parsed_data"]:
            for gene, is_present in res["parsed_data"]["AML_defining_recurrent_genetic_abnormalities"].items():
                if is_present:
                    # Convert to the format expected by our algorithm
                    if gene == "NPM1_mutation":
                        patient_genetic_data.append("NPM1")
                    elif gene == "CBFB_MYH11":
                        patient_genetic_data.append("CBFB-MYH11")
                    elif gene == "RUNX1_RUNX1T1":
                        patient_genetic_data.append("RUNX1-RUNX1T1")
                    elif gene == "KMT2A_rearranged":
                        patient_genetic_data.append("KMT2A")
                    elif gene == "DEK_NUP214":
                        patient_genetic_data.append("DEK-NUP214")
                    elif gene == "BCR_ABL1":
                        patient_genetic_data.append("BCR-ABL1")
                    elif gene == "PML_RARA":
                        # Use PML-RARA format consistently for detection
                        patient_genetic_data.append("PML-RARA")
                    else:
                        patient_genetic_data.append(gene)
        
        # Check MDS related mutations
        if "MDS_related_mutation" in res["parsed_data"]:
            for gene, is_present in res["parsed_data"]["MDS_related_mutation"].items():
                if is_present:
                    patient_genetic_data.append(gene)
        
        # Display the detected markers
        st.markdown("#### Detected Markers for MRD Monitoring")
        if not patient_genetic_data:
            st.warning("No specific genetic markers for MRD monitoring were detected.")
            st.markdown("""
            **Recommendation:** Consider flow cytometry-based MRD assessment to detect Leukemia Associated Immunophenotypes (LAIPs).
            """)
        else:
            st.write("The following genetic markers were detected that may be suitable for MRD monitoring:")
            for gene in patient_genetic_data:
                st.markdown(f"- **{gene}**")
        
        # Enhanced pattern matching for gene detection (debug info)
        has_pml_rara_debug = any(("PML" in gene and "RARA" in gene) or ("PML-RARA" in gene) or ("PML::RARA" in gene) for gene in patient_genetic_data)
        has_cbfb_myh11_debug = any(("CBFB" in gene and "MYH11" in gene) or ("CBFB-MYH11" in gene) or ("CBFB::MYH11" in gene) for gene in patient_genetic_data)
        has_runx1_runx1t1_debug = any(("RUNX1" in gene and ("RUNX1T1" in gene or "AML1-ETO" in gene)) or ("RUNX1-RUNX1T1" in gene) or ("RUNX1::RUNX1T1" in gene) for gene in patient_genetic_data)
        

        
        # Display MRD monitoring schedules based on detected markers
        st.markdown("### MRD Monitoring Schedules")
        
        # Flag to track if any specific marker was found and displayed
        found_specific_marker = False
        
        # PML-RARA fusion - Enhanced detection for any format containing both PML and RARA
        if any(("PML" in gene and "RARA" in gene) or ("PML-RARA" in gene) or ("PML::RARA" in gene) for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### PML-RARA Fusion")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### Low Risk PML-RARA (WBC ≤ 10 × 10⁹/L)")
                st.markdown("""
                **Test Type:** Molecular RT-qPCR
                
                **Recommended Schedule:**
                * **Diagnosis:** Bone Marrow (BM)
                * **During Induction:** Not routinely performed
                * **Post Induction:** Not routinely performed 
                * **End of Consolidation:** BM (critical timepoint)
                * **Follow-up:** If BM negative at end of consolidation, MRD monitoring can be discontinued
                """)
            
            with col2:
                st.markdown("##### High Risk PML-RARA (WBC > 10 × 10⁹/L)")
                st.markdown("""
                **Test Type:** Molecular RT-qPCR
                
                **Recommended Schedule:**
                * **Diagnosis:** Bone Marrow (BM)
                * **During Consolidation:** PB every 4-6 weeks
                * **End of Consolidation:** BM (critical timepoint)
                * **Follow-up:** BM every 3 months for at least 24 months
                * **If Transplant:** Pre- and post-transplant monitoring
                """)
        
        # NPM1 - Enhanced detection
        if any("NPM1" in gene for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### NPM1 Mutation")
            st.markdown("""
            **Test Type:** Molecular qPCR
            
            **Recommended Schedule:**
            * **Diagnosis:** Bone Marrow (BM) and/or Peripheral Blood (PB)
            * **Post 2 Cycles of Induction Therapy:** PB
            * **End of Treatment:** BM
            * **Follow-up (for 24 months):** BM every 3 months or PB every 4-6 weeks
            * **If Transplant:** Pre- and post-transplant monitoring
            """)
        
        # Core Binding Factor Leukemias - Enhanced detection for both fusion types
        if any(("CBFB" in gene and "MYH11" in gene) or ("CBFB-MYH11" in gene) or ("CBFB::MYH11" in gene) for gene in patient_genetic_data) or any(("RUNX1" in gene and ("RUNX1T1" in gene or "AML1-ETO" in gene)) or ("RUNX1-RUNX1T1" in gene) or ("RUNX1::RUNX1T1" in gene) for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### Core-Binding Factor (CBF) Leukemia")
            
            # Determine which CBF type is present
            cbf_type = "CBFB-MYH11" if any(("CBFB" in gene and "MYH11" in gene) or ("CBFB-MYH11" in gene) or ("CBFB::MYH11" in gene) for gene in patient_genetic_data) else "RUNX1-RUNX1T1"
            
            st.markdown(f"""
            **Fusion:** {cbf_type}
            
            **Test Type:** Molecular RT-qPCR
            
            **Recommended Schedule:**
            * **Diagnosis:** Bone Marrow (BM) and/or Peripheral Blood (PB)
            * **Post 2 Cycles of Induction Therapy:** PB
            * **End of Treatment:** BM
            * **Follow-up (for 24 months):** PB every 4-6 weeks
            * **If Transplant:** Pre- and post-transplant monitoring
            """)
        
        # KMT2A rearrangements - Enhanced detection
        if any(("KMT2A" in gene) or ("MLL" in gene) for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### KMT2A Rearrangement")
            st.markdown("""
            **Test Type:** Molecular RT-PCR or qPCR
            
            **Recommended Schedule:**
            * **Diagnosis:** Bone Marrow (BM)
            * **Post 2 Cycles of Induction Therapy:** BM
            * **End of Treatment:** BM
            * **Follow-up:** No specific ELN recommendations
            * **If Transplant:** Pre- and post-transplant monitoring
            
            **Note:** KMT2A partner gene needed for specific assay design.
            """)
        
        # DEK-NUP214 fusion - Enhanced detection
        if any(("DEK" in gene and "NUP214" in gene) or ("DEK-NUP214" in gene) or ("DEK::NUP214" in gene) for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### DEK-NUP214 Fusion")
            st.markdown("""
            **Test Type:** Molecular RT-qPCR
            
            **Recommended Schedule:**
            * **Diagnosis:** Bone Marrow (BM)
            * **Post 2 Cycles of Induction Therapy:** BM
            * **End of Treatment:** BM
            * **Follow-up:** No specific ELN recommendations
            * **If Transplant:** Pre- and post-transplant monitoring
            """)
        
        # BCR-ABL1 fusion - Enhanced detection
        if any(("BCR" in gene and "ABL1" in gene) or ("BCR-ABL1" in gene) or ("BCR::ABL1" in gene) for gene in patient_genetic_data):
            found_specific_marker = True
            st.markdown("#### BCR-ABL1 Fusion")
            st.markdown("""
            **Test Type:** Molecular RT-qPCR
            
            **Recommended Schedule:**
            * **Diagnosis:** Bone Marrow (BM)
            * **During Treatment:** No routine MRD assessment specified
            * **End of Treatment:** No routine MRD assessment specified
            * **Follow-up:** Submit with all follow-up samples
            * **If Transplant:** Pre- and post-transplant monitoring
            """)
        
        # If none of the specific markers were found or displayed, show flow cytometry recommendation
        if not found_specific_marker:
            st.markdown("#### Flow Cytometry Recommended")
            st.markdown("""
            **Test Type:** Flow Cytometry MRD
            
            **Target:** Leukemia-Associated Immunophenotype (LAIP) or Differentiation from Normal (DfN)
            
            **Sample Type:** Bone Marrow
            """)

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
        "mrd_test_result",
        "aml_gene_review",
        "aml_additional_comments",
        "initial_parsed_data",
        "free_text_input",
        "erythroid_form_submitted",
        "matched_trials",
        "formatted_patient_data"
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



# Function to display ELN risk assessment for AML
def show_eln_risk_assessment(res, free_text_input_value):
    from classifiers.aml_risk_classifier import eln2022_intensive_risk, eln2024_non_intensive_risk
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
                risk_eln2022, eln22_median_os, derivation_eln2022 = eln2022_intensive_risk(parsed_eln_data)
                
                # Calculate ELN 2024 non-intensive risk
                risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
                
                # Store for potential reuse
                st.session_state['eln_derivation'] = derivation_eln2022
                st.session_state['eln24_derivation'] = eln24_derivation
                st.session_state['original_eln_data'] = parsed_eln_data.copy()
            else:
                # Fall back to using the parsed data from the AML parser - use ELN intensive classifier
                risk_eln2022, eln22_median_os, derivation_eln2022 = eln2022_intensive_risk(res["parsed_data"])
                eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
                risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
    else:
        # Fall back to using the parsed data from the AML parser - use ELN intensive classifier
        risk_eln2022, eln22_median_os, derivation_eln2022 = eln2022_intensive_risk(res["parsed_data"])
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

# Helper function (similar to the one in ELN) to get CSS class for risk boxes
def get_risk_class(risk_category):
    """Maps risk category string to a CSS class."""
    if not risk_category or not isinstance(risk_category, str):
        return "risk-unknown" # Default class if category is missing or not a string
    
    risk_lower = risk_category.lower().replace(" ", "-").replace("_", "-")
    # Map specific IPSS categories to standardized classes if needed, 
    # otherwise, use the direct mapping.
    # Example mapping (adjust based on your actual categories):
    if "very-low" in risk_lower: return "risk-very-low"
    if "low" in risk_lower: return "risk-low"
    if "intermediate" in risk_lower or "moderate" in risk_lower : return "risk-moderate" # Handle variations
    if "very-high" in risk_lower: return "risk-very-high"
    if "high" in risk_lower: return "risk-high"
    
    # Fallback if no specific class matched (can adjust this logic)
    return f"risk-{risk_lower}"


# Function to display IPSS risk assessment for MDS
def show_ipss_risk_assessment(res, free_text_input_value):
    """
    This function is identical to ipss_risk_calculator_page but takes a free_text_input_value
    parameter to prepopulate the text area.
    """
    # Import necessary functions
    from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
    from parsers.mds_ipss_parser import parse_ipss_report
    import pandas as pd
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    from streamlit_option_menu import option_menu
    


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
    ipss_mode_toggle = st.toggle("Free-text Mode", key="ipss_mode_toggle", value=True)
    
    patient_data = None
    
    # FREE TEXT MODE
    if ipss_mode_toggle:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("""
            ### Input MDS/IPSS Report
            
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
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="hb_override"
                )
                
                plt_override = st.number_input(
                    "Platelets (10^9/L)",
                    min_value=0, 
                    max_value=1000,
                    value=0,
                    step=1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="plt_override"
                )
            
            with col2:
                anc_override = st.number_input(
                    "ANC (10^9/L)",
                    min_value=0.0, 
                    max_value=20.0,
                    value=0.0,
                    step=0.1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="anc_override"
                )
                
                blast_override = st.number_input(
                    "Bone Marrow Blasts (%)",
                    min_value=0.0, 
                    max_value=30.0,
                    value=0.0,
                    step=0.1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="blast_override"
                )
            
            with col3:
                age_override = st.number_input(
                    "Age (years)",
                    min_value=0, 
                    max_value=120,
                    value=0,  # 18 signals "not set"
                    step=1,
                    help="Enter a value greater than 18 to override the report.",
                    key="age_override"
                )
            
            # Use the free_text_input_value parameter to prepopulate the text area
            free_report_text = st.text_area(
                "Enter MDS report data:",
                value=free_text_input_value,  # Prepopulate with the provided text
                placeholder="Paste your MDS report here including: lab values, cytogenetics, gene mutations...",
                key="ipss_free_text_input",
                height=250
            )
            
            # Check if all override fields are manually set (i.e. not their default "not set" values)
            all_fields_entered = (
                (hb_override != 0.0) and 
                (plt_override != 0) and 
                (anc_override != 0.0) and 
                (blast_override != 0.0) and 
                (age_override != 0)
            )
            
            if not all_fields_entered:
                st.warning("Please manually enter values for all override fields before submitting.")
            
            # The calculate button is disabled until all override fields have been manually filled.
            calculate_button = st.button(
                "Calculate Risk Scores", 
                key="calculate_ipss_scores", 
                type="primary", 
                disabled=not all_fields_entered
            )
            
            if calculate_button:
                # First try to process any text input
                parsed_data = None
                if free_report_text.strip():
                    with st.spinner("Processing report text..."):
                        parsed_data = parse_ipss_report(free_report_text)
                        if parsed_data:
                            st.info("Report processed successfully.")
                            # Store parsed data for gene mutations and other details
                            st.session_state['original_ipss_data'] = parsed_data.copy()
                            # We'll display JSON in a dedicated section later
                
                # Start with parsed data as the base, then apply overrides only if set
                with st.spinner("Calculating risk scores..."):
                    if parsed_data or 'original_ipss_data' in st.session_state:
                        original_data = parsed_data or st.session_state.get('original_ipss_data', {})
                        patient_data = original_data.copy()
                    else:
                        patient_data = {}
                    
                    # Apply overrides now that we know they're all manually entered
                    patient_data["HB"] = hb_override
                    patient_data["PLT"] = plt_override
                    patient_data["ANC"] = anc_override
                    patient_data["BM_BLAST"] = blast_override
                    patient_data["AGE"] = age_override
                    
                    # Default cytogenetic value if not available - normal karyotype
                    if patient_data.get("CYTO_IPSSR") is None:
                        patient_data["CYTO_IPSSR"] = "Good"
                    

                    
                    # Store for calculations but keep the prompts intact
                    if 'original_ipss_data' in st.session_state and '__prompts' in st.session_state['original_ipss_data']:
                        prompts = st.session_state['original_ipss_data']['__prompts']
                        st.session_state['original_ipss_data'] = patient_data.copy()
                        st.session_state['original_ipss_data']['__prompts'] = prompts
                    else:
                        st.session_state['original_ipss_data'] = patient_data.copy()
                    
                    calculation_data = patient_data.copy()
                    if '__prompts' in calculation_data:
                        del calculation_data['__prompts']
                    
                    # Make sure to keep the default VAF flag in the session state data
                    if 'used_default_tp53_vaf' in patient_data:
                        calculation_data['used_default_tp53_vaf'] = patient_data['used_default_tp53_vaf']
                        
                    st.session_state['ipss_patient_data'] = calculation_data
                    
                    try:
                        ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
                        ipssr_result = calculate_ipssr(patient_data, return_components=True)
                        
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
                            'derivation': []
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
                            'derivation': []
                        }
                        
                        st.session_state['ipssm_result'] = formatted_ipssm
                        st.session_state['ipssr_result'] = formatted_ipssr
                        st.session_state["risk_results_tab"] = "IPSS-M"
                                                    
                    except Exception as e:
                        st.error(f"Error calculating risk scores: {str(e)}")

    # MANUAL MODE
    else:
        # Get patient data using the existing form
        from app import build_manual_ipss_data  # Import the manual data builder function
        
        patient_data = build_manual_ipss_data()
        if patient_data and st.button("Calculate Risk Scores", type="primary"):
            with st.spinner("Calculating risk scores..."):
                try:
                    # Store original manual data in session state
                    st.session_state['original_ipss_data'] = patient_data.copy()
                    
                    # Remove prompts if they exist before storing calculation data
                    calculation_data = patient_data.copy()
                    if '__prompts' in calculation_data:
                        del calculation_data['__prompts']
                    st.session_state['ipss_patient_data'] = calculation_data
                    
                    # Calculate IPSS-M with contributions
                    ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
                    
                    # Calculate IPSS-R with return_components=True
                    ipssr_result = calculate_ipssr(patient_data, return_components=True)
                    
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
        
        # Show warning if default TP53 VAF value was used
        if patient_data and patient_data.get('used_default_tp53_vaf', False):
            st.warning("⚠️ **Notice:** Default TP53 mutation VAF value (30%) was used in calculations because no specific VAF value was found in your report. For more accurate risk classification, please provide the actual VAF if available.", icon="⚠️")
        
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
            st.markdown("### IPSS-M Risk Classification")
            
            # Display all risk scenarios in a single row with matching panel styles
            st.markdown("#### Risk Calculations")
            
            # Add explanation for the three different risk scores
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 3px solid #4b7bec;">
                <h5 style="margin-top: 0;">Understanding IPSS-M Risk Scores</h5>
                <p>The IPSS-M model provides three different risk scores to account for potential uncertainty in the data:</p>
                <ul>
                    <li><strong>Mean Risk:</strong> Calculated using available data with population averages for any missing values, particularly for residual gene mutations.</li>
                    <li><strong>Best Case:</strong> Assumes the most favorable outcome for any missing data points.</li>
                    <li><strong>Worst Case:</strong> Assumes the most unfavorable outcome for any missing data points.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
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
            
            # Add IPSS-M Contributors section below
            st.markdown("---")
            st.markdown("### IPSS-M Risk Score Contributors")
            if 'contributions' in formatted_ipssm['means']:
                contributions = formatted_ipssm['means']['contributions']
                
                # Sort contributions by absolute value
                sorted_contributions = sorted(
                    contributions.items(),
                    key=lambda x: abs(x[1]) if x[0] != 'total' else 0,
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
                
                # Add a detailed table of gene contributions
                st.markdown("#### Detailed Gene Contribution Values")
                st.markdown("This table shows the exact contribution of each gene and factor to the IPSS-M risk score:")
                
                # Create a styled DataFrame with positive/negative highlighting
                df_styled = df.copy()
                df_styled['Impact'] = ['Risk-increasing' if c > 0 else 'Risk-decreasing' for c in df['Contribution']]
                
                # Separate genetic and clinical factors
                genetic_factors = df_styled[df_styled['Factor'].str.contains('_mut|residual', case=False, regex=True)]
                clinical_factors = df_styled[~df_styled['Factor'].str.contains('_mut|residual', case=False, regex=True)]
                
                # Show tables with styling
                if not genetic_factors.empty:
                    st.markdown("#### Genetic Factors")
                    st.dataframe(
                        genetic_factors,
                        column_config={
                            "Factor": "Gene/Mutation",
                            "Contribution": st.column_config.NumberColumn(
                                "Contribution Value",
                                format="%.3f",
                                help="Contribution to overall risk score"
                            ),
                            "Impact": "Impact on Risk"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                if not clinical_factors.empty:
                    st.markdown("#### Clinical Factors")
                    st.dataframe(
                        clinical_factors,
                        column_config={
                            "Factor": "Clinical Parameter",
                            "Contribution": st.column_config.NumberColumn(
                                "Contribution Value",
                                format="%.3f",
                                help="Contribution to overall risk score"
                            ),
                            "Impact": "Impact on Risk"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Summary statistics
                total_positive = df[df['Contribution'] > 0]['Contribution'].sum()
                total_negative = df[df['Contribution'] < 0]['Contribution'].sum()
                
                st.markdown(f"""
                **Summary:**
                - Total risk-increasing contributions: +{total_positive:.3f}
                - Total risk-decreasing contributions: {total_negative:.3f}
                - Net risk score contribution: {(total_positive + total_negative):.3f}
                """)
        
        elif selected_tab == "IPSS-R":
            # IPSS-R Results section
            st.markdown("### IPSS-R Risk Classification")
            
            # Display IPSS-R score and category
            st.markdown("#### IPSS-R Base Score")
            ipssr_cols = st.columns(2)
            with ipssr_cols[0]:
                st.metric(label="IPSS-R Score", value=f"{formatted_ipssr['IPSSR_SCORE']:.2f}")
            with ipssr_cols[1]:
                ipssr_color = get_risk_class_color(formatted_ipssr['IPSSR_CAT'])
                st.markdown(f"""
                <div style="background-color: {ipssr_color}; padding: 10px; border-radius: 5px; text-align: center;">
                    <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSR_CAT']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Age-adjusted score
            st.markdown("#### Age-adjusted Score (IPSS-RA)")
            ipssra_cols = st.columns(2)
            with ipssra_cols[0]:
                st.metric(label="IPSS-RA Score", value=f"{formatted_ipssr['IPSSRA_SCORE']:.2f}")
            with ipssra_cols[1]:
                ipssra_color = get_risk_class_color(formatted_ipssr['IPSSRA_CAT'])
                st.markdown(f"""
                <div style="background-color: {ipssra_color}; padding: 10px; border-radius: 5px; text-align: center;">
                    <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSRA_CAT']}</span>
                </div>
                """, unsafe_allow_html=True)
                
            # IPSS-R Components
            st.markdown("---")
            st.markdown("### IPSS-R Score Components")
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
                
                # Display parameter categorization table
                st.markdown("### Parameter Categorization")
                st.markdown("This table shows how each parameter is categorized in the IPSS-R scoring system:")
                
                # Create DataFrame for parameter categorization
                param_data = {
                    "Parameter": ["Hemoglobin", "Platelets", "ANC", "Bone Marrow Blasts", "Cytogenetics"],
                    "Value": [patient_data["HB"], patient_data["PLT"], patient_data["ANC"], patient_data["BM_BLAST"], patient_data["CYTO_IPSSR"]],
                    "Category": [
                        f"{formatted_ipssr['hb_category']} ({components.get('Hemoglobin', 'N/A')} points)",
                        f"{formatted_ipssr['plt_category']} ({components.get('Platelets', 'N/A')} points)",
                        f"{formatted_ipssr['anc_category']} ({components.get('ANC', 'N/A')} points)",
                        f"{formatted_ipssr['blast_category']} ({components.get('Bone Marrow Blasts', 'N/A')} points)",
                        f"{formatted_ipssr['cyto_category']} ({components.get('Cytogenetics', 'N/A')} points)"
                    ]
                }
                
                df_params = pd.DataFrame(param_data)
                st.table(df_params)


# Helper function to map risk category to CSS class (ensure this exists or define it)
def get_risk_class(risk_category):
    """Maps risk category string to a CSS class for styling."""
    if risk_category:
        category_lower = risk_category.lower()
        if "favorable" in category_lower:
            return "favorable"
        elif "intermediate" in category_lower:
            return "intermediate"
        elif "adverse" in category_lower:
            return "adverse"
    return "unknown" # Default class if category is None or unexpected


# Main function definition starts here
def eln_risk_calculator_page():
    """
    Standalone calculator for ELN 2022 and ELN 2024 risk assessment for AML,
    with enhanced Streamlit presentation and integrated instructions.
    """

    # --- Page Configuration & Styling ---
    st.markdown(
        """
        <div style="background-color:#FFFFFF; border-radius:8px; padding: 15px 20px; margin-bottom: 10px; border: 1px solid #e6e6e6; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <h2 style="color:#009688; text-align:left; margin:0 0 5px 0;">ELN Risk Calculator</h2>
            <p style="color:#555; margin:0; font-size:0.95rem;">Calculate ELN risk stratification based on ELN 2022 (Intensive) and ELN 2024 (Non-Intensive) guidelines.</p>
        </div>
        """, unsafe_allow_html=True
    )

    with st.expander("ℹ️ How to Use This Calculator", expanded=False):
        st.markdown("""
        * **Purpose:** Calculates ELN 2022 (intensive therapy) & ELN 2024 (non-intensive therapy) risk for AML.
        * **Choose Input Method:**
            * **Free-text Mode (Recommended):** Toggle ON, paste the full report, use optional overrides, click 'Analyse Report'.
            * **Manual Entry Mode:** Toggle OFF, select findings, click 'Calculate ELN Risk'.
        * **Results:** Shows risk category, median OS, and derivation steps. Review 'Data Used' section for inputs.
        """)

    # --- CSS Injection (ensure it's included) ---
    st.markdown("""
    <style>
        /* Include all the CSS from the previous version here */
        .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        .risk-box { padding: 25px; border-radius: 10px; margin-bottom: 20px; text-align: center; border-width: 1px; border-style: solid; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: transform 0.2s ease-in-out; }
        .risk-box:hover { transform: translateY(-3px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .favorable { background-color: #E8F5E9; border-color: #66BB6A; }
        .intermediate { background-color: #FFFDE7; border-color: #FFEE58; }
        .adverse { background-color: #FFEBEE; border-color: #EF5350; }
        .unknown { background-color: #F5F5F5; border-color: #BDBDBD; }
        .risk-title { font-size: 1.1rem; font-weight: 600; color: #333; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .risk-value { font-size: 2.0rem; font-weight: 700; margin-bottom: 12px; color: #111; }
        .risk-os { font-style: normal; font-size: 0.95rem; color: #555; margin-bottom: 0px; }
        .stExpander { border: 1px solid #e6e6e6; border-radius: 8px; margin-bottom: 15px; }
        .stExpander header { font-weight: 600; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        .stExpander[aria-expanded="false"] header { background-color: #fafafa; }
        .stExpander[aria-expanded="true"] header { background-color: #f0f2f6; }
        .stButton button { font-weight: 600; border-radius: 8px; }
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { border: 1px solid #e6e6e6; border-radius: 8px; padding: 1rem; background-color: #ffffff; margin-bottom: 1rem; }
        .stApp > header + div > .block-container > div > div > section > div > div > div > h3 { margin-top: 0.5rem; }
        /* Style for data list items */
        ul li { margin-bottom: 4px; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)


    # --- Input Section ---
    st.subheader("1. Input Patient Data")
    eln_mode_toggle = st.toggle("Use Free-text Mode", key="eln_mode_toggle", value=True, help="Toggle ON to paste report, OFF for manual selection.")
    input_data = None
    col_main_input, col_options = st.columns([3, 1])
    with col_main_input:
        if eln_mode_toggle:
            st.markdown("##### Paste Full Report Text")
            report_text = st.text_area("Enter relevant AML data:", placeholder="Paste comprehensive AML report...", height=300, label_visibility="collapsed")
            calculate_button = st.button("Analyse Report", type="primary", use_container_width=True, key="analyze_report_btn")
        else:
            st.markdown("##### Select Findings Manually")
            with st.container(border=True):
                 eln_data_manual = build_manual_eln_data()
            manual_calculate_button = st.button("Calculate ELN Risk", type="primary", use_container_width=True, key="calculate_manual_btn")
    with col_options:
        if eln_mode_toggle:
            st.markdown("##### Overrides")
            with st.container(border=True):
                 tp53_override = st.selectbox("TP53 Mutation", ["Auto-detect", "Present", "Not detected"], index=0, help="Manually set TP53 status.", key="tp53_override_select")
                 complex_karyotype_override = st.selectbox("Complex Karyotype", ["Auto-detect", "Present", "Not detected"], index=0, help="Manually set complex karyotype status.", key="ck_override_select")
        else:
            st.markdown("##### Options")
            st.caption("Manual entry selected. Options in Free-text mode.")

    # --- Calculation Logic ---
    triggered_calculation = False
    if eln_mode_toggle and st.session_state.get('analyze_report_btn', False) and 'report_text' in locals() and report_text:
        triggered_calculation = True
        overrides = {}
        if tp53_override != "Auto-detect": overrides["tp53_override"] = tp53_override == "Present"
        if complex_karyotype_override != "Auto-detect": overrides["complex_karyotype_override"] = complex_karyotype_override == "Present"
        with st.spinner("🔄 Extracting & calculating..."):
            parsed_eln_data = parse_eln_report(report_text)
            if parsed_eln_data:
                if overrides:
                    if "tp53_override" in overrides: parsed_eln_data["tp53_mutation"] = overrides["tp53_override"]
                    if "complex_karyotype_override" in overrides: parsed_eln_data["complex_karyotype"] = overrides["complex_karyotype_override"]
                input_data = parsed_eln_data
                st.session_state['manual_calculation'] = False
            else:
                st.error("⚠️ Could not extract factors. Check input or use manual entry.")
                input_data = None

    elif not eln_mode_toggle and st.session_state.get('calculate_manual_btn', False):
        triggered_calculation = True
        with st.spinner("🔄 Calculating..."):
            input_data = eln_data_manual
            st.session_state['manual_calculation'] = True

    if triggered_calculation and input_data:
        try:
            eln24_genes = { k: input_data.get(k, False) for k in ["tp53_mutation", "kras", "ptpn11", "nras", "flt3_itd", "npm1_mutation", "idh1", "idh2", "ddx41"] }
            risk_eln2022, eln22_median_os, derivation_eln2022 = eln2022_intensive_risk(input_data)
            risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
            st.session_state['eln_results'] = {
                'risk_eln2022': risk_eln2022, 'eln22_median_os': eln22_median_os, 'derivation_eln2022': derivation_eln2022,
                'risk_eln24': risk_eln24, 'median_os_eln24': median_os_eln24, 'eln24_derivation': eln24_derivation,
                'eln_data': input_data
            }
            st.success("✅ Risk calculation complete!")
        except Exception as e:
            st.error(f"An error occurred during calculation: {e}")
            if 'eln_results' in st.session_state: del st.session_state['eln_results']


    # --- Display Results Section ---
    st.markdown("---")
    st.subheader("2. ELN Risk Classification Results")

    if 'eln_results' in st.session_state:
        results = st.session_state['eln_results']
        # (Result extraction and display for ELN 2022 / 2024 risk boxes - code omitted for brevity, assume it's the same as before)
        risk_eln2022 = results['risk_eln2022']
        eln22_median_os = results['eln22_median_os']
        derivation_eln2022 = results['derivation_eln2022']
        risk_eln24 = results['risk_eln24']
        median_os_eln24 = results['median_os_eln24']
        eln24_derivation = results['eln24_derivation']

        eln_class = get_risk_class(risk_eln2022)
        eln24_class = get_risk_class(risk_eln24)

        eln_col1, eln_col2 = st.columns(2)

        with eln_col1:
            with st.container(border=True):
                st.markdown(f"""
                <div class='risk-box {eln_class}'>
                    <div class='risk-title'>ELN 2022 Risk (Intensive Tx)</div>
                    <div class='risk-value'>{risk_eln2022 or 'N/A'}</div>
                    <div class='risk-os'>Median OS: {eln22_median_os or 'Not Available'}</div>
                </div>""", unsafe_allow_html=True)
                with st.expander("Show ELN 2022 Derivation"):
                    if isinstance(derivation_eln2022, list) and derivation_eln2022:
                        for step in derivation_eln2022: st.markdown(f"- {step}")
                    elif isinstance(derivation_eln2022, str): st.markdown(derivation_eln2022)
                    else: st.info("No derivation steps available.")

        with eln_col2:
            with st.container(border=True):
                os_display_24 = f"{median_os_eln24} months" if isinstance(median_os_eln24, (int, float)) else (median_os_eln24 or 'Not Available')
                st.markdown(f"""
                <div class='risk-box {eln24_class}'>
                    <div class='risk-title'>ELN 2024 Risk (Non-Intensive Tx)</div>
                    <div class='risk-value'>{risk_eln24 or 'N/A'}</div>
                    <div class='risk-os'>Median OS: {os_display_24}</div>
                </div>""", unsafe_allow_html=True)
                with st.expander("Show ELN 2024 Derivation"):
                    if isinstance(eln24_derivation, list) and eln24_derivation:
                        for step in eln24_derivation: st.markdown(f"- {step}")
                    else: st.info("No derivation steps available.")


        # --- Updated Data Used Display ---
        st.markdown("---")
        with st.expander("🔍 View Data Used for Classification", expanded=False):
            st.caption("Features extracted or entered:")
            display_data = results.get('eln_data', {})

            formatted_html_list = format_display_data(display_data)

            # Decide on number of columns based on item count
            num_items = len(formatted_html_list) - 2 # Subtract <ul> tags
            num_columns = 2 if num_items > 6 else 1 # Use 2 columns if more than 6 items

            if num_items > 0:
                 cols = st.columns(num_columns)
                 items_per_col = (num_items + num_columns - 1) // num_columns

                 current_col_index = 0
                 items_in_current_col = 0

                 # Print opening ul tag for the first column
                 cols[current_col_index].markdown(formatted_html_list[0], unsafe_allow_html=True)

                 for i in range(1, len(formatted_html_list) - 1): # Iterate through li items
                     cols[current_col_index].markdown(formatted_html_list[i], unsafe_allow_html=True)
                     items_in_current_col += 1

                     # Check if we need to move to the next column
                     if items_in_current_col == items_per_col and current_col_index < num_columns - 1:
                          # Print closing ul tag for the current column
                          cols[current_col_index].markdown(formatted_html_list[-1], unsafe_allow_html=True)
                          # Move to next column
                          current_col_index += 1
                          items_in_current_col = 0
                          # Print opening ul tag for the new column
                          cols[current_col_index].markdown(formatted_html_list[0], unsafe_allow_html=True)

                 # Print closing ul tag for the last column
                 cols[current_col_index].markdown(formatted_html_list[-1], unsafe_allow_html=True)

            else:
                 # Handle case where format_display_data returned only the info message
                 st.info(formatted_html_list[0])


        # --- Clear Button ---
        if st.button("Clear Results & Start Over", use_container_width=True, key="clear_results_btn"):
            keys_to_clear = ['eln_results', 'manual_calculation', 'analyze_report_btn', 'calculate_manual_btn']
            for key in keys_to_clear:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    else:
        st.info("Enter patient data above and click 'Analyse Report' or 'Calculate ELN Risk' to see the results.")

def ipss_risk_calculator_page():
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
    
    # ipss Risk Calculator Page Top Controls
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
    from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr
    import pandas as pd
    import matplotlib.pyplot as plt
    
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
    ipss_mode_toggle = st.toggle("Free-text Mode", key="ipss_mode_toggle", value=True)
    
    patient_data = None
    
    # FREE TEXT MODE
    if ipss_mode_toggle:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("""
            ### Input MDS/ipss Report
            
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
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="hb_override"
                )
                
                plt_override = st.number_input(
                    "Platelets (10^9/L)",
                    min_value=0, 
                    max_value=1000,
                    value=0,
                    step=1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="plt_override"
                )
            
            with col2:
                anc_override = st.number_input(
                    "ANC (10^9/L)",
                    min_value=0.0, 
                    max_value=20.0,
                    value=0.0,
                    step=0.1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="anc_override"
                )
                
                blast_override = st.number_input(
                    "Bone Marrow Blasts (%)",
                    min_value=0.0, 
                    max_value=30.0,
                    value=0.0,
                    step=0.1,
                    help="Enter a value to override the report. (Default is 0, which means not set.)",
                    key="blast_override"
                )
            
            with col3:
                age_override = st.number_input(
                    "Age (years)",
                    min_value=0, 
                    max_value=120,
                    value=0,  # 18 signals "not set"
                    step=1,
                    help="Enter a value greater than 18 to override the report.",
                    key="age_override"
                )
            
            free_report_text = st.text_area(
                "Enter MDS report data:",
                placeholder="Paste your MDS report here including: lab values, cytogenetics, gene mutations...",
                key="ipss_free_text_input",
                height=250
            )
            
            # Check if all override fields are manually set (i.e. not their default "not set" values)
            all_fields_entered = (
                (hb_override != 0.0) and 
                (plt_override != 0) and 
                (anc_override != 0.0) and 
                (blast_override != 0.0) and 
                (age_override != 0)
            )
            
            if not all_fields_entered:
                st.warning("Please manually enter values for all override fields before submitting.")
            
            # The calculate button is disabled until all override fields have been manually filled.
            calculate_button = st.button(
                "Calculate Risk Scores", 
                key="calculate_ipss_scores", 
                type="primary", 
                disabled=not all_fields_entered
            )
            
            if calculate_button:
                # First try to process any text input
                parsed_data = None
                if free_report_text.strip():
                    with st.spinner("Processing report text..."):
                        parsed_data = parse_ipss_report(free_report_text)
                        if parsed_data:
                            st.info("Report processed successfully.")
                            # Store parsed data for gene mutations and other details
                            st.session_state['original_ipss_data'] = parsed_data.copy()
                            # We'll display JSON in a dedicated section later
                
                # Start with parsed data as the base, then apply overrides only if set
                with st.spinner("Calculating risk scores..."):
                    if parsed_data or 'original_ipss_data' in st.session_state:
                        original_data = parsed_data or st.session_state.get('original_ipss_data', {})
                        patient_data = original_data.copy()
                    else:
                        patient_data = {}
                    
                    # Apply overrides now that we know they're all manually entered
                    patient_data["HB"] = hb_override
                    patient_data["PLT"] = plt_override
                    patient_data["ANC"] = anc_override
                    patient_data["BM_BLAST"] = blast_override
                    patient_data["AGE"] = age_override
                    
                    # Default cytogenetic value if not available - normal karyotype
                    if patient_data.get("CYTO_IPSSR") is None:
                        patient_data["CYTO_IPSSR"] = "Good"

                    
                    # Store for calculations but keep the prompts intact
                    if 'original_ipss_data' in st.session_state and '__prompts' in st.session_state['original_ipss_data']:
                        prompts = st.session_state['original_ipss_data']['__prompts']
                        st.session_state['original_ipss_data'] = patient_data.copy()
                        st.session_state['original_ipss_data']['__prompts'] = prompts
                    else:
                        st.session_state['original_ipss_data'] = patient_data.copy()
                    
                    calculation_data = patient_data.copy()
                    if '__prompts' in calculation_data:
                        del calculation_data['__prompts']
                    
                    # Make sure to keep the default VAF flag in the session state data
                    if 'used_default_tp53_vaf' in patient_data:
                        calculation_data['used_default_tp53_vaf'] = patient_data['used_default_tp53_vaf']
                        
                    st.session_state['ipss_patient_data'] = calculation_data
                    
                    try:
                        ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
                        ipssr_result = calculate_ipssr(patient_data, return_components=True)
                        
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
                            'derivation': []
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
                            'derivation': []
                        }
                        
                        st.session_state['ipssm_result'] = formatted_ipssm
                        st.session_state['ipssr_result'] = formatted_ipssr
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
                    st.session_state['original_ipss_data'] = patient_data.copy()
                    
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
        
        # Show warning if default TP53 VAF value was used
        if patient_data and patient_data.get('used_default_tp53_vaf', False):
            st.warning("⚠️ **Notice:** Default TP53 mutation VAF value (30%) was used in calculations because no specific VAF value was found in your report. For more accurate risk classification, please provide the actual VAF if available.", icon="⚠️")
        
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
            st.markdown("### IPSS-M Risk Classification")
            
            # Display all risk scenarios in a single row with matching panel styles
            st.markdown("#### Risk Calculations")
            
            # Add explanation for the three different risk scores
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 3px solid #4b7bec;">
                <h5 style="margin-top: 0;">Understanding IPSS-M Risk Scores</h5>
                <p>The IPSS-M model provides three different risk scores to account for potential uncertainty in the data:</p>
                <ul>
                    <li><strong>Mean Risk:</strong> Calculated using available data with population averages for any missing values, particularly for residual gene mutations.</li>
                    <li><strong>Best Case:</strong> Assumes the most favorable outcome for any missing data points.</li>
                    <li><strong>Worst Case:</strong> Assumes the most unfavorable outcome for any missing data points.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
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
            
            # Add IPSS-M Contributors section below
            st.markdown("---")
            st.markdown("### IPSS-M Risk Score Contributors")
            if 'contributions' in formatted_ipssm['means']:
                contributions = formatted_ipssm['means']['contributions']
                
                # Sort contributions by absolute value
                sorted_contributions = sorted(
                    contributions.items(),
                    key=lambda x: abs(x[1]) if x[0] != 'total' else 0,
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
                
                # Add a detailed table of gene contributions
                st.markdown("#### Detailed Gene Contribution Values")
                st.markdown("This table shows the exact contribution of each gene and factor to the IPSS-M risk score:")
                
                # Create a styled DataFrame with positive/negative highlighting
                df_styled = df.copy()
                df_styled['Impact'] = ['Risk-increasing' if c > 0 else 'Risk-decreasing' for c in df['Contribution']]
                
                # Separate genetic and clinical factors
                genetic_factors = df_styled[df_styled['Factor'].str.contains('_mut|residual', case=False, regex=True)]
                clinical_factors = df_styled[~df_styled['Factor'].str.contains('_mut|residual', case=False, regex=True)]
                
                # Show tables with styling
                if not genetic_factors.empty:
                    st.markdown("#### Genetic Factors")
                    st.dataframe(
                        genetic_factors,
                        column_config={
                            "Factor": "Gene/Mutation",
                            "Contribution": st.column_config.NumberColumn(
                                "Contribution Value",
                                format="%.3f",
                                help="Contribution to overall risk score"
                            ),
                            "Impact": "Impact on Risk"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                if not clinical_factors.empty:
                    st.markdown("#### Clinical Factors")
                    st.dataframe(
                        clinical_factors,
                        column_config={
                            "Factor": "Clinical Parameter",
                            "Contribution": st.column_config.NumberColumn(
                                "Contribution Value",
                                format="%.3f",
                                help="Contribution to overall risk score"
                            ),
                            "Impact": "Impact on Risk"
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Summary statistics
                total_positive = df[df['Contribution'] > 0]['Contribution'].sum()
                total_negative = df[df['Contribution'] < 0]['Contribution'].sum()
                
                st.markdown(f"""
                **Summary:**
                - Total risk-increasing contributions: +{total_positive:.3f}
                - Total risk-decreasing contributions: {total_negative:.3f}
                - Net risk score contribution: {(total_positive + total_negative):.3f}
                """)
        
        elif selected_tab == "IPSS-R":
            # IPSS-R Results section
            st.markdown("### IPSS-R Risk Classification")
            
            # Display IPSS-R score and category
            st.markdown("#### IPSS-R Base Score")
            ipssr_cols = st.columns(2)
            with ipssr_cols[0]:
                st.metric(label="IPSS-R Score", value=f"{formatted_ipssr['IPSSR_SCORE']:.2f}")
            with ipssr_cols[1]:
                ipssr_color = get_risk_class_color(formatted_ipssr['IPSSR_CAT'])
                st.markdown(f"""
                <div style="background-color: {ipssr_color}; padding: 10px; border-radius: 5px; text-align: center;">
                    <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSR_CAT']}</span>
                </div>
                """, unsafe_allow_html=True)
            
            # Age-adjusted score
            st.markdown("#### Age-adjusted Score (IPSS-RA)")
            ipssra_cols = st.columns(2)
            with ipssra_cols[0]:
                st.metric(label="IPSS-RA Score", value=f"{formatted_ipssr['IPSSRA_SCORE']:.2f}")
            with ipssra_cols[1]:
                ipssra_color = get_risk_class_color(formatted_ipssr['IPSSRA_CAT'])
                st.markdown(f"""
                <div style="background-color: {ipssra_color}; padding: 10px; border-radius: 5px; text-align: center;">
                    <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSRA_CAT']}</span>
                </div>
                """, unsafe_allow_html=True)
                
            # IPSS-R Components
            st.markdown("---")
            st.markdown("### IPSS-R Score Components")
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
                
                # Display parameter categorization table
                st.markdown("### Parameter Categorization")
                st.markdown("This table shows how each parameter is categorized in the IPSS-R scoring system:")
                
                # Create DataFrame for parameter categorization
                param_data = {
                    "Parameter": ["Hemoglobin", "Platelets", "ANC", "Bone Marrow Blasts", "Cytogenetics"],
                    "Value": [patient_data["HB"], patient_data["PLT"], patient_data["ANC"], patient_data["BM_BLAST"], patient_data["CYTO_IPSSR"]],
                    "Category": [
                        f"{formatted_ipssr['hb_category']} ({components.get('Hemoglobin', 'N/A')} points)",
                        f"{formatted_ipssr['plt_category']} ({components.get('Platelets', 'N/A')} points)",
                        f"{formatted_ipssr['anc_category']} ({components.get('ANC', 'N/A')} points)",
                        f"{formatted_ipssr['blast_category']} ({components.get('Bone Marrow Blasts', 'N/A')} points)",
                        f"{formatted_ipssr['cyto_category']} ({components.get('Cytogenetics', 'N/A')} points)"
                    ]
                }
                
                df_params = pd.DataFrame(param_data)
                st.table(df_params)


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

    # Remove the sidebar IPSS calculator call
    # sidebar_ipss_calculator()

    # Add sidebar navigation options
    with st.sidebar:
        selected = option_menu(
            menu_title="Haem.io",
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
        st.session_state["page"] = "ipss_risk_calculator"
    elif selected == "ELN Risk Calculator":
        st.session_state["page"] = "eln_risk_calculator"
    elif selected == "AML/MDS Classifier" and st.session_state["page"] != "results":
        st.session_state["page"] = "data_entry"

    if st.session_state["page"] == "data_entry":
        data_entry_page()
    elif st.session_state["page"] == "results":
        results_page()
    elif st.session_state["page"] == "ipss_risk_calculator":
        ipss_risk_calculator_page()
    elif st.session_state["page"] == "eln_risk_calculator":
        eln_risk_calculator_page()


if __name__ == "__main__":
    app_main()
