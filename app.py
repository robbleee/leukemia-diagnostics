import streamlit as st
import bcrypt
from openai import OpenAI
import graphviz

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

##############################
# SET PAGE CONFIGURATION FIRST
##############################
st.set_page_config(page_title="Hematologic Classification", layout="wide")

if "show_explanation" not in st.session_state:
    st.session_state["show_explanation"] = False

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
    """
    dot = graphviz.Digraph(comment="Classification Flow", format='png')

    # Start node
    dot.node("Start", "Start", shape="ellipse")

    # Each decision point becomes a node in the flow.
    previous_node = "Start"
    for i, point in enumerate(decision_points, 1):
        node_name = f"Step{i}"
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
    Displays a comprehensive and visually appealing explanation/help page in Markdown,
    detailing how classification logic is applied to arrive at each cancer type.
    Also provides a list of all cancer types that can be classified.
    """

    # Provide a button to hide the explanation (go back to the main view)
    if st.button("Hide Explanation"):
        st.session_state["show_explanation"] = False
        st.rerun()

    st.markdown("""
    <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; border: 1px solid #add8e6;">
      <h2 style="color: #003366;">Welcome to the Hematologic Classification Tool</h2>
      <p>
        This application assists in classifying hematologic malignancies based on user-provided data.
        Below is an in-depth overview of how the classification logic operates, including each decision point
        and the full range of cancer types it can identify.
      </p>
      <p><em>Disclaimer:</em> This tool is intended for <strong>educational purposes only</strong> and 
      should <strong>not</strong> be used as a substitute for professional medical advice or diagnosis.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    ## 1. Key Decision Factors

    The classification process is driven by several key inputs:

    - **Blasts Percentage**:
      - Determines whether a neoplasm is considered **acute** (≥20% blasts in marrow) or **chronic** (<20% blasts).
    - **Lineage**:
      - Identifies if cells appear **Myeloid**, **Lymphoid**, or **Undetermined**, guiding subsequent classification steps.
    - **Immunophenotype & Special Flags**:
      - **Markers** (e.g., CD19, CD3, CD138) indicate specific cell lineages or subtypes (B-cells, T-cells, plasma cells, etc.).
      - **Special flags** (e.g., "Skin involvement", "CD7 loss") capture nuanced clinical/lab findings that can refine subtype.
    - **Cytogenetic Abnormalities & Molecular Mutations**:
      - **Chromosomal Translocations** (e.g., t(8;21), t(15;17)).
      - **Gene Mutations** (e.g., FLT3, NPM1).
    - **Patient Age**:
      - Helps differentiate pediatric (<18 years) from adult presentations (≥18 years), especially relevant for ALL.
    """)

    st.markdown("""
    ## 2. Full Classification Logic

    This tool follows a hierarchical set of checks to arrive at the most specific possible diagnosis:

    ### 2.1. Acute vs. Chronic
    1. **Assess Blasts Percentage**:
       - If **blasts ≥ 20%**, the case is treated as an **acute leukemia**.
       - If **blasts < 20%**, the classification proceeds as **chronic** or **other** (e.g., lymphoma, myeloproliferative neoplasm).

    ### 2.2. Myeloid vs. Lymphoid Lineage
    - After determining acute vs. chronic, the tool examines **lineage**:
      - **Myeloid** → Evaluate for AML, MDS, MPN, or CML.
      - **Lymphoid** → Evaluate for ALL, Hodgkin, or Non-Hodgkin lymphoma.
      - **Undetermined** → May end up as 'Acute Leukemia of Ambiguous Lineage' or 'Other Chronic Hematologic Neoplasm'.

    ---
    ### **A) Acute Myeloid Leukemia (≥20% blasts, Myeloid)**
    1. **Initial AML Assignment**: If blasts ≥ 20% and lineage is myeloid, default is **Acute Myeloid Leukemia (AML)**.
    2. **Further Subtyping** (checked in this order):
       - **BPDCN (Blastic Plasmacytoid Dendritic Cell Neoplasm)**:
         - Identified if the immunophenotype shows **CD123 + CD4 + CD56** (plasmacytoid dendritic phenotype).
       - **AML-M6 (Erythroid)**:
         - If morphological details mention “Erythroid precursors” or markers like **Glycophorin A** or **CD71** are present.
       - **AML-M7 (Megakaryoblastic)**:
         - If morphological details indicate “Megakaryoblasts” or markers **CD41**, **CD42b**, or **CD61** are found.
       - **Acute Promyelocytic Leukemia (APL)**:
         - If **t(15;17)** is present.
       - **AML with t(8;21)**:
         - If that specific translocation is observed.
       - **AML with inv(16)/t(16;16)**:
         - If those rearrangements appear in cytogenetics.
       - **AML with FLT3**:
         - If molecular testing detects a FLT3 mutation.
       - **AML with NPM1**:
         - If molecular testing detects an NPM1 mutation.

    ---
    ### **B) Acute Lymphoblastic Leukemia (≥20% blasts, Lymphoid)**
    - **Pediatric ALL**: If the patient is <18.
    - **Adult ALL**: If the patient is ≥18.

    ---
    ### **C) Acute Leukemia of Ambiguous Lineage**
    - If blasts ≥ 20% but lineage is undetermined or contradictory, it may result in a diagnosis of ambiguous or mixed phenotype.

    ---
    ### **D) Chronic (Blasts < 20%) Myeloid Entities**
    1. **Check MPN Driver Mutations** (JAK2, CALR, MPL):
       - If positive, classify as **Myeloproliferative Neoplasm (MPN)**.
    2. **Evaluate for MDS** (Myelodysplastic Syndromes):
       - **MDS with Excess Blasts**: 5–19% blasts.
       - **MDS with Isolated del(5q)**: If a del(5q) abnormality is detected.
       - **RCMD**: If “Multilineage dysplasia” is present.
       - **Refractory Anemia**: Subtype under MDS with primarily anemic presentation.
    3. **Chronic Myeloid Leukemia (CML)**:
       - If none of the above criteria (MPN or MDS) are met, default to CML.

    ---
    ### **E) Chronic (Blasts < 20%) Lymphoid Entities**
    - **Suspect Hodgkin Lymphoma**:
      - If `hodgkin_markers = True`; refine using **CD15+ CD30+** → Classic HL, **CD20+ only** → NLPHL, or Unspecified.
    - **Non-Hodgkin**:
      1. **B-cell**:
         - **Mantle Cell Lymphoma**: (Cyclin D1 or t(11;14)) + **CD5+**. Typically **CD23-**.
         - **Marginal Zone Lymphoma**: Usually **CD20+** or **CD79a+**, but negative for CD5/CD10.
         - **Primary CNS Lymphoma**: Subset of DLBCL with **BCL6, CD20** and “CNS involvement”.
         - **Burkitt’s Lymphoma**: **MYC** or **t(8;14)** + **CD10+**.
         - **Follicular Lymphoma**: If **CD10+** without MYC features.
         - **Diffuse Large B-Cell Lymphoma (DLBCL)**: Default if no other B-cell category matches.
      2. **T-cell**:
         - **ALCL**: T-cell with **CD30+**; if cytogenetics show "ALK" → ALCL (ALK+), otherwise ALK–.
         - **AITL**: T-cell with **CD10** plus **PD-1/CXCL13/BCL6**.
         - **Mycosis Fungoides**: T-cell with “Skin involvement” or “CD7 loss” + **CD4**.
         - **Peripheral T-Cell Lymphoma (PTCL)**: T-lymphoid neoplasm not fitting the above specific categories.
      3. **Chronic Lymphocytic Leukemia (CLL)**:
         - Default if the immunophenotype suggests mature B-cells without any of the lymphoma indicators above.
         - If “Hairy cells” flag is triggered, → **Hairy Cell Leukemia**.

    ---
    ### **F) Other or Rare Entities**
    - **Multiple Myeloma (Plasma Cell Neoplasm)**:
      - If **CD138** is detected among markers.
    - **Mast Cell Involvement**:
      - Suggests possible **Mastocytosis** (Placeholder logic).
    - **Histiocytic Marker**:
      - Suggests **Histiocytic or Dendritic Cell Neoplasm** (Placeholder logic).
    - **Undetermined**:
      - If none of the above branches apply, classification defaults to “Undetermined Hematologic Neoplasm.”

    ---
    ## 3. All Recognized Hematologic Malignancies

    The following is a comprehensive list (alphabetical) of the malignancies the tool can classify:

    | **Cancer Type**                                            | **Description**                                      |
    |------------------------------------------------------------|------------------------------------------------------|
    | Acute Erythroid Leukemia (AML-M6)                          | AML subtype with erythroid precursors.               |
    | Acute Lymphoblastic Leukemia (ALL, Pediatric)              | ALL in patients younger than 18 years.               |
    | Acute Lymphoblastic Leukemia (ALL, Adult)                  | ALL in patients 18 years and older.                  |
    | Acute Megakaryoblastic Leukemia (AML-M7)                    | AML subtype with megakaryoblasts.                    |
    | Acute Myeloid Leukemia (AML)                                | General AML classification.                           |
    | Acute Promyelocytic Leukemia (APL)                          | AML subtype characterized by t(15;17).               |
    | AML with FLT3 Mutation                                      | AML subtype with FLT3 mutation.                      |
    | AML with NPM1 Mutation                                      | AML subtype with NPM1 mutation.                      |
    | AML with t(8;21)                                            | AML subtype with t(8;21) translocation.              |
    | AML with inv(16)/t(16;16)                                   | AML subtype with inv(16) or t(16;16) translocation.  |
    | Anaplastic Large Cell Lymphoma (ALCL, ALK+)                 | ALCL subtype positive for ALK.                       |
    | Anaplastic Large Cell Lymphoma (ALCL, ALK–)                 | ALCL subtype negative for ALK.                       |
    | Angioimmunoblastic T-Cell Lymphoma (AITL)                   | T-cell lymphoma with angioimmunoblastic features.    |
    | Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)        | Aggressive myeloid neoplasm with plasmacytoid dendritic phenotype. |
    | Burkitt's Lymphoma (High-Grade B-Cell NHL)                  | Highly aggressive B-cell non-Hodgkin lymphoma.       |
    | Chronic Lymphocytic Leukemia (CLL)                          | Chronic B-cell leukemia.                             |
    | Chronic Myeloid Leukemia (CML)                              | Chronic leukemia with Philadelphia chromosome.       |
    | Cutaneous T-Cell Lymphoma (Mycosis Fungoides)               | T-cell lymphoma affecting the skin.                  |
    | Diffuse Large B-Cell Lymphoma (DLBCL)                       | Aggressive B-cell non-Hodgkin lymphoma.              |
    | Follicular Lymphoma (Non-Hodgkin)                           | B-cell non-Hodgkin lymphoma with follicular features.|
    | Hairy Cell Leukemia (Rare B-Cell Neoplasm)                  | Rare B-cell leukemia with characteristic “hairy” cells. |
    | Histiocytic/Dendritic Cell Neoplasm                         | Placeholder logic for histiocytic marker positivity. |
    | Hodgkin Lymphoma (Unspecified Subtype)                      | Hodgkin lymphoma without a specified marker profile. |
    | Mantle Cell Lymphoma                                        | B-cell lymphoma with (Cyclin D1 or t(11;14)) + CD5+. |
    | Marginal Zone Lymphoma                                      | B-cell lymphoma with marginal zone characteristics.  |
    | Mastocytosis (Suspected)                                    | Basic placeholder if mast cell involvement is noted. |
    | MDS (Refractory Anemia)                                     | MDS subtype primarily manifested as anemia.          |
    | MDS with Excess Blasts                                      | Blasts 5–19% in a myeloid context.                   |
    | MDS with Isolated del(5q)                                   | MDS subtype with 5q deletion.                        |
    | Multiple Myeloma (Plasma Cell Neoplasm)                     | Plasma cell malignancy indicated by CD138.           |
    | Myeloproliferative Neoplasm (MPN)                           | Chronic proliferation of myeloid lineages (JAK2/CALR/MPL). |
    | Mycosis Fungoides (Cutaneous T-Cell Lymphoma)               | T-cell lymphoma often with skin lesions or CD7 loss. |
    | Nodular Lymphocyte-Predominant HL (NLPHL)                   | Hodgkin variant with CD20 positivity and CD15/CD30 negativity. |
    | Peripheral T-Cell Lymphoma (PTCL)                           | T-cell non-Hodgkin lymphoma not fitting other subtypes. |
    | Primary CNS Lymphoma (DLBCL)                                | DLBCL confined to the central nervous system.        |
    | Refractory Cytopenia with Multilineage Dysplasia (RCMD)     | MDS subtype with multiple dysplastic lineages.       |
    | Undetermined Hematologic Neoplasm                           | Neoplasm that doesn’t meet specific classification.  |

    ---

    ## 4. How to Use the Classification Tool

    1. **Data Entry**: Provide accurate CBC values, immunophenotyping markers, cytogenetics, etc.
    2. **Classification**: Click **“Classify”** to run the logic and obtain a classification result.
    3. **Derivation**: Review the step-by-step explanation describing how each decision was made.
    4. **AI Review & Flowchart** (if authenticated):
       - Get additional insights or next-step recommendations from an AI summary.
       - Explore an interactive flowchart illustrating how each branching point led to the final classification.

    ---

    ## Important Considerations
    
    - **Data Quality**: All inputs must be **accurate** and **comprehensive** for an optimal match.
    - **Placeholder Entities**: Some conditions (e.g., Mastocytosis, Histiocytic Neoplasm) are flagged but not deeply elaborated.
    - **Clinical Correlation**: Always combine this tool’s results with full clinical evaluation, specialist consultation, and advanced diagnostics.
    - **Disclaimer**: This logic is **simplified** and not a substitute for professional pathology or oncological expertise.

    ---
    """, unsafe_allow_html=True)



##############################
# CLASSIFICATION
##############################
def classify_blood_cancer(
    blasts_percentage: float,
    lineage: str,
    is_b_cell: bool,
    is_t_cell: bool,
    is_nk_cell: bool,
    morphological_details: list,
    immunophenotype_markers: list,
    immunophenotype_special: list,  # e.g., ["Skin involvement", "CD7 loss", "Hairy cells"]
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
    Includes logic for:
      - Rare B-Cell Lymphomas (Mantle Cell, Marginal Zone, Primary CNS)
      - Aggressive Myeloid Cancers (BPDCN, AML-M6, AML-M7)
      - ALK for ALCL
      - immunophenotype_special for T-cell or special B-cell notes
    """

    decision_points = []
    additional_info = []
    classification = "Unspecified Hematologic Neoplasm"

    # Pediatric check
    pediatric_case = (patient_age < 18)
    if pediatric_case:
        additional_info.append("Patient is pediatric (<18), applying pediatric considerations.")

    # (1) Check for Multiple Myeloma
    if "CD138" in immunophenotype_markers:
        decision_points.append("Detected 'CD138' => Possible Multiple Myeloma.")
        classification = "Multiple Myeloma (Plasma Cell Neoplasm)"
    else:
        # (2) ACUTE vs CHRONIC
        if blasts_percentage >= 20:
            decision_points.append("Blasts >= 20% => Likely acute leukemia.")
            if lineage == "Myeloid":
                classification = "Acute Myeloid Leukemia (AML)"
                decision_points.append("Lineage: Myeloid => AML classification.")

                # AML Subtypes
                # -- Check for BPDCN first if we see CD123, CD4, CD56
                if all(m in immunophenotype_markers for m in ["CD123", "CD4", "CD56"]):
                    classification = "Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)"
                    decision_points.append("Detected CD123/CD4/CD56 => BPDCN (aggressive myeloid).")
                # -- AML-M6 (Erythroid)
                elif "Erythroid precursors" in morphological_details or any(m in immunophenotype_markers for m in ["Glycophorin A", "CD71"]):
                    classification = "Acute Erythroid Leukemia (AML-M6)"
                    decision_points.append("Erythroid lineage => AML-M6 subtype.")
                # -- AML-M7 (Megakaryoblastic)
                elif "Megakaryoblasts" in morphological_details or any(m in immunophenotype_markers for m in ["CD41", "CD42b", "CD61"]):
                    classification = "Acute Megakaryoblastic Leukemia (AML-M7)"
                    decision_points.append("Megakaryocyte markers => AML-M7 subtype.")
                # -- APL check
                elif "t(15;17)" in cytogenetic_abnormalities:
                    classification = "Acute Promyelocytic Leukemia (APL)"
                    decision_points.append("Detected t(15;17) => APL subtype.")
                # -- AML with t(8;21)
                elif "t(8;21)" in cytogenetic_abnormalities:
                    classification = "AML with t(8;21)"
                    decision_points.append("Detected t(8;21) => AML subtype.")
                # -- AML with inv(16)
                elif any(x in cytogenetic_abnormalities for x in ["inv(16)", "t(16;16)"]):
                    classification = "AML with inv(16)/t(16;16)"
                    decision_points.append("Detected inv(16)/t(16;16) => AML subtype.")
                else:
                    # Basic AML with FLT3 or NPM1
                    if "FLT3" in molecular_mutations:
                        classification = "AML with FLT3 Mutation"
                        decision_points.append("Detected FLT3 => AML with FLT3 mutation.")
                    elif "NPM1" in molecular_mutations:
                        classification = "AML with NPM1 Mutation"
                        decision_points.append("Detected NPM1 => AML with NPM1.")
            elif lineage == "Lymphoid":
                if pediatric_case:
                    classification = "Acute Lymphoblastic Leukemia (ALL, Pediatric)"
                    decision_points.append("Lymphoid + Pediatric => ALL (Pediatric).")
                else:
                    classification = "Acute Lymphoblastic Leukemia (ALL, Adult)"
                    decision_points.append("Lymphoid + Adult => ALL (Adult).")
            else:
                classification = "Acute Leukemia of Ambiguous Lineage"
                decision_points.append("Lineage undetermined => Possibly mixed phenotype.")
        else:
            decision_points.append("Blasts < 20% => Chronic or other non-acute neoplasm.")
            if lineage == "Myeloid":
                # Check for MPN driver
                mpn_drivers = {"JAK2", "CALR", "MPL"}
                if mpn_drivers.intersection(set(molecular_mutations)):
                    classification = "Myeloproliferative Neoplasm (MPN)"
                    decision_points.append("Detected MPN driver => MPN classification.")
                else:
                    # MDS checks
                    blasts_for_mds = blasts_percentage
                    has_del5q = any("del(5q)" in ab.lower() for ab in cytogenetic_abnormalities)
                    dysplasia_count = sum(
                        x in morphological_details
                        for x in [
                            "Dyserythropoiesis",
                            "Dysgranulopoiesis",
                            "Dysmegakaryopoiesis",
                            "Multilineage dysplasia"
                        ]
                    )
                    if 5 <= blasts_for_mds < 20:
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
                            classification = "Chronic Myeloid Leukemia (CML)"
                            decision_points.append("Defaulting to CML classification.")

                if "Ring sideroblasts" in morphological_details:
                    additional_info.append("Ring sideroblasts => Possibly MDS w/ ring sideroblasts or overlap.")

            elif lineage == "Lymphoid":
                # Hodgkin check
                if hodgkin_markers:
                    decision_points.append("Suspect Hodgkin => Checking markers.")
                    if cd15_positive and cd30_positive:
                        classification = "Classical Hodgkin Lymphoma"
                        decision_points.append("CD15+ and CD30+ => Classical Hodgkin.")
                    else:
                        if cd20_positive and not cd30_positive and not cd15_positive:
                            classification = "Nodular Lymphocyte-Predominant Hodgkin Lymphoma (NLPHL)"
                            decision_points.append("CD20+ only => NLPHL (Hodgkin).")
                        else:
                            classification = "Hodgkin Lymphoma (Unspecified Subtype)"
                            decision_points.append("Hodgkin markers => Unspecified subtype.")
                else:
                    # Non-Hodgkin T vs B
                    if is_b_cell:
                        # -- FIRST: Rare B-Cell expansions
                        # 1) Mantle Cell => (Cyclin D1 or t(11;14)) + CD5+ + often CD23-
                        if any("t(11;14) CCND1-IGH" in ab for ab in cytogenetic_abnormalities) or "Cyclin D1" in immunophenotype_markers:
                            if "CD5" in immunophenotype_markers and "CD23" not in immunophenotype_markers:
                                classification = "Mantle Cell Lymphoma"
                                decision_points.append("Detected t(11;14)/Cyclin D1 + CD5+ => Mantle Cell.")
                        # 2) Marginal Zone => typically CD20+, CD79a+, CD5-, CD10-
                        elif ("CD20" in immunophenotype_markers or "CD79a" in immunophenotype_markers) \
                             and "CD5" not in immunophenotype_markers \
                             and "CD10" not in immunophenotype_markers:
                            classification = "Marginal Zone Lymphoma"
                            decision_points.append("CD20/CD79a, no CD5/CD10 => Marginal Zone Lymphoma.")
                        # 3) Primary CNS => often DLBCL with BCL6, CD20, confined to CNS (not fully captured here)
                        elif "BCL6" in immunophenotype_markers and "CD20" in immunophenotype_markers and "CNS involvement" in immunophenotype_special:
                            classification = "Primary CNS Lymphoma (DLBCL)"
                            decision_points.append("CD20/BCL6 + CNS involvement => Primary CNS Lymphoma.")
                        else:
                            # Check for Burkitt’s
                            has_myc = ("MYC" in molecular_mutations) or any("t(8;14)" in ab for ab in cytogenetic_abnormalities)
                            if has_myc and "CD10" in immunophenotype_markers:
                                classification = "Burkitt's Lymphoma (High-Grade B-Cell NHL)"
                                decision_points.append("Detected MYC/t(8;14) + CD10 => Burkitt's Lymphoma.")
                            else:
                                # Follicular
                                if "CD10" in immunophenotype_markers:
                                    classification = "Follicular Lymphoma (Non-Hodgkin)"
                                    decision_points.append("CD10 => Follicular Lymphoma.")
                                else:
                                    classification = "Diffuse Large B-Cell Lymphoma (DLBCL)"
                                    decision_points.append("B-cell => DLBCL (default).")

                    elif is_t_cell:
                        # ALCL: CD30+ T-cell + ALK in cytogenetics
                        if cd30_positive:
                            if "ALK" in cytogenetic_abnormalities:
                                classification = "Anaplastic Large Cell Lymphoma (ALCL, ALK+)"
                                decision_points.append("T-cell + CD30+ + ALK => ALCL (ALK+).")
                            else:
                                classification = "Anaplastic Large Cell Lymphoma (ALCL, ALK–)"
                                decision_points.append("T-cell + CD30+ => ALCL (ALK–).")
                        # AITL => CD10 + (PD-1 or CXCL13 or BCL6)
                        elif ("CD10" in immunophenotype_markers) and (
                            any(x in immunophenotype_markers for x in ["PD-1", "CXCL13"])
                            or "BCL6" in molecular_mutations
                        ):
                            classification = "Angioimmunoblastic T-Cell Lymphoma (AITL)"
                            decision_points.append("T-cell + CD10 + PD-1/CXCL13/BCL6 => AITL.")
                        # Mycosis Fungoides => "CD4" + "CD7 loss" or "Skin involvement"
                        elif ("CD4" in immunophenotype_markers and "CD7 loss" in immunophenotype_special) or \
                             ("Skin involvement" in immunophenotype_special):
                            classification = "Cutaneous T-Cell Lymphoma (Mycosis Fungoides)"
                            decision_points.append("T-cell + CD4 + CD7 loss or Skin => Mycosis Fungoides.")
                        else:
                            classification = "Peripheral T-Cell Lymphoma (Non-Hodgkin)"
                            decision_points.append("Detected T-cell => PTCL (NHL).")
                    else:
                        classification = "Chronic Lymphocytic Leukemia (CLL)"
                        decision_points.append("Defaulting to CLL (lymphoid).")
                        # Check if "Hairy cells" in special flags
                        if "Hairy cells" in immunophenotype_special:
                            classification = "Hairy Cell Leukemia (Rare B-Cell Neoplasm)"
                            decision_points.append("Detected 'Hairy cells' => Hairy Cell Leukemia.")
            else:
                classification = "Other Chronic Hematologic Neoplasm"
                decision_points.append("Lineage undetermined => Possibly rare entity.")

    # Collect additional info
    if immunophenotype_special:
        additional_info.append(f"Special immunophenotype flags: {', '.join(immunophenotype_special)}.")
    if cytogenetic_abnormalities:
        additional_info.append(f"Cytogenetic abnormalities: {', '.join(cytogenetic_abnormalities)}.")
    if molecular_mutations:
        additional_info.append(f"Molecular mutations: {', '.join(molecular_mutations)}.")

    # Build the derivation string
    derivation = log_derivation(
        blasts=blasts_percentage,
        lineage=lineage,
        decision_points=decision_points,
        additional_info=additional_info
    )

    return classification, derivation, decision_points


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
# AI Review
##############################
def get_gpt4_review(
    classification: str,
    explanation: str,
    user_inputs: dict
) -> str:
    """
    Sends the classification, explanation, and all user input data to AI
    for review and next steps.
    """
    # Create a readable string of user inputs
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

    # Send to AI
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Or "gpt-4" if your environment supports it
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
    Primary Streamlit app function using the updated classification logic.
    Includes new inputs relevant for:
      - Rare B-Cell Lymphomas (Mantle Cell, Marginal Zone, Primary CNS)
      - Aggressive Myeloid Cancers (BPDCN, AML-M6, AML-M7)
      - ALK for ALCL detection
      - immunophenotype_special for T-cell notes (e.g., CD7 loss, Skin involvement, Hairy cells)
    """
    
    # Sidebar for Explanation and Authentication
    st.sidebar.header("Navigation")
    if st.sidebar.button("Show Explanation"):
        st.session_state["show_explanation"] = True
    
    if st.session_state.get("show_explanation", False):
        show_explanation()
        return
    
    # Introduction Section
    st.markdown("""
    <div style="background-color: #e7f3fe; padding: 20px; border-radius: 10px;">
    <h2 style="color: #31708f;">WHO Hematologic Classification Tool</h2>
    <p>
        This app classifies hematologic malignancies based on user inputs. 
    </p>
    <p><em>Disclaimer:</em> This tool is for <strong>educational demonstration</strong> only and is not a clinical or diagnostic tool.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 1) Complete Blood Count (CBC)
    with st.container():
        st.subheader("1. Complete Blood Count (CBC)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            wbc_count = st.number_input("WBC (x10^9/L)", min_value=0.0, value=7.5, step=0.1, help="White Blood Cell Count")
        with col2:
            rbc_count = st.number_input("RBC (x10^12/L)", min_value=0.0, value=4.5, step=0.1, help="Red Blood Cell Count")
        with col3:
            platelet_count = st.number_input("Platelet (x10^9/L)", min_value=0.0, value=250.0, step=10.0, help="Platelet Count")
        with col4:
            eosinophil_count = st.number_input("Eosinophils (x10^9/L)", min_value=0.0, value=0.2, step=0.1, help="Eosinophil Count")
    
    st.markdown("---")
    
    # 2) Bone Marrow Blasts (%)
    with st.container():
        st.subheader("2. Bone Marrow Blasts (%)")
        blasts_percentage = st.slider("Blasts in marrow (%)", 0, 100, 5, help="Percentage of Blasts in Bone Marrow")
    
    st.markdown("---")
    
    # 3) Morphological Details
    with st.container():
        st.subheader("3. Morphological Details")
        morphological_options = [
            "Auer rods",
            "Granular promyelocytes",
            "Ring sideroblasts",
            "Dyserythropoiesis",
            "Dysgranulopoiesis",
            "Dysmegakaryopoiesis",
            "Micromegakaryocytes",
            "Starry sky pattern",    # e.g., Burkitt's
            "Erythroid precursors", # e.g., AML-M6
            "Megakaryoblasts"       # e.g., AML-M7
        ]
        morphological_details = st.multiselect("Select observed morphological features:", morphological_options, help="Choose all that apply based on bone marrow examination.")
    
    st.markdown("---")
    
    # 4) Additional MDS/MPN Overlap
    with st.container():
        st.subheader("4. Additional Counts for MDS/MPN Overlap")
        col5, col6 = st.columns(2)
        with col5:
            monocyte_count = st.number_input("Monocyte count (x10^9/L)", min_value=0.0, value=0.5, step=0.1, help="Monocyte Count")
        with col6:
            patient_age = st.number_input("Patient age (years)", min_value=0, max_value=120, value=50, step=1, help="Age of the patient in years")
    
    st.markdown("---")
    
    # 5) Dominant Lineage
    with st.container():
        st.subheader("5. Dominant Lineage (User Assessment)")
        lineage = st.radio("Predominant lineage:", ["Myeloid", "Lymphoid", "Undetermined"], index=1, help="Select the predominant cell lineage based on clinical assessment.")
        is_b_cell = False
        is_t_cell = False
        is_nk_cell = False
        if lineage == "Lymphoid":
            subset = st.selectbox("Lymphoid subset (if known):", ["Unknown", "B-cell", "T-cell", "NK-cell"], index=0, help="Select the specific lymphoid subset if identified.")
            if subset == "B-cell":
                is_b_cell = True
            elif subset == "T-cell":
                is_t_cell = True
            elif subset == "NK-cell":
                is_nk_cell = True
    
    st.markdown("---")
    
    # 6) Immunophenotyping Markers and 6a) Special Immunophenotype Flags
    with st.container():
        st.subheader("6. Immunophenotyping")
        col6a_1, col6a_2 = st.columns(2)
        with col6a_1:
            st.markdown("**6.1. Immunophenotyping Markers**")
            marker_choices = [
                # T and NK
                "CD2", "CD3", "CD4", "CD5", "CD7", "CD8", "CD10", "CD14", "CD15", "CD19", "CD20",
                "CD23", "CD30", "CD34", "CD45", "CD56", "CD79a", "CD123", 
                "Myeloperoxidase (MPO)", 
                # Additional for B-cells
                "Cyclin D1",  # Mantle Cell
                "BCL6",       # e.g., CNS lymphoma, DLBCL
                "CD71",       # AML-M6
                "CD41", "CD42b", "CD61"  # AML-M7
            ]
            immunophenotype_markers = st.multiselect(
                "Select Positive Markers:", 
                marker_choices, 
                help="Choose all immunophenotypic markers that are positive in the patient's cells."
            )
        with col6a_2:
            st.markdown("**6.2. Special Immunophenotype Flags**")
            special_flags_options = [
                "Skin involvement", 
                "CD7 loss",
                "Hairy cells",
                "CNS involvement"  # Added for Primary CNS Lymphoma
            ]
            immunophenotype_special = st.multiselect(
                "Select any special flags that apply:", 
                special_flags_options,
                help="Select any special immunophenotypic features observed."
            )
    
    st.markdown("---")
    
    # 7) Cytogenetic Abnormalities and 7a) Molecular Mutations
    st.subheader("7. Cytogenetic & Molecular")
    col7_1, col7_2 = st.columns(2)
    with col7_1:
        st.markdown("**7.1. Cytogenetic Abnormalities**")
        cytogenetic_samples = [
            "t(15;17)", "t(8;21)", "inv(16)", "t(16;16)", "t(9;22) BCR-ABL1", 
            "t(12;21)", "t(1;19)", "t(11;14) CCND1-IGH",  # Mantle cell
            "t(14;18) BCL2-IGH",  # Follicular
            "t(8;14) MYC-IGH",    # Burkitt's
            "ALK",                # ALCL
            "Other"
        ]
        cytogenetic_abnormalities = st.multiselect(
            "Select Cytogenetic Abnormalities:", 
            cytogenetic_samples,
            help="Choose all cytogenetic abnormalities identified in the patient's cells."
        )
    with col7_2:
        st.markdown("**7.2. Molecular Mutations**")
        mutation_samples = [
            "FLT3", "NPM1", "CEBPA", "RUNX1", "JAK2", "CALR", "MPL", "BCR-ABL1",
            "KMT2A (MLL)", "ETV6-RUNX1", "TCF3-PBX1", "MYC", "BCL2", "BCL6", "CCND1",
            "TET2", "SRSF2", "SF3B1", "IDH1", "IDH2", "ASXL1", "HTLV-1", 
            "HYPERDIPLOID", "HYPODIPLOID",
            "Other"
        ]
        molecular_mutations = st.multiselect(
            "Select Molecular Mutations:", 
            mutation_samples,
            help="Select all molecular mutations identified in the patient's cells."
        )

    st.markdown("---")
    
    # 8) Special Entities
    with st.container():
        st.subheader("8. Special Entities")
        col8_1, col8_2 = st.columns(2)
        with col8_1:
            mast_cell_involvement = st.checkbox("Suspect Mastocytosis?", help="Check if mast cell neoplasm is suspected.")
            histiocytic_marker = st.checkbox("Suspect Histiocytic/Dendritic Cell Neoplasm?", help="Check if histiocytic or dendritic cell neoplasm is suspected.")
        with col8_2:
            hodgkin_markers = st.checkbox("Suspect Hodgkin Lymphoma?", help="Check if Hodgkin Lymphoma is suspected.")
            cd15_positive = st.checkbox("CD15+ (Hodgkin)?", help="Check if CD15 marker is positive.")
            cd30_positive = st.checkbox("CD30+ (Hodgkin)?", help="Check if CD30 marker is positive.")
            cd20_positive = st.checkbox("CD20+ (Hodgkin)?", help="Check if CD20 marker is positive.")
            cd45_negative = st.checkbox("CD45- (Hodgkin)?", help="Check if CD45 marker is negative.")
    
    st.markdown("---")
    
    # CLASSIFY button
    with st.container():
        if st.button("🔍 Classify"):
            # 1) Validate Inputs
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
                    st.error(f"⚠️ **Error:** {error}")
                st.stop()
    
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ **Warning:** {warning}")
    
            # 2) Classification
            classification, derivation_string, decision_points = classify_blood_cancer(
                blasts_percentage=blasts_percentage,
                lineage=lineage,
                is_b_cell=is_b_cell,
                is_t_cell=is_t_cell,
                is_nk_cell=is_nk_cell,
                morphological_details=morphological_details,
                immunophenotype_markers=immunophenotype_markers,
                immunophenotype_special=immunophenotype_special, # New param
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
    
            # 3) Build user_inputs dict
            user_inputs = {
                "blasts_percentage": blasts_percentage,
                "lineage": lineage,
                "is_b_cell": is_b_cell,
                "is_t_cell": is_t_cell,
                "is_nk_cell": is_nk_cell,
                "morphological_details": morphological_details,
                "immunophenotype_markers": immunophenotype_markers,
                "immunophenotype_special": immunophenotype_special,  # collecting special flags
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
            <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                <h3 style='color: #0f5132;'>Classification Result</h3>
                <p style='color: #0f5132; font-size: 1.2rem;'><strong>{classification}</strong></p>
            </div>
            """, unsafe_allow_html=True)
    
            # 5) Display derivation
            display_derivation(derivation_string)
    
            # 6) AI Review and Clinical Next Steps
            if st.session_state['authenticated']:
                with st.spinner("Generating AI review and clinical next steps..."):
                    gpt4_review_result = get_gpt4_review(
                        classification=classification,
                        explanation=derivation_string,
                        user_inputs=user_inputs
                    )
                st.markdown("### **AI Review & Clinical Next Steps**")
                st.markdown(f"""
                    <div style='background-color: #cff4fc; padding: 15px; border-radius: 10px;'>
                        {gpt4_review_result}
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info("🔒 **Log in** to receive an AI-generated review and clinical recommendations.")
    
            # 7) Interactive Classification Flowchart
            if decision_points:
                flowchart_src = build_decision_flowchart(classification, decision_points)
                st.markdown("### **Interactive Classification Flowchart**")
                st.graphviz_chart(flowchart_src)
            else:
                st.warning("⚠️ No decision points available to display in the flowchart.")
    
            # Final Disclaimer
            st.markdown("""
            ---
            <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
                <p><strong>Disclaimer:</strong> This app is a simplified demonstration and <strong>not</strong> a replacement 
                for professional pathology review or real-world WHO classification.</p>
            </div>
            """, unsafe_allow_html=True)


def main():
    app_main()

if __name__ == "__main__":
    main()
