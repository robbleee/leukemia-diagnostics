import json

def classify_MDS_WHO2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS based on WHO 2022 criteria including qualifiers.

    Returns:
      - classification (str)
      - derivation (list of str) describing logic steps
    """
    derivation = []
    # Default classification (without suffix)
    classification = "MDS, unclassifiable"
    derivation.append(f"Default classification set to: {classification}")

    # Step 1: Biallelic TP53 inactivation
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    cond1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    cond2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    cond3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
    derivation.append(f"Checking for biallelic TP53: {biallelic_tp53}")
    if cond1 or cond2 or cond3:
        classification = "MDS with biallelic TP53 inactivation"
        derivation.append("Biallelic TP53 detected => " + classification)
        return classification + " (WHO 2022)", derivation

    # Step 2: Blasts percentage & fibrotic status
    blasts = parsed_data.get("blasts_percentage", None)
    fibrotic = parsed_data.get("fibrotic", False)
    derivation.append(f"Retrieved blasts: {blasts}, fibrotic: {fibrotic}")
    if blasts is not None:
        if 5 <= blasts <= 9:
            classification = "MDS with increased blasts 1"
            derivation.append("5-9% blasts => " + classification)
        if 10 <= blasts <= 19:
            classification = "MDS with increased blasts 2"
            derivation.append("10-19% blasts => " + classification)
        if 5 <= blasts <= 19 and fibrotic:
            classification = "MDS, fibrotic"
            derivation.append("Blasts 5-19% with fibrotic marrow => " + classification)
    else:
        derivation.append("No blasts_percentage provided; skipping blast-based classification.")

    if "increased blasts" in classification or "fibrotic" in classification:
        derivation.append(f"Current classification: {classification}")

    # Step 3: SF3B1 mutation
    if classification == "MDS, unclassifiable":
        sf3b1 = parsed_data.get("MDS_related_mutation", {}).get("SF3B1", False)
        if sf3b1:
            classification = "MDS with low blasts and SF3B1"
            derivation.append("SF3B1 mutation detected => " + classification)

    # Step 4: del(5q)
    if classification == "MDS, unclassifiable":
        cytogen = parsed_data.get("MDS_related_cytogenetics", {})
        if cytogen.get("del_5q", False):
            classification = "MDS with low blasts and isolated 5q-"
            derivation.append("del(5q) detected => " + classification)

    # Step 5: Hypoplasia
    if classification == "MDS, unclassifiable":
        if parsed_data.get("hypoplasia", False):
            classification = "MDS, hypoplastic"
            derivation.append("Hypoplasia detected => " + classification)

    # Step 6: Dysplastic lineages
    if classification == "MDS, unclassifiable":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        if lineages is not None:
            if lineages == 1:
                classification = "MDS with low blasts"
                derivation.append("Single dysplastic lineage => " + classification)
            elif lineages > 1:
                classification = "MDS with low blasts"
                derivation.append("Multiple dysplastic lineages => " + classification)

    # Step 7: Append Qualifiers
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_list = []

    # For MDS WHO, use field "post_cytotoxic_therapy".
    therapy = qualifiers.get("post_cytotoxic_therapy", "None")
    who_accepted = ["Ionising radiation", "Cytotoxic chemotherapy", "Any combination"]
    if therapy in who_accepted:
        qualifier_list.append("post cytotoxic therapy")
        derivation.append(f"Detected WHO therapy => post cytotoxic therapy: {therapy}")
    # If therapy is "Immune interventions" (or not accepted), we add nothing for WHO.

    # Germline predisposition (WHO uses "associated with")
    germline_variant = qualifiers.get("predisposing_germline_variant")
    if germline_variant and germline_variant.strip().lower() != "none":
        raw_variants = [v.strip() for v in germline_variant.split(",") if v.strip()]
        filtered_variants = [v.split(" (")[0] for v in raw_variants]
        # Exclude Diamond-Blackfan anemia for WHO
        filtered_variants = [v for v in filtered_variants if v.lower() != "diamond-blackfan anemia"]
        if filtered_variants:
            qualifier_list.append("associated with " + ", ".join(filtered_variants))
            derivation.append("Detected germline predisposition => associated with " + ", ".join(filtered_variants))
    else:
        derivation.append("No germline predisposition indicated (review at MDT)")

    if qualifier_list:
        classification += ", " + ", ".join(qualifier_list)
        derivation.append("Classification with qualifiers: " + classification)

    classification += " (WHO 2022)"
    derivation.append("Final classification => " + classification)
    return classification, derivation


def classify_MDS_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS subtypes based on ICC 2022 criteria.

    Returns:
      - classification (str)
      - derivation (list of str) describing logic steps
    """
    derivation = []
    classification = "MDS, NOS"  # default without suffix
    derivation.append(f"Default classification set to: {classification}")

    # Step 1: Biallelic TP53 inactivation
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    cond1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    cond2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    cond3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
    if cond1 or cond2 or cond3:
        classification = "MDS with mutated TP53"
        derivation.append("Biallelic TP53 detected => " + classification)
        return classification + " (ICC 2022)", derivation

    # Step 2: Blasts percentage & fibrotic status
    blasts = parsed_data.get("blasts_percentage", None)
    derivation.append(f"blasts_percentage: {blasts}")
    if blasts is not None:
        if 5 <= blasts <= 9:
            classification = "MDS with excess blasts"
            derivation.append("5-9% blasts => " + classification)
        elif 10 <= blasts <= 19:
            classification = "MDS/AML"
            derivation.append("10-19% blasts => " + classification)

    # Step 3: SF3B1 mutation
    if classification == "MDS, NOS":
        if parsed_data.get("MDS_related_mutation", {}).get("SF3B1", False):
            classification = "MDS with mutated SF3B1"
            derivation.append("SF3B1 mutation detected => " + classification)

    # Step 4: del(5q)
    if classification == "MDS, NOS":
        if parsed_data.get("MDS_related_cytogenetics", {}).get("del_5q", False):
            classification = "MDS with del(5q)"
            derivation.append("del(5q) detected => " + classification)

    # Step 5: Dysplastic lineages
    if classification == "MDS, NOS":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        derivation.append(f"number_of_dysplastic_lineages: {lineages}")
        if lineages == 1:
            classification = "MDS, NOS with single lineage dysplasia"
            derivation.append("Single lineage dysplasia => " + classification)
        elif lineages is not None and lineages > 1:
            classification = "MDS, NOS with multilineage dysplasia"
            derivation.append("Multilineage dysplasia => " + classification)

    # Step 6: Check for monosomy_7 or complex karyotype if still NOS.
    if classification == "MDS, NOS":
        cytogen = parsed_data.get("MDS_related_cytogenetics", {})
        if cytogen.get("monosomy_7", False) or cytogen.get("complex_karyotype", False):
            classification = "MDS, NOS without dysplasia"
            derivation.append("Monosomy 7 or complex karyotype detected => " + classification)

    # Step 7: Append Qualifiers
    qualifier_list = []
    qualifiers = parsed_data.get("qualifiers", {})

    # For ICC, use field "post_cytotoxic_therapy" (ICC accepts: Ionising radiation, Cytotoxic chemotherapy, Immune interventions, Any combination)
    therapy = qualifiers.get("post_cytotoxic_therapy", "None")
    icc_accepted = ["Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions", "Any combination"]
    if therapy in icc_accepted:
        qualifier_list.append("therapy related")
        derivation.append(f"Detected ICC therapy => therapy related: {therapy}")

    # Germline predisposition for ICC uses "in the setting of"
    germline_variant = qualifiers.get("predisposing_germline_variant", "").strip()
    if germline_variant and germline_variant.lower() not in ["", "none"]:
        raw_variants = [v.strip() for v in germline_variant.split(",") if v.strip()]
        no_bracket = [v.split(" (")[0] for v in raw_variants]
        # Exclude "germline BLM mutation" for ICC
        final_variants = [v for v in no_bracket if v.lower() != "germline blm mutation"]
        if final_variants:
            phrase = "in the setting of " + ", ".join(final_variants)
            qualifier_list.append(phrase)
            derivation.append("Qualifier => " + phrase)
    else:
        derivation.append("No germline predisposition indicated (review at MDT)")

    if qualifier_list and "Not AML" not in classification:
        classification += ", " + ", ".join(qualifier_list)
        derivation.append("Classification with qualifiers => " + classification)

    classification += " (ICC 2022)"
    derivation.append("Final classification => " + classification)

    return classification, derivation
