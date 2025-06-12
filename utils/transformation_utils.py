"""
Utility functions for transforming data between parser formats.
"""

def transform_main_parser_to_treatment_format(main_parser_data: dict) -> dict:
    """
    Transform data from the main AML parser format to the treatment parser format.
    This is a fallback function when the specialized treatment parser is not used.
    
    Args:
        main_parser_data (dict): Data from the main AML parser
        
    Returns:
        dict: Data in treatment parser format
    """
    treatment_data = {
        "qualifiers": {
            "therapy_related": False,
            "previous_chemotherapy": False,
            "previous_radiotherapy": False,
            "previous_MDS": False,
            "previous_MPN": False,
            "previous_MDS/MPN": False,
            "previous_CMML": False,
            "relapsed": False,
            "refractory": False,
            "secondary": False
        },
        "cd33_positive": None,  # Not available in main parser
        "cd33_percentage": None,  # Not available in main parser
        "AML_defining_recurrent_genetic_abnormalities": {
            "RUNX1_RUNX1T1": False,
            "t_8_21": False,
            "CBFB_MYH11": False,
            "inv_16": False,
            "t_16_16": False,
            "NPM1_mutation": False,
            "FLT3_ITD": False,
            "FLT3_TKD": False,
            "PML_RARA": False
        },
        "MDS_related_mutation": {
            "FLT3": False,
            "ASXL1": False,
            "BCOR": False,
            "EZH2": False,
            "RUNX1": False,
            "SF3B1": False,
            "SRSF2": False,
            "STAG2": False,
            "U2AF1": False,
            "ZRSR2": False,
            "UBA1": False,
            "JAK2": False
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype": False,
            "-5": False,
            "del_5q": False,
            "-7": False,
            "del_7q": False,
            "-17": False,
            "del_17p": False
        },
        "number_of_dysplastic_lineages": None,
        "no_cytogenetics_data": False
    }
    
    # Map qualifiers from main parser to treatment format
    qualifiers = main_parser_data.get("qualifiers", {})
    
    # Map previous conditions
    if qualifiers.get("previous_MDS_diagnosed_over_3_months_ago"):
        treatment_data["qualifiers"]["previous_MDS"] = True
    if qualifiers.get("previous_MPN_diagnosed_over_3_months_ago"):
        treatment_data["qualifiers"]["previous_MPN"] = True
    if qualifiers.get("previous_MDS/MPN_diagnosed_over_3_months_ago"):
        treatment_data["qualifiers"]["previous_MDS/MPN"] = True
    
    # Map therapy-related status
    previous_cytotoxic = qualifiers.get("previous_cytotoxic_therapy")
    if previous_cytotoxic and previous_cytotoxic != "None":
        treatment_data["qualifiers"]["therapy_related"] = True
        treatment_data["qualifiers"]["previous_chemotherapy"] = True
    
    # Map AML-defining genetic abnormalities
    aml_genes = main_parser_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    
    # Direct mappings
    if aml_genes.get("PML::RARA"):
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["PML_RARA"] = True
    if aml_genes.get("NPM1"):
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["NPM1_mutation"] = True
    if aml_genes.get("RUNX1::RUNX1T1"):
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["RUNX1_RUNX1T1"] = True
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["t_8_21"] = True
    if aml_genes.get("CBFB::MYH11"):
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["CBFB_MYH11"] = True
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["inv_16"] = True
    
    # Map FLT3 from ELN2024 genes
    eln2024_genes = main_parser_data.get("ELN2024_risk_genes", {})
    if eln2024_genes.get("FLT3_ITD"):
        treatment_data["AML_defining_recurrent_genetic_abnormalities"]["FLT3_ITD"] = True
        treatment_data["MDS_related_mutation"]["FLT3"] = True
    
    # Map general FLT3 from AML genes
    if aml_genes.get("FLT3"):
        treatment_data["MDS_related_mutation"]["FLT3"] = True
    
    # Map MDS-related mutations (direct copy)
    mds_mutations = main_parser_data.get("MDS_related_mutation", {})
    for gene in treatment_data["MDS_related_mutation"]:
        if gene in mds_mutations:
            treatment_data["MDS_related_mutation"][gene] = mds_mutations[gene]
    
    # Map MDS-related cytogenetics
    mds_cyto = main_parser_data.get("MDS_related_cytogenetics", {})
    
    # Direct mappings where field names match
    direct_cyto_mappings = {
        "Complex_karyotype": "Complex_karyotype",
        "del_5q": "del_5q",
        "-7": "-7",
        "del_7q": "del_7q",
        "-17": "-17",
        "del_17p": "del_17p"
    }
    
    for treatment_field, main_field in direct_cyto_mappings.items():
        if mds_cyto.get(main_field):
            treatment_data["MDS_related_cytogenetics"][treatment_field] = True
    
    # Map monosomy 5 (different field names)
    if mds_cyto.get("del_5q") or mds_cyto.get("t_5q") or mds_cyto.get("add_5q"):
        treatment_data["MDS_related_cytogenetics"]["-5"] = True
    
    # Copy other fields
    treatment_data["number_of_dysplastic_lineages"] = main_parser_data.get("number_of_dysplastic_lineages")
    treatment_data["no_cytogenetics_data"] = main_parser_data.get("no_cytogenetics_data", False)
    
    return treatment_data 