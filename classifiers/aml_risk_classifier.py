import json

def classify_full_eln2022(params: dict) -> tuple:
    """
    Classify an AML case according to the ELN 2022 risk stratification.
    
    Parameters:
        params (dict): A dictionary containing cytogenetic and molecular markers.
            Expected keys (all booleans unless noted):
                -- Cytogenetic markers:
                   "t_8_21": True if t(8;21)(q22;q22.1) [RUNX1::RUNX1T1] is present.
                   "inv_16_or_t_16_16": True if inv(16)(p13.1q22) or t(16;16)(p13.1;q22) [CBFB::MYH11] is present.
                   "t_9_11": True if t(9;11)(p21.3;q23.3) [MLLT3::KMT2A] is present (intermediate risk).
                   "t_6_9": True if t(6;9)(p23;q34.1) [DEK::NUP214] is present.
                   "t_9_22": True if t(9;22)(q34.1;q11.2) [BCR::ABL1] is present.
                   "kmt2a_rearranged": True if any KMT2A (MLL) rearrangement is present 
                                        (excluding t(9;11) which is handled separately).
                   "inv3_or_t3": True if inv(3)(q21.3q26.2) or t(3;3)(q21.3;q26.2) (GATA2/MECOM) is present.
                   "t_8_16": True if t(8;16)(p11;p13) [KAT6A::CREBBP] is present.
                   "minus5_or_del5q": True if –5 or del(5q) is present.
                   "minus7": True if –7 is present.
                   "abnormal17p": True if 17p abnormalities (often involving TP53) are present.
                   "complex_karyotype": True if there are ≥3 unrelated chromosomal abnormalities.
                   "monosomal_karyotype": True if a monosomal karyotype is present.
                   "hyperdiploid_trisomy": True if a hyperdiploid karyotype with ≥3 trisomies (and no structural abnormalities) is present.
                
                -- Molecular markers:
                   "npm1_mutation": True if NPM1 mutation is detected.
                   "flt3_itd": True if FLT3 internal tandem duplication (FLT3-ITD) is detected.
                      (Note: FLT3-ITD is considered intermediate risk in ELN 2022 regardless of allelic ratio.)
                   "cebpa_bzip": True if an in-frame mutation in the CEBPA bZIP domain is present.
                   "tp53_mutation": True if TP53 mutation (with VAF ≥10%) is present.
                   "runx1_mutation": True if RUNX1 mutation (point/frameshift, not part of t(8;21)) is present.
                   "asxl1_mutation": True if ASXL1 mutation is detected.
                   "ezh2_mutation": True if EZH2 mutation is detected.
                   "bcor_mutation": True if BCOR mutation is detected.
                   "stag2_mutation": True if STAG2 mutation is detected.
                   "srsf2_mutation": True if SRSF2 mutation is detected.
                   "u2af1_mutation": True if U2AF1 mutation is detected.
                   "zrsr2_mutation": True if ZRSR2 mutation is detected.
                
                -- Additional:
                   "secondary_aml": True if the AML is secondary/therapy-related.
                                   (This flag is noted but risk is determined by the genetic markers.)

    Returns:
        tuple: (risk_category, median_os, derivation)
            risk_category (str): "Favorable", "Intermediate", or "Adverse".
            median_os (str): A string describing the median overall survival.
            derivation (list): A list of strings explaining the classification steps.
    """
    
    derivation = []
    step = 1
    
    ################################
    # Step 1: Check for Adverse Risk Markers
    ################################
    derivation.append(f"Step {step}: Checking for adverse risk markers...")
    adverse_reasons = []
    
    # -- Cytogenetic Adverse Markers --
    if params.get("t_6_9", False):
        adverse_reasons.append("t(6;9) [DEK::NUP214]")
    if params.get("t_9_22", False) or params.get("bcr_abl1", False):
        adverse_reasons.append("t(9;22) [BCR::ABL1]")
    if params.get("kmt2a_rearranged", False) and not params.get("t_9_11", False):
        adverse_reasons.append("KMT2A rearrangement (other than t(9;11))")
    if params.get("inv3_or_t3", False) or params.get("inv_3", False) or params.get("t_3_3", False):
        adverse_reasons.append("inv(3) or t(3;3) [GATA2/MECOM]")
    if params.get("t_8_16", False):
        adverse_reasons.append("t(8;16) [KAT6A::CREBBP]")
    if params.get("minus5_or_del5q", False) or params.get("minus_5", False) or params.get("del_5q", False):
        adverse_reasons.append("-5 or del(5q)")
    if params.get("minus7", False) or params.get("minus_7", False):
        adverse_reasons.append("-7")
    if params.get("abnormal17p", False) or params.get("del_17p", False):
        adverse_reasons.append("17p abnormality")
    if params.get("complex_karyotype", False):
        adverse_reasons.append("Complex karyotype (≥3 abnormalities)")
    if params.get("monosomal_karyotype", False):
        adverse_reasons.append("Monosomal karyotype")
    if params.get("hyperdiploid_trisomy", False):
        adverse_reasons.append("Hyperdiploid karyotype with ≥3 trisomies")
    
    # -- Molecular Adverse Markers --
    if params.get("tp53_mutation", False):
        adverse_reasons.append("TP53 mutation")
    if params.get("runx1_mutation", False):
        adverse_reasons.append("RUNX1 mutation")
    if params.get("asxl1_mutation", False):
        adverse_reasons.append("ASXL1 mutation")
    if params.get("ezh2_mutation", False):
        adverse_reasons.append("EZH2 mutation")
    if params.get("bcor_mutation", False):
        adverse_reasons.append("BCOR mutation")
    if params.get("stag2_mutation", False):
        adverse_reasons.append("STAG2 mutation")
    if params.get("srsf2_mutation", False):
        adverse_reasons.append("SRSF2 mutation")
    if params.get("u2af1_mutation", False):
        adverse_reasons.append("U2AF1 mutation")
    if params.get("zrsr2_mutation", False):
        adverse_reasons.append("ZRSR2 mutation")
    
    # If any adverse marker is present, classify as Adverse.
    if adverse_reasons:
        for reason in adverse_reasons:
            derivation.append(f"  ➔ Found {reason}. [Adverse]")
        derivation.append("  ➔ Adverse markers detected - will override any favorable markers.")
        step += 1
    else:
        derivation.append("  ➔ No adverse risk markers found.")
        step += 1
    
    ################################
    # Step 2: Check for Favorable Markers
    ################################
    derivation.append(f"Step {step}: Checking for favorable markers...")
    favorable_reasons = []
    
    # Favorable cytogenetics: Core-binding factor leukemias.
    if params.get("t_8_21", False):
        favorable_reasons.append("t(8;21) [RUNX1::RUNX1T1]")
    if params.get("inv_16_or_t_16_16", False) or params.get("inv_16", False) or params.get("t_16_16", False):
        favorable_reasons.append("inv(16)/t(16;16) [CBFB::MYH11]")
    
    # Favorable molecular markers.
    # NPM1 mutation without FLT3-ITD is favorable.
    if params.get("npm1_mutation", False) and not params.get("flt3_itd", False):
        favorable_reasons.append("NPM1 mutation without FLT3-ITD")
    
    # CEBPA bZIP mutation is favorable.
    if params.get("cebpa_bzip", False) or params.get("biallelic_cebpa", False):
        favorable_reasons.append("Biallelic CEBPA mutation")
    
    # Note: APL (t(15;17)) is not handled here as it is treated as a distinct entity.
    
    if favorable_reasons:
        for reason in favorable_reasons:
            derivation.append(f"  ➔ Found {reason}. [Favorable]")
    else:
        derivation.append("  ➔ No favorable markers found.")
    
    step += 1
    
    ################################
    # Step 3: Check for Intermediate Markers
    ################################
    derivation.append(f"Step {step}: Checking for intermediate markers...")
    intermediate_reasons = []
    
    # FLT3-ITD (regardless of allelic ratio) is intermediate per ELN 2022.
    if params.get("flt3_itd", False):
        intermediate_reasons.append("FLT3-ITD mutation")
    
    # t(9;11) is specifically considered intermediate.
    if params.get("t_9_11", False):
        intermediate_reasons.append("t(9;11) [MLLT3::KMT2A]")
    
    if intermediate_reasons:
        for reason in intermediate_reasons:
            derivation.append(f"  ➔ Found {reason}. [Intermediate]")
    else:
        derivation.append("  ➔ No specific intermediate markers found.")
    
    # Also note secondary/therapy-related AML if flagged (though genetic markers drive the risk).
    if params.get("secondary_aml", False):
        derivation.append("  ➔ History of secondary/therapy-related AML noted.")
    
    step += 1
    
    ################################
    # Step 4: Final Risk Classification
    ################################
    derivation.append(f"Step {step}: Determining final risk classification...")
    
    # If any adverse marker is present, classify as Adverse.
    if adverse_reasons:
        risk_category = "Adverse"
        median_os = "Approximately 8-10 months"
        derivation.append("  ➔ Final classification: ADVERSE RISK")
        derivation.append("  ➔ Adverse markers override any favorable or intermediate markers.")
    
    # If any favorable marker is present and no adverse markers, assign Favorable.
    # Note: If FLT3-ITD is present even with NPM1 mutation, ELN 2022 classifies it as Intermediate.
    elif favorable_reasons and not params.get("flt3_itd", False):
        risk_category = "Favorable"
        median_os = "Not reached or >60 months"
        derivation.append("  ➔ Final classification: FAVORABLE RISK")
        derivation.append("  ➔ Favorable markers present without FLT3-ITD or adverse markers.")
    
    # Otherwise, classify as Intermediate (including NPM1+/FLT3-ITD+ cases).
    else:
        risk_category = "Intermediate"
        median_os = "Approximately 16-24 months"
        if params.get("npm1_mutation", False) and params.get("flt3_itd", False):
            derivation.append("  ➔ Final classification: INTERMEDIATE RISK")
            derivation.append("  ➔ NPM1+ with FLT3-ITD+ assigns to Intermediate Risk category.")
        elif favorable_reasons and params.get("flt3_itd", False):
            derivation.append("  ➔ Final classification: INTERMEDIATE RISK")
            derivation.append("  ➔ Favorable markers with FLT3-ITD+ assigns to Intermediate Risk category.")
        elif intermediate_reasons:
            derivation.append("  ➔ Final classification: INTERMEDIATE RISK")
            derivation.append("  ➔ Intermediate risk markers present without favorable or adverse markers.")
        else:
            derivation.append("  ➔ Final classification: INTERMEDIATE RISK")
            derivation.append("  ➔ No definitive favorable or adverse markers identified.")
    
    return risk_category, median_os, derivation


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
