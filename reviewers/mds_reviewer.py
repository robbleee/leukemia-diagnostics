import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# AI REVIEW MDS - CLASSIFICATION ONLY
##############################
def get_gpt4_review_mds_classification(classification: dict, user_inputs: dict) -> str:
    """
    Sends the MDS classification (WHO / ICC) to OpenAI for a short 'classification review.'
    
    :param classification: A dict like:
        {
            "WHO 2022": {
                "Classification": "...",
                "Derivation": [...]
            },
            "ICC 2022": {
                "Classification": "...",
                "Derivation": [...]
            }
        }
    :param user_inputs: The parsed user data dict (not strictly necessary for this prompt, 
        but included for consistency).
    :return: classification_review (str) – a concise summary of the classification result.
    """
    
    # Convert classification dict into a readable string
    who_2022 = classification.get("WHO 2022", {})
    icc_2022 = classification.get("ICC 2022", {})

    who_class = who_2022.get("Classification", "")
    who_deriv = who_2022.get("Derivation", "")
    icc_class = icc_2022.get("Classification", "")
    icc_deriv = icc_2022.get("Derivation", "")

    # Convert derivations if they are lists
    if isinstance(who_deriv, list):
        who_deriv = "\n".join(who_deriv)
    if isinstance(icc_deriv, list):
        icc_deriv = "\n".join(icc_deriv)

    classification_text = f"""
**WHO 2022**:
Classification: {who_class}
Derivation: {who_deriv}

**ICC 2022**:
Classification: {icc_class}
Derivation: {icc_deriv}
"""

    # Build prompt
    classification_prompt = f"""
You are a specialized medical AI focusing on Myelodysplastic Syndromes (MDS). 
The user has provided the following classification details:

{classification_text}

**Task**:
1. Provide a quick review of this classification result, highlighting any potential concerns or inconsistencies.
2. Suggest clinically relevant next steps for further evaluation or management.

**Response**:
- Use a professional, concise tone (≤ 200 words).
- Structure in Markdown with smaller headings (suitable for Streamlit).
"""

    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": classification_prompt}
            ],
            max_tokens=600,
            temperature=0.2,
        )
        classification_review = response.choices[0].message.content.strip()
    except Exception as e:
        classification_review = f"Error in MDS classification review call: {str(e)}"

    return classification_review


##############################
# AI REVIEW MDS - GENE / CYTOGENETIC ANALYSIS
##############################
def get_gpt4_review_mds_genes(classification: dict, user_inputs: dict) -> str:
    """
    Sends user input data (parsed MDS fields) to OpenAI for a gene/cytogenetic-level review.
    Focus on what was actually found (marked True) and discuss the clinical relevance briefly.
    
    :param classification: 
        e.g. { "WHO 2022": "MDS with excess blasts-1", "ICC 2022": "MDS-EB1", ... }
        (Not strictly required, but you may incorporate classification references if desired.)
    :param user_inputs: The parsed user data dict containing flags for MDS-related genes, blasts %, etc.
    :return: gene_review (str) – a summary of the relevant gene/cytogenetic findings.
    """

    # Build a readable summary of the user inputs
    input_data_str = "The user provided these MDS findings:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    # Customize instructions for MDS genes / cytogenetics
    gene_prompt = f"""
You are a specialized medical AI focusing on Myelodysplastic Syndromes (MDS). 
Here is the patient's MDS data, including any gene/cytogenetic findings:

{input_data_str}

**Task**:
Provide a 'Gene & Cytogenetic Review' section that:
1. Identifies which genes/cytogenetic abnormalities (if any) are flagged as true/positive.
2. Summarises their clinical implications (prognostic impact, treatment considerations, etc.) succinctly 
   (≤ 200 words per abnormality).
3. Use UK spelling and a professional tone.
4. When referencing a specific gene name, display it in *italic capital letters* (e.g. *TP53*).
5. Highlight outcome impacts with **bold** text.
6. Provide 2-3 relevant references for each positive gene/abnormality.
7. If no positive findings, return 'No significant gene/cytogenetic findings identified.'
8. Structure your answer in Markdown with smaller headings (suitable for Streamlit).

**Response**:
- Do not begin with 'Certainly' or 'Here is the review:' – just provide the direct content.
"""

    try:
        gene_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": gene_prompt}
            ],
            max_tokens=3000,
            temperature=0.0,
        )
        gene_review = gene_response.choices[0].message.content.strip()
    except Exception as e:
        gene_review = f"Error in MDS gene review call: {str(e)}"

    return gene_review
