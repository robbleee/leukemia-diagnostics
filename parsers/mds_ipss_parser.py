import streamlit as st
import json
import concurrent.futures
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

def get_json_from_prompt(prompt: str) -> dict:
    """Helper function to call OpenAI and return the JSON-parsed response."""
    response = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {"role": "system", "content": "You are a knowledgeable hematologist who returns valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

def try_convert_tp53_vaf(vaf_value):
    """
    Helper function to properly convert TP53 VAF values to the expected format.
    Returns a number if VAF > 0, otherwise "NA".
    
    Args:
        vaf_value: The VAF value to convert, could be a number or string
        
    Returns:
        float or "NA": The converted VAF value
    """
    try:
        # First try to convert to float if it's a string
        if isinstance(vaf_value, str):
            vaf_value = float(vaf_value)
            
        # Check if it's a number > 0
        if isinstance(vaf_value, (int, float)) and vaf_value > 0:
            return vaf_value
        else:
            return "NA"
    except (ValueError, TypeError):
        # If conversion fails, return "NA"
        return "NA"

def parse_ipss_report(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI to extract values 
    needed for IPSS-M and IPSS-R risk classification.
    
    Extracts:
    1) Clinical values - Hemoglobin, Platelet count, ANC, bone marrow blasts, age
    2) Cytogenetic information - del5q, del7q, etc., karyotype complexity
    3) TP53 mutation status
    4) Gene mutations relevant for IPSS-M
    
    Returns:
        dict: A dictionary containing all fields needed for IPSS-M/R classification
    """
    # Safety check: if user typed nothing, return empty.
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}
        
    # The required JSON structure for IPSS-M/R calculation
    required_json_structure = {
        "clinical_values": {
            "HB": 10.0,            # Hemoglobin in g/dL
            "PLT": 150,            # Platelet count in 10^9/L
            "ANC": 2.0,            # Absolute Neutrophil Count in 10^9/L
            "BM_BLAST": 0.0,       # Bone Marrow blast percentage
            "Age": 70              # Patient age in years
        },
        "cytogenetics": {
            "del5q": False,        # del(5q)
            "del7q": False,        # del(7q)
            "minus7": False,       # -7
            "del17p": False,       # del(17p)
            "minus17": False,      # -17
            "plus8": False,        # +8
            "plus19": False,       # +19
            "del13q": False,       # del(13q)
            "del11q": False,       # del(11q)
            "del9q": False,        # del(9q)
            "del20q": False,       # del(20q)
            "delY": False,         # -Y
            "i17q": False,         # i(17q)
            "plus21": False,       # +21
            "t3q": False,          # t(3q)
            "t5q": False,          # t(5q)
            "minus13": False,      # -13
            "minus5": False,       # -5
            "t1q": False,          # t(1q)
            "inv3": False,         # inv(3)
            "t3q_GATA2": False,    # t(3q) / GATA2
            "karyotype_complexity": "Normal" # Can be "Normal", "Complex (3 abnormalities)", or "Very complex (>3 abnormalities)"
        },
        "tp53_details": {
            "TP53mut": "0",        # TP53 mutation status (0 or 1 as string)
            "TP53maxvaf": 0.0,     # Maximum VAF of TP53 mutation (percentage)
            "TP53loh": False       # Loss of heterozygosity
        },
        "gene_mutations": {
            "ASXL1": False,        # Core genes for IPSS-M
            "RUNX1": False,
            "SF3B1": False,
            "EZH2": False,
            "SRSF2": False,
            "U2AF1": False,
            "DNMT3A": False,
            "MLL_PTD": False,  
            "FLT3": False,
            "CBL": False,
            "NRAS": False,
            "IDH2": False,
            "KRAS": False,
            "NPM1": False,
            "ETV6": False,
            "TP53multi": False     # Multiple TP53 mutations (biallelic)
        },
        "residual_genes": {        # Additional genes for IPSS-M
            "BCOR": False,
            "BCORL1": False,
            "CEBPA": False,
            "ETNK1": False,
            "GATA2": False,
            "GNB1": False,
            "IDH1": False,
            "NF1": False,
            "PHF6": False,
            "PPM1D": False,
            "PRPF8": False,
            "PTPN11": False,
            "SETBP1": False,
            "STAG2": False,
            "WT1": False
        },
        "cyto_category_ipssr": "Intermediate"  # IPSS-R cytogenetic category: "Very Good", "Good", "Intermediate", "Poor", "Very Poor"
    }
    
    # -------------------------------------------------------
    # Prompt #1: Clinical Values
    # -------------------------------------------------------
    clinical_prompt = f"""
The user has pasted a free-text hematological report.
Please extract the following clinical values from the text and format them into a valid JSON object.
For numerical fields, provide the value as a number (not a string).
If a field is not found or unclear, use the default value provided.

Extract these fields:
"clinical_values": {{
    "HB": [Hemoglobin level in g/dL, default: 10.0],
    "PLT": [Platelet count in 10^9/L or K/uL, default: 150],
    "ANC": [Absolute Neutrophil Count in 10^9/L, default: 2.0],
    "BM_BLAST": [Bone Marrow blast percentage, default: 0.0],
    "Age": [Patient's age in years, default: 70]
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """
    
    # -------------------------------------------------------
    # Prompt #2: Cytogenetics
    # -------------------------------------------------------
    cytogenetics_prompt = f"""
The user has pasted a free-text hematological report.
Please extract the following cytogenetic information from the text and format it into a valid JSON object.
For boolean fields, use true/false.

Extract these fields:
"cytogenetics": {{
    "del5q": false,        
    "del7q": false,       
    "minus7": false,     
    "del17p": false,     
    "minus17": false,     
    "plus8": false,       
    "plus19": false,      
    "del13q": false,      
    "del11q": false,      
    "del9q": false,       
    "del20q": false,      
    "delY": false,        
    "i17q": false,        
    "plus21": false,      
    "t3q": false,         
    "t5q": false,         
    "minus13": false,     
    "minus5": false,      
    "t1q": false,         
    "inv3": false,        
    "t3q_GATA2": false,
    "karyotype_complexity": "Normal" 
}},
"cyto_category_ipssr": "Intermediate"

For "karyotype_complexity", choose from "Normal", "Complex (3 abnormalities)", or "Very complex (>3 abnormalities)".
For "cyto_category_ipssr", choose from "Very Good", "Good", "Intermediate", "Poor", or "Very Poor" based on the IPSS-R criteria:
- Very Good: isolated del(5q), isolated del(11q), -Y, or any double including one of these abnormalities
- Good: normal, t(5;13), t(5;17)
- Intermediate: del(13q), +8, t(2;11), -7/7q-, del(12p), i(17q), t(11;16), +2, +19, +6, +21, +1, +15, t(X;10)(q22;q21), t(11;17)(q;23;q21)  
- Poor: inv(3), t(3;3), Monosomal karyotype (2 autosomal monosomies or 1 monosomy + 1 structural abnormality), Complex (3 abnormalities)
- Very Poor: Very complex (>3 abnormalities)

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """
    
    # -------------------------------------------------------
    # Prompt #3: TP53 details
    # -------------------------------------------------------
    tp53_prompt = f"""
The user has pasted a free-text hematological report.
Please extract the TP53 mutation information from the text and format it into a valid JSON object.

Extract these fields:
"tp53_details": {{
    "TP53mut": [TP53 mutation count as a string: "0" if none, "1" if single mutation, "2" if multiple mutations are present],
    "TP53maxvaf": [Maximum variant allele frequency (VAF) of the TP53 mutation as a number (0-100), default: 0.0],
    "TP53loh": [true if there's loss of heterozygosity in TP53, false otherwise]
}}

IMPORTANT RULES:
1. Return "TP53mut" as a STRING: "0", "1", or "2" 
2. Return "TP53maxvaf" as a NUMBER (not a string): e.g., 45.2 for 45.2%
3. If no VAF is mentioned but TP53 mutation is present, use 30.0 as a default value
4. For "TP53loh", return a BOOLEAN: true or false

Examples of what to look for:
- "TP53 mutation with 45% VAF" → TP53mut: "1", TP53maxvaf: 45.0, TP53loh: false
- "Biallelic TP53 mutation" → TP53mut: "2", TP53maxvaf: 30.0, TP53loh: true
- "TP53 mutation with loss of heterozygosity" → TP53mut: "1", TP53maxvaf: 30.0, TP53loh: true
- "Two TP53 mutations" → TP53mut: "2", TP53maxvaf: 30.0, TP53loh: false
- "No TP53 mutation" → TP53mut: "0", TP53maxvaf: 0.0, TP53loh: false

Take care to distinguish between single and multiple TP53 mutations. If the text mentions "biallelic" TP53 or multiple mutations, use "2" for TP53mut.

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """
    
    # -------------------------------------------------------
    # Prompt #4: Gene mutations
    # -------------------------------------------------------
    genes_prompt = f"""
The user has pasted a free-text hematological report.
Please extract information about gene mutations from the text and format it into a valid JSON object.
For each gene, set the value to true if the text indicates that gene is mutated; otherwise false.

Extract these fields:
"gene_mutations": {{
    "ASXL1": false,
    "RUNX1": false,
    "SF3B1": false,
    "EZH2": false,
    "SRSF2": false,
    "U2AF1": false,
    "DNMT3A": false,
    "MLL_PTD": false,
    "FLT3": false,
    "CBL": false,
    "NRAS": false,
    "IDH2": false,
    "KRAS": false,
    "NPM1": false,
    "ETV6": false,
    "TP53multi": false
}},
"residual_genes": {{
    "BCOR": false,
    "BCORL1": false,
    "CEBPA": false,
    "ETNK1": false,
    "GATA2": false,
    "GNB1": false,
    "IDH1": false,
    "NF1": false,
    "PHF6": false,
    "PPM1D": false,
    "PRPF8": false,
    "PTPN11": false,
    "SETBP1": false,
    "STAG2": false,
    "WT1": false
}}

CRITICAL INSTRUCTIONS FOR TP53multi:
Set "TP53multi" to true if ANY of these conditions are met:
1. Multiple TP53 mutations are mentioned (e.g., "2 TP53 mutations", "two TP53 mutations")
2. The text mentions "biallelic TP53" or "biallelic mutation of TP53"
3. One TP53 mutation is mentioned along with LOH or loss of heterozygosity
4. One TP53 mutation is mentioned along with deletion of the other allele (e.g., del(17p))
5. The VAF of TP53 is >50% (suggesting loss of wild-type allele)
6. The text mentions "compound heterozygous TP53 mutations"

Examples of text that should set TP53multi to true:
- "TP53 mutation (c.817C>T, p.R273C) with VAF 80% and chromosome 17p deletion"
- "Biallelic inactivation of TP53"
- "Two pathogenic mutations in TP53: p.R248W and p.R175H"
- "TP53 mutation with loss of heterozygosity"

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
   
    """
    
    try:
        # Store prompts for debugging
        prompts = {
            "clinical_prompt": clinical_prompt,
            "cytogenetics_prompt": cytogenetics_prompt,
            "tp53_prompt": tp53_prompt,
            "genes_prompt": genes_prompt
        }
        
        # Parallelize the prompt calls
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(get_json_from_prompt, clinical_prompt)
            future2 = executor.submit(get_json_from_prompt, cytogenetics_prompt)
            future3 = executor.submit(get_json_from_prompt, tp53_prompt)
            future4 = executor.submit(get_json_from_prompt, genes_prompt)

            # Gather results when all are complete
            clinical_data = future1.result()
            cytogenetics_data = future2.result()
            tp53_data = future3.result()
            genes_data = future4.result()

        # Merge all data into one dictionary
        parsed_data = {}
        parsed_data.update(clinical_data)
        parsed_data.update(cytogenetics_data)
        parsed_data.update(tp53_data)
        parsed_data.update(genes_data)
        
        # Add prompts to the parsed data for debugging
        parsed_data["__prompts"] = prompts

        # -------------------------------------------------------
        # Validate TP53 data and ensure it exists with proper format
        # -------------------------------------------------------
        # Check if tp53_details exists in the parsed data
        if "tp53_details" not in parsed_data or not isinstance(parsed_data["tp53_details"], dict):
            print("⚠️ tp53_details missing or not a dictionary! Creating default structure.")
            parsed_data["tp53_details"] = {"TP53mut": "0", "TP53maxvaf": 0.0, "TP53loh": False}
        
        # Direct text analysis for TP53 as a fallback
        if "tp53_details" in parsed_data and (
            parsed_data["tp53_details"].get("TP53mut", "0") == "0" or 
            parsed_data["tp53_details"].get("TP53maxvaf", 0) == 0
        ):
            # Fallback: direct text search for TP53 mutations
            tp53_text_patterns = [
                "TP53 mutation", "p53 mutation", "TP53 mutated", 
                "TP53 pathogenic", "mutated TP53", "TP53 variant"
            ]
            
            # Check if any TP53 patterns are in the text
            if any(pattern.lower() in report_text.lower() for pattern in tp53_text_patterns):
                print("⚠️ Found TP53 mutation in text but not in JSON response. Setting values manually.")
                parsed_data["tp53_details"]["TP53mut"] = "1"
                parsed_data["tp53_details"]["TP53maxvaf"] = 30.0  # Default VAF
                
                # Look for biallelic/double mutations
                biallelic_patterns = [
                    "biallelic", "multiple", "two TP53", "second TP53", 
                    "both allele", "both copies", "compound heterozygous"
                ]
                if any(pattern.lower() in report_text.lower() for pattern in biallelic_patterns):
                    parsed_data["tp53_details"]["TP53mut"] = "2"
                    parsed_data["gene_mutations"]["TP53multi"] = True
                
                # Look for LOH
                loh_patterns = ["LOH", "loss of heterozygosity", "17p deletion", "del(17p)"]
                if any(pattern.lower() in report_text.lower() for pattern in loh_patterns):
                    parsed_data["tp53_details"]["TP53loh"] = True
                
                # Look for VAF patterns like "40%", "VAF 40", etc.
                import re
                vaf_matches = re.findall(r'(?:VAF|variant allele frequency|allele frequency)[^\d]*(\d+(?:\.\d+)?)', report_text, re.IGNORECASE)
                if vaf_matches:
                    try:
                        parsed_data["tp53_details"]["TP53maxvaf"] = float(vaf_matches[0])
                    except (ValueError, TypeError):
                        pass  # Keep the default value

        # Ensure TP53_details has all required fields
        required_tp53_fields = {"TP53mut": "0", "TP53maxvaf": 0.0, "TP53loh": False}
        for field, default_value in required_tp53_fields.items():
            if field not in parsed_data["tp53_details"]:
                print(f"⚠️ Missing {field} in tp53_details! Setting default value.")
                parsed_data["tp53_details"][field] = default_value
            elif parsed_data["tp53_details"][field] is None:
                print(f"⚠️ {field} is None in tp53_details! Setting default value.")
                parsed_data["tp53_details"][field] = default_value

        # Fill missing keys from required structure
        for key, val in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = val
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_val
        
        # Prepare the data in the format expected by the IPSS-M/R calculator
        ipssm_data = {
            # Clinical values
            "BM_BLAST": parsed_data["clinical_values"]["BM_BLAST"],
            "HB": parsed_data["clinical_values"]["HB"],
            "PLT": parsed_data["clinical_values"]["PLT"],
            "ANC": parsed_data["clinical_values"]["ANC"],
            "AGE": parsed_data["clinical_values"]["Age"],
            
            # IPSS-R cytogenetic category
            "CYTO_IPSSR": parsed_data["cyto_category_ipssr"],
            
            # Cytogenetic abnormalities
            "del5q": 1 if parsed_data["cytogenetics"]["del5q"] else 0,
            "del7q": 1 if parsed_data["cytogenetics"]["del7q"] else 0,
            "del7_minus7": 1 if parsed_data["cytogenetics"]["minus7"] else 0,
            "del17_17p": 1 if parsed_data["cytogenetics"]["del17p"] else 0,
            "complex": 1 if parsed_data["cytogenetics"]["karyotype_complexity"] in ["Complex (3 abnormalities)", "Very complex (>3 abnormalities)"] else 0,
            
            # TP53 status - FIXED: Convert values and provide fallbacks
            "TP53mut": str(parsed_data["tp53_details"]["TP53mut"]),  # Ensure it's a string
            "TP53maxvaf": try_convert_tp53_vaf(parsed_data["tp53_details"]["TP53maxvaf"]),
            "TP53loh": "1" if parsed_data["tp53_details"]["TP53loh"] else "0",
            "TP53multi": 1 if parsed_data["gene_mutations"].get("TP53multi", False) or str(parsed_data["tp53_details"]["TP53mut"]) == "2" else 0
        }
        
        # Additional validation for TP53 data
        if isinstance(ipssm_data["TP53mut"], (int, float)):
            ipssm_data["TP53mut"] = str(int(ipssm_data["TP53mut"]))
        
        # Check for TP53 data consistency and apply fallbacks
        # If TP53mut is "1" or "2", ensure TP53maxvaf has a value other than "NA"
        if ipssm_data["TP53mut"] in ["1", "2"] and ipssm_data["TP53maxvaf"] == "NA":
            print("⚠️ TP53 mutation present but VAF is NA. Setting default value of 30.0")
            ipssm_data["TP53maxvaf"] = 30.0  # Default value if mutation is present but VAF is missing
            
        # If TP53mut isn't one of the expected values, fix it
        if ipssm_data["TP53mut"] not in ["0", "1", "2"]:
            print(f"⚠️ Invalid TP53mut value: {ipssm_data['TP53mut']}. Converting to appropriate string.")
            if ipssm_data["TP53mut"] and ipssm_data["TP53mut"].lower() not in ["0", "false", "no", "none"]:
                ipssm_data["TP53mut"] = "1"  # Any non-zero/non-false value becomes "1"
            else:
                ipssm_data["TP53mut"] = "0"
                
        # If we have del17p and TP53 mutation, set TP53multi to 1
        if ipssm_data["del17_17p"] == 1 and ipssm_data["TP53mut"] in ["1", "2"]:
            ipssm_data["TP53multi"] = 1
            ipssm_data["TP53loh"] = "1"
            
        # Add gene mutations
        for gene_category in ["gene_mutations", "residual_genes"]:
            for gene, value in parsed_data[gene_category].items():
                if gene != "TP53multi":  # Already handled above
                    ipssm_data[gene] = 1 if value else 0
        
        # Add the prompts to the ipssm_data for debugging
        ipssm_data["__prompts"] = parsed_data["__prompts"]
        
        # Debug print
        print("Parsed ipss Report JSON:")
        print(json.dumps(parsed_data, indent=2))
        
        # Debug TP53 data specifically
        print("\nTP53 Data Debug:")
        print(f"TP53 details from LLM: {json.dumps(parsed_data['tp53_details'], indent=2)}")
        print(f"TP53multi from gene mutations: {parsed_data['gene_mutations']['TP53multi']}")
        print(f"Final TP53 data in IPSSM format:")
        print(f"  TP53mut: {ipssm_data['TP53mut']}")
        print(f"  TP53maxvaf: {ipssm_data['TP53maxvaf']}")
        print(f"  TP53loh: {ipssm_data['TP53loh']}")
        print(f"  TP53multi: {ipssm_data['TP53multi']}")
        
        return ipssm_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse AI response into JSON. Ensure the report is well-formatted.")
        print("❌ JSONDecodeError: Could not parse AI JSON response.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI: {str(e)}")
        print(f"❌ Exception: {str(e)}")
        return {} 