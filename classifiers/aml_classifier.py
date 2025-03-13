import json


##############################
# CLASSIFY AML WHO 2022
##############################
def classify_AML_WHO2022(parsed_data: dict, not_erythroid: bool = False) -> tuple:
    """
    Classifies AML subtypes based on WHO 2022 criteria, including qualifiers.
    If the final classification is "Acute myeloid leukaemia, [define by differentiation]",
    we attempt to insert AML_differentiation from parsed_data if available.

    WHO accepts these 'previous_cytotoxic_therapy' options:
      - Ionising radiation
      - Cytotoxic chemotherapy
      - Any combination

    If any of these is found, we append "previous cytotoxic therapy" as a qualifier.
    'Immune interventions' is not recognized by WHO.

    Additionally, if either 'previous_MDS_diagnosed_over_3_months_ago' or
    'previous_MDS/MPN_diagnosed_over_3_months_ago' is true, we add a qualifier
    "progressed from MDS".

    Args:
        parsed_data (dict): Extracted report data.
        not_erythroid (bool): If True, prevents overriding classification with an erythroid subtype.

    Returns:
        tuple: (classification (str), derivation (list of str))
    """
    derivation = []
    
    # Validate blasts_percentage
    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")
    if blasts_percentage is None:
        msg = "Error: blasts_percentage is missing. Classification cannot proceed."
        derivation.append(msg)
        return (msg, derivation)
    if not isinstance(blasts_percentage, (int, float)) or not (0.0 <= blasts_percentage <= 100.0):
        msg = "Error: blasts_percentage must be a number between 0 and 100."
        derivation.append(msg)
        return (msg, derivation)

    classification = "Acute myeloid leukaemia, [define by differentiation]"
    derivation.append(f"Default classification set to: {classification}")

    # STEP 1: AML-Defining Recurrent Genetic Abnormalities (WHO)
    aml_def_map = {
        "PML::RARA": "Acute promyelocytic leukaemia with PML::RARA fusion",
        "NPM1": "AML with NPM1 mutation",
        "RUNX1::RUNX1T1": "AML with RUNX1::RUNX1T1 fusion",
        "CBFB::MYH11": "AML with CBFB::MYH11 fusion",
        "DEK::NUP214": "AML with DEK::NUP214 fusion",
        "RBM15::MRTFA": "AML with RBM15::MRTFA fusion",
        "MLLT3::KMT2A": "AML with KMT2A rearrangement",
        "GATA2:: MECOM": "AML with MECOM rearrangement",
        "KMT2A": "AML with KMT2A rearrangement",
        "MECOM": "AML with MECOM rearrangement",
        "NUP98": "AML with NUP98 rearrangement",
        "CEBPA": "AML with CEBPA mutation",  # Requires blasts >=20%
        "bZIP": "AML with CEBPA mutation",   # Requires blasts >=20%
        "BCR::ABL1": "AML with BCR::ABL1 fusion"  # Requires blasts >=20%
    }
    aml_gen_abn = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    true_aml_genes = [gene for gene, val in aml_gen_abn.items() if val]

    if not true_aml_genes:
        derivation.append("All AML-defining recurrent genetic abnormality flags are false.")
        if blasts_percentage < 20:
            classification = "Not AML, consider MDS classification"
            derivation.append("No AML-defining abnormalities and blasts <20 => consider reclassification as MDS.")
    else:
        derivation.append(f"Detected AML-defining abnormality flags: {', '.join(true_aml_genes)}")
        updated = False
        for gene, final_label in aml_def_map.items():
            if aml_gen_abn.get(gene, False):
                # For certain genes require blasts >=20
                if gene in ["CEBPA", "bZIP", "BCR::ABL1"]:
                    if blasts_percentage >= 20:
                        classification = final_label
                        derivation.append(f"{gene} with blasts >=20 => {classification}")
                        updated = True
                        break
                    else:
                        derivation.append(f"{gene} found but blasts <20 => not AML by this route")
                else:
                    classification = final_label
                    derivation.append(f"{gene} => {classification}")
                    updated = True
                    break
        if not updated and blasts_percentage < 20:
            classification = "Not AML, consider MDS classification"
            derivation.append("No AML-defining abnormality fully matched, blasts <20 => consider MDS.")

    # STEP 2: MDS-Related Mutations
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_mut = parsed_data.get("MDS_related_mutation", {})
        found = [g for g, val in mds_mut.items() if val]
        if found:
            classification = "AML, myelodysplasia related"
            derivation.append(f"MDS-related mutation(s): {', '.join(found)} => {classification}")
        else:
            derivation.append("No MDS-related mutations found.")

    # STEP 3: MDS-Related Cytogenetics
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
        found_cyto = [abn for abn, val in mds_cyto.items() if val]
        if found_cyto:
            classification = "AML, myelodysplasia related"
            derivation.append(f"MDS-related cytogenetic(s): {', '.join(found_cyto)} => {classification}")
        else:
            derivation.append("No MDS-related cytogenetic flags found.")

    # STEP 4: AML_differentiation override
    aml_diff = parsed_data.get("AML_differentiation")
    if aml_diff: 
        derivation.append(f"AML_differentiation: {aml_diff}")
    else:
        derivation.append("No AML_differentiation provided.")

    FAB_TO_WHO = {
        "M0": "Acute myeloid leukaemia with minimal differentiation",
        "M1": "Acute myeloid leukaemia without maturation",
        "M2": "Acute myeloid leukaemia with maturation",
        "M3": "Acute promyelocytic leukaemia",
        "M4": "Acute myelomonocytic leukaemia",
        "M4Eo": "Acute myelomonocytic leukaemia with eosinophilia",
        "M5a": "Acute monoblastic leukaemia",
        "M5b": "Acute monocytic leukaemia",
        "M6a": "Acute erythroid leukaemia",
        "M6b": "Pure erythroid leukaemia",
        "M7": "Acute megakaryoblastic leukaemia",
    }

    if ("define by differentiation" in classification) or ("Not AML" in classification):
        if aml_diff in ["M6a", "M6b"]:
            if not not_erythroid:
                classification = "Acute Erythroid leukaemia"
                derivation.append(f"Erythroid subtype => {classification}")
            else:
                derivation.append("not_erythroid flag => skipping erythroid override")
        elif classification == "Acute myeloid leukaemia, [define by differentiation]" and aml_diff in FAB_TO_WHO:
            classification = FAB_TO_WHO[aml_diff]
            derivation.append(f"FAB mapping => {classification}")
        elif classification == "Acute myeloid leukaemia, [define by differentiation]":
            classification = "Acute myeloid leukaemia, unknown differentiation"
            derivation.append("No valid AML_differentiation => unknown differentiation")

    # STEP 5: Append Qualifiers
    qualifier_list = []
    q = parsed_data.get("qualifiers", {})

    # Use "previous_cytotoxic_therapy" for WHO.
    therapy_type = q.get("previous_cytotoxic_therapy", "None")
    who_accepted = ["Ionising radiation", "Cytotoxic chemotherapy", "Any combination"]
    if therapy_type in who_accepted:
        qualifier_list.append("previous cytotoxic therapy")
        derivation.append(f"Detected WHO therapy => previous cytotoxic therapy: {therapy_type}")

    # Germline predisposition: WHO uses "associated with"
    germline_var = q.get("predisposing_germline_variant", "").strip()
    if germline_var.lower() not in ["", "none"]:
        raw_vs = [v.strip() for v in germline_var.split(",") if v.strip()]
        no_brackets = [r.split(" (")[0] for r in raw_vs]
        # Exclude "diamond-blackfan anemia" (WHO only)
        final_germ = [x for x in no_brackets if x.lower() != "diamond-blackfan anemia"]
        if final_germ:
            qualifier_list.append("associated with " + ", ".join(final_germ))
            derivation.append("Detected germline predisposition => associated with " + ", ".join(final_germ))
    else:
        derivation.append("No germline predisposition indicated (review at MDT)")

    # NEW: check if "previous_MDS_diagnosed_over_3_months_ago" or "previous_MDS/MPN_diagnosed_over_3_months_ago" is True
    progressed_from_mds = (
        q.get("previous_MDS_diagnosed_over_3_months_ago", False) or
        q.get("previous_MDS/MPN_diagnosed_over_3_months_ago", False)
    )
    if progressed_from_mds:
        qualifier_list.append("progressed from MDS")
        derivation.append("Either previous_MDS or previous_MDS/MPN is True => 'progressed from MDS'")

    if qualifier_list:
        classification += ", " + ", ".join(qualifier_list)
        derivation.append("Classification with qualifiers => " + classification)

    if "Not AML" not in classification:
        classification += " (WHO 2022)"
    derivation.append("Final classification => " + classification)
    return classification, derivation




##############################
# CLASSIFY AML ICC 2022
##############################
def classify_AML_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies AML subtypes based on ICC 2022 criteria, including qualifiers.

    ICC accepts these 'previous_cytotoxic_therapy' options:
      - Ionising radiation
      - Cytotoxic chemotherapy
      - Immune interventions
      - Any combination

    If any are found, "therapy related" is appended as a qualifier.
    'Immune interventions' is recognized by ICC only.

    Additionally, if either 'previous_MDS_diagnosed_over_3_months_ago' or
    'previous_MDS/MPN_diagnosed_over_3_months_ago' is true, we add a qualifier
    "arising post MDS".

    Args:
        parsed_data (dict): Extracted report data.

    Returns:
        tuple: (classification (str), derivation (list of str))
    """
    derivation = []
    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")

    if blasts_percentage is None:
        msg = "Error: blasts_percentage is missing. Classification cannot proceed."
        derivation.append(msg)
        return (msg, derivation)
    if not isinstance(blasts_percentage, (int, float)) or not (0.0 <= blasts_percentage <= 100.0):
        msg = "Error: blasts_percentage must be a number between 0 and 100."
        derivation.append(msg)
        return (msg, derivation)

    classification = "AML, NOS"
    derivation.append(f"Default classification set to: {classification}")

    aml_def_gen = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    mds_mutations = parsed_data.get("MDS_related_mutation", {})
    mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
    qualifiers = parsed_data.get("qualifiers", {})

    # STEP 1: AML-defining Recurrent Genetic Abnormalities (ICC)
    icc_map = {
        "PML::RARA": "APL with t(15;17)(q24.1;q21.2)/PML::RARA",
        "NPM1": "AML with mutated NPM1",
        "RUNX1::RUNX1T1": "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1",
        "CBFB::MYH11": "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11",
        "DEK::NUP214": "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214",
        "RBM15::MRTFA": "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTFA",
        "MLLT3::KMT2A": "AML with t(9;11)(p21.3;q23.3)/MLLT3::KMT2A",
        "GATA2::MECOM": "AML with inv(3)(q21.3q26.2) or t(3;3)(q21.3;q26.2)/GATA2, MECOM(EVI1)",
        "KMT2A": "AML with other KMT2A rearrangements",
        "MECOM": "AML with other MECOM rearrangements",
        "NUP98": "AML with NUP98 and other partners",
        "bZIP": "AML with in-frame bZIP mutated CEBPA",
        "BCR::ABL1": "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1",
        # Rare RARA partners
        "IRF2BP2::RARA": "APL with t(1;17)(q42.3;q21.2)/IRF2BP2::RARA",
        "NPM1::RARA": "APL with t(5;17)(q35.1;q21.2)/NPM1::RARA",
        "ZBTB16::RARA": "APL with t(11;17)(q23.2;q21.2)/ZBTB16::RARA",
        "STAT5B::RARA": "APL with cryptic inv(17) or del(17)(q21.2q21.2)/STAT5B::RARA",
        "STAT3::RARA": "APL with cryptic inv(17) or del(17)(q21.2q21.2)/STAT3::RARA",
        "RARA::TBL1XR1": "APL with RARA::TBL1XR1",
        "RARA::FIP1L1": "APL with RARA::FIP1L1",
        "RARA::BCOR": "APL with RARA::BCOR",
        # More KMT2A
        "AFF1::KMT2A": "AML with t(4;11)(q21.3;q23.3)/AFF1::KMT2A",
        "AFDN::KMT2A": "AML with t(6;11)(q27;q23.3)/AFDN::KMT2A",
        "MLLT10::KMT2A": "AML with t(10;11)(p12.3;q23.3)/MLLT10::KMT2A",
        "TET1::KMT2A": "AML with t(10;11)(q21.3;q23.3)/TET1::KMT2A",
        "KMT2A::ELL": "AML with t(11;19)(q23.3;p13.1)/KMT2A::ELL",
        "KMT2A::MLLT1": "AML with t(11;19)(q23.3;p13.3)/KMT2A::MLLT1",
        # Others
        "MYC::MECOM": "AML with t(3;8)(q26.2;q24.2)/MYC::MECOM",
        "ETV6::MECOM": "AML with t(3;12)(q26.2;p13.2)/ETV6::MECOM",
        "MECOM::RUNX1": "AML with t(3;21)(q26.2;q22.1)/MECOM::RUNX1",
        "PRDM16::RPN1": "AML with t(1;3)(p36.3;q21.3)/PRDM16::RPN1",
        "NPM1::MLF1": "AML with t(3;5)(q25.3;q35.1)/NPM1::MLF1",
        "NUP98::NSD1": "AML with t(5;11)(q35.2;p15.4)/NUP98::NSD1",
        "ETV6::MNX1": "AML with t(7;12)(q36.3;p13.2)/ETV6::MNX1",
        "KAT6A::CREBBP": "AML with t(8;16)(p11.2;p13.3)/KAT6A::CREBBP",
        "PICALM::MLLT10": "AML with t(10;11)(p12.3;q14.2)/PICALM::MLLT10",
        "NUP98::KMD5A": "AML with t(11;12)(p15.4;p13.3)/NUP98::KMD5A",
        "FUS::ERG": "AML with t(16;21)(p11.2;q22.2)/FUS::ERG",
        "RUNX1::CBFA2T3": "AML with t(16;21)(q24.3;q22.1)/RUNX1::CBFA2T3",
        "CBFA2T3::GLIS2": "AML with inv(16)(p13.3q24.3)/CBFA2T3::GLIS2"
    }
    true_flags = [g for g, val in aml_def_gen.items() if val]
    if true_flags:
        derivation.append("ICC AML-defining flags => " + ", ".join(true_flags))
        updated = False
        for gene, label in icc_map.items():
            if aml_def_gen.get(gene, False):
                if blasts_percentage >= 10:
                    classification = label
                    derivation.append(f"{gene} => {classification}")
                    updated = True
                    break
                else:
                    derivation.append(f"{gene} but blasts <10 => cannot label AML here")
        if not updated:
            derivation.append("No single ICC AML-def abnormality triggered classification.")
    else:
        derivation.append("No ICC AML-defining abnormality is True.")

    # STEP 2: Biallelic TP53
    conds = [
        biallelic_tp53.get("2_x_TP53_mutations", False),
        biallelic_tp53.get("1_x_TP53_mutation_del_17p", False),
        biallelic_tp53.get("1_x_TP53_mutation_LOH", False),
        biallelic_tp53.get("1_x_TP53_mutation_10_percent_vaf", False)
    ]
    if classification == "AML, NOS":
        if any(conds):
            classification = "AML with mutated TP53"
            derivation.append("Biallelic TP53 => AML with mutated TP53")
        else:
            derivation.append("No biallelic TP53 conditions met.")

    # STEP 3: MDS-related Mutations
    if classification == "AML, NOS":
        found_mds = [m for m, val in mds_mutations.items() if val]
        if found_mds:
            classification = "AML with myelodysplasia related gene mutation"
            derivation.append("MDS-related genes => " + classification)
        else:
            derivation.append("No MDS-related genes set to True.")

    # STEP 4: MDS-related Cytogenetics
    if classification == "AML, NOS":
        mrd_cyto = [
            "Complex_karyotype", "del_5q", "t_5q", "add_5q", "-7", "del_7q",
            "del_12p", "t_12p", "add_12p", "i_17q", "idic_X_q13"
        ]
        nos_cyto = ["5q", "+8", "del_11q", "12p", "-13", "-17", "add_17p", "del_20q"]
        all_cyts = mrd_cyto + nos_cyto
        found_cyts = [c for c, val in mds_cyto.items() if val and c in all_cyts]
        if found_cyts:
            classification = "AML with myelodysplasia related cytogenetic abnormality"
            derivation.append("MDS-related cyto => " + classification)
        else:
            derivation.append("No MDS-related cytogenetics triggered classification.")

    # STEP 5: Final Blast-Count check
    convertible = {
        "AML with mutated TP53",
        "AML with myelodysplasia related gene mutation",
        "AML with myelodysplasia related cytogenetic abnormality",
        "AML, NOS"
    }
    if classification in convertible:
        if blasts_percentage < 10:
            classification = "Not AML, consider MDS classification"
            derivation.append("Blasts <10 => final classification: Not AML, consider MDS classification")
        elif 10 <= blasts_percentage < 20:
            new_class = classification.replace("AML", "MDS/AML", 1)
            derivation.append("Blasts 10–19 => replaced 'AML' with 'MDS/AML'. Final classification: " + new_class)
            classification = new_class
        else:
            derivation.append("Blasts >=20 => remain AML")
    else:
        if blasts_percentage < 10:
            classification = "Not AML, consider MDS classification"
            derivation.append("Blasts <10 => final classification: Not AML, consider MDS classification")

    # STEP 6: Append Qualifiers
    q_list = []
    # For ICC, we read the therapy value from "previous_cytotoxic_therapy"
    therapy = qualifiers.get("previous_cytotoxic_therapy", "None")
    icc_accepted = ["Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions", "Any combination"]
    if therapy in icc_accepted:
        q_list.append("therapy related")
        derivation.append(f"Detected ICC therapy => therapy related: {therapy}")

    # Germline predisposition => "in the setting of"
    germ_v = qualifiers.get("predisposing_germline_variant", "").strip()
    if germ_v.lower() not in ["", "none"]:
        raw = [i.strip() for i in germ_v.split(",") if i.strip()]
        no_brackets = [r.split(" (")[0] for r in raw]
        # Exclude "germline blm mutation" for ICC
        no_blm = [x for x in no_brackets if x.lower() != "germline blm mutation"]
        if no_blm:
            phrase = "in the setting of " + ", ".join(no_blm)
            q_list.append(phrase)
            derivation.append("Qualifier => " + phrase)
    else:
        derivation.append("No germline predisposition indicated (review at MDT)")

    # NEW: check if "previous_MDS_diagnosed_over_3_months_ago" or "previous_MDS/MPN_diagnosed_over_3_months_ago" is True
    progressed_from_mds = (
        qualifiers.get("previous_MDS_diagnosed_over_3_months_ago", False)
        or qualifiers.get("previous_MDS/MPN_diagnosed_over_3_months_ago", False)
    )
    if progressed_from_mds:
        q_list.append("arising post MDS")
        derivation.append("Either previous_MDS or previous_MDS/MPN => 'arising post MDS'")

    if q_list and "Not AML" not in classification:
        classification += ", " + ", ".join(q_list) + " (ICC 2022)"
        derivation.append("Qualifiers appended => " + classification)
    else:
        if "Not AML" not in classification:
            classification += " (ICC 2022)"
        derivation.append("Final => " + classification)

    return classification, derivation



