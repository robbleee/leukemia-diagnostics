import streamlit as st
import json
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ----------------------------
# PARSE GENETICS AML
# ----------------------------
def parse_genetics_report_aml(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI and requests a structured JSON
    with all fields needed for classification. Note that the FAB classification for AML
    differentiation is not extracted in the first pass. Instead, a second pass is always
    executed to determine the AML differentiation along with a bullet point reasoning.
    
    Returns:
        dict: A dictionary containing the extracted fields, including "AML_differentiation" and
              "differentiation_reasoning". If parsing fails to determine blast percentage, the value
              will be set to "Unknown".
    """
    # Safety check: if the user didn’t type anything, return an empty dict
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}

    # Updated required JSON structure with new markers including differentiation_reasoning
    required_json_structure = {
        "blasts_percentage": None,  # Changed from 0.0 to None
        "fibrotic": False,         # True if the report suggests MDS with fibrosis
        "hypoplasia": False,       # True if the report suggests MDS with hypoplasia
        "number_of_dysplastic_lineages": None,  # integer or None
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
        "AML_differentiation": None,          # To be determined in the second pass
        "differentiation_reasoning": None,      # To store bullet point reasoning
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": False,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
            "previous_cytotoxic_therapy": False,
            "predisposing_germline_variant": "None"
        }
    }

    # First pass: extract all fields except AML_differentiation and differentiation_reasoning.
    # (Any AML_differentiation data from the report is disregarded.)
    first_prompt = f"""
The user has pasted a free-text hematological report.
Please extract the following fields from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false. For numerical fields, provide the value. If a field is not found or unclear, set it to false or a default value.
Ignore any FAB classification or AML differentiation details in the report.

**Required JSON structure (excluding AML_differentiation and differentiation_reasoning):**
{{
    "blasts_percentage": null,
    "fibrotic": false,
    "hypoplasia": false,
    "number_of_dysplastic_lineages": null,
    "AML_defining_recurrent_genetic_abnormalities": {{ ... }},
    "Biallelic_TP53_mutation": {{ ... }},
    "MDS_related_mutation": {{ ... }},
    "MDS_related_cytogenetics": {{ ... }},
    "AML_differentiation": null,
    "differentiation_reasoning": null,
    "qualifiers": {{ ... }}
}}

Here is the free-text hematological report to parse:
{report_text}
    """
    try:
        first_response = client.chat.completions.create(
            model="o3-mini",  # Adjust the model name as appropriate
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist who formats output strictly in JSON."},
                {"role": "user", "content": first_prompt}
            ]
        )
        first_raw = first_response.choices[0].message.content.strip()
        parsed_data = json.loads(first_raw)

        # Ensure all required fields are present; fill missing fields with defaults
        for key, value in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_value

        # Handle blasts_percentage and validation
        blasts = parsed_data.get("blasts_percentage")
        if blasts is None:
            parsed_data["blasts_percentage"] = "Unknown"
        elif blasts != "Unknown":
            if not isinstance(blasts, (int, float)) or not (0.0 <= blasts <= 100.0):
                st.error("❌ Invalid `blasts_percentage` value. It must be a number between 0 and 100.")
                return {}

        # Second pass: always run to determine AML_differentiation and differentiation_reasoning.
        second_prompt = f"""
The previous hematological report needs to be evaluated for AML differentiation.
Using only data from morphology, histology, and flow cytometry (ignore any genetic or cytogenetic data),
suggest the most appropriate category of AML differentiation and convert that suggestion to the corresponding FAB classification code according to the mapping below:

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

Return "ambiguous" if you are unsure.

Additionally, justify your differentiation decision using simple bullet points. Include only information relevant to the differentiation; add no additional text and do not mention the blast cell count.

Return a JSON object with the keys "AML_differentiation" and "differentiation_reasoning".
Report: {report_text}
        """
        second_response = client.chat.completions.create(
            model="o3-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist who returns valid JSON."},
                {"role": "user", "content": second_prompt}
            ]
        )
        second_raw = second_response.choices[0].message.content.strip()
        try:
            second_data = json.loads(second_raw)
            if "AML_differentiation" in second_data:
                parsed_data["AML_differentiation"] = second_data["AML_differentiation"]
            else:
                st.warning("Second pass did not return a valid AML_differentiation. Keeping original value.")
            if "differentiation_reasoning" in second_data:
                parsed_data["differentiation_reasoning"] = second_data["differentiation_reasoning"]
            else:
                st.warning("Second pass did not return valid differentiation_reasoning. Leaving it null.")
        except json.JSONDecodeError:
            st.error("❌ Failed to parse second pass response into JSON. Leaving AML_differentiation and differentiation_reasoning null.")

        # Print the parsed JSON object to stdout for debugging
        print("Parsed Haematology Report JSON:")
        print(json.dumps(parsed_data, indent=2))

        return parsed_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse the AI response into JSON. Please ensure the report is well-formatted.")
        print("❌ JSONDecodeError: Failed to parse AI response.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI: {str(e)}")
        print(f"❌ Exception: {str(e)}")
        return {}
