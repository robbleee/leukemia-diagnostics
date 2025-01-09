# test_classification.py

import pytest
from app import classify_AML_WHO2022, classify_AML_ICC2022

# ---------------------------
# Test Cases for WHO 2022 Classification
# ---------------------------

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 1: NPM1 Mutation
        (
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True,
                    "RUNX1::RUNX1T1": False,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "CEBPA": False,
                    "bZIP": False,
                    "BCR::ABL1": False
                },
                "MDS_related_mutation": {
                    "ASXL1": False,
                    "BCOR": False,
                    "EZH2": False,
                    "RUNX1": False,
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {
                    "Complex_karyotype": False,
                    "del_5q": False,
                    "t_5q": False,
                    "add_5q": False,
                    "-7": False,
                    "del_7q": False,
                    "+8": False,
                    "del_11q": False,
                    "del_12p": False,
                    "t_12p": False,
                    "add_12p": False,
                    "-13": False,
                    "i_17q": False,
                    "-17": False,
                    "add_17p": False,
                    "del_17p": False,
                    "del_20q": False,
                    "idic_X_q13": False,
                    "5q": False
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with NPM1 mutation (WHO 2022)"
        ),
        # Test Case 2: RUNX1::RUNX1T1 Fusion
        (
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": False,
                    "RUNX1::RUNX1T1": True,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "CEBPA": False,
                    "bZIP": False,
                    "BCR::ABL1": False
                },
                "MDS_related_mutation": {
                    "ASXL1": False,
                    "BCOR": False,
                    "EZH2": False,
                    "RUNX1": False,
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with RUNX1::RUNX1T1 fusion, post cytotoxic therapy (WHO 2022)"
        ),
        # Test Case 3: MDS-related Mutation (ASXL1)
        (
            {
                "blasts_percentage": 5.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "CEBPA": False,
                    "bZIP": False,
                    "BCR::ABL1": False
                },
                "MDS_related_mutation": {
                    "ASXL1": True,
                    "BCOR": False,
                    "EZH2": False,
                    "RUNX1": False,
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML, myelodysplasia related (WHO 2022)"
        ),
        # Test Case 4: MDS-related Cytogenetics (del_5q)
        (
            {
                "blasts_percentage": 8.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "ASXL1": False,
                    "BCOR": False,
                    "EZH2": False,
                    "RUNX1": False,
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {
                    "del_5q": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML, myelodysplasia related (WHO 2022)"
        ),
        # Test Case 5: CEBPA Mutation with blasts_percentage >= 20%
        (
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CEBPA": True,
                    "bZIP": False,
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "BCR::ABL1": False
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "GATA2"
                }
            },
            "AML with CEBPA mutation, associated with germline GATA2 (WHO 2022)"
        ),
        # Test Case 6: CEBPA Mutation with blasts_percentage < 20% (should not apply)
        (
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CEBPA": True,
                    "bZIP": False,
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "BCR::ABL1": False
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML, Not Otherwise Specified (NOS) (WHO 2022)"
        ),
        # Test Case 7: MDS-related Mutation with Qualifiers
        (
            {
                "blasts_percentage": 10.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "ASXL1": True,
                    "BCOR": False,
                    "EZH2": False,
                    "RUNX1": False,
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML, myelodysplasia related, post cytotoxic therapy (WHO 2022)"
        ),
        # Test Case 8: Multiple Genetic Abnormalities (only first should apply)
        (
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True,
                    "RUNX1::RUNX1T1": True,  # Should not be classified as RUNX1::RUNX1T1 since NPM1 is checked first
                    "CBFB::MYH11": False
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML with NPM1 mutation (WHO 2022)"
        ),
        # Test Case 9: No Genetic Abnormalities, No MDS Features, with qualifiers
        (
            {
                "blasts_percentage": 5.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML, Not Otherwise Specified (NOS), post cytotoxic therapy, associated with germline RUNX1 (WHO 2022)"
        ),
        # Test Case 10: Boundary Condition - CEBPA Mutation with blasts_percentage exactly 20%
        (
            {
                "blasts_percentage": 20.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CEBPA": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML with CEBPA mutation (WHO 2022)"
        ),
        # Test Case 11: Multiple Qualifiers with MDS-related Mutation
        (
            {
                "blasts_percentage": 7.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "ASXL1": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "GATA2"
                }
            },
            "AML, myelodysplasia related, post cytotoxic therapy, associated with germline GATA2 (WHO 2022)"
        ),
        # Test Case 12: Missing Keys in parsed_data
        (
            {
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True
                }
                # Missing "MDS_related_mutation", "MDS_related_cytogenetics", and "qualifiers"
            },
            "Error: `blasts_percentage` is missing. Please provide this information for classification."
        ),
        # Test Case 13: Predisposing Germline Variant Only
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "predisposing_germline_variant": "RUNX1",
                    "previous_cytotoxic_therapy": False
                }
            },
            "AML, Not Otherwise Specified (NOS), associated with germline RUNX1 (WHO 2022)"
        ),
        # Test Case 14: All Qualifiers Present with Genetic Abnormality
        (
            {
                "blasts_percentage": 22.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True,
                    "CEBPA": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML with NPM1 mutation, post cytotoxic therapy, associated with germline RUNX1 (WHO 2022)"
        ),
    ]
)
def test_classify_AML_WHO2022(parsed_data, expected_classification):
    classification, _ = classify_AML_WHO2022(parsed_data)
    assert classification == expected_classification

# ---------------------------
# Test Cases for ICC 2022 Classification
# ---------------------------

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 1: NPM1 Mutation with blasts_percentage >= 10%
        (
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True,
                    "RUNX1::RUNX1T1": False,
                    "CBFB::MYH11": False,
                    "DEK::NUP214": False,
                    "RBM15::MRTFA": False,
                    "KMT2A": False,
                    "MECOM": False,
                    "NUP98": False,
                    "bZIP": False,
                    "BCR::ABL1": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with mutated NPM1 (ICC 2022)"
        ),
        # Test Case 2: RUNX1::RUNX1T1 Fusion with blasts_percentage >= 10%
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "RUNX1::RUNX1T1": True,
                    "NPM1": False,
                    "CBFB::MYH11": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1 (ICC 2022)"
        ),
        # Test Case 3: KMT2A Rearrangement with blasts_percentage >= 10%
        (
            {
                "blasts_percentage": 20.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "KMT2A": True,
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with other KMT2A rearrangements, therapy related (ICC 2022)"
        ),
        # Test Case 4: BCR::ABL1 Fusion with blasts_percentage >= 10%
        (
            {
                "blasts_percentage": 18.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "BCR::ABL1": True,
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1 (ICC 2022)"
        ),
        # Test Case 5: Biallelic TP53 Mutations
        (
            {
                "blasts_percentage": 5.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {
                    "2_x_TP53_mutations": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with mutated TP53, therapy related (ICC 2022)"
        ),
        # Test Case 6: MDS-related Mutation (ASXL1)
        (
            {
                "blasts_percentage": 8.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {
                    "ASXL1": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with myelodysplasia related gene mutation (ICC 2022)"
        ),
        # Test Case 7: MDS-related Cytogenetics (del_7q)
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {
                    "del_7q": True
                },
                "qualifiers": {
                    "previous_MDS_diagnosed_over_3_months_ago": True,
                    "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with myelodysplasia related cytogenetic abnormality, post MDS (ICC 2022)"
        ),
        # Test Case 8: 5q Cytogenetic Abnormality (AML, NOS)
        (
            {
                "blasts_percentage": 7.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {
                    "5q": True
                },
                "qualifiers": {}
            },
            "AML, NOS (ICC 2022)"
        ),
        # Test Case 9: No Genetic Abnormalities, No MDS Features, with qualifiers
        (
            {
                "blasts_percentage": 3.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_MDS_diagnosed_over_3_months_ago": False,
                    "previous_MDS/MPN_diagnosed_over_3_months_ago": False,
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML, Not Otherwise Specified (NOS), therapy related (ICC 2022)"
        ),
        # Test Case 10: Multiple Genetic Abnormalities (only first should apply)
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NUP98": True,
                    "BCR::ABL1": True
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML with NUP98 and other partners (ICC 2022)"
        ),
    ]
)
def test_classify_AML_ICC2022(parsed_data, expected_classification):
    classification, _ = classify_AML_ICC2022(parsed_data)
    assert classification == expected_classification

# ---------------------------
# Additional Test Cases (Edge Cases) for WHO 2022 Classification
# ---------------------------

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 11: No data provided
        (
            {},
            "Error: `blasts_percentage` is missing. Please provide this information for classification."
        ),
        # Test Case 12: All possible qualifiers present
        (
            {
                "blasts_percentage": 20.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML with NPM1 mutation, post cytotoxic therapy, associated with germline RUNX1 (WHO 2022)"
        ),
        # Test Case 13: Predisposing Germline Variant Only
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "predisposing_germline_variant": "RUNX1",
                    "previous_cytotoxic_therapy": False
                }
            },
            "AML, Not Otherwise Specified (NOS), associated with germline RUNX1 (WHO 2022)"
        ),
        # Test Case 14: Multiple Qualifiers with MDS-related Mutation
        (
            {
                "blasts_percentage": 7.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "ASXL1": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "GATA2"
                }
            },
            "AML, myelodysplasia related, post cytotoxic therapy, associated with germline GATA2 (WHO 2022)"
        ),
        # Test Case 15: Boundary Condition - CEBPA Mutation with blasts_percentage exactly 20%
        (
            {
                "blasts_percentage": 20.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CEBPA": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML with CEBPA mutation (WHO 2022)"
        ),
        # Test Case 16: Missing Keys in parsed_data
        (
            {
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True
                }
                # Missing "MDS_related_mutation", "MDS_related_cytogenetics", and "qualifiers"
            },
            "Error: `blasts_percentage` is missing. Please provide this information for classification."
        ),
    ]
)
def test_classify_AML_WHO2022_edge_cases(parsed_data, expected_classification):
    classification, _ = classify_AML_WHO2022(parsed_data)
    assert classification == expected_classification

# ---------------------------
# Additional Test Cases (Edge Cases) for ICC 2022 Classification
# ---------------------------

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 11: No data provided
        (
            {},
            "Error: `blasts_percentage` is missing. Please provide this information for classification."
        ),
        # Test Case 12: All possible qualifiers present
        (
            {
                "blasts_percentage": 18.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "BCR::ABL1": True
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_MDS_diagnosed_over_3_months_ago": True,
                    "previous_MDS/MPN_diagnosed_over_3_months_ago": True,
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1, post MDS/MPN, therapy related (ICC 2022)"
        ),
        # Test Case 13: Invalid Data - Negative blasts_percentage
        (
            {
                "blasts_percentage": -5.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "Error: `blasts_percentage` must be a number between 0 and 100."
        ),
        # Test Case 14: Predisposing Germline Variant Only
        (
            {
                "blasts_percentage": 14.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "predisposing_germline_variant": "RUNX1",
                    "previous_cytotoxic_therapy": False
                }
            },
            "AML, Not Otherwise Specified (NOS) (ICC 2022)"
        ),
        # Test Case 15: Multiple Qualifiers with MDS-related Mutation
        (
            {
                "blasts_percentage": 9.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {
                    "RUNX1": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "GATA2"
                }
            },
            "AML with myelodysplasia related gene mutation, therapy related (ICC 2022)"
        ),
    ]
)
def test_classify_AML_ICC2022_edge_cases(parsed_data, expected_classification):
    classification, _ = classify_AML_ICC2022(parsed_data)
    assert classification == expected_classification
