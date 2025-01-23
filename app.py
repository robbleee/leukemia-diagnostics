import streamlit as st
import bcrypt
import json
from openai import OpenAI

# Example imports for your parsers/classifiers
from parsers.aml_parser import parse_genetics_report_aml
from parsers.aml_response_parser import parse_aml_response_report
from parsers.mds_parser import parse_genetics_report_mds

from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022

# Splitted review imports
from reviewers.aml_reviewer import (
    get_gpt4_review_aml_classification,
    get_gpt4_review_aml_genes,
    get_gpt4_review_aml_additional_comments,
    get_gpt4_review_aml_mrd

)
from reviewers.mds_reviewer import (
    get_gpt4_review_mds_classification,
    get_gpt4_review_mds_genes
)

##################################
# PAGE CONFIG
##################################
st.set_page_config(page_title="Haematologic Classification", layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['username'] = ''

##################################
# AUTH FUNCTIONS
##################################
def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def authenticate_user(username: str, password: str) -> bool:
    users = st.secrets["auth"]["users"]
    for user in users:
        if user["username"] == username:
            return verify_password(user["hashed_password"], password)
    return False

def login_logout():
    """Handles login/logout in the sidebar."""
    if st.session_state['authenticated']:
        st.sidebar.markdown(f"### Logged in as **{st.session_state['username']}**")
        if st.sidebar.button("Logout", key="logout_button"):
            st.session_state['authenticated'] = False
            st.session_state['username'] = ''
            st.sidebar.success("Logged out successfully!")
    else:
        st.sidebar.header("Login for AI Features")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")
        if st.sidebar.button("Login", key="login_button"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.sidebar.success("Logged in successfully!")
            else:
                st.sidebar.error("Invalid username or password")

login_logout()

##################################
# CUSTOM CSS
##################################
def local_css():
    st.markdown(
        """
        <style>
        /* Toggle Switch Styles */
        .toggle-switch {
            display: flex;
            align-items: center;
            font-size: 18px;
            font-weight: bold;
        }

        .toggle-switch input {
            display: none;
        }

        .toggle-switch-label {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
            margin-right: 10px;
        }

        .toggle-switch-label input:checked + span {
            background-color: #4CAF50;
        }

        .toggle-switch-label input:checked + span:before {
            transform: translateX(26px);
        }

        .toggle-switch-label span {
            position: absolute;
            cursor: pointer;
            background-color: #ccc;
            border-radius: 34px;
            top: 0; left: 0; right: 0; bottom: 0;
            transition: 0.4s;
        }

        .toggle-switch-label span:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px; bottom: 4px;
            background-color: white;
            border-radius: 50%;
            transition: 0.4s;
        }

        /* Increase tab text size */
        div[data-baseweb="tabs"] > div > div {
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

local_css()


##################################
# FORMS & PARSING HELPERS
##################################
def build_manual_aml_data() -> dict:
    st.markdown("### Manual AML Data Entry ")
    blasts = st.number_input("Blasts (%)", min_value=0.0, max_value=100.0, value=0.0, key="aml_blasts_percentage")

    st.markdown("#### AML-defining Recurrent Genetic Abnormalities")
    c1, c2 = st.columns(2)
    with c1:
        npm1 = st.checkbox("NPM1 mutation", key="aml_npm1_mutation")
        runx1_runx1t1 = st.checkbox("RUNX1::RUNX1T1 fusion", key="aml_runx1_runx1t1")
        cbfb_myh11 = st.checkbox("CBFB::MYH11 fusion", key="aml_cbfb_myh11")
        dek_nup214 = st.checkbox("DEK::NUP214 fusion", key="aml_dek_nup214")
        rbm15_mrtfa = st.checkbox("RBM15::MRTFA fusion", key="aml_rbm15_mrtfa")
    with c2:
        mllt3_kmt2a = st.checkbox("MLLT3::KMT2A fusion", key="aml_mllt3_kmt2a")
        kmt2a = st.checkbox("KMT2A rearrangement (other)", key="aml_kmt2a_other")
        mecom = st.checkbox("MECOM rearrangement", key="aml_mecom")
        nup98 = st.checkbox("NUP98 rearrangement", key="aml_nup98")
        cebpa = st.checkbox("CEBPA mutation", key="aml_cebpa_mutation")

    # Additional row
    c3, c4 = st.columns(2)
    with c3:
        bzip = st.checkbox("CEBPA bZIP mutation", key="aml_cebpa_bzip")
    with c4:
        bcr_abl1 = st.checkbox("BCR::ABL1 fusion", key="aml_bcr_abl1")

    # Biallelic TP53
    st.markdown("#### Biallelic TP53 Mutation")
    tp1, tp2, tp3 = st.columns(3)
    with tp1:
        two_tp53 = st.checkbox("2 x TP53 mutations", key="aml_tp53_2")
    with tp2:
        one_tp53_del17p = st.checkbox("1 x TP53 + del(17p)", key="aml_tp53_del17p")
    with tp3:
        one_tp53_loh = st.checkbox("1 x TP53 + LOH", key="aml_tp53_loh")

    # MDS-related expanders
    st.markdown("#### MDS Related Flags")
    with st.expander("MDS-related Mutations", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            asxl1 = st.checkbox("ASXL1", key="aml_asxl1")
            bcor = st.checkbox("BCOR", key="aml_bcor")
            ezh2 = st.checkbox("EZH2", key="aml_ezh2")
            runx1_mds = st.checkbox("RUNX1 (MDS-related)", key="aml_runx1_mds")
            sf3b1 = st.checkbox("SF3B1", key="aml_sf3b1")
        with col_b:
            srsf2 = st.checkbox("SRSF2", key="aml_srsf2")
            stag2 = st.checkbox("STAG2", key="aml_stag2")
            u2af1 = st.checkbox("U2AF1", key="aml_u2af1")
            zrsr2 = st.checkbox("ZRSR2", key="aml_zrsr2")

    with st.expander("MDS-related Cytogenetics", expanded=False):
        c_left, c_right = st.columns(2)
        with c_left:
            complex_kary = st.checkbox("Complex karyotype", key="aml_complex_karyotype")
            del_5q = st.checkbox("del(5q)", key="aml_del_5q")
            t_5q = st.checkbox("t(5q)", key="aml_t_5q")
            add_5q = st.checkbox("add(5q)", key="aml_add_5q")
            minus7 = st.checkbox("-7", key="aml_minus7")
            del_7q = st.checkbox("del(7q)", key="aml_del_7q")
            plus8 = st.checkbox("+8", key="aml_plus8")
        with c_right:
            del_11q = st.checkbox("del(11q)", key="aml_del_11q")
            del_12p = st.checkbox("del(12p)", key="aml_del_12p")
            t_12p = st.checkbox("t(12p)", key="aml_t_12p")
            add_12p = st.checkbox("add(12p)", key="aml_add_12p")
            minus13 = st.checkbox("-13", key="aml_minus13")
            i_17q = st.checkbox("i(17q)", key="aml_i_17q")
            minus17 = st.checkbox("-17", key="aml_minus17")
            add_17p = st.checkbox("add(17p)", key="aml_add_17p")
            del_17p = st.checkbox("del(17p)", key="aml_del_17p")
            del_20q = st.checkbox("del(20q)", key="aml_del_20q")
            idic_x_q13 = st.checkbox("idic_X_q13", key="aml_idic_x_q13")

    # AML Differentiation
    aml_diff = st.text_input("AML differentiation (e.g. 'FAB M3', 'M4')", value="", key="aml_differentiation")

    # Qualifiers
    st.markdown("#### Qualifiers")
    qc1, qc2 = st.columns(2)
    with qc1:
        prev_mds_3mo = st.checkbox("Previous MDS diagnosed >3 months ago", key="aml_prev_mds_3mo")
        prev_mds_mpn_3mo = st.checkbox("Previous MDS/MPN diagnosed >3 months ago", key="aml_prev_mds_mpn_3mo")
    with qc2:
        prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="aml_prev_cytotx")
        germ_variant = st.text_input("Predisposing germline variant (if any)", value="None", key="aml_germ_variant")

    manual_data = {
        "blasts_percentage": blasts,
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1": npm1,
            "RUNX1::RUNX1T1": runx1_runx1t1,
            "CBFB::MYH11": cbfb_myh11,
            "DEK::NUP214": dek_nup214,
            "RBM15::MRTFA": rbm15_mrtfa,
            "MLLT3::KMT2A": mllt3_kmt2a,
            "KMT2A": kmt2a,
            "MECOM": mecom,
            "NUP98": nup98,
            "CEBPA": cebpa,
            "bZIP": bzip,
            "BCR::ABL1": bcr_abl1
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": two_tp53,
            "1_x_TP53_mutation_del_17p": one_tp53_del17p,
            "1_x_TP53_mutation_LOH": one_tp53_loh
        },
        "MDS_related_mutation": {
            "ASXL1": asxl1,
            "BCOR": bcor,
            "EZH2": ezh2,
            "RUNX1": runx1_mds,
            "SF3B1": sf3b1,
            "SRSF2": srsf2,
            "STAG2": stag2,
            "U2AF1": u2af1,
            "ZRSR2": zrsr2
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": complex_kary,
            "del_5q": del_5q,
            "t_5q": t_5q,
            "add_5q": add_5q,
            "-7": minus7,
            "del_7q": del_7q,
            "+8": plus8,
            "del_11q": del_11q,
            "del_12p": del_12p,
            "t_12p": t_12p,
            "add_12p": add_12p,
            "-13": minus13,
            "i(17q)": i_17q,
            "-17": minus17,
            "add(17p)": add_17p,
            "del(17p)": del_17p,
            "del(20q)": del_20q,
            "idic_X_q13": idic_x_q13
        },
        "AML_differentiation": aml_diff.strip() if aml_diff.strip() else None,
        "qualifiers": {
            "previous_MDS_diagnosed_over_3_months_ago": prev_mds_3mo,
            "previous_MDS/MPN_diagnosed_over_3_months_ago": prev_mds_mpn_3mo,
            "previous_cytotoxic_therapy": prev_cytotx,
            "predisposing_germline_variant": germ_variant.strip() if germ_variant.strip() else "None"
        }
    }
    return manual_data

def build_manual_mds_data_compact() -> dict:
    """Manual MDS Data Entry."""
    st.markdown("#### Manual MDS Data Entry ")
    c1, c2, c3 = st.columns(3)
    with c1:
        blasts = st.number_input("Blasts (%)", min_value=0.0, max_value=100.0, value=0.0, key="mds_blasts_percentage")
    with c2:
        fibrotic = st.checkbox("Fibrotic marrow?", key="mds_fibrotic")
    with c3:
        hypoplasia = st.checkbox("Hypoplastic MDS?", key="mds_hypoplasia")

    dys_lineages = st.number_input("Number of Dysplastic Lineages (0-3)", min_value=0, max_value=3, value=0, key="mds_dys_lineages")

    st.markdown("##### Biallelic TP53 Mutation")
    ctp1, ctp2, ctp3 = st.columns(3)
    with ctp1:
        tp53_2 = st.checkbox("2 x TP53 mutations", key="mds_tp53_2")
    with ctp2:
        tp53_17p = st.checkbox("1 x TP53 + del(17p)", key="mds_tp53_del17p")
    with ctp3:
        tp53_loh = st.checkbox("1 x TP53 + LOH", key="mds_tp53_loh")

    st.markdown("##### MDS-related Mutation")
    sf3b1 = st.checkbox("SF3B1 mutation", key="mds_sf3b1")

    st.markdown("##### MDS-related Cytogenetics")
    del_5q = st.checkbox("del(5q) / isolated 5q-", key="mds_del_5q")

    st.markdown("##### Qualifiers")
    ql1, ql2 = st.columns(2)
    with ql1:
        prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="mds_prev_cytotx")
    with ql2:
        germ_variant = st.text_input("Predisposing germline variant", value="None", key="mds_germ_variant")

    return {
        "blasts_percentage": blasts,
        "fibrotic": fibrotic,
        "hypoplasia": hypoplasia,
        "number_of_dysplastic_lineages": int(dys_lineages),
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": tp53_2,
            "1_x_TP53_mutation_del_17p": tp53_17p,
            "1_x_TP53_mutation_LOH": tp53_loh
        },
        "MDS_related_mutation": {
            "SF3B1": sf3b1
        },
        "MDS_related_cytogenetics": {
            "del_5q": del_5q
        },
        "qualifiers": {
            "previous_cytotoxic_therapy": prev_cytotx,
            "predisposing_germline_variant": germ_variant.strip() if germ_variant.strip() else "None"
        }
    }

def build_manual_aml_response_data() -> dict:
    st.markdown("#### Manual AML Response Assessment (ELN 2022)")
    col1, col2 = st.columns(2)
    with col1:
        adequate_sample = st.checkbox("Adequate sample available?", key="response_adequate_sample")
        bone_marrow_blasts = st.number_input("Bone Marrow Blasts (%)", min_value=0.0, max_value=100.0, value=0.0, key="response_bone_marrow_blasts")
        blood_counts_provided = st.checkbox("Are blood counts provided?", key="response_blood_counts_provided")
    with col2:
        platelets = st.number_input("Platelet count (x10^9/L)", min_value=0.0, value=0.0, key="response_platelets")
        neutrophils = st.number_input("Neutrophil count (x10^9/L)", min_value=0.0, value=0.0, key="response_neutrophils")

    st.markdown("##### Additional Response-Related Fields")
    col3, col4 = st.columns(2)
    with col3:
        previously_cr = st.checkbox("Previously achieved CR/CRh/CRi?", key="response_previously_cr")
        blasts_decrease_50 = st.checkbox("Blasts decreased by >= 50%?", key="response_blasts_decrease_50")
    with col4:
        tnc_5_25 = st.checkbox("TNC 5-25 x10^9/L?", key="response_tnc_5_25")

    manual_response_data = {
        "AdequateSample": adequate_sample,
        "BoneMarrowBlasts": bone_marrow_blasts,
        "BloodCountsProvided": blood_counts_provided,
        "Platelets": platelets,
        "Neutrophils": neutrophils,
        "PreviouslyAchievedCR_CRh_Cri": previously_cr,
        "BlastsDecreaseBy50Percent": blasts_decrease_50,
        "TNCBetween5And25": tnc_5_25
    }
    return manual_response_data

##################################
# CLASSIFICATION DISPLAY HELPERS
##################################
def display_aml_classification_results(parsed_fields, classification_who, who_derivation,
                                       classification_icc, icc_derivation, mode="manual"):
    """
    Displays AML classification results WITHOUT automatically calling the AI review.
    """
    with st.expander("### **View Parsed AML Values**", expanded=False):
        st.json(parsed_fields)

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

    col_who, col_icc = st.columns(2)
    with col_who:
        with st.expander("🔍 WHO 2022 Derivation", expanded=False):
            who_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(who_derivation, start=1)]
            )
            st.markdown(who_derivation_markdown)
    with col_icc:
        with st.expander("🔍 ICC 2022 Derivation", expanded=False):
            icc_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(icc_derivation, start=1)]
            )
            st.markdown(icc_derivation_markdown)

    st.markdown("---")
    st.markdown("""
    <div style='background-color: #D6EFFF; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>Analysis Actions:</h3>
    </div>
    """, unsafe_allow_html=True)

def display_mds_classification_results(parsed_fields, classification_who, derivation_who,
                                       classification_icc, derivation_icc, mode="manual"):
    """
    Displays MDS classification results WITHOUT automatically calling the AI review.
    """
    with st.expander("View Parsed MDS Values", expanded=False):
        st.json(parsed_fields)

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

    col_who, col_icc = st.columns(2)
    with col_who:
        with st.expander("🔍 WHO 2022 Derivation", expanded=False):
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_who, start=1)]
            )
            st.markdown(derivation_text)
    with col_icc:
        with st.expander("🔍 ICC 2022 Derivation", expanded=False):
            derivation_text = "\n\n".join(
                [f"**Step {i}**: {step}" for i, step in enumerate(derivation_icc, start=1)]
            )
            st.markdown(derivation_text)

    st.markdown("---")
    st.markdown("""
    <div style='background-color: #D6EFFF; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>Analysis Results</h3>
        <p>Classification computed successfully.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ---
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
        <p><strong>Disclaimer:</strong> This app is a simplified demonstration and 
        <strong>not</strong> a replacement for professional pathology review or real-world WHO/ICC classification.</p>
    </div>
    """, unsafe_allow_html=True)

def display_aml_response_results(parsed_data, response, derivation, mode="manual"):
    with st.expander("### **View Parsed AML Response Values**", expanded=False):
        st.json(parsed_data)

    st.markdown("""
    <div style='background-color: #d1e7dd; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h3 style='color: #0f5132;'>AML Response Assessment Result</h3>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### **{response}**")

    with st.expander("🔍 Derivation Steps", expanded=False):
        derivation_text = "\n\n".join([f"**Step {i}**: {step}" for i, step in enumerate(derivation, start=1)])
        st.markdown(derivation_text)

    st.markdown("""
    ---
    <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">
        <p><strong>Disclaimer:</strong> This AML response assessment is a simplified demonstration 
        and <strong>not</strong> a replacement for professional hematological review or real-world ELN criteria.</p>
    </div>
    """, unsafe_allow_html=True)




##################################
# MAIN APP
##################################
def app_main():
    st.title("AML Diagnostics Support Tool")
    
    if st.session_state.get("authenticated", False):
        # Create tabs
        tab_aml, tab_mds, tab_response = st.tabs(
            ["AML Classification", "MDS Classification", "AML Response Assessment"]
        )

        


        ################################################
        # AML TAB
        ################################################
        with tab_aml:
            st.subheader("Acute Myeloid Leukemia (AML)")

            aml_mode_toggle = st.checkbox("AI Mode", key="aml_mode_toggle")

            ########################
            # MANUAL MODE
            ########################
            if not aml_mode_toggle:
                st.markdown("---")
                manual_data = build_manual_aml_data()

                if st.button("Classify AML (Manual)"):
                    classification_who, who_derivation = classify_AML_WHO2022(manual_data)
                    classification_icc, icc_derivation = classify_AML_ICC2022(manual_data)

                    st.session_state["aml_manual_result"] = {
                        "parsed_data": manual_data,
                        "who_class": classification_who,
                        "who_derivation": who_derivation,
                        "icc_class": classification_icc,
                        "icc_derivation": icc_derivation,
                    }

                # Always display classification if it exists
                if "aml_manual_result" in st.session_state:
                    res = st.session_state["aml_manual_result"]
                    display_aml_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="manual"
                    )

                    # Build classification dict
                    classification_dict = {
                        "WHO 2022": {
                            "Classification": res["who_class"],
                            "Derivation": res["who_derivation"]
                        },
                        "ICC 2022": {
                            "Classification": res["icc_class"],
                            "Derivation": res["icc_derivation"]
                        }
                    }

                    # 4 BUTTONS in 2 rows / or 1 row of 4 columns
                    # Example: We'll do 2 columns for row1, 2 columns for row2
                    # so we don't have 4 tiny columns. Or we can do all 4 in a single row.
                    
                    # Place all four buttons on the same row
                    rev_col1, rev_col2, rev_col3, rev_col4 = st.columns(4)

                    with rev_col1:
                        if st.button("🩺 Classification"):
                            class_review = get_gpt4_review_aml_classification(classification_dict, res["parsed_data"])
                            st.session_state["aml_manual_class_review"] = class_review

                    with rev_col2:
                        if st.button("🧬 Gene Review"):
                            gene_review = get_gpt4_review_aml_genes(classification_dict, res["parsed_data"])
                            st.session_state["aml_manual_gene_review"] = gene_review

                    with rev_col3:
                        if st.button("🧪 MRD Review"):
                            mrd_review = get_gpt4_review_aml_mrd(classification_dict, res["parsed_data"])
                            st.session_state["aml_manual_mrd_review"] = mrd_review

                    with rev_col4:
                        if st.button("📄 AI Comments"):
                            add_comments = get_gpt4_review_aml_additional_comments(classification_dict, res["parsed_data"])
                            st.session_state["aml_manual_additional_comments"] = add_comments

                    # Now display each if it exists
                    # Classification review
                    if "aml_manual_class_review" in st.session_state:
                        with st.expander("### AI Classification Review", expanded=True):
                            st.markdown(st.session_state["aml_manual_class_review"])

                    # Gene review
                    if "aml_manual_gene_review" in st.session_state:
                        with st.expander("### AI Gene Analysis", expanded=True):
                            st.markdown(st.session_state["aml_manual_gene_review"])

                    # MRD review
                    if "aml_manual_mrd_review" in st.session_state:
                        with st.expander("### AI MRD Review", expanded=True):
                            st.markdown(st.session_state["aml_manual_mrd_review"])

                    # Additional Comments
                    if "aml_manual_additional_comments" in st.session_state:
                        with st.expander("### AI Additional Comments", expanded=True):
                            st.markdown(st.session_state["aml_manual_additional_comments"])


            ########################
            # AI MODE
            ########################
            else:
                st.markdown("**AI Mode:** Paste your free-text AML reports. Then click 'Parse & Classify AML (AI)'.")
                st.markdown("---")

                col1, col2 = st.columns(2)
                with col1:
                    blasts_override = st.text_input("Blasts % (Override)", placeholder="25")
                with col2:
                    diff_override = st.text_input("AML Differentiation", placeholder="FAB M3")

                morph_input = st.text_input("Morphology/Clinical Info", placeholder="e.g. Dysplasia observed...")

                genetics_report = st.text_area("Genetics Report:", height=100)
                cytogenetics_report = st.text_area("Cytogenetics Report:", height=100)

                if st.button("Parse & Classify AML (AI)"):
                    combined = f"{genetics_report}\n\n{cytogenetics_report}"
                    if combined.strip():
                        with st.spinner("Parsing & classifying (AI)..."):
                            parsed_data = parse_genetics_report_aml(combined)
                            if blasts_override.strip():
                                try:
                                    parsed_data["blasts_percentage"] = float(blasts_override.strip())
                                except ValueError:
                                    st.warning("Invalid blasts override")
                            if diff_override.strip():
                                parsed_data["AML_differentiation"] = diff_override.strip()
                            if morph_input.strip():
                                parsed_data["morphology_clinical"] = morph_input.strip()

                            who_class, who_deriv = classify_AML_WHO2022(parsed_data)
                            icc_class, icc_deriv = classify_AML_ICC2022(parsed_data)

                            st.session_state["aml_ai_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv
                            }
                    else:
                        st.error("No AML data provided.")

                if "aml_ai_result" in st.session_state:
                    res = st.session_state["aml_ai_result"]
                    display_aml_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="ai"
                    )

                    classification_dict = {
                        "WHO 2022": {
                            "Classification": res["who_class"],
                            "Derivation": res["who_derivation"]
                        },
                        "ICC 2022": {
                            "Classification": res["icc_class"],
                            "Derivation": res["icc_derivation"]
                        }
                    }

                    # 4 Buttons in 2 rows:
                    row1_col1, row1_col2 = st.columns(2)
                    with row1_col1:
                        if st.button("🩺 Classification Review (AI)"):
                            class_rev = get_gpt4_review_aml_classification(classification_dict, res["parsed_data"])
                            st.session_state["aml_ai_class_review"] = class_rev
                    with row1_col2:
                        if st.button("🧬 Gene Review (AI)"):
                            gene_rev = get_gpt4_review_aml_genes(classification_dict, res["parsed_data"])
                            st.session_state["aml_ai_gene_review"] = gene_rev

                    row2_col1, row2_col2 = st.columns(2)
                    with row2_col1:
                        if st.button("🧪 MRD Review (AI)"):
                            mrd_rev = get_gpt4_review_mrd(classification_dict, res["parsed_data"])
                            st.session_state["aml_ai_mrd_review"] = mrd_rev
                    with row2_col2:
                        if st.button("📄 Additional Comments (AI)"):
                            add_comments = get_gpt4_review_additional_comments(classification_dict, res["parsed_data"])
                            st.session_state["aml_ai_additional_comments"] = add_comments

                    # Now show them if exist:
                    if "aml_ai_class_review" in st.session_state:
                        with st.expander("### AI Classification Review", expanded=True):
                            st.markdown(st.session_state["aml_ai_class_review"])

                    if "aml_ai_gene_review" in st.session_state:
                        with st.expander("### AI Gene Analysis", expanded=True):
                            st.markdown(st.session_state["aml_ai_gene_review"])

                    if "aml_ai_mrd_review" in st.session_state:
                        with st.expander("### AI MRD Review", expanded=True):
                            st.markdown(st.session_state["aml_ai_mrd_review"])

                    if "aml_ai_additional_comments" in st.session_state:
                        with st.expander("### AI Additional Comments", expanded=True):
                            st.markdown(st.session_state["aml_ai_additional_comments"])



        ################################################
        # MDS TAB
        ################################################
        with tab_mds:
            st.subheader("Myelodysplastic Syndromes (MDS)")
            mds_mode_toggle = st.checkbox("AI Mode", key="mds_mode_toggle")

            # -------------------
            # MDS Manual
            # -------------------
            if not mds_mode_toggle:
                st.markdown("---")
                manual_data = build_manual_mds_data_compact()

                if st.button("Classify MDS (Manual)"):
                    who_class, who_deriv = classify_MDS_WHO2022(manual_data)
                    icc_class, icc_deriv = classify_MDS_ICC2022(manual_data)

                    st.session_state["mds_manual_result"] = {
                        "parsed_data": manual_data,
                        "who_class": who_class,
                        "who_derivation": who_deriv,
                        "icc_class": icc_class,
                        "icc_derivation": icc_deriv
                    }

                if "mds_manual_result" in st.session_state:
                    res = st.session_state["mds_manual_result"]
                    display_mds_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="manual"
                    )

                    classification_dict = {
                        "WHO 2022": {
                            "Classification": res["who_class"],
                            "Derivation": res["who_derivation"]
                        },
                        "ICC 2022": {
                            "Classification": res["icc_class"],
                            "Derivation": res["icc_derivation"]
                        }
                    }

                    # Horizontal row for MDS review
                    col_rev1, col_rev2 = st.columns(2)
                    with col_rev1:
                        if st.button("🩺 Classification Review"):
                            class_rev = get_gpt4_review_mds_classification(classification_dict, res["parsed_data"])
                            st.session_state["mds_manual_class_review"] = class_rev

                    with col_rev2:
                        if st.button("🧬 Gene Review"):
                            gene_rev = get_gpt4_review_mds_genes(classification_dict, res["parsed_data"])
                            st.session_state["mds_manual_gene_review"] = gene_rev

                    if "mds_manual_class_review" in st.session_state:
                        with st.expander("### AI MDS Classification Review", expanded=True):
                            st.markdown(st.session_state["mds_manual_class_review"])

                    if "mds_manual_gene_review" in st.session_state:
                        with st.expander("### AI MDS Gene Analysis", expanded=True):
                            st.markdown(st.session_state["mds_manual_gene_review"])

            # -------------------
            # MDS AI
            # -------------------
            else:
                st.markdown("---")
                blasts_input = st.text_input("Blasts (%) Override", placeholder="e.g. 8")
                genetics_report = st.text_area("Genetics (MDS)", height=100)
                cytogenetics_report = st.text_area("Cytogenetics (MDS)", height=100)

                if st.button("Parse & Classify MDS (AI)"):
                    combined = f"{genetics_report}\n\n{cytogenetics_report}"
                    if combined.strip():
                        with st.spinner("Parsing & classifying MDS..."):
                            parsed = parse_genetics_report_mds(combined)
                            if blasts_input.strip():
                                try:
                                    parsed["blasts_percentage"] = float(blasts_input.strip())
                                except ValueError:
                                    st.warning("Invalid blasts override")

                            who_class, who_deriv = classify_MDS_WHO2022(parsed)
                            icc_class, icc_deriv = classify_MDS_ICC2022(parsed)

                            st.session_state["mds_ai_result"] = {
                                "parsed_data": parsed,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv
                            }
                    else:
                        st.error("Please provide MDS genetics/cytogenetics data.")

                if "mds_ai_result" in st.session_state:
                    res = st.session_state["mds_ai_result"]
                    display_mds_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode="ai"
                    )

                    classification_dict = {
                        "WHO 2022": {
                            "Classification": res["who_class"],
                            "Derivation": res["who_derivation"]
                        },
                        "ICC 2022": {
                            "Classification": res["icc_class"],
                            "Derivation": res["icc_derivation"]
                        }
                    }

                    # Horizontal row for MDS AI review
                    col_rev1, col_rev2 = st.columns(2)
                    with col_rev1:
                        if st.button("🩺 Classification Review (AI)"):
                            class_rev = get_gpt4_review_mds_classification(classification_dict, res["parsed_data"])
                            st.session_state["mds_ai_class_review"] = class_rev

                    with col_rev2:
                        if st.button("🧬 Gene Review (AI)"):
                            gene_rev = get_gpt4_review_mds_genes(classification_dict, res["parsed_data"])
                            st.session_state["mds_ai_gene_review"] = gene_rev

                    if "mds_ai_class_review" in st.session_state:
                        with st.expander("### AI MDS Classification Review", expanded=True):
                            st.markdown(st.session_state["mds_ai_class_review"])

                    if "mds_ai_gene_review" in st.session_state:
                        with st.expander("### AI MDS Gene Analysis", expanded=True):
                            st.markdown(st.session_state["mds_ai_gene_review"])


        ################################################
        # AML RESPONSE TAB
        ################################################
        with tab_response:
            st.subheader("AML Response Assessment")
            response_mode_toggle = st.checkbox("AI Mode", key="response_mode_toggle")

            # Manual
            if not response_mode_toggle:
                st.markdown("Fill out the form, then click 'Assess AML Response'.")
                manual_data = build_manual_aml_response_data()
                if st.button("Assess AML Response (Manual)"):
                    resp, deriv = classify_AML_Response_ELN2022(manual_data)
                    st.session_state["aml_response_manual"] = {
                        "parsed_data": manual_data,
                        "response": resp,
                        "derivation": deriv
                    }

                if "aml_response_manual" in st.session_state:
                    r = st.session_state["aml_response_manual"]
                    display_aml_response_results(r["parsed_data"], r["response"], r["derivation"], "manual")

            # AI
            else:
                st.markdown("Paste your AML response findings, then click 'Assess AML Response (AI)'.")
                free_text = st.text_area("AML Response (free-text)", height=120)

                if st.button("Assess AML Response (AI)"):
                    if free_text.strip():
                        with st.spinner("Extracting & classifying response..."):
                            parsed = parse_aml_response_report(free_text)
                            if not parsed:
                                st.warning("Parsing returned no data.")
                            else:
                                resp, deriv = classify_AML_Response_ELN2022(parsed)
                                st.session_state["aml_response_ai"] = {
                                    "parsed_data": parsed,
                                    "response": resp,
                                    "derivation": deriv
                                }
                    else:
                        st.error("Please provide AML response text.")

                if "aml_response_ai" in st.session_state:
                    r = st.session_state["aml_response_ai"]
                    display_aml_response_results(r["parsed_data"], r["response"], r["derivation"], "ai")

    else:
        st.info("🔒 **Log in** to use the classification features.")

    st.markdown("---")


def main():
    app_main()

if __name__ == "__main__":
    main()



