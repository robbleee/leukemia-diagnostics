import re
import datetime
import streamlit as st
from fpdf import FPDF
from classifiers.aml_risk_classifier import eln2024_non_intensive_risk, eln2022_intensive_risk
from parsers.final_review_parser import generate_final_overview

##################################
# PDF CONVERTER HELPERS
##################################
def safe_text(value):
    """
    Ensures any value is properly cleaned and safe for inclusion in the PDF.
    Handles different data types and ensures all text is Latin-1 compatible.
    """
    if value is None:
        return "N/A"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return clean_text(value)
    elif isinstance(value, (list, tuple)):
        return ", ".join(safe_text(item) for item in value)
    elif isinstance(value, dict):
        return str({k: safe_text(v) for k, v in value.items()})
    else:
        return clean_text(str(value))

def clean_text(text: str) -> str:
    # Replace the Unicode heavy arrow (➔) with a simple arrow.
    text = text.replace('\u2794', '->')
    # Replace en-dash with simple dash to be Latin-1 safe.
    text = text.replace('\u2013', '-')
    # Replace em-dash with simple dash
    text = text.replace('\u2014', '-')
    # Replace other common Unicode characters
    text = text.replace('\u2018', "'")  # Left single quote
    text = text.replace('\u2019', "'")  # Right single quote
    text = text.replace('\u201c', '"')  # Left double quote
    text = text.replace('\u201d', '"')  # Right double quote
    text = text.replace('\u2026', '...') # Ellipsis
    text = text.replace('\u00a0', ' ')  # Non-breaking space
    # Remove common markdown tokens.
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'__(.*?)__', r'\1', text)        # bold alternate
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # italic
    text = re.sub(r'_(.*?)_', r'\1', text)            # italic alternate
    text = re.sub(r'`{1,3}', '', text)                # inline code
    
    # Final check - replace any remaining non-Latin1 characters
    latin1_safe = ''
    for char in text:
        if ord(char) < 256:  # Latin-1 range
            latin1_safe += char
        else:
            latin1_safe += '?'  # Replace with question mark
            
    return latin1_safe.strip()

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
    for start, kw in occurrences:
        if start > current:
            pdf.write(line_height, line[current:start])
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, kw)
        pdf.set_font("Arial", "", 10)
        current = start + len(kw)
    if current < len(line):
        pdf.write(line_height, line[current:])
    pdf.ln(line_height)

def write_line_with_subheadings(pdf: FPDF, line: str, line_height: float = 8):
    """
    Handles subheadings vs. normal text.
    """
    predefined_subheadings = [
        "Classification Review",
        "MRD Review",
        "Gene Review",
        "Additional Comments",
        "References"
    ]
    stripped_line = line.strip()
    
    for sub in predefined_subheadings:
        if stripped_line.lower() == sub.lower():
            pdf.set_font("Arial", "B", 10)
            pdf.multi_cell(0, line_height, line, align="L")
            return
    
    if stripped_line.endswith(':') and len(stripped_line) <= 40:
        pdf.set_font("Arial", "B", 10)
        pdf.multi_cell(0, line_height, line, align="L")
        return
    
    colon_index = stripped_line.find(':')
    if 0 <= colon_index <= 30:
        subheading = stripped_line[:colon_index+1].strip()
        rest = stripped_line[colon_index+1:].strip()
        
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, subheading + " ")
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, rest, align="L")
        return
    
    write_line_with_keywords(pdf, stripped_line, line_height)

def output_review_text(pdf: FPDF, review_text: str, section: str):
    """
    Splits review_text into lines and prints each line with subheading logic.
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
        if any(cleaned_line.lower() == x.lower() for x in skip_list):
            continue
        write_line_with_subheadings(pdf, cleaned_line)
        pdf.ln(2)

def _is_positive(value):
    """
    Returns True if the value is considered "positive".
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(_is_positive(v) for v in value.values())
    return False

def output_positive_findings(pdf: FPDF, data: dict, indent: int = 0):
    """
    Recursively prints only "positive" fields from the manual input dictionary.
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
            filtered_subdict = {k: v for k, v in value.items() if k not in SKIP_FIELDS}
            if any(_is_positive(subv) for subv in filtered_subdict.values()):
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 8, " " * indent + f"{key}:", ln=1)
                output_positive_findings(pdf, filtered_subdict, indent=indent + 4)

class PDF(FPDF):
    """
    A custom PDF class that automatically sanitizes all text inputs
    to ensure they are Latin-1 compatible.
    """
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", "B", 14)
            self.set_text_color(0, 150, 136)
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

    # Override text methods to automatically sanitize text
    def cell(self, w=0, h=0, txt='', border=0, ln=0, align='', fill=False, link=''):
        # Sanitize text before passing to parent method
        sanitized_txt = safe_text(txt) if txt else ''
        return super().cell(w, h, sanitized_txt, border, ln, align, fill, link)
    
    def multi_cell(self, w, h, txt='', border=0, align='J', fill=False):
        # Sanitize text before passing to parent method
        sanitized_txt = safe_text(txt) if txt else ''
        return super().multi_cell(w, h, sanitized_txt, border, align, fill)
    
    def write(self, h, txt='', link=''):
        # Sanitize text before passing to parent method
        sanitized_txt = safe_text(txt) if txt else ''
        return super().write(h, sanitized_txt, link)

def add_section_title(pdf: PDF, title: str):
    # No need to call clean_text here as our PDF class will handle it
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 150, 136)
    pdf.cell(0, 10, title, ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

def add_user_input_section_title(pdf: PDF, title: str):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 153)
    pdf.cell(0, 10, clean_text(title), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

def add_classification_section(pdf: FPDF, classification_data: dict):
    line_height = 8
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "WHO 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['WHO']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(classification_data["WHO"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(4)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "ICC 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Classification: {clean_text(classification_data['ICC']['classification'])}", line_height)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(classification_data["ICC"]["derivation"], start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, line_height, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(6)

def add_risk_section(pdf: FPDF, risk_data: dict, parsed_data: dict):
    """
    Adds two risk sections:
      - ELN 2022 Risk Classification using risk_data.
      - Revised ELN24 (Non-Intensive) Risk Classification computed from parsed_data.
    """
    line_height = 8
    # ELN 2022 Risk Section
    add_section_title(pdf, "ELN 2022 Risk Classification")
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Risk Category: {risk_data.get('eln_class', 'N/A')}", line_height)
    pdf.ln(2)
    write_line_with_subheadings(pdf, f"Median OS: {risk_data.get('eln_median_os', 'N/A')}", line_height)
    pdf.ln(2)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(risk_data.get("eln_derivation", []), start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 8, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(4)
    
    # Revised ELN24 Risk Section
    add_section_title(pdf, "Revised ELN24 (Non-Intensive) Risk Classification")
    # Compute revised ELN24 risk from parsed_data.
    eln24_genes = parsed_data.get("ELN2024_risk_genes", {})
    risk_eln24, median_os_eln24, derivation_eln24 = eln2024_non_intensive_risk(eln24_genes)
    pdf.set_font("Arial", "", 10)
    write_line_with_subheadings(pdf, f"Risk Category: {risk_eln24}", line_height)
    pdf.ln(2)
    write_line_with_subheadings(pdf, f"Median OS: {median_os_eln24} months", line_height)
    pdf.ln(2)
    write_line_with_subheadings(pdf, "Derivation Steps:", line_height)
    for i, step in enumerate(derivation_eln24, start=1):
        pdf.set_font("Arial", "", 10)
        pdf.multi_cell(0, 8, f"{i}. {clean_text(step)}", align="L")
    pdf.ln(4)

def _generate_mds_confirmation_derivation_steps(mds_confirmation: dict) -> list:
    """
    Generate derivation steps based on MDS confirmation form results.
    
    Args:
        mds_confirmation (dict): MDS confirmation form data from session state
        
    Returns:
        list: List of derivation step strings describing the confirmation process
    """
    steps = []
    
    # Add header for MDS confirmation review
    steps.append("MDS Diagnostic Criteria Review:")
    
    # Check cytopenia confirmation
    cytopenia_confirmed = mds_confirmation.get("cytopenia_confirmed", False)
    if cytopenia_confirmed:
        steps.append("✓ Persistent cytopenia (>4 months) in at least one lineage confirmed")
    else:
        steps.append("✗ Persistent cytopenia requirement NOT met - lacking cytopenia >4 months without alternative cause")
    
    # Check morphological dysplasia
    morphological_dysplasia = mds_confirmation.get("morphological_dysplasia", False)
    if morphological_dysplasia:
        steps.append("✓ Morphologically defined dysplasia confirmed")
    else:
        steps.append("✗ Morphologically defined dysplasia NOT confirmed")
    
    # Check for cytoses
    wbc_cytosis = mds_confirmation.get("wbc_cytosis", False)
    monocyte_cytosis = mds_confirmation.get("monocyte_cytosis", False)
    platelet_cytosis = mds_confirmation.get("platelet_cytosis", False)
    eosinophil_cytosis = mds_confirmation.get("eosinophil_cytosis", False)
    
    cytoses = []
    if wbc_cytosis:
        cytoses.append("WBC > 13 × 10^9/L")
    if monocyte_cytosis:
        cytoses.append("Monocytosis ≥ 10% and ≥ 0.5 × 10^9/L")
    if platelet_cytosis:
        cytoses.append("Thrombocytosis ≥ 450 × 10^9/L")
    if eosinophil_cytosis:
        cytoses.append("Eosinophilia > 0.5 × 10^9/L")
    
    if cytoses:
        steps.append(f"✗ Exclusionary cytoses present: {', '.join(cytoses)}")
    else:
        steps.append("✓ No exclusionary cytoses detected")
    
    return steps

def add_ipss_risk_section(pdf: FPDF, mds_result: dict):
    """
    Adds IPSS-M and IPSS-R risk classification sections to the PDF.
    Uses the IPSS calculation results stored in the session state.
    If results aren't available, tries to calculate them from the MDS data.
    """
    line_height = 8
    
    # First, log what data is available to help with debugging
    pdf.set_font("Arial", "", 8)
    has_ipssm = 'ipssm_result' in st.session_state
    has_ipssr = 'ipssr_result' in st.session_state
    
    # Try to get IPSS data from session state, or calculate it if needed
    ipssm_result = None
    ipssr_result = None
    
    # Approach 1: Get from session state
    if 'ipssm_result' in st.session_state and 'ipssr_result' in st.session_state:
        ipssm_result = st.session_state['ipssm_result']
        ipssr_result = st.session_state['ipssr_result']
    
    # Approach 2: Try to calculate if we have the necessary data
    patient_data = None
    if (ipssm_result is None or ipssr_result is None) and mds_result and "parsed_data" in mds_result:
        try:
            from classifiers.mds_risk_classifier import calculate_ipssm, calculate_ipssr
            
            # Get patient data from the MDS result
            patient_data = mds_result["parsed_data"]
            if patient_data:
                # Calculate IPSS-M with contributions
                try:
                    ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
                    
                    # Format for consistent structure with the interactive UI
                    ipssm_result = {
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
                        }
                    }
                except Exception as e:
                    ipssm_result = None
                    pdf.cell(0, line_height, f"Note: Could not calculate IPSS-M. Error: {safe_text(str(e))}", ln=1)
                
                # Calculate IPSS-R with components
                try:
                    ipssr_result = calculate_ipssr(patient_data, return_components=True)
                except Exception as e:
                    ipssr_result = None
                    pdf.cell(0, line_height, f"Note: Could not calculate IPSS-R. Error: {safe_text(str(e))}", ln=1)
        except Exception as e:
            pdf.cell(0, line_height, f"Note: Could not import IPSS calculation modules. Error: {safe_text(str(e))}", ln=1)
    
    # If we now have IPSS results, display them
    if ipssm_result and ipssr_result:
        # IPSS-M Risk Section
        add_section_title(pdf, "IPSS-M Risk Classification")
        
        # Show warning if default TP53 VAF value was used - check both patient_data and session state
        used_default = False
        if patient_data and patient_data.get('used_default_tp53_vaf', False):
            used_default = True
        elif 'ipss_patient_data' in st.session_state and st.session_state['ipss_patient_data'].get('used_default_tp53_vaf', False):
            used_default = True
            
        if used_default:
            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(200, 0, 0)
            pdf.cell(0, line_height, "Note: Default TP53 VAF value (30%) was used in risk calculations.", ln=1)
            pdf.cell(0, line_height, "For more accurate classification, please provide the actual VAF if available.", ln=1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)
        
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, line_height, "Risk Categories", ln=1, border='B')
        pdf.ln(2)
        
        # Mean Risk
        if 'means' in ipssm_result and 'riskCat' in ipssm_result['means'] and 'riskScore' in ipssm_result['means']:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, line_height, "Mean Risk:", 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, line_height, f"{safe_text(ipssm_result['means']['riskCat'])} (Score: {ipssm_result['means']['riskScore']:.2f})", ln=1)
        
        # Best Case
        if 'best' in ipssm_result and 'riskCat' in ipssm_result['best'] and 'riskScore' in ipssm_result['best']:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, line_height, "Best Case:", 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, line_height, f"{safe_text(ipssm_result['best']['riskCat'])} (Score: {ipssm_result['best']['riskScore']:.2f})", ln=1)
        
        # Worst Case
        if 'worst' in ipssm_result and 'riskCat' in ipssm_result['worst'] and 'riskScore' in ipssm_result['worst']:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, line_height, "Worst Case:", 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, line_height, f"{safe_text(ipssm_result['worst']['riskCat'])} (Score: {ipssm_result['worst']['riskScore']:.2f})", ln=1)
        
        pdf.ln(4)
        
        # IPSS-M Contributors section if available
        if 'means' in ipssm_result and 'contributions' in ipssm_result['means']:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, line_height, "IPSS-M Risk Contributors", ln=1, border='B')
            pdf.ln(2)
            
            contributions = ipssm_result['means']['contributions']
            # Print each contribution except 'total'
            for factor, value in sorted(contributions.items(), key=lambda x: abs(x[1]) if x[0] != 'total' else 0, reverse=True):
                if factor != 'total':
                    pdf.set_font("Arial", "", 10)
                    pdf.cell(80, line_height, f"{safe_text(factor)}:", 0, 0)
                    pdf.cell(0, line_height, f"{value:.3f}", ln=1)
            
            # Print total at the end
            if 'total' in contributions:
                pdf.ln(2)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(80, line_height, "Total Score:", 0, 0)
                pdf.cell(0, line_height, f"{contributions['total']:.3f}", ln=1)
        
        pdf.ln(4)
            
        # IPSS-R Risk Section
        add_section_title(pdf, "IPSS-R Risk Classification")
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, line_height, "Risk Categories", ln=1, border='B')
        pdf.ln(2)
        
        # Standard IPSS-R
        if 'IPSSR_SCORE' in ipssr_result and 'IPSSR_CAT' in ipssr_result:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, line_height, "IPSS-R Risk Category:", 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, line_height, f"{safe_text(ipssr_result['IPSSR_CAT'])} (Score: {ipssr_result['IPSSR_SCORE']:.2f})", ln=1)
        
        # Age-adjusted IPSS-R
        if 'IPSSRA_SCORE' in ipssr_result and 'IPSSRA_CAT' in ipssr_result:
            pdf.set_font("Arial", "B", 10)
            pdf.cell(60, line_height, "Age-Adjusted Risk Category:", 0, 0)
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, line_height, f"{safe_text(ipssr_result['IPSSRA_CAT'])} (Score: {ipssr_result['IPSSRA_SCORE']:.2f})", ln=1)
        
        pdf.ln(4)
        
        # IPSS-R Components section if available
        if 'components' in ipssr_result:
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, line_height, "IPSS-R Score Components", ln=1, border='B')
            pdf.ln(2)
            
            components = ipssr_result['components']
            # Print each component
            for component, value in components.items():
                pdf.set_font("Arial", "", 10)
                pdf.cell(80, line_height, f"{safe_text(component)}:", 0, 0)
                if isinstance(value, (int, float)):
                    pdf.cell(0, line_height, f"{value:.1f} points", ln=1)
                else:
                    pdf.cell(0, line_height, f"{safe_text(value)} points", ln=1)
            
            pdf.ln(2)
            
            # Print categorization if available
            categories = {
                'Hemoglobin': 'hb_category',
                'Platelets': 'plt_category',
                'ANC': 'anc_category',
                'Bone Marrow Blasts': 'blast_category',
                'Cytogenetics': 'cyto_category'
            }
            
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, line_height, "Parameter Categorization", ln=1, border='B')
            pdf.ln(2)
            
            for param, category_key in categories.items():
                if category_key in ipssr_result:
                    pdf.set_font("Arial", "B", 10)
                    pdf.cell(60, line_height, f"{param}:", 0, 0)
                    pdf.set_font("Arial", "", 10)
                    component_key = param if param in components else None
                    score_text = ""
                    if component_key and component_key in components:
                        value = components.get(component_key)
                        if isinstance(value, (int, float)):
                            score_text = f"{value:.1f} points"
                        else:
                            score_text = f"{safe_text(value)} points"
                    pdf.cell(0, line_height, f"{safe_text(ipssr_result[category_key])} ({score_text})", ln=1)
        
        pdf.ln(4)
    else:
        # No IPSS results available - add a section explaining that
        add_section_title(pdf, "IPSS Risk Classification")
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, line_height, "IPSS risk assessment was not performed or results are not available.", ln=1)
        pdf.ln(4)
        pdf.cell(0, line_height, "Please use the Risk tab in the application to calculate IPSS risk scores.", ln=1)
        
        # Add debug info to help troubleshoot
        pdf.ln(8)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, line_height, f"Debug: ipssm_result in session state: {has_ipssm}, ipssr_result in session state: {has_ipssr}", ln=1)

def add_diagnostic_section(pdf: FPDF, diag_type: str):
    manual_key = diag_type.lower() + "_manual_result"
    ai_key = diag_type.lower() + "_ai_result"
    if manual_key in st.session_state:
        data = st.session_state[manual_key]
    elif ai_key in st.session_state:
        data = st.session_state[ai_key]
    else:
        return

    # Check if MDS confirmation form has been submitted and resulted in exclusions
    who_classification = data["who_class"]
    icc_classification = data["icc_class"]
    who_derivation = data["who_derivation"].copy() if data["who_derivation"] else []
    icc_derivation = data["icc_derivation"].copy() if data["icc_derivation"] else []
    
    # Check if this is an MDS case and if the confirmation form has been submitted
    if diag_type.upper() == "AML":  # AML can have MDS classifications too
        who_is_mds = "MDS" in who_classification if who_classification else False
        icc_is_mds = "MDS" in icc_classification if icc_classification else False
        
        if (who_is_mds or icc_is_mds) and "mds_confirmation" in st.session_state:
            mds_confirmation = st.session_state["mds_confirmation"]
            if mds_confirmation.get("submitted", False):
                # Append MDS confirmation information to derivations
                confirmation_info = _generate_mds_confirmation_derivation_steps(mds_confirmation)
                
                if mds_confirmation.get("has_exclusions", False):
                    # Override MDS classifications with exclusion result
                    if who_is_mds:
                        who_classification = "Not MDS - consider other diagnostic pathways"
                        who_derivation.extend(confirmation_info)
                        who_derivation.append("Final result: MDS diagnosis excluded due to above criteria.")
                    if icc_is_mds:
                        icc_classification = "Not MDS - consider other diagnostic pathways"
                        icc_derivation.extend(confirmation_info)
                        icc_derivation.append("Final result: MDS diagnosis excluded due to above criteria.")
                else:
                    # MDS confirmed - add confirmation info to derivation
                    if who_is_mds:
                        who_derivation.extend(confirmation_info)
                        who_derivation.append("Final result: MDS diagnosis confirmed by clinical review.")
                    if icc_is_mds:
                        icc_derivation.extend(confirmation_info)
                        icc_derivation.append("Final result: MDS diagnosis confirmed by clinical review.")

    classification_data = {
        "WHO": {
            "classification": who_classification,
            "derivation": who_derivation
        },
        "ICC": {
            "classification": icc_classification,
            "derivation": icc_derivation
        }
    }

    add_section_title(pdf, f"{diag_type} Classification Results")
    add_classification_section(pdf, classification_data)

    review_sections = [
        ("Classification Review", diag_type.lower() + "_class_review"),
        ("MRD Review", diag_type.lower() + "_mrd_review"),
        ("Gene Review", diag_type.lower() + "_gene_review"),
        ("Differentiation Review", "differentiation"),
        ("Additional Comments", diag_type.lower() + "_additional_comments")
    ]
    for section_name, key in review_sections:
        if key in st.session_state:
            add_section_title(pdf, section_name)
            output_review_text(pdf, st.session_state[key], section_name)
            pdf.ln(4)

def create_base_pdf(user_comments: str = None) -> bytes:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Generate and add clinical overview at the top of the report
    aml_result = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    mds_result = st.session_state.get("mds_manual_result") or st.session_state.get("mds_ai_result")
    
    # Determine which parsed data to use for the overview
    parsed_data_for_overview = None
    original_report_text = ""
    
    if aml_result:
        parsed_data_for_overview = aml_result["parsed_data"]
        original_report_text = aml_result.get("free_text_input", "")
    elif mds_result:
        parsed_data_for_overview = mds_result["parsed_data"]
        original_report_text = mds_result.get("free_text_input", "")
    
    # Generate clinical overview if we have parsed data
    if parsed_data_for_overview:
        with st.spinner("Generating clinical overview..."):
            clinical_overview = generate_final_overview(parsed_data_for_overview, original_report_text)
        
        # Add Clinical Overview section at the top
        add_section_title(pdf, "Overview")
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 6, clinical_overview, align="L")
        pdf.ln(6)

    # Add AML diagnostics.
    if aml_result:
        add_diagnostic_section(pdf, "AML")
        # Compute ELN2022 risk classification on the fly
        risk_eln2022, median_os_eln2022, derivation_eln2022 = eln2022_intensive_risk(aml_result["parsed_data"])
        risk_data = {
            "eln_class": risk_eln2022,
            "eln_median_os": median_os_eln2022,
            "eln_derivation": derivation_eln2022
        }
        add_risk_section(pdf, risk_data, aml_result["parsed_data"])

    # Append MDS diagnostics if available.
    if mds_result:
        add_section_title(pdf, "MDS Diagnostics")
        add_diagnostic_section(pdf, "MDS")
        # Add IPSS risk assessment if MDS is present and IPSS results are available
        add_ipss_risk_section(pdf, mds_result)
    
    if user_comments:
        add_section_title(pdf, "User Comments")
        output_review_text(pdf, user_comments, "User Comments")
        pdf.ln(4)
    
    aml_data = st.session_state.get("aml_ai_result") or st.session_state.get("aml_manual_result")
    if "aml_manual_result" in st.session_state or (aml_data and aml_data.get("free_text_input")):
        pdf.add_page()

    if "aml_manual_result" in st.session_state:
        add_user_input_section_title(pdf, "Manual User Positive Inputs")
        output_positive_findings(pdf, st.session_state["aml_manual_result"])
        pdf.ln(4)

    if aml_data and aml_data.get("free_text_input"):
        add_user_input_section_title(pdf, "Free-Text User Inputs")
        output_review_text(pdf, aml_data["free_text_input"], "Molecular Details")
        pdf.ln(4)

    try:
        return pdf.output(dest="S").encode("latin1")
    except UnicodeEncodeError:
        # If we still have encoding issues, use a more aggressive approach
        # Create a fresh PDF with maximum sanitization
        st.warning("Warning: Some special characters in your report were replaced with '?' due to encoding limitations.")
        
        # Use stringIO to capture and sanitize the PDF output
        import io
        output_buffer = io.StringIO()
        for char in pdf.output(dest="S"):
            if ord(char) < 256:  # Latin-1 range
                output_buffer.write(char)
            else:
                output_buffer.write('?')
        
        # Now encode the sanitized output
        return output_buffer.getvalue().encode("latin1")
