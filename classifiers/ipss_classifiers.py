import math

###################################################
# Constants & Configurations for IPSS-R and IPSS-M
###################################################
IPSSR_CATEGORIES = ["Very Low", "Low", "Int", "High", "Very High"]
IPSSM_CATEGORIES = ["Very Low", "Low", "Moderate Low", "Moderate High", "High", "Very High"]

# Mapping for cytogenetics category (from string to numeric)
CYTO_IPSSR_MAP = {
    "Very Good": 0,
    "Good": 1,
    "Intermediate": 2,
    "Poor": 3,
    "Very Poor": 4
}

# Configuration for each clinical variable used in IPSS-R.
# Each variable is assigned a set of breakpoints and a mapping that converts its raw value into a score.
VARIABLE_CONFIG = {
    "BM_BLAST": {
        "breaks": [-float('inf'), 2, 4.99, 10, float('inf')],
        "mapping": [0, 1, 2, 3],
        "description": "Bone Marrow Blasts"
    },
    "HB": {
        "breaks": [-float('inf'), 8, 10, float('inf')],
        "mapping": [1.5, 1, 0],
        "description": "Hemoglobin"
    },
    "PLT": {
        "breaks": [-float('inf'), 50, 100, float('inf')],
        "mapping": [1, 0.5, 0],
        "description": "Platelet Count"
    },
    "ANC": {
        "breaks": [-float('inf'), 0.8, float('inf')],
        "mapping": [0.5, 0],
        "description": "Absolute Neutrophil Count"
    }
}

###################################################
# Beta Definitions for IPSS-M
###################################################
betas = [
    { "name": "CYTOVEC",       "coeff": 0.287,  "means": 1.39,  "worst": 4,    "best": 0 },
    { "name": "BLAST5",        "coeff": 0.352,  "means": 0.922, "worst": 4,    "best": 0 },
    { "name": "TRANSF_PLT100", "coeff": -0.222, "means": 1.41,  "worst": 0,    "best": 2.5 },
    { "name": "HB1",           "coeff": -0.171, "means": 9.87,  "worst": 2,    "best": 20 },
    { "name": "SF3B1_alpha",   "coeff": -0.0794,"means": 0.186, "worst": 0,    "best": 1 },
    { "name": "SF3B1_5q",      "coeff": 0.504,  "means": 0.0166,"worst": 1,    "best": 0 },
    { "name": "ASXL1",         "coeff": 0.213,  "means": 0.252, "worst": 1,    "best": 0 },
    { "name": "SRSF2",         "coeff": 0.239,  "means": 0.158, "worst": 1,    "best": 0 },
    { "name": "DNMT3A",        "coeff": 0.221,  "means": 0.161, "worst": 1,    "best": 0 },
    { "name": "RUNX1",         "coeff": 0.423,  "means": 0.126, "worst": 1,    "best": 0 },
    { "name": "U2AF1",         "coeff": 0.247,  "means": 0.0866,"worst": 1,    "best": 0 },
    { "name": "EZH2",          "coeff": 0.27,   "means": 0.0588,"worst": 1,    "best": 0 },
    { "name": "CBL",           "coeff": 0.295,  "means": 0.0473,"worst": 1,    "best": 0 },
    { "name": "NRAS",          "coeff": 0.417,  "means": 0.0362,"worst": 1,    "best": 0 },
    { "name": "IDH2",          "coeff": 0.379,  "means": 0.0429,"worst": 1,    "best": 0 },
    { "name": "KRAS",          "coeff": 0.202,  "means": 0.0271,"worst": 1,    "best": 0 },
    { "name": "MLL_PTD",       "coeff": 0.798,  "means": 0.0247,"worst": 1,    "best": 0 },
    { "name": "ETV6",          "coeff": 0.391,  "means": 0.0216,"worst": 1,    "best": 0 },
    { "name": "NPM1",          "coeff": 0.43,   "means": 0.0112,"worst": 1,    "best": 0 },
    { "name": "TP53multi",     "coeff": 1.18,   "means": 0.071, "worst": 1,    "best": 0 },
    { "name": "FLT3",          "coeff": 0.798,  "means": 0.0108,"worst": 1,    "best": 0 },
    { "name": "Nres2",         "coeff": 0.231,  "means": 0.388, "worst": 2,    "best": 0 }
]

###################################################
# Helper Functions for IPSS-R Calculation
###################################################
def cut_break(value: float, breaks: list, mapping: list, right: bool = True, derivation: list = None) -> float:
    """
    Categorize a numeric value based on provided intervals.
    
    For example, if a value of 5.05 falls between 4.5 and 6 (right-closed),
    we assign the corresponding category label.
    
    If 'derivation' is provided, add a plain-language explanation.
    """
    for i in range(1, len(breaks)):
        lower = breaks[i - 1]
        upper = breaks[i]
        if right:
            if value > lower and value <= upper:
                if derivation is not None:
                    derivation.append(f"Value {value} falls between {lower} and {upper} (right-closed); assign score '{mapping[i-1]}'.")
                return mapping[i - 1]
        else:
            if value >= lower and value < upper:
                if derivation is not None:
                    derivation.append(f"Value {value} falls between {lower} and {upper} (left-closed); assign score '{mapping[i-1]}'.")
                return mapping[i - 1]
    if derivation is not None:
        derivation.append(f"Value {value} did not fall into any interval.")
    return float('nan')

def get_ipssr_contribution(value: float, var_name: str, derivation: list) -> float:
    """
    Calculate the contribution score for a clinical variable (e.g., BM_BLAST)
    using the predefined configuration. Appends a plain-language explanation
    to the derivation log.
    """
    cfg = VARIABLE_CONFIG.get(var_name)
    if not cfg:
        msg = f"No configuration found for variable {var_name}."
        derivation.append(msg)
        raise ValueError(msg)
    
    desc = cfg.get("description", var_name)
    derivation.append(f"Evaluating {desc} value: {value}.")
    mapped_val = cut_break(value, cfg["breaks"], cfg["mapping"], right=True, derivation=derivation)
    derivation.append(f"Thus, the contribution from {desc} is {mapped_val}.")
    return float(mapped_val)

###################################################
# IPSS-R Calculation Function
###################################################
def compute_ipssr(ipss_input: dict, rounding: bool = True, rounding_digits: int = 4) -> dict:
    """
    Compute IPSS-R risk score and risk category (plus age-adjusted values, if AGE is provided)
    from a single input dictionary that follows the required JSON structure.
    
    Expected keys:
      - BM_BLAST (Bone Marrow Blasts, %)
      - HB (Hemoglobin, g/dl)
      - PLT (Platelet Count, 1e9/l)
      - ANC (Absolute Neutrophil Count, 1e9/l)
      - AGE (Age, years)
      - CYTO_IPSSR (Cytogenetics Category, e.g., "Good", "Intermediate")
    
    Returns a dictionary with:
      - IPSSR_SCORE: Raw IPSS-R score.
      - IPSSR_CAT: Risk category.
      - IPSSRA_SCORE: Age-adjusted score (if AGE provided).
      - IPSSRA_CAT: Age-adjusted risk category.
      - derivation: A clinician-friendly explanation of each calculation step.
    """
    derivation = []
    derivation.append("Starting IPSS-R risk calculation.")

    # Extract inputs.
    bmblast = ipss_input.get("BM_BLAST")
    hb = ipss_input.get("HB")
    plt_val = ipss_input.get("PLT")
    anc = ipss_input.get("ANC")
    age = ipss_input.get("AGE")
    cyto_str = ipss_input.get("CYTO_IPSSR")

    derivation.append(f"Received values: BM_BLAST={bmblast}%, HB={hb} g/dl, PLT={plt_val}, ANC={anc}, AGE={age}, CYTO_IPSSR='{cyto_str}'.")

    # Convert cytogenetic category to numeric.
    if cyto_str not in CYTO_IPSSR_MAP:
        msg = f"Error: Cytogenetic category '{cyto_str}' is invalid. Expected one of {list(CYTO_IPSSR_MAP.keys())}."
        derivation.append(msg)
        return {"error": msg, "derivation": derivation}
    cytovec = CYTO_IPSSR_MAP[cyto_str]
    derivation.append(f"Cytogenetic category '{cyto_str}' maps to numeric score {cytovec}.")

    # Compute contributions for each clinical variable.
    try:
        bmblast_contrib = get_ipssr_contribution(float(bmblast), "BM_BLAST", derivation)
        hb_contrib = get_ipssr_contribution(float(hb), "HB", derivation)
        plt_contrib = get_ipssr_contribution(float(plt_val), "PLT", derivation)
        anc_contrib = get_ipssr_contribution(float(anc), "ANC", derivation)
    except ValueError as e:
        derivation.append(str(e))
        return {"error": str(e), "derivation": derivation}

    # Sum contributions.
    derivation.append("Summing contributions for overall IPSS-R score:")
    derivation.append(f"  BM_BLAST: {bmblast_contrib}")
    derivation.append(f"  HB: {hb_contrib}")
    derivation.append(f"  PLT: {plt_contrib}")
    derivation.append(f"  ANC: {anc_contrib}")
    derivation.append(f"  Cytogenetics: {cytovec}")
    ipssr_raw = bmblast_contrib + hb_contrib + plt_contrib + anc_contrib + cytovec
    derivation.append(f"Total raw IPSS-R score = {ipssr_raw}")
    
    if rounding:
        old_score = ipssr_raw
        ipssr_raw = round(ipssr_raw, rounding_digits)
        derivation.append(f"Rounded raw score from {old_score} to {ipssr_raw} (using {rounding_digits} decimals).")

    # Map raw score to a risk category.
    ipssr_breaks = [-float('inf'), 1.5, 3, 4.5, 6, float('inf')]
    derivation.append(f"Mapping score {ipssr_raw} to a risk category using breaks: {ipssr_breaks}.")
    ipssr_cat = cut_break(ipssr_raw, ipssr_breaks, IPSSR_CATEGORIES, right=True, derivation=derivation)
    derivation.append(f"Assigned IPSS-R risk category: '{ipssr_cat}'.")

    # Age-adjustment.
    ipssra_raw = None
    ipssra_cat = None
    if age is not None:
        age_adjust = (float(age) - 70) * (0.05 - ipssr_raw * 0.005)
        derivation.append(f"Calculating age adjustment: (AGE - 70) * (0.05 - (IPSS-R score * 0.005)) = ({age} - 70) * (0.05 - {ipssr_raw} * 0.005) = {age_adjust:.4f}")
        ipssra_raw = ipssr_raw + age_adjust
        derivation.append(f"Age-adjusted raw score = {ipssra_raw}")
        if rounding:
            old_val = ipssra_raw
            ipssra_raw = round(ipssra_raw, rounding_digits)
            derivation.append(f"Rounded age-adjusted score from {old_val} to {ipssra_raw}.")
        ipssra_cat = cut_break(ipssra_raw, ipssr_breaks, IPSSR_CATEGORIES, right=True, derivation=derivation)
        derivation.append(f"Assigned age-adjusted risk category: '{ipssra_cat}'.")
    
    derivation.append("Completed IPSS-R risk calculation.")
    return {
        "IPSSR_SCORE": ipssr_raw,
        "IPSSR_CAT": ipssr_cat,
        "IPSSRA_SCORE": ipssra_raw,
        "IPSSRA_CAT": ipssra_cat,
        "derivation": derivation
    }

###################################################
# IPSS-M Calculation Function
###################################################
def compute_ipssm(ipss_input: dict, betas: list, rounding: bool = True, rounding_digits: int = 2, cutpoints: list = None) -> dict:
    """
    Compute the IPSS-M risk score and risk category based on a single input dictionary.
    
    The input dictionary is expected to contain all fields (clinical and molecular)
    as defined in the required JSON structure.
    
    The 'betas' list (of beta coefficients) specifies how each variable contributes.
    For each beta, if the patient value is missing ("NA" or None), the default for the scenario is used.
    
    The function calculates risk scores for three scenarios: "means", "worst", and "best".
    
    Returns a dictionary with keys "means", "worst", and "best" (each containing:
      - riskScore: computed risk score,
      - riskCat: risk category (text),
      - contributions: a breakdown of contributions)
    along with a "derivation" key containing a detailed plain-language explanation.
    """
    derivation = []
    derivation.append("Starting IPSS-M risk calculation.")
    
    if cutpoints is None:
        cutpoints = [-1.5, -0.5, 0, 0.5, 1.5]
    breaks = [-float('inf')] + cutpoints + [float('inf')]
    derivation.append(f"Using cutpoints: {cutpoints} resulting in breaks: {breaks}.")
    derivation.append(f"Final risk categories will be: {IPSSM_CATEGORIES}.")

    scenarios = ["means", "worst", "best"]
    scores = {}

    for scenario in scenarios:
        derivation.append(f"--- Processing scenario '{scenario}' ---")
        contributions = {}

        for beta in betas:
            var_name = beta["name"]
            derivation.append(f"Evaluating variable '{var_name}' for scenario '{scenario}'.")
            
            raw_value = ipss_input.get(var_name, None)
            if raw_value == "NA" or raw_value is None:
                fallback = beta.get(scenario, beta.get("means", 0))
                derivation.append(f"No value provided for '{var_name}'; using default ({fallback}) for scenario '{scenario}'.")
                raw_value = fallback
            if var_name == "Nres2":
                scenario_dict = ipss_input.get("Nres2", {})
                nested_val = scenario_dict.get(scenario)
                if nested_val is not None:
                    derivation.append(f"Found nested value for '{var_name}' for scenario '{scenario}': {nested_val}.")
                    raw_value = nested_val
                else:
                    fallback = beta.get(scenario, beta.get("means", 0))
                    derivation.append(f"No nested value for '{var_name}'; using default ({fallback}).")
                    raw_value = fallback

            try:
                val_float = float(raw_value)
            except Exception as e:
                derivation.append(f"Error converting value for '{var_name}' to float: {raw_value}. Error: {e}. Using 0.0.")
                val_float = 0.0

            mu = float(beta.get("means", 0))
            coeff = float(beta.get("coeff", 0))
            derivation.append(f"For '{var_name}', patient value = {val_float}, average = {mu}, coefficient = {coeff}.")
            # Contribution formula: (value - mean)*coeff / ln(2)
            contribution = ((val_float - mu) * coeff) / math.log(2)
            derivation.append(f"Contribution for '{var_name}' = (({val_float} - {mu}) * {coeff}) / ln(2) = {contribution:.4f}.")
            contributions[var_name] = contribution

        risk_score = sum(contributions.values())
        derivation.append(f"Scenario '{scenario}': Total raw risk score = {risk_score:.4f}.")
        if rounding:
            old_val = risk_score
            risk_score = round(risk_score, rounding_digits)
            derivation.append(f"Rounded risk score from {old_val} to {risk_score} (using {rounding_digits} decimals).")
        risk_cat = cut_break(risk_score, breaks, IPSSM_CATEGORIES, right=True, derivation=derivation)
        derivation.append(f"Risk score {risk_score} maps to category '{risk_cat}' for scenario '{scenario}'.")
        scores[scenario] = {
            "riskScore": risk_score,
            "riskCat": str(risk_cat),
            "contributions": contributions,
        }
        derivation.append(f"--- Completed scenario '{scenario}' ---")

    derivation.append("Finished IPSS-M risk calculation.")
    return {
        "means": scores["means"],
        "worst": scores["worst"],
        "best": scores["best"],
        "derivation": derivation
    }

###################################################
# Example Usage
###################################################
if __name__ == "__main__":
    # Example input dictionary following the required JSON structure for IPSS.
    example_ipss_dict = {
        "BM_BLAST": 4.5,       # Bone Marrow Blasts (%)
        "HB": 9.0,             # Hemoglobin (g/dl)
        "PLT": 75,             # Platelet Count (1e9/l)
        "ANC": 0.7,            # Absolute Neutrophil Count (1e9/l)
        "AGE": 72,             # Age (years)
        "CYTO_IPSSR": "Intermediate",  # Cytogenetics Category
        
        # Additional fields (for IPSS-M; these may be used by beta definitions)
        "TP53mut": "1",
        "TP53maxvaf": 10,
        "TP53loh": 0,
        "MLL_PTD": 0,
        "FLT3": 0,
        "del5q": 0,
        "del7_7q": 0,
        "del17_17p": 0,
        "complex": 0,
        "ASXL1": 0,
        "CBL": 0,
        "DNMT3A": 0,
        "ETV6": 0,
        "EZH2": 0,
        "IDH2": 0,
        "KRAS": 0,
        "NPM1": 0,
        "NRAS": 0,
        "RUNX1": 0,
        "SF3B1": 0,
        "SRSF2": 0,
        "U2AF1": 0,
        "BCOR": 0,
        "BCORL1": 0,
        "CEBPA": 0,
        "ETNK1": 0,
        "GATA2": 0,
        "GNB1": 0,
        "IDH1": 0,
        "NF1": 0,
        "PHF6": 0,
        "PPM1D": 0,
        "PRPF8": 0,
        "PTPN11": 0,
        "SETBP1": 0,
        "STAG2": 0,
        "WT1": 0
    }

    print("==== IPSS-R Calculation ====")
    ipssr_result = compute_ipssr(example_ipss_dict)
    print("IPSS-R Score:", ipssr_result.get("IPSSR_SCORE"))
    print("IPSS-R Category:", ipssr_result.get("IPSSR_CAT"))
    print("Age-Adjusted IPSS-R Score:", ipssr_result.get("IPSSRA_SCORE"))
    print("Age-Adjusted IPSS-R Category:", ipssr_result.get("IPSSRA_CAT"))
    print("\nDerivation Log:")
    for step in ipssr_result.get("derivation", []):
        print("  ", step)

    print("\n==== IPSS-M Calculation ====")
    # For demonstration, we use the global betas defined above.
    ipssm_result = compute_ipssm(example_ipss_dict, betas)
    print("IPSS-M (Means Scenario):", ipssm_result["means"])
    print("IPSS-M (Worst Scenario):", ipssm_result["worst"])
    print("IPSS-M (Best Scenario):", ipssm_result["best"])
    print("\nDerivation Log:")
    for step in ipssm_result.get("derivation", []):
        print("  ", step)
