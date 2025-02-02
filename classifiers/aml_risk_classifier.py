import json

def classify_ELN2022(parsed_data: dict) -> tuple:
    """
    Classifies AML according to ELN 2022 risk groups (Favorable, Intermediate, or Adverse)
    assuming that the diagnosis of AML has already been confirmed.
    
    This classifier uses the following inputs from the parsed_data dictionary:
      - AML_defining_recurrent_genetic_abnormalities,
      - Biallelic_TP53_mutation,
      - MDS_related_mutation, and
      - MDS_related_cytogenetics.
      
    Returns:
       tuple: (risk_category (str), derivation (list of strings))
    """
    derivation = []
    
    # Initialize risk as Intermediate by default.
    risk = "Intermediate Risk"
    
    # ---------------------------------------
    # Step 1: Check for Adverse Risk Markers
    # ---------------------------------------
    adverse = False
    
    # 1a. Check for TP53 mutations from the Biallelic_TP53_mutation dictionary.
    tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    if any(tp53.get(key, False) for key in tp53):
        adverse = True
        derivation.append("Adverse: TP53 mutation detected in Biallelic_TP53_mutation markers.")
    
    # 1b. Check for MDS-related mutations.
    mds_mut = parsed_data.get("MDS_related_mutation", {})
    mds_mut_list = [gene for gene, val in mds_mut.items() if val]
    if mds_mut_list:
        adverse = True
        derivation.append(f"Adverse: MDS-related mutation(s) detected ({', '.join(mds_mut_list)}).")
    
    # 1c. Check for adverse cytogenetic abnormalities.
    mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
    # For ELN 2022, common adverse cytogenetics include Complex karyotype and del(17p).
    if mds_cyto.get("Complex_karyotype", False):
        adverse = True
        derivation.append("Adverse: Complex karyotype detected.")
    if mds_cyto.get("del(17p)", False):
        adverse = True
        derivation.append("Adverse: del(17p) detected.")
    
    # ---------------------------------------
    # Step 2: Check for Favorable Risk Markers (if no adverse markers)
    # ---------------------------------------
    favorable = False
    favorable_markers = []
    ad_abn = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    
    # Favorable markers according to ELN 2022:
    if ad_abn.get("NPM1", False):
        favorable = True
        favorable_markers.append("NPM1")
    # Use bZIP as a proxy for biallelic CEBPA mutation.
    if ad_abn.get("bZIP", False):
        favorable = True
        favorable_markers.append("bZIP (CEBPA)")
    if ad_abn.get("RUNX1::RUNX1T1", False):
        favorable = True
        favorable_markers.append("RUNX1::RUNX1T1")
    if ad_abn.get("CBFB::MYH11", False):
        favorable = True
        favorable_markers.append("CBFB::MYH11")
    if ad_abn.get("PML::RARA", False):
        favorable = True
        favorable_markers.append("PML::RARA")
    
    if favorable:
        derivation.append(f"Favorable marker(s) detected: {', '.join(favorable_markers)}")
    
    # ---------------------------------------
    # Step 3: Decide Final Risk Category
    # ---------------------------------------
    if adverse:
        risk = "Adverse Risk"
        derivation.append("Final risk classification: Adverse Risk (adverse markers override favorable markers).")
    elif favorable:
        risk = "Favorable Risk"
        derivation.append("Final risk classification: Favorable Risk.")
    else:
        risk = "Intermediate Risk"
        derivation.append("No clear favorable or adverse markers detected; classified as Intermediate Risk.")
    
    # ---------------------------------------
    # Step 4: Append any Additional Qualifiers
    # ---------------------------------------
    qualifiers = parsed_data.get("qualifiers", {})
    qual_list = []
    for key, val in qualifiers.items():
        # If the qualifier is a string, ignore it if it is "none"
        if isinstance(val, str):
            if val.strip().lower() == "none":
                continue
            else:
                qual_list.append(key.replace("_", " "))
        else:
            if val:  # For booleans, only include if True.
                qual_list.append(key.replace("_", " "))
    if qual_list:
        derivation.append(f"Step {step}: Additional qualifiers detected: {', '.join(qual_list)}.")
        risk += " with qualifiers"

    
    return risk, derivation
