import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# AI REVIEW AML - CLASSIFICATION ONLY
##############################
def get_gpt4_review_aml_classification(classification: dict, user_inputs: dict) -> str:
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
    :param user_inputs: The parsed user data dict (not strictly needed for this prompt, 
        but included for consistency).
    :return: classification_review (str)
    """
    
    # Convert classification dict into a readable string:
    who_2022 = classification.get("WHO 2022", {})
    icc_2022 = classification.get("ICC 2022", {})

    who_class = who_2022.get("Classification", "")
    who_deriv = who_2022.get("Derivation", "")
    icc_class = icc_2022.get("Classification", "")
    icc_deriv = icc_2022.get("Derivation", "")

    # You can join derivation steps if it's a list
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

    # Create the prompt
    classification_prompt = f"""
You are a specialized medical AI. The user has provided the following hematological data:

    **Classification Result**: {classification}
    **Task**:
	1. Provide a quick review of the classification result 
	2. You should explain any differences that are present in diagnostic categories determined by WHO and ICC classifications
	3. If the blast cell percentage is at a borderline level for classification by either classification system then this should be discussed. For most cases the classification will require a blast count of 20%; however, for cases where a genetic lesion allows an AML at a lower blast percentage then consider that blast count instead.
	4. If genetic testing or cytogenetic test results are not present in the data you have been given then state this finding and consider any impact this may have on the classification.
	5. If these are stated in the reviewed information, please discuss the sample quality statement in the clinical report, the DNA quality metric in the genetic report, or the stated number of cells or metaphases considered in the cytogenetics report. Based on each of these values discuss any concerns around sample quality that you spot. If the aspirate is of poor quality then consider whether this may affect the representation of cells in the genetic sample and how it may affect VAF or sensitivity.
	6. If the VAF levels suggest the presence of subclones state this

    **Response**:
    - Be concise and professional.
    - Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamli frontend.
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
def get_gpt4_review_aml_genes(classification: dict, user_inputs: dict) -> str:
    """
    Sends user input data (parsed AML fields) to OpenAI for gene-level analysis.
    Emphasizes which genes were marked "True" and their clinical implications.
    
    :param classification: A dict like:
        {
            "WHO 2022": "Some classification",
            "ICC 2022": "Some classification"
        }
      (Here, we only need it if you want to mention classification in the prompt.)
    :param user_inputs: The parsed user data dict containing gene flags, blasts%, etc.
    :return: gene_review (str)
    """

    # Build a readable string of user inputs for the prompt
    # Only illustrate keys relevant to genes/positives, or everything if you prefer
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    gene_prompt = f"""
You are a specialized medical AI. The user has provided the following hematological data:

    {input_data_str}

	**Task**:
	Provide a section called Genetics Review.
	Please follow these rules: 
	1. Forget any gene or cytogenetic lists used in previous analyses and do not include that content in your answer.
	2. Use UK spelling.  Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction.
	3. If there are no mutated genes or cytogenetic change present then do not discuss any genes. Instead state that no genetic or cytogenetic lesions were detected using the procedures and panels employed in the testing and advise that the classification has been made on that basis. Suggest that MDT meetings should advise whether repeat or extended testing should be performed.
	4. Where genetic or cytogenetic lesions are found summarise the clinical implications for each positive finding in the above list. This discussion should assume a proven diagnosis of AML. The summary for each gene should use fewer than 200 words and be written to inform a medical professional using succinct language and only using peer reviewed content. The summary should emphasise the role of the listed genes or cytogenetic change on clinical outcome. 
	5. If outcome effects may be modified by other genes indicate this in bold lettering (except for gene names which remain in italic capital text). This action should particularly focus on the effects of any other genes on the provided input list. 
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
def get_gpt4_review_aml_mrd(classification: dict, user_inputs: dict) -> str:

    # Build a readable string of user inputs for the prompt
    # Only illustrate keys relevant to genes/positives, or everything if you prefer
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    mrd_prompt = f"""
    You are a specialized medical AI. The user has provided the following hematological data:

    {input_data_str}

	**Task**:
	Provide a section called MRD strategy
	Please follow these rules: 
	1. Use only the gene lists from this input data. 
	2. Use UK spelling.  Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction.
	3. Discuss only those genes from the list that are suitable for monitoring minimal residual disease in the UK. 
	4. Then for any gene that can be used to monitor MRD advise the appropriate monitoring recommendations used in the UK. The advice should be provided for a well-informed doctor wishing to monitor the patient and should be succinct but include time intervals and sample types. This should be performed separately for each identified target gene or cytogenetic lesion. The monitoring recommendation should use European LeukemiaNet MRD Working Party recommendations 2021 described in Blood. 2021 Dec 30;138(26):2753–2767. The summary for each gene should use fewer than 200 words and be written to inform a medical professional using succinct language and only using peer reviewed content. 
	5. Provide a maximum of 2 references that have high citation for each recommendation. 
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
        mrd_review = f"Error in gene review call: {str(e)}"

    return mrd_review


##############################
# AI REVIEW AML - ADDITIONAL COMMENTS
##############################
def get_gpt4_review_aml_additional_comments(classification: dict, user_inputs: dict) -> str:

    # Build a readable string of user inputs for the prompt
    # Only illustrate keys relevant to genes/positives, or everything if you prefer
    input_data_str = "Below is the AML data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key}: {value}\n"

    additional_comments_prompt = f"""
    You are a specialized medical AI. The user has provided the following hematological data:

    {input_data_str}

	**Task**:
	Provide a section called Additional Comments
	Please follow these rules: 
	1. Use only gene lists from this input data. 
	2. Use UK spelling.  Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other instruction.
	3. If the list is not empty then write a brief cautionary note advising users about each gene noting how frequently it is found in acute myeloid leukaemia, also consider how frequently it arises as a variant of uncertain significance. 
	4. If any gene in the list has a possible germline origin state this using a threshold of 0.3 (30%) and consider the implications of this. For genes that have possible germline origin consider whether the reported VAF is consistent with a germline origin. When discussing possible germline origin use the phrase “may support germline origin”.
	5. If TP53 has a single allele mutated consider whether there is also a 17p deletion present when interpreting the VAF result. If the case has biallelic mutations of TP53 then do not discuss the possibility of a 17p deletion.
	6. If the gene mutation may also occur in lymphoid cells or co-existent lymphoid neoplasms discuss this and advise that clinical features may be reviewed to determine “if there is any clinical suspicion”. 
	7. Do this separately for each gene using minimum text, aim for fewer that 100 words

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
