import streamlit as st
import bcrypt
import json
import graphviz
from parsers.aml_parser import parse_genetics_report_aml
from parsers.mds_parser import parse_genetics_report_mds
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022
from reviewers.aml_reviewer import get_gpt4_review_aml
from reviewers.mds_reviewer import get_gpt4_review_mds
from openai import OpenAI


##############################
# SET PAGE CONFIGURATION FIRST
##############################
st.set_page_config(page_title="Haematologic Classification", layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''


##############################
# AUTHENTICATION
##############################
def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verifies a provided password against the stored hashed password using bcrypt.
    """
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticates a user by username and password.
    """
    users = st.secrets["auth"]["users"]
    for user in users:
        if user["username"] == username:
            return verify_password(user["hashed_password"], password)
    return False

def login_logout():
    """
    Displays login/logout controls in the sidebar.
    """
    if st.session_state['authenticated']:
        st.sidebar.markdown(f"### Logged in as **{st.session_state['username']}**")
        if st.sidebar.button("Logout"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = ''
            st.sidebar.success("Logged out successfully!")
    else:
        st.sidebar.header("Login for AI Features")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.sidebar.success("Logged in successfully!")
            else:
                st.sidebar.error("Invalid username or password")

login_logout()


##############################
# APP AML SECTION
##############################
def app_aml_section():
    st.subheader("Acute Myeloid Leukemia (AML) Classification")
    st.markdown("""
    Enter the **full** hematological and cytogenetics reports in the text boxes below. 
    The AI will extract key fields, and classification will proceed based on the extracted data.
    """)

    # 1) Manual Input for Myeloid Blast Percentage
    blast_input = st.text_input(
        label="Myeloid Blasts Percentage (AML)", 
        placeholder="e.g. 25",
        help="Enter the myeloid blasts percentage. This overrides any value extracted from the reports."
    )

    # 2) Two Text Areas for the Reports
    hematology_report = st.text_area(
        "Genetics Report (AML):", 
        height=100, 
        help="Paste the complete hematology report from laboratory results."
    )

    cytogenetics_report = st.text_area(
        "Cytogenetics Report (AML):", 
        height=100, 
        help="Paste the complete cytogenetics report from laboratory results."
    )

    # 3) Button to Parse & Classify
    if st.button("Parse & Classify AML from Free-Text"):
        combined_report = f"{hematology_report}\n\n{cytogenetics_report}"
        if combined_report.strip():
            with st.spinner("Extracting data for AML classification..."):
                # Parse the report
                parsed_fields = parse_genetics_report_aml(combined_report)

                # If the user supplied a blasts percentage, override it
                if blast_input.strip():
                    try:
                        blasts_value = float(blast_input.strip())
                        parsed_fields["blasts_percentage"] = blasts_value
                        st.info(f"Using manually entered blasts_percentage = {blasts_value}")
                    except ValueError:
                        st.warning("Invalid number entered for blasts percentage. Using parsed value if available.")

                if not parsed_fields:
                    st.warning("No data extracted or an error occurred during parsing.")
                    return

                # 4) Classify using WHO 2022 and ICC 2022
                classification_who, who_derivation = classify_AML_WHO2022(parsed_fields)
                classification_icc, icc_derivation = classify_AML_ICC2022(parsed_fields)

            # 5) Check for error messages
            if classification_who.startswith("Error:"):
                st.error(classification_who)
            else:
                # --- Show the extracted JSON data (Collapsed by Default) ---
                with st.expander("### **View Extracted AML Values**", expanded=False):
                    st.json(parsed_fields)


                # 6) Display Classifications
                st.markdown("""
                <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                    <h3 style='color: #0f5132;'>Classification Results</h3>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("### **WHO 2022 Classification**")
                    st.markdown(f"**Classification:** {classification_who}")

                with col2:
                    st.markdown("### **ICC 2022 Classification**")
                    st.markdown(f"**Classification:** {classification_icc}")

                # 7) Show derivations side-by-side
                col_who, col_icc = st.columns(2)
                with col_who:
                    with st.expander("🔍 WHO 2022 Derivation", expanded=False):
                        who_derivation_markdown = "\n\n".join(
                            [f"**Step {idx}:** {step}"
                             for idx, step in enumerate(who_derivation, start=1)]
                        )
                        st.markdown(who_derivation_markdown)

                with col_icc:
                    with st.expander("🔍 ICC 2022 Derivation", expanded=False):
                        icc_derivation_markdown = "\n\n".join(
                            [f"**Step {idx}:** {step}"
                             for idx, step in enumerate(icc_derivation, start=1)]
                        )
                        st.markdown(icc_derivation_markdown)

                # 8) AI Review & Clinical Next Steps (Optional)
                if st.session_state.get('authenticated', False):
                    with st.spinner("Generating AI review and clinical next steps..."):
                        combined_classifications = {
                            "WHO 2022": {"Classification": classification_who},
                            "ICC 2022": {"Classification": classification_icc}
                        }
                        gpt4_review_result = get_gpt4_review_aml(
                            classification=combined_classifications,
                            user_inputs=parsed_fields
                        )
                    st.info(gpt4_review_result)
                else:
                    st.info("🔒 **Log in** to receive an AI-generated review and clinical recommendations.")

                # Final Disclaimer
                st.markdown("""
                ---
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                    <p><strong>Disclaimer:</strong> This app is a simplified demonstration and <strong>not</strong> a replacement 
                    for professional pathology review or real-world WHO/ICC classification.</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("Please provide at least one of the AML-related reports.")


##############################
# APP MDS SECTION
##############################
def app_mds_section():
    st.subheader("Myelodysplastic Syndromes (MDS) Classification")

    st.markdown("""
    Enter the MDS-specific data in the fields below. 
    The AI will parse or use your overrides, then classify using WHO 2022 and ICC 2022.
    """)

    # 1) Manual Input for Myeloid Blast Percentage
    mds_blast_input = st.text_input(
        label="Myeloid Blasts Percentage (MDS)",
        placeholder="e.g. 8",
        help="Overrides the blasts value from the text report if provided."
    )

    # 2) Text areas for MDS genetics & cytogenetics
    mds_genetics_report = st.text_area(
        "Genetics / Mutation Findings (MDS):",
        height=100,
        help="Paste or summarize genetic findings relevant to MDS."
    )

    mds_cytogenetics_report = st.text_area(
        "Cytogenetics / Karyotype (MDS):",
        height=100,
        help="Paste or summarize cytogenetic data relevant to MDS."
    )

    # Combine them for parsing
    combined_mds_report = f"{mds_genetics_report}\n\n{mds_cytogenetics_report}"

    # 3) Parse & Classify button
    if st.button("Parse & Classify MDS"):
        if combined_mds_report.strip():
            with st.spinner("Parsing MDS data..."):
                parsed_mds_fields = parse_genetics_report_mds(combined_mds_report)

                # Override blasts if user typed them
                if mds_blast_input.strip():
                    try:
                        override_blasts = float(mds_blast_input.strip())
                        parsed_mds_fields["blasts_percentage"] = override_blasts
                        st.info(f"Overridden blasts_percentage = {override_blasts}")
                    except ValueError:
                        st.warning("Invalid blasts percentage for MDS. Using parsed value.")

                if not parsed_mds_fields:
                    st.warning("No data extracted or an error occurred during MDS parsing.")
                    return

            # 4) Classify WHO & ICC
            with st.spinner("Classifying MDS WHO & ICC..."):
                classification_who, derivation_who = classify_MDS_WHO2022(parsed_mds_fields)
                classification_icc, derivation_icc = classify_MDS_ICC2022(parsed_mds_fields)

            # 5) Display results
            st.markdown("""
            <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                <h3 style='color: #0f5132;'>MDS Classification Results</h3>
            </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### **WHO 2022 Classification**")
                st.write(classification_who)

            with col2:
                st.markdown("### **ICC 2022 Classification**")
                st.write(classification_icc)

            # 6) Show derivations side-by-side
            col_who, col_icc = st.columns(2)
            with col_who:
                with st.expander("🔍 WHO 2022 Derivation", expanded=False):
                    who_derivation_markdown = "\n\n".join(
                        [f"**Step {i}:** {step}" for i, step in enumerate(derivation_who, 1)]
                    )
                    st.markdown(who_derivation_markdown)

            with col_icc:
                with st.expander("🔍 ICC 2022 Derivation", expanded=False):
                    icc_derivation_markdown = "\n\n".join(
                        [f"**Step {i}:** {step}" for i, step in enumerate(derivation_icc, 1)]
                    )
                    st.markdown(icc_derivation_markdown)

            # Show parsed JSON
            with st.expander("View Extracted MDS Values", expanded=False):
                st.json(parsed_mds_fields)

            # Optional AI review
            if st.session_state.get("authenticated", False):
                with st.spinner("Generating AI review and next steps..."):
                    combined_mds_classifications = {
                        "WHO 2022": {"Classification": classification_who},
                        "ICC 2022": {"Classification": classification_icc}
                    }
                    # Or pass them individually
                    review_result = get_gpt4_review_mds(
                        classification=combined_mds_classifications,
                        user_inputs=parsed_mds_fields
                    )
                st.info(review_result)
            else:
                st.info("🔒 **Log in** to receive an AI-generated review and recommendations.")

            # Disclaimer
            st.markdown("""
            ---
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                <p><strong>Disclaimer:</strong> This app is a simplified demonstration and <strong>not</strong> a replacement 
                for professional pathology review or real-world WHO/ICC classification.</p>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.error("Please provide MDS genetics and/or cytogenetics report.")


##############################
# APP MAIN
##############################
def app_main():
    st.title("Haematologic Classification Tool")

    if st.session_state.get("authenticated", False):
        # Choose which classification to perform
        classification_choice = st.radio("Select classification type:", ("AML", "MDS"))

        if classification_choice == "AML":
            app_aml_section()
        else:
            app_mds_section()

    else:
        st.info("🔒 **Log in** to use the classification features.")

    st.markdown("---")


##############################
# MAIN FUNCTION
##############################
def main():
    app_main()


if __name__ == "__main__":
    main()