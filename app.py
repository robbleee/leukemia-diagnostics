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
    st.title("Diagnosis Support Tool")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_user(username, password):
            token = create_jwt_token(username)
            st.session_state["jwt_token"] = token
            st.session_state["username"] = username
            cookies["jwt_token"] = token
            cookies.save()
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password!")

##################################
# APP MAIN
##################################
def app_main():
    full_report_text = ""
    token = st.session_state.get("jwt_token")
    user_data = verify_jwt_token(token) if token else None
    if not user_data:
        st.info("🔒 **Log in** to use the classification features.")
        show_login_page()
        return

    # Sidebar expander with logout.
    with st.sidebar.expander("User Options", expanded=True):
        st.write("Logged in as:", st.session_state["username"])
        if st.button("Logout"):
            st.session_state["jwt_token"] = None
            st.session_state["username"] = ""
            cookies["jwt_token"] = ""
            cookies.save()
            st.rerun()

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

    aml_mode_toggle = st.toggle("Free-text Mode", key="aml_mode_toggle", value=True)
    if "aml_busy" not in st.session_state:
        st.session_state["aml_busy"] = False

    # --- MANUAL MODE ---
    if not aml_mode_toggle:
        manual_data = build_manual_aml_data()
        if st.button("Analyse Genetics", key="analyse_genetics_manual"):
            st.session_state["aml_manual_expanded"] = False
            st.session_state["aml_busy"] = True
            with st.spinner("Compiling results. Please wait..."):
                for key in [
                    "aml_manual_result",
                    "aml_ai_result",
                    "aml_class_review",
                    "aml_mrd_review",
                    "aml_gene_review",
                    "aml_additional_comments",
                    "initial_parsed_data",
                    "blast_percentage_known"
                ]:
                    st.session_state.pop(key, None)
                classification_who, who_derivation = classify_combined_WHO2022(manual_data, not_erythroid=False)
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
        # Free text input area
        with st.expander("Input Area", expanded=st.session_state.get("aml_free_text_expanded", True)):
            # Optional fields container in 4 columns:
            #   col0: Bone Marrow Blasts Override (%)
            #   col1: Prior cytotoxic chemotherapy (dropdown)
            #   col2: Germline predisposition (dropdown with default "No")
            #   col3: Previous MDS/MDS-MPN
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
                    prior_chemo = st.selectbox(
                        "Prior cytotoxic chemotherapy",
                        options=["No", "Yes"],
                        index=0
                    )
                with col2:
                    germline_options = [
                        "No", "Down syndrome", "BRCA1", "BRCA2", "TP53", "CHEK2", "PALB2",
                        "DDX1", "RUNX1", "CEBPA", "GATA2", "ETV6", "ANKRD26", 
                        "SRP72", "SAMD9", "SAMD9L", "Other"
                    ]
                    germline_pred = st.selectbox(
                        "Germline predisposition",
                        options=germline_options,
                        index=0
                    )
                with col3:
                    previous_mds = st.selectbox("Previous MDS/MDS-MPN", options=["None", "Previous MDS", "Previous MDS/MPN"])
            
            full_report_text = st.text_area(
                "Enter all relevant AML/MDS data here (Blast % is required; everything else is optional):",
                placeholder="Paste all reports and clinical info here",
                key="full_text_input",
                height=200
            )
        
        # Only show the "Analyse Report" button if manual input is not pending.
        if not (st.session_state.get("initial_parsed_data") and st.session_state.get("manual_inputs_visible") is False):
            if st.button("Analyse Report", key="analyse_report"):
                # Clear previous results.
                for key in [
                    "aml_ai_result",
                    "aml_class_review",
                    "aml_mrd_review",
                    "aml_gene_review",
                    "aml_additional_comments",
                    "initial_parsed_data",
                    "blast_percentage_known"
                ]:
                    st.session_state.pop(key, None)
                if full_report_text.strip():
                    # Build optional text from the 4 fields.
                    opt_text = ""
                    opt_text += "Bone Marrow Blasts Override: " + str(st.session_state["bone_marrow_blasts_initial"]) + "%. "
                    if germline_pred != "No":
                        opt_text += "Germline predisposition: " + germline_pred + ". "
                    else:
                        opt_text += "Germline predisposition: None. "
                    if prior_chemo != "No":
                        opt_text += "Prior cytotoxic chemotherapy: Yes. "
                    else:
                        opt_text += "Prior cytotoxic chemotherapy: No. "
                    if previous_mds != "None":
                        opt_text += "Previous MDS/MDS-MPN: " + previous_mds + ". "
                    full_report_text = opt_text + "\n" + full_report_text
                    with st.spinner("Parsing report..."):
                        parsed_data = parse_genetics_report_aml(full_report_text)
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
                            st.session_state["manual_inputs_visible"] = False
                else:
                    st.error("No AML data provided.")
        
        # Always show the manual input form if initial data exists.
        if st.session_state.get("initial_parsed_data"):
            st.warning("Either the blast percentage could not be automatically determined or the differentiation is ambiguous/missing. Please provide the missing information to proceed with classification.")
            with st.expander("Enter Manual Inputs", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    default_blast = float(st.session_state["initial_parsed_data"].get("blasts_percentage")) if st.session_state["initial_parsed_data"].get("blasts_percentage") != "Unknown" else 0.0
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
                # Propagate the override value from the initial form.
                updated_parsed_data["bone_marrow_blasts_override"] = st.session_state["bone_marrow_blasts_initial"]
                if updated_parsed_data.get("AML_differentiation") is None or (updated_parsed_data.get("AML_differentiation") or "").lower() == "ambiguous":
                    updated_parsed_data["AML_differentiation"] = diff_map[manual_differentiation]
                with st.spinner("Re-classifying with manual inputs..."):
                    who_class, who_deriv = classify_combined_WHO2022(updated_parsed_data, not_erythroid=False)
                    icc_class, icc_deriv = classify_combined_ICC2022(updated_parsed_data)
                    eln_class, eln_deriv = classify_ELN2022(updated_parsed_data)
                    st.session_state["aml_ai_result"] = {
                        "parsed_data": updated_parsed_data,
                        "who_class": who_class,
                        "who_derivation": who_deriv,
                        "icc_class": icc_class,
                        "icc_derivation": icc_deriv,
                        "eln_class": eln_class,
                        "eln_derivation": eln_deriv,
                        "free_text_input": full_report_text
                    }
                    st.session_state["expanded_aml_section"] = "classification"
                    # Do not clear initial_parsed_data so the form remains for further updates.

    # --- Display Results Sub-menu ---
    if "aml_manual_result" in st.session_state or "aml_ai_result" in st.session_state:
        res = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
        mode = "manual" if "aml_manual_result" in st.session_state else "ai"
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
                classification_eln=res["eln_class"],
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
            st.markdown("### ELN 2022 Risk Classification")
            st.markdown(f"**Risk Category:** {res['eln_class']}")
            with st.expander("ELN Derivation", expanded=True):
                for i, step in enumerate(res["eln_derivation"], start=1):
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

        # --- Download, Report Incorrect, and Clear Buttons ---

        st.markdown(
            """
            <style>
            /* This targets the button in the sixth column of a horizontal block */
            div[data-testid="stHorizontalBlock"] > div:nth-of-type(6) button {
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

        # Arrange buttons in six columns so that Clear is the leftmost.
        col_download, col_report, col3, col4, col5, col_clear = st.columns(6)

        with col_clear:
            if st.button("Clear Analysis Results", key="clear_button"):
                for key in clear_keys:
                    st.session_state.pop(key, None)
                st.rerun()


        with col_download:
            if st.button("Download Report"):
                st.session_state["show_pdf_form"] = True

        with col_report:
            if st.button("Report Incorrect Result"):
                st.session_state["show_report_incorrect"] = True

                st.session_state["show_report_incorrect"] = True

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
                    except Exception as e:
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
                    st.markdown("### PDF Preview")
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base_pdf_b64}" width="100%" height="600"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                    st.session_state.show_pdf_form = False

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

##################################
# Main Execution
##################################
if __name__ == "__main__":
    app_main()
