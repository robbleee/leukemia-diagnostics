import json

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
