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
from parsers.mds_ipss_parser import parse_ipss_report
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
            <div class="app-icon">🧬</div>
            <h1 class="app-title">HemaGenix</h1>
            <p class="app-subtitle">Advanced Hematologic Classification System</p>
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
                        "Agreed blast count(%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=1.0, 
                        value=0.0,
                        key="bone_marrow_blasts_initial",
                        help="Leave at 0 to use value from report. Only set if you want to override."
                    )
                with col1:
                    prior_therapy = st.selectbox(
                        "Previous cytotoxic therapy",
                        options=["None", "Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions (ICC)", "Any combination"],
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
    
    elif sub_tab == "IPSS Risk (MDS)" or sub_tab == "Risk" and show_ipss:
        # Import necessary functions for risk assessment
        from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
        from parsers.mds_ipss_parser import parse_ipss_report
        

        # Style for risk boxes - needed for risk assessments
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
        
        # Create helper function for coloring risk categories
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
        
        st.markdown("## IPSS Risk Assessment")
        st.markdown("International Prognostic Scoring System for myelodysplastic syndromes.")
        
        # Toggle for free-text vs. manual mode (matching the main calculator)
        ipss_mode_toggle = st.toggle("Free-text Mode", key="ipss_classifier_mode_toggle", value=True)
        
        if ipss_mode_toggle:
            # FREE TEXT MODE
            with st.container():
                st.markdown("### Input MDS Report")
                
                # Create 3 columns for the clinical value inputs
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    hb_override = st.number_input(
                        "Hemoglobin (g/dL)", 
                        min_value=0.0, 
                        max_value=20.0,
                        value=None,
                        step=0.1,
                        help="Enter the hemoglobin level in g/dL",
                        key="ipss_hb_override"
                    )
                    
                    plt_override = st.number_input(
                        "Platelets (10^9/L)",
                        min_value=0, 
                        max_value=1000,
                        value=None,
                        step=1,
                        help="Enter the platelet count in 10^9/L",
                        key="ipss_plt_override"
                    )
                
                with col2:
                    anc_override = st.number_input(
                        "ANC (10^9/L)",
                        min_value=0.0, 
                        max_value=20.0,
                        value=None,
                        step=0.1,
                        help="Enter the absolute neutrophil count in 10^9/L",
                        key="ipss_anc_override"
                    )
                    
                    blast_override = st.number_input(
                        "Bone Marrow Blasts (%)",
                        min_value=0.0, 
                        max_value=30.0,
                        value=None,
                        step=0.1,
                        help="Enter the bone marrow blast percentage",
                        key="ipss_blast_override"
                    )
                
                with col3:
                    age_override = st.number_input(
                        "Age (years)",
                        min_value=18, 
                        max_value=120,
                        value=None,
                        step=1,
                        help="Enter the patient's age in years",
                        key="ipss_age_override"
                    )
                    
                    cyto_options = ["Very Good", "Good", "Intermediate", "Poor", "Very Poor"]
                    cyto_override = st.selectbox(
                        "Cytogenetic Risk",
                        options=cyto_options,
                        index=None,
                        help="Select the cytogenetic risk category",
                        key="ipss_cyto_override"
                    )
                
                free_report_text = st.text_area(
                    "Enter MDS report data (optional):",
                    placeholder="Paste your MDS report here if available for additional information",
                    key="ipss_free_text_input",
                    height=150,
                    value=free_text_input_value if free_text_input_value else ""
                )
                
                # Single calculate button
                calculate_button = st.button("Calculate Risk Scores", key="calculate_ipss_scores", type="primary")
                
                if calculate_button:
                    # Check if all required fields are filled
                    missing_fields = []
                    if hb_override is None:
                        missing_fields.append("Hemoglobin")
                    if plt_override is None:
                        missing_fields.append("Platelets")
                    if anc_override is None:
                        missing_fields.append("ANC")
                    if blast_override is None:
                        missing_fields.append("Bone Marrow Blasts")
                    if age_override is None:
                        missing_fields.append("Age")
                    if cyto_override is None:
                        missing_fields.append("Cytogenetic Risk")
                    
                    if missing_fields:
                        st.error(f"Please enter values for all required fields: {', '.join(missing_fields)}")
                    else:
                        # Process any text input (optional)
                        parsed_data = None
                        if free_report_text.strip():
                            with st.spinner("Processing report text for additional information..."):
                                parsed_data = parse_ipss_report(free_report_text)
                                if parsed_data:
                                    st.info("Report processed successfully for additional information.")
                                    # Store parsed data for gene mutations and other details
                                    st.session_state['original_ipss_data'] = parsed_data.copy()
                        
                        # Create patient data from the manual inputs
                        with st.spinner("Calculating risk scores..."):
                            patient_data = {
                                "HB": hb_override,
                                "PLT": plt_override,
                                "ANC": anc_override,
                                "BM_BLAST": blast_override,
                                "AGE": age_override,
                                "CYTO_IPSSR": cyto_override
                            }
                            
                            # If we have parsed data, merge any additional information not covered by manual inputs
                            if parsed_data:
                                # Only copy over fields that don't override the manual inputs
                                for key, value in parsed_data.items():
                                    if key not in ["HB", "PLT", "ANC", "BM_BLAST", "AGE", "CYTO_IPSSR"]:
                                        patient_data[key] = value
                            
                            # Default values for TP53 status if not available from parsed data
                            if "TP53mut" not in patient_data:
                                patient_data["TP53mut"] = "NA"
                            if "TP53loh" not in patient_data:
                                patient_data["TP53loh"] = "NA"
                            if "TP53maxvaf" not in patient_data:
                                patient_data["TP53maxvaf"] = "NA"
                            if "TP53multi" not in patient_data:
                                patient_data["TP53multi"] = "NA"
                            
                            # Calculate IPSS-M scores
                            ipssm_result = calculate_ipssm(patient_data=patient_data)
                            
                            # Calculate IPSS-R scores with components
                            ipssr_result = calculate_ipssr(patient_data=patient_data, return_components=True)
                            
                            # Store the parameter contributions for visualization
                            parameter_contributions = {}
                            if "components" in ipssr_result:
                                parameter_contributions = {
                                    "Cytogenetics": ipssr_result["components"].get("Cytogenetics", 0),
                                    "Blasts": ipssr_result["components"].get("Blasts", 0),
                                    "Hemoglobin": ipssr_result["components"].get("Hemoglobin", 0),
                                    "Platelets": ipssr_result["components"].get("Platelets", 0),
                                    "ANC": ipssr_result["components"].get("ANC", 0)
                                }
                            
                            # Format the IPSS-M result for display
                            formatted_ipssm = {
                                'means': ipssm_result.get('means', {}),
                                'best': ipssm_result.get('best', {}),
                                'worst': ipssm_result.get('worst', {})
                            }
                            
                            # Format the IPSS-R result for display
                            formatted_ipssr = {
                                'IPSSR_SCORE': ipssr_result.get('total_score', 0),
                                'IPSSR_CAT': ipssr_result.get('risk_category', 'Unknown'),
                                'components': ipssr_result.get('components', {})
                            }
                            
                            # Store results in session state
                            st.session_state['ipssm_result'] = formatted_ipssm
                            st.session_state['ipssr_result'] = formatted_ipssr
                            st.session_state['ipss_patient_data'] = patient_data
                
                # If results are available in session state, display them
                if ('ipssm_result' in st.session_state and 
                    'ipssr_result' in st.session_state and
                    st.session_state['ipssm_result'] is not None and
                    st.session_state['ipssr_result'] is not None):
                    
                    # Create navigation menu for IPSS-M and IPSS-R tabs
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
                        default_index=0,
                        orientation="horizontal",
                        key="risk_results_tabs_classifier",
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
                    
                    # Get formatted results from session state
                    formatted_ipssm = st.session_state['ipssm_result']
                    formatted_ipssr = st.session_state['ipssr_result']
                    patient_data = st.session_state['ipss_patient_data']
                    
                    # Display the selected tab content
                    if selected_tab == "IPSS-M":
                        # IPSS-M Results section
                        st.markdown("### IPSS-M Risk Classification")
                        
                        # Display all risk scenarios in a single row
                        st.markdown("#### Risk Calculations")
                        mean_best_worst_cols = st.columns(3)
                        
                        # Mean risk in a styled panel
                        with mean_best_worst_cols[0]:
                            risk_category_m = formatted_ipssm.get("means", {}).get("risk_cat", "Unknown")
                            mean_color = get_risk_class_color(risk_category_m)
                            mean_score = formatted_ipssm.get("means", {}).get("risk_score", "N/A")
                            
                            if isinstance(mean_score, (int, float)):
                                mean_score_display = f"{mean_score:.2f}"
                            else:
                                mean_score_display = str(mean_score)
                                
                            st.markdown(f"""
                            <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                                <div style="font-weight: 500; margin-bottom: 5px;">Mean Risk</div>
                                <div style="font-size: 1.2em; font-weight: bold;">{mean_score_display}</div>
                                <div style="background-color: {mean_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                    {risk_category_m}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        # Best case panel
                        with mean_best_worst_cols[1]:
                            best_category = formatted_ipssm.get("best", {}).get("risk_cat", "Unknown")
                            best_color = get_risk_class_color(best_category)
                            best_score = formatted_ipssm.get("best", {}).get("risk_score", "N/A")
                            
                            if isinstance(best_score, (int, float)):
                                best_score_display = f"{best_score:.2f}"
                            else:
                                best_score_display = str(best_score)
                                
                            st.markdown(f"""
                            <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                                <div style="font-weight: 500; margin-bottom: 5px;">Best Case</div>
                                <div style="font-size: 1.2em; font-weight: bold;">{best_score_display}</div>
                                <div style="background-color: {best_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                    {best_category}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        # Worst case panel
                        with mean_best_worst_cols[2]:
                            worst_category = formatted_ipssm.get("worst", {}).get("risk_cat", "Unknown")
                            worst_color = get_risk_class_color(worst_category)
                            worst_score = formatted_ipssm.get("worst", {}).get("risk_score", "N/A")
                            
                            if isinstance(worst_score, (int, float)):
                                worst_score_display = f"{worst_score:.2f}"
                            else:
                                worst_score_display = str(worst_score)
                                
                            st.markdown(f"""
                            <div style="background-color: white; padding: 8px; border-radius: 5px; text-align: center; border: 1px solid #eee;">
                                <div style="font-weight: 500; margin-bottom: 5px;">Worst Case</div>
                                <div style="font-size: 1.2em; font-weight: bold;">{worst_score_display}</div>
                                <div style="background-color: {worst_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                    {worst_category}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # Get survival data for the mean risk category
                        risk_category_m = formatted_ipssm.get("means", {}).get("risk_cat", "Unknown")
                        survival_data = get_ipssm_survival_data(risk_category_m)
                        
                        # Show survival data
                        st.markdown("#### Survival Data")
                        st.markdown(f"**Median Overall Survival:** {survival_data.get('median_os', 'N/A')}")
                        
                        # Add IPSS-M Contributors section if available
                        if "contributions" in formatted_ipssm.get("means", {}):
                            st.markdown("---")
                            st.markdown("### IPSS-M Risk Score Contributors")
                            contributions = formatted_ipssm["means"]["contributions"]
                            
                            # Sort contributions by absolute value
                            sorted_contributions = sorted(
                                contributions.items(),
                                key=lambda x: abs(x[1]),
                                reverse=True
                            )
                            
                            # Convert to DataFrame for easier plotting
                            import pandas as pd
                            import matplotlib.pyplot as plt
                            
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
                            ipssr_score = formatted_ipssr.get('IPSSR_SCORE', 'N/A')
                            if isinstance(ipssr_score, (int, float)):
                                ipssr_score_display = f"{ipssr_score:.2f}"
                            else:
                                ipssr_score_display = str(ipssr_score)
                                
                            st.metric(label="IPSS-R Score", value=ipssr_score_display)
                            
                        with ipssr_cols[1]:
                            risk_category = formatted_ipssr.get('IPSSR_CAT', 'Unknown')
                            ipssr_color = get_risk_class_color(risk_category)
                            st.markdown(f"""
                            <div style="background-color: {ipssr_color}; padding: 10px; border-radius: 5px; text-align: center;">
                                <span style="font-weight: bold; font-size: 1.2em;">{risk_category}</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        # IPSS-R Components
                        st.markdown("---")
                        st.markdown("### IPSS-R Score Components")
                        
                        if 'components' in formatted_ipssr and formatted_ipssr['components']:
                            import pandas as pd
                            import matplotlib.pyplot as plt
                            import plotly.graph_objects as go
                            
                            components = formatted_ipssr['components']
                            
                            # Prepare data for the horizontal bar chart
                            params = list(components.keys())
                            values = list(components.values())
                            
                            # Define colors for different parameter types
                            colors = {
                                'Cytogenetics': '#FF9800',  # Orange
                                'Blasts': '#F44336',        # Red 
                                'Hemoglobin': '#2196F3',    # Blue
                                'Platelets': '#4CAF50',     # Green
                                'ANC': '#9C27B0'            # Purple
                            }
                            
                            # Create the horizontal bar chart
                            fig = go.Figure(go.Bar(
                                x=values,
                                y=params,
                                orientation='h',
                                marker_color=[colors.get(param, '#757575') for param in params],
                                text=values,
                                textposition='auto'
                            ))
                            
                            # Customize the layout
                            fig.update_layout(
                                title="Contribution to IPSS-R Score",
                                xaxis_title="Points",
                                yaxis_title="Parameters",
                                height=300,
                                margin=dict(l=20, r=20, t=50, b=20)
                            )
                            
                            # Add a vertical line for the total score
                            total_score = sum(values)
                            fig.add_vline(
                                x=total_score, 
                                line_width=2, 
                                line_dash="dash", 
                                line_color="black",
                                annotation_text=f"Total: {total_score:.1f}",
                                annotation_position="top right"
                            )
                            
                            # Display the chart
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Show the values as text too
                            st.markdown("#### Score Components")
                            for param, value in components.items():
                                st.markdown(f"- **{param}**: {value} points")
                            st.markdown(f"- **Total Score**: {total_score}")
                        else:
                            st.info("Parameter contribution data not available for visualization.")
                    else:
                        st.warning("Insufficient data to calculate IPSS risk scores. Please ensure your text contains clinical values and cytogenetics information.")
                else:
                    # MANUAL MODE
                    st.markdown("#### Manual Mode Coming Soon")
                    st.info("Please use the Free-text Mode for now. Manual Mode will be available in a future update.")

    elif sub_tab == "Risk":
        # Import necessary functions for risk assessment
        from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk
        from parsers.aml_eln_parser import parse_eln_report
        from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr, get_ipssm_survival_data
        from parsers.mds_ipss_parser import parse_ipss_report
        

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
    from parsers.mds_ipss_parser import parse_ipss_report
    
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
    with st.expander("Required fields", expanded=True):
        st.markdown("### Required fields")
        st.markdown("Manually enter override values below. All fields must be set before you can calculate the risk.")
        
        # Create 3 columns for the clinical value inputs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hb_override = st.number_input(
                "Hemoglobin (g/dL)", 
                min_value=0.0, 
                max_value=20.0,
                value=0.0,
                step=0.1,
                help="Enter a value to override the report. (Default is 0, meaning not set.)",
                key="ipss_hb_override"
            )
            
            plt_override = st.number_input(
                "Platelets (10^9/L)",
                min_value=0, 
                max_value=1000,
                value=0,
                step=1,
                help="Enter a value to override the report. (Default is 0, meaning not set.)",
                key="ipss_plt_override"
            )
        
        with col2:
            anc_override = st.number_input(
                "ANC (10^9/L)",
                min_value=0.0, 
                max_value=20.0,
                value=0.0,
                step=0.1,
                help="Enter a value to override the report. (Default is 0, meaning not set.)",
                key="ipss_anc_override"
            )
            
            blast_override = st.number_input(
                "Bone Marrow Blasts (%)",
                min_value=0.0, 
                max_value=30.0,
                value=0.0,
                step=0.1,
                help="Enter a value to override the report. (Default is 0, meaning not set.)",
                key="ipss_blast_override"
            )
        
        with col3:
            age_override = st.number_input(
                "Age (years)",
                min_value=0, 
                max_value=120,
                value=0,  # 0 indicates "not set"
                step=1,
                help="Enter an age greater than 0 to override the report.",
                key="ipss_age_override"
            )

    st.markdown("")  # Add an empty line for spacing

    # Check if all override fields have been manually set:
    all_fields_entered = (
        (hb_override != 0.0) and 
        (plt_override != 0) and 
        (anc_override != 0.0) and 
        (blast_override != 0.0) and 
        (age_override != 0)
    )

    if not all_fields_entered:
        st.warning("Please manually enter values for all override fields before submitting.")

    # Button to calculate with overrides (disabled until all fields are set)
    calculate_button = st.button(
        "Calculate IPSS Risk", 
        key="calculate_ipss_with_overrides", 
        type="primary", 
        disabled=not all_fields_entered
    )


    # IPSS-M/R Risk data section - Only run when calculate button is pressed
    if calculate_button and free_text_input_value:
        # Parse the free text for ipss risk parameters
        ipss_data = parse_ipss_report(free_text_input_value)
        
        if ipss_data:
            # Apply overrides if specified by user
            if hb_override > 0:
                ipss_data["HB"] = hb_override
                st.sidebar.info(f"Using override: Hemoglobin: {hb_override} g/dL")
            
            if plt_override > 0:
                ipss_data["PLT"] = plt_override
                st.sidebar.info(f"Using override: Platelets: {plt_override} × 10^9/L")
            
            if anc_override > 0:
                ipss_data["ANC"] = anc_override
                st.sidebar.info(f"Using override: ANC: {anc_override} × 10^9/L")
            
            if blast_override > 0:
                ipss_data["BM_BLAST"] = blast_override
                st.sidebar.info(f"Using override: BM Blasts: {blast_override}%")
            
            if age_override > 18:  # Age 18 is the minimum and signals "not set"
                ipss_data["AGE"] = age_override
                st.sidebar.info(f"Using override: Age: {age_override} years")

            st.sidebar.markdown("---")
            st.sidebar.markdown("### Results")
            
            # Calculate IPSS-M scores
            ipssm_result = calculate_ipssm(patient_data=ipss_data)
            
            # Calculate IPSS-R scores with components
            ipssr_result = calculate_ipssr(patient_data=ipss_data, return_components=True)
            
            # Store the parameter contributions for visualization
            parameter_contributions = {}
            if "components" in ipssr_result:
                parameter_contributions = {
                    "Cytogenetics": ipssr_result["components"].get("Cytogenetics", 0),
                    "Blasts": ipssr_result["components"].get("Blasts", 0),
                    "Hemoglobin": ipssr_result["components"].get("Hemoglobin", 0),
                    "Platelets": ipssr_result["components"].get("Platelets", 0),
                    "ANC": ipssr_result["components"].get("ANC", 0)
                }
            
            # Create two columns for risk displays
            ipss_col1, ipss_col2 = st.sidebar.columns(2)
            
            # IPSS-R Risk Classification
            with ipss_col1:
                risk_category = ipssr_result.get("risk_category", "Unknown")
                risk_class = risk_category.lower().replace(" ", "-") + "-risk" if risk_category else "moderate-risk"
                
                st.markdown(f"""
                <div class='risk-box {risk_class}'>
                    <div class='risk-title'>IPSS-R Risk</div>
                    <div class='risk-value'>{risk_category}</div>
                    <div class='risk-os'>Score: {ipssr_result.get("total_score", "N/A")}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # IPSS-M Risk Classification
            with ipss_col2:
                risk_category_m = ipssm_result.get("means", {}).get("risk_cat", "Unknown")
                risk_class_m = risk_category_m.lower().replace(" ", "-") + "-risk" if risk_category_m else "moderate-risk"
                
                # Get survival data for the mean risk category
                survival_data = get_ipssm_survival_data(risk_category_m)
                
                st.markdown(f"""
                <div class='risk-box {risk_class_m}'>
                    <div class='risk-title'>IPSS-M Risk</div>
                    <div class='risk-value'>{risk_category_m}</div>
                    <div class='risk-os'>Score: {ipssm_result.get("means", {}).get("risk_score", "N/A")}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Display parameter contributions graph
            with st.sidebar.expander("Parameter Contributions", expanded=True):
                st.markdown("### IPSS-R Score Contributions")
                
                if parameter_contributions:
                    import pandas as pd
                    import plotly.graph_objects as go
                    
                    # Prepare data for the horizontal bar chart
                    params = list(parameter_contributions.keys())
                    values = list(parameter_contributions.values())
                    
                    # Define colors for different parameter types
                    colors = {
                        'Cytogenetics': '#FF9800',  # Orange
                        'Blasts': '#F44336',        # Red 
                        'Hemoglobin': '#2196F3',    # Blue
                        'Platelets': '#4CAF50',     # Green
                        'ANC': '#9C27B0'            # Purple
                    }
                    
                    # Create the horizontal bar chart
                    fig = go.Figure(go.Bar(
                        x=values,
                        y=params,
                        orientation='h',
                        marker_color=[colors.get(param, '#757575') for param in params],
                        text=values,
                        textposition='auto'
                    ))
                    
                    # Customize the layout
                    fig.update_layout(
                        title="Contribution to IPSS-R Score",
                        xaxis_title="Points",
                        yaxis_title="Parameters",
                        height=300,
                        margin=dict(l=20, r=20, t=50, b=20)
                    )
                    
                    # Add a vertical line for the total score
                    total_score = sum(values)
                    fig.add_vline(
                        x=total_score, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="black",
                        annotation_text=f"Total: {total_score:.1f}",
                        annotation_position="top right"
                    )
                    
                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show the values as text too
                    st.markdown("#### Score Components")
                    for param, value in parameter_contributions.items():
                        st.markdown(f"- **{param}**: {value} points")
                    st.markdown(f"- **Total Score**: {total_score}")
                else:
                    st.info("Parameter contribution data not available for visualization.")
            
            # Display more detailed information in expander
            with st.sidebar.expander("IPSS Details", expanded=False):
                st.markdown("### IPSS-M Details")
                st.markdown(f"**Mean Risk Score:** {ipssm_result.get('means', {}).get('risk_score', 'N/A')}")
                st.markdown(f"**Risk Category:** {risk_category_m}")
                st.markdown(f"**Median OS:** {survival_data.get('median_os', 'N/A')}")
                
                st.markdown("### IPSS-R Details")
                st.markdown(f"**Standard IPSS-R Score:** {ipssr_result.get('total_score', 'N/A')}")
                st.markdown(f"**Risk Category:** {risk_category}")
        else:
            st.sidebar.warning("Insufficient data to calculate IPSS risk scores. Please ensure your text contains clinical values and cytogenetics information.")
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

    # Remove the sidebar IPSS calculator call
    # sidebar_ipss_calculator()

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
                    min_value=18, 
                    max_value=120,
                    value=18,  # 18 signals "not set"
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
                (age_override != 18)
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
                    
                    # Handle TP53 overrides - updated to match manual form
                    patient_data["TP53mut"] = "NA"
                    patient_data["TP53loh"] = "NA"
                    patient_data["TP53maxvaf"] = "NA"
                    patient_data["TP53multi"] = "NA"
                    
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
            st.markdown("### IPSS-M Risk Classification")
            
            # Display all risk scenarios in a single row with matching panel styles
            st.markdown("#### Risk Calculations")
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
                        f"{formatted_ipssr['hb_category']} ({components['Hemoglobin']} points)",
                        f"{formatted_ipssr['plt_category']} ({components['Platelets']} points)",
                        f"{formatted_ipssr['anc_category']} ({components['ANC']} points)",
                        f"{formatted_ipssr['blast_category']} ({components['Bone Marrow Blasts']} points)",
                        f"{formatted_ipssr['cyto_category']} ({components['Cytogenetics']} points)"
                    ]
                }
                
                df_params = pd.DataFrame(param_data)
                st.table(df_params)

def eln_risk_calculator_page():
    """
    Standalone calculator for ELN 2022 and ELN 2024 risk assessment for AML.
    """
    from classifiers.aml_risk_classifier import classify_full_eln2022, eln2024_non_intensive_risk, classify_ELN2022
    from parsers.aml_eln_parser import parse_eln_report
    from utils.forms import build_manual_eln_data
    
    # Title / Header with styling to match main classifier
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
    
    # Add custom styling for the risk boxes
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
    
    # Instructions expander
    with st.expander("📋 Instructions", expanded=False):
        st.markdown("""
        ## ELN Risk Calculator - Instructions
        
        This tool calculates European LeukemiaNet (ELN) risk stratification for AML patients using either free text reports or manual entry.
        
        ### How to use this calculator:

        #### Free Text Mode:
        1. Toggle "Free-text Mode" to ON
        2. Paste your complete molecular report into the text area
        3. Use the override options if needed (for TP53 or complex karyotype)
        4. Click "Analyse Report" to calculate ELN risk

        #### Manual Entry Mode:
        1. Toggle "Free-text Mode" to OFF
        2. Select all relevant genetic abnormalities in the form
        3. Click "Calculate ELN Risk" to determine the risk category
        
        ### Results:
        - The calculator will show both ELN 2022 and ELN 2024 (Non-Intensive) risk classifications
        - Each result includes the risk category, median overall survival, and detailed derivation steps
        - You can expand the derivation sections to see how the risk was calculated
        """)
    
    # Toggle for free-text vs. manual mode (matching main classifier)
    eln_mode_toggle = st.toggle("Free-text Mode", key="eln_mode_toggle", value=True)
    
    # FREE TEXT MODE
    if eln_mode_toggle:
        with st.expander("Free Text Input", expanded=True):
            st.markdown("### Input AML Report")
            
            st.markdown("""
            Enter your report data below. The system will extract relevant markers for ELN risk classification.
            """)
            
            # Optional override parameters in columns (like main classifier)
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    tp53_override = st.selectbox(
                        "TP53 mutation override",
                        options=["Auto-detect", "Present", "Not detected"],
                        index=0,
                        help="Override TP53 mutation status if necessary"
                    )
                with col2:
                    complex_karyotype_override = st.selectbox(
                        "Complex karyotype override",
                        options=["Auto-detect", "Present", "Not detected"],
                        index=0,
                        help="Override complex karyotype status if necessary"
                    )
            
            # Text area for pasting report - matching main classifier's look
            report_text = st.text_area(
                "Enter all relevant AML data here:",
                placeholder="Paste your AML report here including: clinical info, molecular findings, cytogenetics, mutations...",
                height=250
            )
            
            # Analyse button inside the expander, primary styling
            calculate_button = st.button("Analyse Report", type="primary", use_container_width=True)
    
    # MANUAL MODE
    else:

        
        # Use the build_manual_eln_data function from utils.forms to get the manual inputs
        eln_data_manual = build_manual_eln_data()
        
        # Button for manual calculation - with primary styling
        manual_calculate_button = st.button("Calculate ELN Risk", type="primary", use_container_width=True)
        
        if manual_calculate_button:
            # Process the manually entered data
            with st.spinner("Calculating ELN risk categories..."):
                # Calculate ELN 2022 risk
                risk_eln2022, eln22_median_os, derivation_eln2022 = classify_full_eln2022(eln_data_manual)
                
                # Prepare data for ELN 2024 non-intensive classification
                eln24_genes = {
                    "TP53": eln_data_manual.get("tp53_mutation", False),
                    "KRAS": eln_data_manual.get("kras", False),
                    "PTPN11": eln_data_manual.get("ptpn11", False),
                    "NRAS": eln_data_manual.get("nras", False),
                    "FLT3_ITD": eln_data_manual.get("flt3_itd", False),
                    "NPM1": eln_data_manual.get("npm1_mutation", False),
                    "IDH1": eln_data_manual.get("idh1", False),
                    "IDH2": eln_data_manual.get("idh2", False),
                    "DDX41": eln_data_manual.get("ddx41", False)
                }
                
                # Calculate ELN 2024 non-intensive risk
                risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
                
                # Store the results in session state for display
                st.session_state['eln_results'] = {
                    'risk_eln2022': risk_eln2022,
                    'eln22_median_os': eln22_median_os,
                    'derivation_eln2022': derivation_eln2022,
                    'risk_eln24': risk_eln24,
                    'median_os_eln24': median_os_eln24,
                    'eln24_derivation': eln24_derivation,
                    'eln_data': eln_data_manual
                }
                
                # Set flag to indicate manual calculation was performed
                st.session_state['manual_calculation'] = True
                
                # Rerun to display the results
                st.rerun()
    
    # Process the report text when the calculate button is clicked (for free text mode)
    if eln_mode_toggle and calculate_button and report_text:
        # Apply overrides if specified
        overrides = {}
        if tp53_override != "Auto-detect":
            overrides["tp53_override"] = tp53_override == "Present"
        if complex_karyotype_override != "Auto-detect":
            overrides["complex_karyotype_override"] = complex_karyotype_override == "Present"
        
        # Process the report text
        with st.spinner("Extracting data and calculating risk..."):
            # Parse the report to extract ELN markers
            parsed_eln_data = parse_eln_report(report_text)
            
            # Apply any overrides
            if parsed_eln_data and overrides:
                for key, value in overrides.items():
                    if key == "tp53_override":
                        parsed_eln_data["tp53_mutation"] = value
                    elif key == "complex_karyotype_override":
                        parsed_eln_data["complex_karyotype"] = value
            
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
                
                # Store the results in session state for display
                st.session_state['eln_results'] = {
                    'risk_eln2022': risk_eln2022,
                    'eln22_median_os': eln22_median_os,
                    'derivation_eln2022': derivation_eln2022,
                    'risk_eln24': risk_eln24,
                    'median_os_eln24': median_os_eln24,
                    'eln24_derivation': eln24_derivation,
                    'eln_data': parsed_eln_data
                }
                
                # Set flag to indicate report processing was performed
                st.session_state['manual_calculation'] = False
                
                # Rerun to display the results
                st.rerun()
            else:
                st.error("Could not extract sufficient ELN risk factors from the report. Please try using the manual entry option.")
    
    # Display results if available in session state
    if 'eln_results' in st.session_state:
        results = st.session_state['eln_results']
        
        
        # Get the risk data
        risk_eln2022 = results['risk_eln2022']
        eln22_median_os = results['eln22_median_os']
        derivation_eln2022 = results['derivation_eln2022']
        risk_eln24 = results['risk_eln24']
        median_os_eln24 = results['median_os_eln24']
        eln24_derivation = results['eln24_derivation']
        
        # Get the risk classes for styling
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
        
        # Display the data used for calculation for transparency
        with st.expander("Data Used for Classification", expanded=False):
            st.subheader("Features Used for ELN Classification")
            display_data = results['eln_data'].copy()
            if '__prompts' in display_data:
                del display_data['__prompts']
            st.json(display_data)
        
        # Clear results button
        if st.button("Clear Results and Start Over"):
            # Remove the results from session state
            if 'eln_results' in st.session_state:
                del st.session_state['eln_results']
            if 'manual_calculation' in st.session_state:
                del st.session_state['manual_calculation']
            # Rerun to refresh the page
            st.rerun()

# Helper function for risk class styling
def get_risk_class(risk):
    """Returns the CSS class for a risk category."""
    risk = risk.lower() if isinstance(risk, str) else "intermediate"
    if "favorable" in risk:
        return "favorable"
    elif "adverse" in risk:
        return "adverse"
    else:
        return "intermediate"

if __name__ == "__main__":
    app_main()
