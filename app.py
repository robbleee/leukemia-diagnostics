import streamlit as st
import bcrypt
import json
import datetime
from openai import OpenAI
from streamlit_option_menu import option_menu
from fpdf import FPDF
import re
import base64
import streamlit.components.v1 as components  # <-- Ensure this line is present

# Example imports for your parsers/classifiers
from parsers.aml_parser import parse_genetics_report_aml
from parsers.aml_response_parser import parse_aml_response_report
from parsers.mds_parser import parse_genetics_report_mds
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022

# Splitted review imports
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
        layout="wide",
        initial_sidebar_state="expanded"
    )

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

def login_logout():
    """Handles login/logout in the sidebar."""
    if st.session_state['authenticated']:
        st.sidebar.markdown(f"### Logged in as **{st.session_state['username']}**")
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = ''
            st.sidebar.success("Logged out successfully!")
    else:
        st.sidebar.header("Login for all Features")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", key="login_button"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.sidebar.success("Logged in successfully!")
                # Force a full script rerun so that the top-level st.set_page_config()
                # sees authenticated=True and collapses the sidebar immediately:
                st.rerun()
            else:
                st.sidebar.error("Invalid username or password")

login_logout()


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




# ------------------------------------------------------------------------------
# Helper function to strip markdown formatting from text
# ------------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """
    Remove common markdown tokens (headings, emphasis, code markers) so that
    the PDF shows plain, nicely formatted text.
    """
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'__(.*?)__', r'\1', text)        # bold alternate
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # italic
    text = re.sub(r'_(.*?)_', r'\1', text)            # italic alternate
    text = re.sub(r'`{1,3}', '', text)                # inline code
    return text.strip()

def write_line_with_keywords(pdf: FPDF, line: str, line_height: float = 8):
    """
    Writes a line to the PDF, but forces certain keywords to be in bold.
    """
    bold_keywords = ["Classification Review", "Sample Quality:", "Derivation Steps:", "Classification:", "Other Genes"]
    # We'll find all occurrences of any of the keywords.
    occurrences = []
    for kw in bold_keywords:
        start = line.find(kw)
        if start != -1:
            occurrences.append((start, kw))
    occurrences.sort(key=lambda x: x[0])
    
    current = 0
    # If there are no occurrences, just write the whole line normally.
    if not occurrences:
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line)
        pdf.ln(line_height)
        return
    
    # Otherwise, write in segments.
    for start, kw in occurrences:
        if start > current:
            # Write the segment before the keyword in normal font.
            pdf.set_font("Arial", "", 10)
            pdf.write(line_height, line[current:start])
        # Write the keyword in bold.
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, kw)
        current = start + len(kw)
    # Write any remaining text in normal font.
    if current < len(line):
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line[current:])
    pdf.ln(line_height)

def output_review_text(pdf: FPDF, review_text: str, section: str):
    """
    Splits review_text into lines and outputs each line.
    
    For sections "MRD Review", "Gene Review", and "Additional Comments", if a line is short
    and entirely uppercase, it is rendered as a subheading (bold, larger font).
    Otherwise, each line is output using write_line_with_keywords() so that specific keywords
    are automatically rendered in bold.
    
    For other sections (for example, "Classification Review"), all lines are output via write_line_with_keywords().
    """
    # For duplicate heading removal, we filter only for some sections.
    DUPLICATE_HEADINGS = {
        "MRD Review": ["MRD Strategy", "MRD Review", "MRD Review:"],
        "Gene Review": ["Genetics Review", "Gene Review", "Genetics Review:"],
        "Additional Comments": ["Additional Considerations", "Additional Considerations:"]
    }
    dup_list = DUPLICATE_HEADINGS.get(section, [])
    lines = review_text.splitlines()
    
    for line in lines:
        cleaned_line = clean_text(line)
        if not cleaned_line:
            pdf.ln(4)
            continue
        # For sections with duplicate headings to filter, skip them.
        if dup_list and any(cleaned_line.lower() == dup.lower() for dup in dup_list):
            continue
        # If the section is one where we want subheading formatting…
        if section in ["MRD Review", "Gene Review", "Additional Comments"]:
            # If the line is short and entirely uppercase, treat it as a subheading.
            if len(cleaned_line) < 30 and cleaned_line.isupper():
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, cleaned_line, ln=1)
                pdf.set_font("Arial", "", 10)
            else:
                write_line_with_keywords(pdf, cleaned_line)
        else:
            # For Classification Review and other sections, always output using inline keyword formatting.
            write_line_with_keywords(pdf, cleaned_line)

# ------------------------------------------------------------------------------
# Custom PDF class with a minimal header (only on the first page) and a footer
# ------------------------------------------------------------------------------
class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", "B", 14)
            self.set_text_color(0, 70, 140)
            self.cell(0, 8, "Diagnostic Report", ln=1, align="C")
            self.set_font("Arial", "", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, datetime.datetime.now().strftime("%B %d, %Y"), ln=1, align="C")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

# ------------------------------------------------------------------------------
# Helper function: Add a colored section title
# ------------------------------------------------------------------------------
def add_section_title(pdf: PDF, title: str):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 70, 140)
    pdf.cell(0, 10, clean_text(title), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

# ------------------------------------------------------------------------------
# Helper function: Add the classification details in a “table‐like” layout.
# ------------------------------------------------------------------------------
def add_classification_section(pdf: PDF, classification_data: dict):
    line_height = 8
    # WHO 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "WHO 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, line_height, f"Classification: {clean_text(classification_data['WHO']['classification'])}")
    pdf.multi_cell(0, line_height, "Derivation Steps:")
    for i, step in enumerate(classification_data["WHO"]["derivation"], start=1):
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(4)
    # ICC 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "ICC 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, line_height, f"Classification: {clean_text(classification_data['ICC']['classification'])}")
    pdf.multi_cell(0, line_height, "Derivation Steps:")
    for i, step in enumerate(classification_data["ICC"]["derivation"], start=1):
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(6)

# ------------------------------------------------------------------------------
# Helper function: Build a diagnostic section (AML or MDS) using session state data.
# ------------------------------------------------------------------------------
def add_diagnostic_section(pdf: PDF, diag_type: str):
    """
    diag_type: "AML" or "MDS"
    """
    manual_key = diag_type.lower() + "_manual_result"
    ai_key = diag_type.lower() + "_ai_result"
    if manual_key in st.session_state:
        data = st.session_state[manual_key]
        prefix = diag_type.lower() + "_manual"
    elif ai_key in st.session_state:
        data = st.session_state[ai_key]
        prefix = diag_type.lower() + "_ai"
    else:
        return

    classification_data = {
        "WHO": {
            "classification": data["who_class"],
            "derivation": data["who_derivation"]
        },
        "ICC": {
            "classification": data["icc_class"],
            "derivation": data["icc_derivation"]
        }
    }

    add_section_title(pdf, f"{diag_type} Classification Results")
    add_classification_section(pdf, classification_data)

    review_sections = [
        ("Classification Review", prefix + "_class_review"),
        ("MRD Review", prefix + "_mrd_review"),
        ("Gene Review", prefix + "_gene_review"),
        ("Additional Comments", prefix + "_additional_comments")
    ]
    for section_name, key in review_sections:
        if key in st.session_state:
            add_section_title(pdf, section_name)
            output_review_text(pdf, st.session_state[key], section_name)
            pdf.ln(4)

# ------------------------------------------------------------------------------
# Main function: Create the beautifully formatted PDF report.
# Now it accepts patient_name and patient_dob, which are included at the top.
# ------------------------------------------------------------------------------
def create_beautiful_pdf(patient_name: str, patient_dob: datetime.date) -> bytes:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add a Patient Information section at the top.
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=1)
    pdf.cell(0, 10, f"Date of Birth: {patient_dob.strftime('%B %d, %Y')}", ln=1)
    pdf.ln(10)

    # Add diagnostic sections (AML and MDS, if available)
    add_diagnostic_section(pdf, "AML")
    add_diagnostic_section(pdf, "MDS")

    return pdf.output(dest="S").encode("latin1")







##################################
# FORMS & PARSING HELPERS
##################################
def build_manual_aml_data() -> dict:
    # Wrap everything in a single expander
    with st.expander("Manual Input Area", expanded=True):
        st.markdown("### Manual AML Data Entry")
        # ---------------------------------------------------------------------
        # Blasts
        # ---------------------------------------------------------------------
        blasts = st.number_input(
            "Blasts (%)",
            min_value=0.0, 
            max_value=100.0, 
            value=0.0,
            key="aml_blasts_percentage"
        )

        # ---------------------------------------------------------------------
        # AML-defining Recurrent Genetic Abnormalities (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### AML-defining Recurrent Genetic Abnormalities")
        c_aml1, c_aml2, c_aml3, c_aml4 = st.columns(4)

        with c_aml1:
            npm1 = st.checkbox("NPM1 mutation", key="aml_npm1_mutation")
            runx1_runx1t1 = st.checkbox("RUNX1::RUNX1T1 fusion", key="aml_runx1_runx1t1")
            cbfb_myh11 = st.checkbox("CBFB::MYH11 fusion", key="aml_cbfb_myh11")

        with c_aml2:
            dek_nup214 = st.checkbox("DEK::NUP214 fusion", key="aml_dek_nup214")
            rbm15_mrtfa = st.checkbox("RBM15::MRTFA fusion", key="aml_rbm15_mrtfa")
            mllt3_kmt2a = st.checkbox("MLLT3::KMT2A fusion", key="aml_mllt3_kmt2a")

        with c_aml3:
            kmt2a = st.checkbox("KMT2A rearrangement (other)", key="aml_kmt2a_other")
            mecom = st.checkbox("MECOM rearrangement", key="aml_mecom")
            nup98 = st.checkbox("NUP98 rearrangement", key="aml_nup98")

        with c_aml4:
            cebpa = st.checkbox("CEBPA mutation", key="aml_cebpa_mutation")
            bzip = st.checkbox("CEBPA bZIP mutation", key="aml_cebpa_bzip")
            bcr_abl1 = st.checkbox("BCR::ABL1 fusion", key="aml_bcr_abl1")

        # ---------------------------------------------------------------------
        # Biallelic TP53
        # ---------------------------------------------------------------------
        st.markdown("#### Biallelic TP53 Mutation")
        tp1, tp2, tp3, tp4 = st.columns(4)
        with tp1:
            two_tp53 = st.checkbox("2 x TP53 mutations", key="aml_tp53_2")
        with tp2:
            one_tp53_del17p = st.checkbox("1 x TP53 + del(17p)", key="aml_tp53_del17p")
        with tp3:
            one_tp53_loh = st.checkbox("1 x TP53 + LOH", key="aml_tp53_loh")
        with tp4:
            pass

        # ---------------------------------------------------------------------
        # MDS-related Mutations (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### MDS-related Mutations")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            asxl1 = st.checkbox("ASXL1", key="aml_asxl1")
            bcor = st.checkbox("BCOR", key="aml_bcor")
            ezh2 = st.checkbox("EZH2", key="aml_ezh2")
        with col_a2:
            runx1_mds = st.checkbox("RUNX1 (MDS-related)", key="aml_runx1_mds")
            sf3b1 = st.checkbox("SF3B1", key="aml_sf3b1")
        with col_a3:
            srsf2 = st.checkbox("SRSF2", key="aml_srsf2")
            stag2 = st.checkbox("STAG2", key="aml_stag2")
        with col_a4:           
            u2af1 = st.checkbox("U2AF1", key="aml_u2af1")
            zrsr2 = st.checkbox("ZRSR2", key="aml_zrsr2")

        # ---------------------------------------------------------------------
        # MDS-related Cytogenetics (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### MDS-related Cytogenetics")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)

        with col_b1:
            complex_kary = st.checkbox("Complex karyotype", key="aml_complex_karyotype")
            del_5q = st.checkbox("del(5q)", key="aml_del_5q")
            t_5q = st.checkbox("t(5q)", key="aml_t_5q")
            add_5q = st.checkbox("add(5q)", key="aml_add_5q")
            minus7 = st.checkbox("-7", key="aml_minus7")
        with col_b2:
            del_7q = st.checkbox("del(7q)", key="aml_del_7q")
            plus8 = st.checkbox("+8", key="aml_plus8")
            del_11q = st.checkbox("del(11q)", key="aml_del_11q")
            del_12p = st.checkbox("del(12p)", key="aml_del_12p")
            t_12p = st.checkbox("t(12p)", key="aml_t_12p")
        with col_b3:
            add_12p = st.checkbox("add(12p)", key="aml_add_12p")
            minus13 = st.checkbox("-13", key="aml_minus13")
            i_17q = st.checkbox("i(17q)", key="aml_i_17q")
            minus17 = st.checkbox("-17", key="aml_minus17")
            add_17p = st.checkbox("add(17p)", key="aml_add_17p")
        with col_b4:
            del_17p = st.checkbox("del(17p)", key="aml_del_17p")
            del_20q = st.checkbox("del(20q)", key="aml_del_20q")
            idic_x_q13 = st.checkbox("idic_X_q13", key="aml_idic_x_q13")

        # ---------------------------------------------------------------------
        # AML Differentiation
        # ---------------------------------------------------------------------
        aml_diff = st.text_input(
            "AML differentiation (e.g. 'FAB M3', 'M4')",
            value="", 
            key="aml_differentiation"
        )

        # ---------------------------------------------------------------------
        # Qualifiers
        # ---------------------------------------------------------------------
        st.markdown("#### Qualifiers")
        qc1, qc2 = st.columns(2)
        with qc1:
            prev_mds_3mo = st.checkbox("Previous MDS diagnosed >3 months ago", key="aml_prev_mds_3mo")
            prev_mds_mpn_3mo = st.checkbox("Previous MDS/MPN diagnosed >3 months ago", key="aml_prev_mds_mpn_3mo")
        with qc2:
            prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="aml_prev_cytotx")
            germ_variant = st.text_input("Predisposing germline variant (if any)", value="None", key="aml_germ_variant")

    # -------------------------------------------------------------------------
    # Collect inputs into a dictionary
    # -------------------------------------------------------------------------
    manual_data = {
        "blasts_percentage": blasts,
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1": npm1,
            "RUNX1::RUNX1T1": runx1_runx1t1,
            "CBFB::MYH11": cbfb_myh11,
            "DEK::NUP214": dek_nup214,
            "RBM15::MRTFA": rbm15_mrtfa,
            "MLLT3::KMT2A": mllt3_kmt2a,
            "KMT2A": kmt2a,
            "MECOM": mecom,
            "NUP98": nup98,
            "CEBPA": cebpa,
            "bZIP": bzip,
            "BCR::ABL1": bcr_abl1
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": two_tp53,
            "1_x_TP53_mutation_del_17p": one_tp53_del17p,
            "1_x_TP53_mutation_LOH": one_tp53_loh
        },
        "MDS_related_mutation": {
            "ASXL1": asxl1,
            "BCOR": bcor,
            "EZH2": ezh2,
            "RUNX1": runx1_mds,
            "SF3B1": sf3b1,
            "SRSF2": srsf2,
            "STAG2": stag2,
            "U2AF1": u2af1,
            "ZRSR2": zrsr2
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": complex_kary,
            "del_5q": del_5q,
            "t_5q": t_5q,
            "add_5q": add_5q,
            "-7": minus7,
            "del_7q": del_7q,
            "+8": plus8,
            "del_11q": del_11q,
            "del_12p": del_12p,
            "t_12p": t_12p,
            "add_12p": add_12p,
            "-13": minus13,
            "i(17q)": i_17q,
            "-17": minus17,
            "add(17p)": add_17p,
            "del(17p)": del_17p,
            "del(20q)": del_20q,
            "idic_X_q13": idic_x_q13
        },
        "AML_differentiation": aml_diff.strip() if aml_diff.strip() else None,
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": prev_mds_3mo,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": prev_mds_mpn_3mo,
            "previous_cytotoxic_therapy": prev_cytotx,
            "predisposing_germline_variant": germ_variant.strip() if germ_variant.strip() else "None"
        }
    }

    return manual_data

def build_manual_mds_data_compact() -> dict:
    """Manual MDS Data Entry."""
    # Wrap the entire MDS data entry in one expander
    with st.expander("Manual MDS Input Area", expanded=True):
        st.markdown("### Manual MDS Data Entry")

        c1, c2, c3 = st.columns(3)
        with c1:
            blasts = st.number_input(
                "Blasts (%)", 
                min_value=0.0, max_value=100.0, value=0.0, 
                key="mds_blasts_percentage"
            )
        with c2:
            fibrotic = st.checkbox("Fibrotic marrow?", key="mds_fibrotic")
        with c3:
            hypoplasia = st.checkbox("Hypoplastic MDS?", key="mds_hypoplasia")

        dys_lineages = st.number_input(
            "Number of Dysplastic Lineages (0-3)",
            min_value=0,
            max_value=3,
            value=0,
            key="mds_dys_lineages"
        )

        st.markdown("#### Biallelic TP53 Mutation")
        ctp1, ctp2, ctp3 = st.columns(3)
        with ctp1:
            tp53_2 = st.checkbox("2 x TP53 mutations", key="mds_tp53_2")
        with ctp2:
            tp53_17p = st.checkbox("1 x TP53 + del(17p)", key="mds_tp53_del17p")
        with ctp3:
            tp53_loh = st.checkbox("1 x TP53 + LOH", key="mds_tp53_loh")

        st.markdown("#### MDS-related Mutation")
        sf3b1 = st.checkbox("SF3B1 mutation", key="mds_sf3b1")

        st.markdown("#### MDS-related Cytogenetics")
        del_5q = st.checkbox("del(5q) / isolated 5q-", key="mds_del_5q")

        st.markdown("#### Qualifiers")
        ql1, ql2 = st.columns(2)
        with ql1:
            prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="mds_prev_cytotx")
        with ql2:
            germ_variant = st.text_input("Predisposing germline variant", value="None", key="mds_germ_variant")

    return {
        "blasts_percentage": blasts,
        "fibrotic": fibrotic,
        "hypoplasia": hypoplasia,
        "number_of_dysplastic_lineages": int(dys_lineages),
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": tp53_2,
            "1_x_TP53_mutation_del_17p": tp53_17p,
            "1_x_TP53_mutation_LOH": tp53_loh
        },
        "MDS_related_mutation": {
            "SF3B1": sf3b1
        },
        "MDS_related_cytogenetics": {
            "del_5q": del_5q
        },
        "qualifiers": {
            "previous_cytotoxic_therapy": prev_cytotx,
            "predisposing_germline_variant": germ_variant.strip() if germ_variant.strip() else "None"
        }
    }

def build_manual_aml_response_data() -> dict:
    st.markdown("#### Manual AML Response Assessment (ELN 2022)")
    col1, col2 = st.columns(2)
    with col1:
        adequate_sample = st.checkbox("Adequate sample available?", key="response_adequate_sample")
        bone_marrow_blasts = st.number_input("Bone Marrow Blasts (%)", min_value=0.0, max_value=100.0, value=0.0, key="response_bone_marrow_blasts")
        blood_counts_provided = st.checkbox("Are blood counts provided?", key="response_blood_counts_provided")
    with col2:
        platelets = st.number_input("Platelet count (x10^9/L)", min_value=0.0, value=0.0, key="response_platelets")
        neutrophils = st.number_input("Neutrophil count (x10^9/L)", min_value=0.0, value=0.0, key="response_neutrophils")

    st.markdown("##### Additional Response-Related Fields")
    col3, col4 = st.columns(2)
    with col3:
        previously_cr = st.checkbox("Previously achieved CR/CRh/CRi?", key="response_previously_cr")
        blasts_decrease_50 = st.checkbox("Blasts decreased by >= 50%?", key="response_blasts_decrease_50")
    with col4:
        tnc_5_25 = st.checkbox("TNC 5-25 x10^9/L?", key="response_tnc_5_25")

    manual_response_data = {
        "AdequateSample": adequate_sample,
        "BoneMarrowBlasts": bone_marrow_blasts,
        "BloodCountsProvided": blood_counts_provided,
        "Platelets": platelets,
        "Neutrophils": neutrophils,
        "PreviouslyAchievedCR_CRh_Cri": previously_cr,
        "BlastsDecreaseBy50Percent": blasts_decrease_50,
        "TNCBetween5And25": tnc_5_25
    }
    return manual_response_data


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
    # 2. Classification Header
    ##########################################
    st.markdown(
        """
        <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
            <h3 style='color: #0f5132;'>Classification Results</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

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
    
    st.markdown("""
                <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                    <h3 style='color: #0f5132;'>Classification Results</h3>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>MDS Classification Results</h3>
    </div>
    """, unsafe_allow_html=True)

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

   
##################################
# MAIN APP
##################################
def app_main():
    from streamlit_option_menu import option_menu


    # Ensure expanders are tracked in session_state
    if "expanded_aml_section" not in st.session_state:
        st.session_state["expanded_aml_section"] = None
    if "expanded_mds_section" not in st.session_state:
        st.session_state["expanded_mds_section"] = None

    # Only show classification features if authenticated
    if st.session_state.get("authenticated", False):
        # Replace st.tabs with a horizontal menu
        selected_tab = option_menu(
            menu_title=None,
            options=["AML Diagnostics", "MDS Diagnostics"],
            default_index=0,
            orientation="horizontal"
        )
          


        # --------------------------------------------------------------
        # AML CLASSIFICATION
        # --------------------------------------------------------------
        if selected_tab == "AML Diagnostics":
            st.subheader("Acute Myeloid Leukemia (AML)")
            
            # Mode toggle checkbox
            aml_mode_toggle = st.checkbox("Free Text Mode", key="aml_mode_toggle")

            # Make sure 'aml_busy' exists in session_state
            if "aml_busy" not in st.session_state:
                st.session_state["aml_busy"] = False

            ##################################
            # MANUAL MODE
            ##################################
            if not aml_mode_toggle:
                manual_data = build_manual_aml_data()

                # Button to classify AML (Manual)
                if st.button("Classify AML (Manual)"):
                    st.session_state["aml_busy"] = True

                    # Show a neutral spinner and text
                    with st.spinner("Compiling results. Please wait..."):
                        # 1) Clear old session state
                        for key in [
                            "aml_manual_result", "aml_manual_class_review", "aml_manual_mrd_review",
                            "aml_manual_gene_review", "aml_manual_additional_comments",
                            "aml_ai_result", "aml_ai_class_review", "aml_ai_mrd_review",
                            "aml_ai_gene_review", "aml_ai_additional_comments"
                        ]:
                            st.session_state.pop(key, None)

                        # 2) Do the classification
                        classification_who, who_derivation = classify_AML_WHO2022(manual_data)
                        classification_icc, icc_derivation = classify_AML_ICC2022(manual_data)

                        # 3) Store results
                        st.session_state["aml_manual_result"] = {
                            "parsed_data": manual_data,
                            "who_class": classification_who,
                            "who_derivation": who_derivation,
                            "icc_class": classification_icc,
                            "icc_derivation": icc_derivation,
                        }

                        # 4) Auto-generate classification review
                        classification_dict = {
                            "WHO 2022": {
                                "Classification": classification_who,
                                "Derivation": who_derivation
                            },
                            "ICC 2022": {
                                "Classification": classification_icc,
                                "Derivation": icc_derivation
                            }
                        }
                        class_review = get_gpt4_review_aml_classification(classification_dict, manual_data)
                        st.session_state["aml_manual_class_review"] = class_review
                        st.session_state["expanded_aml_section"] = "classification"

                    st.session_state["aml_busy"] = False

                # Always display classification if it exists
                if "aml_manual_result" in st.session_state:
                    res = st.session_state["aml_manual_result"]

                    display_aml_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="manual"
                    )

                    # Classification Review
                    if "aml_manual_class_review" in st.session_state:
                        with st.expander(
                            "View Classification Review",
                            expanded=(st.session_state["expanded_aml_section"] == "classification")
                        ):
                            st.markdown(st.session_state["aml_manual_class_review"])

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

                    ##########################################
                    # Buttons for MRD, Gene Review, Comments
                    ##########################################
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        if st.button("🧪 MRD Review"):
                            st.session_state["aml_busy"] = True
                            with st.spinner("Compiling results. Please wait..."):
                                mrd_review = get_gpt4_review_aml_mrd(classification_dict, res["parsed_data"])
                                st.session_state["aml_manual_mrd_review"] = mrd_review
                                st.session_state["expanded_aml_section"] = "mrd_review"
                            st.session_state["aml_busy"] = False

                    with col2:
                        if st.button("🧬 Gene Review"):
                            st.session_state["aml_busy"] = True
                            with st.spinner("Compiling results. Please wait..."):
                                gene_review = get_gpt4_review_aml_genes(classification_dict, res["parsed_data"])
                                st.session_state["aml_manual_gene_review"] = gene_review
                                st.session_state["expanded_aml_section"] = "gene_review"
                            st.session_state["aml_busy"] = False

                    with col3:
                        if st.button("📄 Further Comments"):
                            st.session_state["aml_busy"] = True
                            with st.spinner("Compiling results. Please wait..."):
                                add_comments = get_gpt4_review_aml_additional_comments(classification_dict, res["parsed_data"])
                                st.session_state["aml_manual_additional_comments"] = add_comments
                                st.session_state["expanded_aml_section"] = "comments"
                            st.session_state["aml_busy"] = False

                    with col4:
                        pass
                    with col5:
                        if "show_pdf_form" not in st.session_state:
                            st.session_state.show_pdf_form = False

                        if st.button("Download Report 📄⬇️"):
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
                                    # Build the HTML that creates a hidden anchor and auto-clicks it.
                                    download_html = f'''
                                        <a id="pdf_download" href="data:application/pdf;base64,{pdf_base64}" download="diagnostic_report.pdf"></a>
                                        <script>
                                            // Wait a short moment to ensure the anchor is rendered, then click it.
                                            setTimeout(function() {{
                                                document.getElementById("pdf_download").click();
                                            }}, 100);
                                        </script>
                                    '''
                                    # Use st.components.v1.html to render the HTML/JS so it will execute.
                                    components.html(download_html, height=0)
                                    st.session_state.show_pdf_form = False



                    ##########################################
                    # Display reviews, if any
                    ##########################################
                    # Gene Analysis
                    if "aml_manual_gene_review" in st.session_state:
                        with st.expander(
                            "### Gene Analysis",
                            expanded=(st.session_state["expanded_aml_section"] == "gene_review")
                        ):
                            st.markdown(st.session_state["aml_manual_gene_review"])

                    # MRD
                    if "aml_manual_mrd_review" in st.session_state:
                        with st.expander(
                            "### MRD Review",
                            expanded=(st.session_state["expanded_aml_section"] == "mrd_review")
                        ):
                            st.markdown(st.session_state["aml_manual_mrd_review"])

                    # Additional Comments
                    if "aml_manual_additional_comments" in st.session_state:
                        with st.expander(
                            "### Additional Comments",
                            expanded=(st.session_state["expanded_aml_section"] == "comments")
                        ):
                            st.markdown(st.session_state["aml_manual_additional_comments"])


            ########################
            # FREE TEXT MODE
            ########################
            else:
                # Wrap input fields in an expander, but no button here.
                with st.expander("Free Text Input Area", expanded=True):
                    st.markdown("**Free Text Mode:** Paste your free-text genetics reports and other findings.")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Blasts % (Override)", placeholder="25", key="blasts_override")
                    with col2:
                        st.text_input("AML Differentiation", placeholder="FAB M3", key="diff_override")

                    st.text_input("Morphology/Clinical Info", placeholder="e.g. Dysplasia observed...", key="morph_input")
                    st.text_area("Genetics Report:", height=100, key="genetics_report")
                    st.text_area("Cytogenetics Report:", height=100, key="cytogenetics_report")

                # --- Button *outside* the expander ---
                if st.button("Parse & Classify AML"):
                    # Clear previous AML session state
                    for key in [
                        "aml_manual_result", "aml_manual_class_review", "aml_manual_mrd_review",
                        "aml_manual_gene_review", "aml_manual_additional_comments",
                        "aml_ai_result", "aml_ai_class_review", "aml_ai_mrd_review",
                        "aml_ai_gene_review", "aml_ai_additional_comments"
                    ]:
                        st.session_state.pop(key, None)

                    # Retrieve all text inputs from session_state
                    blasts_override = st.session_state.get("blasts_override", "")
                    diff_override = st.session_state.get("diff_override", "")
                    morph_input = st.session_state.get("morph_input", "")
                    genetics_report = st.session_state.get("genetics_report", "")
                    cytogenetics_report = st.session_state.get("cytogenetics_report", "")

                    # Combine genetics + cytogenetics (if needed)
                    combined = f"{genetics_report}\n\n{cytogenetics_report}"

                    # Create a record of the user input (for reference or passing to a function)
                    free_text_input = f"""
                    Blasts Override: {blasts_override}
                    AML Differentiation: {diff_override}
                    Morphology / Clinical Info: {morph_input}
                    Genetics Report:
                    {genetics_report}

                    Cytogenetics Report:
                    {cytogenetics_report}
                    """.strip()

                    if combined.strip():
                        with st.spinner("Parsing & classifying ..."):
                            # Example parse function
                            parsed_data = parse_genetics_report_aml(combined)

                            # Merge overrides
                            if blasts_override.strip():
                                try:
                                    parsed_data["blasts_percentage"] = float(blasts_override.strip())
                                except ValueError:
                                    st.warning("Invalid blasts override")
                            if diff_override.strip():
                                parsed_data["AML_differentiation"] = diff_override.strip()
                            if morph_input.strip():
                                parsed_data["morphology_clinical"] = morph_input.strip()

                            who_class, who_deriv = classify_AML_WHO2022(parsed_data)
                            icc_class, icc_deriv = classify_AML_ICC2022(parsed_data)

                            st.session_state["aml_ai_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                "free_text_input": free_text_input
                            }

                            # Auto-generate classification review
                            classification_dict = {
                                "WHO 2022": {
                                    "Classification": who_class,
                                    "Derivation": who_deriv
                                },
                                "ICC 2022": {
                                    "Classification": icc_class,
                                    "Derivation": icc_deriv
                                }
                            }
                            class_review = get_gpt4_review_aml_classification(
                                classification_dict,
                                parsed_data,
                                free_text_input=free_text_input
                            )
                            st.session_state["aml_ai_class_review"] = class_review
                            st.session_state["expanded_aml_section"] = "classification"

                    else:
                        st.error("No AML data provided.")

                # --- Display classification results if any ---
                if "aml_ai_result" in st.session_state:
                    res = st.session_state["aml_ai_result"]
                    display_aml_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="ai",
                        show_parsed_fields=True
                    )

                    # Classification
                    if "aml_ai_class_review" in st.session_state:
                        with st.expander(
                            "### Classification Review",
                            expanded=(st.session_state["expanded_aml_section"] == "classification")
                        ):
                            st.markdown(st.session_state["aml_ai_class_review"])

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
                    user_free_text = res.get("free_text_input", "")

                    col_a, col_b, col_c, col_d, col_e = st.columns(5)

                    with col_a:
                        if st.button("🧪 MRD Review"):
                            mrd_rev = get_gpt4_review_aml_mrd(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=user_free_text
                            )
                            st.session_state["aml_ai_mrd_review"] = mrd_rev
                            st.session_state["expanded_aml_section"] = "mrd_review"

                    with col_b:
                        if st.button("🧬 Gene Review"):
                            gene_rev = get_gpt4_review_aml_genes(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=user_free_text
                            )
                            st.session_state["aml_ai_gene_review"] = gene_rev
                            st.session_state["expanded_aml_section"] = "gene_review"

                    with col_c:
                        if st.button("📄 Further Comments"):
                            add_comments = get_gpt4_review_aml_additional_comments(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=user_free_text
                            )
                            st.session_state["aml_ai_additional_comments"] = add_comments
                            st.session_state["expanded_aml_section"] = "comments"

                    with col_d:
                        pass

                    with col_e:
                        # Ensure the session state flag is initialized.
                        if "show_pdf_form" not in st.session_state:
                            st.session_state.show_pdf_form = False

                        # Create the download button.
                        if st.button("Download Report 📄⬇️"):
                            st.session_state.show_pdf_form = True

                        # Create a placeholder container for the form.
                        form_placeholder = st.empty()

                        # If the flag is set, display the form in the placeholder.
                        if st.session_state.show_pdf_form:
                            with form_placeholder.form(key="pdf_info_form"):
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
                                    st.success("Your beautiful PDF report is ready for download!")
                                    # Clear the form by emptying the placeholder and resetting the flag.
                                    st.session_state.show_pdf_form = False
                                    form_placeholder.empty()







                    # Gene Analysis
                    if "aml_ai_gene_review" in st.session_state:
                        with st.expander(
                            "### AI Gene Analysis",
                            expanded=(st.session_state["expanded_aml_section"] == "gene_review")
                        ):
                            st.markdown(st.session_state["aml_ai_gene_review"])

                    # MRD
                    if "aml_ai_mrd_review" in st.session_state:
                        with st.expander(
                            "### AI MRD Review",
                            expanded=(st.session_state["expanded_aml_section"] == "mrd_review")
                        ):
                            st.markdown(st.session_state["aml_ai_mrd_review"])

                    # Additional Comments
                    if "aml_ai_additional_comments" in st.session_state:
                        with st.expander(
                            "### AI Additional Comments",
                            expanded=(st.session_state["expanded_aml_section"] == "comments")
                        ):
                            st.markdown(st.session_state["aml_ai_additional_comments"])

        # --------------------------------------------------------------
        # MDS CLASSIFICATION
        # --------------------------------------------------------------
        elif selected_tab == "MDS Diagnostics":
            st.subheader("Myelodysplastic Syndromes (MDS)")
            mds_mode_toggle = st.checkbox("Free Text Mode", key="mds_mode_toggle")

            # --------------- MDS Manual ---------------
            if not mds_mode_toggle:

                manual_data = build_manual_mds_data_compact()

                if st.button("Classify MDS (Manual)"):
                    who_class, who_deriv = classify_MDS_WHO2022(manual_data)
                    icc_class, icc_deriv = classify_MDS_ICC2022(manual_data)

                    st.session_state["mds_manual_result"] = {
                        "parsed_data": manual_data,
                        "who_class": who_class,
                        "who_derivation": who_deriv,
                        "icc_class": icc_class,
                        "icc_derivation": icc_deriv
                    }

                    classification_dict = {
                        "WHO 2022": {
                            "Classification": who_class,
                            "Derivation": who_deriv
                        },
                        "ICC 2022": {
                            "Classification": icc_class,
                            "Derivation": icc_deriv
                        }
                    }
                    class_rev = get_gpt4_review_mds_classification(
                        classification_dict,
                        manual_data
                    )
                    st.session_state["mds_manual_class_review"] = class_rev
                    st.session_state["expanded_mds_section"] = "classification"

                if "mds_manual_result" in st.session_state:
                    res = st.session_state["mds_manual_result"]
                    display_mds_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="manual"
                    )

                    if "mds_manual_class_review" in st.session_state:
                        with st.expander(
                            "### Classification Review",
                            expanded=(st.session_state["expanded_mds_section"] == "classification")
                        ):
                            st.markdown(st.session_state["mds_manual_class_review"])

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

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🧬 Gene Review"):
                            gene_rev = get_gpt4_review_mds_genes(
                                classification_dict,
                                res["parsed_data"]
                            )
                            st.session_state["mds_manual_gene_review"] = gene_rev
                            st.session_state["expanded_mds_section"] = "gene_review"

                    with col2:
                        if st.button("📄 Further Comments (MDS)"):
                            add_comments = get_gpt4_review_mds_additional_comments(
                                classification_dict,
                                res["parsed_data"]
                            )
                            st.session_state["mds_manual_additional_comments"] = add_comments
                            st.session_state["expanded_mds_section"] = "comments"

                    if "mds_manual_additional_comments" in st.session_state:
                        with st.expander(
                            "### Additional Comments",
                            expanded=(st.session_state["expanded_mds_section"] == "comments")
                        ):
                            st.markdown(st.session_state["mds_manual_additional_comments"])

                    if "mds_manual_gene_review" in st.session_state:
                        with st.expander(
                            "### MDS Gene Analysis",
                            expanded=(st.session_state["expanded_mds_section"] == "gene_review")
                        ):
                            st.markdown(st.session_state["mds_manual_gene_review"])


            # --------------- MDS Free Text Mode ---------------
            else:
                # Put all free-text fields into an expander
                with st.expander("MDS Free Text Input Area", expanded=True):
                    st.markdown("Paste your free-text MDS genetics/cytogenetics data below:")

                    st.text_input("Blasts (%) Override", 
                                placeholder="e.g. 8", 
                                key="mds_blasts_input")

                    st.text_area("Genetics (MDS)", 
                                height=100, 
                                key="mds_genetics_report")

                    st.text_area("Cytogenetics (MDS)", 
                                height=100, 
                                key="mds_cytogenetics_report")

                # Button to parse & classify MDS (outside the expander!)
                if st.button("Parse & Classify MDS"):
                    # Retrieve input values from session_state
                    blasts_input = st.session_state.get("mds_blasts_input", "")
                    genetics_report = st.session_state.get("mds_genetics_report", "")
                    cytogenetics_report = st.session_state.get("mds_cytogenetics_report", "")

                    combined = f"{genetics_report}\n\n{cytogenetics_report}"
                    if combined.strip():
                        with st.spinner("Parsing & classifying MDS..."):
                            parsed = parse_genetics_report_mds(combined)

                            # Blasts override
                            if blasts_input.strip():
                                try:
                                    parsed["blasts_percentage"] = float(blasts_input.strip())
                                except ValueError:
                                    st.warning("Invalid blasts override")

                            who_class, who_deriv = classify_MDS_WHO2022(parsed)
                            icc_class, icc_deriv = classify_MDS_ICC2022(parsed)

                            st.session_state["mds_ai_result"] = {
                                "parsed_data": parsed,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv
                            }

                            # Optionally get GPT-4 classification review
                            classification_dict = {
                                "WHO 2022": {
                                    "Classification": who_class,
                                    "Derivation": who_deriv
                                },
                                "ICC 2022": {
                                    "Classification": icc_class,
                                    "Derivation": icc_deriv
                                }
                            }
                            class_rev = get_gpt4_review_mds_classification(classification_dict, parsed)
                            st.session_state["mds_ai_class_review"] = class_rev
                            st.session_state["expanded_mds_section"] = "classification"
                    else:
                        st.error("Please provide MDS genetics/cytogenetics data.")

                # --- Display classification results if any ---
                if "mds_ai_result" in st.session_state:
                    res = st.session_state["mds_ai_result"]
                    display_mds_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="ai"
                    )

                    # Classification Review
                    if "mds_ai_class_review" in st.session_state:
                        with st.expander(
                            "### Classification Review",
                            expanded=(st.session_state["expanded_mds_section"] == "classification")
                        ):
                            st.markdown(st.session_state["mds_ai_class_review"])

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

                    col_f, col_g = st.columns(2)
                    with col_f:
                        if st.button("🧬 Gene Review"):
                            gene_rev = get_gpt4_review_mds_genes(
                                classification_dict,
                                res["parsed_data"]
                            )
                            st.session_state["mds_ai_gene_review"] = gene_rev
                            st.session_state["expanded_mds_section"] = "gene_review"

                    with col_g:
                        if st.button("📄 Further Comments"):
                            add_comments = get_gpt4_review_mds_additional_comments(
                                classification_dict,
                                res["parsed_data"]
                            )
                            st.session_state["mds_ai_additional_comments"] = add_comments
                            st.session_state["expanded_mds_section"] = "comments"

                    # Additional Comments
                    if "mds_ai_additional_comments" in st.session_state:
                        with st.expander(
                            "### Additional Comments",
                            expanded=(st.session_state["expanded_mds_section"] == "comments")
                        ):
                            st.markdown(st.session_state["mds_ai_additional_comments"])

                    # Gene Review
                    if "mds_ai_gene_review" in st.session_state:
                        with st.expander(
                            "### MDS Gene Analysis",
                            expanded=(st.session_state["expanded_mds_section"] == "gene_review")
                        ):
                            st.markdown(st.session_state["mds_ai_gene_review"])


    else:
        st.info("🔒 **Log in** to use the classification features.")

def main():
    app_main()

if __name__ == "__main__":
    main()




