"""
Utility functions for the differential diagnosis testing engine.

This module provides helper functions for data generation, validation,
and analysis support for the differential testing engine.
"""

import random
import itertools
from typing import Dict, List, Tuple, Any, Optional, Union
import json
import csv
from pathlib import Path


def generate_random_test_data(
    blast_range: Tuple[float, float] = (0, 100),
    include_aml_genes: bool = True,
    include_mds_mutations: bool = True,
    include_tp53: bool = True,
    include_qualifiers: bool = True,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate random test data for classification testing.
    
    Args:
        blast_range: Tuple of (min, max) blast percentage
        include_aml_genes: Whether to include AML-defining genes
        include_mds_mutations: Whether to include MDS-related mutations
        include_tp53: Whether to include TP53 data
        include_qualifiers: Whether to include qualifier data
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with random test data
    """
    if seed is not None:
        random.seed(seed)
    
    test_data = {
        "blasts_percentage": round(random.uniform(*blast_range), 1),
        "AML_defining_recurrent_genetic_abnormalities": {},
        "MDS_related_mutation": {},
        "MDS_related_cytogenetics": {},
        "Biallelic_TP53_mutation": {},
        "qualifiers": {}
    }
    
    # AML-defining genes
    if include_aml_genes:
        aml_genes = [
            "PML::RARA", "NPM1", "RUNX1::RUNX1T1", "CBFB::MYH11", 
            "DEK::NUP214", "RBM15::MRTFA", "KMT2A", "MECOM", 
            "NUP98", "CEBPA", "bZIP", "BCR::ABL1"
        ]
        # Randomly select 0-2 genes
        selected_genes = random.sample(aml_genes, random.randint(0, min(2, len(aml_genes))))
        for gene in selected_genes:
            test_data["AML_defining_recurrent_genetic_abnormalities"][gene] = True
    
    # MDS mutations
    if include_mds_mutations:
        mds_mutations = [
            "ASXL1", "RUNX1", "SF3B1", "SRSF2", "U2AF1", "EZH2",
            "BCOR", "STAG2", "TET2", "DNMT3A", "IDH1", "IDH2"
        ]
        # Randomly select 0-3 mutations
        selected_mutations = random.sample(mds_mutations, random.randint(0, min(3, len(mds_mutations))))
        for mutation in selected_mutations:
            test_data["MDS_related_mutation"][mutation] = True
    
    # MDS cytogenetics
    cyto_abnormalities = [
        "del_5q", "Complex_karyotype", "-7", "del_7q", "+8",
        "del_11q", "12p", "-13", "-17", "add_17p", "del_20q"
    ]
    selected_cyto = random.sample(cyto_abnormalities, random.randint(0, min(2, len(cyto_abnormalities))))
    for cyto in selected_cyto:
        test_data["MDS_related_cytogenetics"][cyto] = True
    
    # TP53 data
    if include_tp53:
        tp53_conditions = [
            "2_x_TP53_mutations", "1_x_TP53_mutation_del_17p",
            "1_x_TP53_mutation_LOH", "1_x_TP53_mutation_50_percent_vaf",
            "1_x_TP53_mutation_10_percent_vaf"
        ]
        # Small chance of TP53 abnormalities
        if random.random() < 0.15:  # 15% chance
            selected_tp53 = random.choice(tp53_conditions)
            test_data["Biallelic_TP53_mutation"][selected_tp53] = True
    
    # Qualifiers
    if include_qualifiers:
        therapies = ["None", "Ionising radiation", "Cytotoxic chemotherapy", "Immune interventions", "Any combination"]
        therapy = random.choice(therapies)
        if therapy != "None":
            test_data["qualifiers"]["previous_cytotoxic_therapy"] = therapy
        
        # Germline variants (small chance)
        if random.random() < 0.1:  # 10% chance
            variants = [
                "germline CEBPA mutation", "germline DDX41 mutation",
                "Diamond-Blackfan anemia", "germline BLM mutation",
                "Fanconi anaemia", "Down Syndrome"
            ]
            test_data["qualifiers"]["predisposing_germline_variant"] = random.choice(variants)
    
    return test_data


def generate_boundary_test_cases(parameter: str, values: List[Any]) -> List[Dict[str, Any]]:
    """
    Generate test cases around boundary values for a specific parameter.
    
    Args:
        parameter: Parameter name to test boundaries for
        values: List of boundary values to test
        
    Returns:
        List of test case dictionaries
    """
    base_case = {
        "blasts_percentage": 20.0,
        "AML_defining_recurrent_genetic_abnormalities": {},
        "MDS_related_mutation": {},
        "MDS_related_cytogenetics": {},
        "Biallelic_TP53_mutation": {},
        "qualifiers": {}
    }
    
    test_cases = []
    for value in values:
        case = base_case.copy()
        
        # Handle nested parameters
        if "." in parameter:
            parts = parameter.split(".")
            if parts[0] not in case:
                case[parts[0]] = {}
            case[parts[0]][parts[1]] = value
        else:
            case[parameter] = value
        
        test_cases.append(case)
    
    return test_cases


def validate_test_data(test_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate test data for consistency and completeness.
    
    Args:
        test_data: Test data dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = [
        "blasts_percentage",
        "AML_defining_recurrent_genetic_abnormalities",
        "MDS_related_mutation",
        "MDS_related_cytogenetics",
        "Biallelic_TP53_mutation",
        "qualifiers"
    ]
    
    for field in required_fields:
        if field not in test_data:
            errors.append(f"Missing required field: {field}")
    
    # Validate blast percentage
    blasts = test_data.get("blasts_percentage")
    if blasts is not None:
        if not isinstance(blasts, (int, float)):
            errors.append("blasts_percentage must be a number")
        elif not 0 <= blasts <= 100:
            errors.append("blasts_percentage must be between 0 and 100")
    
    # Validate boolean flags in genetic data
    genetic_sections = [
        "AML_defining_recurrent_genetic_abnormalities",
        "MDS_related_mutation",
        "MDS_related_cytogenetics",
        "Biallelic_TP53_mutation"
    ]
    
    for section in genetic_sections:
        if section in test_data and isinstance(test_data[section], dict):
            for gene, value in test_data[section].items():
                if not isinstance(value, bool):
                    errors.append(f"{section}.{gene} must be a boolean value")
    
    # Validate therapy options
    if "qualifiers" in test_data and "previous_cytotoxic_therapy" in test_data["qualifiers"]:
        valid_therapies = [
            "None", "Ionising radiation", "Cytotoxic chemotherapy", 
            "Immune interventions", "Any combination"
        ]
        therapy = test_data["qualifiers"]["previous_cytotoxic_therapy"]
        if therapy not in valid_therapies:
            errors.append(f"Invalid therapy option: {therapy}")
    
    return len(errors) == 0, errors


def create_matrix_combinations(
    blast_percentages: List[float],
    aml_genes: List[str],
    mds_mutations: List[str],
    max_combinations: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Create a matrix of test combinations from provided parameters.
    
    Args:
        blast_percentages: List of blast percentages to test
        aml_genes: List of AML genes to test
        mds_mutations: List of MDS mutations to test
        max_combinations: Maximum number of combinations to return
        
    Returns:
        List of test case dictionaries
    """
    test_cases = []
    
    # Generate all combinations
    for blast_pct in blast_percentages:
        for aml_gene in aml_genes + [None]:  # Include no AML gene
            for mds_mutation in mds_mutations + [None]:  # Include no MDS mutation
                test_case = {
                    "blasts_percentage": blast_pct,
                    "AML_defining_recurrent_genetic_abnormalities": {},
                    "MDS_related_mutation": {},
                    "MDS_related_cytogenetics": {},
                    "Biallelic_TP53_mutation": {},
                    "qualifiers": {}
                }
                
                if aml_gene:
                    test_case["AML_defining_recurrent_genetic_abnormalities"][aml_gene] = True
                
                if mds_mutation:
                    test_case["MDS_related_mutation"][mds_mutation] = True
                
                test_cases.append(test_case)
    
    # Shuffle and limit if requested
    if max_combinations and len(test_cases) > max_combinations:
        random.shuffle(test_cases)
        test_cases = test_cases[:max_combinations]
    
    return test_cases


def export_results_to_csv(results: List[Dict], filename: str) -> None:
    """
    Export test results to CSV format.
    
    Args:
        results: List of test result dictionaries
        filename: Output CSV filename
    """
    if not results:
        return
    
    # Flatten nested data for CSV
    flattened_results = []
    for result in results:
        flat_result = {
            "test_id": result.get("test_id", ""),
            "who_classification": result.get("who_classification", ""),
            "icc_classification": result.get("icc_classification", ""),
            "who_disease_type": result.get("who_disease_type", ""),
            "icc_disease_type": result.get("icc_disease_type", ""),
            "are_equivalent": result.get("are_equivalent", False),
            "test_focus": result.get("test_focus", ""),
            "blasts_percentage": result.get("input_data", {}).get("blasts_percentage", ""),
            "significance": result.get("difference_analysis", {}).get("significance", ""),
            "difference_type": result.get("difference_analysis", {}).get("difference_type", ""),
            "timestamp": result.get("timestamp", "")
        }
        
        # Add genetic flags
        genetic_data = result.get("input_data", {})
        for section in ["AML_defining_recurrent_genetic_abnormalities", "MDS_related_mutation", "Biallelic_TP53_mutation"]:
            if section in genetic_data:
                for gene, value in genetic_data[section].items():
                    flat_result[f"{section}_{gene}"] = value
        
        # Add qualifiers
        qualifiers = genetic_data.get("qualifiers", {})
        for key, value in qualifiers.items():
            flat_result[f"qualifier_{key}"] = value
        
        flattened_results.append(flat_result)
    
    # Write to CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        if flattened_results:
            fieldnames = flattened_results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flattened_results)


def analyze_test_coverage(results: List[Dict]) -> Dict[str, Any]:
    """
    Analyze test coverage across different parameters.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        Dictionary with coverage analysis
    """
    if not results:
        return {"message": "No results to analyze"}
    
    coverage = {
        "total_tests": len(results),
        "blast_ranges_tested": set(),
        "aml_genes_tested": set(),
        "mds_mutations_tested": set(),
        "therapies_tested": set(),
        "germline_variants_tested": set(),
        "tp53_conditions_tested": set()
    }
    
    for result in results:
        input_data = result.get("input_data", {})
        
        # Blast ranges
        blasts = input_data.get("blasts_percentage")
        if blasts is not None:
            if blasts < 5:
                coverage["blast_ranges_tested"].add("0-4%")
            elif blasts < 10:
                coverage["blast_ranges_tested"].add("5-9%")
            elif blasts < 20:
                coverage["blast_ranges_tested"].add("10-19%")
            elif blasts < 30:
                coverage["blast_ranges_tested"].add("20-29%")
            else:
                coverage["blast_ranges_tested"].add("30%+")
        
        # AML genes
        aml_genes = input_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        for gene, value in aml_genes.items():
            if value:
                coverage["aml_genes_tested"].add(gene)
        
        # MDS mutations
        mds_mutations = input_data.get("MDS_related_mutation", {})
        for mutation, value in mds_mutations.items():
            if value:
                coverage["mds_mutations_tested"].add(mutation)
        
        # Therapies
        therapy = input_data.get("qualifiers", {}).get("previous_cytotoxic_therapy")
        if therapy:
            coverage["therapies_tested"].add(therapy)
        
        # Germline variants
        germline = input_data.get("qualifiers", {}).get("predisposing_germline_variant")
        if germline:
            coverage["germline_variants_tested"].add(germline)
        
        # TP53 conditions
        tp53_data = input_data.get("Biallelic_TP53_mutation", {})
        for condition, value in tp53_data.items():
            if value:
                coverage["tp53_conditions_tested"].add(condition)
    
    # Convert sets to lists for JSON serialization
    for key in coverage:
        if isinstance(coverage[key], set):
            coverage[key] = list(coverage[key])
    
    return coverage


def find_minimal_difference_cases(results: List[Dict], max_cases: int = 10) -> List[Dict]:
    """
    Find test cases with minimal input differences that produce different classifications.
    
    Args:
        results: List of test result dictionaries
        max_cases: Maximum number of cases to return
        
    Returns:
        List of interesting difference cases
    """
    difference_cases = []
    
    # Find cases with differences
    different_results = [r for r in results if not r.get("are_equivalent", True)]
    
    for result in different_results[:max_cases]:
        input_data = result.get("input_data", {})
        
        # Count how many things are "turned on"
        complexity_score = 0
        
        # Count AML genes
        aml_genes = input_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        complexity_score += sum(1 for v in aml_genes.values() if v)
        
        # Count MDS mutations
        mds_mutations = input_data.get("MDS_related_mutation", {})
        complexity_score += sum(1 for v in mds_mutations.values() if v)
        
        # Count TP53 conditions
        tp53_data = input_data.get("Biallelic_TP53_mutation", {})
        complexity_score += sum(1 for v in tp53_data.values() if v)
        
        # Count qualifiers
        qualifiers = input_data.get("qualifiers", {})
        complexity_score += len([v for v in qualifiers.values() if v and v != "None"])
        
        difference_cases.append({
            "result": result,
            "complexity_score": complexity_score
        })
    
    # Sort by complexity (simpler cases first)
    difference_cases.sort(key=lambda x: x["complexity_score"])
    
    return [case["result"] for case in difference_cases[:max_cases]]


def generate_focused_test_suite(focus_area: str, num_tests: int = 50) -> List[Dict[str, Any]]:
    """
    Generate a focused test suite for a specific area of interest.
    
    Args:
        focus_area: Area to focus on (blast_thresholds, therapy_qualifiers, etc.)
        num_tests: Number of tests to generate
        
    Returns:
        List of test case dictionaries
    """
    from .diagnosis_mapping import (
        generate_blast_test_cases, 
        generate_therapy_test_cases, 
        generate_germline_test_cases
    )
    
    if focus_area == "blast_thresholds":
        return generate_blast_test_cases()[:num_tests]
    elif focus_area == "therapy_qualifiers":
        return generate_therapy_test_cases()[:num_tests]
    elif focus_area == "germline_qualifiers":
        return generate_germline_test_cases()[:num_tests]
    else:
        # Generate random tests
        return [generate_random_test_data() for _ in range(num_tests)]


def compare_classification_systems(results: List[Dict]) -> Dict[str, Any]:
    """
    Compare WHO and ICC classification systems based on test results.
    
    Args:
        results: List of test result dictionaries
        
    Returns:
        Dictionary with comparison analysis
    """
    if not results:
        return {"message": "No results to compare"}
    
    comparison = {
        "total_comparisons": len(results),
        "agreement_rate": 0,
        "who_more_specific": 0,
        "icc_more_specific": 0,
        "category_changes": {},
        "system_preferences": {}
    }
    
    agreements = 0
    
    for result in results:
        if result.get("are_equivalent", True):
            agreements += 1
        else:
            # Analyze the type of difference
            who_class = result.get("who_classification", "")
            icc_class = result.get("icc_classification", "")
            
            # Track category changes
            change_key = f"WHO: {who_class[:30]}... → ICC: {icc_class[:30]}..."
            comparison["category_changes"][change_key] = \
                comparison["category_changes"].get(change_key, 0) + 1
            
            # Simple heuristic for specificity
            if len(who_class) > len(icc_class):
                comparison["who_more_specific"] += 1
            elif len(icc_class) > len(who_class):
                comparison["icc_more_specific"] += 1
    
    comparison["agreement_rate"] = agreements / len(results) * 100
    
    return comparison 