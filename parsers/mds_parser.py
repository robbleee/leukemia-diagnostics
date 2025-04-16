import streamlit as st
import json
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# PARSE GENETICS MDS
##############################
def parse_genetics_report_mds(report_text: str) -> dict:
    """
    Parses free-text haematological/cytogenetics reports specifically for MDS classification
    under WHO 2022. Returns a dict containing relevant fields.
    """
    if not report_text.strip():
        st.warning("Empty MDS report text received.")
        return {}
    
    # Fields needed for MDS classification under WHO 2022
    required_json_structure = {
        "blasts_percentage": None,
        "fibrotic": False,       # True if the report suggests MDS with fibrosis
        "hypoplasia": False,     # True if the report suggests MDS with hypoplasia
        "number_of_dysplastic_lineages": None,  # integer or None
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": False,
            "1_x_TP53_mutation_del_17p": False,
            "1_x_TP53_mutation_LOH": False
        },
        "MDS_related_mutation": {
            "SF3B1": False
        },
        "MDS_related_cytogenetics": {
            "del_5q": False
        },
        "qualifiers": {
            "previous_cytotoxic_therapy": False,
            "predisposing_germline_variant": None
        }
    }

    # Build the prompt
    prompt = f"""
    You are a specialized medical AI with knowledge of MDS classification.
    Please read the free-text report below and extract the following fields
    as valid JSON. If a field is not mentioned, default to false or null.
    Do not add extra keys or text. Use exact key names and structure.

    Required JSON structure:
    {{
      "blasts_percentage": null,
      "fibrotic": false,
      "hypoplasia": false,
      "number_of_dysplastic_lineages": null,
      "Biallelic_TP53_mutation": {{
          "2_x_TP53_mutations": false,
          "1_x_TP53_mutation_del_17p": false,
          "1_x_TP53_mutation_LOH": false
      }},
      "MDS_related_mutation": {{
          "SF3B1": false
      }},
      "MDS_related_cytogenetics": {{
          "del_5q": false
      }},
      "qualifiers": {{
          "previous_cytotoxic_therapy": false,
          "predisposing_germline_variant": null
      }}
    }}

    **Instructions**:
    1. Return valid JSON only with no extra commentary or keys.
    2. Convert user shorthand to boolean or numeric fields where appropriate.
    3. "fibrotic" => True if the text suggests marrow fibrosis for MDS.
    4. "hypoplasia" => True if the text suggests hypoplastic MDS.
    5. "number_of_dysplastic_lineages" => integer 1, 2, or 3 if the text indicates single/multi-lineage dysplasia.
    6. "blasts_percentage" => numeric blasts percentage, or null if unknown.
    7. For biallelic TP53 mutation, set the relevant booleans to true if indicated.
    8. For "SF3B1" => true if there's mention of SF3B1 mutation.
    9. For "del_5q" => true if there's mention of isolated 5q- or del(5q).
    10. "qualifiers" => set to true or specify the germline variant if it’s present, else false/null.

    **Here is the free-text report to parse**:
    {report_text}
    """

    # Replace `YOUR_OPENAI_API_KEY` or use st.secrets as appropriate
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",  # or whichever model you prefer
            messages=[
                {"role": "system", "content": "You are a helpful medical AI that returns valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.0
        )
        raw_content = response.choices[0].message.content.strip()

        # Attempt to parse the JSON
        parsed_data = json.loads(raw_content)

        # Ensure required structure
        for key, default_val in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = default_val
            elif isinstance(default_val, dict):
                # check sub-fields
                for sub_key, sub_val in default_val.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_val

        # Optional validation for blasts percentage
        blasts = parsed_data.get("blasts_percentage")
        if blasts is not None and blasts != "":
            try:
                blasts = float(blasts)
            except ValueError:
                blasts = None
            if blasts is not None and (blasts < 0 or blasts > 100):
                st.warning("Blasts percentage out of range (0–100). Setting to null.")
                blasts = None
            parsed_data["blasts_percentage"] = blasts

        # Optional validation for number_of_dysplastic_lineages
        dys_lineages = parsed_data.get("number_of_dysplastic_lineages")
        if dys_lineages is not None:
            try:
                dys_lineages = int(dys_lineages)
            except ValueError:
                dys_lineages = None
            if dys_lineages not in [0,1,2,3]:
                # If the text suggests single lineage, multi-lineage, or ring sideroblasts, etc.
                # we might guess but let's just set it to None if invalid
                dys_lineages = None
            parsed_data["number_of_dysplastic_lineages"] = dys_lineages

        return parsed_data
    
    except json.JSONDecodeError:
        st.error("❌ Failed to parse the AI response into JSON for MDS report.")
        return {}
    except Exception as e:
        st.error(f"❌ Error in MDS parsing: {str(e)}")
        return {}
