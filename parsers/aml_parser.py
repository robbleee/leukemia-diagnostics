import streamlit as st
import json
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

def parse_genetics_report_aml(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI using four separate prompts:
      1) Basic clinical numeric/boolean values,
      2) Genetic abnormalities,
      3) Qualifiers,
      4) AML differentiation.

    Then merges all four JSON objects into one dictionary. 
    No second pass is performed—each section's data is returned from its dedicated prompt.

    Returns:
        dict: A dictionary containing all fields needed for classification, 
              including 'AML_differentiation' and 'differentiation_reasoning'.
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
        }
    }

    # -------------------------------------------------------
    # Prompt #1: Basic clinical numeric & boolean values.
    # (Exact wording from "previous" code)
    # -------------------------------------------------------
    first_prompt_1 = f"""
The user has pasted a free-text hematological report.
Please extract the following fields from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false. For numerical fields, provide the value.
If a field is not found or unclear, set it to false (for booleans) or null (for numerical values).

Extract these fields:
- "blasts_percentage": (a numerical value between 0 and 100, or null if not found)
- "fibrotic": (true if the report suggests MDS with fibrosis; otherwise false)
- "hypoplasia": (true if the report suggests MDS with hypoplasia; otherwise false)
- "number_of_dysplastic_lineages": (an integer, or null if not found)

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #2: Genetic abnormalities.
    # (Exact wording from "previous" code)
    # -------------------------------------------------------
    first_prompt_2 = f"""
The user has pasted a free-text hematological report.
Please extract the following nested fields from the text and format them into a valid JSON object exactly as specified below.
Only record a genetic abnormality as true if the report exactly mentions it as described.
For boolean fields, use true/false.

Extract these nested fields:
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
}},
"Biallelic_TP53_mutation": {{
    "2_x_TP53_mutations": false,
    "1_x_TP53_mutation_del_17p": false,
    "1_x_TP53_mutation_LOH": false,
    "1_x_TP53_mutation_10_percent_vaf": false
}},
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

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #3: Qualifiers.
    # (Exact wording from "previous" code)
    # -------------------------------------------------------
    first_prompt_3 = f"""
The user has pasted a free-text hematological report.
Please extract the following nested fields under "qualifiers" from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false and for text fields, output the value exactly. If a field is not found or unclear, set it to false or "None" as appropriate.

Extract these fields:
"qualifiers": {{
    "previous_MDS_diagnosed_over_3_months_ago": false,
    "previous_MDS/MPN_diagnosed_over_3_months_ago": false,
    "previous_cytotoxic_therapy": None,
    "predisposing_germline_variant": "None"
}}

Return valid JSON only with these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #4: AML differentiation (including reasoning).
    # (Exact wording from "previous" code)
    # -------------------------------------------------------
    second_prompt = f"""
The previous hematological report needs to be evaluated for AML differentiation.
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

Report: {report_text}
    """

    try:
        # Gather data from each prompt (4 total).
        first_raw_1 = get_json_from_prompt(first_prompt_1)
        first_raw_2 = get_json_from_prompt(first_prompt_2)
        first_raw_3 = get_json_from_prompt(first_prompt_3)
        diff_data = get_json_from_prompt(second_prompt)

        # Merge all data into one dictionary.
        parsed_data = {}
        parsed_data.update(first_raw_1)
        parsed_data.update(first_raw_2)
        parsed_data.update(first_raw_3)
        parsed_data.update(diff_data)

        # Ensure keys for AML_differentiation and reasoning exist.
        if "AML_differentiation" not in parsed_data:
            parsed_data["AML_differentiation"] = None
        if "differentiation_reasoning" not in parsed_data:
            parsed_data["differentiation_reasoning"] = None

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
