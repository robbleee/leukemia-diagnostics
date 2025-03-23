import streamlit as st
# IMPORTANT: Call set_page_config as the very first Streamlit command.
st.set_page_config(
    page_title="Haematologic Classification",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import urllib.parse
import bcrypt
import datetime
import jwt
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
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022
from classifiers.aml_risk_classifier import classify_ELN2022, eln2024_non_intensive_risk
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
        with st.expander("Input Area", expanded=st.session_state.get("aml_free_text_expanded", True)):
            with st.container():
                col0, col1, col2, col3 = st.columns(4)
                with col0:
                    bone_marrow_blasts = st.number_input(
                        "Bone Marrow Blasts Override (%)", 
                        min_value=0.0, 
                        max_value=100.0, 
                        step=0.1, 
                        value=0.0,
                        key="bone_marrow_blasts_initial"
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
                        "Germline predisposition?",
                        options=["Yes", "None", "Undetermined"],
                        index=2,
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
            
            full_report_text = st.text_area(
                "Enter all relevant AML/MDS data here:",
                placeholder="Paste all reports and clinical info here",
                key="full_text_input",
                height=200
            )

        if not (st.session_state.get("initial_parsed_data") and st.session_state.get("manual_inputs_visible") is False):
            if st.button("Analyse Report", key="analyse_report"):
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

            if st.button("Analyse With Manual Inputs", key="submit_manual"):
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

    sub_tab = option_menu(
        menu_title=None,
        options=["Classification", "Risk", "MRD Review", "Gene Review", "AI Comments", "Differentiation"],
        icons=["clipboard", "graph-up-arrow", "recycle", "bar-chart", "chat-left-text", "funnel"],
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
            with st.expander("ELN 2022 Derivation", expanded=True):
                for line in derivation_eln2022:
                    st.markdown(f"- {line}")
        
        # Right Column: Revised ELN24 Non-Intensive Risk Classification
        with col2:
            st.markdown("#### Revised ELN24 (Non-Intensive) Risk")
            eln24_genes = res["parsed_data"].get("ELN2024_risk_genes", {})
            risk_eln24, median_os_eln24, eln24_derivation = eln2024_non_intensive_risk(eln24_genes)
            st.markdown(f"**Risk Category:** {risk_eln24}")
            st.markdown(f"**Median OS:** {median_os_eln24} months")
            with st.expander("Revised ELN24 Derivation", expanded=True):
                for step in eln24_derivation:
                    st.markdown(f"- {step}")

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
    
    # Import the calculator functions
    from classifiers.mds_ipssm_risk_classifier import calculate_ipssm, calculate_ipssr
    import pandas as pd
    import matplotlib.pyplot as plt
    
    # Get patient data using the existing form
    patient_data = build_manual_ipss_data()
    
    # Calculate button
    if st.button("Calculate Risk Scores", type="primary"):
        with st.spinner("Calculating risk scores..."):
            try:
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
                    'derivation': []  # Add derivation if needed
                }
                
                # Store results in session state
                st.session_state['ipssm_result'] = formatted_ipssm
                st.session_state['ipssr_result'] = formatted_ipssr
                st.session_state['ipss_patient_data'] = patient_data
                
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
                
                # Create a unified results summary section
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
                
                # IPSS-M and IPSS-R results side by side
                col1, col2 = st.columns(2)
                
                with col1:
                    # IPSS-M section
                    st.subheader("IPSS-M Risk Classification")
                    
                    # Display mean risk score and category
                    mean_score_col, mean_cat_col = st.columns(2)
                    with mean_score_col:
                        st.metric(label="Mean Risk Score", value=f"{formatted_ipssm['means']['riskScore']:.2f}")
                    with mean_cat_col:
                        cat_color = get_risk_class_color(formatted_ipssm['means']['riskCat'])
                        st.markdown(f"""
                        <div style="background-color: {cat_color}; padding: 10px; border-radius: 5px; text-align: center;">
                            <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssm['means']['riskCat']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Alternative scenarios
                    st.markdown("#### Alternative Scenarios")
                    best_col, worst_col = st.columns(2)
                    
                    with best_col:
                        best_color = get_risk_class_color(formatted_ipssm['best']['riskCat'])
                        st.markdown(f"""
                        <div style="background-color: #e8f5e9; padding: 8px; border-radius: 5px; text-align: center;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Best Case</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssm['best']['riskScore']:.2f}</div>
                            <div style="background-color: {best_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {formatted_ipssm['best']['riskCat']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with worst_col:
                        worst_color = get_risk_class_color(formatted_ipssm['worst']['riskCat'])
                        st.markdown(f"""
                        <div style="background-color: #fbe9e7; padding: 8px; border-radius: 5px; text-align: center;">
                            <div style="font-weight: 500; margin-bottom: 5px;">Worst Case</div>
                            <div style="font-size: 1.2em; font-weight: bold;">{formatted_ipssm['worst']['riskScore']:.2f}</div>
                            <div style="background-color: {worst_color}; border-radius: 4px; padding: 3px; margin-top: 5px;">
                                {formatted_ipssm['worst']['riskCat']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    # IPSS-R section
                    st.subheader("IPSS-R Risk Classification")
                    
                    # Display IPSS-R score and category
                    ipssr_score_col, ipssr_cat_col = st.columns(2)
                    with ipssr_score_col:
                        st.metric(label="IPSS-R Score", value=f"{formatted_ipssr['IPSSR_SCORE']:.2f}")
                    with ipssr_cat_col:
                        ipssr_color = get_risk_class_color(formatted_ipssr['IPSSR_CAT'])
                        st.markdown(f"""
                        <div style="background-color: {ipssr_color}; padding: 10px; border-radius: 5px; text-align: center;">
                            <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSR_CAT']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Age-adjusted score
                    st.markdown("#### Age-adjusted Score")
                    ipssra_score_col, ipssra_cat_col = st.columns(2)
                    with ipssra_score_col:
                        st.metric(label="IPSS-RA Score", value=f"{formatted_ipssr['IPSSRA_SCORE']:.2f}")
                    with ipssra_cat_col:
                        ipssra_color = get_risk_class_color(formatted_ipssr['IPSSRA_CAT'])
                        st.markdown(f"""
                        <div style="background-color: {ipssra_color}; padding: 10px; border-radius: 5px; text-align: center;">
                            <span style="font-weight: bold; font-size: 1.2em;">{formatted_ipssr['IPSSRA_CAT']}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Display IPSS-R components
                    if 'components' in ipssr_result:
                        st.markdown("#### Score Components")
                        
                        components = ipssr_result['components']
                        components_info = [
                            {"name": "Cytogenetics", "value": components["Cytogenetics"]},
                            {"name": "Bone Marrow Blasts", "value": components["Bone Marrow Blasts"]},
                            {"name": "Hemoglobin", "value": components["Hemoglobin"]},
                            {"name": "Platelets", "value": components["Platelets"]},
                            {"name": "ANC", "value": components["ANC"]}
                        ]
                        
                        # Sort by contribution and display as a simple table
                        components_info.sort(key=lambda x: x["value"], reverse=True)
                        
                        # Convert to DataFrame and display
                        comp_df = pd.DataFrame(components_info)
                        st.dataframe(comp_df, hide_index=True, use_container_width=True)
                
                # Create tabs for IPSS-M and IPSS-R visualizations
                vis_tab1, vis_tab2 = st.tabs(["IPSS-M Visualizations", "IPSS-R Visualizations"])
                
                # IPSS-M Visualizations tab
                with vis_tab1:
                    if 'contributions' in ipssm_result['means']:
                        st.markdown("## IPSS-M Risk Score Contributors")
                        contributions = ipssm_result['means']['contributions']
                        
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
                        st.markdown("### Detailed Gene Contribution Values")
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
                
                # IPSS-R Visualizations tab
                with vis_tab2:
                    if 'components' in ipssr_result:
                        st.markdown("## IPSS-R Score Components")
                        components = ipssr_result['components']
                        
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
                                f"{ipssr_result['hb_category']} ({components['Hemoglobin']} points)",
                                f"{ipssr_result['plt_category']} ({components['Platelets']} points)",
                                f"{ipssr_result['anc_category']} ({components['ANC']} points)",
                                f"{ipssr_result['blast_category']} ({components['Bone Marrow Blasts']} points)",
                                f"{ipssr_result['cyto_category']} ({components['Cytogenetics']} points)"
                            ]
                        }
                        
                        df_params = pd.DataFrame(param_data)
                        st.table(df_params)
                
            except Exception as e:
                st.error(f"Error calculating risk scores: {str(e)}")

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

    with st.sidebar.expander("User Options", expanded=True):
        st.write("Logged in as:", st.session_state["username"])
        if st.button("Logout"):
            st.session_state["jwt_token"] = None
            st.session_state["username"] = ""
            cookies["jwt_token"] = ""
            cookies.save()
            st.rerun()

    # Add sidebar navigation options
    with st.sidebar:
        selected = option_menu(
            menu_title="Navigation",
            options=["AML/MDS Classifier", "IPSS-M/R Risk Tool"],
            icons=["clipboard-data", "calculator"],
            menu_icon="cast",
            default_index=0,
        )
        
    if "page" not in st.session_state:
        st.session_state["page"] = "data_entry"
    
    # Handle navigation selection
    if selected == "IPSS-M/R Risk Tool":
        st.session_state["page"] = "ipcc_risk_calculator"
    elif selected == "AML/MDS Classifier" and st.session_state["page"] != "results":
        st.session_state["page"] = "data_entry"

    if st.session_state["page"] == "data_entry":
        data_entry_page()
    elif st.session_state["page"] == "results":
        results_page()
    elif st.session_state["page"] == "ipcc_risk_calculator":
        ipcc_risk_calculator_page()

if __name__ == "__main__":
    app_main()
