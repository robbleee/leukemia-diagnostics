import re
import datetime
import streamlit as st
from fpdf import FPDF

##################################
# PDF CONVERTER HELPERS
##################################
def clean_text(text: str) -> str:
    # Replace the Unicode heavy arrow (➔) with a simple arrow.
    text = text.replace('\u2794', '->')
    # Remove common markdown tokens
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'__(.*?)__', r'\1', text)       # bold alternate
    text = re.sub(r'\*(.*?)\*', r'\1', text)       # italic
    text = re.sub(r'_(.*?)_', r'\1', text)         # italic alternate
    text = re.sub(r'`{1,3}', '', text)             # inline code
    return text.strip()

def write_line_with_keywords(pdf: FPDF, line: str, line_height: float = 8):
    """
    Writes a line to the PDF, highlighting specific keywords in bold.
    (Used only if no subheading pattern is matched.)
    """
    bold_keywords = [
        "Classification Review",
        "Sample Quality:",
        "Derivation Steps:",
        "Classification:",
        "Other Genes"
    ]
    occurrences = []
    for kw in bold_keywords:
        start = line.find(kw)
        if start != -1:
            occurrences.append((start, kw))
    occurrences.sort(key=lambda x: x[0])
    
    current = 0
    if not occurrences:
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, line, align="L")
        return
    
    pdf.set_font("Arial", "", 10)
    # Build up the line in segments
    for start, kw in occurrences:
        if start > current:
            pdf.write(line_height, line[current:start])
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, kw)
        pdf.set_font("Arial", "", 10)
        current = start + len(kw)
    # If there's any text after the last keyword
    if current < len(line):
        pdf.write(line_height, line[current:])
    pdf.ln(line_height)

def write_line_with_subheadings(pdf: FPDF, line: str, line_height: float = 8):
    """
    Simplified function that handles subheadings vs. normal text.
    - If the entire line matches a known subheading or is a short line ending with a colon,
      print in bold as a single multi_cell line.
    - If there's an early colon (<= 30 chars in), treat that portion as subheading, rest normal.
    - Otherwise, just call multi_cell or fallback to keyword highlighting.
    """
    predefined_subheadings = [
        "Classification Review",
        "MRD Review",
        "Gene Review",
        "Additional Comments",
        "References"
    ]
    stripped_line = line.strip()
    
    # Check if line is an exact (case-insensitive) match to a known subheading
    for sub in predefined_subheadings:
        if stripped_line.lower() == sub.lower():
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(0, line_height, line, align="L")
            return
    
    # If line ends with ':' and is short (≤ 40 chars), treat as subheading
    if stripped_line.endswith(':') and len(stripped_line) <= 40:
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(0, line_height, line, align="L")
        return
    
    # If there's a colon in the first ~30 chars, split subheading vs. normal text
    colon_index = stripped_line.find(':')
    if 0 <= colon_index <= 30:
        subheading = stripped_line[:colon_index + 1].strip()
        rest = stripped_line[colon_index + 1:].strip()
        
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, subheading + " ")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, rest, align="L")
        return
    
    # Otherwise, fallback to our keyword-highlighting approach
    # (which also calls multi_cell if no keywords found)
    write_line_with_keywords(pdf, stripped_line, line_height)

def output_review_text(pdf: FPDF, review_text: str, section: str):
    """
    Splits review_text into lines and prints each line with subheading logic.
    Skips certain duplicate headings if they appear in the text.
    """
    DUPLICATE_HEADINGS = {
        "MRD Review": ["MRD Strategy", "MRD Review", "MRD Review:"],
        "Gene Review": ["Genetics Review", "Gene Review", "Genetics Review:"],
        "Additional Comments": ["Additional Considerations", "Additional Considerations:"]
    }
    skip_list = DUPLICATE_HEADINGS.get(section, [])
    lines = review_text.splitlines()
    
    for line in lines:
        cleaned_line = clean_text(line)
        if not cleaned_line:
            pdf.ln(4)
            continue
        
        # Skip lines that are basically duplicate headings
        if any(cleaned_line.lower() == x.lower() for x in skip_list):
            continue
        
        write_line_with_subheadings(pdf, cleaned_line)
        pdf.ln(2)  # Extra spacing after each line for readability

class PDF(FPDF):
    """
    Custom FPDF class to add a header and footer to the first/any pages.
    """
    def header(self):
        if self.page_no() == 1:
            # Main title
            self.set_font("Arial", "B", 14)
            self.set_text_color(0, 70, 140)
            self.cell(0, 8, "Diagnostic Report", ln=1, align="C")
            # Date
            self.set_font("Arial", "", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, datetime.datetime.now().strftime("%B %d, %Y"), ln=1, align="C")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def add_section_title(pdf: PDF, title: str):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 70, 140)
    pdf.cell(0, 10, clean_text(title), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

def add_classification_section(pdf: FPDF, classification_data: dict):
    """
    Adds WHO & ICC classification content with multi_cell for step text.
    """
    line_height = 8
    
    # WHO 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "WHO 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['WHO']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    
    for i, step in enumerate(classification_data["WHO"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(4)

    # ICC 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "ICC 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['ICC']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    
    for i, step in enumerate(classification_data["ICC"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(6)

def add_risk_section(pdf: FPDF, risk_data: dict):
    add_section_title(pdf, "ELN 2022 Risk Classification")
    pdf.set_font("Arial", "", 10)
    
    write_line_with_subheadings(pdf, f"Risk Category: {risk_data.get('eln_class', 'N/A')}", 8)
    pdf.ln(2)
    write_line_with_subheadings(pdf, "Derivation Steps:", 8)
    
    for i, step in enumerate(risk_data.get("eln_derivation", []), start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 8, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(4)

def add_diagnostic_section(pdf: FPDF, diag_type: str):
    """
    Detect whether we have manual or AI results for the given diag_type.
    Then output classification + review text sections.
    """
    manual_key = diag_type.lower() + "_manual_result"
    ai_key = diag_type.lower() + "_ai_result"
    
    if manual_key in st.session_state:
        data = st.session_state[manual_key]
    elif ai_key in st.session_state:
        data = st.session_state[ai_key]
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
        ("Classification Review", diag_type.lower() + "_class_review"),
        ("MRD Review", diag_type.lower() + "_mrd_review"),
        ("Gene Review", diag_type.lower() + "_gene_review"),
        ("Additional Comments", diag_type.lower() + "_additional_comments")
    ]
    for section_name, key in review_sections:
        if key in st.session_state:
            add_section_title(pdf, section_name)
            output_review_text(pdf, st.session_state[key], section_name)
            pdf.ln(4)

def _is_positive(value):
    """
    Returns True if the value is considered "positive":
      - boolean True,
      - non-zero numeric,
      - non-empty string,
      - a dict that has at least one positive sub-value
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return (value != 0)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_is_positive(v) for v in value.values())
    return False

def output_positive_findings(pdf: FPDF, data: dict, indent: int = 0):
    """
    Recursively prints only "positive" fields from the manual input dictionary.
    Skips classification keys: 'who_class', 'icc_class', 'eln_class'.
    """
    SKIP_FIELDS = {"who_class", "icc_class", "eln_class"}

    for key, value in data.items():
        if key in SKIP_FIELDS:
            continue

        if isinstance(value, bool) and value:
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, (int, float)) and value:
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, str) and value.strip():
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, dict):
            # Filter out skip fields and see if anything remains
            filtered_subdict = {k: v for k, v in value.items() if k not in SKIP_FIELDS}
            if any(_is_positive(subv) for subv in filtered_subdict.values()):
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 8, " " * indent + f"{key}:", ln=1)
                output_positive_findings(pdf, filtered_subdict, indent=indent + 4)

##################################
# create_base_pdf
##################################
def create_base_pdf(user_comments: str = None) -> bytes:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # AML diagnostics
    aml_result = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    if aml_result:
        add_diagnostic_section(pdf, "AML")
        if aml_result.get("eln_class"):
            risk_data = {
                "eln_class": aml_result.get("eln_class", "N/A"),
                "eln_derivation": aml_result.get("eln_derivation", [])
            }
            add_risk_section(pdf, risk_data)

    # MDS diagnostics
    mds_result = st.session_state.get("mds_manual_result") or st.session_state.get("mds_ai_result")
    if mds_result:
        add_section_title(pdf, "MDS Diagnostics")
        add_diagnostic_section(pdf, "MDS")

    # Manual positive findings (manual mode only)
    if "aml_manual_result" in st.session_state:
        add_section_title(pdf, "Manual Positive Findings")
        output_positive_findings(pdf, st.session_state["aml_manual_result"])
        pdf.ln(4)

    # Optional user comments
    if user_comments:
        add_section_title(pdf, "User Comments")
        output_review_text(pdf, user_comments, "User Comments")
        pdf.ln(4)

    # Free text details
    aml_data = st.session_state.get("aml_ai_result") or st.session_state.get("aml_manual_result")
    if aml_data and aml_data.get("free_text_input"):
        add_section_title(pdf, "Molecular, Cytogenetic, Differentiation Clinical Details")
        output_review_text(pdf, aml_data["free_text_input"], "Molecular Details")
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin1")
