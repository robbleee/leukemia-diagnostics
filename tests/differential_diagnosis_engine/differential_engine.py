"""
Core differential diagnosis testing engine for comparing WHO 2022 vs ICC 2022 classifications.

This module provides the main testing engine that generates test cases, runs classifications,
and analyzes differences between the two systems in a systematic way.
"""

import json
import random
import itertools
from typing import Dict, List, Tuple, Optional, Generator
from dataclasses import dataclass, asdict
from datetime import datetime
import os
import sys

# Add the parent directory to the path to import classifiers
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from .diagnosis_mapping import (
    get_diagnosis_differences, are_equivalent_diagnoses, 
    get_test_focus_areas, categorize_diagnosis,
    generate_blast_test_cases, generate_therapy_test_cases, generate_germline_test_cases
)

@dataclass
class TestResult:
    """Represents the result of a single WHO vs ICC test case."""
    test_id: str
    input_data: Dict
    who_classification: str
    icc_classification: str
    who_derivation: List[str]
    icc_derivation: List[str]
    who_disease_type: str
    icc_disease_type: str
    are_equivalent: bool
    difference_analysis: Dict
    test_focus: str
    timestamp: str
    significance: str
    clinical_impact_score: float
    clinical_consequences: List[str]
    treatment_implications: List[str]
    mrd_implications: List[str]
    prognostic_implications: List[str]
    test_case: Dict

@dataclass
class TestSummary:
    """Summary statistics for a test run."""
    total_tests: int
    equivalent_results: int
    different_results: int
    high_significance_differences: int
    medium_significance_differences: int
    low_significance_differences: int
    differences_by_focus: Dict[str, int]
    differences_by_category: Dict[str, int]

class DifferentialDiagnosisEngine:
    """
    Main engine for testing differences between WHO 2022 and ICC 2022 classification systems.
    """
    
    def __init__(self, output_dir: str = "test_results"):
        """
        Initialize the differential diagnosis engine.
        
        Args:
            output_dir: Directory to save test results
        """
        self.output_dir = output_dir
        self.results: List[TestResult] = []
        self.test_counter = 0
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_test_id(self) -> str:
        """Generate a unique test ID."""
        self.test_counter += 1
        return f"test_{self.test_counter:06d}"
    
    def run_single_test(self, test_data: Dict, test_focus: str = "general") -> TestResult:
        """
        Run a single differential diagnosis test.
        
        Args:
            test_data: Dictionary containing patient data for testing
            test_focus: String describing the focus area of this test
            
        Returns:
            TestResult containing the analysis
        """
        test_id = f"test_{len(self.results) + 1}_{test_focus}"
        
        try:
            # Run WHO 2022 classification
            who_result, who_derivation, who_disease_type = classify_combined_WHO2022(
                test_data, not_erythroid=False
            )
            
            # Run ICC 2022 classification  
            icc_result, icc_derivation, icc_disease_type = classify_combined_ICC2022(test_data)
            
            # Analyze differences
            difference_analysis = get_diagnosis_differences(who_result, icc_result)
            
            # Create result with all clinical impact data
            return TestResult(
                test_id=test_id,
                input_data=test_data,
                who_classification=difference_analysis["who_classification"],
                icc_classification=difference_analysis["icc_classification"],
                who_derivation=who_derivation,
                icc_derivation=icc_derivation,
                who_disease_type=difference_analysis["who_category"],
                icc_disease_type=difference_analysis["icc_category"],
                are_equivalent=difference_analysis["are_equivalent"],
                difference_analysis=difference_analysis,
                test_focus=test_focus,
                timestamp=datetime.now().isoformat(),
                significance=difference_analysis["significance"],
                clinical_impact_score=difference_analysis["clinical_impact_score"],
                clinical_consequences=difference_analysis["clinical_consequences"],
                treatment_implications=difference_analysis["treatment_implications"],
                mrd_implications=difference_analysis["mrd_implications"],
                prognostic_implications=difference_analysis["prognostic_implications"],
                test_case=test_data
            )
            
        except Exception as e:
            return TestResult(
                test_id=test_id,
                input_data=test_data,
                who_classification=f"ERROR: {str(e)}",
                icc_classification=f"ERROR: {str(e)}",
                who_derivation=[f"Error during WHO classification: {str(e)}"],
                icc_derivation=[f"Error during ICC classification: {str(e)}"],
                who_disease_type="ERROR",
                icc_disease_type="ERROR",
                are_equivalent=False,
                difference_analysis={"error": True, "message": str(e)},
                test_focus=test_focus,
                timestamp=datetime.now().isoformat(),
                significance="critical",
                clinical_impact_score=0.0,
                clinical_consequences=[f"Error during classification: {str(e)}"],
                treatment_implications=[],
                mrd_implications=[],
                prognostic_implications=[],
                test_case=test_data
            )
    
    def generate_comprehensive_test_cases(self) -> List[Dict]:
        """
        Generate a comprehensive set of test cases targeting known difference areas.
        
        Returns:
            List of test case dictionaries
        """
        all_test_cases = []
        
        # 1. Blast threshold tests
        blast_cases = generate_blast_test_cases()
        all_test_cases.extend(blast_cases)
        
        # 2. Therapy qualifier tests
        therapy_cases = generate_therapy_test_cases()
        all_test_cases.extend(therapy_cases)
        
        # 3. Germline variant tests
        germline_cases = generate_germline_test_cases()
        all_test_cases.extend(germline_cases)
        
        # 4. TP53 terminology tests
        tp53_cases = self._generate_tp53_test_cases()
        all_test_cases.extend(tp53_cases)
        
        # 5. MDS blast range tests
        mds_blast_cases = self._generate_mds_blast_test_cases()
        all_test_cases.extend(mds_blast_cases)
        
        # 6. Erythroid handling tests
        erythroid_cases = self._generate_erythroid_test_cases()
        all_test_cases.extend(erythroid_cases)
        
        # 7. Combination scenario tests
        combination_cases = self._generate_combination_test_cases()
        all_test_cases.extend(combination_cases)
        
        # 8. Edge case tests
        edge_cases = self._generate_edge_case_tests()
        all_test_cases.extend(edge_cases)
        
        # 9. Realistic clinical scenarios
        realistic_cases = self._generate_realistic_clinical_scenarios()
        all_test_cases.extend(realistic_cases)
        
        # 10. Age-dependent differences
        age_cases = self._generate_age_dependent_test_cases()
        all_test_cases.extend(age_cases)
        
        # 11. Complex cytogenetic cases
        cytogenetic_cases = self._generate_complex_cytogenetic_test_cases()
        all_test_cases.extend(cytogenetic_cases)
        
        # 12. Co-mutation pattern tests
        comutation_cases = self._generate_comutation_test_cases()
        all_test_cases.extend(comutation_cases)
        
        # 13. Therapy evolution tests
        therapy_evolution_cases = self._generate_therapy_evolution_test_cases()
        all_test_cases.extend(therapy_evolution_cases)
        
        # 14. NEW: AML vs MDS borderline cases
        aml_vs_mds_cases = self._generate_aml_vs_mds_borderline_cases()
        all_test_cases.extend(aml_vs_mds_cases)
        
        # 15. NEW: Disease type disagreement cases
        disease_type_cases = self._generate_disease_type_disagreement_cases()
        all_test_cases.extend(disease_type_cases)
        
        return all_test_cases
    
    def _generate_tp53_test_cases(self) -> List[Dict]:
        """Generate test cases focusing on TP53 differences."""
        test_cases = []
        
        tp53_conditions = [
            {"2_x_TP53_mutations": True},
            {"1_x_TP53_mutation_del_17p": True},
            {"1_x_TP53_mutation_LOH": True},
            {"1_x_TP53_mutation_50_percent_vaf": True},
            {"1_x_TP53_mutation_10_percent_vaf": True},
        ]
        
        blast_ranges = [5, 10, 15, 20, 25]
        
        for tp53_condition in tp53_conditions:
            for blast_pct in blast_ranges:
                # AML case
                test_case = {
                    "blasts_percentage": blast_pct,
                    "Biallelic_TP53_mutation": tp53_condition,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {},
                    "test_focus": "tp53_terminology"
                }
                test_cases.append(test_case)
                
                # MDS case with complex karyotype
                if "1_x_TP53_mutation_10_percent_vaf" in tp53_condition:
                    mds_case = test_case.copy()
                    mds_case["MDS_related_cytogenetics"] = {"Complex_karyotype": True}
                    test_cases.append(mds_case)
        
        return test_cases
    
    def _generate_mds_blast_test_cases(self) -> List[Dict]:
        """Generate test cases focusing on MDS blast percentage differences."""
        test_cases = []
        
        # Critical blast percentages for MDS
        blast_values = [4, 5, 8, 9, 10, 15, 19, 20]
        
        # Different MDS scenarios
        scenarios = [
            {"scenario": "pure_blasts", "extras": {}},
            {"scenario": "with_sf3b1", "extras": {"MDS_related_mutation": {"SF3B1": True}}},
            {"scenario": "with_del5q", "extras": {"MDS_related_cytogenetics": {"del_5q": True}}},
            {"scenario": "with_dysplasia", "extras": {"number_of_dysplastic_lineages": 2}},
            {"scenario": "fibrotic", "extras": {"fibrotic": True}},
            {"scenario": "hypoplastic", "extras": {"hypoplasia": True}},
        ]
        
        for blast_pct in blast_values:
            for scenario in scenarios:
                test_case = {
                    "blasts_percentage": blast_pct,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "Biallelic_TP53_mutation": {},
                    "qualifiers": {},
                    "test_focus": "mds_blast_ranges"
                }
                
                # Add scenario-specific data
                test_case.update(scenario["extras"])
                test_cases.append(test_case)
        
        return test_cases
    
    def _generate_erythroid_test_cases(self) -> List[Dict]:
        """Generate test cases focusing on erythroid differentiation."""
        test_cases = []
        
        erythroid_differentiations = ["M6a", "M6b"]
        blast_values = [15, 20, 25, 30]
        
        for diff in erythroid_differentiations:
            for blast_pct in blast_values:
                test_case = {
                    "blasts_percentage": blast_pct,
                    "AML_differentiation": diff,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "qualifiers": {},
                    "test_focus": "erythroid_handling"
                }
                test_cases.append(test_case)
        
        return test_cases
    
    def _generate_combination_test_cases(self) -> List[Dict]:
        """Generate test cases with multiple confounding factors."""
        test_cases = []
        
        # Complex scenarios that combine multiple difference areas
        complex_scenarios = [
            {
                "name": "blast_threshold_with_therapy",
                "data": {
                    "blasts_percentage": 15,
                    "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True},
                    "qualifiers": {"previous_cytotoxic_therapy": "Immune interventions"}
                }
            },
            {
                "name": "tp53_with_germline",
                "data": {
                    "blasts_percentage": 20,
                    "Biallelic_TP53_mutation": {"2_x_TP53_mutations": True},
                    "qualifiers": {"predisposing_germline_variant": "Diamond-Blackfan anemia"}
                }
            },
            {
                "name": "mds_blasts_with_tp53_and_therapy",
                "data": {
                    "blasts_percentage": 12,
                    "Biallelic_TP53_mutation": {"1_x_TP53_mutation_del_17p": True},
                    "qualifiers": {"previous_cytotoxic_therapy": "Immune interventions"}
                }
            },
            {
                "name": "erythroid_with_mds_genetics",
                "data": {
                    "blasts_percentage": 25,
                    "AML_differentiation": "M6a",
                    "MDS_related_mutation": {"ASXL1": True, "SF3B1": True}
                }
            }
        ]
        
        for scenario in complex_scenarios:
            test_case = {
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {},
                "qualifiers": {},
                "test_focus": "combination_scenarios"
            }
            test_case.update(scenario["data"])
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_edge_case_tests(self) -> List[Dict]:
        """Generate edge case and boundary condition tests.""" 
        test_cases = []
        
        # Edge cases
        edge_cases = [
            {
                "name": "zero_blasts",
                "data": {"blasts_percentage": 0}
            },
            {
                "name": "exactly_100_blasts", 
                "data": {"blasts_percentage": 100}
            },
            {
                "name": "multiple_aml_genes",
                "data": {
                    "blasts_percentage": 25,
                    "AML_defining_recurrent_genetic_abnormalities": {
                        "NPM1": True,
                        "RUNX1::RUNX1T1": True, 
                        "CBFB::MYH11": True
                    }
                }
            },
            {
                "name": "all_mds_mutations",
                "data": {
                    "blasts_percentage": 8,
                    "MDS_related_mutation": {
                        "ASXL1": True, "RUNX1": True, "SF3B1": True,
                        "SRSF2": True, "U2AF1": True, "EZH2": True
                    }
                }
            },
            {
                "name": "all_tp53_conditions",
                "data": {
                    "blasts_percentage": 15,
                    "Biallelic_TP53_mutation": {
                        "2_x_TP53_mutations": True,
                        "1_x_TP53_mutation_del_17p": True,
                        "1_x_TP53_mutation_LOH": True,
                        "1_x_TP53_mutation_50_percent_vaf": True,
                        "1_x_TP53_mutation_10_percent_vaf": True
                    }
                }
            }
        ]
        
        for case in edge_cases:
            test_case = {
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {},
                "qualifiers": {},
                "test_focus": "edge_cases"
            }
            test_case.update(case["data"])
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_realistic_clinical_scenarios(self) -> List[Dict]:
        """Generate test cases based on realistic clinical presentations."""
        test_cases = []
        
        # Common real-world scenarios that often cause classification confusion
        realistic_scenarios = [
            {
                "name": "elderly_mds_with_tp53",
                "description": "Elderly patient with MDS and TP53 mutation - classic high-risk scenario",
                "data": {
                    "blasts_percentage": 12,
                    "Biallelic_TP53_mutation": {"1_x_TP53_mutation_50_percent_vaf": True},
                    "MDS_related_mutation": {"ASXL1": True},
                    "MDS_related_cytogenetics": {"Complex_karyotype": True},
                    "age": 75
                }
            },
            {
                "name": "young_adult_npm1_aml",
                "description": "Young adult with NPM1+ AML - good prognosis group",
                "data": {
                    "blasts_percentage": 85,
                    "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
                    "age": 28
                }
            },
            {
                "name": "aml_with_antecedent_mds",
                "description": "AML evolving from prior MDS - therapy-related scenario",
                "data": {
                    "blasts_percentage": 35,
                    "MDS_related_mutation": {"SF3B1": True, "RUNX1": True},
                    "qualifiers": {"previous_myeloid_malignancy": "Previous MDS"}
                }
            },
            {
                "name": "core_binding_factor_aml",
                "description": "Core-binding factor AML with good prognosis",
                "data": {
                    "blasts_percentage": 45,
                    "AML_defining_recurrent_genetic_abnormalities": {"RUNX1::RUNX1T1": True}
                }
            },
            {
                "name": "therapy_related_aml_tp53",
                "description": "Therapy-related AML with TP53 mutation - poor prognosis",
                "data": {
                    "blasts_percentage": 65,
                    "Biallelic_TP53_mutation": {"1_x_TP53_mutation_del_17p": True},
                    "qualifiers": {"previous_cytotoxic_therapy": "Cytotoxic chemotherapy"}
                }
            },
            {
                "name": "mds_sf3b1_ring_sideroblasts",
                "description": "MDS with SF3B1 mutation and ring sideroblasts",
                "data": {
                    "blasts_percentage": 3,
                    "MDS_related_mutation": {"SF3B1": True},
                    "number_of_dysplastic_lineages": 1
                }
            },
            {
                "name": "hypoplastic_mds",
                "description": "Hypoplastic MDS - can mimic aplastic anemia",
                "data": {
                    "blasts_percentage": 8,
                    "hypoplasia": True,
                    "MDS_related_mutation": {"ASXL1": True},
                    "number_of_dysplastic_lineages": 2
                }
            },
            {
                "name": "fibrotic_mds",
                "description": "Fibrotic MDS - difficult to aspirate marrow",
                "data": {
                    "blasts_percentage": 15,
                    "fibrotic": True,
                    "MDS_related_cytogenetics": {"del_5q": True}
                }
            }
        ]
        
        for scenario in realistic_scenarios:
            test_case = {
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {},
                "qualifiers": {},
                "test_focus": "realistic_clinical_scenarios",
                "scenario_name": scenario["name"],
                "scenario_description": scenario["description"]
            }
            test_case.update(scenario["data"])
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_age_dependent_test_cases(self) -> List[Dict]:
        """Generate test cases focusing on age-dependent classification differences."""
        test_cases = []
        
        # Age groups with different classification implications
        age_scenarios = [
            {"age_group": "pediatric", "age": 12, "blasts": 25},
            {"age_group": "young_adult", "age": 25, "blasts": 20},
            {"age_group": "middle_aged", "age": 55, "blasts": 18},
            {"age_group": "elderly", "age": 78, "blasts": 15}
        ]
        
        # Genetic contexts that might be age-dependent
        genetic_contexts = [
            {"name": "cebpa_bzip", "genetics": {"CEBPA": True, "bZIP": True}},
            {"name": "npm1_flt3", "genetics": {"NPM1": True, "FLT3_ITD": True}},
            {"name": "runx1_germline", "genetics": {}, "qualifiers": {"predisposing_germline_variant": "germline RUNX1 mutation"}},
            {"name": "ddx41_germline", "genetics": {}, "qualifiers": {"predisposing_germline_variant": "germline DDX41 mutation"}}
        ]
        
        for age_scenario in age_scenarios:
            for genetic_context in genetic_contexts:
                test_case = {
                    "blasts_percentage": age_scenario["blasts"],
                    "age": age_scenario["age"],
                    "AML_defining_recurrent_genetic_abnormalities": genetic_context.get("genetics", {}),
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "Biallelic_TP53_mutation": {},
                    "qualifiers": genetic_context.get("qualifiers", {}),
                    "test_focus": "age_dependent_differences",
                    "age_group": age_scenario["age_group"],
                    "genetic_context": genetic_context["name"]
                }
                test_cases.append(test_case)
        
        return test_cases
    
    def _generate_complex_cytogenetic_test_cases(self) -> List[Dict]:
        """Generate test cases with complex, realistic cytogenetic abnormalities."""
        test_cases = []
        
        # Complex cytogenetic scenarios commonly seen clinically
        cytogenetic_scenarios = [
            {
                "name": "complex_karyotype_tp53",
                "description": "Complex karyotype with TP53 mutation",
                "cytogenetics": {"Complex_karyotype": True, "del_17p": True},
                "tp53": {"1_x_TP53_mutation_del_17p": True},
                "blasts": 22
            },
            {
                "name": "del5q_syndrome_progression",
                "description": "del(5q) syndrome with blast progression",
                "cytogenetics": {"del_5q": True},
                "blasts": 18,
                "mds_mutations": {"ASXL1": True}
            },
            {
                "name": "monosomy7_childhood",
                "description": "Monosomy 7 in young patient",
                "cytogenetics": {"-7": True},
                "blasts": 25,
                "age": 8
            },
            {
                "name": "inv3_evi1_aml",
                "description": "inv(3) with EVI1 rearrangement",
                "cytogenetics": {"inv3_t33": True},
                "blasts": 45,
                "mds_mutations": {"EVI1": True}
            },
            {
                "name": "del7q_mds",
                "description": "del(7q) in MDS",
                "cytogenetics": {"del_7q": True},
                "blasts": 8,
                "mds_mutations": {"RUNX1": True}
            },
            {
                "name": "normal_karyotype_multiple_mutations",
                "description": "Normal karyotype with multiple mutations",
                "cytogenetics": {},
                "blasts": 28,
                "mds_mutations": {"DNMT3A": True, "TET2": True, "ASXL1": True}
            }
        ]
        
        for scenario in cytogenetic_scenarios:
            test_case = {
                "blasts_percentage": scenario["blasts"],
                "MDS_related_cytogenetics": scenario["cytogenetics"],
                "MDS_related_mutation": scenario.get("mds_mutations", {}),
                "Biallelic_TP53_mutation": scenario.get("tp53", {}),
                "AML_defining_recurrent_genetic_abnormalities": {},
                "qualifiers": {},
                "test_focus": "complex_cytogenetics",
                "scenario_name": scenario["name"],
                "scenario_description": scenario["description"]
            }
            
            if "age" in scenario:
                test_case["age"] = scenario["age"]
                
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_comutation_test_cases(self) -> List[Dict]:
        """Generate test cases with clinically relevant co-occurring mutations."""
        test_cases = []
        
        # Realistic co-mutation patterns observed in clinical practice
        comutation_patterns = [
            {
                "name": "dnmt3a_npm1_flt3",
                "description": "DNMT3A + NPM1 + FLT3-ITD triple mutation",
                "aml_genes": {"NPM1": True, "FLT3_ITD": True},
                "mds_genes": {"DNMT3A": True},
                "blasts": 75
            },
            {
                "name": "tet2_sf3b1_mds",
                "description": "TET2 + SF3B1 in MDS with ring sideroblasts",
                "mds_genes": {"TET2": True, "SF3B1": True},
                "blasts": 5
            },
            {
                "name": "asxl1_runx1_poor_risk",
                "description": "ASXL1 + RUNX1 mutations - poor risk combination",
                "mds_genes": {"ASXL1": True, "RUNX1": True},
                "blasts": 16
            },
            {
                "name": "tp53_complex_karyotype",
                "description": "TP53 mutation with complex karyotype",
                "tp53": {"2_x_TP53_mutations": True},
                "cytogenetics": {"Complex_karyotype": True},
                "blasts": 35
            },
            {
                "name": "srsf2_tet2_cmml_like",
                "description": "SRSF2 + TET2 mutations - CMML-like pattern",
                "mds_genes": {"SRSF2": True, "TET2": True},
                "blasts": 12
            },
            {
                "name": "u2af1_dnmt3a_secondary",
                "description": "U2AF1 + DNMT3A in therapy-related MDS",
                "mds_genes": {"U2AF1": True, "DNMT3A": True},
                "blasts": 9,
                "therapy": "Cytotoxic chemotherapy"
            },
            {
                "name": "ezh2_asxl1_high_risk",
                "description": "EZH2 + ASXL1 high-risk combination",
                "mds_genes": {"EZH2": True, "ASXL1": True},
                "blasts": 14
            }
        ]
        
        for pattern in comutation_patterns:
            test_case = {
                "blasts_percentage": pattern["blasts"],
                "AML_defining_recurrent_genetic_abnormalities": pattern.get("aml_genes", {}),
                "MDS_related_mutation": pattern.get("mds_genes", {}),
                "MDS_related_cytogenetics": pattern.get("cytogenetics", {}),
                "Biallelic_TP53_mutation": pattern.get("tp53", {}),
                "qualifiers": {},
                "test_focus": "comutation_patterns",
                "pattern_name": pattern["name"],
                "pattern_description": pattern["description"]
            }
            
            if "therapy" in pattern:
                test_case["qualifiers"]["previous_cytotoxic_therapy"] = pattern["therapy"]
                
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_therapy_evolution_test_cases(self) -> List[Dict]:
        """Generate test cases showing realistic disease evolution after therapy."""
        test_cases = []
        
        # Realistic scenarios of disease progression/evolution
        evolution_scenarios = [
            {
                "name": "mds_to_aml_progression",
                "description": "MDS progression to AML with acquired mutations",
                "initial_blasts": 8,
                "final_blasts": 25,
                "baseline_mutations": {"SF3B1": True},
                "acquired_mutations": {"NRAS": True},
                "therapy": "Previous MDS"
            },
            {
                "name": "post_chemo_aml_tp53",
                "description": "Therapy-related AML with TP53 after chemotherapy",
                "final_blasts": 45,
                "acquired_mutations": {},
                "tp53": {"1_x_TP53_mutation_50_percent_vaf": True},
                "cytogenetics": {"Complex_karyotype": True},
                "therapy": "Cytotoxic chemotherapy"
            },
            {
                "name": "relapsed_aml_new_mutations",
                "description": "Relapsed AML with additional mutations",
                "final_blasts": 60,
                "baseline_mutations": {"NPM1": True},
                "acquired_mutations": {"TP53": True},
                "therapy": "Cytotoxic chemotherapy"
            },
            {
                "name": "post_radiation_mds",
                "description": "Radiation-induced MDS with del(5q)",
                "final_blasts": 12,
                "cytogenetics": {"del_5q": True, "Complex_karyotype": True},
                "therapy": "Ionising radiation"
            },
            {
                "name": "immune_therapy_related",
                "description": "Post-immunotherapy myeloid neoplasm",
                "final_blasts": 18,
                "acquired_mutations": {"ASXL1": True, "TET2": True},
                "therapy": "Immune interventions"
            }
        ]
        
        for scenario in evolution_scenarios:
            # Create test case for the evolved/final state
            test_case = {
                "blasts_percentage": scenario["final_blasts"],
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": scenario.get("cytogenetics", {}),
                "Biallelic_TP53_mutation": scenario.get("tp53", {}),
                "qualifiers": {"previous_cytotoxic_therapy": scenario["therapy"]},
                "test_focus": "therapy_evolution",
                "scenario_name": scenario["name"],
                "scenario_description": scenario["description"]
            }
            
            # Add baseline and acquired mutations
            all_mutations = {**scenario.get("baseline_mutations", {}), **scenario.get("acquired_mutations", {})}
            test_case["MDS_related_mutation"].update(all_mutations)
            
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_aml_vs_mds_borderline_cases(self) -> List[Dict]:
        """Generate test cases specifically targeting AML vs MDS disagreements."""
        test_cases = []
        
        # 1. Blast percentage borderline cases with genetic abnormalities
        borderline_blast_genetic_cases = [
            {
                "name": "blast_15_with_cebpa_bzip",
                "description": "15% blasts with CEBPA bZIP mutation - ICC may call AML, WHO may call MDS",
                "data": {
                    "blasts_percentage": 15,
                    "AML_defining_recurrent_genetic_abnormalities": {"CEBPA_bZIP": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_12_with_npm1",
                "description": "12% blasts with NPM1 mutation - borderline case",
                "data": {
                    "blasts_percentage": 12,
                    "AML_defining_recurrent_genetic_abnormalities": {"NPM1_mutation": True},
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_18_with_runx1_runx1t1",
                "description": "18% blasts with RUNX1-RUNX1T1 fusion",
                "data": {
                    "blasts_percentage": 18,
                    "AML_defining_recurrent_genetic_abnormalities": {"RUNX1_RUNX1T1": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_16_with_inv16",
                "description": "16% blasts with inv(16) - core binding factor",
                "data": {
                    "blasts_percentage": 16,
                    "AML_defining_recurrent_genetic_abnormalities": {"CBFB_MYH11": True},
                    "dysplastic_lineages": 0,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # 2. MDS-related mutations with borderline blast counts
        mds_related_borderline_cases = [
            {
                "name": "blast_19_with_sf3b1_asxl1",
                "description": "19% blasts with SF3B1 and ASXL1 mutations",
                "data": {
                    "blasts_percentage": 19,
                    "MDS_related_mutation": {"SF3B1": True, "ASXL1": True},
                    "dysplastic_lineages": 3,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_21_with_tet2_dnmt3a",
                "description": "21% blasts with TET2 and DNMT3A mutations",
                "data": {
                    "blasts_percentage": 21,
                    "MDS_related_mutation": {"TET2": True, "DNMT3A": True},
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_18_with_srsf2_u2af1",
                "description": "18% blasts with SRSF2 and U2AF1 mutations",
                "data": {
                    "blasts_percentage": 18,
                    "MDS_related_mutation": {"SRSF2": True, "U2AF1": True},
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # 3. Therapy-related borderline cases
        therapy_related_borderline_cases = [
            {
                "name": "tr_blast_15_with_tp53",
                "description": "Therapy-related case with 15% blasts and TP53 mutation",
                "data": {
                    "blasts_percentage": 15,
                    "Biallelic_TP53_mutation": {"1_x_TP53_mutation_50_percent_vaf": True},
                    "therapy_qualifier": "Cytotoxic chemotherapy",
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "tr_blast_22_complex_karyotype",
                "description": "Therapy-related case with 22% blasts and complex karyotype",
                "data": {
                    "blasts_percentage": 22,
                    "complex_karyotype": True,
                    "therapy_qualifier": "Ionising radiation",
                    "dysplastic_lineages": 3,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # 4. Erythroid predominant cases
        erythroid_borderline_cases = [
            {
                "name": "erythroid_blast_18_dysplastic",
                "description": "18% blasts with erythroid predominance and dysplasia",
                "data": {
                    "blasts_percentage": 18,
                    "AML_differentiation": "M6",
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "erythroid_blast_25_with_sf3b1",
                "description": "25% blasts with erythroid features and SF3B1 mutation",
                "data": {
                    "blasts_percentage": 25,
                    "AML_differentiation": "M6",
                    "MDS_related_mutation": {"SF3B1": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # 5. Complex cases with mixed features
        mixed_feature_cases = [
            {
                "name": "blast_19_npm1_with_dysplasia",
                "description": "19% blasts with NPM1 mutation but significant dysplasia",
                "data": {
                    "blasts_percentage": 19,
                    "AML_defining_recurrent_genetic_abnormalities": {"NPM1_mutation": True},
                    "MDS_related_mutation": {"DNMT3A": True, "TET2": True},
                    "dysplastic_lineages": 3,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_17_flt3_with_mds_changes",
                "description": "17% blasts with FLT3-ITD and MDS-related changes",
                "data": {
                    "blasts_percentage": 17,
                    "AML_defining_recurrent_genetic_abnormalities": {"FLT3_ITD": True},
                    "MDS_related_mutation": {"ASXL1": True, "SRSF2": True},
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_21_cebpa_with_complex_karyotype",
                "description": "21% blasts with CEBPA mutation and complex karyotype",
                "data": {
                    "blasts_percentage": 21,
                    "AML_defining_recurrent_genetic_abnormalities": {"CEBPA_bZIP": True},
                    "complex_karyotype": True,
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # 6. Cases with previous MDS history
        previous_mds_cases = [
            {
                "name": "previous_mds_blast_18",
                "description": "18% blasts in patient with previous MDS diagnosis",
                "data": {
                    "blasts_percentage": 18,
                    "MDS_related_mutation": {"TET2": True, "SF3B1": True},
                    "previous_mds_mpn": "Previous MDS",
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "previous_mds_blast_22_with_new_mutation",
                "description": "22% blasts with previous MDS and new AML-defining mutation",
                "data": {
                    "blasts_percentage": 22,
                    "AML_defining_recurrent_genetic_abnormalities": {"NPM1_mutation": True},
                    "MDS_related_mutation": {"TET2": True},
                    "previous_mds_mpn": "Previous MDS",
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # Combine all borderline cases
        all_borderline_cases = (
            borderline_blast_genetic_cases + 
            mds_related_borderline_cases + 
            therapy_related_borderline_cases + 
            erythroid_borderline_cases + 
            mixed_feature_cases + 
            previous_mds_cases
        )
        
        for case in all_borderline_cases:
            test_cases.append({
                "test_name": case["name"],
                "description": case["description"],
                "test_focus": "aml_vs_mds_borderline",
                "expected_difference": True,
                "significance": "high",
                **case["data"]
            })
        
        return test_cases

    def _generate_disease_type_disagreement_cases(self) -> List[Dict]:
        """Generate test cases specifically designed to cause disease type disagreements."""
        test_cases = []
        
        # Cases targeting WHO AML vs ICC MDS
        who_aml_icc_mds_cases = [
            {
                "name": "who_aml_icc_mds_blast_20_with_dysplasia",
                "description": "20% blasts with extensive dysplasia - WHO may favor AML, ICC may favor MDS",
                "data": {
                    "blasts_percentage": 20,
                    "dysplastic_lineages": 3,
                    "MDS_related_mutation": {"ASXL1": True, "TET2": True, "SRSF2": True},
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_20_with_ring_sideroblasts",
                "description": "20% blasts with >15% ring sideroblasts and SF3B1 mutation",
                "data": {
                    "blasts_percentage": 20,
                    "MDS_related_mutation": {"SF3B1": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular",
                    "ring_sideroblasts_percent": 25
                }
            }
        ]
        
        # Cases targeting WHO MDS vs ICC AML
        who_mds_icc_aml_cases = [
            {
                "name": "who_mds_icc_aml_blast_15_cebpa",
                "description": "15% blasts with CEBPA bZIP - ICC may call AML, WHO may call MDS",
                "data": {
                    "blasts_percentage": 15,
                    "AML_defining_recurrent_genetic_abnormalities": {"CEBPA_bZIP": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_12_with_bcr_abl1",
                "description": "12% blasts with BCR::ABL1 fusion",
                "data": {
                    "blasts_percentage": 12,
                    "AML_defining_recurrent_genetic_abnormalities": {"BCR::ABL1": True},
                    "dysplastic_lineages": 0,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "blast_18_with_kmt2a_rearrangement",
                "description": "18% blasts with KMT2A rearrangement",
                "data": {
                    "blasts_percentage": 18,
                    "AML_defining_recurrent_genetic_abnormalities": {"KMT2A_rearranged": True},
                    "dysplastic_lineages": 0,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        # Therapy-related cases with ambiguous classification
        therapy_related_ambiguous_cases = [
            {
                "name": "tr_blast_15_immune_intervention",
                "description": "15% blasts after immune intervention therapy",
                "data": {
                    "blasts_percentage": 15,
                    "therapy_qualifier": "Immune interventions (ICC)",
                    "MDS_related_mutation": {"TP53": True},
                    "dysplastic_lineages": 2,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            },
            {
                "name": "tr_blast_19_with_aml_mutation",
                "description": "19% blasts after chemotherapy with new AML-defining mutation",
                "data": {
                    "blasts_percentage": 19,
                    "therapy_qualifier": "Cytotoxic chemotherapy",
                    "AML_defining_recurrent_genetic_abnormalities": {"NPM1_mutation": True},
                    "dysplastic_lineages": 1,
                    "bone_marrow_cellularity": "Hypercellular"
                }
            }
        ]
        
        all_disease_type_cases = (
            who_aml_icc_mds_cases + 
            who_mds_icc_aml_cases + 
            therapy_related_ambiguous_cases
        )
        
        for case in all_disease_type_cases:
            test_cases.append({
                "test_name": case["name"],
                "description": case["description"],
                "test_focus": "disease_type_disagreement",
                "expected_difference": True,
                "significance": "high",
                **case["data"]
            })
        
        return test_cases

    def analyze_disease_type_disagreements(self) -> Dict[str, any]:
        """Analyze patterns in disease type disagreements between WHO and ICC."""
        disease_type_disagreements = []
        aml_vs_mds_patterns = {
            "who_aml_icc_mds": [],
            "who_mds_icc_aml": [],
            "blast_range_analysis": {},
            "mutation_patterns": {},
            "therapy_related_patterns": {}
        }
        
        for result in self.results:
            if result.who_disease_type != result.icc_disease_type:
                disease_type_disagreements.append(result)
                
                # Categorize the disagreement type
                if result.who_disease_type == "AML" and result.icc_disease_type == "MDS":
                    aml_vs_mds_patterns["who_aml_icc_mds"].append(result)
                elif result.who_disease_type == "MDS" and result.icc_disease_type == "AML":
                    aml_vs_mds_patterns["who_mds_icc_aml"].append(result)
                
                # Analyze blast percentage patterns
                blast_pct = result.input_data.get("blasts_percentage", 0)
                blast_range = self._get_blast_range(blast_pct)
                if blast_range not in aml_vs_mds_patterns["blast_range_analysis"]:
                    aml_vs_mds_patterns["blast_range_analysis"][blast_range] = []
                aml_vs_mds_patterns["blast_range_analysis"][blast_range].append(result)
                
                # Analyze mutation patterns
                aml_mutations = result.input_data.get("AML_defining_recurrent_genetic_abnormalities", {})
                mds_mutations = result.input_data.get("MDS_related_mutation", {})
                
                for mutation, present in aml_mutations.items():
                    if present:
                        if mutation not in aml_vs_mds_patterns["mutation_patterns"]:
                            aml_vs_mds_patterns["mutation_patterns"][mutation] = {"aml_defining": 0, "disagreements": 0}
                        aml_vs_mds_patterns["mutation_patterns"][mutation]["aml_defining"] += 1
                        aml_vs_mds_patterns["mutation_patterns"][mutation]["disagreements"] += 1
                
                for mutation, present in mds_mutations.items():
                    if present:
                        if mutation not in aml_vs_mds_patterns["mutation_patterns"]:
                            aml_vs_mds_patterns["mutation_patterns"][mutation] = {"mds_related": 0, "disagreements": 0}
                        aml_vs_mds_patterns["mutation_patterns"][mutation]["mds_related"] = aml_vs_mds_patterns["mutation_patterns"][mutation].get("mds_related", 0) + 1
                        aml_vs_mds_patterns["mutation_patterns"][mutation]["disagreements"] += 1
                
                # Analyze therapy-related patterns
                therapy_qualifier = result.input_data.get("therapy_qualifier")
                if therapy_qualifier and therapy_qualifier != "None":
                    if therapy_qualifier not in aml_vs_mds_patterns["therapy_related_patterns"]:
                        aml_vs_mds_patterns["therapy_related_patterns"][therapy_qualifier] = []
                    aml_vs_mds_patterns["therapy_related_patterns"][therapy_qualifier].append(result)
        
        return {
            "total_disease_type_disagreements": len(disease_type_disagreements),
            "disagreement_rate": len(disease_type_disagreements) / len(self.results) if self.results else 0,
            "patterns": aml_vs_mds_patterns,
            "detailed_cases": disease_type_disagreements[:10]  # First 10 for detailed review
        }
    
    def _get_blast_range(self, blast_pct: float) -> str:
        """Categorize blast percentage into ranges for analysis."""
        if blast_pct < 10:
            return "<10%"
        elif blast_pct < 15:
            return "10-14%"
        elif blast_pct < 20:
            return "15-19%"
        elif blast_pct < 25:
            return "20-24%"
        elif blast_pct < 30:
            return "25-29%"
        else:
            return "≥30%"
    
    def generate_targeted_test_cases(self, test_focus: str) -> List[Dict]:
        """
        Generate test cases focused on a specific area.
        
        Args:
            test_focus: The specific focus area for test generation
            
        Returns:
            List of test case dictionaries focused on the specified area
        """
        if test_focus == "blast_thresholds":
            return generate_blast_test_cases()
        elif test_focus == "therapy_qualifiers":
            return generate_therapy_test_cases() 
        elif test_focus == "germline_qualifiers":
            return generate_germline_test_cases()
        elif test_focus == "tp53_terminology":
            return self._generate_tp53_test_cases()
        elif test_focus == "mds_blast_ranges":
            return self._generate_mds_blast_test_cases()
        elif test_focus == "erythroid_handling":
            return self._generate_erythroid_test_cases()
        elif test_focus == "realistic_clinical_scenarios":
            return self._generate_realistic_clinical_scenarios()
        elif test_focus == "age_dependent_differences":
            return self._generate_age_dependent_test_cases()
        elif test_focus == "complex_cytogenetics":
            return self._generate_complex_cytogenetic_test_cases()
        elif test_focus == "comutation_patterns":
            return self._generate_comutation_test_cases()
        elif test_focus == "therapy_evolution":
            return self._generate_therapy_evolution_test_cases()
        elif test_focus == "aml_vs_mds_borderline":
            return self._generate_aml_vs_mds_borderline_cases()
        elif test_focus == "disease_type_disagreement":
            return self._generate_disease_type_disagreement_cases()
        else:
            # Default to comprehensive test cases
            return self.generate_comprehensive_test_cases()

    def run_comprehensive_test_suite(self, test_focus: str = "all", max_tests: Optional[int] = None) -> TestSummary:
        """
        Run a comprehensive suite of differential diagnosis tests.
        
        Args:
            test_focus: Focus area for testing
            max_tests: Maximum number of tests to run (None for unlimited)
            
        Returns:
            TestSummary with aggregated results
        """
        if test_focus == "all":
            test_cases = self.generate_comprehensive_test_cases()
        else:
            test_cases = self.generate_targeted_test_cases(test_focus)
        
        # Limit test cases if max_tests is specified
        if max_tests is not None:
            test_cases = test_cases[:max_tests]
        
        print(f"Running {len(test_cases)} differential diagnosis tests...")
        
        # Clear previous results
        self.results.clear()
        
        # Run each test
        for i, test_case in enumerate(test_cases, 1):
            print(f"Running test {i}/{len(test_cases)}...", end="\r")
            
            test_focus = test_case.pop("test_focus", "general")
            result = self.run_single_test(test_case, test_focus)
            self.results.append(result)
        
        # Generate summary
        return self._generate_summary()
    
    def _generate_summary(self) -> TestSummary:
        """Generate summary statistics from test results."""
        total = len(self.results)
        equivalent = sum(1 for r in self.results if r.are_equivalent)
        different = total - equivalent
        
        # Count by significance - only for NON-EQUIVALENT cases
        different_results = [r for r in self.results if not r.are_equivalent]
        
        high_sig = sum(1 for r in different_results 
                      if r.difference_analysis.get("significance") in ["high", "critical"])
        medium_sig = sum(1 for r in different_results 
                        if r.difference_analysis.get("significance") == "medium")
        low_sig = sum(1 for r in different_results 
                     if r.difference_analysis.get("significance") in ["low", "minimal"])
        
        # Count by test focus - only for non-equivalent cases
        focus_counts = {}
        for result in different_results:
            focus = result.test_focus
            focus_counts[focus] = focus_counts.get(focus, 0) + 1
        
        # Count by category differences - only for non-equivalent cases
        category_counts = {}
        for result in different_results:
            diff_type = result.difference_analysis.get("difference_type", "unknown")
            category_counts[diff_type] = category_counts.get(diff_type, 0) + 1
        
        return TestSummary(
            total_tests=total,
            equivalent_results=equivalent,
            different_results=different,
            high_significance_differences=high_sig,
            medium_significance_differences=medium_sig,
            low_significance_differences=low_sig,
            differences_by_focus=focus_counts,
            differences_by_category=category_counts
        )
    
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save test results to JSON file.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"differential_test_results_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Convert results to serializable format
        results_data = {
            "summary": asdict(self._generate_summary()),
            "test_results": [asdict(result) for result in self.results],
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results)
        }
        
        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Results saved to: {filepath}")
        return filepath
    
    def get_high_impact_differences(self) -> List[TestResult]:
        """
        Get test results with high-impact differences between WHO and ICC.
        
        Returns:
            List of TestResult objects with significant differences
        """
        return [
            result for result in self.results
            if not result.are_equivalent and 
            result.difference_analysis.get("significance") in ["high", "critical"]
        ]
    
    def analyze_difference_patterns(self) -> Dict[str, any]:
        """
        Analyze patterns in differences found between WHO and ICC classifications.
        
        Returns:
            Dictionary containing pattern analysis results
        """
        if not self.results:
            return {"error": "No test results available for analysis"}
        
        # Basic statistics
        total_tests = len(self.results)
        different_results = [r for r in self.results if not r.are_equivalent]
        
        # Focus area analysis
        focus_area_differences = {}
        for result in different_results:
            focus = result.test_focus
            if focus not in focus_area_differences:
                focus_area_differences[focus] = []
            focus_area_differences[focus].append(result)
        
        # Blast percentage analysis
        blast_difference_analysis = {}
        for result in different_results:
            blast_pct = result.input_data.get("blasts_percentage", 0)
            blast_range = self._get_blast_range(blast_pct)
            if blast_range not in blast_difference_analysis:
                blast_difference_analysis[blast_range] = []
            blast_difference_analysis[blast_range].append(result)
        
        # Mutation type analysis
        mutation_difference_patterns = {}
        for result in different_results:
            aml_mutations = result.input_data.get("AML_defining_recurrent_genetic_abnormalities", {})
            mds_mutations = result.input_data.get("MDS_related_mutation", {})
            
            for mutation, present in aml_mutations.items():
                if present:
                    if mutation not in mutation_difference_patterns:
                        mutation_difference_patterns[mutation] = {"count": 0, "aml_defining": True}
                    mutation_difference_patterns[mutation]["count"] += 1
            
            for mutation, present in mds_mutations.items():
                if present:
                    if mutation not in mutation_difference_patterns:
                        mutation_difference_patterns[mutation] = {"count": 0, "mds_related": True}
                    mutation_difference_patterns[mutation]["count"] += 1
        
        # Disease type disagreement analysis
        disease_type_analysis = self.analyze_disease_type_disagreements()
        
        # Significance level analysis
        significance_analysis = {
            "high": [r for r in different_results if r.difference_analysis.get("significance") in ["high", "critical"]],
            "medium": [r for r in different_results if r.difference_analysis.get("significance") == "medium"],
            "low": [r for r in different_results if r.difference_analysis.get("significance") in ["low", "minimal"]]
        }
        
        return {
            "total_tests": total_tests,
            "total_differences": len(different_results),
            "difference_rate": len(different_results) / total_tests,
            "focus_area_analysis": {area: len(cases) for area, cases in focus_area_differences.items()},
            "blast_range_analysis": {range_: len(cases) for range_, cases in blast_difference_analysis.items()},
            "mutation_patterns": mutation_difference_patterns,
            "disease_type_disagreements": disease_type_analysis,
            "significance_distribution": {level: len(cases) for level, cases in significance_analysis.items()},
            "detailed_focus_areas": focus_area_differences
        }
    
    def generate_difference_report(self) -> str:
        """
        Generate a comprehensive human-readable report of differences found.
        
        Returns:
            Formatted string report
        """
        if not self.results:
            return "No test results provided."
        
        # Group results by significance level
        critical_cases = []
        high_impact_cases = []
        medium_impact_cases = []
        low_impact_cases = []
        minimal_impact_cases = []
        
        for result in self.results:
            if result.significance == "critical":
                critical_cases.append(result)
            elif result.significance == "high":
                high_impact_cases.append(result)
            elif result.significance == "medium":
                medium_impact_cases.append(result)
            elif result.significance == "low":
                low_impact_cases.append(result)
            else:
                minimal_impact_cases.append(result)
        
        # Generate disease type disagreement analysis
        disease_disagreements = [r for r in self.results if r.who_disease_type != r.icc_disease_type and 
                               any(cat in ["AML_GENETIC", "MDS_BLASTS", "MDS_TP53", "MDS_AML_HYBRID"] 
                                   for cat in [r.who_disease_type, r.icc_disease_type])]
        
        report = []
        report.append("=" * 80)
        report.append("BLOOD CANCER CLASSIFICATION DIFFERENCES REPORT")
        report.append("WHO 2022 vs ICC 2022 Classifications")
        report.append("=" * 80)
        report.append("")
        
        # Summary statistics with clinical impact focus
        report.append("SUMMARY STATISTICS")
        report.append("-" * 40)
        report.append(f"Total test cases analyzed: {len(self.results)}")
        report.append(f"Cases with differences: {len([r for r in self.results if not r.are_equivalent])}")
        report.append(f"Disease type disagreements: {len(disease_disagreements)}")
        report.append("")
        
        # Clinical Impact Summary
        report.append("CLINICAL IMPACT SUMMARY")
        report.append("-" * 40)
        report.append(f"Critical Impact (Score ≥80): {len(critical_cases)}")
        report.append(f"High Impact (Score 50-79): {len(high_impact_cases)}")
        report.append(f"Medium Impact (Score 25-49): {len(medium_impact_cases)}")
        report.append(f"Low Impact (Score 1-24): {len(low_impact_cases)}")
        report.append(f"Minimal Impact (Score 0): {len(minimal_impact_cases)}")
        report.append("")
        
        # CRITICAL IMPACT CASES
        if critical_cases:
            report.append("🚨 CRITICAL CLINICAL IMPACT CASES (Score ≥80)")
            report.append("=" * 60)
            report.append("These differences have major treatment and outcome implications")
            report.append("")
            
            for i, result in enumerate(critical_cases, 1):
                report.append(f"CRITICAL CASE #{i} (Impact Score: {result.clinical_impact_score})")
                report.append("-" * 40)
                report.append(f"WHO 2022: {result.who_classification}")
                report.append(f"ICC 2022: {result.icc_classification}")
                report.append("")
                
                if result.clinical_consequences:
                    report.append("🏥 CLINICAL CONSEQUENCES:")
                    for consequence in result.clinical_consequences:
                        report.append(f"  • {consequence}")
                    report.append("")
                
                if result.treatment_implications:
                    report.append("💊 TREATMENT IMPLICATIONS:")
                    for treatment in result.treatment_implications:
                        report.append(f"  • {treatment}")
                    report.append("")
                
                if result.mrd_implications:
                    report.append("🔬 MRD MONITORING IMPLICATIONS:")
                    for mrd in result.mrd_implications:
                        report.append(f"  • {mrd}")
                    report.append("")
                
                if result.prognostic_implications:
                    report.append("📊 PROGNOSTIC IMPLICATIONS:")
                    for prognosis in result.prognostic_implications:
                        report.append(f"  • {prognosis}")
                    report.append("")
                
                # Test case details
                report.append("📋 TEST CASE DETAILS:")
                report.append(f"  • Age: {result.test_case.get('age', 'unknown')}")
                report.append(f"  • Blast %: {result.input_data.get('blasts_percentage', 'unknown')}")
                if hasattr(result.test_case, 'mutations') and result.test_case.get('mutations'):
                    report.append(f"  • Key mutations: {', '.join(result.test_case.get('mutations', [])[:5])}")
                if hasattr(result.test_case, 'cytogenetics') and result.test_case.get('cytogenetics'):
                    report.append(f"  • Cytogenetics: {result.test_case.get('cytogenetics', '')}")
                report.append("")
                report.append("-" * 60)
                report.append("")
        
        # HIGH IMPACT CASES
        if high_impact_cases:
            report.append("⚠️  HIGH CLINICAL IMPACT CASES (Score 50-79)")
            report.append("=" * 60)
            report.append("These differences have significant clinical implications")
            report.append("")
            
            for i, result in enumerate(high_impact_cases, 1):
                report.append(f"HIGH IMPACT CASE #{i} (Impact Score: {result.clinical_impact_score})")
                report.append("-" * 40)
                report.append(f"WHO 2022: {result.who_classification}")
                report.append(f"ICC 2022: {result.icc_classification}")
                report.append("")
                
                # Show key implications only for high impact cases
                if result.treatment_implications:
                    report.append("💊 Key Treatment Differences:")
                    for treatment in result.treatment_implications[:3]:  # Show top 3
                        report.append(f"  • {treatment}")
                    report.append("")
                
                if result.mrd_implications:
                    report.append("🔬 MRD Monitoring Differences:")
                    for mrd in result.mrd_implications[:2]:  # Show top 2
                        report.append(f"  • {mrd}")
                    report.append("")
                
                report.append("")
        
        # MEDIUM IMPACT CASES (Summary only)
        if medium_impact_cases:
            report.append("📋 MEDIUM CLINICAL IMPACT CASES (Score 25-49)")
            report.append("=" * 60)
            report.append(f"Found {len(medium_impact_cases)} cases with moderate clinical implications")
            report.append("")
            
            # Group by difference type
            medium_by_type = {}
            for result in medium_impact_cases:
                diff_type = result.difference_analysis.get("difference_type", "unknown")
                if diff_type not in medium_by_type:
                    medium_by_type[diff_type] = []
                medium_by_type[diff_type].append(result)
            
            for diff_type, cases in medium_by_type.items():
                report.append(f"• {diff_type.replace('_', ' ').title()}: {len(cases)} cases")
                if cases:
                    example = cases[0]
                    report.append(f"  Example: WHO '{example.who_classification}' vs ICC '{example.icc_classification}'")
                    if example.treatment_implications:
                        report.append(f"  Key difference: {example.treatment_implications[0]}")
            report.append("")
        
        # DISEASE TYPE DISAGREEMENT ANALYSIS
        if disease_disagreements:
            report.append("🔥 CRITICAL: DISEASE TYPE DISAGREEMENTS")
            report.append("=" * 60)
            report.append("Cases where classifications fall into different disease categories")
            report.append("(These have the highest clinical impact)")
            report.append("")
            
            # Analyze patterns
            who_aml_icc_mds = 0
            who_mds_icc_aml = 0
            other_disagreements = 0
            
            for result in disease_disagreements:
                if ("AML" in result.who_disease_type or result.who_disease_type == "APL") and \
                   ("MDS" in result.icc_disease_type):
                    who_aml_icc_mds += 1
                elif ("MDS" in result.who_disease_type) and \
                     ("AML" in result.icc_disease_type or result.icc_disease_type == "APL"):
                    who_mds_icc_aml += 1
                else:
                    other_disagreements += 1
            
            report.append(f"WHO→AML, ICC→MDS: {who_aml_icc_mds} cases")
            report.append(f"WHO→MDS, ICC→AML: {who_mds_icc_aml} cases") 
            report.append(f"Other disagreements: {other_disagreements} cases")
            report.append("")
            
            # Show examples of each pattern
            if who_mds_icc_aml > 0:
                example = next(r for r in disease_disagreements 
                              if ("MDS" in r.who_disease_type) and ("AML" in r.icc_disease_type))
                report.append("Most Common Pattern - WHO→MDS, ICC→AML:")
                report.append(f"  WHO: {example.who_classification}")
                report.append(f"  ICC: {example.icc_classification}")
                report.append(f"  Clinical Impact: Supportive care vs intensive chemotherapy")
                report.append("")
        
        # STATISTICAL INSIGHTS
        report.append("📊 CLINICAL IMPACT STATISTICS")
        report.append("=" * 60)
        
        if self.results:
            avg_impact = sum(r.clinical_impact_score for r in self.results) / len(self.results)
            max_impact = max(r.clinical_impact_score for r in self.results)
            
            report.append(f"Average Clinical Impact Score: {avg_impact:.1f}")
            report.append(f"Maximum Clinical Impact Score: {max_impact}")
            
            # Treatment implication statistics
            treatment_affected = len([r for r in self.results if r.treatment_implications])
            mrd_affected = len([r for r in self.results if r.mrd_implications])
            prognosis_affected = len([r for r in self.results if r.prognostic_implications])
            
            report.append(f"Cases affecting treatment decisions: {treatment_affected} ({100*treatment_affected/len(self.results):.1f}%)")
            report.append(f"Cases affecting MRD monitoring: {mrd_affected} ({100*mrd_affected/len(self.results):.1f}%)")
            report.append(f"Cases affecting prognosis: {prognosis_affected} ({100*prognosis_affected/len(self.results):.1f}%)")
            report.append("")
        
        # Add metadata
        report.append("REPORT METADATA")
        report.append("-" * 40)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Analysis: WHO 2022 vs ICC 2022 classifications")
        report.append(f"Focus: Clinical impact assessment")
        report.append("=" * 80)
        
        return "\n".join(report) 