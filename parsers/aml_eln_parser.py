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
        "inv_16_or_t_16_16": False,  # Combined field for classifier compatibility
        "normal_karyotype": False,
        "t_9_11": False,
        "t_v_11q23": False, # Other 11q23 abnormalities
        "kmt2a_rearranged": False,  # For classifier compatibility
        "t_6_9": False,
        "t_9_22": False,  # BCR-ABL1 translocation
        "inv_3": False,
        "t_3_3": False,
        "inv3_or_t3": False,  # Combined field for classifier compatibility
        "t_8_16": False,  # t(8;16) [KAT6A::CREBBP] - missing in original
        "minus_5": False,
        "del_5q": False,
        "minus5_or_del5q": False,  # Combined field for classifier compatibility
        "minus_7": False,
        "minus7": False,  # Alternative name for classifier compatibility
        "del_7q": False,
        "del_17p": False,
        "abnormal17p": False,  # Alternative name for classifier compatibility
        "complex_karyotype": False,
        "monosomal_karyotype": False,
        "hyperdiploid_trisomy": False,  # Missing in original
        
        # Molecular markers
        "npm1_mutation": False,
        "biallelic_cebpa": False,
        "cebpa_bzip": False,  # Alternative name for classifier compatibility
        "flt3_itd": False,
        "flt3_itd_high": False,  # High allelic ratio
        "flt3_tkd": False,
        "tp53_mutation": False,
        "runx1_mutation": False,
        "asxl1_mutation": False,
        "ezh2_mutation": False,  # Missing in original
        "bcor_mutation": False,  # Missing in original
        "stag2_mutation": False,  # Missing in original
        "srsf2_mutation": False,  # Missing in original
        "u2af1_mutation": False,  # Missing in original
        "zrsr2_mutation": False,  # Missing in original
        "bcr_abl1": False,
        
        # Additional markers for ELN 2024 non-intensive
        "kras": False,
        "nras": False,
        "ptpn11": False,
        "idh1": False,
        "idh2": False,
        "ddx41": False,
        
        # Additional classification flags
        "secondary_aml": False  # Missing in original
    }
    
    # Build the OpenAI prompt
    prompt = f"""
    You are a specialized haematology AI assistant with expertise in AML and MDS genetics. 
    Please analyse the clinical report provided below and extract information relevant 
    for ELN 2022 and ELN 2024 risk stratification.
    
    Return your analysis as a valid JSON object with exactly the following structure. 
    For each marker, indicate true if present or false if absent/not mentioned:
    
    {{
        "t_8_21": false,              # t(8;21)(q22;q22.1) / RUNX1-RUNX1T1
        "inv_16": false,              # inv(16)(p13.1q22) / CBFB-MYH11
        "t_16_16": false,             # t(16;16)(p13.1;q22) / CBFB-MYH11
        "inv_16_or_t_16_16": false,   # Either inv(16) or t(16;16) / CBFB-MYH11
        "normal_karyotype": false,    # 46,XX or 46,XY with no abnormalities
        "t_9_11": false,              # t(9;11)(p21.3;q23.3) / MLLT3-KMT2A
        "t_v_11q23": false,           # Other KMT2A/MLL rearrangements excluding t(9;11)
        "kmt2a_rearranged": false,    # Any KMT2A rearrangement excluding t(9;11)
        "t_6_9": false,               # t(6;9)(p23;q34.1) / DEK-NUP214
        "t_9_22": false,              # t(9;22)(q34.1;q11.2) / BCR-ABL1
        "inv_3": false,               # inv(3)(q21.3q26.2) / GATA2,MECOM
        "t_3_3": false,               # t(3;3)(q21.3;q26.2) / GATA2,MECOM
        "inv3_or_t3": false,          # Either inv(3) or t(3;3) / GATA2,MECOM
        "t_8_16": false,              # t(8;16)(p11;p13) / KAT6A-CREBBP
        "minus_5": false,             # Monosomy 5 / -5
        "del_5q": false,              # Deletion 5q / del(5q)
        "minus5_or_del5q": false,     # Either -5 or del(5q)
        "minus_7": false,             # Monosomy 7 / -7
        "minus7": false,              # Monosomy 7 / -7 (alternative naming)
        "del_7q": false,              # Deletion 7q / del(7q)
        "del_17p": false,             # Deletion 17p / del(17p) / TP53 deletion
        "abnormal17p": false,         # 17p abnormalities (alternative naming)
        "complex_karyotype": false,   # ≥3 chromosomal abnormalities
        "monosomal_karyotype": false, # Monosomal karyotype
        "hyperdiploid_trisomy": false, # Hyperdiploid karyotype with ≥3 trisomies
        
        "npm1_mutation": false,       # NPM1 mutation 
        "biallelic_cebpa": false,     # Biallelic CEBPA mutations / double CEBPA mutations
        "cebpa_bzip": false,          # CEBPA bZIP domain mutation (alternative naming)
        "flt3_itd": false,            # FLT3 internal tandem duplication
        "flt3_itd_high": false,       # FLT3-ITD with high allelic ratio (>0.5)
        "flt3_tkd": false,            # FLT3 tyrosine kinase domain mutation (e.g., D835)
        "tp53_mutation": false,       # TP53 mutation
        "runx1_mutation": false,      # RUNX1 mutation (not as part of translocation)
        "asxl1_mutation": false,      # ASXL1 mutation
        "ezh2_mutation": false,       # EZH2 mutation
        "bcor_mutation": false,       # BCOR mutation
        "stag2_mutation": false,      # STAG2 mutation
        "srsf2_mutation": false,      # SRSF2 mutation
        "u2af1_mutation": false,      # U2AF1 mutation
        "zrsr2_mutation": false,      # ZRSR2 mutation
        "bcr_abl1": false,            # BCR-ABL1 fusion / t(9;22)
        
        "kras": false,                # KRAS mutation (for ELN 2024)
        "nras": false,                # NRAS mutation (for ELN 2024)
        "ptpn11": false,              # PTPN11 mutation (for ELN 2024)
        "idh1": false,                # IDH1 mutation (for ELN 2024)
        "idh2": false,                # IDH2 mutation (for ELN 2024)
        "ddx41": false,               # DDX41 mutation (for ELN 2024)
        
        "secondary_aml": false        # Secondary or therapy-related AML
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
            model="o3-mini",  
            messages=[
                {"role": "system", "content": "You are a specialized haematology AI that returns valid JSON."},
                {"role": "user", "content": prompt}
            ],
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
            
            # Post-process to populate combined fields for classifier compatibility
            extracted_data["inv_16_or_t_16_16"] = extracted_data.get("inv_16", False) or extracted_data.get("t_16_16", False)
            extracted_data["inv3_or_t3"] = extracted_data.get("inv_3", False) or extracted_data.get("t_3_3", False)
            extracted_data["minus5_or_del5q"] = extracted_data.get("minus_5", False) or extracted_data.get("del_5q", False)
            extracted_data["minus7"] = extracted_data.get("minus_7", False)
            extracted_data["abnormal17p"] = extracted_data.get("del_17p", False)
            extracted_data["kmt2a_rearranged"] = extracted_data.get("t_v_11q23", False)
            extracted_data["cebpa_bzip"] = extracted_data.get("biallelic_cebpa", False)
            extracted_data["t_9_22"] = extracted_data.get("bcr_abl1", False)
            
            # Post-process to populate uppercase field names for ELN 2024 non-intensive classifier
            extracted_data["TP53"] = extracted_data.get("tp53_mutation", False)
            extracted_data["KRAS"] = extracted_data.get("kras", False)
            extracted_data["PTPN11"] = extracted_data.get("ptpn11", False)
            extracted_data["NRAS"] = extracted_data.get("nras", False)
            extracted_data["FLT3_ITD"] = extracted_data.get("flt3_itd", False)
            extracted_data["NPM1"] = extracted_data.get("npm1_mutation", False)
            extracted_data["IDH1"] = extracted_data.get("idh1", False)
            extracted_data["IDH2"] = extracted_data.get("idh2", False)
            extracted_data["DDX41"] = extracted_data.get("ddx41", False)
            
            return extracted_data
            
        except json.JSONDecodeError:
            st.error("Failed to parse the AI response into JSON.")
            return default_structure
            
    except Exception as e:
        st.error(f"Error in ELN parsing: {str(e)}")
        return default_structure 