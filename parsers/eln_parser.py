#!/usr/bin/env python
"""
Parser for extracting ELN 2022 risk classification relevant data from clinical reports.
This parser specifically focuses on extracting cytogenetic and molecular markers
needed for the ELN 2022 risk stratification of AML.
"""

import streamlit as st
import json
import re
from typing import Dict, Any
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def parse_eln_report(report_text: str) -> Dict[str, Any]:
    """
    Extracts relevant cytogenetic and molecular markers from clinical reports
    for ELN 2022 risk stratification using OpenAI's language model.
    
    Args:
        report_text (str): Raw text from clinical report
        
    Returns:
        Dict[str, Any]: Dictionary of extracted markers with boolean values
    """
    # Safety check for empty report
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}
    
    # Initialize the default structure
    default_structure = {
        # Cytogenetic abnormalities
        "t_8_21": False,
        "inv_16": False,
        "t_16_16": False,
        "normal_karyotype": False,
        "t_9_11": False,
        "t_v_11q23": False, # Other 11q23 abnormalities
        "t_6_9": False,
        "inv_3": False,
        "t_3_3": False,
        "minus_5": False,
        "del_5q": False,
        "minus_7": False,
        "del_7q": False,
        "del_17p": False,
        "complex_karyotype": False,
        "monosomal_karyotype": False,
        
        # Molecular markers
        "npm1_mutation": False,
        "biallelic_cebpa": False,
        "flt3_itd": False,
        "flt3_itd_high": False,  # High allelic ratio
        "flt3_tkd": False,
        "tp53_mutation": False,
        "runx1_mutation": False,
        "asxl1_mutation": False,
        "bcr_abl1": False,
        
        # Additional markers for ELN 2024 non-intensive
        "kras": False,
        "nras": False,
        "ptpn11": False,
        "idh1": False,
        "idh2": False,
        "ddx41": False
    }
    
    # Build the OpenAI prompt
    prompt = f"""
    You are a specialized hematology AI assistant with expertise in AML and MDS genetics. 
    Please analyze the clinical report provided below and extract information relevant 
    for ELN 2022 and ELN 2024 risk stratification.
    
    Return your analysis as a valid JSON object with exactly the following structure. 
    For each marker, indicate true if present or false if absent/not mentioned:
    
    {{
        "t_8_21": false,              # t(8;21)(q22;q22.1) / RUNX1-RUNX1T1
        "inv_16": false,              # inv(16)(p13.1q22) / CBFB-MYH11
        "t_16_16": false,             # t(16;16)(p13.1;q22) / CBFB-MYH11
        "normal_karyotype": false,    # 46,XX or 46,XY with no abnormalities
        "t_9_11": false,              # t(9;11)(p21.3;q23.3) / MLLT3-KMT2A
        "t_v_11q23": false,           # Other KMT2A/MLL rearrangements excluding t(9;11)
        "t_6_9": false,               # t(6;9)(p23;q34.1) / DEK-NUP214
        "inv_3": false,               # inv(3)(q21.3q26.2) / GATA2,MECOM
        "t_3_3": false,               # t(3;3)(q21.3;q26.2) / GATA2,MECOM
        "minus_5": false,             # Monosomy 5 / -5
        "del_5q": false,              # Deletion 5q / del(5q)
        "minus_7": false,             # Monosomy 7 / -7
        "del_7q": false,              # Deletion 7q / del(7q)
        "del_17p": false,             # Deletion 17p / del(17p) / TP53 deletion
        "complex_karyotype": false,   # ≥3 chromosomal abnormalities
        "monosomal_karyotype": false, # Monosomal karyotype
        
        "npm1_mutation": false,       # NPM1 mutation 
        "biallelic_cebpa": false,     # Biallelic CEBPA mutations / double CEBPA mutations
        "flt3_itd": false,            # FLT3 internal tandem duplication
        "flt3_itd_high": false,       # FLT3-ITD with high allelic ratio (>0.5)
        "flt3_tkd": false,            # FLT3 tyrosine kinase domain mutation (e.g., D835)
        "tp53_mutation": false,       # TP53 mutation
        "runx1_mutation": false,      # RUNX1 mutation (not as part of translocation)
        "asxl1_mutation": false,      # ASXL1 mutation
        "bcr_abl1": false,            # BCR-ABL1 fusion / t(9;22)
        
        "kras": false,                # KRAS mutation (for ELN 2024)
        "nras": false,                # NRAS mutation (for ELN 2024)
        "ptpn11": false,              # PTPN11 mutation (for ELN 2024)
        "idh1": false,                # IDH1 mutation (for ELN 2024)
        "idh2": false,                # IDH2 mutation (for ELN 2024)
        "ddx41": false                # DDX41 mutation (for ELN 2024)
    }}
    
    **IMPORTANT**:
    - Return ONLY valid JSON, no other text.
    - Be precise about identifying genetic markers.
    - If the same gene appears in different contexts, carefully distinguish between them.
    - For cytogenetic findings, recognize common notations (e.g., "46,XX" = normal karyotype).
    - For molecular findings, consider various notations (e.g., "NPM1+" = NPM1 mutation).
    - For FLT3-ITD, check if an allelic ratio is mentioned; if >0.5, set flt3_itd_high to true.
    
    Here is the clinical report:
    
    {report_text}
    """
    
    try:
        # Make the API call to OpenAI
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for better accuracy with medical text
            messages=[
                {"role": "system", "content": "You are a specialized hematology AI that returns valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Set to 0 for most deterministic response
            max_tokens=1000
        )
        
        # Extract the content
        response_content = response.choices[0].message.content.strip()
        
        # Parse the JSON response
        try:
            extracted_data = json.loads(response_content)
            
            # Ensure all required keys are present
            for key in default_structure:
                if key not in extracted_data:
                    extracted_data[key] = default_structure[key]
            
            # Fallback regex check for critical markers that might be missed
            # This is a safety net in case the AI misses obvious mentions
            text = report_text.lower()
            
            # Critical marker check for common, unambiguous patterns
            if not extracted_data["flt3_itd"] and re.search(r'flt3\s*-?\s*itd|flt3\s+internal\s+tandem', text):
                extracted_data["flt3_itd"] = True
                st.info("FLT3-ITD detected by pattern matching (missed by AI).")
            
            if not extracted_data["npm1_mutation"] and re.search(r'npm1\s+mutation|\bnpm1\+', text):
                extracted_data["npm1_mutation"] = True
                st.info("NPM1 mutation detected by pattern matching (missed by AI).")
            
            return extracted_data
            
        except json.JSONDecodeError:
            st.error("Failed to parse the AI response into JSON. Using regex fallback.")
            # Fall back to regex-based extraction using the original implementation
            return regex_fallback_parse(report_text)
            
    except Exception as e:
        st.error(f"Error in ELN parsing: {str(e)}")
        # Fall back to regex-based extraction
        return regex_fallback_parse(report_text)

def regex_fallback_parse(report_text: str) -> Dict[str, Any]:
    """
    Fallback function that uses regex patterns to extract ELN markers
    when the OpenAI API call fails.
    
    Args:
        report_text (str): Raw text from clinical report
        
    Returns:
        Dict[str, Any]: Dictionary of extracted markers with boolean values
    """
    # Initialize output dictionary with all markers set to False
    eln_data = {
        # Cytogenetic abnormalities
        "t_8_21": False,
        "inv_16": False,
        "t_16_16": False,
        "normal_karyotype": False,
        "t_9_11": False,
        "t_v_11q23": False, # Other 11q23 abnormalities
        "t_6_9": False,
        "inv_3": False,
        "t_3_3": False,
        "minus_5": False,
        "del_5q": False,
        "minus_7": False,
        "del_7q": False,
        "del_17p": False,
        "complex_karyotype": False,
        "monosomal_karyotype": False,
        
        # Molecular markers
        "npm1_mutation": False,
        "biallelic_cebpa": False,
        "flt3_itd": False,
        "flt3_itd_high": False,  # High allelic ratio
        "flt3_tkd": False,
        "tp53_mutation": False,
        "runx1_mutation": False,
        "asxl1_mutation": False,
        "bcr_abl1": False,
        
        # Additional markers for ELN 2024 non-intensive
        "kras": False,
        "nras": False,
        "ptpn11": False,
        "idh1": False,
        "idh2": False,
        "ddx41": False
    }
    
    # Convert to lowercase for case-insensitive matching
    text = report_text.lower()
    
    # Check for cytogenetic abnormalities
    if re.search(r't\(8;21\)|aml1[/-]eto|runx1[/-]runx1t1', text):
        eln_data["t_8_21"] = True
    
    if re.search(r'inv\(16\)|cbfb[/-]myh11', text):
        eln_data["inv_16"] = True
    
    if re.search(r't\(16;16\)', text):
        eln_data["t_16_16"] = True
    
    if re.search(r'normal karyotype|46,x[xy](\s|,|$)|cytogenetically normal', text):
        eln_data["normal_karyotype"] = True
    
    if re.search(r't\(9;11\)|mllt3[/-]kmt2a', text):
        eln_data["t_9_11"] = True
    
    if re.search(r't\(\d+;11q23\)|t\(11q23;\d+\)|mll\s+rearrangement|kmt2a\s+rearrangement', text) and not eln_data["t_9_11"]:
        eln_data["t_v_11q23"] = True
    
    if re.search(r't\(6;9\)|dek[/-]nup214', text):
        eln_data["t_6_9"] = True
    
    if re.search(r'inv\(3\)|mecom\s+rearrangement', text):
        eln_data["inv_3"] = True
    
    if re.search(r't\(3;3\)', text):
        eln_data["t_3_3"] = True
    
    if re.search(r'-5\b|\bmonosomy 5\b', text):
        eln_data["minus_5"] = True
    
    if re.search(r'del\(5q\)|5q-', text):
        eln_data["del_5q"] = True
    
    if re.search(r'-7\b|\bmonosomy 7\b', text):
        eln_data["minus_7"] = True
    
    if re.search(r'del\(7q\)|7q-', text):
        eln_data["del_7q"] = True
    
    if re.search(r'del\(17p\)|17p\-|tp53\s+deletion|p53\s+deletion', text):
        eln_data["del_17p"] = True
    
    if re.search(r'complex karyotype|≥\s*3\s*abnormalities|≥3\s+abnormalities|three or more (distinct )?abnormalities', text):
        eln_data["complex_karyotype"] = True
    
    if re.search(r'monosomal karyotype', text):
        eln_data["monosomal_karyotype"] = True
    
    # Check for molecular mutations
    if re.search(r'npm1\s+mutation|npm1\s+\bpositive\b|\bnpm1\+', text):
        eln_data["npm1_mutation"] = True
    
    if re.search(r'biallelic\s+cebpa|cebpa\s+biallelic|double\s+mutated\s+cebpa|cebpa\s+double\s+mutation', text):
        eln_data["biallelic_cebpa"] = True
    
    flt3_itd_match = re.search(r'flt3\s*-?\s*itd|flt3\s+internal\s+tandem\s+duplication', text)
    if flt3_itd_match:
        eln_data["flt3_itd"] = True
        
        # Look for high allelic ratio
        high_ratio_pattern = r'(high|increased)(\s+allelic)?\s+ratio|allelic\s+ratio\s*(>|≥|greater than)\s*0\.5|ar\s*(>|≥|greater than)\s*0\.5'
        if re.search(high_ratio_pattern, text, flags=re.IGNORECASE):
            eln_data["flt3_itd_high"] = True
    
    if re.search(r'flt3\s*-?\s*tkd|flt3\s+tyrosine\s+kinase\s+domain|flt3\s+d835', text):
        eln_data["flt3_tkd"] = True
    
    if re.search(r'tp53\s+mutation|p53\s+mutation|\btp53\+|\bp53\+', text):
        eln_data["tp53_mutation"] = True
    
    if re.search(r'runx1\s+mutation|\brunx1\+', text):
        eln_data["runx1_mutation"] = True
    
    if re.search(r'asxl1\s+mutation|\basxl1\+', text):
        eln_data["asxl1_mutation"] = True
    
    if re.search(r'bcr[/-]abl1|t\(9;22\)|philadelphia\s+chromosome', text):
        eln_data["bcr_abl1"] = True
    
    # Additional markers for ELN 2024
    if re.search(r'kras\s+mutation|\bkras\+', text):
        eln_data["kras"] = True
    
    if re.search(r'nras\s+mutation|\bnras\+', text):
        eln_data["nras"] = True
    
    if re.search(r'ptpn11\s+mutation|\bptpn11\+', text):
        eln_data["ptpn11"] = True
    
    if re.search(r'idh1\s+mutation|\bidh1\+', text):
        eln_data["idh1"] = True
    
    if re.search(r'idh2\s+mutation|\bidh2\+', text):
        eln_data["idh2"] = True
    
    if re.search(r'ddx41\s+mutation|\bddx41\+', text):
        eln_data["ddx41"] = True
    
    return eln_data 