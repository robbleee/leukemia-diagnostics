import json


##############################
# CLASSIFY AML RESPONSE ELN 2022
##############################
def classify_AML_Response_ELN2022(parsed_data: dict) -> tuple[str, list[str]]:
    """
    Classifies AML response based on ELN 2022 criteria.
    
    The parsed_data should contain:
    - "AdequateSample" (bool)
    - "BoneMarrowBlasts" (float)
    - "BloodCountsProvided" (bool)
    - "Platelets" (float)
    - "Neutrophils" (float)
    - "PreviouslyAchievedCR_CRh_Cri" (bool)
    - "BlastsDecreaseBy50Percent" (bool)
    - "TNCBetween5And25" (bool)
    
    Returns:
      (response, derivation_log)
    """
    derivation = []
    response = "Nonevaluable for response"

    adequate_sample = parsed_data.get("AdequateSample", True)
    bone_marrow_blasts = parsed_data.get("BoneMarrowBlasts", None)
    blood_counts_provided = parsed_data.get("BloodCountsProvided", False)
    platelets = parsed_data.get("Platelets", None)
    neutrophils = parsed_data.get("Neutrophils", None)
    previously_cr = parsed_data.get("PreviouslyAchievedCR_CRh_Cri", False)
    blasts_decrease_50 = parsed_data.get("BlastsDecreaseBy50Percent", False)
    tnc_5_25 = parsed_data.get("TNCBetween5And25", False)

    derivation.append(f"AdequateSample: {adequate_sample}")
    derivation.append(f"BoneMarrowBlasts: {bone_marrow_blasts}")
    derivation.append(f"BloodCountsProvided: {blood_counts_provided}")
    derivation.append(f"Platelets: {platelets}, Neutrophils: {neutrophils}")
    derivation.append(f"PreviouslyAchievedCR_CRh_Cri: {previously_cr}")
    derivation.append(f"BlastsDecreaseBy50Percent: {blasts_decrease_50}")
    derivation.append(f"TNCBetween5And25: {tnc_5_25}")

    # 1) If AdequateSample == no => "Nonevaluable for response"
    if not adequate_sample:
        response = "Nonevaluable for response"
        derivation.append("AdequateSample == no => Nonevaluable for response")
        return response, derivation
    # 2) else if BoneMarrowBlasts < 5
    if bone_marrow_blasts is not None and bone_marrow_blasts < 5:
        if not blood_counts_provided:
            # BloodCountsProvided == no => MLFS
            response = "Morphological leukaemia-free state (MLFS)"
            derivation.append("BloodCountsProvided == no => MLFS")
        else:
            # We do have BloodCountsProvided
            if (platelets is not None and platelets >= 100) and (neutrophils is not None and neutrophils >= 1):
                response = "Complete response (CR)"
                derivation.append("Platelets >= 100 & Neutrophils >= 1 => CR")
            elif (platelets is not None and platelets >= 50) and (neutrophils is not None and neutrophils >= 0.5):
                response = "Complete response with partial haematological recovery (CRh)"
                derivation.append("Platelets >= 50 & Neutrophils >= 0.5 => CRh")
            else:
                # Platelets < 50 OR Neutrophils < 0.5 => CRi
                response = "Complete response with incomplete haematological recovery (CRi)"
                derivation.append("Platelets < 50 or Neutrophils < 0.5 => CRi")
    else:
        # BoneMarrowBlasts >= 5
        if previously_cr:
            # previously achieved CR => relapsed disease
            response = "Relapsed disease"
            derivation.append("PreviouslyAchievedCR_CRh_Cri == yes => Relapsed disease")
        else:
            # check if partial response or refractory
            if (blasts_decrease_50 and tnc_5_25 and neutrophils is not None and neutrophils >= 1 
                and platelets is not None and platelets >= 100):
                response = "Partial response"
                derivation.append("Blasts decrease >=50%, TNC 5-25, Neut >=1, Platelets >=100 => Partial response")
            else:
                response = "No response / Refractory disease"
                derivation.append("No partial response criteria => No response / Refractory disease")

    return response, derivation
