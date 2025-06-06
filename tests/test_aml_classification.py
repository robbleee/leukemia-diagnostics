"""
Comprehensive test suite for AML (Acute Myeloid Leukemia) classification functions.

This test suite covers:
1. AML WHO 2022 classification (classify_AML_WHO2022)
2. AML ICC 2022 classification (classify_AML_ICC2022)

Tests include:
- Basic classification scenarios (positive cases)
- AML-defining genetic abnormalities
- MDS-related features
- FAB differentiation subtypes
- Qualifiers (therapy, germline variants, progression)
- Edge cases and boundary conditions
- Complex scenarios with multiple features
- Error handling and robustness
"""

import pytest
import sys
import os
import time
import threading

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022


class TestAMLWHO2022BasicClassification:
    """Test suite for basic AML WHO 2022 classification scenarios."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: APL with PML::RARA
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "PML::RARA": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "Acute promyelocytic leukaemia with PML::RARA fusion (WHO 2022)"
            ),
            # Test Case 2: AML with NPM1 mutation
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True,
                        "PML::RARA": False
                    },
                    "qualifiers": {}
                },
                "AML with NPM1 mutation (WHO 2022)"
            ),
            # Test Case 3: AML with RUNX1::RUNX1T1 fusion
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RUNX1::RUNX1T1": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with RUNX1::RUNX1T1 fusion (WHO 2022)"
            ),
            # Test Case 4: AML with CBFB::MYH11 fusion
            (
                {
                    "blasts_percentage": 40.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CBFB::MYH11": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with CBFB::MYH11 fusion (WHO 2022)"
            ),
            # Test Case 5: AML with DEK::NUP214 fusion
            (
                {
                    "blasts_percentage": 45.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "DEK::NUP214": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with DEK::NUP214 fusion (WHO 2022)"
            ),
            # Test Case 6: AML with RBM15::MRTFA fusion
            (
                {
                    "blasts_percentage": 50.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RBM15::MRTFA": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with RBM15::MRTFA fusion (WHO 2022)"
            ),
            # Test Case 7: AML with KMT2A rearrangement (MLLT3::KMT2A)
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MLLT3::KMT2A": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with KMT2A rearrangement (WHO 2022)"
            ),
            # Test Case 8: AML with MECOM rearrangement (GATA2::MECOM)
            (
                {
                    "blasts_percentage": 33.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "GATA2:: MECOM": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with MECOM rearrangement (WHO 2022)"
            ),
            # Test Case 9: AML with KMT2A rearrangement (general)
            (
                {
                    "blasts_percentage": 38.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "KMT2A": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with KMT2A rearrangement (WHO 2022)"
            ),
            # Test Case 10: AML with MECOM rearrangement (general)
            (
                {
                    "blasts_percentage": 42.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MECOM": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with MECOM rearrangement (WHO 2022)"
            ),
            # Test Case 11: AML with NUP98 rearrangement
            (
                {
                    "blasts_percentage": 26.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NUP98": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with NUP98 rearrangement (WHO 2022)"
            ),
            # Test Case 12: AML with CEBPA mutation (≥20% blasts)
            (
                {
                    "blasts_percentage": 22.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CEBPA": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with CEBPA mutation (WHO 2022)"
            ),
            # Test Case 13: AML with bZIP CEBPA mutation (≥20% blasts)
            (
                {
                    "blasts_percentage": 24.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "bZIP": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with CEBPA mutation (WHO 2022)"
            ),
            # Test Case 14: AML with BCR::ABL1 fusion (≥20% blasts)
            (
                {
                    "blasts_percentage": 27.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "BCR::ABL1": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with BCR::ABL1 fusion (WHO 2022)"
            ),
        ]
    )
    def test_aml_defining_genetic_abnormalities_who2022(self, parsed_data, expected_classification):
        """Test AML WHO 2022 classification with AML-defining genetic abnormalities."""
        result, derivation = classify_AML_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
        assert len(derivation) > 0
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: CEBPA mutation with <20% blasts (should not be AML)
            (
                {
                    "blasts_percentage": 15.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CEBPA": True,
                        "NPM1": False
                    }
                },
                "Not AML, consider MDS classification"
            ),
            # Test Case 2: bZIP mutation with <20% blasts (should not be AML)
            (
                {
                    "blasts_percentage": 18.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "bZIP": True,
                        "NPM1": False
                    }
                },
                "Not AML, consider MDS classification"
            ),
            # Test Case 3: BCR::ABL1 fusion with <20% blasts (should not be AML)
            (
                {
                    "blasts_percentage": 12.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "BCR::ABL1": True,
                        "NPM1": False
                    }
                },
                "Not AML, consider MDS classification"
            ),
            # Test Case 4: AML, myelodysplasia related (MDS-related mutations)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {
                        "ASXL1": True,
                        "SF3B1": False
                    },
                    "MDS_related_cytogenetics": {}
                },
                "AML, myelodysplasia related (WHO 2022)"
            ),
            # Test Case 5: AML, myelodysplasia related (MDS-related cytogenetics)
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True,
                        "del_5q": False
                    }
                },
                "AML, myelodysplasia related (WHO 2022)"
            ),
        ]
    )
    def test_aml_special_cases_who2022(self, parsed_data, expected_classification):
        """Test special AML WHO 2022 classification cases."""
        result, derivation = classify_AML_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLWHO2022FABDifferentiation:
    """Test suite for AML WHO 2022 FAB differentiation."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: M0 - Minimal differentiation
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M0"
                },
                "Acute myeloid leukaemia with minimal differentiation (WHO 2022)"
            ),
            # Test Case 2: M1 - Without maturation
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M1"
                },
                "Acute myeloid leukaemia without maturation (WHO 2022)"
            ),
            # Test Case 3: M2 - With maturation
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M2"
                },
                "Acute myeloid leukaemia with maturation (WHO 2022)"
            ),
            # Test Case 4: M3 - Promyelocytic
            (
                {
                    "blasts_percentage": 40.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M3"
                },
                "Acute promyelocytic leukaemia (WHO 2022)"
            ),
            # Test Case 5: M4 - Myelomonocytic
            (
                {
                    "blasts_percentage": 45.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M4"
                },
                "Acute myelomonocytic leukaemia (WHO 2022)"
            ),
            # Test Case 6: M4Eo - Myelomonocytic with eosinophilia
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M4Eo"
                },
                "Acute myelomonocytic leukaemia with eosinophilia (WHO 2022)"
            ),
            # Test Case 7: M5a - Monoblastic
            (
                {
                    "blasts_percentage": 32.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M5a"
                },
                "Acute monoblastic leukaemia (WHO 2022)"
            ),
            # Test Case 8: M5b - Monocytic
            (
                {
                    "blasts_percentage": 37.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M5b"
                },
                "Acute monocytic leukaemia (WHO 2022)"
            ),
            # Test Case 9: M6a - Erythroid leukaemia
            (
                {
                    "blasts_percentage": 42.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M6a"
                },
                "Acute Erythroid leukaemia (WHO 2022)"
            ),
            # Test Case 10: M6b - Pure erythroid leukaemia
            (
                {
                    "blasts_percentage": 26.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M6b"
                },
                "Acute Erythroid leukaemia (WHO 2022)"
            ),
            # Test Case 11: M7 - Megakaryoblastic
            (
                {
                    "blasts_percentage": 48.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M7"
                },
                "Acute megakaryoblastic leukaemia (WHO 2022)"
            ),
            # Test Case 12: M6a with not_erythroid flag (should skip erythroid override)
            (
                {
                    "blasts_percentage": 29.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M6a"
                },
                "Acute myeloid leukaemia, [define by differentiation] (WHO 2022)"
            ),
        ]
    )
    def test_fab_differentiation_who2022(self, parsed_data, expected_classification):
        """Test AML WHO 2022 FAB differentiation mapping."""
        # Test normal case vs not_erythroid case
        if "define by differentiation" in expected_classification:
            # Test with not_erythroid flag for M6a/M6b
            result, derivation = classify_AML_WHO2022(parsed_data, not_erythroid=True)
        else:
            result, derivation = classify_AML_WHO2022(parsed_data)
        
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLWHO2022Qualifiers:
    """Test suite for AML WHO 2022 qualifiers."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Previous cytotoxic therapy (Ionising radiation)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Ionising radiation"
                    }
                },
                "AML with NPM1 mutation, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 2: Previous cytotoxic therapy (Cytotoxic chemotherapy)
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RUNX1::RUNX1T1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy"
                    }
                },
                "AML with RUNX1::RUNX1T1 fusion, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 3: Previous cytotoxic therapy (Any combination)
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CBFB::MYH11": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Any combination"
                    }
                },
                "AML with CBFB::MYH11 fusion, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 4: Immune interventions (NOT accepted for WHO)
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Immune interventions"
                    }
                },
                "AML with NPM1 mutation (WHO 2022)"
            ),
            # Test Case 5: Germline predisposition (single variant)
            (
                {
                    "blasts_percentage": 40.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "DEK::NUP214": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "AML with DEK::NUP214 fusion, associated with RUNX1 (WHO 2022)"
            ),
            # Test Case 6: Multiple germline variants
            (
                {
                    "blasts_percentage": 33.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RBM15::MRTFA": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "GATA2, DDX41"
                    }
                },
                "AML with RBM15::MRTFA fusion, associated with GATA2, DDX41 (WHO 2022)"
            ),
            # Test Case 7: Diamond-Blackfan anemia (excluded for WHO)
            (
                {
                    "blasts_percentage": 26.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "Diamond-Blackfan anemia"
                    }
                },
                "AML with NPM1 mutation (WHO 2022)"
            ),
            # Test Case 8: Progressed from MDS
            (
                {
                    "blasts_percentage": 31.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "KMT2A": True
                    },
                    "qualifiers": {
                        "previous_MDS_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with KMT2A rearrangement, progressed from MDS (WHO 2022)"
            ),
            # Test Case 9: Progressed from MDS/MPN
            (
                {
                    "blasts_percentage": 38.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MECOM": True
                    },
                    "qualifiers": {
                        "previous_MDS/MPN_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with MECOM rearrangement, progressed from MDS (WHO 2022)"
            ),
            # Test Case 10: Progressed from MPN
            (
                {
                    "blasts_percentage": 44.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NUP98": True
                    },
                    "qualifiers": {
                        "previous_MPN_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with NUP98 rearrangement, progressed from MDS (WHO 2022)"
            ),
            # Test Case 11: Multiple qualifiers
            (
                {
                    "blasts_percentage": 27.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2",
                        "previous_MDS_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with NPM1 mutation, previous cytotoxic therapy, associated with GATA2, progressed from MDS (WHO 2022)"
            ),
        ]
    )
    def test_aml_who2022_qualifiers(self, parsed_data, expected_classification):
        """Test AML WHO 2022 classification with various qualifiers."""
        result, derivation = classify_AML_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLICC2022BasicClassification:
    """Test suite for basic AML ICC 2022 classification scenarios."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: APL with t(15;17)/PML::RARA
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "PML::RARA": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "APL with t(15;17)(q24.1;q21.2)/PML::RARA (ICC 2022)"
            ),
            # Test Case 2: AML with mutated NPM1
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True,
                        "PML::RARA": False
                    },
                    "qualifiers": {}
                },
                "AML with mutated NPM1 (ICC 2022)"
            ),
            # Test Case 3: AML with t(8;21)/RUNX1::RUNX1T1
            (
                {
                    "blasts_percentage": 15.0,  # ≥10% for ICC
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RUNX1::RUNX1T1": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1 (ICC 2022)"
            ),
            # Test Case 4: AML with inv(16)/CBFB::MYH11
            (
                {
                    "blasts_percentage": 12.0,  # ≥10% for ICC
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CBFB::MYH11": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11 (ICC 2022)"
            ),
            # Test Case 5: AML with t(6;9)/DEK::NUP214
            (
                {
                    "blasts_percentage": 18.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "DEK::NUP214": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214 (ICC 2022)"
            ),
            # Test Case 6: AML (megakaryoblastic) with t(1;22)/RBM15::MRTFA
            (
                {
                    "blasts_percentage": 22.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RBM15::MRTFA": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTFA (ICC 2022)"
            ),
            # Test Case 7: AML with t(9;11)/MLLT3::KMT2A
            (
                {
                    "blasts_percentage": 16.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MLLT3::KMT2A": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with t(9;11)(p21.3;q23.3)/MLLT3::KMT2A (ICC 2022)"
            ),
            # Test Case 8: AML with inv(3)/GATA2::MECOM
            (
                {
                    "blasts_percentage": 24.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "GATA2::MECOM": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with inv(3)(q21.3q26.2) or t(3;3)(q21.3;q26.2)/GATA2, MECOM(EVI1) (ICC 2022)"
            ),
            # Test Case 9: AML with other KMT2A rearrangements
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "KMT2A": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with other KMT2A rearrangements (ICC 2022)"
            ),
            # Test Case 10: AML with other MECOM rearrangements
            (
                {
                    "blasts_percentage": 32.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MECOM": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with other MECOM rearrangements (ICC 2022)"
            ),
            # Test Case 11: AML with NUP98 and other partners
            (
                {
                    "blasts_percentage": 26.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NUP98": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with NUP98 and other partners (ICC 2022)"
            ),
            # Test Case 12: AML with in-frame bZIP mutated CEBPA
            (
                {
                    "blasts_percentage": 14.0,  # ≥10% for ICC
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "bZIP": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with in-frame bZIP mutated CEBPA (ICC 2022)"
            ),
            # Test Case 13: AML with t(9;22)/BCR::ABL1
            (
                {
                    "blasts_percentage": 19.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "BCR::ABL1": True,
                        "NPM1": False
                    },
                    "qualifiers": {}
                },
                "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1 (ICC 2022)"
            ),
        ]
    )
    def test_aml_defining_genetic_abnormalities_icc2022(self, parsed_data, expected_classification):
        """Test AML ICC 2022 classification with AML-defining genetic abnormalities."""
        result, derivation = classify_AML_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
        assert len(derivation) > 0

    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: AML with mutated TP53 (biallelic - 2 mutations)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "qualifiers": {}
                },
                "AML with mutated TP53 (ICC 2022)"
            ),
            # Test Case 2: AML with mutated TP53 (1 mutation + del17p)
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "qualifiers": {}
                },
                "AML with mutated TP53 (ICC 2022)"
            ),
            # Test Case 3: AML with mutated TP53 (1 mutation + LOH)
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": True,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "qualifiers": {}
                },
                "AML with mutated TP53 (ICC 2022)"
            ),
            # Test Case 4: AML with mutated TP53 (≥10% VAF)
            (
                {
                    "blasts_percentage": 40.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_10_percent_vaf": True
                    },
                    "qualifiers": {}
                },
                "AML with mutated TP53 (ICC 2022)"
            ),
            # Test Case 5: AML with myelodysplasia related gene mutation
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {
                        "ASXL1": True,
                        "SF3B1": False
                    },
                    "qualifiers": {}
                },
                "AML with myelodysplasia related gene mutation (ICC 2022)"
            ),
            # Test Case 6: AML with myelodysplasia related cytogenetic abnormality
            (
                {
                    "blasts_percentage": 33.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True,
                        "del_5q": False
                    },
                    "qualifiers": {}
                },
                "AML with myelodysplasia related cytogenetic abnormality (ICC 2022)"
            ),
            # Test Case 7: AML, NOS (no defining features)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "AML, NOS (ICC 2022)"
            ),
        ]
    )
    def test_aml_special_categories_icc2022(self, parsed_data, expected_classification):
        """Test AML ICC 2022 special categories (TP53, MDS-related, NOS)."""
        result, derivation = classify_AML_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLICC2022BlastThresholds:
    """Test suite for AML ICC 2022 blast percentage thresholds."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: <10% blasts with genetic abnormality (should be "Not AML")
            (
                {
                    "blasts_percentage": 8.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "Not AML, consider MDS classification"
            ),
            # Test Case 2: 10-19% blasts with TP53 mutation (should be MDS/AML)
            (
                {
                    "blasts_percentage": 15.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True
                    }
                },
                "MDS/AML with mutated TP53 (ICC 2022)"
            ),
            # Test Case 3: 10-19% blasts with MDS-related mutation (should be MDS/AML)
            (
                {
                    "blasts_percentage": 12.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {
                        "ASXL1": True
                    }
                },
                "MDS/AML with myelodysplasia related gene mutation (ICC 2022)"
            ),
            # Test Case 4: 10-19% blasts with MDS-related cytogenetics (should be MDS/AML)
            (
                {
                    "blasts_percentage": 18.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "del_5q": True
                    }
                },
                "MDS/AML with myelodysplasia related cytogenetic abnormality (ICC 2022)"
            ),
            # Test Case 5: 10-19% blasts with no special features (should be MDS/AML, NOS)
            (
                {
                    "blasts_percentage": 14.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {}
                },
                "MDS/AML, NOS (ICC 2022)"
            ),
            # Test Case 6: <10% blasts with special genetic abnormality (should be "Not AML")
            (
                {
                    "blasts_percentage": 5.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RUNX1::RUNX1T1": True
                    }
                },
                "Not AML, consider MDS classification"
            ),
        ]
    )
    def test_aml_icc2022_blast_thresholds(self, parsed_data, expected_classification):
        """Test AML ICC 2022 blast percentage thresholds."""
        result, derivation = classify_AML_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLICC2022Qualifiers:
    """Test suite for AML ICC 2022 qualifiers."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Therapy related (Ionising radiation)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Ionising radiation"
                    }
                },
                "AML with mutated NPM1, therapy related (ICC 2022)"
            ),
            # Test Case 2: Therapy related (Cytotoxic chemotherapy)
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RUNX1::RUNX1T1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy"
                    }
                },
                "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1, therapy related (ICC 2022)"
            ),
            # Test Case 3: Therapy related (Immune interventions - accepted for ICC)
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CBFB::MYH11": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Immune interventions"
                    }
                },
                "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11, therapy related (ICC 2022)"
            ),
            # Test Case 4: Therapy related (Any combination)
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "DEK::NUP214": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Any combination"
                    }
                },
                "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214, therapy related (ICC 2022)"
            ),
            # Test Case 5: In the setting of germline predisposition (single variant)
            (
                {
                    "blasts_percentage": 40.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "RBM15::MRTFA": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTFA, in the setting of RUNX1 (ICC 2022)"
            ),
            # Test Case 6: Multiple germline variants
            (
                {
                    "blasts_percentage": 33.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MLLT3::KMT2A": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "GATA2, DDX41"
                    }
                },
                "AML with t(9;11)(p21.3;q23.3)/MLLT3::KMT2A, in the setting of GATA2, DDX41 (ICC 2022)"
            ),
            # Test Case 7: Germline BLM mutation (excluded for ICC)
            (
                {
                    "blasts_percentage": 26.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "germline BLM mutation"
                    }
                },
                "AML with mutated NPM1 (ICC 2022)"
            ),
            # Test Case 8: Arising post MDS
            (
                {
                    "blasts_percentage": 31.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "KMT2A": True
                    },
                    "qualifiers": {
                        "previous_MDS_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with other KMT2A rearrangements, arising post MDS (ICC 2022)"
            ),
            # Test Case 9: Arising post MDS/MPN
            (
                {
                    "blasts_percentage": 38.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "MECOM": True
                    },
                    "qualifiers": {
                        "previous_MDS/MPN_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with other MECOM rearrangements, arising post MDS (ICC 2022)"
            ),
            # Test Case 10: Arising post MPN
            (
                {
                    "blasts_percentage": 44.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NUP98": True
                    },
                    "qualifiers": {
                        "previous_MPN_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with NUP98 and other partners, arising post MDS (ICC 2022)"
            ),
            # Test Case 11: Multiple qualifiers
            (
                {
                    "blasts_percentage": 27.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2",
                        "previous_MDS_diagnosed_over_3_months_ago": True
                    }
                },
                "AML with mutated NPM1, therapy related, in the setting of GATA2, arising post MDS (ICC 2022)"
            ),
        ]
    )
    def test_aml_icc2022_qualifiers(self, parsed_data, expected_classification):
        """Test AML ICC 2022 classification with various qualifiers."""
        result, derivation = classify_AML_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestAMLEdgeCases:
    """Test suite for AML classification edge cases and boundary conditions."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_who_result, expected_icc_result",
        [
            # Test Case 1: Boundary blast percentage (exactly 20% for WHO)
            (
                {
                    "blasts_percentage": 20.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CEBPA": True
                    }
                },
                "AML with CEBPA mutation (WHO 2022)",
                "AML, NOS (ICC 2022)"
            ),
            # Test Case 2: Boundary blast percentage (exactly 19.9% for WHO)
            (
                {
                    "blasts_percentage": 19.9,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "CEBPA": True
                    }
                },
                "Not AML, consider MDS classification",
                "MDS/AML, NOS (ICC 2022)"
            ),
            # Test Case 3: Boundary blast percentage (exactly 10% for ICC) - NPM1 doesn't require 20%
            (
                {
                    "blasts_percentage": 10.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "AML with NPM1 mutation (WHO 2022)",
                "AML with mutated NPM1 (ICC 2022)"
            ),
            # Test Case 4: Boundary blast percentage (exactly 9.9% for ICC)
            (
                {
                    "blasts_percentage": 9.9,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "AML with NPM1 mutation (WHO 2022)",
                "Not AML, consider MDS classification"
            ),
            # Test Case 5: Multiple genetic abnormalities (first one wins)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "PML::RARA": True,
                        "NPM1": True,  # This should be ignored
                        "RUNX1::RUNX1T1": True  # This should be ignored
                    }
                },
                "Acute promyelocytic leukaemia with PML::RARA fusion (WHO 2022)",
                "APL with t(15;17)(q24.1;q21.2)/PML::RARA (ICC 2022)"
            ),
            # Test Case 6: Missing blasts percentage
            (
                {
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "Error: blasts_percentage is missing. Classification cannot proceed.",
                "Error: blasts_percentage is missing. Classification cannot proceed."
            ),
            # Test Case 7: Invalid blasts percentage (negative)
            (
                {
                    "blasts_percentage": -5.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "Error: blasts_percentage must be a number between 0 and 100.",
                "Error: blasts_percentage must be a number between 0 and 100."
            ),
            # Test Case 8: Invalid blasts percentage (>100)
            (
                {
                    "blasts_percentage": 105.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    }
                },
                "Error: blasts_percentage must be a number between 0 and 100.",
                "Error: blasts_percentage must be a number between 0 and 100."
            ),
        ]
    )
    def test_aml_edge_cases(self, parsed_data, expected_who_result, expected_icc_result):
        """Test AML classification edge cases and boundary conditions."""
        who_result, who_derivation = classify_AML_WHO2022(parsed_data)
        icc_result, icc_derivation = classify_AML_ICC2022(parsed_data)
        
        assert who_result == expected_who_result
        assert icc_result == expected_icc_result
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)


class TestAMLComplexScenarios:
    """Test suite for complex AML classification scenarios."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_who_classification, expected_icc_classification",
        [
            # Test Case 1: Complex scenario with MDS-related features and qualifiers
            (
                {
                    "blasts_percentage": 28.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {
                        "ASXL1": True,
                        "SF3B1": True,
                        "SRSF2": False
                    },
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True,
                        "del_5q": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2",
                        "previous_MDS_diagnosed_over_3_months_ago": True
                    }
                },
                "AML, myelodysplasia related, previous cytotoxic therapy, associated with GATA2, progressed from MDS (WHO 2022)",
                "AML with myelodysplasia related gene mutation, therapy related, in the setting of GATA2, arising post MDS (ICC 2022)"
            ),
            # Test Case 2: FAB differentiation with qualifiers
            (
                {
                    "blasts_percentage": 35.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M4",
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Ionising radiation",
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "Acute myelomonocytic leukaemia, previous cytotoxic therapy, associated with RUNX1 (WHO 2022)",
                "AML, NOS, therapy related, in the setting of RUNX1 (ICC 2022)"
            ),
            # Test Case 3: Erythroid leukaemia with not_erythroid flag
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "AML_differentiation": "M6a",
                    "qualifiers": {}
                },
                "Acute myeloid leukaemia, [define by differentiation] (WHO 2022)",
                "AML, NOS (ICC 2022)"
            ),
            # Test Case 4: Both MDS-related mutations and cytogenetics (mutations take precedence)
            (
                {
                    "blasts_percentage": 25.0,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {
                        "ASXL1": True,
                        "RUNX1": True
                    },
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True,
                        "del_7q": True
                    },
                    "qualifiers": {}
                },
                "AML, myelodysplasia related (WHO 2022)",
                "AML with myelodysplasia related gene mutation (ICC 2022)"
            ),
            # Test Case 5: Priority testing - AML-defining beats MDS-related
            (
                {
                    "blasts_percentage": 30.0,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True
                    },
                    "MDS_related_mutation": {
                        "ASXL1": True,
                        "SF3B1": True
                    },
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True
                    },
                    "qualifiers": {}
                },
                "AML with NPM1 mutation (WHO 2022)",
                "AML with mutated NPM1 (ICC 2022)"
            ),
        ]
    )
    def test_complex_aml_scenarios(self, parsed_data, expected_who_classification, expected_icc_classification):
        """Test complex AML classification scenarios where WHO and ICC may differ."""
        who_result, who_derivation = classify_AML_WHO2022(parsed_data)
        icc_result, icc_derivation = classify_AML_ICC2022(parsed_data)
        
        # Special handling for not_erythroid test case
        if "M6a" in str(parsed_data.get("AML_differentiation", "")):
            who_result, who_derivation = classify_AML_WHO2022(parsed_data, not_erythroid=True)
        
        assert who_result == expected_who_classification
        assert icc_result == expected_icc_classification
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)
        assert len(who_derivation) > 0
        assert len(icc_derivation) > 0


class TestAMLErrorHandling:
    """Test suite for AML classification error handling and robustness."""
    
    @pytest.mark.parametrize(
        "parsed_data",
        [
            # Test Case 1: Empty input
            {},
            # Test Case 2: Only blast percentage
            {"blasts_percentage": 25.0},
            # Test Case 3: Missing critical sections
            {
                "blasts_percentage": 30.0,
                "qualifiers": {}
            },
            # Test Case 4: All sections present but empty
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
        ]
    )
    def test_aml_robustness(self, parsed_data):
        """Test that AML classification functions handle incomplete data gracefully."""
        # Should not raise exceptions
        who_result, who_derivation = classify_AML_WHO2022(parsed_data)
        icc_result, icc_derivation = classify_AML_ICC2022(parsed_data)
        
        # Results should be strings 
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
        
        # Should either end with classification system or be an error message
        assert (who_result.endswith("(WHO 2022)") or who_result.startswith("Error:") or "Not AML" in who_result)
        assert (icc_result.endswith("(ICC 2022)") or icc_result.startswith("Error:") or "Not AML" in icc_result)
        
        # Derivations should be lists
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)
    
    def test_aml_return_format(self):
        """Test that AML classification functions return the expected format."""
        test_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": {
                "NPM1": True
            },
            "qualifiers": {}
        }
        
        who_result, who_derivation = classify_AML_WHO2022(test_data)
        icc_result, icc_derivation = classify_AML_ICC2022(test_data)
        
        # Test return types
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)
        
        # Test that results contain expected suffixes
        assert "(WHO 2022)" in who_result
        assert "(ICC 2022)" in icc_result
        
        # Test that derivations are not empty
        assert len(who_derivation) > 0
        assert len(icc_derivation) > 0
        
        # Test that all derivation items are strings
        assert all(isinstance(item, str) for item in who_derivation)
        assert all(isinstance(item, str) for item in icc_derivation)
    
    @pytest.mark.parametrize(
        "invalid_blasts",
        [None, "invalid", -10, 150, float('inf'), float('nan')]
    )
    def test_aml_invalid_blast_values(self, invalid_blasts):
        """Test AML classification with invalid blast percentage values."""
        test_data = {
            "blasts_percentage": invalid_blasts,
            "AML_defining_recurrent_genetic_abnormalities": {
                "NPM1": True
            }
        }
        
        who_result, who_derivation = classify_AML_WHO2022(test_data)
        icc_result, icc_derivation = classify_AML_ICC2022(test_data)
        
        # Should return error messages for invalid values
        if invalid_blasts is None:
            assert "missing" in who_result.lower()
            assert "missing" in icc_result.lower()
        else:
            assert "Error:" in who_result or "Error:" in icc_result
        
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)


class TestAMLStressTests:
    """Stress test suite with really difficult and complex AML scenarios designed to break the system."""
    
    def test_extreme_blast_percentages(self):
        """Test with extreme blast percentage values that might cause issues."""
        extreme_cases = [
            {"blasts_percentage": 0.0, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 0.1, "AML_defining_recurrent_genetic_abnormalities": {"PML::RARA": True}},
            {"blasts_percentage": 99.9, "AML_defining_recurrent_genetic_abnormalities": {"RUNX1::RUNX1T1": True}},
            {"blasts_percentage": 100.0, "AML_defining_recurrent_genetic_abnormalities": {"CBFB::MYH11": True}},
            {"blasts_percentage": 9.99999, "AML_defining_recurrent_genetic_abnormalities": {"BCR::ABL1": True}},
            {"blasts_percentage": 10.00001, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
            {"blasts_percentage": 19.99999, "AML_defining_recurrent_genetic_abnormalities": {"bZIP": True}},
            {"blasts_percentage": 20.00001, "AML_defining_recurrent_genetic_abnormalities": {"BCR::ABL1": True}},
        ]
        
        for test_data in extreme_cases:
            # Should not crash
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
    
    def test_massive_genetic_abnormality_overload(self):
        """Test with every possible genetic abnormality set to True."""
        overloaded_data = {
            "blasts_percentage": 50.0,
            "AML_defining_recurrent_genetic_abnormalities": {
                "PML::RARA": True,
                "NPM1": True,
                "RUNX1::RUNX1T1": True,
                "CBFB::MYH11": True,
                "DEK::NUP214": True,
                "RBM15::MRTFA": True,
                "MLLT3::KMT2A": True,
                "GATA2::MECOM": True,
                "KMT2A": True,
                "MECOM": True,
                "NUP98": True,
                "CEBPA": True,
                "bZIP": True,
                "BCR::ABL1": True
            },
            "Biallelic_TP53_mutation": {
                "2_x_TP53_mutations": True,
                "1_x_TP53_mutation_del_17p": True,
                "1_x_TP53_mutation_LOH": True,
                "1_x_TP53_mutation_10_percent_vaf": True
            },
            "MDS_related_mutation": {
                "ASXL1": True,
                "SF3B1": True,
                "SRSF2": True,
                "RUNX1": True,
                "BCOR": True,
                "STAG2": True
            },
            "MDS_related_cytogenetics": {
                "Complex_karyotype": True,
                "del_5q": True,
                "del_7q": True,
                "del_20q": True,
                "i_17q": True
            },
            "AML_differentiation": "M7",
            "qualifiers": {
                "previous_cytotoxic_therapy": "Any combination",
                "predisposing_germline_variant": "RUNX1, GATA2, DDX41, CEBPA",
                "previous_MDS_diagnosed_over_3_months_ago": True,
                "previous_MPN_diagnosed_over_3_months_ago": True,
                "previous_MDS/MPN_diagnosed_over_3_months_ago": True
            }
        }
        
        # Should handle gracefully and pick the first/highest priority classification
        who_result, who_derivation = classify_AML_WHO2022(overloaded_data)
        icc_result, icc_derivation = classify_AML_ICC2022(overloaded_data)
        
        # Should still return valid classifications (likely PML::RARA since it's usually first)
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
    
    def test_conflicting_qualifier_combinations(self):
        """Test with contradictory or unusual qualifier combinations."""
        conflicting_cases = [
            # Case 1: Multiple progression types simultaneously
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
                "qualifiers": {
                    "previous_MDS_diagnosed_over_3_months_ago": True,
                    "previous_MPN_diagnosed_over_3_months_ago": True,
                    "previous_MDS/MPN_diagnosed_over_3_months_ago": True
                }
            },
            # Case 2: Excluded variants mixed with accepted ones
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {"RUNX1::RUNX1T1": True},
                "qualifiers": {
                    "predisposing_germline_variant": "RUNX1, Diamond-Blackfan anemia, GATA2, germline BLM mutation"
                }
            },
            # Case 3: All therapy types
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {"CBFB::MYH11": True},
                "qualifiers": {
                    "previous_cytotoxic_therapy": "Ionising radiation, Cytotoxic chemotherapy, Immune interventions, Any combination"
                }
            },
            # Case 4: Very long germline variant list
            {
                "blasts_percentage": 40.0,
                "AML_defining_recurrent_genetic_abnormalities": {"DEK::NUP214": True},
                "qualifiers": {
                    "predisposing_germline_variant": "RUNX1, GATA2, DDX41, CEBPA, ANKRD26, ETV6, SAMD9, SAMD9L, ERCC6L2, TERC, TERT, SRP72, BRCA2, FANCG, FANCL, FANCM, ATM"
                }
            }
        ]
        
        for test_data in conflicting_cases:
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            # Should handle conflicts gracefully
            assert not who_result.startswith("Error:")
            assert not icc_result.startswith("Error:")
    
    def test_unicode_and_special_characters(self):
        """Test with unicode characters and special symbols in genetic names."""
        unicode_cases = [
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": True,
                    "RUNX1::RUNX1T1": True,  # Double colon
                    "PML→RARA": False,  # Arrow instead of ::
                    "CBFB—MYH11": False,  # Em dash
                    "test_gene_αβγ": False  # Greek letters
                },
                "qualifiers": {
                    "predisposing_germline_variant": "GATA2, DDX41, test—gene—α",
                    "previous_cytotoxic_therapy": "Iönising radiatiön"  # Unicode characters
                }
            }
        ]
        
        for test_data in unicode_cases:
            # Should handle gracefully without crashing
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
    
    def test_nested_data_structure_corruption(self):
        """Test with corrupted or unusual nested data structures."""
        corrupted_cases = [
            # Case 1: Nested dictionaries in genetic abnormalities
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": {"mutation_type": "insertion", "vaf": 45.6},
                    "PML::RARA": [True, False, "maybe"],
                    "RUNX1::RUNX1T1": {"nested": {"very": {"deep": True}}}
                }
            },
            # Case 2: List instead of dictionary
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": [
                    "NPM1", "PML::RARA", "RUNX1::RUNX1T1"
                ]
            },
            # Case 3: Mixed data types in qualifiers
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
                "qualifiers": {
                    "previous_cytotoxic_therapy": ["Cytotoxic chemotherapy", "Ionising radiation"],
                    "predisposing_germline_variant": 12345,
                    "previous_MDS_diagnosed_over_3_months_ago": "yes"
                }
            }
        ]
        
        for test_data in corrupted_cases:
            # Should handle gracefully without crashing
            try:
                who_result, who_derivation = classify_AML_WHO2022(test_data)
                icc_result, icc_derivation = classify_AML_ICC2022(test_data)
                
                assert isinstance(who_result, str)
                assert isinstance(icc_result, str)
            except (KeyError, TypeError, AttributeError):
                # Acceptable to raise appropriate errors for malformed data
                pass
    
    def test_impossible_clinical_scenarios(self):
        """Test clinically impossible or highly unusual scenarios."""
        impossible_cases = [
            # Case 1: 0% blasts but multiple AML-defining abnormalities
            {
                "blasts_percentage": 0.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "PML::RARA": True,
                    "NPM1": True,
                    "RUNX1::RUNX1T1": True
                },
                "qualifiers": {}
            },
            # Case 2: 100% blasts with MDS-related features only
            {
                "blasts_percentage": 100.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {"ASXL1": True},
                "MDS_related_cytogenetics": {"del_5q": True},
                "qualifiers": {}
            },
            # Case 3: M6a differentiation with 5% blasts
            {
                "blasts_percentage": 5.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "AML_differentiation": "M6a",
                "qualifiers": {}
            },
            # Case 4: Therapy-related but no therapy specified
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
                "qualifiers": {
                    "previous_cytotoxic_therapy": "",
                    "predisposing_germline_variant": ""
                }
            }
        ]
        
        for test_data in impossible_cases:
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            # Should still return something reasonable
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            assert isinstance(who_derivation, list)
            assert isinstance(icc_derivation, list)
    
    def test_system_difference_exploitation(self):
        """Test cases specifically designed to exploit differences between WHO and ICC."""
        differential_cases = [
            # Case 1: CEBPA with exactly 15% blasts (WHO needs ≥20%, ICC needs ≥10%)
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True},
                "qualifiers": {}
            },
            # Case 2: Multiple therapy types where WHO/ICC differ
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
                "qualifiers": {
                    "previous_cytotoxic_therapy": "Immune interventions"  # ICC accepts, WHO doesn't
                }
            },
            # Case 3: Germline variants where WHO/ICC differ
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {"RUNX1::RUNX1T1": True},
                "qualifiers": {
                    "predisposing_germline_variant": "Diamond-Blackfan anemia"  # WHO excludes
                }
            },
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {"CBFB::MYH11": True},
                "qualifiers": {
                    "predisposing_germline_variant": "germline BLM mutation"  # ICC excludes
                }
            },
            # Case 4: 15% blasts with TP53 (should be MDS/AML in ICC, not AML in WHO)
            {
                "blasts_percentage": 15.0,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "Biallelic_TP53_mutation": {"2_x_TP53_mutations": True},
                "qualifiers": {}
            }
        ]
        
        for test_data in differential_cases:
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            # These should give different results between systems
            # but both should be valid
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            
            # The results should often be different for these edge cases
            print(f"WHO: {who_result}")
            print(f"ICC: {icc_result}")
            print("---")
    
    def test_recursive_and_circular_data(self):
        """Test with potential recursive or circular data structures."""
        # Create a dictionary that references itself (if that's possible)
        circular_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "qualifiers": {}
        }
        # Add circular reference
        circular_data["self_reference"] = circular_data
        
        # Should handle without infinite recursion
        try:
            who_result, who_derivation = classify_AML_WHO2022(circular_data)
            icc_result, icc_derivation = classify_AML_ICC2022(circular_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
        except (RecursionError, ValueError):
            # Acceptable to fail on circular references
            pass
    
    def test_extremely_long_strings(self):
        """Test with extremely long string values."""
        long_string = "A" * 10000  # 10KB string
        very_long_variant_list = ", ".join([f"GENE{i}" for i in range(1000)])  # 1000 genes
        
        stress_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "qualifiers": {
                "predisposing_germline_variant": very_long_variant_list,
                "previous_cytotoxic_therapy": long_string
            }
        }
        
        # Should handle without memory issues
        who_result, who_derivation = classify_AML_WHO2022(stress_data)
        icc_result, icc_derivation = classify_AML_ICC2022(stress_data)
        
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
        # Results might be truncated or filtered, but should not crash
    
    def test_floating_point_precision_edge_cases(self):
        """Test floating point precision edge cases around thresholds."""
        precision_cases = [
            {"blasts_percentage": 9.999999999999998, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 10.000000000000002, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
            {"blasts_percentage": 19.999999999999996, "AML_defining_recurrent_genetic_abnormalities": {"bZIP": True}},
            {"blasts_percentage": 20.000000000000004, "AML_defining_recurrent_genetic_abnormalities": {"BCR::ABL1": True}},
        ]
        
        for test_data in precision_cases:
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            # Should handle floating point precision consistently
            print(f"Blasts: {test_data['blasts_percentage']}, WHO: {who_result}, ICC: {icc_result}")

    def test_memory_and_performance_stress(self):
        """Test with scenarios that might cause memory or performance issues."""
        # Test with a huge number of genetic abnormalities
        massive_abnormalities = {}
        for i in range(10000):  # 10,000 fake genetic abnormalities
            massive_abnormalities[f"FAKE_GENE_{i}"] = (i % 2 == 0)  # Alternating True/False
        
        # Add real ones too
        massive_abnormalities.update({
            "NPM1": True,
            "PML::RARA": False,
            "RUNX1::RUNX1T1": False
        })
        
        stress_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": massive_abnormalities,
            "qualifiers": {}
        }
        
        # Should complete in reasonable time without memory issues
        start_time = time.time()
        
        who_result, who_derivation = classify_AML_WHO2022(stress_data)
        icc_result, icc_derivation = classify_AML_ICC2022(stress_data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
        assert execution_time < 5.0  # Should complete within 5 seconds
        print(f"Execution time: {execution_time:.3f} seconds")
    
    def test_malicious_injection_attempts(self):
        """Test with data that might be used for injection attacks."""
        malicious_cases = [
            # SQL injection style
            {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1'; DROP TABLE patients; --": False,
                    "NPM1": True
                },
                "qualifiers": {
                    "predisposing_germline_variant": "GATA2'; DELETE * FROM mutations; --"
                }
            },
            # Script injection style
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "<script>alert('hack')</script>": False,
                    "RUNX1::RUNX1T1": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": "javascript:alert(document.cookie)"
                }
            },
            # Path traversal style
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "../../etc/passwd": False,
                    "CBFB::MYH11": True
                },
                "qualifiers": {
                    "predisposing_germline_variant": "../../../sensitive_data.txt"
                }
            },
            # Code injection style
            {
                "blasts_percentage": 40.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "__import__('os').system('rm -rf /')": False,
                    "DEK::NUP214": True
                },
                "qualifiers": {
                    "previous_cytotoxic_therapy": "eval('malicious_code()')"
                }
            }
        ]
        
        for test_data in malicious_cases:
            # Should handle without executing any malicious code
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            # Should not contain any indication of successful injection
            assert "DROP TABLE" not in who_result
            assert "alert" not in icc_result
            assert "rm -rf" not in who_result
    
    def test_type_confusion_attacks(self):
        """Test with type confusion scenarios."""
        type_confusion_cases = [
            # Integers as strings
            {
                "blasts_percentage": "25.0",  # String instead of float
                "AML_defining_recurrent_genetic_abnormalities": {
                    "NPM1": "True"  # String instead of boolean
                }
            },
            # Lists instead of booleans
            {
                "blasts_percentage": 30.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "RUNX1::RUNX1T1": [1, 2, 3],  # List instead of boolean
                    "NPM1": {"complex": "object"}  # Dict instead of boolean
                }
            },
            # Functions or callables
            {
                "blasts_percentage": 35.0,
                "AML_defining_recurrent_genetic_abnormalities": {
                    "CBFB::MYH11": lambda: True,  # Function instead of boolean
                    "NPM1": False
                }
            }
        ]
        
        for test_data in type_confusion_cases:
            try:
                who_result, who_derivation = classify_AML_WHO2022(test_data)
                icc_result, icc_derivation = classify_AML_ICC2022(test_data)
                
                # If it doesn't crash, should return reasonable results
                assert isinstance(who_result, str)
                assert isinstance(icc_result, str)
            except (TypeError, ValueError, AttributeError):
                # Acceptable to raise appropriate type errors
                pass
    
    def test_boundary_condition_exploitation(self):
        """Test exact boundary conditions that might cause off-by-one errors."""
        boundary_cases = [
            # Exactly at integer boundaries
            {"blasts_percentage": 10, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 20, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
            
            # Just below boundaries
            {"blasts_percentage": 9.999999999, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 19.999999999, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
            
            # Just above boundaries  
            {"blasts_percentage": 10.000000001, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 20.000000001, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
            
            # Extreme precision
            {"blasts_percentage": 9.9999999999999999999999999999999, "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True}},
            {"blasts_percentage": 10.0000000000000000000000000000001, "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True}},
        ]
        
        for test_data in boundary_cases:
            who_result, who_derivation = classify_AML_WHO2022(test_data)
            icc_result, icc_derivation = classify_AML_ICC2022(test_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
            print(f"Blasts: {test_data['blasts_percentage']}, WHO: {'AML' in who_result}, ICC: {'AML' in icc_result}")
    
    def test_concurrent_stress(self):
        """Test concurrent execution to look for race conditions."""
        import threading
        import time
        
        test_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "qualifiers": {}
        }
        
        results = []
        errors = []
        
        def worker():
            try:
                for _ in range(100):  # Each thread does 100 classifications
                    who_result, who_derivation = classify_AML_WHO2022(test_data)
                    icc_result, icc_derivation = classify_AML_ICC2022(test_data)
                    results.append((who_result, icc_result))
            except Exception as e:
                errors.append(e)
        
        # Start 10 concurrent threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have no errors and consistent results
        assert len(errors) == 0, f"Concurrent execution errors: {errors}"
        assert len(results) == 1000  # 10 threads × 100 iterations
        
        # All results should be identical
        first_result = results[0]
        for result in results:
            assert result == first_result, "Inconsistent results in concurrent execution"
    
    def test_deep_nesting_stress(self):
        """Test with deeply nested data structures."""
        # Create deeply nested structure
        deep_nested = {"level_0": {}}
        current = deep_nested["level_0"]
        for i in range(1, 1000):  # 1000 levels deep
            current[f"level_{i}"] = {}
            current = current[f"level_{i}"]
        current["NPM1"] = True
        
        stress_data = {
            "blasts_percentage": 25.0,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "deeply_nested_data": deep_nested,  # This shouldn't be processed but shouldn't crash
            "qualifiers": {}
        }
        
        # Should handle without stack overflow
        try:
            who_result, who_derivation = classify_AML_WHO2022(stress_data)
            icc_result, icc_derivation = classify_AML_ICC2022(stress_data)
            
            assert isinstance(who_result, str)
            assert isinstance(icc_result, str)
        except RecursionError:
            # Acceptable to fail on extremely deep nesting
            pass


# Custom pytest plugin to display test summary
class SummaryReporterPlugin:
    """Custom pytest plugin to collect and display test results summary."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = 0
        
    def pytest_runtest_logreport(self, report):
        """Called after each test phase."""
        if report.when == 'call':
            if report.outcome == 'passed':
                self.passed += 1
            elif report.outcome == 'failed':
                self.failed += 1
            elif report.outcome == 'skipped':
                self.skipped += 1
        elif report.when == 'setup' and report.outcome == 'failed':
            self.errors += 1
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Called after test session finishes."""
        total = self.passed + self.failed + self.skipped + self.errors
        
        print("\n" + "=" * 80)
        print("AML CLASSIFICATION TEST SUMMARY")
        print("=" * 80)
        print(f"Total tests run: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        if self.skipped > 0:
            print(f"⏭️  Skipped: {self.skipped}")
        if self.errors > 0:
            print(f"🔥 Errors: {self.errors}")
        
        if total > 0:
            pass_rate = (self.passed / total) * 100
            print(f"\nPass rate: {pass_rate:.1f}%")
            
            if self.failed == 0 and self.errors == 0:
                print("🎉 All tests passed!")
            elif self.failed > 0:
                print(f"⚠️  {self.failed} test(s) failed")
        
        print("=" * 80)


if __name__ == "__main__":
    # Register the custom plugin when running this file directly
    pytest.main([__file__, "-v"], plugins=[SummaryReporterPlugin()]) 