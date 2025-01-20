import streamlit as st
import json
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# PARSE GENETICS AML
##############################
def parse_genetics_report_aml(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI and requests a structured JSON
    with all fields needed for classification, including AML differentiation.
    
    Returns:
        dict: A dictionary containing the extracted fields. Returns an empty dict if parsing fails.
    """
    # Safety check: if the user didn’t type anything, return an empty dict
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}
    
    # Define the fields to extract
    required_json_structure = {
        "blasts_percentage": None,  # Changed from 0.0 to None
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1": False,
            "RUNX1::RUNX1T1": False,
            "CBFB::MYH11": False,
            "DEK::NUP214": False,
            "RBM15::MRTFA": False,
            "MLLT3::KMT2A": False,
            "GATA2:: MECOM": False,
            "KMT2A": False,
            "MECOM": False,
            "NUP98": False,
            "CEBPA": False,
            "bZIP": False,  
            "BCR::ABL1": False
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": False,
            "1_x_TP53_mutation_del_17p": False,
            "1_x_TP53_mutation_LOH": False
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
            "predisposing_germline_variant": None
        }
    }
    
    # Construct the prompt with detailed instructions
    prompt = f"""
        You are a specialized medical AI and a knowledgeable hematologist. The user has pasted a free-text hematological report. 
        Please extract the following fields from the text and format them into a valid JSON object exactly as specified below. 
        For boolean fields, use true/false. For numerical fields, provide the value. If a field is not found or unclear, set it to false or a default value.
        
        Additionally, extract the AML differentiation classification using the FAB (M0-M7) or WHO classification systems. If the classification is given in some other form then convert it to fab.
        If the differentiation is not specified, set the value to null.
        
        Try to consider if the user may have used some sort of shorthand and translate where necessary.
        
        **For example**:
        
        1. 2_x_TP53_mutations: Extract if the report mentions phrases like "2 TP53 mutations," "biallelic TP53 mutations," or similar.
        2. 1_x_TP53_mutation_del_17p: This needs to be a TP 53 mutation AND a del_17p. We need both.
        3. 1_x_TP53_mutation_LOH: Identify phrases such as "TP53 mutation and LOH," "TP53 mutation with Loss of Heterozygosity," or equivalent.
        4. AML_differentiation: Extract the AML differentiation classification, such as "FAB M3" or "WHO AML with myelodysplasia-related changes."
        
        Examples of predisposing germline variants:
            Germline predisposition
                • CEBPA 
                • DDX41 
                • TP53 
            Germline predisposition and pre-existing platelet disorder:
                • RUNX1
                • ANKRD26
                • ETV6 
            Germline predisposition and potential organ dysfunction:
                • GATA2
            Noonan syndrome-like disorders:
                • Down syndrome
                • SAMD9
                • BLM 
    
        Make sure to onle record AML_defining_recurrent_genetic_abnormalities if the abnorrmality pressent is the exact one mentioned in the list below:
            NPM1 mutation
            RUNX1::RUNX1T1
            CBFB::MYH11 fusion
            DEK::NUP214 fusion
            RBM15::MRTFA fusion
            MLLT3::KMT2A fusion
            KMT2A rearrangement
            MECOM rearrangement
            NUP98 rearrangement
            CEBPA / bZIP mutation
            BCR::ABL1 fusion

            For example:
            - "NPM1 mutation" -> "NPM1" = true
            - "No KMT2A rearrangement detected" -> "KMT2A" = false
            - "KMT2A amplification" alone is NOT the same as a rearrangement -> "KMT2A" = false
            - "RUNX1::RUNX1T1 fusion present" -> "RUNX1::RUNX1T1" = true

    
        For predisposing_germline_variant, leave as "None" if there is none otherwise record the variant specified.
        
        **Required JSON structure:**
        {{
            "blasts_percentage": null, 
            "AML_defining_recurrent_genetic_abnormalities": {{
                "NPM1": false,
                "RUNX1::RUNX1T1": false,
                "CBFB::MYH11": false,
                "DEK::NUP214": false,
                "RBM15::MRTFA": false,
                "MLLT3::KMT2A": false,
                "GATA2:: MECOM": false,
                "KMT2A": false,
                "MECOM": false,
                "NUP98": false,
                "CEBPA": false,
                "bZIP": false,
                "BCR::ABL1": false
            }},
            "Biallelic_TP53_mutation": {{
                "2_x_TP53_mutations": false,
                "1_x_TP53_mutation_del_17p": false,
                "1_x_TP53_mutation_LOH": false
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
            "AML_differentiation": "None"
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
        3. Use true/false for boolean values.
        4. If a field is not applicable or not mentioned, set it to false or null as appropriate.
        5. Do not wrap the JSON in Markdown or any other formatting.
        
        **Here is the free-text hematological report to parse:**
        {report_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Corrected model name
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist who formats output strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,  # Increased max_tokens to accommodate detailed JSON including AML differentiation
            temperature=0.0  # Deterministic output
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
        
        # Validate blasts_percentage
        blasts = parsed_data.get("blasts_percentage")
        if blasts is not None:
            if not isinstance(blasts, (int, float)) or not (0.0 <= blasts <= 100.0):
                st.error("❌ Invalid `blasts_percentage` value. It must be a number between 0 and 100.")
                return {}
        
        # Validate AML_differentiation
        aml_diff = parsed_data.get("AML_differentiation")
        valid_fab_classes = [f"M{i}" for i in range(0, 8)]  # M0 to M7
        if aml_diff is not None:
            if not isinstance(aml_diff, str):
                st.error("❌ Invalid `AML_differentiation` value. It must be a string representing the classification (e.g., 'FAB M3').")
                return {}
            elif not any(fab in aml_diff.upper() for fab in valid_fab_classes):
                st.warning("⚠️ `AML_differentiation` value does not match known FAB classifications.")
        
        # Print the parsed JSON object to stdout
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
