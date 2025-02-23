import json
##############################
# CLASSIFY MDS WHO 2022
##############################
def classify_MDS_WHO2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS based on WHO 2022 criteria.
    Returns:
      - classification (str)
      - derivation (list of str) describing logic steps
    """
    derivation = []
    classification = "MDS, unclassifiable"  # default fallback without the designation

    # Step 1: Biallelic TP53 inactivation
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    condition1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    condition2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    condition3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)

    derivation.append(f"Checking for biallelic TP53: {biallelic_tp53}")

    if condition1 or condition2 or condition3:
        classification = "MDS with biallelic TP53 inactivation"
        derivation.append("Classification => MDS with biallelic TP53 inactivation")
        # Return immediately if you want this to take precedence
        classification = classification.strip() + " (WHO 2022)"
        return classification, derivation

    # Step 2: Check blasts percentage & fibrotic
    blasts = parsed_data.get("blasts_percentage", None)
    fibrotic = parsed_data.get("fibrotic", False)

    derivation.append(f"Retrieved blasts_percentage: {blasts}, fibrotic: {fibrotic}")
    if blasts is not None:
        if 5 <= blasts <= 9:
            classification = "MDS with increased blasts 1"
            derivation.append("5-9% blasts => MDS with increased blasts 1")
        if 10 <= blasts <= 19:
            classification = "MDS with increased blasts 2"
            derivation.append("10-19% blasts => MDS with increased blasts 2")
        if 5 <= blasts <= 19 and fibrotic:
            classification = "MDS, fibrotic"
            derivation.append("5-19% blasts + fibrotic => MDS, fibrotic")
    else:
        derivation.append("No blasts_percentage provided; skipping blasts-based classification.")

    if "increased blasts" in classification or "fibrotic" in classification:
        derivation.append(f"Current classification is: {classification}")

    # Step 3: SF3B1
    if classification == "MDS, unclassifiable":
        sf3b1 = parsed_data.get("MDS_related_mutation", {}).get("SF3B1", False)
        if sf3b1:
            classification = "MDS with low blasts and SF3B1"
            derivation.append("SF3B1 mutation => MDS with low blasts and SF3B1")

    # Step 4: del(5q)
    if classification == "MDS, unclassifiable":
        cytogen = parsed_data.get("MDS_related_cytogenetics", {})
        if cytogen.get("del_5q", False):
            classification = "MDS with low blasts and isolated 5q-"
            derivation.append("del(5q) => MDS with low blasts and isolated 5q-")

    # Step 5: Hypoplasia
    if classification == "MDS, unclassifiable":
        if parsed_data.get("hypoplasia", False):
            classification = "MDS, hypoplastic"
            derivation.append("Hypoplasia => MDS, hypoplastic")

    # Step 6: Dysplastic lineages
    if classification == "MDS, unclassifiable":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        if lineages is not None:
            if lineages == 1:
                classification = "MDS with low blasts"
                derivation.append("1 dysplastic lineage => MDS with low blasts")
            elif lineages > 1:
                classification = "MDS with low blasts"
                derivation.append(">1 dysplastic lineages => MDS with low blasts")

    # Step 7: Qualifiers
    qualifiers = parsed_data.get("qualifiers", {})
    qualifier_list = []

    if qualifiers.get("previous_cytotoxic_therapy", False):
        qualifier_list.append("post cytotoxic therapy")
        derivation.append("Qualifier: post cytotoxic therapy")

    germline_variant = qualifiers.get("predisposing_germline_variant")
    if germline_variant and str(germline_variant).lower() != "none":
        qualifier_list.append(f"associated with germline {germline_variant}")
        derivation.append(f"Qualifier: associated with germline {germline_variant}")

    if qualifier_list:
        classification += f", {', '.join(qualifier_list)}"
        derivation.append(f"Final classification with qualifiers => {classification}")

    # Ensure the designation appears only at the end.
    classification = classification.strip()
    if not classification.endswith("(WHO 2022)"):
        classification += " (WHO 2022)"

    return classification, derivation


##############################
# CLASSIFY MDS ICC 2022
##############################
def classify_MDS_ICC2022(parsed_data: dict) -> tuple:
    """
    Classifies MDS subtypes based on ICC 2022 criteria.
    Returns:
      - classification (str)
      - derivation (list of str) describing logic steps
    """
    derivation = []
    classification = "MDS, NOS"  # default fallback without the designation

    # 1) Biallelic TP53
    biallelic_tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    condition1 = biallelic_tp53.get("2_x_TP53_mutations", False)
    condition2 = biallelic_tp53.get("1_x_TP53_mutation_del_17p", False)
    condition3 = biallelic_tp53.get("1_x_TP53_mutation_LOH", False)
    if condition1 or condition2 or condition3:
        classification = "MDS with mutated TP53"
        derivation.append("Biallelic TP53 => MDS with mutated TP53")
        classification = classification.strip() + " (ICC 2022)"
        return classification, derivation

    # 2) Blasts
    blasts = parsed_data.get("blasts_percentage", None)
    if blasts is not None:
        if 5 <= blasts <= 9:
            classification = "MDS with excess blasts"
            derivation.append("5-9% blasts => MDS with excess blasts")
        elif 10 <= blasts <= 19:
            classification = "MDS/AML"
            derivation.append("10-19% blasts => MDS/AML")

    # 3) SF3B1
    if classification == "MDS, NOS":
        if parsed_data.get("MDS_related_mutation", {}).get("SF3B1", False):
            classification = "MDS with mutated SF3B1"
            derivation.append("SF3B1 mutation => MDS with mutated SF3B1")

    # 4) del(5q)
    if classification == "MDS, NOS":
        if parsed_data.get("MDS_related_cytogenetics", {}).get("del_5q", False):
            classification = "MDS with del(5q)"
            derivation.append("del(5q) => MDS with del(5q)")

    # 5) Dysplastic lineages
    if classification == "MDS, NOS":
        lineages = parsed_data.get("number_of_dysplastic_lineages", None)
        if lineages is not None:
            if lineages == 1:
                classification = "MDS, NOS with single lineage dysplasia"
                derivation.append("1 dysplastic lineage => single lineage dysplasia")
            elif lineages > 1:
                classification = "MDS, NOS with multilineage dysplasia"
                derivation.append(">1 dysplastic lineages => multilineage dysplasia")

    # 6) Check monosomy 7 or complex karyotype if still NOS.
    if classification == "MDS, NOS":
        cytogen = parsed_data.get("MDS_related_cytogenetics", {})
        if cytogen.get("monosomy_7", False) or cytogen.get("complex_karyotype", False):
            classification = "MDS, NOS without dysplasia"
            derivation.append("monosomy_7 or complex karyotype => MDS, NOS without dysplasia")

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

    # Ensure the designation appears only at the end.
    classification = classification.strip()
    if not classification.endswith("(ICC 2022)"):
        classification += " (ICC 2022)"

    return classification, derivation
