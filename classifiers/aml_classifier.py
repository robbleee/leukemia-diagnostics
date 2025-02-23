import json


##############################
# CLASSIFY AML WHO 2022
##############################
def classify_AML_WHO2022(parsed_data: dict, not_erythroid: bool = False) -> tuple:
    """
    Classifies AML subtypes based on the WHO 2022 criteria, including qualifiers.
    If the final classification is "Acute myeloid leukaemia, [define by differentiation]",
    we attempt to insert AML_differentiation from parsed_data if available.
    
    An optional parameter 'not_erythroid' (boolean) may be provided.
    If set to True, then even if AML_differentiation is "M6a" or "M6b", the
    classification will not be overridden to an erythroid subtype.
    
    Args:
        parsed_data (dict): A dictionary containing extracted hematological report data.
        not_erythroid (bool): If True, prevents overriding classification with erythroid subtype.
    
    Returns:
        tuple: 
            classification (str): The final AML classification according to WHO 2022.
            derivation (list): A list capturing the step-by-step logic used.
    """
    derivation = []

    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")

    # Validate blasts_percentage
    if blasts_percentage is None:
        derivation.append("Error: blasts_percentage is missing. Classification cannot proceed.")
        return (
            "Error: blasts_percentage is missing. Please provide this information for classification.",
            derivation,
        )
    if not isinstance(blasts_percentage, (int, float)) or not (0.0 <= blasts_percentage <= 100.0):
        derivation.append("Error: blasts_percentage must be a number between 0 and 100.")
        return (
            "Error: blasts_percentage must be a number between 0 and 100.",
            derivation,
        )

    classification = "Acute myeloid leukaemia, [define by differentiation]"
    derivation.append(f"Default classification set to: {classification}")

    # -----------------------------
    # STEP 1: AML-Defining Recurrent Genetic Abnormalities (WHO)
    # -----------------------------
    aml_genetic_abnormalities_map = {
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
        "CEBPA": "AML with CEBPA mutation",  # Needs blasts >= 20%
        "bZIP": "AML with CEBPA mutation",   # Needs blasts >= 20%
        "BCR::ABL1": "AML with BCR::ABL1 fusion"  # Needs blasts >= 20%
    }

    aml_def_genetic = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    true_aml_genes = [gene for gene, val in aml_def_genetic.items() if val is True]

    if not true_aml_genes:
        derivation.append("All AML-defining recurrent genetic abnormality flags are false.")
        if blasts_percentage < 20.0:
            classification = "Not AML, consider MDS classification"
            derivation.append("No AML defining abnormalities and blasts < 20% => 'Consider reclassification as MDS'.")
    else:
        derivation.append(f"Detected AML-defining abnormality flags: {', '.join(true_aml_genes)}")
        updated = False
        for gene, classif in aml_genetic_abnormalities_map.items():
            if gene in ["CEBPA", "bZIP", "BCR::ABL1"]:
                # For these, require blasts >= 20%
                if aml_def_genetic.get(gene, False) and blasts_percentage >= 20.0:
                    classification = classif
                    derivation.append(
                        f"{gene} abnormality meets blasts >=20%. Classification => {classification}"
                    )
                    updated = True
                    break
            elif gene in [
                "PML::RARA", "NPM1", "RUNX1::RUNX1T1", "CBFB::MYH11",
                "DEK::NUP214", "RBM15::MRTFA", "MLLT3::KMT2A",
                "GATA2:: MECOM", "KMT2A", "MECOM", "NUP98"
            ]:
                # Removed the blasts > 5% requirement for these abnormalities.
                if aml_def_genetic.get(gene, False):
                    classification = classif
                    derivation.append(
                        f"{gene} abnormality detected (blasts_percentage: {blasts_percentage}). Classification => {classification}"
                    )
                    updated = True
                    break
            else:
                if aml_def_genetic.get(gene, False):
                    classification = classif
                    derivation.append(
                        f"{gene} abnormality detected. Classification => {classification}"
                    )
                    updated = True
                    break

        if not updated:
            derivation.append("No WHO AML-defining abnormality met final requirements.")
            if blasts_percentage < 20.0:
                classification = "Not AML, consider MDS classification"
                derivation.append("No AML defining abnormalities and blasts < 20% => 'Consider reclassification as MDS'.")

    # -----------------------------
    # STEP 2: MDS-Related Mutations
    # -----------------------------
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_related_mutations = parsed_data.get("MDS_related_mutation", {})
        true_mds_mutations = [gene for gene, val in mds_related_mutations.items() if val is True]
        if true_mds_mutations:
            classification = "AML, myelodysplasia related"
            derivation.append(f"MDS-related mutation(s): {', '.join(true_mds_mutations)} => {classification}")
        else:
            derivation.append("All MDS-related mutation flags are false.")

    # -----------------------------
    # STEP 3: MDS-Related Cytogenetics
    # -----------------------------
    if classification == "Acute myeloid leukaemia, [define by differentiation]":
        mds_related_cytogenetics = parsed_data.get("MDS_related_cytogenetics", {})
        true_mds_cytos = [abn for abn, val in mds_related_cytogenetics.items() if val is True]
        if true_mds_cytos:
            classification = "AML, myelodysplasia related"
            derivation.append(
                f"MDS-related cytogenetic abnormality(ies): {', '.join(true_mds_cytos)} => {classification}"
            )
        else:
            derivation.append("All MDS-related cytogenetic flags are false.")

    # -----------------------------
    # STEP 5: Update using AML_differentiation (with Override for Erythroid)
    # -----------------------------
    aml_diff = parsed_data.get("AML_differentiation")
    if aml_diff:
        derivation.append(f"AML_differentiation provided: {aml_diff}")
    else:
        derivation.append("No AML_differentiation provided.")

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

    # New override logic:
    # - Erythroid differentiation (M6a/M6b) should override if current classification is default 
    #   or "Not AML, consider MDS classification" UNLESS not_erythroid is True.
    # - Other differentiations can only override the default classification.
    if ("define by differentiation" in classification) or ("Not AML" in classification):
        if aml_diff:
            if aml_diff in ["M6a", "M6b"]:
                if not not_erythroid:
                    classification = "Acute Erythroid leukemia"
                    derivation.append(f"Erythroid subtype ({aml_diff}) detected; overriding classification to {classification}")
                else:
                    derivation.append("not_erythroid flag is True; erythroid override skipped.")
            elif classification.strip() == "Acute myeloid leukaemia, [define by differentiation]" and aml_diff in FAB_TO_WHO_MAPPING:
                classification = FAB_TO_WHO_MAPPING[aml_diff]
                derivation.append(f"Classification updated using FAB-to-WHO mapping => {classification}")
            elif classification.strip() == "Acute myeloid leukaemia, [define by differentiation]":
                classification = "Acute myeloid leukaemia, unknown differentiation"
                derivation.append("AML_differentiation is invalid or missing => 'Acute myeloid leukaemia, unknown differentiation'.")
            # If classification is "Not AML, consider MDS classification" and AML_differentiation is non-erythroid, do not override.
    else:
        derivation.append("AML_differentiation provided but classification already determined; no override.")

    # -----------------------------
    # STEP 4 (Moved): Append Qualifiers
    # -----------------------------
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_descriptions = []

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_descriptions.append("post cytotoxic therapy")
        derivation.append("Detected qualifier: post cytotoxic therapy")

    germline_variant = qualifiers.get("predisposing_germline_variant", "None")
    if germline_variant and germline_variant.lower() != "none":
        qualifier_descriptions.append(f"associated with germline {germline_variant}")
        derivation.append(f"Detected qualifier: germline variant = {germline_variant}")

    if qualifier_descriptions:
        classification += f", {', '.join(qualifier_descriptions)}"
        derivation.append(f"Qualifiers appended => {classification}")

    # -----------------------------
    # Append WHO 2022 suffix if applicable
    # -----------------------------
    if "Not AML" not in classification:
        classification += " (WHO 2022)"
    derivation.append(f"Final classification => {classification}")

    return classification, derivation


##############################
# CLASSIFY MDS WHO 2022
##############################
def classify_MDS_WHO2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS based on the WHO 2022 criteria you provided.
    Returns:
      - classification (str)
      - derivation (list of str) describing logic steps
    """
    derivation = []
    classification = "MDS, unclassifiable (WHO 2022)"  # default fallback

    # Step 1: Biallelic TP53 inactivation
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    condition1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    condition2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    condition3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)

    derivation.append(f"Checking for biallelic TP53: {biallelic_tp53}")

    if condition1 or condition2 or condition3:
        classification = "MDS with biallelic TP53 inactivation (WHO 2022)"
        derivation.append("Classification => MDS with biallelic TP53 inactivation")
        # Return immediately if you want this to take precedence
        return classification, derivation

    # Step 2: Check blasts percentage & fibrotic
    blasts = parsed_data.get("blasts_percentage", None)
    fibrotic = parsed_data.get("fibrotic", False)

    derivation.append(f"Retrieved blasts_percentage: {blasts}, fibrotic: {fibrotic}")
    if blasts is not None:
        # TBC: Does fibrotic take precedence?
        # The logic below checks blasts first, but if fibrotic takes precedence,
        # you could reorder the if-statements. For now, we use the logic as provided.

        if 5 <= blasts <= 9:
            # 5-9%
            classification = "MDS with increased blasts 1 (WHO 2022)"
            derivation.append("5-9% blasts => MDS with increased blasts 1")
        if 10 <= blasts <= 19:
            # 10-19%
            classification = "MDS with increased blasts 2 (WHO 2022)"
            derivation.append("10-19% blasts => MDS with increased blasts 2")
        if 5 <= blasts <= 19 and fibrotic:
            classification = "MDS, fibrotic (WHO 2022)"
            derivation.append("5-19% blasts + fibrotic => MDS, fibrotic")
    else:
        derivation.append("No blasts_percentage provided; skipping blasts-based classification.")

    # If we already assigned an "increased blasts" classification, no further steps needed
    if "increased blasts" in classification or "fibrotic" in classification:
        # Check if classification changed above
        # We do not return immediately in case there's a nuance in your real logic
        derivation.append(f"Current classification is: {classification}")

    # Step 3: SF3B1
    if classification == "MDS, unclassifiable (WHO 2022)":
        sf3b1 = parsed_data.get("MDS_related_mutation", {}).get("SF3B1", False)
        if sf3b1:
            classification = "MDS with low blasts and SF3B1 (WHO 2022)"
            derivation.append("SF3B1 mutation => MDS with low blasts and SF3B1")

    # Step 4: del(5q)
    if classification == "MDS, unclassifiable (WHO 2022)":
        cytogen = parsed_data.get("MDS_related_cytogenetics", {})
        if cytogen.get("del_5q", False):
            classification = "MDS with low blasts and isolated 5q- (WHO 2022)"
            derivation.append("del(5q) => MDS with low blasts and isolated 5q-")

    # Step 5: Hypoplasia
    if classification == "MDS, unclassifiable (WHO 2022)":
        if parsed_data.get("hypoplasia", False):
            classification = "MDS, hypoplastic (WHO 2022)"
            derivation.append("Hypoplasia => MDS, hypoplastic")

    # Step 6: Dysplastic lineages
    if classification == "MDS, unclassifiable (WHO 2022)":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        if lineages is not None:
            if lineages == 1:
                classification = "MDS with low blasts (WHO 2022)" 
                derivation.append("1 dysplastic lineage => MDS with low blasts")
            elif lineages > 1:
                classification = "MDS with low blasts (WHO 2022)"
                derivation.append(">1 dysplastic lineages => MDS with low blasts")

    # Step 7: Qualifiers
    # "previous_cytotoxic_therapy" => post cytotoxic therapy
    # "predisposing_germline_variant" => associated with germline ...
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_list = []

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_list.append("post cytotoxic therapy")
        derivation.append("Qualifier: post cytotoxic therapy")

    germline_variant = qualifiers.get("predisposing_germline_variant")
    if germline_variant and str(germline_variant).lower() != "none":
        qualifier_list.append(f"associated with germline {germline_variant}")
        derivation.append(f"Qualifier: associated with germline {germline_variant}")

    # Append any qualifiers to classification
    if qualifier_list:
        classification += f", {', '.join(qualifier_list)}"
        derivation.append(f"Final classification with qualifiers => {classification}")

    # Ensure we have at least the default WHO label
    if "(WHO 2022)" not in classification:
        classification += " (WHO 2022)"

    return classification, derivation




##############################
# CLASSIFY AML ICC 2022
##############################
def classify_AML_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies AML subtypes based on the ICC 2022 criteria, including qualifiers.

    Args:
        parsed_data (dict): A dictionary containing extracted hematological report data.

    Returns:
        tuple:
            classification (str): The final classification according to ICC 2022.
            derivation (list): A list capturing the step-by-step logic used.
    """
    derivation = []

    blasts_percentage = parsed_data.get("blasts_percentage")
    derivation.append(f"Retrieved blasts_percentage: {blasts_percentage}")

    # Validate blasts_percentage
    if blasts_percentage is None:
        derivation.append("Error: `blasts_percentage` is missing. Classification cannot proceed.")
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

    # Default classification
    classification = "AML, NOS"
    derivation.append(f"Default classification set to: {classification}")

    # Gather fields relevant to ICC classification
    aml_def_genetic = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    mds_related_mutations = parsed_data.get("MDS_related_mutation", {})
    mds_related_cytogenetics = parsed_data.get("MDS_related_cytogenetics", {})
    qualifiers = parsed_data.get("qualifiers", {})

    # -----------------------------
    # STEP 1: AML-defining Recurrent Genetic Abnormalities (ICC)
    # -----------------------------
    # Updated mapping to include both common and uncommon genetic abnormalities:
    aml_genetic_abnormalities_map = {
        # Main set (common)
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
        # Uncommon recurring translocations involving RARA (infrequent forms, group 1)
        "IRF2BP2::RARA": "APL with t(1;17)(q42.3;q21.2)/IRF2BP2::RARA",
        "NPM1::RARA": "APL with t(5;17)(q35.1;q21.2)/NPM1::RARA",
        "ZBTB16::RARA": "APL with t(11;17)(q23.2;q21.2)/ZBTB16::RARA",
        "STAT5B::RARA": "APL with cryptic inv(17) or del(17)(q21.2q21.2)/STAT5B::RARA",
        "STAT3::RARA": "APL with cryptic inv(17) or del(17)(q21.2q21.2)/STAT3::RARA",
        "RARA::TBL1XR1": "APL with RARA::TBL1XR1 (rare rearrangement)",
        "RARA::FIP1L1": "APL with RARA::FIP1L1 (rare rearrangement)",
        "RARA::BCOR": "APL with RARA::BCOR (rare rearrangement)",
        # Uncommon recurring translocations involving KMT2A (infrequent forms, group 2)
        "AFF1::KMT2A": "AML with t(4;11)(q21.3;q23.3)/AFF1::KMT2A",
        "AFDN::KMT2A": "AML with t(6;11)(q27;q23.3)/AFDN::KMT2A",
        "MLLT10::KMT2A": "AML with t(10;11)(p12.3;q23.3)/MLLT10::KMT2A",
        "TET1::KMT2A": "AML with t(10;11)(q21.3;q23.3)/TET1::KMT2A",
        "KMT2A::ELL": "AML with t(11;19)(q23.3;p13.1)/KMT2A::ELL",
        "KMT2A::MLLT1": "AML with t(11;19)(q23.3;p13.3)/KMT2A::MLLT1",
        # Uncommon recurring translocations involving MECOM (infrequent forms, group 3)
        "MYC::MECOM": "AML with t(3;8)(q26.2;q24.2)/MYC::MECOM",
        "ETV6::MECOM": "AML with t(3;12)(q26.2;p13.2)/ETV6::MECOM",
        "MECOM::RUNX1": "AML with t(3;21)(q26.2;q22.1)/MECOM::RUNX1",
        # Rare recurring translocations (group 4)
        "PRDM16::RPN1": "AML with t(1;3)(p36.3;q21.3)/PRDM16::RPN1",
        "NPM1::MLF1": "AML with t(3;5)(q25.3;q35.1)/NPM1::MLF1",
        "NUP98::NSD1": "AML with t(5;11)(q35.2;p15.4)/NUP98::NSD1",
        "ETV6::MNX1": "AML with t(7;12)(q36.3;p13.2)/ETV6::MNX1",
        "KAT6A::CREBBP": "AML with t(8;16)(p11.2;p13.3)/KAT6A::CREBBP",
        "PICALM::MLLT10": "AML with t(10;11)(p12.3;q14.2)/PICALM::MLLT10",
        "NUP98::KMD5A": "AML with t(11;12)(p15.4;p13.3)/NUP98::KMD5A",
        "FUS::ERG": "AML with t(16;21)(p11.2;q22.2)/FUS::ERG",
        "RUNX1::CBFA2T3": "AML with t(16;21)(q24.3;q22.1)/RUNX1::CBFA2T3",
        "CBFA2T3::GLIS2": "AML with inv(16)(p13.3q24.3)/CBFA2T3::GLIS2",
    }

    # Check if any of the ICC AML-defining genetic abnormalities are present
    true_aml_genes = [gene for gene, val in aml_def_genetic.items() if val is True]
    if true_aml_genes:
        derivation.append(f"Detected ICC AML-defining flags: {', '.join(true_aml_genes)}")
        updated = False
        for gene, classif in aml_genetic_abnormalities_map.items():
            if aml_def_genetic.get(gene, False):
                # For ICC 2022, if blasts >=10%, we typically consider AML.
                if blasts_percentage >= 10.0:
                    classification = classif
                    derivation.append(f"{gene} abnormality => provisional classification: {classification}")
                    updated = True
                    break
                else:
                    derivation.append(
                        f"Found {gene} abnormality, but blasts <10% => cannot label as AML at this stage"
                    )
        if not updated:
            derivation.append("No single ICC AML-defining abnormality triggered classification.")
    else:
        derivation.append("All ICC AML-defining genetic abnormality flags are false.")

    # -----------------------------
    # STEP 2: Biallelic TP53
    # -----------------------------
    if classification == "AML, NOS":
        conditions = [
            biallelic_tp53.get("2_x_TP53_mutations", False),
            biallelic_tp53.get("1_x_TP53_mutation_del_17p", False),
            biallelic_tp53.get("1_x_TP53_mutation_LOH", False),
            biallelic_tp53.get("1_x_TP53_mutation_10_percent_vaf", False)
        ]
        if any(conditions):
            classification = "AML with mutated TP53"
            derivation.append("Biallelic TP53 mutation condition met => provisional classification: AML with mutated TP53")
        else:
            derivation.append("All biallelic TP53 mutation flags are false.")

    # -----------------------------
    # STEP 3: MDS-related Mutations
    # -----------------------------
    if classification == "AML, NOS":
        true_mds_mutations = [gene for gene, val in mds_related_mutations.items() if val is True]
        if true_mds_mutations:
            classification = "AML with myelodysplasia related gene mutation"
            derivation.append(
                f"MDS-related mutation(s): {', '.join(true_mds_mutations)} => provisional classification: {classification}"
            )
        else:
            derivation.append("All MDS-related gene mutation flags are false.")

    # -----------------------------
    # STEP 4: MDS-related Cytogenetics
    # -----------------------------
    if classification == "AML, NOS":
        mrd_cytogenetics = [
            "Complex_karyotype", "del_5q", "t_5q", "add_5q", "-7", "del_7q",
            "del_12p", "t_12p", "add_12p", "i_17q", "idic_X_q13"
        ]
        nos_cytogenetics = [
            "5q", "+8", "del_11q", "12p", "-13",
            "-17", "add_17p", "del_20q"
        ]
        all_cytogenetics = mrd_cytogenetics + nos_cytogenetics

        true_cytogenetics = [
            abn for abn, val in mds_related_cytogenetics.items()
            if val is True and abn in all_cytogenetics
        ]
        if true_cytogenetics:
            classification = "AML with myelodysplasia related cytogenetic abnormality"
            derivation.append(
                f"MDS-related cytogenetic abnormality(ies): {', '.join(true_cytogenetics)} => provisional classification: {classification}"
            )
        else:
            derivation.append("All MDS-related cytogenetic flags are false.")

    # -----------------------------
    # STEP 5: Final Blast-Count Check (AML vs MDS/AML vs Not AML)
    # -----------------------------
    convertible_subtypes = {
        "AML with mutated TP53",
        "AML with myelodysplasia related gene mutation",
        "AML with myelodysplasia related cytogenetic abnormality",
        "AML, NOS"
    }

    if classification in convertible_subtypes:
        if blasts_percentage < 10.0:
            classification = "Not AML, consider MDS classification"
            derivation.append("Blasts <10% => final classification: Not AML, consider MDS classification")
        elif 10.0 <= blasts_percentage < 20.0:
            new_classification = classification.replace("AML", "MDS/AML", 1)
            derivation.append(
                "Blasts 10–19% => replaced 'AML' with 'MDS/AML'. Final classification: "
                f"{new_classification}"
            )
            classification = new_classification
        else:
            derivation.append("Blasts >=20% => remain AML.")
    else:
        if blasts_percentage < 10.0:
            classification = "Not AML, consider MDS classification"
            derivation.append("Blasts <10% => final classification: Not AML, consider MDS classification")

    # -----------------------------
    # STEP 6: Qualifiers
    # -----------------------------
    qualifier_descriptions = []

    if qualifiers.get("previous_MDS_diagnosed_over_3_months_ago", False):
        qualifier_descriptions.append("post MDS")
        derivation.append("Detected qualifier: post MDS")

    if qualifiers.get("previous_MDS/MPN_diagnosed_over_3_months_ago", False):
        qualifier_descriptions.append("post MDS/MPN")
        derivation.append("Detected qualifier: post MDS/MPN")

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_descriptions.append("therapy related")
        derivation.append("Detected qualifier: therapy related")

    if qualifier_descriptions and "Not AML" not in classification:
        qualifiers_str = ", ".join(qualifier_descriptions)
        classification += f", {qualifiers_str} (ICC 2022)"
        derivation.append(f"Qualifiers appended => {classification}")
    else:
        if "Not AML" not in classification:
            classification += " (ICC 2022)"
        derivation.append(f"Final classification => {classification}")

    return classification, derivation



##############################
# CLASSIFY MDS ICC 2022
##############################
def classify_MDS_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS subtypes based on the ICC 2022 criteria you provided:
    
    1. Biallelic TP53 => 'MDS with mutated TP53 (ICC 2022)'
    2. Blasts:
        - 5-9% => 'MDS with excess blasts (ICC 2022)'
        - 10-19% => 'MDS/AML (ICC 2022)'
    3. SF3B1 => 'MDS with mutated SF3B1 (ICC 2022)'
    4. del(5q) => 'MDS with del(5q) (ICC 2022)'
    5. Dysplastic lineages:
        - =1 => 'MDS, NOS with single lineage dysplasia (ICC 2022)'
        - >1 => 'MDS, NOS with multilineage dysplasia (ICC 2022)'
    6. If (monosomy 7) OR (complex karyotype) => 'MDS, NOS without dysplasia (ICC 2022)'
    7. Qualifiers, if any.
    """
    derivation = []
    classification = "MDS, NOS (ICC 2022)"  # default

    # 1) Biallelic TP53
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    condition1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    condition2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    condition3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
    if condition1 or condition2 or condition3:
        classification = "MDS with mutated TP53 (ICC 2022)"
        derivation.append("Biallelic TP53 => MDS with mutated TP53")
        return classification, derivation

    # 2) Blasts
    blasts = parsed_data.get("blasts_percentage", None)
    if blasts is not None:
        if 5 <= blasts <= 9:
            classification = "MDS with excess blasts (ICC 2022)"
            derivation.append("5-9% blasts => MDS with excess blasts")
        elif 10 <= blasts <= 19:
            classification = "MDS/AML (ICC 2022)"
            derivation.append("10-19% blasts => MDS/AML")

    # 3) SF3B1
    if classification == "MDS, NOS (ICC 2022)":
        if parsed_data["MDS_related_mutation"].get("SF3B1", False):
            classification = "MDS with mutated SF3B1 (ICC 2022)"
            derivation.append("SF3B1 => MDS with mutated SF3B1")

    # 4) del(5q)
    if classification == "MDS, NOS (ICC 2022)":
        if parsed_data["MDS_related_cytogenetics"].get("del_5q", False):
            classification = "MDS with del(5q) (ICC 2022)"
            derivation.append("del(5q) => MDS with del(5q)")

    # 5) Dysplastic lineages
    if classification == "MDS, NOS (ICC 2022)":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        if lineages == 1:
            classification = "MDS, NOS with single lineage dysplasia (ICC 2022)"
            derivation.append("=> single lineage => MDS, NOS (single lineage)")
        elif (lineages is not None) and lineages > 1:
            classification = "MDS, NOS with multilineage dysplasia (ICC 2022)"
            derivation.append("=> multilineage => MDS, NOS (multilineage)")

    # 6) If still NOS, check monosomy_7 or complex karyotype
    if classification == "MDS, NOS (ICC 2022)":
        cytogen = parsed_data["MDS_related_cytogenetics"]
        if cytogen.get("monosomy_7", False) or cytogen.get("complex_karyotype", False):
            classification = "MDS, NOS without dysplasia (ICC 2022)"
            derivation.append("=> monosomy_7 or complex karyotype => MDS, NOS without dysplasia")

    # 7) Qualifiers
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_list = []

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_list.append("therapy related")
        derivation.append("Qualifier: therapy related")
    if qualifiers.get("predisposing_germline_variant"):
        germ = qualifiers["predisposing_germline_variant"]
        if germ.lower() != "none":
            qualifier_list.append(f"associated with germline {germ}")
            derivation.append(f"Qualifier: associated with germline {germ}")

    if qualifier_list:
        classification += f", {', '.join(qualifier_list)}"

    return classification, derivation


