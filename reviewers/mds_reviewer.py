# File name: ai_review_mds.py

import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# AI REVIEW MDS - CLASSIFICATION ONLY
##############################
def get_gpt4_review_mds_classification(classification: dict, 
                                       manual_inputs: dict, 
                                       free_text_input: str = None) -> str:
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
    :param manual_inputs: The parsed user data dict (blasts%, cytopenias, genetic findings, etc.).
    :param free_text_input: A single string containing all user-provided free text (notes, reports, etc.).
    :return: classification_review (str)
    """

    # Extract WHO/ICC details
    who_2022 = classification.get("WHO 2022", {})
    icc_2022 = classification.get("ICC 2022", {})

    who_class = who_2022.get("Classification", "")
    who_deriv = who_2022.get("Derivation", "")
    icc_class = icc_2022.get("Classification", "")
    icc_deriv = icc_2022.get("Derivation", "")

    # If derivation is a list, join it neatly
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
""".strip()

    # Include free-text input if present
    if free_text_input:
        free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n"
    else:
        free_text_str = ""

    # Construct the prompt
    classification_prompt = f"""
**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: 
{classification_text}

**Task**: 
1. Under the heading “Classification Review,” summarise any significant differences in the classification given by WHO and ICC. Note how these differences might influence the clinical interpretation for Myelodysplastic Syndromes. 
2. Under the heading “Sample Quality,” comment on whether the presence or absence of genetic/cytogenetic data (or morphological data) influences confidence in this classification. If sample adequacy or missing data could alter the classification, mention it.

**Response**:
- Use UK English spelling.
- Provide only the headings “Classification Review” and “Sample Quality” (in bold) with succinct text under each.
- Structure your answer beautifully in markdown with smaller headings (**<heading**>) for a Streamlit UI. no more than 150 words total.
- Do not use bold anywhere except for the exact headings.
"""

    # Call OpenAI
    try:
        classification_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist experienced in MDS."},
                {"role": "user", "content": classification_prompt}
            ],
            max_tokens=600,
            temperature=0.0,
        )
        classification_review = classification_response.choices[0].message.content.strip()
    except Exception as e:
        classification_review = f"Error in classification review call: {str(e)}"

    return classification_review


##############################
# AI REVIEW MDS - GENE ANALYSIS ONLY
##############################
def get_gpt4_review_mds_genes(classification: dict, 
                              manual_inputs: dict, 
                              free_text_input: str = None) -> str:
    """
    Sends user MDS data to OpenAI for gene/cytogenetic-level analysis.
    Focus on how detected mutations or abnormalities affect prognosis and classification.

    :param classification: Dict with MDS classification results ("WHO 2022", "ICC 2022").
    :param manual_inputs: Dict with parsed MDS data (blasts, cytopenias, mutated genes, etc.).
    :param free_text_input: Extra text from user (if any).
    :return: A "Gene Analysis" section in formatted Markdown.
    """

    # Build a readable string of user inputs
    input_data_str = "Below is the MDS data the user provided:\n"
    for key, value in manual_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    if free_text_input:
        free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n"
    else:
        free_text_str = ""

    gene_prompt = f"""
**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification}

**Task**:
Provide a section called Genetics Review for Myelodysplastic Syndromes (MDS). 
Follow these rules:
1. Use UK spelling. 
2. If mutated genes or cytogenetic changes are detected, summarise their known significance in MDS (e.g. prognostic impact, association with specific MDS subtypes). 
3. Keep each gene/abnormality explanation under ~200 words, addressing a professional clinical audience.
4. If no genetic/cytogenetic lesions are reported, simply state that none were detected and that classification is based on morphological or other available data alone.
5. Provide up to three well-cited references per gene/abnormality.

**Response**:
- Structure your answer beautifully in markdown with smaller headings (**<heading**>) for a Streamlit UI.
- Begin with the heading “Genetics Review” (not bold). 
- Each gene or cytogenetic finding should be italicised in capital letters (e.g. *TP53*) and placed at the start of a new line as a subheading.
- Do not add extraneous text like "Certainly, here is the analysis..."
- Do not provide a concluding summary beyond the gene-by-gene detail.
"""

    # Call OpenAI
    try:
        gene_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist experienced in MDS."},
                {"role": "user", "content": gene_prompt}
            ],
            max_tokens=3000,
            temperature=0.0,
        )
        gene_review = gene_response.choices[0].message.content.strip()
    except Exception as e:
        gene_review = f"Error in gene review call: {str(e)}"

    return gene_review


##############################
# AI REVIEW MDS - ADDITIONAL COMMENTS
##############################
def get_gpt4_review_mds_additional_comments(classification: dict, 
                                            manual_inputs: dict, 
                                            free_text_input: str = None) -> str:
    """
    Provides a short "Additional Comments" section for MDS, 
    focusing on further considerations not covered in classification or gene analysis.

    :param classification: Classification data (WHO/ICC).
    :param manual_inputs: Parsed MDS data dict (including genes, blasts, cytopenias, etc.).
    :param free_text_input: Additional user free-text input (like clinical notes).
    :return: A short additional comments review (str).
    """

    input_data_str = "Below is the MDS data the user provided:\n"
    for key, value in manual_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n" if free_text_input else ""

    additional_comments_prompt = f"""
**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification}

**Task**:
Provide a section called Additional Considerations for MDS.
1. Use UK spelling.
2. Keep it short (<150 words).
3. If relevant, comment on factors such as risk scoring (e.g. IPSS-R or IPSS-M), coexisting cytopenias, or how certain genetics might affect management pathways. 
4. If no further detail is necessary, simply state that there are no additional comments.

**Response**:
- Structure your answer beautifully in markdown with smaller headings (**<heading**>) for a Streamlit UI.
- Title it “Additional Considerations” (not bold).
- Do not add extra flourish or disclaimers at the end.
- Keep it succinct and professional.
"""

    # Call OpenAI
    try:
        additional_comments_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist experienced in MDS."},
                {"role": "user", "content": additional_comments_prompt}
            ],
            max_tokens=3000,
            temperature=0.0,
        )
        additional_comments_review = additional_comments_response.choices[0].message.content.strip()
    except Exception as e:
        additional_comments_review = f"Error in additional comments review call: {str(e)}"

    return additional_comments_review
