import streamlit as st
import json
from openai import OpenAI

##############################
# PARSE AML RESPONSE (ELN 2022)
##############################
def parse_aml_response_report(report_text: str) -> dict:
    """
    Sends the free-text AML response assessment report to OpenAI
    and requests a structured JSON object with the fields needed
    for the classify_AML_Response_ELN2022 function.

    The required JSON structure includes:
    {
      "AdequateSample": false,
      "BoneMarrowBlasts": null,
      "BloodCountsProvided": false,
      "Platelets": null,
      "Neutrophils": null,
      "PreviouslyAchievedCR_CRh_Cri": false,
      "BlastsDecreaseBy50Percent": false,
      "TNCBetween5And25": false
    }

    If a field is not mentioned, default to a suitable type (e.g., false for booleans, null for numbers).
    Returns:
        dict: A dictionary containing the response fields, or empty dict if parsing fails.
    """
    if not report_text.strip():
        st.warning("Empty AML response report text received.")
        return {}

    # Define the fields we need
    required_json_structure = {
        "AdequateSample": False,
        "BoneMarrowBlasts": None,
        "BloodCountsProvided": False,
        "Platelets": None,
        "Neutrophils": None,
        "PreviouslyAchievedCR_CRh_Cri": False,
        "BlastsDecreaseBy50Percent": False,
        "TNCBetween5And25": False
    }

    # Build the prompt with instructions
    prompt = f"""
    You are a specialized medical AI and a knowledgeable hematologist. The user has pasted a free-text AML response assessment report.
    Please parse it into a valid JSON object with the exact keys below (no extra keys). 
    Booleans should be true or false. Numeric fields should be integers or floats. Use null if unknown. 

    **Required JSON structure**:
    {{
      "AdequateSample": false,
      "BoneMarrowBlasts": null,
      "BloodCountsProvided": false,
      "Platelets": null,
      "Neutrophils": null,
      "PreviouslyAchievedCR_CRh_Cri": false,
      "BlastsDecreaseBy50Percent": false,
      "TNCBetween5And25": false
    }}

    -----------
    - AdequateSample: set true if the text indicates sample is adequate; false otherwise.
    - BoneMarrowBlasts: numeric bone marrow blasts percentage (0-100).
    - BloodCountsProvided: set true if the text suggests blood counts (platelets, neutrophils) are available.
    - Platelets: numeric (e.g., 50, 100, 120...). Use null if not provided or unknown.
    - Neutrophils: numeric (e.g., 0.5, 1.0...). Use null if not provided.
    - PreviouslyAchievedCR_CRh_Cri: set true if the text indicates the patient previously reached CR/CRh/CRi, else false.
    - BlastsDecreaseBy50Percent: set true if the text indicates blasts have decreased by at least 50%.
    - TNCBetween5And25: set true if the text indicates total nucleated cells in the range 5–25 x10^9/L, else false.

    **Important**: 
    1. Output valid JSON **only** with these keys, no extra commentary or keys.
    2. If a field is not mentioned or unclear, use default or null.

    **Here is the free-text AML response report**:
    {report_text}
    """

    # Instantiate your OpenAI client (e.g., st.secrets["openai"]["api_key"])
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    try:
        # Send to GPT
        response = client.chat.completions.create(
            model="gpt-4",  # or the model you prefer
            messages=[
                {"role": "system", "content": "You are a medical AI that returns valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000,
            temperature=0.0
        )
        raw_content = response.choices[0].message.content.strip()

        # Attempt JSON parse
        parsed_data = json.loads(raw_content)

        # Ensure required fields are present; fill missing with default
        for key, default_val in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = default_val

        # Basic validation
        # AdequateSample, BloodCountsProvided, PreviouslyAchievedCR_CRh_Cri, BlastsDecreaseBy50Percent, TNCBetween5And25 => booleans
        bool_fields = [
            "AdequateSample",
            "BloodCountsProvided",
            "PreviouslyAchievedCR_CRh_Cri",
            "BlastsDecreaseBy50Percent",
            "TNCBetween5And25"
        ]
        for field in bool_fields:
            if field in parsed_data and not isinstance(parsed_data[field], bool):
                st.warning(f"{field} must be a boolean. Setting it to false.")
                parsed_data[field] = False

        # Numeric fields
        numeric_fields = ["BoneMarrowBlasts", "Platelets", "Neutrophils"]
        for field in numeric_fields:
            val = parsed_data.get(field, None)
            if val is not None:
                try:
                    # allow float
                    val = float(val)
                    # ensure bone marrow blasts, platelets, neutrophils >= 0
                    if val < 0:
                        val = None
                except ValueError:
                    val = None
            parsed_data[field] = val

        # Print to stdout (debug)
        print("Parsed AML Response Report JSON:")
        print(json.dumps(parsed_data, indent=2))

        return parsed_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse the AI response into JSON for AML response. Check formatting.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI for AML response parse: {str(e)}")
        return {}