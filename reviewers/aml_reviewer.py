import streamlit as st
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

##############################
# AI REVIEW AML
##############################
def get_gpt4_review_aml(
    classification: str,
    user_inputs: dict
) -> str:
    """
    Sends the classification, explanation, and all user input data to AI
    for review and next steps.
    """
    # Create a readable string of user inputs
    input_data_str = "Below is the data the user provided:\n"
    for key, value in user_inputs.items():
        input_data_str += f"- {key.replace('_', ' ').capitalize()}: {value}\n"

    # Build the final prompt with refined structure
    prompt = f"""
    You are a specialized medical AI. The user has provided the following hematological data:

    {input_data_str}

    **Classification Result**: {classification}

    **Task**:
    1. Provide a quick review of the classification result, highlighting any potential concerns or inconsistencies.
    2. Suggest clinically relevant next steps for further evaluation or management.

    **Response should be concise and professional. It should also be beautifully structured in markdown.**
    """

    # Send to AI
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Ensure your environment supports this model
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.2,
            n=1,
            stop=None
        )
        review = response.choices[0].message.content.strip()
        return review
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"
