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
                                       manual_inputs: dict, 
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
    :param manual_inputs: The parsed user data dict.
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

**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification_text}

**Task**: 
1. Using the heading: “Classification Review”. State any significant differences in the classification of this case given by WHO and ICC focussing particularly on the genetic elements of this classification if present. 
2. Using the heading: “Sample Quality”. If genetic testing or cytogenetic test results are not present in the provided data, then state any impact this may have on the classification. If these are stated in the reviewed information, please discuss the sample quality statement for clinical report, DNA quality metric and the cytogenetics report. Based on each of these values discuss any concerns around sample quality. If the morphology report suggests poor sample quality, then consider whether this may affect the representation of cells in the genetic sample and how it may affect VAF or sensitivity. 

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
                              manual_inputs: dict, 
                              free_text_input: str = None) -> str:
    """
    Sends user input data (parsed AML fields) to OpenAI for gene-level analysis.
    Emphasizes which genes were marked "True" and their clinical implications.
    
    :param classification: A dict with "WHO 2022" / "ICC 2022" classification results.
    :param manual_inputs: The parsed user data dict containing gene flags, blasts%, etc.
    :param free_text_input: A single string containing all user-provided free text.
    :return: gene_review (str)
    """

    # Build a readable string of user inputs
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in manual_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    # Include extra text if provided
    free_text_str = ""
    if free_text_input:
        free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n"

    gene_prompt = f"""
**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification}

**Task**:
Provide a section called Genetics Review.
Please follow these rules: 
1. Use UK spelling.  Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction.
2. If there are no mutated genes or cytogenetic change present then do not discuss any genes. Instead state that no genetic or cytogenetic lesions were detected using the procedures and panels employed in the testing and advise that the classification has been made on that basis. Suggest that MDT meetings should advise whether repeat or extended testing should be performed.
3. Where genetic or cytogenetic lesions are found summarise the clinical implications for each positive finding in the above list. This discussion should assume a proven diagnosis of AML. The summary for each gene should use fewer than 200 words and be written to inform a medical professional using succinct language and only using peer reviewed content. The summary should emphasise the role of the listed genes or cytogenetic change on clinical outcome. 
4. If outcome effects may be modified by other genes indicate this in bold lettering (except for gene names which remain in italic capital text). This action should consider only the effects of any other genes on the provided input list. 
6. Provide three references that have high citation for each gene. 
7. For each gene, if it can be used to monitor minimal residual disease (MRD) in the UK, state this in bold lettering below the title (gene name) 

**Response**:
- Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamlit frontend.
- Make sure that the individual gene headers are on their own line
- Do not ever include anything like this "Certainly, here is the Genetics Review based on the provided data:"
- Do not attempt to provide an overview summary after the written sections
- Do not provide suggestions about treatment approaches or general statements about the value of monitoring MRD
- When structuring your response place those mutations that have greater clinical impact first in your output
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
                            manual_inputs: dict, 
                            free_text_input: str = None) -> str:
    """
    Provides MRD strategy commentary based on the user’s AML data.
    
    :param classification: Classification data (WHO/ICC).
    :param manual_inputs: Parsed user data dict containing gene/cytogenetic details.
    :param free_text_input: A string of any additional free-text user input.
    :return: mrd_review (str)
    """
    
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in manual_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n" if free_text_input else ""

    mrd_prompt = f"""

**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification}


**Task**:
Provide a section called MRD strategy

Please follow these rules: 
1. Use only the gene and cytogenetic lists from this input data. 
2. Use UK spelling. Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction. 
2. Discuss only those genes from the list that are suitable for monitoring minimal residual disease in the UK. 
3. Then for any gene that can be used to monitor MRD advise the appropriate monitoring recommendations used in the UK. The advice should be provided for a well-informed doctor wishing to monitor the patient and should be succinct but include time intervals and sample types. This should be performed separately for each identified target gene or cytogenetic lesion. The monitoring recommendation should use European LeukemiaNet MRD Working Party recommendations 2021 described in Blood. 2021 Dec 30;138(26):2753–2767. The summary for each gene should use fewer than 200 words and be written to inform a medical professional using succinct language and only using peer reviewed content. Do not mention genes present in the list but not detected in this case. 
4. If a cytogenetic lesion is recommended for monitoring as a marker of disease response or can be used as such then discuss that cytogenetic lesion too. 
5. Provide a maximum of 2 references that have high citation for each recommendation. 

**Response**: 
- Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamlit frontend. - Make sure that the individual gene headers are on their own line 
- Do not ever include anything like this "Certainly, here is the Genetics Review based on the provided data:" 
- Do not attempt to provide an overview summary after the written sections
 - Do not provide suggestions about treatment approaches or general statements about the value of monitoring MRD 
- When structuring your response place those mutations that are suitable for MRD monitoring first in your output 
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
                                            manual_inputs: dict, 
                                            free_text_input: str = None) -> str:
    """
    Provides a short "Additional Comments" section focusing on gene frequency, possible germline origin, etc.

    :param classification: Classification data (WHO/ICC).
    :param manual_inputs: Parsed user data dict (genes, blasts, etc.).
    :param free_text_input: Additional user free-text input (overrides, extra details).
    :return: A short additional comments review (str).
    """

    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in manual_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    free_text_str = f"\n**Additional User Entered Text**:\n{free_text_input}\n" if free_text_input else ""

    additional_comments_prompt = f"""
**Free text inputs:** {free_text_input}
**Manual inputs**: {manual_inputs}
**Classification Result**: {classification}

**Task**:
Provide a section called Additional Considerations
Please follow these rules: 
1. Use only genes only listed in the input data. 
2. Use UK spelling.  Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction.
3. If the list does not detect any mutated genes simply state that there are no genes to review. 
4. If mutated genes are detected do the following for each gene using concise language and <150 words:
a. State how frequently the gene is mutated in acute myeloid leukaemia
b. if the VAF levels are significantly lower than other mutated genes consider if the mutated gene may be a subclone. If it is unlikely to be a subclone do mention this in the review.
C. If any mutated gene is frequently associated with germline mutation state whether the VAF supports this and advise appropriately.
d. If TP53 has a single allele mutated consider whether there is also a 17p deletion present when interpreting the VAF result. If the case has biallelic mutations of TP53 then do not discuss the possibility of a 17p deletion.
e. If mutation of the discussed gene is frequently seen in lymphoid cells then state this and advise on possible action. Do this only if the gene is frequently mutated in lymphoid cells.

**Response**:
- Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamlit frontend.
- Make sure that the individual gene headers are on their own line
- Do not ever include anything like this "Certainly, here is the Genetics Review based on the provided data:"
- Do not attempt to provide an overview summary after the written sections
- Do not provide suggestions about treatment approaches or general statements about the value of monitoring MRD
- When structuring your response place those mutations that are suitable for MRD monitoring first in your output
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
