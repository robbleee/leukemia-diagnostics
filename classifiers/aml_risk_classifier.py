import json


def eln2024_non_intensive_risk(mut_dict: dict) -> tuple:
    """
    Classify AML risk according to the revised ELN24 (non-intensive cohort),
    returning the risk level, median OS, and derivation steps.

    The classification hierarchy:
      1) Adverse if TP53, KRAS, or PTPN11 is mutated (OS ~5.4 months)
      2) Otherwise, Intermediate if NRAS or FLT3-ITD is mutated
         (or other unclassified mutations), OS ~13 months
      3) Otherwise, Favorable if NPM1, IDH1, IDH2, or DDX41 is mutated
         (OS ~34.8 months)
      4) Otherwise, Intermediate risk (default)

    Args:
        mut_dict (dict): A dictionary of booleans for relevant genes, e.g.:
            {
                "TP53": True/False,
                "KRAS": True/False,
                "PTPN11": True/False,
                "NRAS": True/False,
                "FLT3_ITD": True/False,
                "NPM1": True/False,
                "IDH1": True/False,
                "IDH2": True/False,
                "DDX41": True/False,
                ...
            }

    Returns:
        tuple: (risk_level (str), median_os (float), derivation (list of str))
    """
    derivation = []
    step = 1

    ################################
    # Step 1: Check for Adverse Risk
    ################################
    derivation.append(f"Step {step}: Checking for adverse risk mutations...")
    if mut_dict.get("TP53", False):
        derivation.append("  ➔ TP53 mutation detected. [Adverse]")
        return "Adverse", 5.4, derivation

    if mut_dict.get("KRAS", False):
        derivation.append("  ➔ KRAS mutation detected. [Adverse]")
        return "Adverse", 5.4, derivation

    if mut_dict.get("PTPN11", False):
        derivation.append("  ➔ PTPN11 mutation detected. [Adverse]")
        return "Adverse", 5.4, derivation

    derivation.append("  ➔ No adverse risk mutations found.")
    step += 1

    ################################
    # Step 2: Check for Intermediate Risk
    ################################
    derivation.append(f"Step {step}: Checking for intermediate risk mutations...")
    if mut_dict.get("NRAS", False):
        derivation.append("  ➔ NRAS mutation detected. [Intermediate]")
        return "Intermediate", 13.0, derivation

    if mut_dict.get("FLT3_ITD", False):
        derivation.append("  ➔ FLT3-ITD mutation detected. [Intermediate]")
        return "Intermediate", 13.0, derivation

    derivation.append("  ➔ No intermediate risk mutations found.")
    step += 1

    ################################
    # Step 3: Check for Favorable Risk
    ################################
    derivation.append(f"Step {step}: Checking for favorable risk mutations...")
    favorable_markers = []
    
    if mut_dict.get("NPM1", False):
        favorable_markers.append("NPM1")
    if mut_dict.get("IDH1", False):
        favorable_markers.append("IDH1")
    if mut_dict.get("IDH2", False):
        favorable_markers.append("IDH2")
    if mut_dict.get("DDX41", False):
        favorable_markers.append("DDX41")

    if favorable_markers:
        derivation.append(f"  ➔ Favorable mutations found: {', '.join(favorable_markers)}. [Favorable]")
        return "Favorable", 34.8, derivation

    derivation.append("  ➔ No favorable risk mutations found.")
    step += 1

    ################################
    # Step 4: Default to Intermediate Risk
    ################################
    derivation.append(f"Step {step}: No adverse, intermediate, or favorable markers detected.")
    derivation.append("  ➔ Defaulting to Intermediate Risk.")
    return "Intermediate", 13.0, derivation


def classify_ELN2022(parsed_data: dict) -> tuple:
    """
    Classifies AML risk based on ELN2022 criteria and returns the risk category, median OS, and derivation.
    
    ELN Risk Category and Median OS:
      - Favorable Risk: Not reached or >60 months
      - Intermediate Risk: Approximately 16–24 months
      - Adverse Risk: Approximately 8–10 months

    Args:
        parsed_data (dict): Extracted report data.

    Returns:
        tuple: (risk (str), median_os (str), derivation (list of str))
    """
    derivation = []
    step = 1

    risk = "Intermediate Risk"

    ################################
    # Step 1: Check for Adverse
    ################################
    adverse = False
    derivation.append(f"Step {step}: Checking for adverse risk markers...")
    
    tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    if any(tp53.get(key, False) for key in tp53):
        adverse = True
        derivation.append("  ➔ Found TP53 mutation. [Adverse]")
    mds_mut = parsed_data.get("MDS_related_mutation", {})
    mds_mut_list = [gene for gene, val in mds_mut.items() if val]
    if mds_mut_list:
        adverse = True
        derivation.append(f"  ➔ Found MDS-related mutations: {', '.join(mds_mut_list)} [Adverse]")
    mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
    if mds_cyto.get("Complex_karyotype", False):
        adverse = True
        derivation.append("  ➔ Found Complex karyotype. [Adverse]")
    if mds_cyto.get("del(17p)", False):
        adverse = True
        derivation.append("  ➔ Found del(17p). [Adverse]")
    
    step += 1

    ################################
    # Step 2: Check for Favorable
    ################################
    derivation.append(f"Step {step}: Checking for favorable markers...")
    favorable = False
    favorable_markers = []
    ad_abn = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})

    if ad_abn.get("NPM1", False):
        favorable = True
        favorable_markers.append("NPM1")
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
        derivation.append(f"  ➔ Found favorable markers: {', '.join(favorable_markers)}")
    else:
        derivation.append("  ➔ No favorable markers found.")
    
    step += 1

    ################################
    # Step 3: Final Risk Category
    ################################
    derivation.append(f"Step {step}: Determining final risk category...")
    if adverse:
        risk = "Adverse Risk"
        derivation.append("  ➔ Adverse overrides favorable => Adverse Risk.")
    elif favorable:
        risk = "Favorable Risk"
        derivation.append("  ➔ Favorable risk set.")
    else:
        risk = "Intermediate Risk"
        derivation.append("  ➔ Neither adverse nor favorable => Intermediate Risk.")
    step += 1

    ################################
    # Step 4: Check Qualifiers
    ################################
    derivation.append(f"Step {step}: Checking qualifiers...")
    qualifiers = parsed_data.get("qualifiers", {})
    qual_list = []
    for key, val in qualifiers.items():
        if isinstance(val, str):
            if val.strip().lower() == "none":
                continue
            else:
                qual_list.append(key.replace("_", " "))
        else:
            if val:
                qual_list.append(key.replace("_", " "))
    if qual_list:
        derivation.append(f"  ➔ Additional qualifiers: {', '.join(qual_list)}")
        risk += " with qualifiers"
    else:
        derivation.append("  ➔ No additional qualifiers found.")

    # Determine median OS based on risk category.
    if "Adverse" in risk:
        median_os = "Approximately 8–10 months"
    elif "Favorable" in risk:
        median_os = "Not reached or >60 months"
    else:
        median_os = "Approximately 16–24 months"

    return risk, median_os, derivation
