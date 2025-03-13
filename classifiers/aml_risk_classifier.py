import json

def classify_eln2024_non_intensive_risk(mut_dict: dict) -> dict:
    """
    Classify AML risk according to the revised ELN24 (non-intensive cohort),
    returning a dictionary with 'risk_level' and 'median_os'.

    The classification hierarchy is:
      1) Adverse if TP53, KRAS, or PTPN11 is mutated (OS ~5.4 months)
      2) Otherwise, Intermediate if NRAS or FLT3-ITD is mutated
         (or other unclassified mutations), OS ~13 months
      3) Otherwise, Favorable if NPM1, IDH1, IDH2, or DDX41 is mutated
         (OS ~34.8 months)
      4) Otherwise, Intermediate risk

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
        dict: {"risk_level": (str), "median_os": (float)}
    """
    # 1) Adverse check
    if mut_dict.get("TP53", False) or mut_dict.get("KRAS", False) or mut_dict.get("PTPN11", False):
        return {"risk_level": "Adverse", "median_os": 5.4}

    # 2) Intermediate check (NRAS or FLT3-ITD or unclassified, assuming no TP53/KRAS/PTPN11)
    if mut_dict.get("NRAS", False) or mut_dict.get("FLT3_ITD", False):
        return {"risk_level": "Intermediate", "median_os": 13.0}

    # 3) Favorable check (NPM1, IDH1, IDH2, DDX41), if not adverse/intermediate
    if (mut_dict.get("NPM1", False) or mut_dict.get("IDH1", False) or
        mut_dict.get("IDH2", False) or mut_dict.get("DDX41", False)):
        return {"risk_level": "Favorable", "median_os": 34.8}

    # 4) Default => Intermediate
    return {"risk_level": "Intermediate", "median_os": 13.0}


def classify_ELN2022(parsed_data: dict) -> tuple:
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

    return risk, derivation
