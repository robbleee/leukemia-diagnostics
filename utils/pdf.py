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
    text = re.sub(r'__(.*?)__', r'\1', text)        # bold alternate
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # italic
    text = re.sub(r'_(.*?)_', r'\1', text)            # italic alternate
    text = re.sub(r'`{1,3}', '', text)                # inline code
    return text.strip()

def write_line_with_keywords(pdf: FPDF, line: str, line_height: float = 8):
    """
    Writes a line to the PDF, highlighting specific keywords in bold.
    (This is used as a fallback if no subheading pattern is found.)
    """
    bold_keywords = ["Classification Review", "Sample Quality:", "Derivation Steps:", "Classification:", "Other Genes"]
    occurrences = []
    for kw in bold_keywords:
        start = line.find(kw)
        if start != -1:
            occurrences.append((start, kw))
    occurrences.sort(key=lambda x: x[0])
    
    current = 0
    if not occurrences:
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line)
        pdf.ln(line_height)
        return
    
    for start, kw in occurrences:
        if start > current:
            pdf.set_font("Arial", "", 10)
            pdf.write(line_height, line[current:start])
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, kw)
        current = start + len(kw)
    if current < len(line):
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line[current:])
    pdf.ln(line_height)

def write_line_with_subheadings(pdf: FPDF, line: str, line_height: float = 8):
    """
    Enhanced function that prints subheadings in bold.
    It uses several heuristics:
      - If the entire line (after stripping) matches a predefined subheading (case-insensitive),
        it is printed in bold.
      - If the line ends with a colon and is short (≤40 characters), it is treated as a subheading.
      - If the line contains a colon and the part before the colon is short (≤30 characters),
        that part (including the colon) is printed in bold and the rest normally.
      - Otherwise, it falls back to the keyword-highlighting function.
    """
    predefined_subheadings = [
        "Classification Review",
        "MRD Review",
        "Gene Review",
        "Additional Comments",
        "References"
    ]
    stripped_line = line.strip()
    # Check for an exact match with a predefined subheading.
    for sub in predefined_subheadings:
        if stripped_line.lower() == sub.lower():
            pdf.set_font("Arial", "B", 10)
            pdf.write(line_height, line)
            pdf.ln(line_height)
            return
    
    # If the line ends with a colon and is short, treat it as a subheading.
    if stripped_line.endswith(':') and len(stripped_line) <= 40:
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, line)
        pdf.ln(line_height)
        return
    
    # If the line contains a colon and the text before the colon is short, split it.
    colon_index = line.find(':')
    if colon_index != -1 and colon_index <= 30:
        subheading = line[:colon_index+1]
        rest = line[colon_index+1:]
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, subheading)
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, rest)
        pdf.ln(line_height)
        return

    # Fallback: use the original keyword highlighting.
    write_line_with_keywords(pdf, line, line_height)

def output_review_text(pdf: FPDF, review_text: str, section: str):
    """
    Splits review_text into lines and outputs each line using enhanced subheading formatting.
    """
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
        if dup_list and any(cleaned_line.lower() == dup.lower() for dup in dup_list):
            continue
        write_line_with_subheadings(pdf, cleaned_line)

def output_positive_findings(pdf: FPDF, data: dict, indent: int = 0):
    """
    Recursively iterates over the manual input dictionary and prints only the fields that are "positive"
    (e.g., boolean True, non-zero numbers, non-empty strings).
    """
    for key, value in data.items():
        # Skip keys that are not manual inputs (if needed, you can adjust here)
        if isinstance(value, bool):
            if value:
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, (int, float)):
            if value:  # if non-zero
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, str):
            if value.strip():
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 8, " " * indent + f"{key}: {value}", ln=1)
        elif isinstance(value, dict):
            # Check if any nested value is "positive"
            if any(v for v in value.values()):
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 8, " " * indent + f"{key}:", ln=1)
                output_positive_findings(pdf, value, indent=indent+4)
        # For lists or other types, you can add handling if needed.

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

def add_section_title(pdf: PDF, title: str):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 70, 140)
    pdf.cell(0, 10, clean_text(title), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

def add_classification_section(pdf: PDF, classification_data: dict):
    line_height = 8
    # WHO 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "WHO 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['WHO']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(classification_data["WHO"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(4)
    # ICC 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "ICC 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['ICC']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(classification_data["ICC"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(6)

def add_risk_section(pdf: PDF, risk_data: dict):
    add_section_title(pdf, "ELN 2022 Risk Classification")
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Risk Category: {risk_data.get('eln_class', 'N/A')}", 8)
    pdf.ln(2)
    write_line_with_subheadings(pdf, "Derivation Steps:", 8)
    for i, step in enumerate(risk_data.get("eln_derivation", []), start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 8, f"  {i}. {clean_text(step)}")
    pdf.ln(4)

def add_diagnostic_section(pdf: PDF, diag_type: str):
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

##################################
# Updated create_base_pdf function:
##################################
def create_base_pdf(user_comments: str = None) -> bytes:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Add AML diagnostics.
    aml_result = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    if aml_result:
        add_diagnostic_section(pdf, "AML")
        if aml_result.get("eln_class"):
            risk_data = {
                "eln_class": aml_result.get("eln_class", "N/A"),
                "eln_derivation": aml_result.get("eln_derivation", [])
            }
            add_risk_section(pdf, risk_data)

    # Append MDS diagnostics (if any) on the same pages.
    mds_result = st.session_state.get("mds_manual_result") or st.session_state.get("mds_ai_result")
    if mds_result:
        add_section_title(pdf, "MDS Diagnostics")
        add_diagnostic_section(pdf, "MDS")
    
    # Append Manual Positive Findings (if manual mode was used).
    if "aml_manual_result" in st.session_state:
        add_section_title(pdf, "Manual Positive Findings")
        output_positive_findings(pdf, st.session_state["aml_manual_result"])
        pdf.ln(4)
    
    # Append User Comments if provided.
    if user_comments:
        add_section_title(pdf, "User Comments")
        output_review_text(pdf, user_comments, "User Comments")
        pdf.ln(4)
    
    # Append any clinical free-text details.
    aml_data = st.session_state.get("aml_ai_result") or st.session_state.get("aml_manual_result")
    if aml_data and aml_data.get("free_text_input"):
        add_section_title(pdf, "Molecular, Cytogenetic, Differentiation Clinical Details")
        output_review_text(pdf, aml_data["free_text_input"], "Molecular Details")
        pdf.ln(4)

    return pdf.output(dest="S").encode("latin1")
