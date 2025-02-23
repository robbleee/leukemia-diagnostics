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
    with all fields needed for classification, including AML differentiation.

    Returns:
        dict: A dictionary containing the extracted fields. Returns the dict with "blasts_percentage": "Unknown" if parsing fails to determine blast percentage.
    """
    # Safety check: if the user didn’t type anything, return an empty dict
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}

    # Updated required JSON structure with new markers
    required_json_structure = {
        "blasts_percentage": None,  # Changed from 0.0 to None
        "fibrotic": False,       # True if the report suggests MDS with fibrosis
        "hypoplasia": False,     # True if the report suggests MDS with hypoplasia
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
            # Additional / Uncommon markers:
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
        "AML_differentiation": None,  # New field added for AML differentiation
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": False,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
            "previous_cytotoxic_therapy": False,
            "predisposing_germline_variant": "None"
        }
    }

    # Construct the prompt with detailed instructions.
    prompt = f"""
The user has pasted a free-text hematological report.
Please extract the following fields from the text and format them into a valid JSON object exactly as specified below.
For boolean fields, use true/false. For numerical fields, provide the value. If a field is not found or unclear, set it to false or a default value.

Additionally, extract the AML differentiation classification field ("AML_differentiation") from the free text.
This field should be filled using the FAB classification system. If the free text provides the differentiation in the FAB format (e.g., "FAB M3") or using a descriptive/standard format (e.g., "Acute promyelocytic leukaemia" or "erythroid differentiation"), convert and record the corresponding FAB classification code according to the following mapping:

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

If the differentiation is not specified or cannot be determined, set the value to null. If for any reason you are unsure what to put (e.g. multiple are mentioned) then set value to "ambiguous"

Try to consider if the user may have used some sort of shorthand and translate where necessary.

For example:
1. 2_x_TP53_mutations: Extract if the report mentions phrases like "2 TP53 mutations," "biallelic TP53 mutations," or similar. We need at least 2 for it to be true.
2. 1_x_TP53_mutation_del_17p: This MUST be a TP53 mutation AND a deletion of 17p. They may be mentioned in different parts of the report.
3. 1_x_TP53_mutation_LOH: Identify phrases such as "TP53 mutation and LOH" or "TP53 mutation with Loss of Heterozygosity." Both conditions must be met.
4. AML_differentiation: Extract the AML differentiation classification and convert it to the appropriate FAB code based on the mapping above.
5. Complex_karyotype: Can be any combination of any three cytogenetic abnormalities, even if they're not MDS-related.

Only record an AML_defining_recurrent_genetic_abnormality as true if the report exactly mentions one of the abnormalities listed below:

    PML::RARA fusion
    NPM1 mutation
    RUNX1::RUNX1T1 fusion
    CBFB::MYH11 fusion
    DEK::NUP214 fusion
    RBM15::MRTFA fusion
    MLLT3::KMT2A fusion
    GATA2::MECOM rearrangement
    KMT2A rearrangement
    MECOM rearrangement
    NUP98 rearrangement
    CEBPA mutation (and if it is an in-frame bZIP mutation, then record "bZIP": true)
    BCR::ABL1 fusion

Additionally, consider the following markers (if mentioned exactly) as part of AML_defining_recurrent_genetic_abnormalities:

    IRF2BP2::RARA
    NPM1::RARA
    ZBTB16::RARA
    STAT5B::RARA
    STAT3::RARA
    RARA::TBL1XR1
    RARA::FIP1L1
    RARA::BCOR
    AFF1::KMT2A
    AFDN::KMT2A
    MLLT10::KMT2A
    TET1::KMT2A
    KMT2A::ELL
    KMT2A::MLLT1
    MYC::MECOM
    ETV6::MECOM
    MECOM::RUNX1
    PRDM16::RPN1
    NPM1::MLF1
    NUP98::NSD1
    NUP98::KMD5A
    ETV6::MNX1
    KAT6A::CREBBP
    PICALM::MLLT10
    FUS::ERG
    RUNX1::CBFA2T3
    CBFA2T3::GLIS2

For predisposing_germline_variant, leave as "None" if there is none; otherwise record the variant specified.

**Required JSON structure:**
{{
    "blasts_percentage": null,
    "fibrotic": False,
    "hypoplasia": False,
    "number_of_dysplastic_lineages": null,
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
    }},
    "AML_differentiation": null,
    "qualifiers": {{
        "previous_MDS_diagnosed_over_3_months_ago": false,
        "previous_MDS/MPN_diagnosed_over_3_months_ago": false,
        "previous_cytotoxic_therapy": false,
        "predisposing_germline_variant": "None"
    }}
}}

**Instructions:**
1. Return **valid JSON only** with no extra text or commentary.
2. Ensure all fields are present as specified.
3. If a field is not applicable or not mentioned, set it to false or null as appropriate.
4. Do not wrap the JSON in Markdown or any other formatting.

Here is the free-text hematological report to parse:
{report_text}
    """

    try:
        response = client.chat.completions.create(
            model="o3-mini",  # Adjust the model name as appropriate
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist who formats output strictly in JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_content = response.choices[0].message.content.strip()

        # Attempt to parse the JSON
        parsed_data = json.loads(raw_content)

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
        elif blasts != "Unknown": # Only validate if it's not already set to "Unknown" from previous parsing attempt
            if not isinstance(blasts, (int, float)) or not (0.0 <= blasts <= 100.0):
                st.error("❌ Invalid `blasts_percentage` value. It must be a number between 0 and 100.")
                return {} # Return empty dict if validation fails for numerical value


        # Validate AML_differentiation
        aml_diff = parsed_data.get("AML_differentiation")
        valid_fab_classes = [f"M{i}" for i in range(0, 8)]  # M0 to M7
        if aml_diff is not None:
            if not isinstance(aml_diff, str):
                st.error("❌ Invalid `AML_differentiation` value. It must be a string (e.g., 'FAB M3').")
                return {}
            elif not any(fab in aml_diff.upper() for fab in valid_fab_classes):
                st.warning("⚠️ `AML_differentiation` value does not match known FAB classifications.")

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