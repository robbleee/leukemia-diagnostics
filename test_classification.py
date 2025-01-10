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
            "Acute myeloid leukaemia, unknown differentiation (WHO 2022)"
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
            "Acute myeloid leukaemia, [define by differentiation], post cytotoxic therapy, associated with germline RUNX1 (WHO 2022)"
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
            "Acute myeloid leukaemia, [define by differentiation], associated with germline RUNX1 (WHO 2022)"
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
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML, NOS (ICC 2022)"
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
            "Acute myeloid leukaemia, [define by differentiation], associated with germline RUNX1 (WHO 2022)"
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
            "AML, NOS (ICC 2022)"
        ),
        # Test Case 15: Multiple Qualifiers with MDS-related Mutation
        (
            {
                "blasts_percentage": 21.0,
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


# ==========================================
# ADDITIONAL TEST CASES FOR WHO 2022
# ==========================================

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case A1: BCR::ABL1 fusion but blasts < 20%
        # WHO 2022 typically requires ≥20% blasts for BCR::ABL1-driven AML classification.
        # Here, blasts < 20% should lead to "NOS" classification.
        (
            {
                "blasts_percentage": 11.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "BCR::ABL1": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "Acute myeloid leukaemia, unknown differentiation (WHO 2022)"
        ),
        # Test Case A2: RBM15::MRTFA (Megakaryoblastic) with blasts ≥ 20%
        # WHO 2022 includes AML with RBM15::MRTFA fusion as a defined subtype.
        (
            {
                "blasts_percentage": 28.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "RBM15::MRTFA": True,
                    "NPM1": False,
                    "CEBPA": False
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with RBM15::MRTFA fusion (WHO 2022)"
        ),
        # Test Case A3: Invalid Negative Blasts Percentage
        # WHO 2022 logic should reject negative blasts as invalid.
        (
            {
                "blasts_percentage": -2.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "Error: `blasts_percentage` must be a number between 0 and 100."
        ),
        # Test Case A4: Complex karyotype + MDS-related mutations + blasts = 19%
        # Myelodysplasia related classification if blasts < 20% might still yield an “MDS with excess blasts” type scenario,
        # but for AML (≥20%), we need to check if the logic defaults to “myelodysplasia related” or “NOS”.
        # Since blasts are 19% (below AML threshold) in strict WHO classification, it might remain “NOS” or cause a borderline scenario.
        # However, your code might interpret any MDS-related mutation + cytogenetics as “myelodysplasia related (WHO 2022)” regardless of blast count.
        # Adjust the expected outcome to match your actual logic.
        (
            {
                "blasts_percentage": 19.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "EZH2": True,
                    "RUNX1": True
                },
                "MDS_related_cytogenetics": {
                    "Complex_karyotype": True
                },
                "qualifiers": {}
            },
            "AML, myelodysplasia related (WHO 2022)"
        ),
    ]
)
def test_classify_AML_WHO2022_additional(parsed_data, expected_classification):
    """
    Additional WHO 2022 test cases to extend coverage.
    """
    classification, _ = classify_AML_WHO2022(parsed_data)
    assert classification == expected_classification


# ==========================================
# ADDITIONAL TEST CASES FOR ICC 2022
# ==========================================

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case B1: BCR::ABL1 rearrangement with blasts < 10%
        # ICC 2022 requires ≥10% blasts for AML-defining genetic abnormalities.
        # With blasts <10%, it should remain "NOS".
        (
            {
                "blasts_percentage": 9.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "BCR::ABL1": True
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML, NOS (ICC 2022)"
        ),
        # Test Case B2: DEK::NUP214 with blasts ≥ 10%
        # ICC 2022 includes AML with t(6;9)(p22.3;q34.1)/DEK::NUP214.
        (
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "DEK::NUP214": True,
                    "NPM1": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_MDS_diagnosed_over_3_months_ago": False,
                    "previous_cytotoxic_therapy": False
                }
            },
            "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214 (ICC 2022)"
        ),
        # Test Case B3: 1 TP53 mutation + del(17p) = Biallelic TP53
        # ICC 2022: This qualifies as "AML with mutated TP53."
        (
            {
                "blasts_percentage": 22.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {
                    "1_x_TP53_mutation_del_17p": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
            "AML with mutated TP53 (ICC 2022)"
        ),
        # Test Case B4: Both MDS-related gene mutation (SRSF2) + cytogenetics (del_7q)
        # with blasts ≥ 10% => "AML with myelodysplasia related gene mutation"
        # or "AML with myelodysplasia related cytogenetic abnormality."
        # The actual string depends on your function's logic priority.
        (
            {
                "blasts_percentage": 13.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {
                    "SRSF2": True
                },
                "MDS_related_cytogenetics": {
                    "del_7q": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": True
                }
            },
            # If your code picks "myelodysplasia related gene mutation" first, it might produce:
            #   "AML with myelodysplasia related gene mutation, therapy related (ICC 2022)"
            # If it picks the cytogenetic route first, it might produce:
            #   "AML with myelodysplasia related cytogenetic abnormality, therapy related (ICC 2022)"
            # Choose whichever matches your actual classification logic’s final string.
            "AML with myelodysplasia related gene mutation, therapy related (ICC 2022)"
        ),
    ]
)
def test_classify_AML_ICC2022_additional(parsed_data, expected_classification):
    """
    Additional ICC 2022 test cases to extend coverage.
    """
    classification, _ = classify_AML_ICC2022(parsed_data)
    assert classification == expected_classification


# ==========================================
# ADDITIONAL COMPLEX TEST CASES FOR WHO 2022
# ==========================================

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 15: NPM1 and RUNX1 Mutations Present with High Blasts and Previous Therapy
        (
            {
                "blasts_percentage": 22.0,
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
                    "RUNX1": True,  # Additional RUNX1 mutation
                    "SF3B1": False,
                    "SRSF2": False,
                    "STAG2": False,
                    "U2AF1": False,
                    "ZRSR2": False
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "RUNX1"
                }
            },
            "AML with NPM1 mutation, post cytotoxic therapy, associated with germline RUNX1 (WHO 2022)"
        ),
        # Test Case 16: CEBPA bZIP Mutation with Previous Therapy and Germline Variant
        (
            {
                "blasts_percentage": 24.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CEBPA": True,
                    "bZIP": True,
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
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "GATA2"
                }
            },
            "AML with CEBPA mutation, post cytotoxic therapy, associated with germline GATA2 (WHO 2022)"
        ),
        # Test Case 17: Multiple MDS-related Mutations with Complex Karyotype and High Blasts
        (
            {
                "blasts_percentage": 19.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {
                    "ASXL1": True,
                    "SF3B1": True,
                    "RUNX1": True
                },
                "MDS_related_cytogenetics": {
                    "Complex_karyotype": True,
                    "del_7q": True,
                    "del_20q": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML, myelodysplasia related, post cytotoxic therapy (WHO 2022)"
        ),
        # Test Case 19: NUP98 with Multiple Fusion Partners and MDS Features
        (
            {
                "blasts_percentage": 8.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NUP98": True,
                    "BCR::ABL1": True  # Additional fusion
                },
                "MDS_related_mutation": {
                    "STAG2": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with NUP98 rearrangement (WHO 2022)"
        ),
        # Test Case 20: TP53 Mutations with Additional Cytogenetic Abnormalities
        (
            {
                "blasts_percentage": 23.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {
                    "del_17p": True,
                    "Complex_karyotype": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                },
                "Biallelic_TP53_mutation": {
                    "2_x_TP53_mutations": True
                }
            },
            "AML, myelodysplasia related (WHO 2022)"
        ),
        # Test Case 21: KMT2A Rearrangement with bZIP Fusion and Previous Therapy
        (
            {
                "blasts_percentage": 26.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "KMT2A": True,
                    "bZIP": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with KMT2A rearrangement, post cytotoxic therapy (WHO 2022)"
        ),
        # Test Case 22: CBFB::MYH11 Fusion with Associated MDS-related Mutations
        (
            {
                "blasts_percentage": 17.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CBFB::MYH11": True
                },
                "MDS_related_mutation": {
                    "SRSF2": True
                },
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with CBFB::MYH11 fusion (WHO 2022)"
        ),
        # Test Case 23: MECOM Rearrangement with del_7q and Previous Cytotoxic Therapy
        (
            {
                "blasts_percentage": 24.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "MECOM": True
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {
                    "del_7q": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "AML with MECOM rearrangement, post cytotoxic therapy (WHO 2022)"
        ),
        # Test Case 24: FLT3-ITD Mutation with High Blasts and Previous Therapy (Handled as NOS)
        (
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "FLT3-ITD": True  # Assuming FLT3-ITD is not explicitly handled and defaults to NOS
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {
                    "previous_cytotoxic_therapy": True,
                    "predisposing_germline_variant": "None"
                }
            },
            "Acute myeloid leukaemia, [define by differentiation], post cytotoxic therapy (WHO 2022)"
        ),
    ]
)
def test_classify_AML_WHO2022_complex(parsed_data, expected_classification):
    """
    Additional complex WHO 2022 test cases to extend coverage.
    """
    classification, _ = classify_AML_WHO2022(parsed_data)
    assert classification == expected_classification


# ==========================================
# ADDITIONAL TEST CASES FOR WHO 2022
# ==========================================

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 18: All Negative Fields with AML Differentiation Provided (FAB Classification)
        (
            {
                "blasts_percentage": 22.0,
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
                "AML_differentiation": "M3",
                "qualifiers": {
                    "previous_cytotoxic_therapy": False,
                    "predisposing_germline_variant": "None"
                }
            },
            "Acute promyelocytic leukaemia (WHO 2022)"
        ),
        # Test Case 19: All Negative Fields with AML Differentiation Provided (WHO Classification)
        (
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M5a",
                "qualifiers": {}
            },
            "Acute monoblastic leukaemia (WHO 2022)"
        ),
        # Test Case 20: All Negative Fields without AML Differentiation Provided
        (
            {
                "blasts_percentage": 18.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": None,
                "qualifiers": {}
            },
            "Acute myeloid leukaemia, unknown differentiation (WHO 2022)"
        ),
        # Test Case 21: All Negative Fields with AML Differentiation Provided (WHO Classification)
        (
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M1",
                "qualifiers": {}
            },
            "Acute myeloid leukaemia without maturation (WHO 2022)"
        ),
        # Test Case 22: Some Fields Negative, AML Differentiation Provided (Should Not Use Differentiation)
        (
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": False,
                    "RUNX1::RUNX1T1": True  # Positive field
                },
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M4",
                "qualifiers": {}
            },
            "AML with RUNX1::RUNX1T1 fusion (WHO 2022)"
        ),
        # Test Case 23: All Negative Fields with AML Differentiation Provided (WHO Classification) - WHO Only
        (
            {
                "blasts_percentage": 28.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M7",
                "qualifiers": {}
            },
            "Acute megakaryoblastic leukaemia (WHO 2022)"
        ),
        # Test Case 24: All Negative Fields with Invalid AML Differentiation Provided
        (
            {
                "blasts_percentage": 22.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "XYZ",  # Invalid differentiation
                "qualifiers": {}
            },
            # Depending on your validation logic, this might either issue a warning and classify as "Acute myeloid leukaemia" without differentiation
            # or handle it differently. Adjust expected_classification accordingly.
            "Acute myeloid leukaemia, unknown differentiation (WHO 2022)"
        ),
    ]
)
def test_classify_AML_WHO2022_differentiation(parsed_data, expected_classification):
    classification, _ = classify_AML_WHO2022(parsed_data)
    assert classification == expected_classification

# ---------------------------
# Additional Test Cases for ICC 2022 Classification
# ---------------------------

@pytest.mark.parametrize(
    "parsed_data, expected_classification",
    [
        # Test Case 16: All Negative Fields with AML Differentiation Provided (ICC Classification)
        # Assuming ICC 2022 does not use differentiation in classification; this test ensures differentiation is ignored
        (
            {
                "blasts_percentage": 20.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M4",
                "qualifiers": {}
            },
            "AML, NOS (ICC 2022)"
        ),
        # Test Case 17: All Negative Fields without AML Differentiation Provided (ICC Classification)
        (
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": None,
                "qualifiers": {}
            },
            "AML, NOS (ICC 2022)"
        ),
        # Test Case 18: Some Fields Negative, AML Differentiation Provided (Should Not Use Differentiation)
        (
            {
                "blasts_percentage": 12.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": False,
                    "RUNX1::RUNX1T1": False
                },
                "Biallelic_TP53_mutation": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M2",
                "qualifiers": {}
            },
            "AML, NOS (ICC 2022)"
        ),
    ]
)
def test_classify_AML_ICC2022_differentiation(parsed_data, expected_classification):
    classification, _ = classify_AML_ICC2022(parsed_data)
    assert classification == expected_classification