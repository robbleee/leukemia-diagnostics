"""
AML Treatment Parser
Extracts specific data fields required for the AML treatment recommendations algorithm.
Based on the consensus guideline approach by Tom Coats et al.
"""

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
            {"role": "system", "content": "You are a knowledgeable haematologist who returns valid JSON for treatment planning."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = response.choices[0].message.content.strip()
    return json.loads(raw)

def parse_treatment_data(report_text: str) -> dict:
    """
    Extracts data fields required for AML treatment recommendations from medical reports.
    
    Uses parallel OpenAI prompts to extract:
    1) Patient qualifiers and clinical history
    2) Flow cytometry data (CD33 status)
    3) AML-defining recurrent genetic abnormalities
    4) MDS-related mutations
    5) MDS-related cytogenetics
    6) Morphologic features (dysplastic lineages)
    7) Cytogenetic data availability
    
    Args:
        report_text (str): Free-text medical report
        
    Returns:
        dict: Structured data for treatment algorithm
    """
    # Safety check
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}

    # Required structure for treatment algorithm
    required_structure = {
        "qualifiers": {
            "therapy_related": False,
            "previous_chemotherapy": False,
            "previous_radiotherapy": False,
            "previous_MDS": False,
            "previous_MPN": False,
            "previous_MDS/MPN": False,
            "previous_CMML": False,
            "relapsed": False,
            "refractory": False,
            "secondary": False
        },
        "cd33_positive": None,
        "cd33_percentage": None,
        "AML_defining_recurrent_genetic_abnormalities": {
            "RUNX1_RUNX1T1": False,
            "t_8_21": False,
            "CBFB_MYH11": False,
            "inv_16": False,
            "t_16_16": False,
            "NPM1_mutation": False,
            "FLT3_ITD": False,
            "FLT3_TKD": False,
            "PML_RARA": False
        },
        "MDS_related_mutation": {
            "FLT3": False,
            "ASXL1": False,
            "BCOR": False,
            "EZH2": False,
            "RUNX1": False,
            "SF3B1": False,
            "SRSF2": False,
            "STAG2": False,
            "U2AF1": False,
            "ZRSR2": False,
            "UBA1": False,
            "JAK2": False
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": False,
            "-5": False,
            "del_5q": False,
            "-7": False,
            "del_7q": False,
            "-17": False,
            "del_17p": False
        },
        "number_of_dysplastic_lineages": None,
        "no_cytogenetics_data": False
    }

    # Define prompts
    qualifiers_prompt = f"""
Extract clinical history and qualifiers from this haematological report.
Return JSON with boolean values for each field:

"qualifiers": {{
    "therapy_related": false,           # True if AML is therapy-related
    "previous_chemotherapy": false,     # True if prior chemotherapy mentioned
    "previous_radiotherapy": false,     # True if prior radiation mentioned
    "previous_MDS": false,              # True if previous MDS mentioned
    "previous_MPN": false,              # True if previous MPN mentioned
    "previous_MDS/MPN": false,          # True if previous MDS/MPN mentioned
    "previous_CMML": false,             # True if previous CMML mentioned
    "relapsed": false,                  # True if relapsed AML
    "refractory": false,                # True if refractory AML
    "secondary": false                  # True if secondary AML
}}

Report: {report_text}
    """

    flow_prompt = f"""
Extract CD33 flow cytometry data from this report.
Return JSON:

"cd33_positive": null,      # true/false/null
"cd33_percentage": null     # 0-100 or null

Report: {report_text}
    """

    genetics_prompt = f"""
Extract AML-defining genetic abnormalities from this report.
Return JSON:

"AML_defining_recurrent_genetic_abnormalities": {{
    "RUNX1_RUNX1T1": false,    # t(8;21) or RUNX1-RUNX1T1
    "t_8_21": false,           # t(8;21)
    "CBFB_MYH11": false,       # inv(16) or CBFB-MYH11
    "inv_16": false,           # inv(16)
    "t_16_16": false,          # t(16;16)
    "NPM1_mutation": false,    # NPM1 mutation
    "FLT3_ITD": false,         # FLT3-ITD
    "FLT3_TKD": false,         # FLT3-TKD
    "PML_RARA": false          # PML-RARA (APL)
}}

Report: {report_text}
    """

    mds_prompt = f"""
Extract MDS-related mutations and cytogenetics from this report.
Return JSON:

"MDS_related_mutation": {{
    "FLT3": false,
    "ASXL1": false,
    "BCOR": false,
    "EZH2": false,
    "RUNX1": false,
    "SF3B1": false,
    "SRSF2": false,
    "STAG2": false,
    "U2AF1": false,
    "ZRSR2": false,
    "UBA1": false,
    "JAK2": false
}},
"MDS_related_cytogenetics": {{
    "Complex_karyotype": false,
    "-5": false,
    "del_5q": false,
    "-7": false,
    "del_7q": false,
    "-17": false,
    "del_17p": false
}}

Report: {report_text}
    """

    morphology_prompt = f"""
Extract morphologic features and cytogenetic data availability from this report.
Return JSON:

"number_of_dysplastic_lineages": null,  # 0-3 or null
"no_cytogenetics_data": false          # true if no cytogenetic data

Report: {report_text}
    """

    try:
        # Run prompts in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future1 = executor.submit(get_json_from_prompt, qualifiers_prompt)
            future2 = executor.submit(get_json_from_prompt, flow_prompt)
            future3 = executor.submit(get_json_from_prompt, genetics_prompt)
            future4 = executor.submit(get_json_from_prompt, mds_prompt)
            future5 = executor.submit(get_json_from_prompt, morphology_prompt)

            # Get results
            qualifiers_data = future1.result()
            flow_data = future2.result()
            genetics_data = future3.result()
            mds_data = future4.result()
            morphology_data = future5.result()

        # Merge data
        parsed_data = {}
        parsed_data.update(qualifiers_data)
        parsed_data.update(flow_data)
        parsed_data.update(genetics_data)
        parsed_data.update(mds_data)
        parsed_data.update(morphology_data)

        # Post-process CD33 data
        cd33_percentage = parsed_data.get("cd33_percentage")
        if cd33_percentage is not None and parsed_data.get("cd33_positive") is None:
            parsed_data["cd33_positive"] = cd33_percentage >= 20

        # Fill missing fields with defaults
        for key, val in required_structure.items():
            if key not in parsed_data:
                parsed_data[key] = val
            elif isinstance(val, dict):
                if key not in parsed_data:
                    parsed_data[key] = {}
                for sub_key, sub_val in val.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_val

        return validate_treatment_data(parsed_data)

    except Exception as e:
        st.error(f"❌ Parsing error: {str(e)}")
        return {}

def validate_treatment_data(parsed_data: dict) -> dict:
    """
    Validate and clean the parsed treatment data.
    
    Args:
        parsed_data (dict): Raw parsed data
        
    Returns:
        dict: Validated and cleaned data
    """
    if not parsed_data:
        return {}

    # Validate CD33 percentage
    cd33_percentage = parsed_data.get("cd33_percentage")
    if cd33_percentage is not None:
        if not isinstance(cd33_percentage, (int, float)) or not (0 <= cd33_percentage <= 100):
            st.warning("⚠️ Invalid CD33 percentage value. Setting to None.")
            parsed_data["cd33_percentage"] = None
            parsed_data["cd33_positive"] = None

    # Validate dysplastic lineages
    dysplastic_lineages = parsed_data.get("number_of_dysplastic_lineages")
    if dysplastic_lineages is not None:
        if not isinstance(dysplastic_lineages, int) or not (0 <= dysplastic_lineages <= 3):
            st.warning("⚠️ Invalid number of dysplastic lineages. Setting to None.")
            parsed_data["number_of_dysplastic_lineages"] = None

    return parsed_data

def display_treatment_parsing_results(parsed_data: dict):
    """
    Display the parsed treatment data in Streamlit interface.
    
    Args:
        parsed_data (dict): Parsed treatment data
    """
    if not parsed_data:
        st.error("❌ No treatment data was successfully parsed.")
        return

    st.markdown("### Parsed Treatment Data")
    
    # Clinical History
    with st.expander("📋 Clinical History & Qualifiers", expanded=True):
        qualifiers = parsed_data.get("qualifiers", {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Disease History:**")
            history_items = []
            if qualifiers.get("previous_MDS"):
                history_items.append("Previous MDS")
            if qualifiers.get("previous_MPN"):
                history_items.append("Previous MPN")
            if qualifiers.get("previous_MDS/MPN"):
                history_items.append("Previous MDS/MPN")
            if qualifiers.get("previous_CMML"):
                history_items.append("Previous CMML")
            
            if history_items:
                for item in history_items:
                    st.markdown(f"• {item}")
            else:
                st.markdown("• None detected")
        
        with col2:
            st.markdown("**Treatment History:**")
            treatment_items = []
            if qualifiers.get("therapy_related"):
                treatment_items.append("Therapy-related AML")
            if qualifiers.get("previous_chemotherapy"):
                treatment_items.append("Previous chemotherapy")
            if qualifiers.get("previous_radiotherapy"):
                treatment_items.append("Previous radiotherapy")
            
            if treatment_items:
                for item in treatment_items:
                    st.markdown(f"• {item}")
            else:
                st.markdown("• None detected")
            
            st.markdown("**Disease Status:**")
            status_items = []
            if qualifiers.get("relapsed"):
                status_items.append("Relapsed")
            if qualifiers.get("refractory"):
                status_items.append("Refractory")
            if qualifiers.get("secondary"):
                status_items.append("Secondary AML")
            
            if status_items:
                for item in status_items:
                    st.markdown(f"• {item}")
            else:
                st.markdown("• Newly diagnosed")

    # Flow Cytometry
    with st.expander("🔬 Flow Cytometry (CD33)", expanded=True):
        cd33_positive = parsed_data.get("cd33_positive")
        cd33_percentage = parsed_data.get("cd33_percentage")
        
        if cd33_percentage is not None:
            st.markdown(f"**CD33 Expression:** {cd33_percentage}%")
            status = "Positive" if cd33_percentage >= 20 else "Negative"
            st.markdown(f"**CD33 Status:** {status} (≥20% threshold)")
        elif cd33_positive is not None:
            status = "Positive" if cd33_positive else "Negative"
            st.markdown(f"**CD33 Status:** {status}")
        else:
            st.markdown("**CD33 Status:** Not reported")

    # Genetic Abnormalities
    with st.expander("🧬 Genetic Abnormalities", expanded=True):
        aml_genes = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        mds_mutations = parsed_data.get("MDS_related_mutation", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**AML-Defining Abnormalities:**")
            aml_found = []
            for gene, present in aml_genes.items():
                if present:
                    aml_found.append(gene)
            
            if aml_found:
                for gene in aml_found:
                    st.markdown(f"• {gene}")
            else:
                st.markdown("• None detected")
        
        with col2:
            st.markdown("**MDS-Related Mutations:**")
            mds_found = []
            for gene, present in mds_mutations.items():
                if present:
                    mds_found.append(gene)
            
            if mds_found:
                for gene in mds_found:
                    st.markdown(f"• {gene}")
            else:
                st.markdown("• None detected")

    # Cytogenetics
    with st.expander("🧮 Cytogenetic Data", expanded=True):
        mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
        no_cyto_data = parsed_data.get("no_cytogenetics_data", False)
        
        if no_cyto_data:
            st.markdown("**⚠️ No cytogenetic data available**")
        else:
            st.markdown("**MDS-Related Cytogenetic Abnormalities:**")
            cyto_found = []
            for abnormality, present in mds_cyto.items():
                if present:
                    cyto_found.append(abnormality)
            
            if cyto_found:
                for abnormality in cyto_found:
                    st.markdown(f"• {abnormality}")
            else:
                st.markdown("• None detected")

    # Morphology
    with st.expander("🔍 Morphologic Features", expanded=True):
        dysplastic_lineages = parsed_data.get("number_of_dysplastic_lineages")
        
        if dysplastic_lineages is not None:
            st.markdown(f"**Dysplastic Lineages:** {dysplastic_lineages}")
        else:
            st.markdown("**Dysplastic Lineages:** Not reported")

    # Raw data for debugging
    with st.expander("🔧 Raw Parsed Data (Debug)", expanded=False):
        st.json(parsed_data)


def demo_treatment_recommendation_workflow(report_text: str, patient_age: int = None):
    """
    Demo function showing how to use the treatment parser with the recommendations algorithm.
    
    Args:
        report_text (str): Medical report text
        patient_age (int): Patient's age
    """
    st.markdown("## Treatment Recommendation Workflow Demo")
    
    # Step 1: Parse the report
    st.markdown("### Step 1: Parse Medical Report")
    with st.spinner("Parsing report data..."):
        parsed_data = parse_treatment_data(report_text)
    
    if not parsed_data:
        st.error("❌ Failed to parse report data.")
        return
    
    # Step 2: Display parsed results
    st.markdown("### Step 2: Parsed Data")
    display_treatment_parsing_results(parsed_data)
    
    # Step 3: Get treatment recommendations
    st.markdown("### Step 3: Treatment Recommendations")
    
    if patient_age is None:
        patient_age = st.number_input("Enter patient age:", min_value=18, max_value=100, value=65, step=1)
    
    if st.button("Generate Treatment Recommendation") or patient_age:
        try:
            # Import the treatment recommendation function
            from utils.aml_treatment_recommendations import get_consensus_treatment_recommendation, display_treatment_recommendations
            
            # Get ELN risk (simplified for demo)
            eln_risk = "Intermediate"  # This would normally be calculated
            
            # Get recommendations
            recommendation = get_consensus_treatment_recommendation(parsed_data, patient_age, eln_risk)
            
            # Display recommendations
            display_treatment_recommendations(parsed_data, eln_risk, patient_age)
            
        except ImportError:
            st.error("❌ Treatment recommendation module not available.")
        except Exception as e:
            st.error(f"❌ Error generating recommendations: {str(e)}")


# Example usage
if __name__ == "__main__":
    # This would be called from the main Streamlit app
    sample_report = """
    Patient: 65-year-old male with acute myeloid leukemia
    
    Flow cytometry shows 75% blasts with CD33 positive expression in 85% of cells.
    
    Cytogenetics: t(8;21)(q22;q22) RUNX1-RUNX1T1 fusion detected.
    
    Molecular: NPM1 mutation detected. FLT3-ITD negative.
    
    History: No prior chemotherapy or radiation. No evidence of prior MDS.
    """
    
    demo_treatment_recommendation_workflow(sample_report, 65) 