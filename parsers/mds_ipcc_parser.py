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

def parse_ipcc_report(report_text: str) -> dict:
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
If a field is not found or unclear, use the default value.

Extract these fields:
"tp53_details": {{
    "TP53mut": [TP53 mutation count: "0" if none, "1" if single mutation, "2" if multiple mutations are present],
    "TP53maxvaf": [Maximum variant allele frequency (VAF) of the TP53 mutation in percentage (0-100), default: 0.0],
    "TP53loh": [true if there's loss of heterozygosity in TP53, false otherwise]
}}

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

Be particularly careful with "TP53multi" - set it to true if ANY of these conditions are met:
1. Multiple TP53 mutations are mentioned (e.g., "2 TP53 mutations", "two TP53 mutations")
2. Biallelic TP53 mutation or abnormality is mentioned
3. One TP53 mutation with loss of heterozygosity (LOH) is mentioned
4. One TP53 mutation with deletion of the other allele (e.g., del(17p)) is mentioned

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
            
            # TP53 status - updated to match manual form format
            "TP53mut": parsed_data["tp53_details"]["TP53mut"],  # Should now be "0", "1", or "2"
            "TP53maxvaf": parsed_data["tp53_details"]["TP53maxvaf"] if parsed_data["tp53_details"]["TP53maxvaf"] > 0 else "NA",
            "TP53loh": "1" if parsed_data["tp53_details"]["TP53loh"] else "0",
            "TP53multi": 1 if parsed_data["gene_mutations"]["TP53multi"] or parsed_data["tp53_details"]["TP53mut"] == "2" else 0
        }
        
        # Add gene mutations
        for gene_category in ["gene_mutations", "residual_genes"]:
            for gene, value in parsed_data[gene_category].items():
                if gene != "TP53multi":  # Already handled above
                    ipssm_data[gene] = 1 if value else 0
        
        # Add the prompts to the ipssm_data for debugging
        ipssm_data["__prompts"] = parsed_data["__prompts"]
        
        # Debug print
        print("Parsed IPCC Report JSON:")
        print(json.dumps(parsed_data, indent=2))
        
        return ipssm_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse AI response into JSON. Ensure the report is well-formatted.")
        print("❌ JSONDecodeError: Could not parse AI JSON response.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI: {str(e)}")
        print(f"❌ Exception: {str(e)}")
        return {} 