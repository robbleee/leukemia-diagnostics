import streamlit as st
import bcrypt
import openai
import graphviz

# -----------------------------
# SET PAGE CONFIGURATION FIRST
# -----------------------------
st.set_page_config(page_title="Hematologic Classification", layout="wide")

##############################
# OPENAI API CONFIG
##############################
openai.api_key = st.secrets["openai"]["api_key"]

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

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''

def login_logout():
    """
    Displays login/logout controls in the sidebar.
    """
    if st.session_state['authenticated']:
        st.sidebar.markdown(f"### Logged in as **{st.session_state['username']}**")
        if st.sidebar.button("Logout"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = ''
            st.experimental_rerun()
    else:
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.sidebar.error("Invalid username or password")

login_logout()

##############################
# HELPER FUNCTIONS
##############################
def log_derivation(
    blasts: float,
    lineage: str,
    decision_points: list,
    additional_info: list
) -> str:
    """
    Builds a verbose derivation string explaining how classification decisions were made.
    """
    derivation = ""
    derivation += f"<strong>Blasts Observed:</strong> {blasts}%. This percentage is crucial for differentiating acute vs. chronic leukemias.<br>"
    derivation += f"<strong>Lineage Determination:</strong> The chosen lineage is <strong>{lineage}</strong>, guiding the next steps.<br><br>"

    if decision_points:
        derivation += "<strong>Key Decision Points in Classification:</strong><br>"
        for i, point in enumerate(decision_points, 1):
            derivation += f"{i}. {point}<br>"

    if additional_info:
        derivation += "<strong>Additional Observations and Notes:</strong><br>"
        for info in additional_info:
            derivation += f"- {info}<br>"

    return derivation

def display_derivation(derivation: str):
    """
    Displays the derivation in a styled container with enhanced formatting.
    """
    st.markdown("### **How This Classification Was Derived**")
    st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>
            <p style='font-size: 1rem; line-height: 1.6; text-align: justify; margin: 0;'>
                {derivation}
            </p>
        </div>
    """, unsafe_allow_html=True)

def build_decision_flowchart(classification: str, decision_points: list) -> str:
    """
    Builds a simple Graphviz flowchart representing the classification path.

    For demonstration, we'll create nodes for each major decision step plus the final classification.
    Returns the DOT source string for rendering with st.graphviz_chart.
    """
    dot = graphviz.Digraph(comment="Classification Flow", format='png')

    # Start node
    dot.node("Start", "Start", shape="ellipse")

    # Each decision point becomes a node in the flow.
    previous_node = "Start"
    for i, point in enumerate(decision_points, 1):
        node_name = f"Step{i}"
        # Shorten the label for better visualization
        label = point if len(point) < 50 else point[:47] + "..."
        dot.node(node_name, label, shape="box")
        dot.edge(previous_node, node_name)
        previous_node = node_name

    # Final classification node
    dot.node("Result", f"Final: {classification}", shape="doublerectangle", color="green")
    dot.edge(previous_node, "Result")

    return dot.source

##############################
# VALIDATION
##############################
def validate_inputs(
    blasts_percentage: float,
    lineage: str,
    is_b_cell: bool,
    is_t_cell: bool,
    is_nk_cell: bool,
    morphological_details: list,
    immunophenotype_markers: list,
    cytogenetic_abnormalities: list,
    molecular_mutations: list,
    wbc_count: float,
    rbc_count: float,
    platelet_count: float,
    eosinophil_count: float,
    monocyte_count: float,
    patient_age: float
) -> tuple:
    """
    Validates user inputs for consistency and completeness.
    Returns a tuple of (errors, warnings).
    """
    errors = []
    warnings = []

    if not (0 <= blasts_percentage <= 100):
        errors.append("Blasts percentage must be between 0 and 100.")

    if not (0 <= wbc_count <= 200):
        warnings.append("WBC count seems unusually high or low.")

    if not (0 <= rbc_count <= 10):
        warnings.append("RBC count seems unusually high or low.")

    if not (0 <= platelet_count <= 1500):
        warnings.append("Platelet count seems unusually high or low.")

    if not (0 <= eosinophil_count <= 50):
        warnings.append("Eosinophil count seems unusually high or low.")

    if not (0 <= monocyte_count <= 50):
        warnings.append("Monocyte count seems unusually high or low.")

    if patient_age < 0 or patient_age > 120:
        errors.append("Patient age must be between 0 and 120 years.")

    return errors, warnings

##############################
# CLASSIFICATION LOGIC (POINT #5 ENHANCEMENTS)
##############################
def classify_blood_cancer(
    blasts_percentage: float,
    lineage: str,
    is_b_cell: bool,
    is_t_cell: bool,
    is_nk_cell: bool,
    morphological_details: list,
    immunophenotype_markers: list,
    immunophenotype_notes: str,
    cytogenetic_abnormalities: list,
    molecular_mutations: list,
    wbc_count: float,
    rbc_count: float,
    platelet_count: float,
    eosinophil_count: float,
    mast_cell_involvement: bool,
    histiocytic_marker: bool,
    hodgkin_markers: bool,
    cd15_positive: bool,
    cd30_positive: bool,
    cd20_positive: bool,
    cd45_negative: bool,
    monocyte_count: float,
    patient_age: float
) -> tuple:
    """
    Returns a tuple of (classification, derivation_string, decision_points).
    Incorporates:
      - Subtype refinement (AML/ALL, etc.)
      - Context-specific classification (e.g., pediatric vs. adult)
      - Rare entity support (basic examples)
    """
    decision_points = []
    additional_info = []
    classification = "Unspecified Hematologic Neoplasm"

    # Pediatric vs. adult example
    pediatric_case = (patient_age < 18)
    if pediatric_case:
        additional_info.append("Patient is pediatric (<18), applying pediatric considerations.")

    # ACUTE VS CHRONIC
    if blasts_percentage >= 20:
        decision_points.append("Blasts >= 20% indicates a likely acute leukemia.")
        if lineage == "Myeloid":
            classification = "Acute Myeloid Leukemia (AML)"
            decision_points.append("Lineage: Myeloid => AML classification.")

            # Subtype checks
            if "t(15;17)" in cytogenetic_abnormalities:
                classification = "Acute Promyelocytic Leukemia (APL)"
                decision_points.append("Detected t(15;17) => APL subtype.")
            elif "t(8;21)" in cytogenetic_abnormalities:
                classification = "AML with t(8;21)"
                decision_points.append("Detected t(8;21), refining AML subtype.")
            elif "inv(16)" in cytogenetic_abnormalities or "t(16;16)" in cytogenetic_abnormalities:
                classification = "AML with inv(16)/t(16;16)"
                decision_points.append("Detected inv(16) or t(16;16), refining AML subtype.")
            else:
                # Mutation checks
                if "FLT3" in molecular_mutations:
                    classification = "AML with FLT3 Mutation"
                    decision_points.append("Detected FLT3 mutation, further refining AML subtype.")
                elif "NPM1" in molecular_mutations:
                    classification = "AML with NPM1 Mutation"
                    decision_points.append("Detected NPM1 mutation, further refining AML subtype.")

        elif lineage == "Lymphoid":
            if pediatric_case:
                classification = "Acute Lymphoblastic Leukemia (ALL, Pediatric)"
                decision_points.append("Lineage: Lymphoid + Pediatric => ALL (Pediatric).")
            else:
                classification = "Acute Lymphoblastic Leukemia (ALL, Adult)"
                decision_points.append("Lineage: Lymphoid + Adult => ALL (Adult).")
        else:
            classification = "Acute Leukemia of Ambiguous Lineage"
            decision_points.append("Lineage undetermined => Possible mixed phenotype or ambiguous lineage.")
    else:
        decision_points.append("Blasts < 20% => Chronic or other non-acute neoplasm.")
        if lineage == "Myeloid":
            classification = "Chronic Myeloid Leukemia (CML)"
            decision_points.append("Lineage: Myeloid => CML classification unless MDS/MPN overlap indicated.")
            if "Ring sideroblasts" in morphological_details:
                additional_info.append("Ring sideroblasts noted => Possible MDS or overlap syndrome if more data support it.")

        elif lineage == "Lymphoid":
            classification = "Chronic Lymphocytic Leukemia (CLL)"
            decision_points.append("Lineage: Lymphoid => CLL or mature B/T/NK neoplasm.")
            if immunophenotype_notes and "hairy" in immunophenotype_notes.lower():
                classification = "Hairy Cell Leukemia (Rare B-Cell Neoplasm)"
                decision_points.append("Detected 'hairy' in immunophenotype notes => Hairy Cell Leukemia.")
        else:
            classification = "Other Chronic Hematologic Neoplasm"
            decision_points.append("Lineage undetermined => Possibly other chronic/rare entity.")

    # Additional data checks
    if immunophenotype_notes:
        additional_info.append(f"Immunophenotype notes: {immunophenotype_notes}.")
    
    if cytogenetic_abnormalities:
        additional_info.append(f"Cytogenetic abnormalities: {', '.join(cytogenetic_abnormalities)}.")
    
    if molecular_mutations:
        additional_info.append(f"Molecular mutations: {', '.join(molecular_mutations)}.")

    derivation = log_derivation(
        blasts=blasts_percentage,
        lineage=lineage,
        decision_points=decision_points,
        additional_info=additional_info
    )

    return classification, derivation, decision_points

##############################
# GPT-4 REVIEW
##############################
def get_gpt4_review(classification: str, explanation: str) -> str:
    """
    Sends the classification and explanation to GPT-4 for review and next steps.
    """
    prompt = f"""
    You are a medical expert reviewing a hematologic malignancy classification.

    **Classification Result**: {classification}

    **Derivation**:
    {explanation}

    **Task**:
    1. Provide a quick review of the classification result, highlighting any potential concerns or inconsistencies.
    2. Suggest clinically relevant next steps for further evaluation or management.

    **Response should be concise and professional.**
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
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

##############################
# MAIN APP
##############################
def app_main():
    """
    Primary Streamlit app function.
    """
    st.title("WHO Classification Demo – Interactive Visualization with Flowchart")

    st.markdown("""
    This **Streamlit** app classifies hematologic malignancies based on user inputs,
    showcasing **interactive visualization** via a simple **Graphviz** flowchart of decision steps.

    **Key Features**:
    - Subtype refinement for AML/ALL
    - Pediatric vs. adult logic
    - Rare entities (e.g., Hairy Cell Leukemia)
    - Graphviz-based flowchart of how the classification was reached
    - GPT-4 integration for review and suggestions (authenticated users)

    **Disclaimer**: This tool is for **educational demonstration** only and is not a clinical or diagnostic tool.
    """)

    st.markdown("---")

    # CBC Inputs in columns
    with st.container():
        st.subheader("1. Complete Blood Count (CBC)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            wbc_count = st.number_input("WBC (x10^9/L)", min_value=0.0, value=7.5, step=0.1)
        with col2:
            rbc_count = st.number_input("RBC (x10^12/L)", min_value=0.0, value=4.5, step=0.1)
        with col3:
            platelet_count = st.number_input("Platelet (x10^9/L)", min_value=0.0, value=250.0, step=10.0)
        with col4:
            eosinophil_count = st.number_input("Eosinophils (x10^9/L)", min_value=0.0, value=0.2, step=0.1)

    # Blasts
    st.subheader("2. Bone Marrow Blasts (%)")
    blasts_percentage = st.slider("Blasts in marrow (%)", 0, 100, 5)

    # Morphology
    st.subheader("3. Morphological Details")
    morphological_options = [
        "Auer rods",
        "Granular promyelocytes",
        "Ring sideroblasts",
        "Dyserythropoiesis",
        "Dysgranulopoiesis",
        "Dysmegakaryopoiesis",
        "Micromegakaryocytes",
    ]
    morphological_details = st.multiselect("Observed morphological features:", morphological_options)

    # Additional MDS/MPN Overlap
    st.subheader("4. Additional Counts for MDS/MPN Overlap")
    col5, col6 = st.columns(2)
    with col5:
        monocyte_count = st.number_input("Monocyte count (x10^9/L)", min_value=0.0, value=0.5, step=0.1)
    with col6:
        patient_age = st.number_input("Patient age (years)", min_value=0.0, value=50.0, step=1.0)

    # Lineage
    st.subheader("5. Dominant Lineage (User Assessment)")
    lineage = st.radio("Predominant lineage:", ["Myeloid", "Lymphoid", "Undetermined"], index=1)
    is_b_cell = False
    is_t_cell = False
    is_nk_cell = False
    if lineage == "Lymphoid":
        subset = st.selectbox("Lymphoid subset (if known)?", ["Unknown", "B-cell", "T-cell", "NK-cell"])
        if subset == "B-cell":
            is_b_cell = True
        elif subset == "T-cell":
            is_t_cell = True
        elif subset == "NK-cell":
            is_nk_cell = True

    # Immunophenotyping
    st.subheader("6. Immunophenotyping Markers")
    marker_choices = [
        "CD2", "CD3", "CD4", "CD5", "CD7", "CD8", "CD10", "CD14", "CD15", "CD19", "CD20",
        "CD23", "CD30", "CD34", "CD45", "CD56", "CD79a", "Myeloperoxidase (MPO)",
    ]
    immunophenotype_markers = st.multiselect("Positive markers:", marker_choices)
    immunophenotype_notes = st.text_input("Additional immunophenotype notes (e.g., 'Follicular', 'hairy cells', etc.)")

    # Cytogenetics & Molecular
    st.subheader("7. Cytogenetics & Molecular")
    cytogenetic_samples = [
        "t(15;17)", "t(8;21)", "inv(16)", "t(16;16)", "t(9;22) BCR-ABL1", "t(12;21)",
        "t(1;19)", "t(11;14) CCND1-IGH", "t(14;18) BCL2-IGH", "t(8;14) MYC-IGH", "Other"
    ]
    cytogenetic_abnormalities = st.multiselect("Cytogenetic Abnormalities:", cytogenetic_samples)

    st.subheader("7a. Molecular Mutations")
    mutation_samples = [
        "FLT3", "NPM1", "CEBPA", "RUNX1", "JAK2", "CALR", "MPL", "BCR-ABL1",
        "KMT2A (MLL)", "ETV6-RUNX1", "TCF3-PBX1", "MYC", "BCL2", "BCL6", "CCND1",
        "TET2", "SRSF2", "SF3B1", "IDH1", "IDH2", "ASXL1", "HTLV-1", "HYPERDIPLOID", "HYPODIPLOID",
        "Other"
    ]
    molecular_mutations = st.multiselect("Molecular Mutations:", mutation_samples)

    # Special Entities
    st.subheader("8. Special Entities")
    col7, col8 = st.columns(2)
    with col7:
        mast_cell_involvement = st.checkbox("Suspect Mastocytosis?")
        histiocytic_marker = st.checkbox("Suspect Histiocytic/Dendritic Cell Neoplasm?")
    with col8:
        hodgkin_markers = st.checkbox("Suspect Hodgkin Lymphoma?")
        cd15_positive = st.checkbox("CD15+ (Hodgkin)?")
        cd30_positive = st.checkbox("CD30+ (Hodgkin)?")
        cd20_positive = st.checkbox("CD20+ (Hodgkin)?")
        cd45_negative = st.checkbox("CD45- (Hodgkin)?")

    st.markdown("---")

    # CLASSIFY BUTTON
    if st.button("Classify"):
        # Validate inputs
        errors, warnings = validate_inputs(
            blasts_percentage=blasts_percentage,
            lineage=lineage,
            is_b_cell=is_b_cell,
            is_t_cell=is_t_cell,
            is_nk_cell=is_nk_cell,
            morphological_details=morphological_details,
            immunophenotype_markers=immunophenotype_markers,
            cytogenetic_abnormalities=cytogenetic_abnormalities,
            molecular_mutations=molecular_mutations,
            wbc_count=wbc_count,
            rbc_count=rbc_count,
            platelet_count=platelet_count,
            eosinophil_count=eosinophil_count,
            monocyte_count=monocyte_count,
            patient_age=patient_age
        )

        if errors:
            for error in errors:
                st.error(f"**Error:** {error}")
            st.stop()

        if warnings:
            for warning in warnings:
                st.warning(f"**Warning:** {warning}")

        # Perform classification
        classification, derivation_string, decision_points = classify_blood_cancer(
            blasts_percentage=blasts_percentage,
            lineage=lineage,
            is_b_cell=is_b_cell,
            is_t_cell=is_t_cell,
            is_nk_cell=is_nk_cell,
            morphological_details=morphological_details,
            immunophenotype_markers=immunophenotype_markers,
            immunophenotype_notes=immunophenotype_notes,
            cytogenetic_abnormalities=cytogenetic_abnormalities,
            molecular_mutations=molecular_mutations,
            wbc_count=wbc_count,
            rbc_count=rbc_count,
            platelet_count=platelet_count,
            eosinophil_count=eosinophil_count,
            mast_cell_involvement=mast_cell_involvement,
            histiocytic_marker=histiocytic_marker,
            hodgkin_markers=hodgkin_markers,
            cd15_positive=cd15_positive,
            cd30_positive=cd30_positive,
            cd20_positive=cd20_positive,
            cd45_negative=cd45_negative,
            monocyte_count=monocyte_count,
            patient_age=patient_age
        )

        # ---- Classification Result Box ----
        st.markdown(f"""
            <div style='background-color: #d1e7dd; padding: 5px 10px; border-radius: 5px; margin-bottom: 15px;'>
                <h4 style='color: #0f5132; margin: 0;'>Classification Result</h4>
                <p style='color: #0f5132; margin: 5px 0 0; font-size: 1rem;'><strong>{classification}</strong></p>
            </div>
        """, unsafe_allow_html=True)

        # ---- Derivation Explanation ----
        display_derivation(derivation_string)

        # If user is authenticated, show GPT-4 review
        if st.session_state['authenticated']:
            with st.spinner("Generating GPT-4 review and clinical next steps..."):
                gpt4_review_result = get_gpt4_review(
                    classification,
                    derivation_string
                )

            # Display GPT-4's response in a styled box
            st.markdown("### **GPT-4 Review & Clinical Next Steps**")
            st.markdown(f"""
                <div style='background-color: #cff4fc; padding: 10px; border-radius: 5px;'>
                    {gpt4_review_result}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Log in to receive an AI-generated review and clinical recommendations.")

        # ---- Build Decision Flowchart from Decision Points ----
        # Use the decision_points list directly
        if decision_points:
            flowchart_src = build_decision_flowchart(classification, decision_points)
            st.subheader("Interactive Classification Flowchart")
            st.graphviz_chart(flowchart_src)
        else:
            st.warning("No decision points available to display in the flowchart.")

        

        st.markdown("""
        ---
        **Disclaimer**: This app is a simplified demonstration and **not** a replacement for 
        professional pathology review or real-world WHO classification.
        """)

##############################
# MAIN ENTRY POINT
##############################
def main():
    app_main()

if __name__ == "__main__":
    main()
