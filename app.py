import streamlit as st
import bcrypt
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Initialize OpenAI API key from secrets

# ----------------------------
# Password Verification Functions
# ----------------------------

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

# ----------------------------
# Authentication State Management
# ----------------------------

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''

# Sidebar for login/logout
def login_logout():
    if st.session_state['authenticated']:
        st.sidebar.write(f"Logged in as **{st.session_state['username']}**")
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

# Execute the login/logout function
login_logout()

# ----------------------------
# Input Validation Function
# ----------------------------
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

    # Convert cytogenetic abnormalities and molecular mutations to uppercase for consistent comparison
    cytogen_list_upper = [ab.upper() for ab in cytogenetic_abnormalities]
    mutation_list_upper = [m.upper() for m in molecular_mutations]

    # 1. Validate numerical ranges
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

    # 2. Lineage vs. markers consistency
    myeloid_markers = ["Myeloperoxidase (MPO)"]
    lymphoid_markers = ["CD19", "CD20", "CD79a", "CD2", "CD3", "CD5", "CD7", "CD56"]

    # Check if lineage matches markers
    if lineage == "Myeloid" and not any(marker in immunophenotype_markers for marker in myeloid_markers):
        warnings.append("Lineage set to Myeloid, but no myeloid markers detected.")

    if lineage == "Lymphoid":
        if is_b_cell and not any(marker in immunophenotype_markers for marker in ["CD19", "CD20", "CD79a"]):
            warnings.append("Lineage set to Lymphoid (B-cell), but no B-cell markers detected.")
        if is_t_cell and not any(marker in immunophenotype_markers for marker in ["CD2", "CD3", "CD5", "CD7"]):
            warnings.append("Lineage set to Lymphoid (T-cell), but no T-cell markers detected.")
        if is_nk_cell and "CD56" not in immunophenotype_markers:
            warnings.append("Lineage set to Lymphoid (NK-cell), but CD56 marker not detected.")

    # 3. Morphological findings vs. lineage
    if lineage == "Lymphoid" and "Ring sideroblasts" in morphological_details:
        warnings.append("Ring sideroblasts are typically associated with myeloid disorders, not lymphoid.")

    # 4. Detect conflicting lineage markers
    if lineage == "Myeloid" and any(marker in immunophenotype_markers for marker in ["CD19", "CD20", "CD79a", "CD2", "CD3", "CD5", "CD7", "CD56"]):
        warnings.append("Myeloid lineage selected, but lymphoid markers detected.")

    if lineage == "Lymphoid" and any(marker in immunophenotype_markers for marker in myeloid_markers):
        warnings.append("Lymphoid lineage selected, but myeloid markers detected.")

    # 5. Detect possible mixed phenotype
    if lineage == "Undetermined" and (is_b_cell or is_t_cell or is_nk_cell):
        warnings.append("Lineage undetermined, but specific lymphoid subsets detected.")

    # 6. Additional Checks
    if "Ring sideroblasts" in morphological_details and "INV(16)" in cytogen_list_upper:
        warnings.append("Ring sideroblasts and inv(16) are typically associated with myeloid neoplasms.")

    return errors, warnings

# ----------------------------
# Classification Logic Function
# ----------------------------
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
    Enhanced classification logic with derivation/explanation tracking.
    Returns a tuple of (classification, explanation list).
    """
    explanation = []

    # ------------------------------------------------
    # (A) INITIAL PROCESSING & FLAGS
    # ------------------------------------------------
    explanation.append(f"Blasts: {blasts_percentage}%. " 
                       f"Lineage (user-chosen): {lineage}. "
                       f"Monocyte count: {monocyte_count}, Age: {patient_age}")

    # Summaries for morphology & immunophenotyping
    if morphological_details:
        explanation.append(f"Morphological findings: {', '.join(morphological_details)}.")
    if immunophenotype_markers:
        explanation.append(f"Immunophenotype markers: {', '.join(immunophenotype_markers)}.")
    if immunophenotype_notes:
        explanation.append(f"Additional immunophenotype notes: {immunophenotype_notes}")

    if cytogenetic_abnormalities:
        explanation.append(f"Cytogenetic abnormalities: {', '.join(cytogenetic_abnormalities)}.")
    if molecular_mutations:
        explanation.append(f"Molecular mutations: {', '.join(molecular_mutations)}.")

    # We’ll track “decision points” in a variable named `decision_points`
    decision_points = []

    # Set up flags from morphological details
    has_auer_rods = ("Auer rods" in morphological_details)
    has_ring_sideroblasts = ("Ring sideroblasts" in morphological_details)
    dysplasia_count = sum(
        x in morphological_details
        for x in ["Dyserythropoiesis", "Dysgranulopoiesis", "Dysmegakaryopoiesis", "Micromegakaryocytes"]
    )

    # ------------------------------
    # (B) IMMUNOPHENOTYPE PROCESSING
    # ------------------------------
    # Override lineage if we see clear myeloid or lymphoid markers
    if "Myeloperoxidase (MPO)" in immunophenotype_markers:
        lineage = "Myeloid"
        decision_points.append("Detected MPO -> Setting lineage to Myeloid.")

    if any(m in immunophenotype_markers for m in ["CD19", "CD20", "CD79a"]):
        is_b_cell = True
        is_t_cell = False
        is_nk_cell = False
        lineage = "Lymphoid"
        decision_points.append("Detected B-cell markers (CD19/CD20/CD79a) -> Setting lineage to Lymphoid (B-cell).")

    if any(m in immunophenotype_markers for m in ["CD2", "CD3", "CD5", "CD7"]):
        is_t_cell = True
        is_b_cell = False
        is_nk_cell = False
        lineage = "Lymphoid"
        decision_points.append("Detected T-cell markers (CD2/CD3/CD5/CD7) -> Setting lineage to Lymphoid (T-cell).")

    if "CD56" in immunophenotype_markers and not is_t_cell and not is_b_cell:
        is_nk_cell = True
        lineage = "Lymphoid"
        decision_points.append("Detected NK marker (CD56) with no T/B -> Setting lineage to Lymphoid (NK-cell).")

    # Set up flags from cytogenetics & mutations
    cytogen_list_upper = [ab.upper() for ab in cytogenetic_abnormalities]
    mutation_list_upper = [m.upper() for m in molecular_mutations]

    # Common flags
    has_bcr_abl = any("BCR-ABL" in mut for mut in mutation_list_upper) or ("T(9;22) BCR-ABL1" in cytogen_list_upper)
    has_jak2 = any("JAK2" in mut for mut in mutation_list_upper)
    has_calr = any("CALR" in mut for mut in mutation_list_upper)
    has_mpl = any("MPL" in mut for mut in mutation_list_upper)

    # AML-likely flags
    has_t_1517 = ("T(15;17)" in cytogen_list_upper)
    has_t_821 = ("T(8;21)" in cytogen_list_upper)
    has_inv16 = any(x in cytogen_list_upper for x in ["INV(16)", "T(16;16)"])

    # ALL-likely flags
    has_etv6_runx1 = any("ETV6-RUNX1" in mut for mut in mutation_list_upper) or ("T(12;21)" in cytogen_list_upper)
    has_tcf3_pbx1 = any("TCF3-PBX1" in mut for mut in mutation_list_upper) or ("T(1;19)" in cytogen_list_upper)

    # KMT2A, NPM1, FLT3, etc.
    has_npm1 = any("NPM1" in mut for mut in mutation_list_upper)
    has_flt3 = any("FLT3" in mut or "FLT3-ITD" in mut for mut in mutation_list_upper)
    has_kmt2a = any("KMT2A" in mut or "MLL" in mut for mut in mutation_list_upper)
    has_cebpa = any("CEBPA" in mut for mut in mutation_list_upper)
    has_runx1 = any("RUNX1" in mut for mut in mutation_list_upper)

    # For MDS & MDS/MPN, commonly mutated epigenetic/splicing genes
    has_mds_epigenetic = any(gene in mutation_list_upper for gene in ["TET2", "SRSF2", "SF3B1", "IDH1", "IDH2", "ASXL1"])

    # ------------------------------
    # (C) CLASSIFICATION LOGIC
    # ------------------------------
    # Start classification result as None
    final_classification = None

    # ------------------------------------------------
    # (D) CHECK FOR SPECIAL ENTITIES FIRST
    # ------------------------------------------------
    if histiocytic_marker:
        decision_points.append("Histiocytic marker present -> Histiocytic or Dendritic Cell Neoplasm.")
        final_classification = "Histiocytic or Dendritic Cell Neoplasm"

    if mast_cell_involvement and not final_classification:
        decision_points.append("Mast cell involvement -> Mastocytosis.")
        final_classification = "Mastocytosis (Systemic or Cutaneous)"

    if hodgkin_markers and not final_classification:
        if cd15_positive and cd30_positive:
            decision_points.append("CD15+ and CD30+ -> Classic Hodgkin Lymphoma.")
            final_classification = "Classic Hodgkin Lymphoma (CD15+, CD30+)"
        else:
            if cd20_positive and not cd30_positive and not cd15_positive and not cd45_negative:
                decision_points.append("CD20+ only -> Nodular Lymphocyte-Predominant Hodgkin Lymphoma.")
                final_classification = "Nodular Lymphocyte-Predominant Hodgkin Lymphoma (NLPHL)"
            else:
                decision_points.append("Suspect Hodgkin Lymphoma -> Unspecified subtype.")
                final_classification = "Hodgkin Lymphoma (Unspecified Subtype)"

    # If we already have a classification from the special entities, skip the rest
    if final_classification:
        explanation.append("Decision Points:\n" + "\n".join(f"- {dp}" for dp in decision_points))
        return final_classification, explanation

    # ------------------------------------------------
    # (E) ACUTE LEUKEMIAS (>=20% blasts)
    # ------------------------------------------------
    if blasts_percentage >= 20:
        decision_points.append(f"Blasts >= 20% -> Consider acute leukemia in lineage {lineage}.")
        if lineage == "Myeloid":
            # Very simplified AML logic:
            if "T(15;17)" in cytogen_list_upper:
                decision_points.append("Detected t(15;17) -> APL (Acute Promyelocytic Leukemia).")
                final_classification = "Acute Promyelocytic Leukemia (APL, AML with t(15;17))"
            else:
                if has_bcr_abl:
                    decision_points.append("Detected BCR-ABL in myeloid blasts -> AML with BCR-ABL1.")
                    final_classification = "Acute Myeloid Leukemia with BCR-ABL1"
                else:
                    decision_points.append("Myeloid blasts >=20%, no special translocation -> AML (NOS).")
                    final_classification = "Acute Myeloid Leukemia (NOS / Other Subtype)"
        elif lineage == "Lymphoid":
            if is_b_cell:
                decision_points.append("Blasts >=20%, lineage = B -> B-ALL.")
                final_classification = "B-ALL (General Category)"
            elif is_t_cell:
                decision_points.append("Blasts >=20%, lineage = T -> T-ALL.")
                final_classification = "T-ALL (T-Lymphoblastic Leukemia)"
            elif is_nk_cell:
                decision_points.append("Blasts >=20%, lineage = NK -> Very rare NK-ALL.")
                final_classification = "NK-ALL (Very Rare)"
            else:
                decision_points.append("Blasts >=20%, lineage = Lymphoid ambiguous -> ALL ambiguous lineage.")
                final_classification = "Acute Lymphoblastic Leukemia of Ambiguous Lineage"
        else:
            decision_points.append("Blasts >=20%, lineage undetermined -> Mixed phenotype acute leukemia possible.")
            final_classification = "Acute Leukemia of Ambiguous / Mixed Phenotype"

        explanation.append("Decision Points:\n" + "\n".join(f"- {dp}" for dp in decision_points))
        return final_classification, explanation

    # ------------------------------------------------
    # (F) CHRONIC OR OTHER (BLASTS < 20%)
    # ------------------------------------------------
    decision_points.append("Blasts < 20% -> Consider chronic or other neoplasms.")

    if lineage == "Myeloid":
        # Example: CML, MPN, MDS, MDS/MPN Overlap
        if has_bcr_abl:
            decision_points.append("Detected BCR-ABL in myeloid cells -> CML.")
            final_classification = "Chronic Myeloid Leukemia (CML, BCR-ABL1+)"
        elif has_jak2 or has_calr or has_mpl:
            decision_points.append("Detected MPN driver mutation (JAK2/CALR/MPL) -> MPN.")
            if rbc_count > 6.0:
                final_classification = "Polycythemia Vera"
                decision_points.append("High RBC -> Polycythemia Vera.")
            elif platelet_count > 450:
                final_classification = "Essential Thrombocythemia"
                decision_points.append("High Platelets -> Essential Thrombocythemia.")
            else:
                final_classification = "Primary Myelofibrosis or Other MPN"
                decision_points.append("Normal RBC/PLT but MPN driver -> Possible Myelofibrosis or other MPN.")
        else:
            # MDS vs. MDS/MPN Overlap
            cytopenias = 0
            if wbc_count < 4.0:
                cytopenias += 1
            if rbc_count < 3.8:
                cytopenias += 1
            if platelet_count < 150:
                cytopenias += 1

            if has_ring_sideroblasts and platelet_count > 450:
                decision_points.append("Ring sideroblasts + thrombocytosis -> RARS-T (MDS/MPN overlap).")
                final_classification = "MDS/MPN: RARS-T"
            elif has_ring_sideroblasts:
                decision_points.append("Ring sideroblasts -> RARS (MDS).")
                final_classification = "MDS with Ring Sideroblasts"
            else:
                # Check for monocytes for CMML/aCML/JMML
                if monocyte_count >= 1.0:
                    if patient_age < 18:
                        decision_points.append("Elevated monocytes + pediatric -> JMML.")
                        final_classification = "Juvenile Myelomonocytic Leukemia (JMML)"
                    else:
                        decision_points.append("Elevated monocytes + adult -> CMML.")
                        final_classification = "Chronic Myelomonocytic Leukemia (CMML)"
                else:
                    # aCML possibility
                    if wbc_count > 13 and "Dysgranulopoiesis" in morphological_details and not has_bcr_abl:
                        decision_points.append("High WBC, dysgranulopoiesis, no BCR-ABL -> aCML.")
                        final_classification = "Atypical Chronic Myeloid Leukemia (aCML, BCR-ABL1–)"
                    else:
                        # If we have multiple dysplastic lines
                        if cytopenias >= 2 or dysplasia_count >= 2:
                            decision_points.append("Multiple cytopenias/dysplasia -> MDS.")
                            final_classification = "Myelodysplastic Syndrome (MDS)"
                        else:
                            decision_points.append("Possible MDS/MPN overlap.")
                            final_classification = "MDS/MPN Overlap or Other Chronic Myeloid Neoplasm"

    elif lineage == "Lymphoid":
        # B/T/NK Chronic
        if is_b_cell:
            # CLL detection (CD5+ CD23+)
            if "CD5" in immunophenotype_markers and "CD23" in immunophenotype_markers:
                decision_points.append("CD5+CD23+ B cells -> CLL.")
                final_classification = "Chronic Lymphocytic Leukemia (CLL)"
            else:
                # Rare B-cell possibilities
                if "PLASMABLASTIC" in immunophenotype_notes.upper():
                    decision_points.append("Detected 'Plasmablastic' -> Plasmablastic Lymphoma (rare).")
                    final_classification = "Plasmablastic Lymphoma"
                else:
                    decision_points.append("Mature B-cell neoplasm (no specific subtype triggers).")
                    final_classification = "Mature B-Cell Neoplasm (Further Subclassification Needed)"
        elif is_t_cell:
            # If we detect “MYCOSIS FUNGOIDES” or “SÉZARY” in notes => Cutaneous T-cell
            if "MYCOSIS FUNGOIDES" in immunophenotype_notes.upper() or "SÉZARY" in immunophenotype_notes.upper():
                decision_points.append("Detected 'Mycosis Fungoides'/'Sézary' -> Cutaneous T-Cell Lymphoma.")
                final_classification = "Cutaneous T-Cell Lymphoma (Mycosis Fungoides / Sézary Syndrome)"
            else:
                decision_points.append("Peripheral T-Cell Lymphoma or other T-cell entity.")
                final_classification = "Peripheral T-Cell Lymphoma (NOS or Other Subtype)"
        elif is_nk_cell:
            decision_points.append("Chronic NK-cell neoplasm (e.g., NK Lymphoma).")
            final_classification = "NK-Cell Lymphoproliferative Disorder or NK-Cell Lymphoma"
        else:
            decision_points.append("Undetermined chronic lymphoid neoplasm.")
            final_classification = "Undetermined Chronic Lymphoid Neoplasm"
    else:
        decision_points.append("Lineage undetermined, blasts <20% -> 'Other Hematologic Neoplasm'.")
        final_classification = "Undetermined or Other Hematologic Neoplasm"

    # Append decision points to explanation
    explanation.append("Decision Points:\n" + "\n".join(f"- {dp}" for dp in decision_points))
    return final_classification, explanation

# ----------------------------
# GPT-4 Review Function
# ----------------------------
def get_gpt4_review(classification: str, explanation: str) -> str:
    """
    Sends the classification and explanation to GPT-4 for review and next steps.
    Returns the GPT-4's response.
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
        response = client.chat.completions.create(model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a knowledgeable hematologist."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.2)
        review = response.choices[0].message.content.strip()
        return review
    except Exception as e:
        return f"Error communicating with OpenAI: {str(e)}"

# ----------------------------
# Main Application Function
# ----------------------------
def app_main():
    st.title("WHO Classification Demo Tool")

    st.markdown("""
    This **Streamlit** app classifies hematologic malignancies based on user inputs and provides an **automated review** and **clinical next steps** using OpenAI's GPT-4.

    **Disclaimer**: This tool is for educational demonstration only and is **not** a clinical or diagnostic tool.
    """)

    st.markdown("---")

    # 1) CBC
    st.subheader("1. Complete Blood Count (CBC)")
    wbc_count = st.number_input("WBC (x10^9/L)", min_value=0.0, value=7.5, step=0.1)
    rbc_count = st.number_input("RBC (x10^12/L)", min_value=0.0, value=4.5, step=0.1)
    platelet_count = st.number_input("Platelet (x10^9/L)", min_value=0.0, value=250.0, step=10.0)
    eosinophil_count = st.number_input("Absolute eosinophil count (x10^9/L)", min_value=0.0, value=0.2, step=0.1)

    # 2) Blasts
    st.subheader("2. Bone Marrow Blasts (%)")
    blasts_percentage = st.slider("Blasts in marrow (%)", 0, 100, 5)

    # 3) Morphology
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

    # 4) Additional counts relevant to MDS/MPN
    st.subheader("4. Additional Counts for MDS/MPN Overlap")
    monocyte_count = st.number_input("Monocyte count (x10^9/L)", min_value=0.0, value=0.5, step=0.1)
    patient_age = st.number_input("Patient age (years)", min_value=0.0, value=50.0, step=1.0)

    # 5) Lineage
    st.subheader("5. Dominant Lineage (User Assessment)")
    lineage = st.radio(
        "Predominant lineage:",
        ["Myeloid", "Lymphoid", "Undetermined"],
        index=1
    )

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

    # 6) Immunophenotyping
    st.subheader("6. Immunophenotyping Markers")
    marker_choices = [
        "CD2", "CD3", "CD4", "CD5", "CD7", "CD8", "CD10", "CD14", "CD15", "CD19", "CD20",
        "CD23", "CD30", "CD34", "CD45", "CD56", "CD79a", "Myeloperoxidase (MPO)",
    ]
    immunophenotype_markers = st.multiselect("Positive markers:", marker_choices)
    immunophenotype_notes = st.text_input(
        "Additional immunophenotype notes (e.g., 'Follicular', 'Mantle', 'Plasmablastic', 'Sézary', etc.)"
    )

    # 7) Cytogenetics & Molecular
    st.subheader("7. Cytogenetic Abnormalities (Multi-Select)")
    cytogenetic_samples = [
        "t(15;17)", "t(8;21)", "inv(16)", "t(16;16)", "t(9;22) BCR-ABL1", "t(12;21)",
        "t(1;19)", "t(11;14) CCND1-IGH", "t(14;18) BCL2-IGH", "t(8;14) MYC-IGH", "Other"
    ]
    cytogenetic_abnormalities = st.multiselect("Select all that apply:", cytogenetic_samples)

    st.subheader("7a. Molecular Mutations (Multi-Select)")
    mutation_samples = [
        "FLT3-ITD", "NPM1", "CEBPA", "RUNX1", "JAK2", "CALR", "MPL", "BCR-ABL1",
        "KMT2A (MLL)", "ETV6-RUNX1", "TCF3-PBX1", "MYC", "BCL2", "BCL6", "CCND1",
        "TET2", "SRSF2", "SF3B1", "IDH1", "IDH2", "ASXL1", "HTLV-1", "HYPERDIPLOID", "HYPODIPLOID",
        "Other"
    ]
    molecular_mutations = st.multiselect("Select all that apply:", mutation_samples)

    # 8) Special Entities
    st.subheader("8. Special Entities")
    mast_cell_involvement = st.checkbox("Suspect Mastocytosis?")
    histiocytic_marker = st.checkbox("Suspect Histiocytic/Dendritic Cell Neoplasm?")

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

        # Display validation errors
        if errors:
            for error in errors:
                st.error(f"Error: {error}")
            st.stop()  # Stop further processing if there are critical errors

        # Display validation warnings
        if warnings:
            for warning in warnings:
                st.warning(f"Warning: {warning}")

        # Proceed with classification
        classification, explanation = classify_blood_cancer(
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

        # Display classification result
        st.success(f"**Classification Result**: {classification}")

        # Display derivation/explanation
        st.markdown("### **How This Classification Was Derived**")
        for line in explanation:
            st.write(line)

        # Prepare data to send to GPT-4
        explanation_text = "\n".join(explanation)

        # Get GPT-4 review and next steps
        with st.spinner("Generating GPT-4 review and clinical next steps..."):
            gpt4_review = get_gpt4_review(classification, explanation_text)

        # Display GPT-4's response
        st.markdown("### **GPT-4 Review & Clinical Next Steps**")
        st.write(gpt4_review)

        st.markdown("""
        ---
        **Disclaimer**: This app is a simplified demonstration and **not** a replacement for 
        professional pathology review or real-world WHO classification.
        """)

# ----------------------------
# Check Authentication and Run App
# ----------------------------
if st.session_state['authenticated']:
    app_main()
