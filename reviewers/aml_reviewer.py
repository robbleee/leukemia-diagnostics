import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# AI REVIEW AML (Combined Output)
##############################
def get_gpt4_review_aml(
    classification: str,
    user_inputs: dict
) -> (str, str):
    """
    Sends the classification and user input data to OpenAI in two separate calls:
    1) Classification Review
    2) Gene Analysis
    
    Returns two separate strings: 
    - classification_review 
    - gene_review
    """

    # Create a readable string of user inputs
    input_data_str = "Below is the data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key.replace('_', ' ').capitalize()}: {value}\n"

    # -----------------------------
    # 1) Classification Review Prompt
    # -----------------------------
    classification_prompt = f"""
    You are a specialized medical AI. The user has provided the following hematological data:

    **Classification Result**: {classification}

    **Task**:
    Provide a quick review of the classification result focussing solely on any potential concerns 
    or inconsistencies you spot.

    **Response**:
    - Be concise and professional.
    - Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamli frontend.
    - Response should not be more than 200 words.
    """

    # -----------------------------
    # 2) Gene Analysis Prompt
    # -----------------------------
    gene_prompt = f"""
    You are a specialized medical AI. The user has provided the following hematological data:

    {input_data_str}

    **Task**:
    Provide a section called Genetics Review.
    Please follow these rules:
    1. Using UK spelling summarise the clinical implications for AML of each positive positive finding on in the above list. 
    2. Summarise each in less than 200 words talking to a medical professional using succinct language and only using 
       peer reviewed content emphasising effects on disease outcome and monitoring.
    3. Whenever a gene name is used this should be stated in capital letters and italic text irrespective of any other 
       instruction. 
    4. State the likely effect on outcome in bold lettering (except for gene names which remain
       in italic capital text). 
    5. If outcome effects may be modified by other genes indicate this in bold lettering (except for gene 
       names which remain in italic capital text). 
    6. Provide three references that have high citation for each gene.
    7. For each gene, if it can be used to monitor minimal residual disease (MRD) in the UK, state this in bold lettering below the title (gene name)

    **Response**:
    - Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamlit frontend.
    - Make sure that the individual gene headers are on their own line
    - Do not ever include anything like this "Certainly, here is the Genetics Review based on the provided data:"
    """

    # -----------------------------------
    # Call 1: Classification Review
    # -----------------------------------
    try:
        classification_response = client.chat.completions.create(
            model="gpt-4o",  
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": classification_prompt}
            ],
            max_tokens=600,
            temperature=0.00,
        )
        classification_review = classification_response.choices[0].message.content.strip()
    except Exception as e:
        classification_review = f"Error in classification review call: {str(e)}"

    # -----------------------------------
    # Call 2: Gene Analysis
    # -----------------------------------
    try:
        gene_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": gene_prompt}
            ],
            max_tokens=3000,
            temperature=0.00,
        )
        gene_review = gene_response.choices[0].message.content.strip()
    except Exception as e:
        gene_review = f"Error in gene review call: {str(e)}"

    # Return the two separate responses
    return classification_review, gene_review
