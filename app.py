import streamlit as st
import bcrypt
import json
import datetime
from openai import OpenAI
from streamlit_option_menu import option_menu
from fpdf import FPDF
import re
import base64
import streamlit.components.v1 as components 

# Example imports for your parsers/classifiers
from parsers.aml_parser import parse_genetics_report_aml
from parsers.aml_response_parser import parse_aml_response_report
from parsers.mds_parser import parse_genetics_report_mds
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.aml_response_classifier import classify_AML_Response_ELN2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022
from classifiers.aml_risk_classifier import classify_ELN2022

# Splitted review imports
from reviewers.aml_reviewer import (
    get_gpt4_review_aml_classification,
    get_gpt4_review_aml_genes,
    get_gpt4_review_aml_additional_comments,
    get_gpt4_review_aml_mrd
)
from reviewers.mds_reviewer import (
    get_gpt4_review_mds_classification,
    get_gpt4_review_mds_genes,
    get_gpt4_review_mds_additional_comments
)


##################################
# PAGE CONFIG
##################################
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.session_state["username"] = ""

if st.session_state["authenticated"]:
    st.set_page_config(
        page_title="Haematologic Classification",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
else:
    st.set_page_config(
        page_title="Haematologic Classification",
        layout="wide",
        initial_sidebar_state="expanded"
    )


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
        st.sidebar.header("Login for all Features")
        username = st.sidebar.text_input("Username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", key="login_password")

        if st.sidebar.button("Login", key="login_button"):
            if authenticate_user(username, password):
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.sidebar.success("Logged in successfully!")
                # Force a full script rerun so that the top-level st.set_page_config()
                # sees authenticated=True and collapses the sidebar immediately:
                st.rerun()
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

        /* Updated the checked background to teal (#009688) */
        .toggle-switch-label input:checked + span {
            background-color: #009688;
        }

        /* Moves toggle circle on check */
        .toggle-switch-label input:checked + span:before {
            transform: translateX(26px);
        }

        .toggle-switch-label span {
            position: absolute;
            cursor: pointer;
            background-color: #ccc; /* Unchecked color */
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

        /* Increase tab text size (only relevant if you still use st.tabs) */
        div[data-baseweb="tabs"] > div > div {
            font-size: 20px;
            font-weight: bold;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def add_custom_css():
    st.markdown(
        """
        <style>
        /* Buttons with a teal outline */
        .stButton > button {
            background-color: white;
            color: #009688; /* Teal text */
            border: 2px solid #009688; /* Teal outline */
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }

        .stButton > button:hover {
            background-color: #E0F2F1; /* Light pastel teal on hover */
            color: #00695C;           /* Slightly darker teal text on hover */
            border-color: #00695C;    /* Darker teal outline on hover */
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

local_css()
add_custom_css()


##################################
# FORMS & PARSING HELPERS
##################################
def build_manual_aml_data() -> dict:
    # Wrap the entire form in one top-level expander.
    with st.expander("Manual Input Area", expanded=True):
        st.markdown("### Manual AML Data Entry")
        
        # ---------------------------------------------------------------------
        # Blasts
        # ---------------------------------------------------------------------
        blasts = st.number_input(
            "Blasts (%)",
            min_value=0.0, 
            max_value=100.0, 
            value=0.0,
            key="aml_blasts_percentage"
        )

        # ---------------------------------------------------------------------
        # AML-defining Recurrent Genetic Abnormalities (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### AML-defining Recurrent Genetic Abnormalities")
        c_aml1, c_aml2, c_aml3, c_aml4 = st.columns(4)

        with c_aml1:
            pml_rara = st.checkbox("PML::RARA fusion", key="aml_pml_rara")
            npm1 = st.checkbox("NPM1 mutation", key="aml_npm1_mutation")
            runx1_runx1t1 = st.checkbox("RUNX1::RUNX1T1 fusion", key="aml_runx1_runx1t1")
            cbfb_myh11 = st.checkbox("CBFB::MYH11 fusion", key="aml_cbfb_myh11")

        with c_aml2:
            dek_nup214 = st.checkbox("DEK::NUP214 fusion", key="aml_dek_nup214")
            rbm15_mrtfa = st.checkbox("RBM15::MRTFA fusion", key="aml_rbm15_mrtfa")
            mllt3_kmt2a = st.checkbox("MLLT3::KMT2A fusion", key="aml_mllt3_kmt2a")

        with c_aml3:
            kmt2a = st.checkbox("KMT2A rearrangement (other)", key="aml_kmt2a_other")
            mecom = st.checkbox("MECOM rearrangement", key="aml_mecom")
            nup98 = st.checkbox("NUP98 rearrangement", key="aml_nup98")

        with c_aml4:
            cebpa = st.checkbox("CEBPA mutation", key="aml_cebpa_mutation")
            bzip = st.checkbox("CEBPA bZIP mutation", key="aml_cebpa_bzip")
            bcr_abl1 = st.checkbox("BCR::ABL1 fusion", key="aml_bcr_abl1")

        # Pre-define additional variables (default values)
        # Additional / Uncommon AML Genetic Abnormalities
        irf2bp2_rara = False
        npm1_rara = False
        zbtb16_rara = False
        stat5b_rara = False
        stat3_rara = False
        rara_tbl1xr1 = False
        rara_fip1l1 = False
        rara_bcor = False

        aff1_kmt2a = False
        afdn_kmt2a = False
        mllt10_kmt2a = False
        tet1_kmt2a = False
        kmt2a_ell = False
        kmt2a_mllt1 = False
        myc_mecom = False
        etv6_mecom = False
        mecom_runx1 = False

        # Other Rare Recurring Translocations
        prdm16_rpn1 = False
        npm1_mlf1 = False
        nup98_nsd1 = False
        nup98_kmd5a = False
        etv6_mnx1 = False
        kat6a_crebbp = False
        picalm_mllt10 = False
        fus_erg = False
        runx1_cbfa2t3 = False
        cbfa2t3_glis2 = False

        # ---------------------------------------------------------------------
        # Toggle switch for Additional / Uncommon AML Genetic Abnormalities
        # ---------------------------------------------------------------------


        # Toggle switch for 'Free Text Mode'
        show_additional_genetics = st.toggle("Additional / Uncommon AML Genetic Abnormalities", key="show_additional_genetics", value=False)

        if show_additional_genetics:
            st.markdown("##### RARA-related Abnormalities")
            # Arrange into two columns
            col_rara1, col_rara2 = st.columns(2)
            with col_rara1:
                irf2bp2_rara = st.checkbox("IRF2BP2::RARA", key="aml_irf2bp2_rara")
                npm1_rara = st.checkbox("NPM1::RARA", key="aml_npm1_rara")
                zbtb16_rara = st.checkbox("ZBTB16::RARA", key="aml_zbtb16_rara")
                stat5b_rara = st.checkbox("STAT5B::RARA", key="aml_stat5b_rara")
            with col_rara2:
                stat3_rara = st.checkbox("STAT3::RARA", key="aml_stat3_rara")
                rara_tbl1xr1 = st.checkbox("RARA::TBL1XR1", key="aml_rara_tbl1xr1")
                rara_fip1l1 = st.checkbox("RARA::FIP1L1", key="aml_rara_fip1l1")
                rara_bcor = st.checkbox("RARA::BCOR", key="aml_rara_bcor")

            st.markdown("##### KMT2A-/MECOM-related Abnormalities")
            # Arrange into three columns
            col_kmt1, col_kmt2, col_kmt3 = st.columns(3)
            with col_kmt1:
                aff1_kmt2a = st.checkbox("AFF1::KMT2A", key="aml_aff1_kmt2a")
                afdn_kmt2a = st.checkbox("AFDN::KMT2A", key="aml_afdn_kmt2a")
            with col_kmt2:
                mllt10_kmt2a = st.checkbox("MLLT10::KMT2A", key="aml_mllt10_kmt2a")
                tet1_kmt2a = st.checkbox("TET1::KMT2A", key="aml_tet1_kmt2a")
            with col_kmt3:
                kmt2a_ell = st.checkbox("KMT2A::ELL", key="aml_kmt2a_ell")
                kmt2a_mllt1 = st.checkbox("KMT2A::MLLT1", key="aml_kmt2a_mllt1")
            # Use a full-width row for the remaining MECOM-related abnormalities.
            myc_mecom = st.checkbox("MYC::MECOM", key="aml_myc_mecom")
            etv6_mecom = st.checkbox("ETV6::MECOM", key="aml_etv6_mecom")
            mecom_runx1 = st.checkbox("MECOM::RUNX1", key="aml_mecom_runx1")



        # Toggle switch for 'Free Text Mode'
        show_other_translocations = st.toggle("Other Rare Recurring Translocations", key="show_other_translocations", value=False)


        if show_other_translocations:
            st.markdown("##### NUP98-related Abnormalities")
            col_nup1, col_nup2 = st.columns(2)
            with col_nup1:
                nup98_nsd1 = st.checkbox("NUP98::NSD1", key="aml_nup98_nsd1")
            with col_nup2:
                nup98_kmd5a = st.checkbox("NUP98::KMD5A", key="aml_nup98_kmd5a")
            
            st.markdown("##### Other Rare Abnormalities")
            col_other1, col_other2, col_other3 = st.columns(3)
            with col_other1:
                prdm16_rpn1 = st.checkbox("PRDM16::RPN1", key="aml_prdm16_rpn1")
                npm1_mlf1 = st.checkbox("NPM1::MLF1", key="aml_npm1_mlf1")
            with col_other2:
                etv6_mnx1 = st.checkbox("ETV6::MNX1", key="aml_etv6_mnx1")
                kat6a_crebbp = st.checkbox("KAT6A::CREBBP", key="aml_kat6a_crebbp")
            with col_other3:
                picalm_mllt10 = st.checkbox("PICALM::MLLT10", key="aml_picalm_mllt10")
                fus_erg = st.checkbox("FUS::ERG", key="aml_fus_erg")
                runx1_cbfa2t3 = st.checkbox("RUNX1::CBFA2T3", key="aml_runx1_cbfa2t3")
                cbfa2t3_glis2 = st.checkbox("CBFA2T3::GLIS2", key="aml_cbfa2t3_glis2")

        # ---------------------------------------------------------------------
        # Biallelic TP53
        # ---------------------------------------------------------------------
        st.markdown("#### Biallelic TP53 Mutation")
        tp1, tp2, tp3, tp4 = st.columns(4)
        with tp1:
            two_tp53 = st.checkbox("2 x TP53 mutations", key="aml_tp53_2")
        with tp2:
            one_tp53_del17p = st.checkbox("1 x TP53 + del(17p)", key="aml_tp53_del17p")
        with tp3:
            one_tp53_loh = st.checkbox("1 x TP53 + LOH", key="aml_tp53_loh")
        with tp4:
            one_tp53_10_vaf = st.checkbox("1 x TP53 with 10% vaf", key="aml_tp53_10_vaf")

        # ---------------------------------------------------------------------
        # MDS-related Mutations (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### MDS-related Mutations")
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)
        with col_a1:
            asxl1 = st.checkbox("ASXL1", key="aml_asxl1")
            bcor = st.checkbox("BCOR", key="aml_bcor")
            ezh2 = st.checkbox("EZH2", key="aml_ezh2")
        with col_a2:
            runx1_mds = st.checkbox("RUNX1 (MDS-related)", key="aml_runx1_mds")
            sf3b1 = st.checkbox("SF3B1", key="aml_sf3b1")
        with col_a3:
            srsf2 = st.checkbox("SRSF2", key="aml_srsf2")
            stag2 = st.checkbox("STAG2", key="aml_stag2")
        with col_a4:           
            u2af1 = st.checkbox("U2AF1", key="aml_u2af1")
            zrsr2 = st.checkbox("ZRSR2", key="aml_zrsr2")

        # ---------------------------------------------------------------------
        # MDS-related Cytogenetics (4 columns)
        # ---------------------------------------------------------------------
        st.markdown("#### MDS-related Cytogenetics")
        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        with col_b1:
            complex_kary = st.checkbox("Complex karyotype", key="aml_complex_karyotype")
            del_5q = st.checkbox("del(5q)", key="aml_del_5q")
            t_5q = st.checkbox("t(5q)", key="aml_t_5q")
            add_5q = st.checkbox("add(5q)", key="aml_add_5q")
            minus7 = st.checkbox("-7", key="aml_minus7")
        with col_b2:
            del_7q = st.checkbox("del(7q)", key="aml_del_7q")
            plus8 = st.checkbox("+8", key="aml_plus8")
            del_11q = st.checkbox("del(11q)", key="aml_del_11q")
            del_12p = st.checkbox("del(12p)", key="aml_del_12p")
            t_12p = st.checkbox("t(12p)", key="aml_t_12p")
        with col_b3:
            add_12p = st.checkbox("add(12p)", key="aml_add_12p")
            minus13 = st.checkbox("-13", key="aml_minus13")
            i_17q = st.checkbox("i(17q)", key="aml_i_17q")
            minus17 = st.checkbox("-17", key="aml_minus17")
            add_17p = st.checkbox("add(17p)", key="aml_add_17p")
        with col_b4:
            del_17p = st.checkbox("del(17p)", key="aml_del_17p")
            del_20q = st.checkbox("del(20q)", key="aml_del_20q")
            idic_x_q13 = st.checkbox("idic_X_q13", key="aml_idic_x_q13")

        # ---------------------------------------------------------------------
        # AML Differentiation
        # ---------------------------------------------------------------------
        aml_diff = st.text_input(
            "AML differentiation (e.g. 'FAB M3', 'M4')",
            value="", 
            key="aml_differentiation"
        )

        # ---------------------------------------------------------------------
        # Qualifiers
        # ---------------------------------------------------------------------
        st.markdown("#### Qualifiers")
        qc1, qc2 = st.columns(2)
        with qc1:
            prev_mds_3mo = st.checkbox("Previous MDS diagnosed >3 months ago", key="aml_prev_mds_3mo")
            prev_mds_mpn_3mo = st.checkbox("Previous MDS/MPN diagnosed >3 months ago", key="aml_prev_mds_mpn_3mo")
        with qc2:
            prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="aml_prev_cytotx")
            germ_variant = st.text_input("Predisposing germline variant (if any)", value="None", key="aml_germ_variant")

    # -------------------------------------------------------------------------
    # Collect inputs into a dictionary
    # -------------------------------------------------------------------------
    manual_data = {
        "blasts_percentage": blasts,
        "AML_defining_recurrent_genetic_abnormalities": {
            "PML::RARA": pml_rara,
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
            "BCR::ABL1": bcr_abl1,
            # Additional / Uncommon Abnormalities:
            "IRF2BP2::RARA": irf2bp2_rara,
            "NPM1::RARA": npm1_rara,
            "ZBTB16::RARA": zbtb16_rara,
            "STAT5B::RARA": stat5b_rara,
            "STAT3::RARA": stat3_rara,
            "RARA::TBL1XR1": rara_tbl1xr1,
            "RARA::FIP1L1": rara_fip1l1,
            "RARA::BCOR": rara_bcor,
            "AFF1::KMT2A": aff1_kmt2a,
            "AFDN::KMT2A": afdn_kmt2a,
            "MLLT10::KMT2A": mllt10_kmt2a,
            "TET1::KMT2A": tet1_kmt2a,
            "KMT2A::ELL": kmt2a_ell,
            "KMT2A::MLLT1": kmt2a_mllt1,
            "MYC::MECOM": myc_mecom,
            "ETV6::MECOM": etv6_mecom,
            "MECOM::RUNX1": mecom_runx1,
            # Other Rare Recurring Translocations:
            "PRDM16::RPN1": prdm16_rpn1,
            "NPM1::MLF1": npm1_mlf1,
            "NUP98::NSD1": nup98_nsd1,
            "NUP98::KMD5A": nup98_kmd5a,
            "ETV6::MNX1": etv6_mnx1,
            "KAT6A::CREBBP": kat6a_crebbp,
            "PICALM::MLLT10": picalm_mllt10,
            "FUS::ERG": fus_erg,
            "RUNX1::CBFA2T3": runx1_cbfa2t3,
            "CBFA2T3::GLIS2": cbfa2t3_glis2
        },
        "Biallelic_TP53_mutation": {
            "2_x_TP53_mutations": two_tp53,
            "1_x_TP53_mutation_del_17p": one_tp53_del17p,
            "1_x_TP53_mutation_LOH": one_tp53_loh,
            "1_x_TP53_mutation_10_percent_vaf": one_tp53_10_vaf
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
    # Wrap the entire MDS data entry in one expander
    with st.expander("Manual MDS Input Area", expanded=True):
        st.markdown("### Manual MDS Data Entry")

        c1, c2 = st.columns(2)
        with c1:
            fibrotic = st.checkbox("Fibrotic marrow?", key="mds_fibrotic")
        with c2:
            hypoplasia = st.checkbox("Hypoplastic MDS?", key="mds_hypoplasia")

                
      
        blasts = st.number_input(
            "Blasts (%)", 
            min_value=0.0, max_value=100.0, value=0.0, 
            key="mds_blasts_percentage"
        )

        dys_lineages = st.number_input(
            "Number of Dysplastic Lineages (0-3)",
            min_value=0,
            max_value=3,
            value=0,
            key="mds_dys_lineages"
        )

        st.markdown("#### Biallelic TP53 Mutation")
        ctp1, ctp2, ctp3 = st.columns(3)
        with ctp1:
            tp53_2 = st.checkbox("2 x TP53 mutations", key="mds_tp53_2")
        with ctp2:
            tp53_17p = st.checkbox("1 x TP53 + del(17p)", key="mds_tp53_del17p")
        with ctp3:
            tp53_loh = st.checkbox("1 x TP53 + LOH", key="mds_tp53_loh")

        st.markdown("#### MDS-related Mutation")
        sf3b1 = st.checkbox("SF3B1 mutation", key="mds_sf3b1")

        st.markdown("#### MDS-related Cytogenetics")
        del_5q = st.checkbox("del(5q) / isolated 5q-", key="mds_del_5q")

        st.markdown("#### Qualifiers")

        prev_cytotx = st.checkbox("Previous cytotoxic therapy?", key="mds_prev_cytotx")

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
def display_aml_classification_results(
    parsed_fields,
    classification_who,
    who_derivation,
    classification_icc,
    icc_derivation,
    mode="manual",
    show_parsed_fields: bool = False
):
    """
    Displays AML classification results in Streamlit.

    Args:
        parsed_fields (dict): The raw parsed data values (if you wish to show them).
        classification_who (str): WHO 2022 classification result.
        who_derivation (list): Step-by-step derivation for WHO 2022.
        classification_icc (str): ICC 2022 classification result.
        icc_derivation (list): Step-by-step derivation for ICC 2022.
        mode (str): Typically 'manual' or whatever mode your app uses.
        show_parsed_fields (bool): Whether to show the "View Parsed AML Values" expander.
    """



    ##########################################
    # 3. Display WHO & ICC Classifications Side-by-Side
    ##########################################
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### **WHO 2022 Classification**")
        st.markdown(f"**Classification:** {classification_who}")
    with col2:
        st.markdown("### **ICC 2022 Classification**")
        st.markdown(f"**Classification:** {classification_icc}")

    ##########################################
    # 4. Display Derivations Side-by-Side
    ##########################################
    col_who, col_icc = st.columns(2)

    with col_who:
        with st.expander("View WHO 2022 Derivation", expanded=False):
            who_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(who_derivation, start=1)]
            )
            st.markdown(who_derivation_markdown)

    with col_icc:
        with st.expander("View ICC 2022 Derivation", expanded=False):
            icc_derivation_markdown = "\n\n".join(
                [f"**Step {idx}:** {step}" for idx, step in enumerate(icc_derivation, start=1)]
            )
            st.markdown(icc_derivation_markdown)

    ##########################################
    # 1. (Optional) Show JSON of parsed fields
    ##########################################
    if show_parsed_fields:
        with st.expander("View Parsed AML Values", expanded=False):
            st.json(parsed_fields)

def display_mds_classification_results(parsed_fields, classification_who, derivation_who,
                                       classification_icc, derivation_icc, mode="manual"):
    """
    Displays MDS classification results WITHOUT automatically calling the AI review.
    """
    with st.expander("View Parsed MDS Values", expanded=False):
        st.json(parsed_fields)
    




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



##################################
# PDF CONVERTER HELPERS
##################################
def clean_text(text: str) -> str:
    # Replace the Unicode heavy arrow (➔) with a simple arrow.
    text = text.replace('\u2794', '->')
    # Remove common markdown tokens
    text = re.sub(r'^\s*#{1,6}\s+', '', text, flags=re.MULTILINE)  # headings
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'__(.*?)__', r'\1', text)        # bold alternate
    text = re.sub(r'\*(.*?)\*', r'\1', text)          # italic
    text = re.sub(r'_(.*?)_', r'\1', text)            # italic alternate
    text = re.sub(r'`{1,3}', '', text)                # inline code
    return text.strip()

def write_line_with_keywords(pdf: FPDF, line: str, line_height: float = 8):
    """
    Writes a line to the PDF, but forces certain keywords to be in bold.
    """
    bold_keywords = ["Classification Review", "Sample Quality:", "Derivation Steps:", "Classification:", "Other Genes"]
    occurrences = []
    for kw in bold_keywords:
        start = line.find(kw)
        if start != -1:
            occurrences.append((start, kw))
    occurrences.sort(key=lambda x: x[0])
    
    current = 0
    if not occurrences:
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line)
        pdf.ln(line_height)
        return
    
    for start, kw in occurrences:
        if start > current:
            pdf.set_font("Arial", "", 10)
            pdf.write(line_height, line[current:start])
        pdf.set_font("Arial", "B", 10)
        pdf.write(line_height, kw)
        current = start + len(kw)
    if current < len(line):
        pdf.set_font("Arial", "", 10)
        pdf.write(line_height, line[current:])
    pdf.ln(line_height)

def output_review_text(pdf: FPDF, review_text: str, section: str):
    """
    Splits review_text into lines and outputs each line.
    
    For sections "MRD Review", "Gene Review", and "Additional Comments", if a line is short
    and entirely uppercase, it is rendered as a subheading (bold, larger font).
    Otherwise, each line is output using write_line_with_keywords() so that specific keywords
    are automatically rendered in bold.
    
    For other sections (for example, "Classification Review"), all lines are output via write_line_with_keywords().
    """
    DUPLICATE_HEADINGS = {
        "MRD Review": ["MRD Strategy", "MRD Review", "MRD Review:"],
        "Gene Review": ["Genetics Review", "Gene Review", "Genetics Review:"],
        "Additional Comments": ["Additional Considerations", "Additional Considerations:"]
    }
    dup_list = DUPLICATE_HEADINGS.get(section, [])
    lines = review_text.splitlines()
    
    for line in lines:
        cleaned_line = clean_text(line)
        if not cleaned_line:
            pdf.ln(4)
            continue
        if dup_list and any(cleaned_line.lower() == dup.lower() for dup in dup_list):
            continue
        if section in ["MRD Review", "Gene Review", "Additional Comments"]:
            if len(cleaned_line) < 30 and cleaned_line.isupper():
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, cleaned_line, ln=1)
                pdf.set_font("Arial", "", 10)
            else:
                write_line_with_keywords(pdf, cleaned_line)
        else:
            write_line_with_keywords(pdf, cleaned_line)

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Arial", "B", 14)
            self.set_text_color(0, 70, 140)
            self.cell(0, 8, "Diagnostic Report", ln=1, align="C")
            self.set_font("Arial", "", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, datetime.datetime.now().strftime("%B %d, %Y"), ln=1, align="C")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def add_section_title(pdf: PDF, title: str):
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(0, 70, 140)
    pdf.cell(0, 10, clean_text(title), ln=1, fill=True)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)

def add_classification_section(pdf: PDF, classification_data: dict):
    line_height = 8
    # WHO 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "WHO 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, line_height, f"Classification: {clean_text(classification_data['WHO']['classification'])}")
    pdf.multi_cell(0, line_height, "Derivation Steps:")
    for i, step in enumerate(classification_data["WHO"]["derivation"], start=1):
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(4)
    # ICC 2022 Section
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, line_height, "ICC 2022", ln=1, border='B')
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, line_height, f"Classification: {clean_text(classification_data['ICC']['classification'])}")
    pdf.multi_cell(0, line_height, "Derivation Steps:")
    for i, step in enumerate(classification_data["ICC"]["derivation"], start=1):
        pdf.multi_cell(0, line_height, f"  {i}. {clean_text(step)}")
    pdf.ln(6)

def add_risk_section(pdf: PDF, risk_data: dict):
    """
    Adds an ELN 2022 Risk Classification section to the PDF.
    Expects risk_data to contain keys 'eln_class' and 'eln_derivation'.
    """
    add_section_title(pdf, "ELN 2022 Risk Classification")
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, f"Risk Category: {risk_data.get('eln_class', 'N/A')}")
    pdf.ln(2)
    pdf.multi_cell(0, 8, "Derivation Steps:")
    for i, step in enumerate(risk_data.get("eln_derivation", []), start=1):
        pdf.multi_cell(0, 8, f"  {i}. {clean_text(step)}")
    pdf.ln(4)

def add_diagnostic_section(pdf: PDF, diag_type: str):
    """
    diag_type: "AML" or "MDS"
    """
    manual_key = diag_type.lower() + "_manual_result"
    ai_key = diag_type.lower() + "_ai_result"
    if manual_key in st.session_state:
        data = st.session_state[manual_key]
        prefix = diag_type.lower() + "_manual"
    elif ai_key in st.session_state:
        data = st.session_state[ai_key]
        prefix = diag_type.lower() + "_ai"
    else:
        return

    classification_data = {
        "WHO": {
            "classification": data["who_class"],
            "derivation": data["who_derivation"]
        },
        "ICC": {
            "classification": data["icc_class"],
            "derivation": data["icc_derivation"]
        }
    }

    add_section_title(pdf, f"{diag_type} Classification Results")
    add_classification_section(pdf, classification_data)

    review_sections = [
        ("Classification Review", prefix + "_class_review"),
        ("MRD Review", prefix + "_mrd_review"),
        ("Gene Review", prefix + "_gene_review"),
        ("Additional Comments", prefix + "_additional_comments")
    ]
    for section_name, key in review_sections:
        if key in st.session_state:
            add_section_title(pdf, section_name)
            output_review_text(pdf, st.session_state[key], section_name)
            pdf.ln(4)

def create_beautiful_pdf(patient_name: str, patient_dob: datetime.date) -> bytes:
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Patient Information Section
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Patient Name: {patient_name}", ln=1)
    pdf.cell(0, 10, f"Date of Birth: {patient_dob.strftime('%B %d, %Y')}", ln=1)
    pdf.ln(10)

    # ----- AML Section -----
    aml_result = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    if aml_result:
        # This function adds classification and review sections if the appropriate keys exist.
        add_diagnostic_section(pdf, "AML")
        
        # Explicitly add individual review sections if needed
        for section_name, key in [
            ("Classification Review", "aml_class_review"),
            ("MRD Review", "aml_mrd_review"),
            ("Gene Review", "aml_gene_review"),
            ("Additional Comments", "aml_additional_comments")
        ]:
            if key in st.session_state:
                add_section_title(pdf, section_name)
                output_review_text(pdf, st.session_state[key], section_name)
                pdf.ln(4)
                
        # Add the Risk Section using the AML result (whether manual or AI)
        if aml_result.get("eln_class"):
            risk_data = {
                "eln_class": aml_result.get("eln_class", "N/A"),
                "eln_derivation": aml_result.get("eln_derivation", [])
            }
            add_risk_section(pdf, risk_data)

    # ----- MDS Section -----
    mds_result = st.session_state.get("mds_manual_result") or st.session_state.get("mds_ai_result")
    if mds_result:
        pdf.add_page()  # Start a new page for MDS diagnostics.
        add_section_title(pdf, "MDS Diagnostics")
        add_diagnostic_section(pdf, "MDS")
        for section_name, key in [
            ("Classification Review", "mds_class_review"),
            ("Gene Review", "mds_gene_review"),
            ("Additional Comments", "mds_additional_comments")
        ]:
            if key in st.session_state:
                add_section_title(pdf, section_name)
                output_review_text(pdf, st.session_state[key], section_name)
                pdf.ln(4)

    return pdf.output(dest="S").encode("latin1")



##################################
# APP MAIN
##################################
def app_main():
    # Initialize expander and section state variables if not present
    if "expanded_aml_section" not in st.session_state:
        st.session_state["expanded_aml_section"] = None
    if "expanded_mds_section" not in st.session_state:
        st.session_state["expanded_mds_section"] = None

    # Session state for free-text expander visibility
    if "aml_free_text_expanded" not in st.session_state:
        st.session_state["aml_free_text_expanded"] = True
    if "mds_free_text_expanded" not in st.session_state:
        st.session_state["mds_free_text_expanded"] = True

    if st.session_state.get("authenticated", False):

        # Top-level menu: AML vs. MDS
        selected_tab = option_menu(
            menu_title=None,
            options=["AML Diagnostics", "MDS Diagnostics"],
            icons=["droplet", "droplet"],
            default_index=0,
            orientation="horizontal"
        )

        # -----------------------------------------------------------
        # AML DIAGNOSTICS
        # -----------------------------------------------------------
        if selected_tab == "AML Diagnostics":
            st.subheader("Acute Myeloid Leukemia (AML)")

            # Toggle switch for 'Free Text Mode'
            aml_mode_toggle = st.toggle("Free Text Mode", key="aml_mode_toggle", value=False)

            if "aml_busy" not in st.session_state:
                st.session_state["aml_busy"] = False

            # --- MANUAL MODE ---
            if not aml_mode_toggle:
                manual_data = build_manual_aml_data()
                if st.button("Analyse Genetics"):
                    st.session_state["aml_busy"] = True
                    with st.spinner("Compiling results. Please wait..."):
                        # Clear old AML keys
                        for key in [
                            "aml_manual_result",
                            "aml_ai_result",
                            "aml_class_review",
                            "aml_mrd_review",
                            "aml_gene_review",
                            "aml_additional_comments"
                        ]:
                            st.session_state.pop(key, None)

                        # Classify
                        classification_who, who_derivation = classify_AML_WHO2022(manual_data)
                        classification_icc, icc_derivation = classify_AML_ICC2022(manual_data)
                        classification_eln, eln_derivation = classify_ELN2022(manual_data)

                        st.session_state["aml_manual_result"] = {
                            "parsed_data": manual_data,
                            "who_class": classification_who,
                            "who_derivation": who_derivation,
                            "icc_class": classification_icc,
                            "icc_derivation": icc_derivation,
                            "eln_class": classification_eln,
                            "eln_derivation": eln_derivation,
                        }
                        st.session_state["expanded_aml_section"] = "classification"
                    st.session_state["aml_busy"] = False

            # --- FREE TEXT MODE ---
            else:
                with st.expander("Free Text Input Area", expanded=st.session_state.get("aml_free_text_expanded", True)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input("Blasts % (Override)", placeholder="25", key="blasts_override")
                    with col2:
                        st.text_input("AML Differentiation", placeholder="FAB M3", key="diff_override")
                    st.text_input("Morphology/Clinical Info", placeholder="e.g. Dysplasia observed...", key="morph_input")
                    st.text_area("Genetics Report:", height=100, key="genetics_report")
                    st.text_area("Cytogenetics Report:", height=100, key="cytogenetics_report")

                if st.button("Analyse Genetics"):
                    # Collapse the free text input area on classification
                    st.session_state["aml_free_text_expanded"] = False

                    for key in [
                        "aml_manual_result",
                        "aml_ai_result",
                        "aml_class_review",
                        "aml_mrd_review",
                        "aml_gene_review",
                        "aml_additional_comments"
                    ]:
                        st.session_state.pop(key, None)

                    # Gather inputs
                    blasts_override = st.session_state.get("blasts_override", "")
                    diff_override = st.session_state.get("diff_override", "")
                    morph_input = st.session_state.get("morph_input", "")
                    genetics_report = st.session_state.get("genetics_report", "")
                    cytogenetics_report = st.session_state.get("cytogenetics_report", "")
                    combined = f"{genetics_report}\n\n{cytogenetics_report}"

                    if combined.strip():
                        with st.spinner("Parsing & classifying ..."):
                            parsed_data = parse_genetics_report_aml(combined)
                            if blasts_override.strip():
                                try:
                                    parsed_data["blasts_percentage"] = float(blasts_override.strip())
                                except ValueError:
                                    st.warning("Invalid blasts override.")
                            if diff_override.strip():
                                parsed_data["AML_differentiation"] = diff_override.strip()
                            if morph_input.strip():
                                parsed_data["morphology_clinical"] = morph_input.strip()

                            # Classify
                            who_class, who_deriv = classify_AML_WHO2022(parsed_data)
                            icc_class, icc_deriv = classify_AML_ICC2022(parsed_data)
                            eln_class, eln_deriv = classify_ELN2022(parsed_data)

                            st.session_state["aml_ai_result"] = {
                                "parsed_data": parsed_data,
                                "who_class": who_class,
                                "who_derivation": who_deriv,
                                "icc_class": icc_class,
                                "icc_derivation": icc_deriv,
                                "eln_class": eln_class,
                                "eln_derivation": eln_deriv,
                                "free_text_input": combined
                            }
                            st.session_state["expanded_aml_section"] = "classification"
                    else:
                        st.error("No AML data provided.")

            # --- If AML results exist, show sub-menu ---
            if "aml_manual_result" in st.session_state or "aml_ai_result" in st.session_state:

                # Priority: manual -> ai
                if "aml_manual_result" in st.session_state:
                    res = st.session_state["aml_manual_result"]
                    mode = "manual"
                else:
                    res = st.session_state["aml_ai_result"]
                    mode = "ai"

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

                # Retrieve the free text input value if available (only in free text/ai mode)
                free_text_input_value = res.get("free_text_input") if mode == "ai" else None

                sub_tab = option_menu(
                    menu_title=None,
                    options=["Classification", "Risk", "MRD Review", "Gene Review", "Additional Comments"],
                    icons=["clipboard", "graph-up-arrow", "recycle", "bar-chart", "chat-left-text"],
                    default_index=0,
                    orientation="horizontal"
                )

                # 1) Classification (show derivation + classification review here!)
                if sub_tab == "Classification":
                    # Show the raw classification data
                    display_aml_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode=mode
                    )

                    # Then show the classification review beneath
                    if "aml_class_review" not in st.session_state:
                        with st.spinner("Generating Classification Review..."):
                            st.session_state["aml_class_review"] = get_gpt4_review_aml_classification(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=free_text_input_value
                            )

                    st.markdown("### Classification Review")
                    st.markdown(st.session_state["aml_class_review"])

                # 2) MRD Review
                elif sub_tab == "MRD Review":
                    if "aml_mrd_review" not in st.session_state:
                        with st.spinner("Generating MRD Review..."):
                            st.session_state["aml_mrd_review"] = get_gpt4_review_aml_mrd(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=free_text_input_value
                            )
                    with st.expander("MRD Review", expanded=True):
                        st.markdown(st.session_state["aml_mrd_review"])

                # 3) Gene Review
                elif sub_tab == "Gene Review":
                    if "aml_gene_review" not in st.session_state:
                        with st.spinner("Generating Gene Review..."):
                            st.session_state["aml_gene_review"] = get_gpt4_review_aml_genes(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=free_text_input_value
                            )
                    with st.expander("Gene Review", expanded=True):
                        st.markdown(st.session_state["aml_gene_review"])

                # 4) Additional Comments
                elif sub_tab == "Additional Comments":
                    if "aml_additional_comments" not in st.session_state:
                        with st.spinner("Generating Additional Comments..."):
                            st.session_state["aml_additional_comments"] = get_gpt4_review_aml_additional_comments(
                                classification_dict,
                                res["parsed_data"],
                                free_text_input=free_text_input_value
                            )
                    with st.expander("Additional Comments", expanded=True):
                        st.markdown(st.session_state["aml_additional_comments"])

                # 5) Risk
                elif sub_tab == "Risk":
                    st.markdown("### ELN 2022 Risk Classification")
                    st.markdown(f"**Risk Category:** {res['eln_class']}")
                    with st.expander("ELN Derivation", expanded=True):
                        for i, step in enumerate(res["eln_derivation"], start=1):
                            st.markdown(f"- {step}")

                # --- PDF Download ---
                if "show_pdf_form" not in st.session_state:
                    st.session_state.show_pdf_form = False
                if st.button("Download Report"):
                    st.session_state.show_pdf_form = True
                if st.session_state.show_pdf_form:
                    with st.form(key="pdf_info_form"):
                        patient_name = st.text_input("Enter Patient Name:")
                        patient_dob = st.date_input("Enter Date of Birth:")
                        submit_pdf = st.form_submit_button("Submit")
                    if submit_pdf:
                        if not patient_name:
                            st.error("Please enter the patient name.")
                        else:
                            pdf_bytes = create_beautiful_pdf(patient_name, patient_dob)
                            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                            download_html = f'''
                                <a id="pdf_download" href="data:application/pdf;base64,{pdf_base64}" download="diagnostic_report.pdf"></a>
                                <script>
                                    setTimeout(function() {{
                                        document.getElementById("pdf_download").click();
                                    }}, 100);
                                </script>
                            '''
                            components.html(download_html, height=0)
                            st.session_state.show_pdf_form = False

        # -----------------------------------------------------------
        # MDS DIAGNOSTICS
        # -----------------------------------------------------------
        elif selected_tab == "MDS Diagnostics":
            st.subheader("Myelodysplastic Syndromes (MDS)")
            mds_mode_toggle = st.toggle("Free Text Mode", key="mds_mode_toggle", value=False)


            # --- MANUAL MODE ---
            if not mds_mode_toggle:
                manual_data = build_manual_mds_data_compact()
                if st.button("Classify MDS (Manual)"):
                    for key in ["mds_manual_result", "mds_class_review", "mds_gene_review", "mds_additional_comments"]:
                        st.session_state.pop(key, None)

                    who_class, who_deriv = classify_MDS_WHO2022(manual_data)
                    icc_class, icc_deriv = classify_MDS_ICC2022(manual_data)
                    st.session_state["mds_manual_result"] = {
                        "parsed_data": manual_data,
                        "who_class": who_class,
                        "who_derivation": who_deriv,
                        "icc_class": icc_class,
                        "icc_derivation": icc_deriv
                    }
                    st.session_state["expanded_mds_section"] = "classification"

            # --- FREE TEXT MODE ---
            else:
                with st.expander("MDS Free Text Input Area", expanded=st.session_state["mds_free_text_expanded"]):
                    st.markdown("Paste your free-text MDS genetics/cytogenetics data below:")
                    st.text_input("Blasts (%) Override", placeholder="e.g. 8", key="mds_blasts_input")
                    st.text_area("Genetics (MDS)", height=100, key="mds_genetics_report")
                    st.text_area("Cytogenetics (MDS)", height=100, key="mds_cytogenetics_report")
                if st.button("Parse & Classify MDS"):
                    # Collapse the free text input area for MDS upon classification
                    st.session_state["mds_free_text_expanded"] = False

                    for key in [
                        "mds_manual_result", 
                        "mds_class_review", 
                        "mds_gene_review", 
                        "mds_additional_comments", 
                        "mds_ai_result"
                    ]:
                        st.session_state.pop(key, None)

                    blasts_input = st.session_state.get("mds_blasts_input", "")
                    genetics_report = st.session_state.get("mds_genetics_report", "")
                    cytogenetics_report = st.session_state.get("mds_cytogenetics_report", "")
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
                            st.session_state["expanded_mds_section"] = "classification"
                    else:
                        st.error("Please provide MDS genetics/cytogenetics data.")

            # --- If MDS results exist, show sub-menu ---
            if "mds_manual_result" in st.session_state or "mds_ai_result" in st.session_state:
                if "mds_manual_result" in st.session_state:
                    res = st.session_state["mds_manual_result"]
                    mode = "manual"
                else:
                    res = st.session_state["mds_ai_result"]
                    mode = "ai"

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

                # We remove "Classification Review" from the sub-menu
                mds_tab = option_menu(
                    menu_title=None,
                    options=["Classification", "Gene Review", "Additional Comments"],
                    icons=["clipboard", "bar-chart", "chat-left-text"],
                    default_index=0,
                    orientation="horizontal"
                )

                # Classification => Show derivation + Classification Review
                if mds_tab == "Classification":
                    display_mds_classification_results(
                        res["parsed_data"],
                        res["who_class"],
                        res["who_derivation"],
                        res["icc_class"],
                        res["icc_derivation"],
                        mode=mode
                    )
                    # Then show classification review below
                    if "mds_class_review" not in st.session_state:
                        with st.spinner("Generating MDS Classification Review..."):
                            st.session_state["mds_class_review"] = get_gpt4_review_mds_classification(
                                classification_dict,
                                res["parsed_data"]
                            )

                    st.markdown("### Classification Review")
                    st.markdown(st.session_state["mds_class_review"])

                # Gene Review
                elif mds_tab == "Gene Review":
                    if "mds_gene_review" not in st.session_state:
                        with st.spinner("Generating Gene Review..."):
                            st.session_state["mds_gene_review"] = get_gpt4_review_mds_genes(
                                classification_dict,
                                res["parsed_data"]
                            )
                    with st.expander("Gene Review", expanded=True):
                        st.markdown(st.session_state["mds_gene_review"])

                # Additional Comments
                elif mds_tab == "Additional Comments":
                    if "mds_additional_comments" not in st.session_state:
                        with st.spinner("Generating Additional Comments..."):
                            st.session_state["mds_additional_comments"] = get_gpt4_review_mds_additional_comments(
                                classification_dict,
                                res["parsed_data"]
                            )
                    with st.expander("Additional Comments", expanded=True):
                        st.markdown(st.session_state["mds_additional_comments"])

    else:
        st.info("🔒 **Log in** to use the classification features.")

def main():
    app_main()

if __name__ == "__main__":
    main()




