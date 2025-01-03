import streamlit as st
import bcrypt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai"]["api_key"])
import graphviz

# -----------------------------
# SET PAGE CONFIGURATION FIRST
# -----------------------------
st.set_page_config(page_title="Hematologic Classification", layout="wide")

if "show_explanation" not in st.session_state:
    st.session_state["show_explanation"] = False

##############################
# OPENAI API CONFIG
##############################

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
    else:
        st.sidebar.header("Login")
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.success("Logged in successfully!")
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
# EXPLANATION FUNCTION
##############################
def show_explanation():
    """
    Displays a nicely formatted explanation/help page, 
    with an option to hide it again.
    """
    st.title("Hematologic Classification – Explanation & Help")

    # Provide a button to hide the explanation (go back to main view)
    if st.button("Hide Explanation"):
        st.session_state["show_explanation"] = False
        st.rerun()

    # A bit of visual styling (light gray box) to separate the explanation
    st.markdown("""
    <div style="background-color: #f9f9f9; padding: 20px; border-radius: 5px;">
    <h2 style="margin-top: 0;">Overview</h2>
    <p>
      This application uses a simplified WHO-based logic to classify hematologic
      malignancies. The classification hinges on:
      <ul>
        <li><strong>Blasts Percentage</strong> (acute vs. chronic threshold at 20%)</li>
        <li><strong>Lineage</strong> (myeloid, lymphoid, or undetermined)</li>
        <li><strong>Immunophenotype Markers &amp; Notes</strong></li>
        <li><strong>Cytogenetic Abnormalities &amp; Molecular Mutations</strong></li>
        <li><strong>Patient Age</strong> (for pediatric vs. adult logic)</li>
        <li>Various <strong>special flags</strong> (Hodgkin, histiocytic, etc.)</li>
      </ul>
    </p>

    <hr>

    <h3>1. Acute vs. Chronic</h3>
    <ul>
      <li><strong>Blasts ≥ 20%</strong> ⇒ Suggests <em>acute leukemia</em>.</li>
      <li><strong>Blasts < 20%</strong> ⇒ Suggests <em>chronic</em> neoplasm or MDS/MPN.</li>
    </ul>

    <h4>Acute Myeloid Leukemia (AML)</h4>
    <ul>
      <li>Possible subtypes based on t(15;17), t(8;21), inv(16), FLT3, NPM1.</li>
      <li>If none of those, classified as <em>AML (NOS)</em>.</li>
    </ul>

    <h4>Acute Lymphoblastic Leukemia (ALL)</h4>
    <ul>
      <li><em>Pediatric ALL</em> if patient under 18.</li>
      <li><em>Adult ALL</em> otherwise.</li>
    </ul>

    <h4>Ambiguous Lineage</h4>
    <ul>
      <li>If lineage is not clearly myeloid or lymphoid, 
        classified as <em>Acute Leukemia of Ambiguous Lineage</em>.</li>
    </ul>

    <hr>

    <h3>2. Chronic Myeloid &amp; MDS/MPN</h3>
    <ul>
      <li>If <strong>blasts < 20%</strong> and lineage = Myeloid:</li>
      <li><em>MPN</em> if JAK2/CALR/MPL driver mutations present.</li>
      <li><em>MDS</em> subtypes (e.g., MDS w/ Excess Blasts, del(5q), etc.) 
          if certain morphological or cytogenetic features appear.</li>
      <li><em>CML</em> if none of the above criteria is triggered.</li>
    </ul>

    <hr>

    <h3>3. Chronic Lymphoid</h3>
    <ul>
      <li><strong>Suspect Hodgkin Lymphoma</strong>:
        <ul>
          <li><em>Classical Hodgkin</em> if CD15+ &amp; CD30+.</li>
          <li><em>NLPHL</em> if CD20+ only, no CD15/CD30.</li>
          <li>Otherwise, <em>Hodgkin (Unspecified)</em>.</li>
        </ul>
      </li>
      <li><strong>Non-Hodgkin Lymphoma</strong> (NHL) checks:
        <ul>
          <li><em>B-Cell</em> (Follicular Lymphoma if CD10+; else DLBCL default).</li>
          <li><em>T-Cell</em> (Peripheral T-Cell Lymphoma as fallback).</li>
        </ul>
      </li>
      <li><strong>CLL</strong> if no specific markers for other B/T subtypes.</li>
      <li><strong>Hairy Cell Leukemia</strong> if 'hairy' in notes.</li>
    </ul>

    <hr>

    <h3>4. Multiple Myeloma</h3>
    <ul>
      <li>If immunophenotype suggests <em>plasma cells</em> (CD138) or 
          notes say "plasma," classified as 
          <em>Multiple Myeloma (Plasma Cell Neoplasm)</em>.</li>
    </ul>

    <hr>

    <h3>5. Special &amp; Rare Entities</h3>
    <ul>
      <li><em>Mast Cell Involvement</em> → Possible Mastocytosis (basic placeholder).</li>
      <li><em>Histiocytic Marker</em> → Histiocytic or Dendritic Cell Neoplasm 
          (also placeholder in this demo).</li>
      <li><em>Undetermined/Other</em> if no logic branch triggers a specific classification.</li>
    </ul>

    <hr>

    <h3>Final Classification List (Simplified)</h3>
    <ul>
      <li><strong>AML</strong> (incl. APL, t(8;21), inv(16), AML w/ FLT3, AML w/ NPM1, etc.)</li>
      <li><strong>ALL</strong> (pediatric or adult)</li>
      <li><strong>Acute Leukemia of Ambiguous Lineage</strong></li>
      <li><strong>Myeloproliferative Neoplasm (MPN)</strong></li>
      <li><strong>Myelodysplastic Syndromes (MDS)</strong> subtypes</li>
      <li><strong>Chronic Myeloid Leukemia (CML)</strong></li>
      <li><strong>Hodgkin Lymphoma</strong> (Classical, NLPHL, or Unspecified)</li>
      <li><strong>Non-Hodgkin Lymphoma</strong> (Follicular, DLBCL, T-Cell, etc.)</li>
      <li><strong>Chronic Lymphocytic Leukemia (CLL)</strong></li>
      <li><strong>Hairy Cell Leukemia</strong></li>
      <li><strong>Multiple Myeloma (Plasma Cell Neoplasm)</strong></li>
      <li><strong>Other Chronic Hematologic Neoplasm</strong></li>
    </ul>

    <div style="border-top: 1px solid #ccc; margin-top: 20px; padding-top: 10px;">
    <em>Disclaimer</em>: This classification logic is <strong>simplified</strong> and
    should not replace real-world pathology review. Consult a hematologist or oncologist 
    for definitive diagnosis and treatment recommendations.
    </div>
    </div>
    """, unsafe_allow_html=True)


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
      - Subtype refinement (AML, ALL, etc.)
      - Context-specific classification (pediatric vs. adult)
      - Myeloma, MDS, MPN expansions
      - Hodgkin Lymphoma subtypes (basic)
      - Non-Hodgkin Lymphoma subtypes (basic)
    """

    decision_points = []
    additional_info = []
    classification = "Unspecified Hematologic Neoplasm"

    # Check if the patient is pediatric
    pediatric_case = (patient_age < 18)
    if pediatric_case:
        additional_info.append("Patient is pediatric (<18), applying pediatric considerations.")

    # 1) Detect multiple myeloma (if plasma cell markers or notes)
    if "plasma" in immunophenotype_notes.lower() or "CD138" in immunophenotype_markers:
        decision_points.append("Detected plasma cell phenotype -> Possible Multiple Myeloma.")
        classification = "Multiple Myeloma (Plasma Cell Neoplasm)"

    else:
        # 2) ACUTE VS CHRONIC (based on blasts >= 20%)
        if blasts_percentage >= 20:
            decision_points.append("Blasts >= 20% => Likely acute leukemia.")
            if lineage == "Myeloid":
                classification = "Acute Myeloid Leukemia (AML)"
                decision_points.append("Lineage: Myeloid => AML classification.")
                
                # AML subtypes
                if "t(15;17)" in cytogenetic_abnormalities:
                    classification = "Acute Promyelocytic Leukemia (APL)"
                    decision_points.append("Detected t(15;17) => APL subtype.")
                elif "t(8;21)" in cytogenetic_abnormalities:
                    classification = "AML with t(8;21)"
                    decision_points.append("Detected t(8;21) => Refining AML subtype.")
                elif any(x in cytogenetic_abnormalities for x in ["inv(16)", "t(16;16)"]):
                    classification = "AML with inv(16)/t(16;16)"
                    decision_points.append("Detected inv(16)/t(16;16) => Refining AML subtype.")
                else:
                    # Mutations
                    if "FLT3" in molecular_mutations:
                        classification = "AML with FLT3 Mutation"
                        decision_points.append("Detected FLT3 mutation => AML with FLT3.")
                    elif "NPM1" in molecular_mutations:
                        classification = "AML with NPM1 Mutation"
                        decision_points.append("Detected NPM1 mutation => AML with NPM1.")

            elif lineage == "Lymphoid":
                # ALL subtypes
                if pediatric_case:
                    classification = "Acute Lymphoblastic Leukemia (ALL, Pediatric)"
                    decision_points.append("Lineage: Lymphoid + Pediatric => ALL (Pediatric).")
                else:
                    classification = "Acute Lymphoblastic Leukemia (ALL, Adult)"
                    decision_points.append("Lineage: Lymphoid + Adult => ALL (Adult).")
            else:
                classification = "Acute Leukemia of Ambiguous Lineage"
                decision_points.append("Lineage undetermined => Mixed phenotype / ambiguous lineage.")
        
        else:
            # CHRONIC or MDS/MPN
            decision_points.append("Blasts < 20% => Chronic or other non-acute neoplasm.")
            if lineage == "Myeloid":
                # MPN driver check (JAK2, CALR, MPL)
                mpn_drivers = {"JAK2", "CALR", "MPL"}
                if mpn_drivers.intersection(set(molecular_mutations)):
                    classification = "Myeloproliferative Neoplasm (MPN)"
                    decision_points.append("Detected MPN driver mutation => MPN classification.")
                else:
                    # MDS checks (simplified)
                    blasts_for_mds = blasts_percentage
                    has_del5q = any("del(5q)" in ab.lower() for ab in cytogenetic_abnormalities)
                    dysplasia_count = sum(
                        x in morphological_details
                        for x in ["Dyserythropoiesis", "Dysgranulopoiesis", "Dysmegakaryopoiesis", "Multilineage dysplasia"]
                    )
                    if blasts_for_mds >= 5 and blasts_for_mds < 20:
                        classification = "MDS with Excess Blasts"
                        decision_points.append("5-19% blasts => MDS with Excess Blasts.")
                    elif has_del5q:
                        classification = "MDS with Isolated del(5q)"
                        decision_points.append("Detected del(5q) => MDS with Isolated del(5q).")
                    else:
                        if "Multilineage dysplasia" in morphological_details or dysplasia_count > 1:
                            classification = "Refractory Cytopenia with Multilineage Dysplasia (RCMD)"
                            decision_points.append("Detected multilineage dysplasia => RCMD.")
                        elif "Refractory Anemia" in morphological_details:
                            classification = "Refractory Anemia (MDS)"
                            decision_points.append("Detected 'Refractory Anemia' => MDS subtype.")
                        else:
                            # Fallback to CML
                            classification = "Chronic Myeloid Leukemia (CML)"
                            decision_points.append("Defaulting to CML classification (no MDS/MPN evidence).")

                # Note ring sideroblasts
                if "Ring sideroblasts" in morphological_details:
                    additional_info.append("Ring sideroblasts => Possibly MDS with ring sideroblasts or MDS/MPN overlap.")

            elif lineage == "Lymphoid":
                # **Add Hodgkin vs Non-Hodgkin logic here**
                # Step 1: Check if suspect Hodgkin's
                if hodgkin_markers:
                    decision_points.append("Suspect Hodgkin Lymphoma => Checking markers.")
                    # Classic Hodgkin if CD15+ and CD30+
                    if cd15_positive and cd30_positive:
                        classification = "Classical Hodgkin Lymphoma"
                        decision_points.append("CD15+ and CD30+ => Classical Hodgkin Lymphoma.")
                    else:
                        # Another approach to differentiate NLPHL
                        # If cd20_positive and not cd30_positive => "Nodular Lymphocyte-Predominant HL" (simplified)
                        if cd20_positive and not cd30_positive and not cd15_positive:
                            classification = "Nodular Lymphocyte-Predominant Hodgkin Lymphoma (NLPHL)"
                            decision_points.append("CD20+ only => NLPHL (Hodgkin subtype).")
                        else:
                            classification = "Hodgkin Lymphoma (Unspecified Subtype)"
                            decision_points.append("Hodgkin markers present => Unspecified HL subtype.")
                else:
                    # NON-HODGKIN LYMPHOMA checks
                    # If B-cell or T-cell known
                    if is_b_cell:
                        # Minimal approach for Non-Hodgkin B-cell
                        # If "CD5" and "CD23" => CLL, but let's see if we want to override older logic or not
                        # For demonstration, let's handle a few subtypes:
                        if "CD10" in immunophenotype_markers:
                            classification = "Follicular Lymphoma (Non-Hodgkin)"
                            decision_points.append("Detected CD10 => Possible Follicular Lymphoma.")
                        else:
                            classification = "Diffuse Large B-Cell Lymphoma (DLBCL)"
                            decision_points.append("B-cell lymphoma => Defaulting to DLBCL (NHL).")
                    elif is_t_cell:
                        classification = "Peripheral T-Cell Lymphoma (Non-Hodgkin)"
                        decision_points.append("Detected T-cell => Peripheral T-Cell Lymphoma (NHL).")
                    else:
                        classification = "Chronic Lymphocytic Leukemia (CLL)"
                        decision_points.append("Lineage: Lymphoid => Defaulting to CLL or mature B/T/NK neoplasm.")
                        # If immunophenotype_notes contains 'hairy', we override to Hairy Cell (kept from older logic)
                        if immunophenotype_notes and "hairy" in immunophenotype_notes.lower():
                            classification = "Hairy Cell Leukemia (Rare B-Cell Neoplasm)"
                            decision_points.append("Detected 'hairy' => Hairy Cell Leukemia.")
            else:
                classification = "Other Chronic Hematologic Neoplasm"
                decision_points.append("Lineage undetermined => Possibly other chronic/rare entity.")

    # Additional checks/notes
    if immunophenotype_notes:
        additional_info.append(f"Immunophenotype notes: {immunophenotype_notes}.")
    if cytogenetic_abnormalities:
        additional_info.append(f"Cytogenetic abnormalities: {', '.join(cytogenetic_abnormalities)}.")
    if molecular_mutations:
        additional_info.append(f"Molecular mutations: {', '.join(molecular_mutations)}.")

    # Build derivation
    derivation = log_derivation(
        blasts=blasts_percentage,
        lineage=lineage,
        decision_points=decision_points,
        additional_info=additional_info
    )

    return classification, derivation, decision_points

def get_gpt4_review(
    classification: str,
    explanation: str,
    user_inputs: dict
) -> str:
    """
    Sends the classification, explanation, and all user input data to AI
    for review and next steps.
    """
    # Format user inputs into a readable string
    # Feel free to customize how you display them.
    input_data_str = "Below is the data the user provided:\n"
    input_data_str += f"- Blasts Percentage: {user_inputs['blasts_percentage']}\n"
    input_data_str += f"- Lineage: {user_inputs['lineage']}\n"
    input_data_str += f"- Is B-Cell: {user_inputs['is_b_cell']}\n"
    input_data_str += f"- Is T-Cell: {user_inputs['is_t_cell']}\n"
    input_data_str += f"- Is NK-Cell: {user_inputs['is_nk_cell']}\n"
    input_data_str += f"- Morphological Details: {user_inputs['morphological_details']}\n"
    input_data_str += f"- Immunophenotype Markers: {user_inputs['immunophenotype_markers']}\n"
    input_data_str += f"- Immunophenotype Notes: {user_inputs['immunophenotype_notes']}\n"
    input_data_str += f"- Cytogenetic Abnormalities: {user_inputs['cytogenetic_abnormalities']}\n"
    input_data_str += f"- Molecular Mutations: {user_inputs['molecular_mutations']}\n"
    input_data_str += f"- WBC Count: {user_inputs['wbc_count']}\n"
    input_data_str += f"- RBC Count: {user_inputs['rbc_count']}\n"
    input_data_str += f"- Platelet Count: {user_inputs['platelet_count']}\n"
    input_data_str += f"- Eosinophil Count: {user_inputs['eosinophil_count']}\n"
    input_data_str += f"- Monocyte Count: {user_inputs['monocyte_count']}\n"
    input_data_str += f"- Patient Age: {user_inputs['patient_age']}\n"
    input_data_str += f"- Mast Cell Involvement: {user_inputs['mast_cell_involvement']}\n"
    input_data_str += f"- Histiocytic Marker: {user_inputs['histiocytic_marker']}\n"
    input_data_str += f"- Suspect Hodgkin Markers: {user_inputs['hodgkin_markers']}\n"
    input_data_str += f"- CD15 Positive: {user_inputs['cd15_positive']}\n"
    input_data_str += f"- CD30 Positive: {user_inputs['cd30_positive']}\n"
    input_data_str += f"- CD20 Positive: {user_inputs['cd20_positive']}\n"
    input_data_str += f"- CD45 Negative: {user_inputs['cd45_negative']}\n"

    # Build the final prompt
    prompt = f"""
    You are a medical expert reviewing a hematologic malignancy classification.

    **User Input Data**:
    {input_data_str}

    **Classification Result**: {classification}

    **Derivation**:
    {explanation}

    **Task**:
    1. Provide a quick review of the classification result, highlighting any potential concerns or inconsistencies.
    2. Suggest clinically relevant next steps for further evaluation or management.

    **Response should be concise and professional.**
    """

    # Send to GPT-4
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
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
    st.title("WHO Blood Cancer Classification Tool")

    # Check if user wants to show/hide explanation
    st.sidebar.write("---")
    if st.sidebar.button("Show Explanation"):
        st.session_state["show_explanation"] = True

    if st.session_state["show_explanation"]:
        show_explanation()
        return  # Stop after showing explanation page

    st.markdown("""
    This **Streamlit** app classifies hematologic malignancies based on user inputs,
    showcasing **interactive visualization** via a simple **Graphviz** flowchart of decision steps.

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

    if st.button("Classify"):
        # 1) Validate inputs
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

        # 2) Perform classification
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

        # 3) Build a dictionary containing all user inputs
        user_inputs = {
            "blasts_percentage": blasts_percentage,
            "lineage": lineage,
            "is_b_cell": is_b_cell,
            "is_t_cell": is_t_cell,
            "is_nk_cell": is_nk_cell,
            "morphological_details": morphological_details,
            "immunophenotype_markers": immunophenotype_markers,
            "immunophenotype_notes": immunophenotype_notes,
            "cytogenetic_abnormalities": cytogenetic_abnormalities,
            "molecular_mutations": molecular_mutations,
            "wbc_count": wbc_count,
            "rbc_count": rbc_count,
            "platelet_count": platelet_count,
            "eosinophil_count": eosinophil_count,
            "monocyte_count": monocyte_count,
            "patient_age": patient_age,
            "mast_cell_involvement": mast_cell_involvement,
            "histiocytic_marker": histiocytic_marker,
            "hodgkin_markers": hodgkin_markers,
            "cd15_positive": cd15_positive,
            "cd30_positive": cd30_positive,
            "cd20_positive": cd20_positive,
            "cd45_negative": cd45_negative
        }

        # 4) Display Classification Result
        st.markdown(f"""
            <div style='background-color: #d1e7dd; padding: 5px 10px; border-radius: 5px; margin-bottom: 15px;'>
                <h4 style='color: #0f5132; margin: 0;'>Classification Result</h4>
                <p style='color: #0f5132; margin: 5px 0 0; font-size: 1rem;'><strong>{classification}</strong></p>
            </div>
        """, unsafe_allow_html=True)

        # 5) Display derivation
        display_derivation(derivation_string)

        # 6) If authenticated, call GPT-4 with the user_inputs
        if st.session_state['authenticated']:
            with st.spinner("Generating AI review and clinical next steps..."):
                gpt4_review_result = get_gpt4_review(
                    classification=classification,
                    explanation=derivation_string,
                    user_inputs=user_inputs  # PASS THE ENTIRE DICT HERE
                )
            st.markdown("### **AI Review & Clinical Next Steps**")
            st.markdown(f"""
                <div style='background-color: #cff4fc; padding: 10px; border-radius: 5px;'>
                    {gpt4_review_result}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Log in to receive an AI-generated review and clinical recommendations.")

        # 7) Build Decision Flowchart
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
