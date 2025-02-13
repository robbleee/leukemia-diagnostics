import streamlit as st

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
        show_additional_genetics = st.toggle("Additional / Uncommon AML Genetic Abnormalities", key="show_additional_genetics", value=False)

        if show_additional_genetics:
            st.markdown("##### RARA-related Abnormalities")
            # Arrange the 8 checkboxes in 2 rows of 4 columns each.
            col_rara_row1 = st.columns(4)
            with col_rara_row1[0]:
                irf2bp2_rara = st.checkbox("IRF2BP2::RARA", key="aml_irf2bp2_rara")
            with col_rara_row1[1]:
                npm1_rara = st.checkbox("NPM1::RARA", key="aml_npm1_rara")
            with col_rara_row1[2]:
                zbtb16_rara = st.checkbox("ZBTB16::RARA", key="aml_zbtb16_rara")
            with col_rara_row1[3]:
                stat5b_rara = st.checkbox("STAT5B::RARA", key="aml_stat5b_rara")

            col_rara_row2 = st.columns(4)
            with col_rara_row2[0]:
                stat3_rara = st.checkbox("STAT3::RARA", key="aml_stat3_rara")
            with col_rara_row2[1]:
                rara_tbl1xr1 = st.checkbox("RARA::TBL1XR1", key="aml_rara_tbl1xr1")
            with col_rara_row2[2]:
                rara_fip1l1 = st.checkbox("RARA::FIP1L1", key="aml_rara_fip1l1")
            with col_rara_row2[3]:
                rara_bcor = st.checkbox("RARA::BCOR", key="aml_rara_bcor")

            st.markdown("##### KMT2A-/MECOM-related Abnormalities")
            # Arrange the 9 checkboxes in 3 rows (first two rows with 4 columns, last row with the remaining item).
            col_kmt_row1 = st.columns(4)
            with col_kmt_row1[0]:
                aff1_kmt2a = st.checkbox("AFF1::KMT2A", key="aml_aff1_kmt2a")
            with col_kmt_row1[1]:
                afdn_kmt2a = st.checkbox("AFDN::KMT2A", key="aml_afdn_kmt2a")
            with col_kmt_row1[2]:
                mllt10_kmt2a = st.checkbox("MLLT10::KMT2A", key="aml_mllt10_kmt2a")
            with col_kmt_row1[3]:
                tet1_kmt2a = st.checkbox("TET1::KMT2A", key="aml_tet1_kmt2a")

            col_kmt_row2 = st.columns(4)
            with col_kmt_row2[0]:
                kmt2a_ell = st.checkbox("KMT2A::ELL", key="aml_kmt2a_ell")
            with col_kmt_row2[1]:
                kmt2a_mllt1 = st.checkbox("KMT2A::MLLT1", key="aml_kmt2a_mllt1")
            with col_kmt_row2[2]:
                myc_mecom = st.checkbox("MYC::MECOM", key="aml_myc_mecom")
            with col_kmt_row2[3]:
                etv6_mecom = st.checkbox("ETV6::MECOM", key="aml_etv6_mecom")

            col_kmt_row3 = st.columns(4)
            with col_kmt_row3[0]:
                mecom_runx1 = st.checkbox("MECOM::RUNX1", key="aml_mecom_runx1")
            # The remaining three columns in this row remain empty.
        
        # ---------------------------------------------------------------------
        # Toggle switch for Other Rare Recurring Translocations
        # ---------------------------------------------------------------------
        show_other_translocations = st.toggle("Other Rare Recurring Translocations", key="show_other_translocations", value=False)

        if show_other_translocations:
            st.markdown("##### NUP98-related Abnormalities")
            # Arrange the 2 checkboxes in one row of 4 columns.
            col_nup = st.columns(4)
            with col_nup[0]:
                nup98_nsd1 = st.checkbox("NUP98::NSD1", key="aml_nup98_nsd1")
            with col_nup[1]:
                nup98_kmd5a = st.checkbox("NUP98::KMD5A", key="aml_nup98_kmd5a")
            # The other two columns remain empty.

            st.markdown("##### Other Rare Abnormalities")
            # Arrange the 8 checkboxes in 2 rows of 4 columns.
            col_other_row1 = st.columns(4)
            with col_other_row1[0]:
                prdm16_rpn1 = st.checkbox("PRDM16::RPN1", key="aml_prdm16_rpn1")
            with col_other_row1[1]:
                npm1_mlf1 = st.checkbox("NPM1::MLF1", key="aml_npm1_mlf1")
            with col_other_row1[2]:
                etv6_mnx1 = st.checkbox("ETV6::MNX1", key="aml_etv6_mnx1")
            with col_other_row1[3]:
                kat6a_crebbp = st.checkbox("KAT6A::CREBBP", key="aml_kat6a_crebbp")
            
            col_other_row2 = st.columns(4)
            with col_other_row2[0]:
                picalm_mllt10 = st.checkbox("PICALM::MLLT10", key="aml_picalm_mllt10")
            with col_other_row2[1]:
                fus_erg = st.checkbox("FUS::ERG", key="aml_fus_erg")
            with col_other_row2[2]:
                runx1_cbfa2t3 = st.checkbox("RUNX1::CBFA2T3", key="aml_runx1_cbfa2t3")
            with col_other_row2[3]:
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

def build_manual_ipss_data() -> dict:
    """
    Builds a Streamlit form that collects all relevant IPSS-R / IPSS-M
    information (e.g., blasts, hemoglobin, platelets, etc.), plus
    molecular or cytogenetic markers.

    Returns:
        dict: A dictionary containing the user's input data, ready for
              IPSS-based classification.
    """
    with st.expander("Manual IPSS Data Entry", expanded=True):
        st.markdown("### Manual IPSS Data Entry")

        # ---------------------------------------------------------------------
        # Basic Clinical Fields
        # ---------------------------------------------------------------------
        st.subheader("Clinical Fields")

        bm_blast = st.number_input(
            "Bone Marrow Blasts (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            key="ipss_bm_blast"
        )
        hb = st.number_input(
            "Hemoglobin (g/dL)",
            min_value=0.0,
            max_value=20.0,
            value=10.0,
            key="ipss_hb"
        )
        plt_count = st.number_input(
            "Platelet Count (1e9/L)",
            min_value=0,
            max_value=2000,
            value=150,
            key="ipss_plt"
        )
        anc = st.number_input(
            "Absolute Neutrophil Count (1e9/L)",
            min_value=0.0,
            max_value=100.0,
            value=2.0,
            key="ipss_anc"
        )
        age = st.number_input(
            "Age (years)",
            min_value=0,
            max_value=120,
            value=70,
            key="ipss_age"
        )

        # ---------------------------------------------------------------------
        # Cytogenetics Category (for IPSS-R)
        # ---------------------------------------------------------------------
        st.subheader("Cytogenetics (IPSS-R Category)")
        cyto_options = ["Very Good", "Good", "Intermediate", "Poor", "Very Poor"]
        cyto_ipssr = st.selectbox(
            "Select IPSS-R Cytogenetics Category",
            cyto_options,
            index=2,
            key="ipss_cyto_ipssr"
        )

        # ---------------------------------------------------------------------
        # Additional Cytogenetic Abnormalities (for IPSS-M if needed)
        # ---------------------------------------------------------------------
        st.markdown("#### Cytogenetic Abnormalities (Optional / IPSS-M)")
        col_cg1, col_cg2 = st.columns(2)
        with col_cg1:
            del5q = st.checkbox("del(5q)", key="ipss_del5q")
            del7_7q = st.checkbox("del(7) or del(7q)", key="ipss_del7_7q")
            del17_17p = st.checkbox("del(17) or del(17p)", key="ipss_del17_17p")
            complex_kary = st.checkbox("Complex Karyotype", key="ipss_complex")

        # If you have more cytogenetic flags for IPSS-M, add them here.

        # ---------------------------------------------------------------------
        # Molecular Data / Genes
        # ---------------------------------------------------------------------
        st.subheader("Molecular Markers (Gene Mutations)")
        st.markdown("Check any that are **detected** in this patient. If undetected or unknown, leave unchecked.")
        # You can group them in columns or in toggles, as you prefer.

        # Example: 2 columns for main genes
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            asxl1 = st.checkbox("ASXL1 mutation", key="ipss_asxl1")
            srsf2 = st.checkbox("SRSF2 mutation", key="ipss_srsf2")
            dnmt3a = st.checkbox("DNMT3A mutation", key="ipss_dnmt3a")
            runx1 = st.checkbox("RUNX1 mutation", key="ipss_runx1")
            u2af1 = st.checkbox("U2AF1 mutation", key="ipss_u2af1")
            ezh2 = st.checkbox("EZH2 mutation", key="ipss_ezh2")
        with col_m2:
            sf3b1 = st.checkbox("SF3B1 mutation", key="ipss_sf3b1")
            cbl = st.checkbox("CBL mutation", key="ipss_cbl")
            nras = st.checkbox("NRAS mutation", key="ipss_nras")
            idh2 = st.checkbox("IDH2 mutation", key="ipss_idh2")
            kras = st.checkbox("KRAS mutation", key="ipss_kras")
            npm1 = st.checkbox("NPM1 mutation", key="ipss_npm1")

        # Additional lines for other genes if needed:
        col_m3, col_m4 = st.columns(2)
        with col_m3:
            # Example placeholders
            srsf2_extra = st.checkbox("TP53 multi-hit", key="ipss_tp53multi")
            flt3 = st.checkbox("FLT3 (ITD / TKD)", key="ipss_flt3")
        with col_m4:
            # More placeholders
            mll_ptd = st.checkbox("MLL PTD", key="ipss_mll_ptd")
            etv6 = st.checkbox("ETV6 mutation", key="ipss_etv6")

        # If you want to collect additional numeric data (like VAFs), add them here:
        tp53_vaf = st.number_input(
            "Max VAF of TP53 mutation (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            key="ipss_tp53maxvaf"
        )

    # -------------------------------------------------------------------------
    # Build a dictionary to hold the user's input
    # -------------------------------------------------------------------------
    manual_data = {
        # Clinical fields
        "BM_BLAST": bm_blast,
        "HB": hb,
        "PLT": plt_count,
        "ANC": anc,
        "AGE": age,
        "CYTO_IPSSR": cyto_ipssr,

        # Additional cytogenetics for IPSS-M
        "del5q": del5q,
        "del7_7q": del7_7q,
        "del17_17p": del17_17p,
        "complex": complex_kary,

        # Example molecular markers (you can expand as needed).
        "ASXL1": asxl1,
        "SRSF2": srsf2,
        "DNMT3A": dnmt3a,
        "RUNX1": runx1,
        "U2AF1": u2af1,
        "EZH2": ezh2,
        "SF3B1": sf3b1,
        "CBL": cbl,
        "NRAS": nras,
        "IDH2": idh2,
        "KRAS": kras,
        "NPM1": npm1,
        "TP53multi": srsf2_extra,  # rename as needed
        "FLT3": flt3,
        "MLL_PTD": mll_ptd,
        "ETV6": etv6,

        # Example numeric field for TP53 VAF
        "TP53maxvaf": tp53_vaf,
    }

    return manual_data
