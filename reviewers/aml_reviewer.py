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
    Provide a section called Genetics Review that has a short paragraph for each and every positive genetic finding. 
    Please follow these rules:
    1. Use UK spelling.
    2. Summarise clinical implications of each gene in AML (under 200 words).
    3. Speak to a medical professional succinctly, referencing only peer-reviewed content.
    4. Emphasise how each gene affects disease outcome and monitoring.
    5. Whenever a gene name is used, it should appear in italic capital text (e.g., *FLT3*).
    6. State the likely effect on outcome in **bold lower case**, unless other genes modify the outcome. 
       In that case, also mention that in **bold lower case**.
    7. Provide three references with high citation counts.
    8. For any gene that can be used to monitor minimal residual disease (MRD) in the UK, put directly beneath the title (gene name)
       in bold but regular size text: "Can be used for MRD in the UK".

    **Response**:
    - Be concise and professional.
    - Structure your answer beautifully in Markdown but reduce heading size so that it looks good in streamli frontend.
    - Make sure that the individual gene headers are on their own line
    - No need to include references
    - Do not include "bold lower case"
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
            max_tokens=1000,
            temperature=0.00,
        )
        gene_review = gene_response.choices[0].message.content.strip()
    except Exception as e:
        gene_review = f"Error in gene review call: {str(e)}"

    # Return the two separate responses
    return classification_review, gene_review
