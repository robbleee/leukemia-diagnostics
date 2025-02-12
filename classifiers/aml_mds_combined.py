import json
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022

##############################
# COMBINED CLASSIFIER ICC 2022
##############################
def classify_combined_ICC2022(parsed_data: dict) -> tuple:
    """
    First attempts AML classification using ICC 2022 criteria.
    If the AML ICC classifier indicates the case is "Not AML, consider MDS classification",
    then the MDS ICC classifier is called and its result is returned.
    
    Args:
        parsed_data (dict): A dictionary containing extracted hematological report data.
    
    Returns:
        tuple: (classification (str), derivation (list of str))
    """
    # Call the AML ICC classifier first.
    aml_icc_classification, aml_icc_derivation = classify_AML_ICC2022(parsed_data)
    
    # If the AML ICC classification suggests that the case is not AML,
    # then call the MDS ICC classifier.
    if "Not AML" in aml_icc_classification:
        mds_icc_classification, mds_icc_derivation = classify_MDS_ICC2022(parsed_data)
        combined_derivation = (
            aml_icc_derivation +
            ["AML ICC classifier indicated that the case is not AML. Switching to MDS ICC classification..."] +
            mds_icc_derivation
        )
        return mds_icc_classification, combined_derivation
    else:
        # Otherwise, return the AML ICC result.
        return aml_icc_classification, aml_icc_derivation


##############################
# COMBINED CLASSIFIER WHO 2022
##############################
def classify_combined_WHO2022(parsed_data: dict) -> tuple:
    """
    First attempts AML classification using WHO 2022 criteria.
    If the AML classifier indicates the case is "Not AML, consider MDS classification",
    then the MDS classifier is called and its result is returned.
    
    Args:
        parsed_data (dict): A dictionary containing extracted report data.
    
    Returns:
        tuple: A tuple of (classification (str), derivation (list of str))
    """
    # Call the AML classifier first.
    aml_classification, aml_derivation = classify_AML_WHO2022(parsed_data)
    
    # If AML classifier suggests it's not AML (e.g. "Not AML, consider MDS classification"),
    # then call the MDS classifier.
    if "Not AML" in aml_classification:
        mds_classification, mds_derivation = classify_MDS_WHO2022(parsed_data)
        # Optionally, combine derivation steps:
        combined_derivation = (
            aml_derivation +
            ["AML classifier indicated that the case is not AML. Switching to MDS classification..."] +
            mds_derivation
        )
        return mds_classification, combined_derivation
    else:
        # Otherwise, return the AML classification result.
        return aml_classification, aml_derivation
