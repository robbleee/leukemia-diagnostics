import json

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
        qualifier_list.append("post cytotoxic therapy")
        derivation.append("Qualifier: post cytotoxic therapy")
    if qualifiers.get("predisposing_germline_variant"):
        germ = qualifiers["predisposing_germline_variant"]
        if germ.lower() != "none":
            qualifier_list.append(f"associated with germline {germ}")
            derivation.append(f"Qualifier: associated with germline {germ}")

    if qualifier_list:
        classification += f", {', '.join(qualifier_list)}"

    return classification, derivation
