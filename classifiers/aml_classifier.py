import json


##############################
# CLASSIFY AML WHO 2022
##############################
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
    
    classification = "Acute myeloid leukaemia, [define by differentiation]"
    derivation.append(f"Initial classification set to: {classification}")

    # -----------------------------
    # STEP 1: AML-Defining Recurrent Genetic Abnormalities (WHO)
    # -----------------------------
    aml_genetic_abnormalities_map = {
        "NPM1": "AML with NPM1 mutation",
        "RUNX1::RUNX1T1": "AML with RUNX1::RUNX1T1 fusion",
        "CBFB::MYH11": "AML with CBFB::MYH11 fusion",
        "DEK::NUP214": "AML with DEK::NUP214 fusion",
        "RBM15::MRTFA": "AML with RBM15::MRTFA fusion",
        "MLLT3::KMT2A": "AML with KMT2A rearrangement",
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
    else:
        # Attempt classification based on AML-defining genetic abnormalities
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
            else:
                if aml_def_genetic.get(gene, False):
                    classification = classif
                    derivation.append(
                        f"{gene} abnormality detected. Classification => {classification}"
                    )
                    updated = True
                    break

        if not updated:
            derivation.append("No WHO AML-defining abnormality met final requirements (e.g. blasts threshold).")

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
    # STEP 4: Add Qualifiers
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
    # STEP 5: Replace "[define by differentiation]" if needed
    # -----------------------------
    if classification.strip() == "Acute myeloid leukaemia, [define by differentiation]":
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

        if aml_diff and aml_diff in FAB_TO_WHO_MAPPING:
            classification = FAB_TO_WHO_MAPPING[aml_diff]
            derivation.append(f"Classification updated using FAB-to-WHO mapping => {classification}")
        else:
            classification = "Acute myeloid leukaemia, unknown differentiation"
            derivation.append("AML_differentiation is invalid or missing => 'unknown differentiation'.")

    # Append "(WHO 2022)" if not already present
    if "(WHO 2022)" not in classification:
        classification += " (WHO 2022)"
        derivation.append(f"Final classification => {classification}")

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
            classification (str): The final AML classification according to ICC 2022
            derivation (list): A list capturing the step-by-step logic used
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

    classification = "AML, NOS"
    derivation.append(f"Initial classification set to: {classification}")

    # Gather fields relevant to ICC classification
    aml_def_genetic = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    mds_related_mutations = parsed_data.get("MDS_related_mutation", {})
    mds_related_cytogenetics = parsed_data.get("MDS_related_cytogenetics", {})
    qualifiers = parsed_data.get("qualifiers", {})

    # -----------------------------
    # STEP 1: AML-defining Recurrent Genetic Abnormalities (ICC)
    # -----------------------------
    aml_genetic_abnormalities_map = {
        "NPM1": "AML with mutated NPM1",
        "RUNX1::RUNX1T1": "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1",
        "CBFB::MYH11": "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11",
        "DEK::NUP214": "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214",
        "RBM15::MRTFA": "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTF1",
        "MLLT3::KMT2A": "AML with t(9;11)(p21.3;q23.3)/MLLT3::KMT2A",
        "KMT2A": "AML with other KMT2A rearrangements",
        "MECOM": "AML with other MECOM rearrangements",
        "NUP98": "AML with NUP98 and other partners",
        "bZIP": "AML with in-frame bZIP CEBPA mutations",
        "BCR::ABL1": "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1"
    }

    true_aml_genes = [gene for gene, val in aml_def_genetic.items() if val is True]
    if not true_aml_genes:
        derivation.append("All ICC AML-defining genetic abnormality flags are false.")
    else:
        derivation.append(f"Detected ICC AML-defining flags: {', '.join(true_aml_genes)}")
        updated = False
        for gene, classif in aml_genetic_abnormalities_map.items():
            if aml_def_genetic.get(gene, False):
                if blasts_percentage >= 10.0:
                    classification = classif
                    derivation.append(f"{gene} abnormality meets blasts >=10%. Classification => {classification}")
                    updated = True
                    break
        if not updated:
            derivation.append("No ICC AML-defining abnormality met the blasts >=10% criterion.")

    # -----------------------------
    # STEP 2: Biallelic TP53
    # -----------------------------
    if classification == "AML, NOS":
        conditions = [
            biallelic_tp53.get("2_x_TP53_mutations", False),
            biallelic_tp53.get("1_x_TP53_mutation_del_17p", False),
            biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
        ]
        if any(conditions):
            classification = "AML with mutated TP53"
            derivation.append("Biallelic TP53 mutation condition met => AML with mutated TP53")
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
                f"MDS-related mutation(s): {', '.join(true_mds_mutations)} => {classification}"
            )
        else:
            derivation.append("All MDS-related gene mutation flags are false.")

    # -----------------------------
    # STEP 4: MDS-related Cytogenetics
    # -----------------------------
    if classification == "AML, NOS":
        # Define relevant cytogenetic abnormalities for ICC
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
                f"MDS-related cytogenetic abnormality(ies): {', '.join(true_cytogenetics)} => {classification}"
            )
        else:
            derivation.append("All MDS-related cytogenetic flags are false.")

    # -----------------------------
    # STEP 5: Qualifiers
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

    if qualifier_descriptions:
        qualifiers_str = ", ".join(qualifier_descriptions)
        classification += f", {qualifiers_str} (ICC 2022)"
        derivation.append(f"Qualifiers appended => {classification}")
    else:
        classification += " (ICC 2022)"
        derivation.append(f"Final classification => {classification}")

    return classification, derivation

