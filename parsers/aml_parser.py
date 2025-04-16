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
            {"role": "system", "content": "You are a knowledgeable haematologist who returns valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

def parse_genetics_report_aml(report_text: str) -> dict:
    """
    Sends the free-text haematological report to OpenAI using separate prompts:
      1) Basic clinical numeric/boolean values,
      2a) AML-defining recurrent genetic abnormalities,
      2b) Biallelic TP53 mutation,
      2c) MDS-related mutations and MDS-related cytogenetics,
      3) Qualifiers,
      4) AML differentiation,
      5) Revised ELN24 genes (added prompt),
      6) Check for missing cytogenetic data.

    Then merges all JSON objects into one dictionary. 
    No second pass is performed—each section's data is returned from its dedicated prompt.

    Returns:
        dict: A dictionary containing all fields needed for classification, 
              including 'AML_differentiation', 'differentiation_reasoning', and 'no_cytogenetics_data'.
              The 'no_cytogenetics_data' field is true if no cytogenetic information was found in the report.
    """
    # Safety check: if user typed nothing, return empty.
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}

    # The original required JSON structure (including differentiation_reasoning).
    required_json_structure = {
        "blasts_percentage": None,  # if unknown, set to None => "Unknown"
        "fibrotic": False,
        "hypoplasia": False,
        "number_of_dysplastic_lineages": None,
        "no_cytogenetics_data": False,  # New field: true if no cytogenetic data is provided
        "AML_defining_recurrent_genetic_abnormalities": {
            "PML::RARA": False,
            "NPM1": False,
            "RUNX1::RUNX1T1": False,
            "CBFB::MYH11": False,
            "DEK::NUP214": False,
            "RBM15::MRTFA": False,
            "MLLT3::KMT2A": False,
            "GATA2::MECOM": False,
            "KMT2A": False,
            "MECOM": False,
            "NUP98": False,
            "CEBPA": False,
            "bZIP": False,
            "BCR::ABL1": False,
            "IRF2BP2::RARA": False,
            "NPM1::RARA": False,
            "ZBTB16::RARA": False,
            "STAT5B::RARA": False,
            "STAT3::RARA": False,
            "RARA::TBL1XR1": False,
            "RARA::FIP1L1": False,
            "RARA::BCOR": False,
            "AFF1::KMT2A": False,
            "AFDN::KMT2A": False,
            "MLLT10::KMT2A": False,
            "TET1::KMT2A": False,
            "KMT2A::ELL": False,
            "KMT2A::MLLT1": False,
            "MYC::MECOM": False,
            "ETV6::MECOM": False,
            "MECOM::RUNX1": False,
            "PRDM16::RPN1": False,
            "NPM1::MLF1": False,
            "NUP98::NSD1": False,
            "NUP98::KMD5A": False,
            "ETV6::MNX1": False,
            "KAT6A::CREBBP": False,
            "PICALM::MLLT10": False,
            "FUS::ERG": False,
            "RUNX1::CBFA2T3": False,
            "CBFA2T3::GLIS2": False
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": False,
            "1_x_TP53_mutation_del_17p": False,
            "1_x_TP53_mutation_LOH": False,
            "1_x_TP53_mutation_10_percent_vaf": False
        },
        "MDS_related_mutation": {
            "ASXL1": False,
            "BCOR": False,
            "EZH2": False,
            "RUNX1": False,
            "SF3B1": False,
            "SRSF2": False,
            "STAG2": False,
            "U2AF1": False,
            "ZRSR2": False
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": False,
            "del_5q": False,
            "t_5q": False,
            "add_5q": False,
            "-7": False,
            "del_7q": False,
            "+8": False,
            "del_11q": False,
            "del_12p": False,
            "t_12p": False,
            "add_12p": False,
            "-13": False,
            "i_17q": False,
            "-17": False,
            "add_17p": False,
            "del_17p": False,
            "del_20q": False,
            "idic_X_q13": False
        },
        "AML_differentiation": None,
        "differentiation_reasoning": None,
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": False,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
            "previous_cytotoxic_therapy": None,
            "predisposing_germline_variant": "None"
        },
        # NEW: Revised ELN24 Genes
        "ELN2024_risk_genes": {
            "TP53": False,
            "KRAS": False,
            "PTPN11": False,
            "NRAS": False,
            "FLT3_ITD": False,
            "NPM1": False,
            "IDH1": False,
            "IDH2": False,
            "DDX41": False
        }
    }

    # -------------------------------------------------------
    # Prompt #1: Basic clinical numeric & boolean values.
    # -------------------------------------------------------
    first_prompt_1 = f"""
The user has pasted a free-text haematological report.
Please extract the following fields from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false. For numerical fields, provide the value.
If a field is not found or unclear, set it to false (for booleans) or null (for numerical values).

Extract these fields:
- "blasts_percentage": (a numerical value between 0 and 100, or null if not found)
- "fibrotic": (true if the report suggests MDS with fibrosis; otherwise false)
- "hypoplasia": (true if the report suggests MDS with hypoplasia; otherwise false)
- "number_of_dysplastic_lineages": (an integer, or null if not found)

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #2a: AML_defining_recurrent_genetic_abnormalities
    first_prompt_2a = f"""
The user has pasted a free-text haematological report.
Please extract the following information from the text and format it into a valid JSON object exactly as specified below.
For boolean fields, use true/false.

Extract this nested field:
"AML_defining_recurrent_genetic_abnormalities": {{
    "PML::RARA": false,
    "NPM1": false,
    "RUNX1::RUNX1T1": false,
    "CBFB::MYH11": false,
    "DEK::NUP214": false,
    "RBM15::MRTFA": false,
    "MLLT3::KMT2A": false,
    "GATA2::MECOM": false,
    "KMT2A": false,
    "MECOM": false,
    "NUP98": false,
    "CEBPA": false,
    "bZIP": false,
    "BCR::ABL1": false,
    "IRF2BP2::RARA": false,
    "NPM1::RARA": false,
    "ZBTB16::RARA": false,
    "STAT5B::RARA": false,
    "STAT3::RARA": false,
    "RARA::TBL1XR1": false,
    "RARA::FIP1L1": false,
    "RARA::BCOR": false,
    "AFF1::KMT2A": false,
    "AFDN::KMT2A": false,
    "MLLT10::KMT2A": false,
    "TET1::KMT2A": false,
    "KMT2A::ELL": false,
    "KMT2A::MLLT1": false,
    "MYC::MECOM": false,
    "ETV6::MECOM": false,
    "MECOM::RUNX1": false,
    "PRDM16::RPN1": false,
    "NPM1::MLF1": false,
    "NUP98::NSD1": false,
    "NUP98::KMD5A": false,
    "ETV6::MNX1": false,
    "KAT6A::CREBBP": false,
    "PICALM::MLLT10": false,
    "FUS::ERG": false,
    "RUNX1::CBFA2T3": false,
    "CBFA2T3::GLIS2": false
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #2b: Biallelic_TP53_mutation
    first_prompt_2b = f"""
The user has pasted a free-text haematological report.
Please extract the following information from the text and format it into a valid JSON object exactly as specified below.
For boolean fields, use true/false.

Extract this nested field:
"Biallelic_TP53_mutation": {{
    "2_x_TP53_mutations": false,
    "1_x_TP53_mutation_del_17p": false,
    "1_x_TP53_mutation_LOH": false,
    "1_x_TP53_mutation_10_percent_vaf": false
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #2c: MDS_related_mutation and MDS_related_cytogenetics
    first_prompt_2c = f"""
The user has pasted a free-text haematological report.
Please extract the following information from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false.

Extract these nested fields:
"MDS_related_mutation": {{
    "ASXL1": false,
    "BCOR": false,
    "EZH2": false,
    "RUNX1": false,
    "SF3B1": false,
    "SRSF2": false,
    "STAG2": false,
    "U2AF1": false,
    "ZRSR2": false
}},
"MDS_related_cytogenetics": {{
    "Complex_karyotype": false,
    "del_5q": false,
    "t_5q": false,
    "add_5q": false,
    "-7": false,
    "del_7q": false,
    "+8": false,
    "del_11q": false,
    "del_12p": false,
    "t_12p": false,
    "add_12p": false,
    "-13": false,
    "i_17q": false,
    "-17": false,
    "add_17p": false,
    "del_17p": false,
    "del_20q": false,
    "idic_X_q13": false
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #3: Qualifiers
    first_prompt_3 = f"""
The user has pasted a free-text haematological report.
Please extract the following information from the text and format it into a valid JSON object exactly as specified below.
For boolean fields, use true/false and for text fields, output the value exactly. If a field is not found or unclear, set it to false or "None" as appropriate.
Assume MDS is over 3 months ago unless stated otherwise.

Extract these fields:
"qualifiers": {{
    "previous_MDS_diagnosed_over_3_months_ago": false,
    "previous_MDS/MPN_diagnosed_over_3_months_ago": false,
    "previous_cytotoxic_therapy": None,
    "predisposing_germline_variant": "None"
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]
    """

    # Prompt #4: AML differentiation
    second_prompt = f"""
The previous haematological report needs to be evaluated for AML differentiation.
Using only data from morphology, histology, and flow cytometry (ignore any genetic or cytogenetic data),
suggest the most appropriate category of AML differentiation and convert that suggestion to the corresponding FAB classification code according to the mapping below:

    None: No differentiation mentioned
    M0: Acute myeloid leukaemia with minimal differentiation
    M1: Acute myeloid leukaemia without maturation
    M2: Acute myeloid leukaemia with maturation
    M3: Acute promyelocytic leukaemia
    M4: Acute myelomonocytic leukaemia
    M4Eo: Acute myelomonocytic leukaemia with eosinophilia
    M5a: Acute monoblastic leukaemia
    M5b: Acute monocytic leukaemia
    M6a: Acute erythroid leukaemia (erythroid/myeloid type)
    M6b: Pure erythroid leukaemia
    M7: Acute megakaryoblastic leukaemia

Return a JSON object with the key "AML_differentiation".
You may also provide a "differentiation_reasoning" key with bullet point logic.

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #5: Revised ELN24 genes
    eln2024_prompt = f"""
The user has pasted a free-text haematological report.
Please extract whether the following genes are mutated (true/false) or not mentioned (false).
For each gene, set the value to true if the text indicates that gene is mutated; otherwise false.

"ELN2024_risk_genes": {{
    "TP53": false,
    "KRAS": false,
    "PTPN11": false,
    "NRAS": false,
    "FLT3_ITD": false,
    "NPM1": false,
    "IDH1": false,
    "IDH2": false,
    "DDX41": false
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    # Prompt #6: Check if cytogenetic data is missing
    cytogenetics_check_prompt = f"""
The user has pasted a free-text haematological report.
Analyze whether the report contains any cytogenetic data or report. Examples of cytogenetic data include:
- Karyotype information
- FISH analysis results
- Any cytogenetic abnormalities (such as translocations, deletions, inversions)
- Mention of cytogenetic testing or analysis

Return a JSON object with a single key "no_cytogenetics_data" set to:
- true if the report does NOT contain any cytogenetic data or if cytogenetic testing is mentioned as "not performed"
- false if the report DOES contain cytogenetic data, even if it's just a normal karyotype

Return valid JSON only with this key and no extra text.

Here is the free-text haematological report to parse:

[START OF REPORT]

{report_text}

[END OF REPORT]   
    """

    try:
        # Parallelize the prompt calls
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1   = executor.submit(get_json_from_prompt, first_prompt_1)
            future2a  = executor.submit(get_json_from_prompt, first_prompt_2a)
            future2b  = executor.submit(get_json_from_prompt, first_prompt_2b)
            future2c  = executor.submit(get_json_from_prompt, first_prompt_2c)
            future3   = executor.submit(get_json_from_prompt, first_prompt_3)
            future4   = executor.submit(get_json_from_prompt, second_prompt)
            future_eln2024 = executor.submit(get_json_from_prompt, eln2024_prompt)
            future_cyto_check = executor.submit(get_json_from_prompt, cytogenetics_check_prompt)

            # Gather results when all are complete
            first_raw_1  = future1.result()
            first_raw_2a = future2a.result()
            first_raw_2b = future2b.result()
            first_raw_2c = future2c.result()
            first_raw_3  = future3.result()
            diff_data     = future4.result()
            eln2024_data  = future_eln2024.result()
            cyto_check_data = future_cyto_check.result()

        # Merge all data into one dictionary.
        parsed_data = {}
        parsed_data.update(first_raw_1)
        parsed_data.update(first_raw_2a)
        parsed_data.update(first_raw_2b)
        parsed_data.update(first_raw_2c)
        parsed_data.update(first_raw_3)
        parsed_data.update(diff_data)
        parsed_data.update(eln2024_data)
        parsed_data.update(cyto_check_data)

        # Ensure keys for AML_differentiation and reasoning exist.
        if "AML_differentiation" not in parsed_data:
            parsed_data["AML_differentiation"] = None
        if "differentiation_reasoning" not in parsed_data:
            parsed_data["differentiation_reasoning"] = None
        
        # Ensure no_cytogenetics_data field exists
        if "no_cytogenetics_data" not in parsed_data:
            parsed_data["no_cytogenetics_data"] = False

        # Fill missing keys from required structure.
        for key, val in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = val
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_val

        # Validate blasts_percentage.
        blasts = parsed_data.get("blasts_percentage")
        if blasts is None:
            parsed_data["blasts_percentage"] = "Unknown"
        elif blasts != "Unknown":
            if not isinstance(blasts, (int, float)) or not (0 <= blasts <= 100):
                st.error("❌ Invalid blasts_percentage value. Must be a number between 0 and 100.")
                return {}
        
        # Secondary detection of missing cytogenetic data
        # Check if any cytogenetic abnormalities were detected in the report
        has_cytogenetic_data = False
        
        # Check AML defining cytogenetic abnormalities
        for key, value in parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {}).items():
            if "::" in key and value == True:  # Only check for fusion genes (contain ::)
                has_cytogenetic_data = True
                break
        
        # Check MDS related cytogenetics
        if not has_cytogenetic_data:
            for key, value in parsed_data.get("MDS_related_cytogenetics", {}).items():
                if value == True:
                    has_cytogenetic_data = True
                    break
        
        # If we directly detected no cytogenetic abnormalities and the dedicated field isn't explicitly set to True,
        # we'll use our secondary detection method as a fallback
        if not has_cytogenetic_data and parsed_data.get("no_cytogenetics_data") is not True:
            # Only set to True if we have strong evidence cytogenetics are missing
            # Count how many cytogenetic keys were analyzed
            cyto_keys_total = len(parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})) + \
                              len(parsed_data.get("MDS_related_cytogenetics", {}))
            
            # If we have a significant number of keys and all are false, likely no cytogenetics data
            if cyto_keys_total > 30:  # We have over 50 cytogenetic keys total, so this is a reasonable threshold
                parsed_data["no_cytogenetics_data"] = True

        # Debug print
        print("Parsed Haematology Report JSON:")
        print(json.dumps(parsed_data, indent=2))
        return parsed_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse AI response into JSON. Ensure the report is well-formatted.")
        print("❌ JSONDecodeError: Could not parse AI JSON response.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI: {str(e)}")
        print(f"❌ Exception: {str(e)}")
        return {}
