import math

# ============================================================================
# Field Definitions and Other Data
# ============================================================================

# Clinical and Molecular Field Definitions
fields_definitions = {
    "BM_BLAST": {
        "label": "Bone Marrow Blasts",
        "category": "clinical",
        "type": "number",
        "required": True,
        "varName": "BM_BLAST",
        "units": "%",
        "min": 0,
        "max": 30,
    },
    "HB": {
        "label": "Hemoglobin",
        "category": "clinical",
        "type": "number",
        "required": True,
        "varName": "HB",
        "units": " g/dl",
        "min": 4,
        "max": 20,
        "notes": "Useful conversion for Hb values: 10 g/dL= 6.2 mmol/L, 8 g/dL= 5.0 mmol/L",
    },
    "PLT": {
        "label": "Platelet Count",
        "category": "clinical",
        "type": "number",
        "required": True,
        "varName": "PLT",
        "units": " 1e9/l",
        "min": 0,
        "max": 2000,
    },
    "ANC": {
        "label": "Absolute Neutrophil Count",
        "category": "clinical",
        "type": "number",
        "required": True,
        "varName": "ANC",
        "min": 0,
        "max": 15,
        "units": " 1e9/l",
        "notes": "Only needed to calculate IPSS-R",
    },
    "AGE": {
        "label": "Age",
        "category": "clinical",
        "type": "number",
        "required": False,
        "varName": "AGE",
        "units": " years",
        "min": 18,
        "max": 120,
        "notes": "Only needed to calculate age-adjusted IPSS-R",
        "allowNull": True,
    },
    "CYTO_IPSSR": {
        "label": "Cytogenetics Category",
        "category": "cytogenetics",
        "type": "string",
        "required": True,
        "varName": "CYTO_IPSSR",
        "values": ['Very Good', 'Good', 'Intermediate', 'Poor', 'Very Poor'],
    },
    "TP53mut": {
        "label": "Number of TP53 mutations",
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": "0",
        "varName": "TP53mut",
        "values": ['0', '1', '2 or more'],
    },
    "TP53maxvaf": {
        "label": "Maximum VAF of TP53 mutation(s)",
        "category": "molecular",
        "type": "number",
        "required": False,
        "default": 0,
        "varName": "TP53maxvaf",
        "units": "%",
        "min": 0,
        "max": 100,
    },
    "TP53loh": {
        "label": "Loss of heterozygosity at TP53 locus",
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": 0,
        "varName": "TP53loh",
        "values": [0, 1, 'NA'],
    },
    "MLL_PTD": {
        "label": "MLL <or KMT2A> PTD",
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": 0,
        "varName": "MLL_PTD",
        "values": [0, 1, 'NA'],
    },
    "FLT3": {
        "label": "FLT3 ITD or TKD",
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": 0,
        "varName": "FLT3",
        "values": [0, 1, 'NA'],
    },
}

# Cytogenetic Data – add a field for each cytogenetic marker.
cytogenetics = ['del5q', 'del7_7q', 'del17_17p', 'complex']
for value in cytogenetics:
    fields_definitions[value] = {
        "label": f"Presence of {value}",
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": 0,
        "varName": value,
        "values": [0, 1],
    }

# Genes – define two lists and then add each gene to the field definitions.
genes_main = ['ASXL1', 'CBL', 'DNMT3A', 'ETV6', 'EZH2', 'IDH2', 'KRAS', 'NPM1', 'NRAS', 'RUNX1', 'SF3B1', 'SRSF2', 'U2AF1']
genes_residual = ['BCOR', 'BCORL1', 'CEBPA', 'ETNK1', 'GATA2', 'GNB1', 'IDH1', 'NF1', 'PHF6', 'PPM1D', 'PRPF8', 'PTPN11', 'SETBP1', 'STAG2', 'WT1']
genes = genes_main + genes_residual

for gene in genes:
    fields_definitions[gene] = {
        "label": gene,
        "category": "molecular",
        "type": "string",
        "required": False,
        "default": 0,
        "varName": gene,
        "values": [0, 1, 'NA'],
    }

# Fields used for IPSS-M and IPSS-R computations
ipssm_fields = [
    fields_definitions['BM_BLAST'],
    fields_definitions['HB'],
    fields_definitions['PLT'],
    fields_definitions['del5q'],
    fields_definitions['del7_7q'],
    fields_definitions['del17_17p'],
    fields_definitions['complex'],
    fields_definitions['CYTO_IPSSR'],
    fields_definitions['TP53mut'],
    fields_definitions['TP53maxvaf'],
    fields_definitions['TP53loh'],
    fields_definitions['MLL_PTD'],
    fields_definitions['FLT3'],
    fields_definitions['ASXL1'],
    fields_definitions['CBL'],
    fields_definitions['DNMT3A'],
    fields_definitions['ETV6'],
    fields_definitions['EZH2'],
    fields_definitions['IDH2'],
    fields_definitions['KRAS'],
    fields_definitions['NPM1'],
    fields_definitions['NRAS'],
    fields_definitions['RUNX1'],
    fields_definitions['SF3B1'],
    fields_definitions['SRSF2'],
    fields_definitions['U2AF1'],
    fields_definitions['BCOR'],
    fields_definitions['BCORL1'],
    fields_definitions['CEBPA'],
    fields_definitions['ETNK1'],
    fields_definitions['GATA2'],
    fields_definitions['GNB1'],
    fields_definitions['IDH1'],
    fields_definitions['NF1'],
    fields_definitions['PHF6'],
    fields_definitions['PPM1D'],
    fields_definitions['PRPF8'],
    fields_definitions['PTPN11'],
    fields_definitions['SETBP1'],
    fields_definitions['STAG2'],
    fields_definitions['WT1'],
]

ipssr_fields = [
    fields_definitions['BM_BLAST'],
    fields_definitions['HB'],
    fields_definitions['PLT'],
    fields_definitions['ANC'],
    fields_definitions['CYTO_IPSSR'],
    fields_definitions['AGE'],
]

# Betas for the IPSS-M risk score calculation
betas = [
    {"name": "CYTOVEC", "coeff": 0.287, "means": 1.39, "worst": 4, "best": 0},
    {"name": "BLAST5", "coeff": 0.352, "means": 0.922, "worst": 4, "best": 0},
    {"name": "TRANSF_PLT100", "coeff": -0.222, "means": 1.41, "worst": 0, "best": 2.5},
    {"name": "HB1", "coeff": -0.171, "means": 9.87, "worst": 2, "best": 20},
    {"name": "SF3B1_alpha", "coeff": -0.0794, "means": 0.186, "worst": 0, "best": 1},
    {"name": "SF3B1_5q", "coeff": 0.504, "means": 0.0166, "worst": 1, "best": 0},
    {"name": "ASXL1", "coeff": 0.213, "means": 0.252, "worst": 1, "best": 0},
    {"name": "SRSF2", "coeff": 0.239, "means": 0.158, "worst": 1, "best": 0},
    {"name": "DNMT3A", "coeff": 0.221, "means": 0.161, "worst": 1, "best": 0},
    {"name": "RUNX1", "coeff": 0.423, "means": 0.126, "worst": 1, "best": 0},
    {"name": "U2AF1", "coeff": 0.247, "means": 0.0866, "worst": 1, "best": 0},
    {"name": "EZH2", "coeff": 0.27, "means": 0.0588, "worst": 1, "best": 0},
    {"name": "CBL", "coeff": 0.295, "means": 0.0473, "worst": 1, "best": 0},
    {"name": "NRAS", "coeff": 0.417, "means": 0.0362, "worst": 1, "best": 0},
    {"name": "IDH2", "coeff": 0.379, "means": 0.0429, "worst": 1, "best": 0},
    {"name": "KRAS", "coeff": 0.202, "means": 0.0271, "worst": 1, "best": 0},
    {"name": "MLL_PTD", "coeff": 0.798, "means": 0.0247, "worst": 1, "best": 0},
    {"name": "ETV6", "coeff": 0.391, "means": 0.0216, "worst": 1, "best": 0},
    {"name": "NPM1", "coeff": 0.43, "means": 0.0112, "worst": 1, "best": 0},
    {"name": "TP53multi", "coeff": 1.18, "means": 0.071, "worst": 1, "best": 0},
    {"name": "FLT3", "coeff": 0.798, "means": 0.0108, "worst": 1, "best": 0},
    {"name": "Nres2", "coeff": 0.231, "means": 0.388, "worst": 2, "best": 0},
]

# Category labels for IPSS-R and IPSS-M scores
ipssrCat = ['Very Low', 'Low', 'Int', 'High', 'Very High']
ipssmCat = ['Very Low', 'Low', 'Moderate Low', 'Moderate High', 'High', 'Very High']

# ============================================================================
# Utility Functions
# ============================================================================

def cut_break(value, breaks, mapping=None, right=True):
    """
    Given a numeric value, find in which interval (defined by 'breaks')
    it lies. If a mapping list is provided, return the mapped value.
    Otherwise, return the interval index.
    
    Parameters:
        value (float): the number to classify.
        breaks (list): a list of boundary numbers (including -inf and +inf).
        mapping (list, optional): a list of mapped values for each interval.
        right (bool): if True, intervals are open on the left and closed on the right.
    
    Returns:
        Mapped value or interval index.
    """
    for i in range(1, len(breaks)):
        if right:
            if value > breaks[i - 1] and value <= breaks[i]:
                return mapping[i - 1] if mapping is not None else i - 1
        else:
            if value >= breaks[i - 1] and value < breaks[i]:
                return mapping[i - 1] if mapping is not None else i - 1
    return float('nan')


# ============================================================================
# Core Computation Functions
# ============================================================================

def compute_ipssr(patient, rounding=True, rounding_digits=4):
    """
    Compute IPSS-R risk score and risk categories.
    
    Parameters:
        patient (dict): Dictionary with required keys:
            - bmblast: Bone marrow blasts (in %)
            - hb: Hemoglobin (g/dl)
            - plt: Platelet count (1e9/l)
            - anc: Absolute neutrophil count (1e9/l)
            - cytovec (optional): Cytogenetic category as a number (0-4)
            - cytoIpssr (optional): Cytogenetic category as a string 
                                    (e.g. 'Very Good', 'Good', etc.)
            - age (optional): Patient age (years)
    
    Returns:
        dict: {
            "IPSSR_SCORE": numeric risk score,
            "IPSSR_CAT": risk category (string),
            "IPSSRA_SCORE": age-adjusted risk score (or None),
            "IPSSRA_CAT": age-adjusted risk category (or None)
        }
    """
    cytovec_map = {'Very Good': 0, 'Good': 1, 'Intermediate': 2, 'Poor': 3, 'Very Poor': 4}
    cytovec = patient.get('cytovec')
    if (cytovec is None or cytovec == '') and patient.get('cytoIpssr') is not None:
        cytovec = cytovec_map.get(patient['cytoIpssr'])
    if cytovec is None or cytovec < 0 or cytovec > 4:
        raise ValueError('Cytogenetic category is not valid.')
    
    # Define variable breakpoints and corresponding ratings.
    bmblast_break = [-float('inf'), 2, 4.99, 10, float('inf')]
    hb_break      = [-float('inf'), 8, 10, float('inf')]
    plt_break     = [-float('inf'), 50, 100, float('inf')]
    anc_break     = [-float('inf'), 0.8, float('inf')]
    ipssrg_breaks = [-float('inf'), 1.5, 3, 4.5, 6, float('inf')]
    
    bmblast_map = [0, 1, 2, 3]
    hb_map      = [1.5, 1, 0]
    plt_map     = [1, 0.5, 0]
    anc_map     = [0.5, 0]
    
    bmblast = patient['bmblast']
    hb      = patient['hb']
    plt_val = patient['plt']
    anc     = patient['anc']
    
    bmblast_rating = cut_break(bmblast, bmblast_break, bmblast_map, right=True)
    hb_rating      = cut_break(hb, hb_break, hb_map, right=False)
    plt_rating     = cut_break(plt_val, plt_break, plt_map, right=False)
    anc_rating     = cut_break(anc, anc_break, anc_map, right=False)
    
    ipssr_raw = bmblast_rating + hb_rating + plt_rating + anc_rating + cytovec
    if rounding:
        ipssr_raw = round(ipssr_raw, rounding_digits)
    ipssr_category = cut_break(ipssr_raw, ipssrg_breaks, ipssrCat, right=True)
    ipssr_category = str(ipssr_category)
    
    # Compute age-adjusted IPSS-R score if age is provided.
    ipssra_raw = None
    ipssra_category = None
    if patient.get('age') is not None:
        age = patient['age']
        age_adjust = (float(age) - 70) * (0.05 - ipssr_raw * 0.005)
        ipssra_raw = ipssr_raw + age_adjust
        if rounding:
            ipssra_raw = round(ipssra_raw, rounding_digits)
        ipssra_category = cut_break(ipssra_raw, ipssrg_breaks, ipssrCat, right=True)
        ipssra_category = str(ipssra_category)
    
    return {
        "IPSSR_SCORE": ipssr_raw,
        "IPSSR_CAT": ipssr_category,
        "IPSSRA_SCORE": ipssra_raw,
        "IPSSRA_CAT": ipssra_category,
    }


def compute_ipssm(patient_values, rounding=True, rounding_digits=2, cutpoints=None):
    """
    Compute IPSS-M risk scores and risk categories.
    
    Parameters:
        patient_values (dict): Dictionary of patient input values. Each key is
                               expected to match a beta name. For the special beta
                               "Nres2", the corresponding value should be a dictionary
                               with keys "means", "worst", and "best".
        rounding (bool): Whether to round the risk score.
        rounding_digits (int): Number of digits to round to.
        cutpoints (list): List of cutoff values for risk categories.
                          Default is [-1.5, -0.5, 0, 0.5, 1.5].
    
    Returns:
        dict: {
            "means": {"riskScore": value, "riskCat": category, "contributions": { ... }},
            "worst": { ... },
            "best": { ... }
        }
    """
    if cutpoints is None:
        cutpoints = [-1.5, -0.5, 0, 0.5, 1.5]
    
    scores = {
        "means": {"riskScore": 0, "riskCat": "", "contributions": {}},
        "worst": {"riskScore": 0, "riskCat": "", "contributions": {}},
        "best":  {"riskScore": 0, "riskCat": "", "contributions": {}},
    }
    
    for scenario in scores.keys():
        contributions = {}
        for beta in betas:
            # Look up the patient value for this beta.
            value = patient_values.get(beta["name"])
            if value == "NA" or value is None:
                value = beta.get(scenario)
            if beta["name"] == "Nres2":
                # For "Nres2", expect a nested dictionary.
                value = patient_values.get("Nres2", {}).get(scenario)
            contribution = ((float(value) - beta["means"]) * beta["coeff"]) / math.log(2)
            contributions[beta["name"]] = contribution
        
        risk_score = sum(contributions.values())
        if rounding:
            risk_score = round(risk_score, rounding_digits)
        
        # Build breakpoints: [-inf] + cutpoints + [inf]
        risk_breaks = [-float('inf')] + cutpoints + [float('inf')]
        risk_cat = cut_break(risk_score, risk_breaks, ipssmCat, right=True)
        scores[scenario] = {
            "riskScore": risk_score,
            "riskCat": str(risk_cat),
            "contributions": contributions,
        }
    
    return scores


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example for IPSS-R
    # (Patient input keys match those expected by compute_ipssr.)
    patient_ipsr = {
        "bmblast": 3,         # Bone marrow blasts in %
        "hb": 9,              # Hemoglobin in g/dl
        "plt": 80,            # Platelet count in 1e9/l
        "anc": 1,             # Absolute neutrophil count in 1e9/l
        "cytoIpssr": "Poor",  # Cytogenetics provided as string
        "age": 65,            # Age in years (optional)
    }
    ipssr_result = compute_ipssr(patient_ipsr)
    print("IPSS-R Results:")
    print(ipssr_result)
    
    # Example for IPSS-M
    # (For a real case, patient_values should include all fields named in betas.)
    patient_ipsm = {
        "CYTOVEC": 0,
        "BLAST5": 0,
        "TRANSF_PLT100": 0,
        "HB1": 0,
        "SF3B1_alpha": 0,
        "SF3B1_5q": 0,
        "ASXL1": 0,
        "SRSF2": 0,
        "DNMT3A": 0,
        "RUNX1": 0,
        "U2AF1": 0,
        "EZH2": 0,
        "CBL": 0,
        "NRAS": 0,
        "IDH2": 0,
        "KRAS": 0,
        "MLL_PTD": 0,
        "ETV6": 0,
        "NPM1": 0,
        "TP53multi": 0,
        "FLT3": 0,
        # For Nres2, we use a nested dictionary providing values for each scenario:
        "Nres2": {"means": 0, "worst": 0, "best": 0},
    }
    ipssm_result = compute_ipssm(patient_ipsm)
    print("\nIPSS-M Results:")
    print(ipssm_result)
