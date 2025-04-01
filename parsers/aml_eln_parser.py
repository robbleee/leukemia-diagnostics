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
    Please analyse the clinical report provided below and extract information relevant 
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
            model="o3-mini",  
            messages=[
                {"role": "system", "content": "You are a specialized hematology AI that returns valid JSON."},
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
            
            return extracted_data
            
        except json.JSONDecodeError:
            st.error("Failed to parse the AI response into JSON.")
            return default_structure
            
    except Exception as e:
        st.error(f"Error in ELN parsing: {str(e)}")
        return default_structure 