import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# AI REVIEW AML - CLASSIFICATION ONLY
##############################
def get_gpt4_review_aml_classification(classification: dict, 
                                       user_inputs: dict, 
                                       free_text_input: str = None) -> str:
    """
    Sends the AML classification (WHO / ICC) to OpenAI for a short 'classification review.'
    
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
    :param user_inputs: The parsed user data dict.
    :param free_text_input: A single string containing all user-provided free text (overrides, notes, etc.).
    :return: classification_review (str)
    """
    
    # Convert classification dict into a readable string:
    who_2022 = classification.get("WHO 2022", {})
    icc_2022 = classification.get("ICC 2022", {})

    who_class = who_2022.get("Classification", "")
    who_deriv = who_2022.get("Derivation", "")
    icc_class = icc_2022.get("Classification", "")
    icc_deriv = icc_2022.get("Derivation", "")

    # Join derivations if they're lists
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

    # Include extra text if provided
    free_text_str = ""
    if free_text_input:
        free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n"

    # Create the prompt
    classification_prompt = f"""


**Classification Result**: {classification_text}

**Task**: 
1. Using the heading: “Classification Review”. State any significant differences in the classification of this case given by WHO and ICC focussing particularly on the genetic elements of this classification if present. 
2. Using the heading: “Sample Quality”. If genetic testing or cytogenetic test results are not present in the provided data, then state any impact this may have on the classification. If these are stated in the reviewed information, please discuss the sample quality statement for clinical report, DNA quality metric and the cytogenetics report. Based on each of these values discuss any concerns around sample quality. If the aspirate is of poor quality, then consider whether this may affect the representation of cells in the genetic sample and how it may affect VAF or sensitivity. 
3. Using the heading: “Additional notes” Do not use bullet points. (1) In the first part of your answer consider whether any mutation present may worsen the prognostic impact of the classification. If prognosis is not worsened, then do not discuss it. (2) In the second part of your answer consider the gene list and identify any that may be inherited (constitutive) considering both the gene and the VAF levels. Your answer to this part should be brief and restricted only to genes that are likely to be constitutively mutated. 
**Response**: 
- Be concise and professional. Provide only the headings stated. Headings should be in bold type followed by a colon, then the text should follow on the next line. - Use UK English spelling. The text elements should not use bold font at any point. 
- Format in Markdown with smaller headings for a Streamlit UI.

- Response should not be more than 150 words. 
"""



    # Call OpenAI
    try:
        classification_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
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
# AI REVIEW AML - GENE ANALYSIS ONLY
##############################
def get_gpt4_review_aml_genes(classification: dict, 
                              user_inputs: dict, 
                              free_text_input: str = None) -> str:
    """
    Sends user input data (parsed AML fields) to OpenAI for gene-level analysis.
    Emphasizes which genes were marked "True" and their clinical implications.
    
    :param classification: A dict with "WHO 2022" / "ICC 2022" classification results.
    :param user_inputs: The parsed user data dict containing gene flags, blasts%, etc.
    :param free_text_input: A single string containing all user-provided free text.
    :return: gene_review (str)
    """

    # Build a readable string of user inputs
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    # Include extra text if provided
    free_text_str = ""
    if free_text_input:
        free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n"

    gene_prompt = f"""
You are a specialized medical AI. The user has provided the following hematological data:

{input_data_str}
{free_text_str}

**Task**:
Provide a section called "Genetics Review" adhering to these rules:
1. Use UK spelling. Whenever a gene name is used, write it in capital letters and *italic text*.
2. If no mutated genes/cytogenetic changes are present, simply note no genetic lesions detected and suggest whether retesting is needed.
3. If there are mutations/cytogenetic lesions, summarize implications for each finding (assume a confirmed AML).
4. Use fewer than 200 words per gene, be succinct and peer-reviewed in tone.
5. If outcome effects are modified by another gene from the input list, bold that note (keep gene name in *italic capitals*).
6. Provide three references for each gene.
7. For each gene that can be used for MRD monitoring in the UK, explicitly state this in **bold** beneath the gene name.

**Response**:
- Structure in Markdown with smaller headings (Streamlit-friendly).
- Do NOT provide an overall summary beyond the gene discussions.
- Prioritize genes with higher clinical impact first.
"""

    # Call OpenAI
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
        gene_review = f"Error in gene review call: {str(e)}"

    return gene_review


##############################
# AI REVIEW AML - MRD ONLY
##############################
def get_gpt4_review_aml_mrd(classification: dict, 
                            user_inputs: dict, 
                            free_text_input: str = None) -> str:
    """
    Provides MRD strategy commentary based on the user’s AML data.
    
    :param classification: Classification data (WHO/ICC).
    :param user_inputs: Parsed user data dict containing gene/cytogenetic details.
    :param free_text_input: A string of any additional free-text user input.
    :return: mrd_review (str)
    """
    
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n" if free_text_input else ""

    mrd_prompt = f"""
You are a specialized medical AI. The user has provided the following hematological data:

{input_data_str}
{free_text_str}

**Task**:
Provide a section called "MRD strategy" following these rules:
1. Use only the genes from the input to discuss MRD applicability in the UK.
2. Use UK spelling, with gene names in capital letters and italic text.
3. For each MRD-applicable gene, advise time intervals and sample types (succinct, <200 words) referencing European LeukemiaNet MRD Working Party (Blood. 2021 Dec 30;138(26):2753–2767).
4. Provide max 2 references per gene.
5. Do not provide an overview summary, only the per-gene discussion.

**Response**:
- Format in Markdown with smaller headings.
- Do NOT provide general treatment approaches or overall summary at the end.
- ONLY mention relevant genes that we have a POSITIVE result for. If no genes mentioned just
  Respond that no relevant genes were positive.
"""

    # Call OpenAI
    try:
        mrd_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": mrd_prompt}
            ],
            max_tokens=3000,
            temperature=0.0,
        )
        mrd_review = mrd_response.choices[0].message.content.strip()
    except Exception as e:
        mrd_review = f"Error in MRD review call: {str(e)}"

    return mrd_review


##############################
# AI REVIEW AML - ADDITIONAL COMMENTS
##############################
def get_gpt4_review_aml_additional_comments(classification: dict, 
                                            user_inputs: dict, 
                                            free_text_input: str = None) -> str:
    """
    Provides a short "Additional Comments" section focusing on gene frequency, possible germline origin, etc.

    :param classification: Classification data (WHO/ICC).
    :param user_inputs: Parsed user data dict (genes, blasts, etc.).
    :param free_text_input: Additional user free-text input (overrides, extra details).
    :return: A short additional comments review (str).
    """

    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n" if free_text_input else ""

    additional_comments_prompt = f"""
You are a specialized medical AI. The user has provided the following hematological data:

{input_data_str}
{free_text_str}

**Task**:
Provide a section called "Additional Comments" following these rules:
1. Only use the genes from this input.
2. Use UK spelling, with gene names in capital letters and italic text.
3. If no genes are present, do not discuss them—simply note that none were found.
4. For each gene, note frequency in AML, possibility of variant of uncertain significance.
5. If a gene "may support germline origin" (VAF ~30%), mention it.
6. If TP53 is single-allele mutated, consider whether 17p deletion is also present. If biallelic TP53, do not mention 17p deletion possibility.
7. If a gene also arises in lymphoid cells, advise to check clinical suspicion.
8. Keep each gene’s comment <100 words.

**Response**:
- Format in Markdown with smaller headings.
- No extra summary beyond the per-gene statements.
- No MRD or treatment approach suggestions.
"""

    # Call OpenAI
    try:
        additional_comments_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": additional_comments_prompt}
            ],
            max_tokens=3000,
            temperature=0.0,
        )
        additional_comments_review = additional_comments_response.choices[0].message.content.strip()
    except Exception as e:
        additional_comments_review = f"Error in additional comments review call: {str(e)}"

    return additional_comments_review
