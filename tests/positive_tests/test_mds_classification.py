"""
Comprehensive test suite for MDS (Myelodysplastic Syndromes) classification functions.

This test suite covers:
1. MDS WHO 2022 classification (classify_MDS_WHO2022)
2. MDS ICC 2022 classification (classify_MDS_ICC2022)

Tests include:
- Basic classification scenarios
- Biallelic TP53 mutations
- Blast percentage thresholds
- SF3B1 mutations
- del(5q) cytogenetics
- Hypoplasia and fibrotic conditions
- Dysplastic lineages
- Qualifiers (therapy, germline variants)
- Edge cases and error conditions
- Complex scenarios with multiple mutations
"""

import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022


class TestMDSWHO2022Classification:
    """Test suite for MDS WHO 2022 classification function."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Basic MDS with biallelic TP53 (2 mutations)
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 8.0,
                    "qualifiers": {}
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 2: Biallelic TP53 with 1 mutation + del(17p)
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 12.0
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 3: Biallelic TP53 with 1 mutation + LOH
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": True,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 5.0
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 4: Biallelic TP53 with 1 mutation + ≥50% VAF
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": True,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 15.0
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 5: Biallelic TP53 with 1 mutation + ≥10% VAF + complex karyotype
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": True
                    },
                    "MDS_related_cytogenetics": {
                        "Complex_karyotype": True
                    },
                    "blasts_percentage": 3.0
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 6: MDS with increased blasts 1 (5-9% blasts)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 7.0,
                    "fibrotic": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {}
                },
                "MDS with increased blasts 1 (WHO 2022)"
            ),
            # Test Case 7: MDS with increased blasts 2 (10-19% blasts)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 14.0,
                    "fibrotic": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {}
                },
                "MDS with increased blasts 2 (WHO 2022)"
            ),
            # Test Case 8: MDS, fibrotic (5-19% blasts + fibrotic)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 8.0,
                    "fibrotic": True,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, fibrotic (WHO 2022)"
            ),
            # Test Case 9: MDS with low blasts and SF3B1 mutation
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "fibrotic": False,
                    "MDS_related_mutation": {
                        "SF3B1": True,
                        "ASXL1": False,
                        "RUNX1": False
                    },
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS with low blasts and SF3B1 (WHO 2022)"
            ),
            # Test Case 10: MDS with low blasts and isolated 5q-
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 3.0,
                    "fibrotic": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "del_5q": True,
                        "Complex_karyotype": False
                    },
                    "qualifiers": {}
                },
                "MDS with low blasts and isolated 5q- (WHO 2022)"
            ),
            # Test Case 11: MDS, hypoplastic
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "hypoplasia": True,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, hypoplastic (WHO 2022)"
            ),
            # Test Case 12: MDS with low blasts (single dysplastic lineage)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "fibrotic": False,
                    "hypoplasia": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {}
                },
                "MDS with low blasts (WHO 2022)"
            ),
            # Test Case 13: MDS with low blasts (multiple dysplastic lineages)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 4.0,
                    "fibrotic": False,
                    "hypoplasia": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 3,
                    "qualifiers": {}
                },
                "MDS with low blasts (WHO 2022)"
            ),
            # Test Case 14: MDS, unclassifiable (no specific features)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "fibrotic": False,
                    "hypoplasia": False,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, unclassifiable (WHO 2022)"
            ),
        ]
    )
    def test_basic_mds_who2022_classification(self, parsed_data, expected_classification):
        """Test basic MDS WHO 2022 classification scenarios."""
        result, derivation = classify_MDS_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
        assert len(derivation) > 0
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Previous cytotoxic therapy (Ionising radiation)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 6.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Ionising radiation"
                    }
                },
                "MDS with increased blasts 1, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 2: Previous cytotoxic therapy (Cytotoxic chemotherapy)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 13.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy"
                    }
                },
                "MDS with increased blasts 2, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 3: Previous cytotoxic therapy (Any combination)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {
                        "SF3B1": True
                    },
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Any combination"
                    }
                },
                "MDS with low blasts and SF3B1, previous cytotoxic therapy (WHO 2022)"
            ),
            # Test Case 4: Immune interventions (NOT accepted for WHO, should not add qualifier)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 8.0,
                    "fibrotic": True,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Immune interventions"
                    }
                },
                "MDS, fibrotic (WHO 2022)"
            ),
            # Test Case 5: Germline predisposition (RUNX1)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 3.0,
                    "MDS_related_cytogenetics": {
                        "del_5q": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "MDS with low blasts and isolated 5q-, associated with RUNX1 (WHO 2022)"
            ),
            # Test Case 6: Multiple germline variants
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 12.0,
                    "qualifiers": {
                        "predisposing_germline_variant": "GATA2, DDX41"
                    }
                },
                "MDS with increased blasts 2, associated with GATA2, DDX41 (WHO 2022)"
            ),
            # Test Case 7: Diamond-Blackfan anemia (should be excluded for WHO)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 4.0,
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "predisposing_germline_variant": "Diamond-Blackfan anemia"
                    }
                },
                "MDS with low blasts (WHO 2022)"
            ),
            # Test Case 8: Both therapy and germline variant
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 9.0,
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2"
                    }
                },
                "MDS with increased blasts 1, previous cytotoxic therapy, associated with GATA2 (WHO 2022)"
            ),
            # Test Case 9: Germline variant with extra information in brackets
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "hypoplasia": True,
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1 (familial platelet disorder)"
                    }
                },
                "MDS, hypoplastic, associated with RUNX1 (WHO 2022)"
            ),
        ]
    )
    def test_mds_who2022_with_qualifiers(self, parsed_data, expected_classification):
        """Test MDS WHO 2022 classification with various qualifiers."""
        result, derivation = classify_MDS_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Missing blasts_percentage
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, unclassifiable (WHO 2022)"
            ),
            # Test Case 2: Complex scenario with multiple TP53 conditions (first one takes precedence)
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": True,  # This should be ignored
                        "1_x_TP53_mutation_LOH": True      # This should be ignored
                    },
                    "blasts_percentage": 10.0
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)"
            ),
            # Test Case 3: Boundary blasts percentage (exactly 5%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 5.0,
                    "fibrotic": False,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with increased blasts 1 (WHO 2022)"
            ),
            # Test Case 4: Boundary blasts percentage (exactly 9%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 9.0,
                    "fibrotic": False,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with increased blasts 1 (WHO 2022)"
            ),
            # Test Case 5: Boundary blasts percentage (exactly 10%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 10.0,
                    "fibrotic": False,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with increased blasts 2 (WHO 2022)"
            ),
            # Test Case 6: Boundary blasts percentage (exactly 19%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 19.0,
                    "fibrotic": False,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with increased blasts 2 (WHO 2022)"
            ),
            # Test Case 7: Fibrotic with boundary blasts (exactly 5%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 5.0,
                    "fibrotic": True
                },
                "MDS, fibrotic (WHO 2022)"
            ),
            # Test Case 8: Fibrotic with boundary blasts (exactly 19%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 19.0,
                    "fibrotic": True
                },
                "MDS, fibrotic (WHO 2022)"
            ),
        ]
    )
    def test_mds_who2022_edge_cases(self, parsed_data, expected_classification):
        """Test edge cases and boundary conditions for MDS WHO 2022 classification."""
        result, derivation = classify_MDS_WHO2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestMDSICC2022Classification:
    """Test suite for MDS ICC 2022 classification function."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Basic MDS with biallelic TP53 (2 mutations)
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": False,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 8.0,
                    "qualifiers": {}
                },
                "MDS with mutated TP53 (ICC 2022)"
            ),
            # Test Case 2: Biallelic TP53 with 1 mutation + del(17p)
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 12.0
                },
                "MDS with mutated TP53 (ICC 2022)"
            ),
            # Test Case 3: MDS with excess blasts (5-9% blasts)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 7.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {}
                },
                "MDS with excess blasts (ICC 2022)"
            ),
            # Test Case 4: MDS/AML (10-19% blasts)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 14.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {}
                },
                "MDS/AML (ICC 2022)"
            ),
            # Test Case 5: MDS with mutated SF3B1
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {
                        "SF3B1": True,
                        "ASXL1": False,
                        "RUNX1": False
                    },
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS with mutated SF3B1 (ICC 2022)"
            ),
            # Test Case 6: MDS with del(5q)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 3.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "del_5q": True,
                        "complex_karyotype": False
                    },
                    "qualifiers": {}
                },
                "MDS with del(5q) (ICC 2022)"
            ),
            # Test Case 7: MDS, NOS with single lineage dysplasia
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {}
                },
                "MDS, NOS with single lineage dysplasia (ICC 2022)"
            ),
            # Test Case 8: MDS, NOS with multilineage dysplasia
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 4.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 3,
                    "qualifiers": {}
                },
                "MDS, NOS with multilineage dysplasia (ICC 2022)"
            ),
            # Test Case 9: MDS, NOS without dysplasia (monosomy 7)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "monosomy_7": True,
                        "complex_karyotype": False
                    },
                    "qualifiers": {}
                },
                "MDS, NOS without dysplasia (ICC 2022)"
            ),
            # Test Case 10: MDS, NOS without dysplasia (complex karyotype)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "monosomy_7": False,
                        "complex_karyotype": True
                    },
                    "qualifiers": {}
                },
                "MDS, NOS without dysplasia (ICC 2022)"
            ),
            # Test Case 11: MDS, NOS (default case)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, NOS (ICC 2022)"
            ),
        ]
    )
    def test_basic_mds_icc2022_classification(self, parsed_data, expected_classification):
        """Test basic MDS ICC 2022 classification scenarios."""
        result, derivation = classify_MDS_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
        assert len(derivation) > 0
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Therapy related (Ionising radiation)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 6.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Ionising radiation"
                    }
                },
                "MDS with excess blasts, therapy related (ICC 2022)"
            ),
            # Test Case 2: Therapy related (Cytotoxic chemotherapy)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 13.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy"
                    }
                },
                "MDS/AML, therapy related (ICC 2022)"
            ),
            # Test Case 3: Therapy related (Immune interventions - accepted for ICC)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {
                        "SF3B1": True
                    },
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Immune interventions"
                    }
                },
                "MDS with mutated SF3B1, therapy related (ICC 2022)"
            ),
            # Test Case 4: Therapy related (Any combination)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 3.0,
                    "MDS_related_cytogenetics": {
                        "del_5q": True
                    },
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Any combination"
                    }
                },
                "MDS with del(5q), therapy related (ICC 2022)"
            ),
            # Test Case 5: In the setting of germline predisposition (RUNX1)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 8.0,
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "MDS with excess blasts, in the setting of RUNX1 (ICC 2022)"
            ),
            # Test Case 6: Multiple germline variants
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 12.0,
                    "qualifiers": {
                        "predisposing_germline_variant": "GATA2, DDX41"
                    }
                },
                "MDS/AML, in the setting of GATA2, DDX41 (ICC 2022)"
            ),
            # Test Case 7: Germline BLM mutation (should be excluded for ICC)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 4.0,
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "predisposing_germline_variant": "germline BLM mutation"
                    }
                },
                "MDS, NOS with single lineage dysplasia (ICC 2022)"
            ),
            # Test Case 8: Both therapy and germline variant
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 9.0,
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2"
                    }
                },
                "MDS with excess blasts, therapy related, in the setting of GATA2 (ICC 2022)"
            ),
            # Test Case 9: Germline variant with extra information in brackets
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "MDS_related_cytogenetics": {
                        "monosomy_7": True
                    },
                    "qualifiers": {
                        "predisposing_germline_variant": "RUNX1 (familial platelet disorder)"
                    }
                },
                "MDS, NOS without dysplasia, in the setting of RUNX1 (ICC 2022)"
            ),
        ]
    )
    def test_mds_icc2022_with_qualifiers(self, parsed_data, expected_classification):
        """Test MDS ICC 2022 classification with various qualifiers."""
        result, derivation = classify_MDS_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)
    
    @pytest.mark.parametrize(
        "parsed_data, expected_classification",
        [
            # Test Case 1: Missing blasts_percentage
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {}
                },
                "MDS, NOS (ICC 2022)"
            ),
            # Test Case 2: Complex scenario with multiple TP53 conditions
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": True
                    },
                    "blasts_percentage": 10.0
                },
                "MDS with mutated TP53 (ICC 2022)"
            ),
            # Test Case 3: Boundary blasts percentage (exactly 5%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 5.0,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with excess blasts (ICC 2022)"
            ),
            # Test Case 4: Boundary blasts percentage (exactly 9%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 9.0,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS with excess blasts (ICC 2022)"
            ),
            # Test Case 5: Boundary blasts percentage (exactly 10%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 10.0,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS/AML (ICC 2022)"
            ),
            # Test Case 6: Boundary blasts percentage (exactly 19%)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 19.0,
                    "number_of_dysplastic_lineages": 1
                },
                "MDS/AML (ICC 2022)"
            ),
            # Test Case 7: Zero dysplastic lineages
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 0,
                    "qualifiers": {}
                },
                "MDS, NOS (ICC 2022)"
            ),
            # Test Case 8: Both monosomy_7 and complex_karyotype present
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 1.0,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {
                        "monosomy_7": True,
                        "complex_karyotype": True
                    },
                    "qualifiers": {}
                },
                "MDS, NOS without dysplasia (ICC 2022)"
            ),
        ]
    )
    def test_mds_icc2022_edge_cases(self, parsed_data, expected_classification):
        """Test edge cases and boundary conditions for MDS ICC 2022 classification."""
        result, derivation = classify_MDS_ICC2022(parsed_data)
        assert result == expected_classification
        assert isinstance(derivation, list)


class TestMDSComplexScenarios:
    """Test suite for complex MDS classification scenarios."""
    
    @pytest.mark.parametrize(
        "parsed_data, expected_who_classification, expected_icc_classification",
        [
            # Test Case 1: Complex scenario with multiple mutations and qualifiers
            (
                {
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": False,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": False,
                        "1_x_TP53_mutation_50_percent_vaf": False,
                        "1_x_TP53_mutation_10_percent_vaf": False
                    },
                    "blasts_percentage": 12.0,
                    "fibrotic": False,
                    "MDS_related_mutation": {
                        "SF3B1": True,
                        "ASXL1": True,
                        "RUNX1": False
                    },
                    "MDS_related_cytogenetics": {
                        "del_5q": True,
                        "Complex_karyotype": True
                    },
                    "number_of_dysplastic_lineages": 3,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Cytotoxic chemotherapy",
                        "predisposing_germline_variant": "GATA2"
                    }
                },
                "MDS with biallelic TP53 inactivation (WHO 2022)",
                "MDS with mutated TP53 (ICC 2022)"
            ),
            # Test Case 2: Scenario where WHO and ICC differ (SF3B1 with qualifiers)
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 3.0,
                    "fibrotic": False,
                    "hypoplasia": False,
                    "MDS_related_mutation": {
                        "SF3B1": True,
                        "ASXL1": False
                    },
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "previous_cytotoxic_therapy": "Immune interventions",
                        "predisposing_germline_variant": "RUNX1"
                    }
                },
                "MDS with low blasts and SF3B1, associated with RUNX1 (WHO 2022)",
                "MDS with mutated SF3B1, therapy related, in the setting of RUNX1 (ICC 2022)"
            ),
            # Test Case 3: Fibrotic case with multiple features
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 8.0,
                    "fibrotic": True,
                    "hypoplasia": False,
                    "MDS_related_mutation": {
                        "SF3B1": True
                    },
                    "MDS_related_cytogenetics": {
                        "del_5q": True
                    },
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {}
                },
                "MDS, fibrotic (WHO 2022)",
                "MDS with excess blasts (ICC 2022)"
            ),
            # Test Case 4: Hypoplastic MDS with germline predisposition
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 2.0,
                    "fibrotic": False,
                    "hypoplasia": True,
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "number_of_dysplastic_lineages": 1,
                    "qualifiers": {
                        "predisposing_germline_variant": "ANKRD26 (thrombocytopenia 2)"
                    }
                },
                "MDS, hypoplastic, associated with ANKRD26 (WHO 2022)",
                "MDS, NOS with single lineage dysplasia, in the setting of ANKRD26 (ICC 2022)"
            ),
            # Test Case 5: Multiple excluded variants
            (
                {
                    "Biallelic_TP53_mutation": {},
                    "blasts_percentage": 4.0,
                    "number_of_dysplastic_lineages": 2,
                    "qualifiers": {
                        "predisposing_germline_variant": "Diamond-Blackfan anemia, germline BLM mutation, GATA2"
                    }
                },
                "MDS with low blasts, associated with germline BLM mutation, GATA2 (WHO 2022)",
                "MDS, NOS with multilineage dysplasia, in the setting of Diamond-Blackfan anemia, GATA2 (ICC 2022)"
            ),
        ]
    )
    def test_complex_mds_scenarios(self, parsed_data, expected_who_classification, expected_icc_classification):
        """Test complex MDS classification scenarios where WHO and ICC may differ."""
        who_result, who_derivation = classify_MDS_WHO2022(parsed_data)
        icc_result, icc_derivation = classify_MDS_ICC2022(parsed_data)
        
        assert who_result == expected_who_classification
        assert icc_result == expected_icc_classification
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)
        assert len(who_derivation) > 0
        assert len(icc_derivation) > 0


class TestMDSErrorHandling:
    """Test suite for MDS classification error handling and robustness."""
    
    @pytest.mark.parametrize(
        "parsed_data",
        [
            # Test Case 1: Empty input
            {},
            # Test Case 2: Only partial data
            {"blasts_percentage": 5.0},
            # Test Case 3: Missing critical sections
            {
                "blasts_percentage": 10.0,
                "qualifiers": {}
            },
            # Test Case 4: All sections present but empty
            {
                "Biallelic_TP53_mutation": {},
                "blasts_percentage": 7.0,
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "qualifiers": {}
            },
        ]
    )
    def test_mds_robustness(self, parsed_data):
        """Test that MDS classification functions handle incomplete data gracefully."""
        # Should not raise exceptions
        who_result, who_derivation = classify_MDS_WHO2022(parsed_data)
        icc_result, icc_derivation = classify_MDS_ICC2022(parsed_data)
        
        # Results should be strings ending with classification system
        assert isinstance(who_result, str)
        assert isinstance(icc_result, str)
        assert who_result.endswith("(WHO 2022)")
        assert icc_result.endswith("(ICC 2022)")
        
        # Derivations should be lists
        assert isinstance(who_derivation, list)
        assert isinstance(icc_derivation, list)
    
    def test_mds_return_format(self):
        """Test that MDS classification functions return the expected format."""
        test_data = {
            "Biallelic_TP53_mutation": {},
            "blasts_percentage": 5.0,
            "MDS_related_mutation": {},
            "MDS_related_cytogenetics": {},
            "qualifiers": {}
        }
        
        who_result, who_derivation = classify_MDS_WHO2022(test_data)
        icc_result, icc_derivation = classify_MDS_ICC2022(test_data)
        
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
        print("MDS CLASSIFICATION TEST SUMMARY")
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