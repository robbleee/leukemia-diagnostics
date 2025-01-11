import streamlit as st
import bcrypt
import json
import graphviz
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

##############################
# SET PAGE CONFIGURATION FIRST
##############################
st.set_page_config(page_title="Hematologic Classification", layout="wide")

# Initialize session state variables
if "show_explanation" not in st.session_state:
    st.session_state["show_explanation"] = False
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
    dot.node("Result", f"Final: {classification}", shape="rectangle", color="green")
    dot.edge(previous_node, "Result")

    return dot.source


def classify_AML_WHO2022(parsed_data: dict) -> tuple:
    """
    Classifies AML subtypes based on the WHO 2022 criteria, including qualifiers.
    If the final classification is "Acute myeloid leukaemia, [define by differentiation]",
    we attempt to insert AML_differentiation from parsed_data if available.
    
    Args:
        parsed_data (dict): A dictionary containing extracted hematological report data.

    Returns:
        tuple: 
            classification (str): The final AML classification according to WHO 2022
            derivation (list): A list capturing the step-by-step logic used
    """
    derivation = []

    # Retrieve blasts_percentage
    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")

    # Check if blasts_percentage is present and valid
    if blasts_percentage is None:
        derivation.append("Error: `blasts_percentage` is missing.")
        return (
            "Error: `blasts_percentage` is missing. Please provide this information for classification.",
            derivation,
        )
    if not isinstance(blasts_percentage, (int, float)) or not (0.0 <= blasts_percentage <= 100.0):
        derivation.append("Error: `blasts_percentage` must be a number between 0 and 100.")
        return (
            "Error: `blasts_percentage` must be a number between 0 and 100.",
            derivation,
        )
    
    classification = "Acute myeloid leukaemia, [define by differentiation]"
    derivation.append(f"Initial classification set to: {classification}")

    # -----------------------------
    # STEP 1: AML-Defining Recurrent Genetic Abnormalities
    # -----------------------------
    aml_genetic_abnormalities_map = {
        "NPM1": "AML with NPM1 mutation",
        "RUNX1::RUNX1T1": "AML with RUNX1::RUNX1T1 fusion",
        "CBFB::MYH11": "AML with CBFB::MYH11 fusion",
        "DEK::NUP214": "AML with DEK::NUP214 fusion",
        "RBM15::MRTFA": "AML with RBM15::MRTFA fusion",
        "KMT2A": "AML with KMT2A rearrangement",
        "MECOM": "AML with MECOM rearrangement",
        "NUP98": "AML with NUP98 rearrangement",
        "CEBPA": "AML with CEBPA mutation",
        "bZIP": "AML with CEBPA mutation",
        "BCR::ABL1": "AML with BCR::ABL1 fusion"
    }

    aml_def_genetic = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    # Identify which abnormalities are actually true
    true_aml_genes = [gene for gene, val in aml_def_genetic.items() if val is True]

    if true_aml_genes:
        derivation.append(f"Detected AML-defining abnormalities: {', '.join(true_aml_genes)}")
    
    # Attempt classification if any are present
    for gene, classif in aml_genetic_abnormalities_map.items():
        if gene in ["CEBPA", "bZIP", "BCR::ABL1"]:
            if aml_def_genetic.get(gene, False) and blasts_percentage >= 20.0:
                classification = classif
                derivation.append(
                    f"Classification updated based on {gene} abnormality (blasts >=20%). => {classification}"
                )
                break
        else:
            if aml_def_genetic.get(gene, False):
                classification = classif
                derivation.append(
                    f"Classification updated based on {gene} abnormality. => {classification}"
                )
                break

    # -----------------------------
    # STEP 2: MDS-Related Mutations
    # -----------------------------
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_related_mutations = parsed_data.get("MDS_related_mutation", {})
        # Identify which are true
        true_mds_mutations = [gene for gene, val in mds_related_mutations.items() if val is True]

        if true_mds_mutations:
            classification = "AML, myelodysplasia related"
            derivation.append(
                f"Detected MDS-related mutation(s): {', '.join(true_mds_mutations)} => {classification}"
            )
        else:
            derivation.append("No MDS-related mutations triggered reclassification.")

    # -----------------------------
    # STEP 3: MDS-Related Cytogenetics
    # -----------------------------
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_related_cytogenetics = parsed_data.get("MDS_related_cytogenetics", {})
        # Identify which are true
        true_mds_cytos = [abn for abn, val in mds_related_cytogenetics.items() if val is True]

        if true_mds_cytos:
            classification = "AML, myelodysplasia related"
            derivation.append(
                f"Detected MDS-related cytogenetic abnormality(ies): {', '.join(true_mds_cytos)} => {classification}"
            )
        else:
            derivation.append("No MDS-related cytogenetic abnormalities triggered reclassification.")

    # -----------------------------
    # STEP 4: Add Qualifiers
    # -----------------------------
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_descriptions = []
    
    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_descriptions.append("post cytotoxic therapy")
        derivation.append("Qualifier detected: post cytotoxic therapy")

    germline_variant = qualifiers.get("predisposing_germline_variant", "None")
    if germline_variant and germline_variant.lower() != "none":
        qualifier_descriptions.append(f"associated with germline {germline_variant}")
        derivation.append(f"Qualifier detected: germline variant = {germline_variant}")

    if qualifier_descriptions:
        classification += f", {', '.join(qualifier_descriptions)}"
        derivation.append(f"Appended qualifiers: {', '.join(qualifier_descriptions)} => {classification}")

    # -----------------------------
    # STEP 5: Replace "[define by differentiation]" if needed
    # -----------------------------
    if classification.strip() == "Acute myeloid leukaemia, [define by differentiation]":
        aml_diff = parsed_data.get("AML_differentiation")
        derivation.append(f"Checking AML_differentiation: {aml_diff}")

        FAB_TO_WHO_MAPPING = {
            "M0": "Acute myeloid leukaemia with minimal differentiation",
            "M1": "Acute myeloid leukaemia without maturation",
            "M2": "Acute myeloid leukaemia with maturation",
            "M3": "Acute promyelocytic leukaemia",
            "M4": "Acute myelomonocytic leukaemia",
            "M4Eo": "Acute myelomonocytic leukaemia with eosinophilia",
            "M5a": "Acute monoblastic leukaemia",
            "M5b": "Acute monocytic leukaemia",
            "M6a": "Acute erythroid leukaemia (erythroid/myeloid type)",
            "M6b": "Pure erythroid leukaemia",
            "M7": "Acute megakaryoblastic leukaemia",
        }

        if aml_diff and aml_diff in FAB_TO_WHO_MAPPING:
            classification = FAB_TO_WHO_MAPPING[aml_diff]
            derivation.append(f"Classification replaced by FAB to WHO mapping => {classification}")
        else:
            classification = "Acute myeloid leukaemia, unknown differentiation"
            derivation.append("Invalid or missing AML_differentiation => 'unknown differentiation'")

    # Append "(WHO 2022)" if not already present
    if "(WHO 2022)" not in classification:
        classification += " (WHO 2022)"
        derivation.append(f"Appended '(WHO 2022)' => {classification}")

    return classification, derivation


def classify_AML_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies AML subtypes based on the ICC 2022 criteria, including qualifiers.

    Args:
        parsed_data (dict): A dictionary containing extracted hematological report data.

    Returns:
        tuple:
            classification (str): The final AML classification according to ICC 2022
            derivation (list): A list capturing the step-by-step logic used
    """
    derivation = []

    # Retrieve blasts_percentage
    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")

    # Check if blasts_percentage is present and valid
    if blasts_percentage is None:
        derivation.append("Error: `blasts_percentage` is missing.")
        return (
            "Error: `blasts_percentage` is missing. Please provide this information for classification.",
            derivation,
        )
    if not isinstance(blasts_percentage, (int, float)) or not (0.0 <= blasts_percentage <= 100.0):
        derivation.append("Error: `blasts_percentage` must be a number between 0 and 100.")
        return (
            "Error: `blasts_percentage` must be a number between 0 and 100.",
            derivation,
        )

    classification = "AML, NOS"
    derivation.append(f"Initial classification set to: {classification}")

    # Retrieve necessary fields
    aml_def_genetic = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    mds_related_mutations = parsed_data.get("MDS_related_mutation", {})
    mds_related_cytogenetics = parsed_data.get("MDS_related_cytogenetics", {})
    qualifiers = parsed_data.get("qualifiers", {})

    # -----------------------------
    # STEP 1: AML-defining Recurrent Genetic Abnormalities
    # -----------------------------
    aml_genetic_abnormalities_map = {
        "NPM1": "AML with mutated NPM1",
        "RUNX1::RUNX1T1": "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1",
        "CBFB::MYH11": "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11",
        "DEK::NUP214": "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214",
        "RBM15::MRTFA": "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTF1",
        "KMT2A": "AML with other KMT2A rearrangements",
        "MECOM": "AML with other MECOM rearrangements",
        "NUP98": "AML with NUP98 and other partners",
        "bZIP": "AML with in-frame bZIP CEBPA mutations",
        "BCR::ABL1": "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1"
    }

    # Identify which AML-defining genes are actually true
    true_aml_genes = [gene for gene, val in aml_def_genetic.items() if val is True]
    if true_aml_genes:
        derivation.append(f"Detected AML-defining abnormalities: {', '.join(true_aml_genes)}")

    # Attempt classification based on these genes
    for gene, classif in aml_genetic_abnormalities_map.items():
        if aml_def_genetic.get(gene, False):
            # Genes that require blasts >= 10%
            if gene in [
                "NPM1", "RUNX1::RUNX1T1", "CBFB::MYH11",
                "DEK::NUP214", "RBM15::MRTFA", "KMT2A",
                "MECOM", "NUP98", "bZIP", "BCR::ABL1"
            ]:
                if blasts_percentage >= 10.0:
                    classification = classif
                    derivation.append(f"Classification updated based on {gene} (blasts >=10%) => {classification}")
                    break
                else:
                    derivation.append(
                        f"{gene} abnormality found, but blasts <10%. Classification remains: {classification}"
                    )
            else:
                # If any other scenario (not typically the case, but kept for completeness)
                classification = classif
                derivation.append(f"Classification updated based on {gene} => {classification}")
                break

    # -----------------------------
    # STEP 2: Biallelic TP53
    # -----------------------------
    if classification == "AML, NOS":
        # If any of these are True => AML with mutated TP53
        conditions = [
            biallelic_tp53.get("2_x_TP53_mutations", False),
            biallelic_tp53.get("1_x_TP53_mutation_del_17p", False),
            biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
        ]
        if any(conditions):
            classification = "AML with mutated TP53"
            derivation.append(f"Biallelic TP53 mutation detected => {classification}")

    # -----------------------------
    # STEP 3: MDS-related Mutations
    # -----------------------------
    if classification == "AML, NOS":
        true_mds_mutations = [gene for gene, val in mds_related_mutations.items() if val is True]

        if true_mds_mutations:
            classification = "AML with myelodysplasia related gene mutation"
            derivation.append(f"MDS-related mutation(s): {', '.join(true_mds_mutations)} => {classification}")

    # -----------------------------
    # STEP 4: MDS-related Cytogenetics
    # -----------------------------
    if classification == "AML, NOS":
        # Combine MRD and NOS cytogenetics
        mrd_cytogenetics = [
            "Complex_karyotype", "del_5q", "t_5q", "add_5q", "-7", "del_7q",
            "del_12p", "t_12p", "add_12p", "i_17q", "idic_X_q13"
        ]
        nos_cytogenetics = [
            "5q", "+8", "del_11q", "12p", "-13",
            "-17", "add_17p", "del_20q"
        ]
        all_cytogenetics = mrd_cytogenetics + nos_cytogenetics

        # Identify which ones are actually true
        true_cytogenetics = [abn for abn, val in mds_related_cytogenetics.items() if val is True and abn in all_cytogenetics]

        if true_cytogenetics:
            classification = "AML with myelodysplasia related cytogenetic abnormality"
            derivation.append(
                f"Detected cytogenetic abnormality(ies): {', '.join(true_cytogenetics)} => {classification}"
            )

    # -----------------------------
    # STEP 5: Qualifiers
    # -----------------------------
    qualifier_descriptions = []

    if qualifiers.get("previous_MDS_diagnosed_over_3_months_ago", False):
        qualifier_descriptions.append("post MDS")
        derivation.append("Qualifier detected: post MDS")

    if qualifiers.get("previous_MDS/MPN_diagnosed_over_3_months_ago", False):
        qualifier_descriptions.append("post MDS/MPN")
        derivation.append("Qualifier detected: post MDS/MPN")

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_descriptions.append("therapy related")
        derivation.append("Qualifier detected: therapy related")

    if qualifier_descriptions:
        qualifiers_str = ", ".join(qualifier_descriptions)
        classification += f", {qualifiers_str} (ICC 2022)"
        derivation.append(f"Appended qualifiers => {classification}")
    else:
        classification += " (ICC 2022)"

    return classification, derivation


##############################
# AI REVIEW
##############################
def get_gpt4_review(
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


##############################
# PARSE HAEMATOLOGY 
##############################
def parse_hematology_report(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI and requests a structured JSON
    with all fields needed for classification, including AML differentiation.
    
    Returns:
        dict: A dictionary containing the extracted fields. Returns an empty dict if parsing fails.
    """
    # Safety check: if the user didn’t type anything, return an empty dict
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}
    
    # Define the fields to extract
    required_json_structure = {
        "blasts_percentage": None,  # Changed from 0.0 to None
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1": False,
            "RUNX1::RUNX1T1": False,
            "CBFB::MYH11": False,
            "DEK::NUP214": False,
            "RBM15::MRTFA": False,
            "KMT2A": False,
            "MECOM": False,
            "NUP98": False,
            "CEBPA": False,
            "bZIP": False,  
            "BCR::ABL1": False
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": False,
            "1_x_TP53_mutation_del_17p": False,
            "1_x_TP53_mutation_LOH": False
        },
        "MDS_related_mutation": {
            "ASXL1": False,
            "BCOR": False,
            "EZH2": False,
            "RUNX1": False,
            "SF3B1": False,
            "SRSF2": False,
            "STAG2": False,
            "U2AF1": False,
            "ZRSR2": False
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": False,
            "del_5q": False,
            "t_5q": False,
            "add_5q": False,
            "-7": False,
            "del_7q": False,
            "+8": False,
            "del_11q": False,
            "del_12p": False,
            "t_12p": False,
            "add_12p": False,
            "-13": False,
            "i_17q": False,
            "-17": False,
            "add_17p": False,
            "del_17p": False,
            "del_20q": False,
            "idic_X_q13": False
        },
        "AML_differentiation": None,  # New field added for AML differentiation
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": False,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
            "previous_cytotoxic_therapy": False,
            "predisposing_germline_variant": None
        }
    }
    
    # Construct the prompt with detailed instructions
    prompt = f"""
        You are a specialized medical AI and a knowledgeable hematologist. The user has pasted a free-text hematological report. 
        Please extract the following fields from the text and format them into a valid JSON object exactly as specified below. 
        For boolean fields, use true/false. For numerical fields, provide the value. If a field is not found or unclear, set it to false or a default value.
        
        Additionally, extract the AML differentiation classification using the FAB (M0-M7) or WHO classification systems. 
        If the differentiation is not specified, set the value to null.
        
        Try to consider if the user may have used some sort of shorthand and translate where necessary.
        
        **For example**:
        
        1. 2_x_TP53_mutations: Extract if the report mentions phrases like "2 TP53 mutations," "biallelic TP53 mutations," or similar.
        2. 1_x_TP53_mutation_del_17p: Look for terms like "TP53 mutation and 17p deletion" or "TP53 mutation with del(17p)."
        3. 1_x_TP53_mutation_LOH: Identify phrases such as "TP53 mutation and LOH," "TP53 mutation with Loss of Heterozygosity," or equivalent.
        4. AML_differentiation: Extract the AML differentiation classification, such as "FAB M3" or "WHO AML with myelodysplasia-related changes."
        
        Examples of predisposing germline variants:
            Germline predisposition
                • CEBPA 
                • DDX41 
                • TP53 
            Germline predisposition and pre-existing platelet disorder:
                • RUNX1
                • ANKRD26
                • ETV6 
            Germline predisposition and potential organ dysfunction:
                • GATA2
            Noonan syndrome-like disorders:
                • Down syndrome
                • SAMD9
                • BLM 
    
        Make sure to onle record AML_defining_recurrent_genetic_abnormalities if the abnorrmality pressent is the exact one mentioned in the list below:
            NPM1 mutation
            RUNX1::RUNX1T1
            CBFB::MYH11 fusion
            DEK::NUP214 fusion
            RBM15::MRTFA fusion
            KMT2A rearrangement
            MECOM rearrangement
            NUP98 rearrangement
            CEBPA / bZIP mutation
            BCR::ABL1 fusion

            For example:
            - "NPM1 mutation" -> "NPM1" = true
            - "No KMT2A rearrangement detected" -> "KMT2A" = false
            - "KMT2A amplification" alone is NOT the same as a rearrangement -> "KMT2A" = false
            - "RUNX1::RUNX1T1 fusion present" -> "RUNX1::RUNX1T1" = true

    

        For predisposing_germline_variant, leave as "None" if there is none otherwise record the variant specified.
        
        **Required JSON structure:**
        {{
            "blasts_percentage": null,  # Changed from 0.0 to null
            "AML_defining_recurrent_genetic_abnormalities": {{
                "NPM1": false,
                "RUNX1::RUNX1T1": false,
                "CBFB::MYH11": false,
                "DEK::NUP214": false,
                "RBM15::MRTFA": false,
                "KMT2A": false,
                "MECOM": false,
                "NUP98": false,
                "CEBPA": false,
                "bZIP": false,
                "BCR::ABL1": false
            }},
            "Biallelic_TP53_mutation": {{
                "2_x_TP53_mutations": false,
                "1_x_TP53_mutation_del_17p": false,
                "1_x_TP53_mutation_LOH": false
            }},
            "MDS_related_mutation": {{
                "ASXL1": false,
                "BCOR": false,
                "EZH2": false,
                "RUNX1": false,
                "SF3B1": false,
                "SRSF2": false,
                "STAG2": false,
                "U2AF1": false,
                "ZRSR2": false
            }},
            "MDS_related_cytogenetics": {{
                "Complex_karyotype": false,
                "del_5q": false,
                "t_5q": false,
                "add_5q": false,
                "-7": false,
                "del_7q": false,
                "+8": false,
                "del_11q": false,
                "del_12p": false,
                "t_12p": false,
                "add_12p": false,
                "-13": false,
                "i_17q": false,
                "-17": false,
                "add_17p": false,
                "del_17p": false,
                "del_20q": false,
                "idic_X_q13": false
            }},
            "AML_differentiation": "None"
            "qualifiers": {{
                "previous_MDS_diagnosed_over_3_months_ago": false,
                "previous_MDS/MPN_diagnosed_over_3_months_ago": false,
                "previous_cytotoxic_therapy": false,
                "predisposing_germline_variant": "None"
            }}
        }}
    
    
    
        
        **Instructions:**
        1. Return **valid JSON only** with no extra text or commentary.
        2. Ensure all fields are present as specified.
        3. Use true/false for boolean values.
        4. If a field is not applicable or not mentioned, set it to false or null as appropriate.
        5. Do not wrap the JSON in Markdown or any other formatting.
        
        **Here is the free-text hematological report to parse:**
        {report_text}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Corrected model name
            messages=[
                {"role": "system", "content": "You are a knowledgeable hematologist who formats output strictly in JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,  # Increased max_tokens to accommodate detailed JSON including AML differentiation
            temperature=0.0  # Deterministic output
        )
        raw_content = response.choices[0].message.content.strip()
        
        # Attempt to parse the JSON
        parsed_data = json.loads(raw_content)
        
        # Ensure all required fields are present; fill missing fields with defaults
        for key, value in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_value
        
        # Validate blasts_percentage
        blasts = parsed_data.get("blasts_percentage")
        if blasts is not None:
            if not isinstance(blasts, (int, float)) or not (0.0 <= blasts <= 100.0):
                st.error("❌ Invalid `blasts_percentage` value. It must be a number between 0 and 100.")
                return {}
        
        # Validate AML_differentiation
        aml_diff = parsed_data.get("AML_differentiation")
        valid_fab_classes = [f"M{i}" for i in range(0, 8)]  # M0 to M7
        if aml_diff is not None:
            if not isinstance(aml_diff, str):
                st.error("❌ Invalid `AML_differentiation` value. It must be a string representing the classification (e.g., 'FAB M3').")
                return {}
            elif not any(fab in aml_diff.upper() for fab in valid_fab_classes):
                st.warning("⚠️ `AML_differentiation` value does not match known FAB classifications.")
        
        # Print the parsed JSON object to stdout
        print("Parsed Hematology Report JSON:")
        print(json.dumps(parsed_data, indent=2))
        
        return parsed_data
    
    except json.JSONDecodeError:
        st.error("❌ Failed to parse the AI response into JSON. Please ensure the report is well-formatted.")
        print("❌ JSONDecodeError: Failed to parse AI response.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI: {str(e)}")
        print(f"❌ Exception: {str(e)}")
        return {}


##############################
# EXPLANATION FUNCTION
##############################
def show_explanation():
    """
    Displays a comprehensive and visually appealing explanation/help page in Markdown,
    detailing how classification logic is applied to arrive at each cancer type.
    Also provides a list of all cancer types that can be classified.
    """


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
         - **ALCL**: T-cell with **CD30+**; if cytogenetics show "ALK" → ALCL (ALK+), otherwise ALCL–.
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
# APP MAIN
##############################
def app_main():
    st.title("Acute Myeloid Leukemia (AML) Classification Tool")

    # ---------------------------
    # FREE-TEXT REPORT PARSER (Visible Only to Authenticated Users)
    # ---------------------------
    if st.session_state.get("authenticated", False):
        st.markdown("""
        Enter the **full** hematological and cytogenetics reports in the text boxes below. The AI will extract key fields, and classification will proceed based on the extracted data.
        """)

        # **Split Input Section into Two Text Boxes**
        hematology_report = st.text_area(
            "Hematology Report:", 
            height=200, 
            help="Paste the complete hematology report from laboratory results."
        )

        cytogenetics_report = st.text_area(
            "Cytogenetics Report:", 
            height=200, 
            help="Paste the complete cytogenetics report from laboratory results."
        )

        if st.button("Parse & Classify from Free-Text"):
            # **Concatenate the Two Reports**
            combined_report = f"{hematology_report}\n\n{cytogenetics_report}"

            if combined_report.strip():
                with st.spinner("Extracting data and classifying..."):
                    # 1) Parse the report with GPT (or your chosen parser)
                    parsed_fields = parse_hematology_report(combined_report)

                    if not parsed_fields:
                        st.warning("No data extracted or an error occurred during parsing.")
                    else:
                        # 2) Use the classification functions
                        # Make sure these functions return (classification, derivation)
                        classification_who, who_derivation = classify_AML_WHO2022(parsed_fields)
                        classification_icc, icc_derivation = classify_AML_ICC2022(parsed_fields)

                        # 3) Check for error classifications
                        if classification_who.startswith("Error:"):
                            st.error(classification_who)
                        else:
                            # Proceed with displaying classifications
                            st.success("Report parsed successfully! Attempting classification...")

                            # --- Show the extracted JSON data ---
                            st.markdown("### **Extracted Values (JSON)**")
                            st.json(parsed_fields)

                            # 4) Log the parsed data and classification results to stdout (optional)
                            print("Parsed Hematology Report JSON:")
                            print(json.dumps(parsed_fields, indent=2))
                            print("WHO 2022 Classification Result:", classification_who)
                            print("ICC 2022 Classification Result:", classification_icc)

                            # 5) Display Classification Results
                            st.markdown("""
                            <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
                                <h3 style='color: #0f5132;'>Classification Results</h3>
                            </div>
                            """, unsafe_allow_html=True)

                            # Create two columns horizontally
                            col1, col2 = st.columns(2)

                            with col1:
                                st.markdown("### **WHO 2022 Classification**")
                                st.markdown(f"**Classification:** {classification_who}")

                            with col2:
                                st.markdown("### **ICC 2022 Classification**")
                                st.markdown(f"**Classification:** {classification_icc}")

                            # 6) Show derivations for both WHO and ICC
                            st.markdown("### **Derivation (Step-by-step Logic)**")
                            with st.expander("🔍 WHO 2022 Derivation"):
                                # Convert derivation list to numbered Markdown list
                                who_derivation_markdown = ""
                                for idx, step in enumerate(who_derivation, start=1):
                                    who_derivation_markdown += f"**Step {idx}:** {step}\n\n"
                                st.markdown(who_derivation_markdown)

                            with st.expander("🔍 ICC 2022 Derivation"):
                                # Convert derivation list to numbered Markdown list
                                icc_derivation_markdown = ""
                                for idx, step in enumerate(icc_derivation, start=1):
                                    icc_derivation_markdown += f"**Step {idx}:** {step}\n\n"
                                st.markdown(icc_derivation_markdown)

                            # 7) AI Review and Clinical Next Steps (Optional)
                            st.markdown("### **AI Review & Clinical Next Steps**")
                            if st.session_state.get('authenticated', False):
                                with st.spinner("Generating AI review and clinical next steps..."):
                                    # Combine WHO and ICC classification results into a single review
                                    combined_classifications = {
                                        "WHO 2022": {
                                            "Classification": classification_who
                                        },
                                        "ICC 2022": {
                                            "Classification": classification_icc
                                        }
                                    }
                                    # Generate a single AI review based on the combined classifications
                                    gpt4_review_result = get_gpt4_review(
                                        classification=combined_classifications,
                                        user_inputs=parsed_fields
                                    )
                                # Display the AI review
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
                st.error("Please provide at least one of the hematology or cytogenetics reports.")
    else:
        # User not authenticated, show a message or keep it hidden
        st.info("🔒 **Log in** to use the free-text hematological report parsing.")

    st.markdown("---")


##############################
# MAIN FUNCTION
##############################
def main():
    app_main()

if __name__ == "__main__":
    main()
