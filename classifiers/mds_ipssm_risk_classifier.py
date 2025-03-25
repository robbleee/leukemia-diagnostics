#!/usr/bin/env python
"""
IPSS-M and IPSS-R Calculator for Myelodysplastic Syndromes
Combined single-file implementation

This file contains the complete implementation of the IPSS-M and IPSS-R
risk score calculators, including all necessary functions, constants,
and utilities. It is designed to be used as a standalone module or as
part of a larger application.

Usage as a module:
    from ipssm_combined import calculate_ipssm, calculate_ipssr
    result = calculate_ipssm(patient_data)
    
Usage as a CLI:
    python ipssm_combined.py ipssm --hb 10 --plt 150 --bm-blast 2 --cyto "Poor" --asxl1 1
    python ipssm_combined.py ipssr --hb 10 --plt 150 --bm-blast 2 --anc 1.8 --cyto "Poor"
    python ipssm_combined.py --json '{"HB": 10, "PLT": 150, "BM_BLAST": 2, "ANC": 1.8, "CYTO_IPSSR": "Poor"}'
"""
import sys
import json
import math
import argparse
from typing import Dict, Any, List, Union, Tuple, Optional
import concurrent.futures
import streamlit as st


###########################################
# Constants and coefficients
###########################################

# IPSS-M risk categories
IPSSM_CATEGORIES = [
    "Very Low",
    "Low", 
    "Moderate Low", 
    "Moderate High", 
    "High", 
    "Very High"
]

# IPSS-R risk categories
IPSSR_CATEGORIES = [
    "Very Low",
    "Low",
    "Int",
    "High",
    "Very High"
]

# IPSS-M coefficients (betas) for the risk model
BETAS = [
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
    {"name": "Nres2", "coeff": 0.231, "means": 0.388, "worst": 2, "best": 0}
]

# List of residual genes used in the IPSS-M model
RESIDUAL_GENES = [
    "BCOR", "BCORL1", "CEBPA", "ETNK1", "GATA2", 
    "GNB1", "IDH1", "NF1", "PHF6", "PPM1D", 
    "PRPF8", "PTPN11", "SETBP1", "STAG2", "WT1"
]

# IPSS-M cutpoints for risk categorization
IPSSM_CUTPOINTS = [-1.5, -0.5, 0, 0.5, 1.5]

# IPSS-R cutpoints and variable breakpoints
IPSSR_CUTPOINTS = [-float('inf'), 1.5, 3, 4.5, 6, float('inf')]
BM_BLAST_BREAKS = [-float('inf'), 2, 4.99, 10, float('inf')]
HB_BREAKS = [-float('inf'), 8, 10, float('inf')]
PLT_BREAKS = [-float('inf'), 50, 100, float('inf')]
ANC_BREAKS = [-float('inf'), 0.8, float('inf')]

# IPSS-R variable score mappings
BM_BLAST_MAP = [0, 1, 2, 3]
HB_MAP = [1.5, 1, 0]
PLT_MAP = [1, 0.5, 0]
ANC_MAP = [0.5, 0]


###########################################
# Utility functions
###########################################

def round_number(value: float, digits: int = 2) -> float:
    """Round a number to specified number of digits."""
    return round(value, digits)


def find_category_index(value: float, breaks: List[float], right: bool = True) -> int:
    """
    Find the category index for a value based on specified breaks.
    
    Args:
        value: The value to categorize
        breaks: The category breakpoints
        right: If True, intervals are closed on the right side (open on left)
              If False, intervals are closed on the left side (open on right)
    
    Returns:
        The index of the category
    """
    for i in range(1, len(breaks)):
        if right:
            # Intervals are closed to the right, and open to the left
            if value > breaks[i - 1] and value <= breaks[i]:
                return i - 1
        else:
            # Intervals are open to the right, and closed to the left
            if value >= breaks[i - 1] and value < breaks[i]:
                return i - 1
    return -1  # Default value for error cases


def calculate_residual_genes(
    patient_data: Dict[str, Any], 
    n_ref: float = 0.388
) -> Dict[str, float]:
    """
    Calculate the residual genes weight contribution to the IPSS-M score.
    
    Args:
        patient_data: Dictionary with patient data
        n_ref: Reference number of residual mutated genes
        
    Returns:
        Dictionary with mean, worst, and best case scenarios
    """
    # Extract residual gene data and handle NA values
    residual_genes_data = {}
    for gene in RESIDUAL_GENES:
        if gene in patient_data:
            value = patient_data[gene]
            if value in [0, 1, "0", "1"]:
                residual_genes_data[gene] = str(value)
            else:
                residual_genes_data[gene] = "NA"
    
    # Number of missing genes (NA values)
    missing_genes = sum(1 for value in residual_genes_data.values() if value == "NA")
    
    # Number of sequenced genes (genes with actual values)
    sequenced_genes = sum(1 for value in residual_genes_data.values() if value != "NA")
    
    # Sum of mutated genes within sequenced genes
    mutated_genes = sum(
        int(value) for value in residual_genes_data.values() if value != "NA"
    )
    
    # Worst scenario: all missing are mutated
    n_res_worst = min(mutated_genes + missing_genes, 2)
    
    # Best scenario: none missing are mutated
    n_res_best = min(mutated_genes, 2)
    
    # Average scenario: generalized min(Nres,2)
    n_res_mean = n_res_best
    if sequenced_genes + missing_genes > 0:
        n_res_mean += max(
            ((2 - mutated_genes) / 2) * (missing_genes / (sequenced_genes + missing_genes)) * n_ref, 
            0
        )
    
    return {
        "means": n_res_mean,
        "worst": n_res_worst,
        "best": n_res_best
    }


def _safe_number(value: Any) -> Optional[int]:
    """Convert a value to an integer safely, returning None if not possible."""
    if value in (0, "0"):
        return 0
    if value in (1, "1"):
        return 1
    return None


###########################################
# Preprocessing functions
###########################################

def preprocess_patient_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess patient input data for IPSS-M calculation.
    
    Args:
        patient_data: Dictionary with patient data
        
    Returns:
        Dictionary with preprocessed data
    """
    # Create a copy to avoid modifying the original data
    processed = {**patient_data}
    
    # Construction of SF3B1 features
    processed["SF3B1_5q"] = "NA"
    
    # If any of these conditions are met, SF3B1_5q is 0
    sf3b1 = _safe_number(processed.get("SF3B1", "NA"))
    del5q = _safe_number(processed.get("del5q", "NA"))
    del7_7q = _safe_number(processed.get("del7_7q", "NA"))
    complex_karyo = _safe_number(processed.get("complex", "NA"))
    
    if (sf3b1 == 0 or del5q == 0 or del7_7q == 1 or complex_karyo == 1):
        processed["SF3B1_5q"] = "0"
        
    # If all these conditions are met, SF3B1_5q is 1
    if (sf3b1 == 1 and del5q == 1 and del7_7q == 0 and complex_karyo == 0):
        processed["SF3B1_5q"] = "1"
    
    # Construction of SF3B1_alpha feature
    processed["SF3B1_alpha"] = "NA"
    
    # Extract values with safety checks
    sf3b1_5q = _safe_number(processed.get("SF3B1_5q", "NA"))
    srsf2 = _safe_number(processed.get("SRSF2", "NA"))
    stag2 = _safe_number(processed.get("STAG2", "NA"))
    bcor = _safe_number(processed.get("BCOR", "NA"))
    bcorl1 = _safe_number(processed.get("BCORL1", "NA"))
    runx1 = _safe_number(processed.get("RUNX1", "NA"))
    nras = _safe_number(processed.get("NRAS", "NA"))
    
    # If any of these conditions are met, SF3B1_alpha is 0
    if (sf3b1 == 0 or sf3b1_5q == 1 or srsf2 == 1 or stag2 == 1 or 
        bcor == 1 or bcorl1 == 1 or runx1 == 1 or nras == 1):
        processed["SF3B1_alpha"] = "0"
        
    # If all these conditions are met, SF3B1_alpha is 1
    if (sf3b1 == 1 and sf3b1_5q == 0 and srsf2 == 0 and stag2 == 0 and
        bcor == 0 and bcorl1 == 0 and runx1 == 0 and nras == 0):
        processed["SF3B1_alpha"] = "1"
    
    # Construction of TP53multi feature
    try:
        # Safely convert TP53maxvaf to float, handling 'NA' values
        if processed.get("TP53maxvaf") == "NA" or processed.get("TP53maxvaf") is None:
            tp53_max_vaf = 0.0
        else:
            tp53_max_vaf = float(processed.get("TP53maxvaf", 0))
    except (ValueError, TypeError):
        tp53_max_vaf = 0.0
        
    del17_17p = _safe_number(processed.get("del17_17p", 0))
    
    # If VAF > 55% or del17/17p present, set TP53loh to 1
    if tp53_max_vaf > 0.55 or del17_17p == 1:
        processed["TP53loh"] = "1"
    
    # Ensure TP53mut and TP53loh are strings
    processed["TP53mut"] = str(processed.get("TP53mut", "0"))
    processed["TP53loh"] = str(processed.get("TP53loh", "0"))
    
    # Determine TP53multi based on conditions
    tp53mut = processed["TP53mut"]
    tp53loh = processed["TP53loh"]
    
    if tp53mut == "0":
        processed["TP53multi"] = "0"
    elif tp53mut == "2 or more":
        processed["TP53multi"] = "1"
    elif tp53mut == "1" and tp53loh == "1":
        processed["TP53multi"] = "1"
    elif tp53mut == "1" and tp53loh == "0":
        processed["TP53multi"] = "0"
    else:
        processed["TP53multi"] = "NA"
    
    # Transformation of clinical variables
    processed["HB1"] = float(processed.get("HB", 0))
    processed["BLAST5"] = min(float(processed.get("BM_BLAST", 0)), 20) / 5
    processed["TRANSF_PLT100"] = min(float(processed.get("PLT", 0)), 250) / 100
    
    # Cytogenetics as a numerical vector
    cyto_mapping = {
        "Very Good": 0,
        "Good": 1,
        "Intermediate": 2,
        "Poor": 3,
        "Very Poor": 4
    }
    processed["CYTOVEC"] = cyto_mapping.get(processed.get("CYTO_IPSSR", "Intermediate"), 2)
    
    # Calculate number of residual mutations Nres2 allowing missing genes
    processed["Nres2"] = calculate_residual_genes(processed)
    
    return processed


###########################################
# Core calculation functions
###########################################

def calculate_ipssm(
    patient_data: Dict[str, Any],
    rounding: bool = True,
    rounding_digits: int = 2,
    include_contributions: bool = False
) -> Dict[str, Any]:
    """
    Calculate IPSS-M risk score and categories.
    
    Args:
        patient_data: Dictionary with patient data
        rounding: Whether to round the results
        rounding_digits: Number of digits to round to
        include_contributions: Whether to include variable contributions in output
        
    Returns:
        Dictionary with IPSS-M scores
    """
    # Preprocess the patient data
    processed_data = preprocess_patient_data(patient_data)
    
    # Initialize result dictionary for the three scenarios
    scores = {
        "means": {"risk_score": 0, "risk_cat": ""},
        "worst": {"risk_score": 0, "risk_cat": ""},
        "best": {"risk_score": 0, "risk_cat": ""}
    }
    
    # Include contributions if requested
    if include_contributions:
        for scenario in scores:
            scores[scenario]["contributions"] = {}
    
    # Calculate scores for each scenario
    for scenario in scores:
        contributions = {}
        
        # Calculate contribution from each variable
        for beta in BETAS:
            var_name = beta["name"]
            
            # Get the value for this variable
            if var_name == "Nres2":
                value = processed_data["Nres2"][scenario]
            else:
                value = processed_data.get(var_name)
                
                # Calculate contribution
                try:
                    # Handle missing values by using scenario-specific defaults
                    if value == "NA" or value is None:
                        value = beta[scenario]
                    
                    # Safely convert to float
                    contribution = ((float(value) - beta["means"]) * beta["coeff"]) / math.log(2)
                    contributions[var_name] = contribution
                except (ValueError, TypeError):
                    # If conversion fails, use the default for this scenario
                    value = beta[scenario]
                    contribution = ((float(value) - beta["means"]) * beta["coeff"]) / math.log(2)
                    contributions[var_name] = contribution
            
            # Calculate total risk score
            risk_score = sum(contributions.values())
            if rounding:
                risk_score = round_number(risk_score, rounding_digits)
            
            # Determine risk category
            extended_cutpoints = [-float('inf')] + IPSSM_CUTPOINTS + [float('inf')]
            cat_index = find_category_index(risk_score, extended_cutpoints)
            risk_cat = IPSSM_CATEGORIES[cat_index] if 0 <= cat_index < len(IPSSM_CATEGORIES) else "Unknown"
            
            # Set results
            scores[scenario]["risk_score"] = risk_score
            scores[scenario]["risk_cat"] = risk_cat
            
            # Add contributions if requested
            if include_contributions:
                scores[scenario]["contributions"] = contributions
    
    return scores


def calculate_ipssr(
    patient_data: Dict[str, Any],
    rounding: bool = True,
    rounding_digits: int = 4,
    return_components: bool = False
) -> Dict[str, Any]:
    """
    Calculate IPSS-R risk score and category, plus age-adjusted version if age is provided.
    
    Args:
        patient_data: Dictionary with patient data including HB, PLT, BM_BLAST, ANC, CYTO_IPSSR
                     and optionally AGE
        rounding: Whether to round the results
        rounding_digits: Number of digits to round to
        return_components: Whether to return detailed components for visualization
        
    Returns:
        Dictionary with IPSS-R and IPSS-RA scores and categories
    """
    # Extract required parameters with defaults
    hb = float(patient_data.get("HB", 0))
    plt = float(patient_data.get("PLT", 0))
    bm_blast = float(patient_data.get("BM_BLAST", 0))
    anc = float(patient_data.get("ANC", 0))
    cyto_ipssr = patient_data.get("CYTO_IPSSR")
    age = patient_data.get("AGE")
    
    # Get cytogenetic category
    cyto_mapping = {
        "Very Good": 0, 
        "Good": 1, 
        "Intermediate": 2, 
        "Poor": 3, 
        "Very Poor": 4
    }
    cytovec = cyto_mapping.get(cyto_ipssr, None)
    
    # Validate cytogenetic category
    if cytovec is None or cytovec < 0 or cytovec > 4:
        raise ValueError("Cytogenetic category is not valid.")
    
    # Find score for each parameter
    bm_blast_score = BM_BLAST_MAP[find_category_index(bm_blast, BM_BLAST_BREAKS, True)]
    hb_score = HB_MAP[find_category_index(hb, HB_BREAKS, False)]
    plt_score = PLT_MAP[find_category_index(plt, PLT_BREAKS, False)]
    anc_score = ANC_MAP[find_category_index(anc, ANC_BREAKS, False)]
    
    # Calculate IPSS-R raw score
    ipssr_raw = bm_blast_score + hb_score + plt_score + anc_score + cytovec
    if rounding:
        ipssr_raw = round_number(ipssr_raw, rounding_digits)
    
    # Map to IPSS-R category
    ipssr_cat_index = find_category_index(ipssr_raw, IPSSR_CUTPOINTS)
    ipssr_cat = IPSSR_CATEGORIES[ipssr_cat_index] if 0 <= ipssr_cat_index < len(IPSSR_CATEGORIES) else "Unknown"
    
    # Initialize results
    results = {
        "IPSSR_SCORE": ipssr_raw,
        "IPSSR_CAT": ipssr_cat,
        "IPSSRA_SCORE": None,
        "IPSSRA_CAT": None
    }
    
    # Calculate IPSS-RA (age-adjusted) if age is provided
    if age is not None:
        age_adjust = (float(age) - 70) * (0.05 - ipssr_raw * 0.005)
        ipssra_raw = ipssr_raw + age_adjust
        if rounding:
            ipssra_raw = round_number(ipssra_raw, rounding_digits)
        
        # Map to IPSS-RA category
        ipssra_cat_index = find_category_index(ipssra_raw, IPSSR_CUTPOINTS)
        ipssra_cat = IPSSR_CATEGORIES[ipssra_cat_index] if 0 <= ipssra_cat_index < len(IPSSR_CATEGORIES) else "Unknown"
        
        results["IPSSRA_SCORE"] = ipssra_raw
        results["IPSSRA_CAT"] = ipssra_cat
    
    # Add detailed component information if requested
    if return_components:
        # Determine categories for each parameter
        hb_cat_index = find_category_index(hb, HB_BREAKS, False)
        plt_cat_index = find_category_index(plt, PLT_BREAKS, False)
        anc_cat_index = find_category_index(anc, ANC_BREAKS, False)
        blast_cat_index = find_category_index(bm_blast, BM_BLAST_BREAKS, True)
        
        # Map indices to human-readable categories
        hb_categories = ["<8", "8-<10", "≥10"]
        plt_categories = ["<50", "50-<100", "≥100"]
        anc_categories = ["<0.8", "≥0.8"]
        blast_categories = ["≤2", ">2-<5", "5-10", ">10"]
        
        # Add components to results
        results["components"] = {
            "Hemoglobin": hb_score,
            "Platelets": plt_score,
            "ANC": anc_score,
            "Bone Marrow Blasts": bm_blast_score,
            "Cytogenetics": float(cytovec)
        }
        
        results["hb_category"] = hb_categories[hb_cat_index] if 0 <= hb_cat_index < len(hb_categories) else "Unknown"
        results["plt_category"] = plt_categories[plt_cat_index] if 0 <= plt_cat_index < len(plt_categories) else "Unknown"
        results["anc_category"] = anc_categories[anc_cat_index] if 0 <= anc_cat_index < len(anc_categories) else "Unknown"
        results["blast_category"] = blast_categories[blast_cat_index] if 0 <= blast_cat_index < len(blast_categories) else "Unknown"
        results["cyto_category"] = cyto_ipssr
    
    return results


###########################################
# Command-line interface
###########################################

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate IPSS-M and IPSS-R risk scores for MDS patients"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # IPSS-M command
    ipssm_parser = subparsers.add_parser("ipssm", help="Calculate IPSS-M risk score")
    ipssm_parser.add_argument("--hb", type=float, required=True, help="Hemoglobin (g/dL)")
    ipssm_parser.add_argument("--plt", type=float, required=True, help="Platelets (Giga/L)")
    ipssm_parser.add_argument("--bm-blast", type=float, required=True, help="Bone marrow blasts (%)")
    ipssm_parser.add_argument("--cyto", type=str, required=True, 
                          choices=["Very Good", "Good", "Intermediate", "Poor", "Very Poor"],
                          help="Cytogenetic category")
    ipssm_parser.add_argument("--tp53mut", type=str, default="0", 
                          choices=["0", "1", "2 or more"],
                          help="Number of TP53 mutations")
    ipssm_parser.add_argument("--detailed", action="store_true", help="Show detailed contributions")
    
    # Add gene mutation flags for common mutations
    for gene in ["ASXL1", "RUNX1", "SF3B1", "EZH2", "SRSF2", "U2AF1"]:
        ipssm_parser.add_argument(f"--{gene.lower()}", type=int, choices=[0, 1], 
                              help=f"{gene} mutation status (0=wild-type, 1=mutated)")
    
    # IPSS-R command
    ipssr_parser = subparsers.add_parser("ipssr", help="Calculate IPSS-R risk score")
    ipssr_parser.add_argument("--hb", type=float, required=True, help="Hemoglobin (g/dL)")
    ipssr_parser.add_argument("--plt", type=float, required=True, help="Platelets (Giga/L)")
    ipssr_parser.add_argument("--bm-blast", type=float, required=True, help="Bone marrow blasts (%)")
    ipssr_parser.add_argument("--anc", type=float, required=True, help="Absolute neutrophil count (Giga/L)")
    ipssr_parser.add_argument("--cyto", type=str, required=True, 
                          choices=["Very Good", "Good", "Intermediate", "Poor", "Very Poor"],
                          help="Cytogenetic category")
    ipssr_parser.add_argument("--age", type=float, help="Age in years (for age-adjusted score)")
    
    # JSON input option
    parser.add_argument("--json", type=str, help="JSON string with patient data")
    
    return parser.parse_args()


def main():
    """Main CLI function."""
    args = parse_args()
    
    # If no command is provided and no JSON, show help
    if not args.command and not args.json:
        print("Error: You must specify a command (ipssm or ipssr) or provide JSON input")
        sys.exit(1)
    
    # Handle JSON input
    if args.json:
        try:
            patient_data = json.loads(args.json)
            
            # Calculate both IPSS-M and IPSS-R if possible
            ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
            
            try:
                ipssr_result = calculate_ipssr(patient_data)
            except Exception:
                ipssr_result = None
            
            # Print results
            print(json.dumps({
                "ipssm": ipssm_result,
                "ipssr": ipssr_result
            }, indent=2))
            
        except json.JSONDecodeError:
            print("Error: Invalid JSON input")
            sys.exit(1)
        except Exception as e:
            print(f"Error calculating risk scores: {str(e)}")
            sys.exit(1)
            
        return
    
    # Handle command-line arguments
    if args.command == "ipssm":
        # Build patient data from arguments
        patient_data = {
            "HB": args.hb,
            "PLT": args.plt,
            "BM_BLAST": args.bm_blast,
            "CYTO_IPSSR": args.cyto,
            "TP53mut": args.tp53mut
        }
        
        # Add gene mutations if provided
        for gene in ["ASXL1", "RUNX1", "SF3B1", "EZH2", "SRSF2", "U2AF1"]:
            arg_name = gene.lower()
            if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
                patient_data[gene] = getattr(args, arg_name)
        
        # Calculate IPSS-M
        result = calculate_ipssm(patient_data, include_contributions=args.detailed)
        
        # Print results
        print("\n===== IPSS-M Risk Score =====")
        print(f"Risk Score: {result['means']['risk_score']}")
        print(f"Risk Category: {result['means']['risk_cat']}")
        
        if args.detailed:
            print("\nRisk Score Contributions:")
            sorted_contributions = sorted(
                result['means']['contributions'].items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            for var_name, contribution in sorted_contributions:
                print(f"  {var_name}: {contribution:.4f}")
        
    elif args.command == "ipssr":
        # Build patient data from arguments
        patient_data = {
            "HB": args.hb,
            "PLT": args.plt,
            "BM_BLAST": args.bm_blast,
            "ANC": args.anc,
            "CYTO_IPSSR": args.cyto
        }
        
        # Add age if provided
        if args.age:
            patient_data["AGE"] = args.age
        
        # Calculate IPSS-R
        result = calculate_ipssr(patient_data)
        
        # Print results
        print("\n===== IPSS-R Risk Score =====")
        print(f"IPSS-R Score: {result['IPSSR_SCORE']}")
        print(f"IPSS-R Category: {result['IPSSR_CAT']}")
        
        if args.age:
            print(f"\nIPSS-RA Score (Age-adjusted): {result['IPSSRA_SCORE']}")
            print(f"IPSS-RA Category (Age-adjusted): {result['IPSSRA_CAT']}")


###########################################
# Simple demo function
###########################################

def demo():
    """Run a demonstration of IPSS-M and IPSS-R calculations."""
    # Example patient data for IPSS-M
    patient_data = {
        "HB": 10,
        "PLT": 150,
        "BM_BLAST": 2,
        "ANC": 1.8,
        "CYTO_IPSSR": "Poor",
        "ASXL1": 1
    }
    
    # Calculate IPSS-M
    ipssm_result = calculate_ipssm(patient_data, include_contributions=True)
    print("\n----- IPSS-M Results -----")
    print(f"Mean Risk Score: {ipssm_result['means']['risk_score']}")
    print(f"Mean Risk Category: {ipssm_result['means']['risk_cat']}")
    
    # Top 5 mean contributions
    print("\nTop 5 Mean Risk Score Contributors:")
    sorted_contributions = sorted(
        ipssm_result['means']['contributions'].items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )[:5]
    for var_name, contribution in sorted_contributions:
        print(f"  {var_name}: {contribution:.4f}")
    
    # Calculate IPSS-R
    ipssr_result = calculate_ipssr(patient_data)
    print("\n----- IPSS-R Results -----")
    print(f"IPSS-R Score: {ipssr_result['IPSSR_SCORE']}")
    print(f"IPSS-R Category: {ipssr_result['IPSSR_CAT']}")


def parse_for_ipssm(report_text: str) -> dict:
    """
    Sends the free-text hematological report to OpenAI to extract data needed for IPSS-M and IPSS-R calculators.
    Uses multiple concurrent prompts to extract different categories of information:
      1) Clinical blood counts (HB, PLT, ANC)
      2) Cytogenetic details and karyotype complexity
      3) TP53 details (VAF, allelic state)
      4) Additional molecular mutations relevant for IPSS-M
      5) Residual gene mutations

    Returns:
        dict: A dictionary containing all fields needed for IPSS-M and IPSS-R calculation
    """
    # Safety check: if user typed nothing, return empty.
    if not report_text.strip():
        st.warning("Empty report text received.")
        return {}

    # The required JSON structure for IPSS-M and IPSS-R
    required_json_structure = {
        # Clinical parameters
        "clinical_values": {
            "HB": None,  # Hemoglobin in g/dL
            "PLT": None,  # Platelets in 10^9/L
            "ANC": None,  # Absolute neutrophil count in 10^9/L
            "Age": None   # Patient age in years (for age-adjusted IPSS-R)
        },
        
        # Cytogenetics with detailed abnormalities
        "cytogenetics": {
            "karyotype_complexity": "Normal (no abnormalities)",  # Options: "Normal", "Single abnormality", "Double abnormality", "Complex (3 abnormalities)", "Very complex (>3 abnormalities)"
            "del5q": False,
            "del7q": False,
            "del7_minus7": False,  # -7/del(7)
            "del11q": False,
            "del12p": False,
            "del17_17p": False,
            "del20q": False,
            "plus8": False,
            "plus19": False,
            "i17q": False,
            "inv3_t3q_del3q": False,
            "minusY": False
        },
        
        # TP53 details
        "tp53_details": {
            "TP53mut": "0",  # "0", "1", or "2 or more"
            "TP53maxvaf": 0,  # Maximum VAF as percentage
            "TP53loh": False  # Loss of heterozygosity
        },
        
        # Additional gene mutations for IPSS-M
        "gene_mutations": {
            "ASXL1": False,
            "RUNX1": False,
            "SF3B1": False,
            "SRSF2": False,
            "U2AF1": False,
            "EZH2": False,
            "DNMT3A": False,
            "MLL_PTD": False,
            "FLT3": False,
            "CBL": False,
            "NRAS": False,
            "KRAS": False,
            "IDH2": False,
            "NPM1": False,
            "ETV6": False
        },
        
        # Residual genes (Nres2 calculation)
        "residual_genes": {
            "BCOR": False,
            "BCORL1": False,
            "CEBPA": False,
            "ETNK1": False,
            "GATA2": False,
            "GNB1": False,
            "IDH1": False,
            "NF1": False,
            "PHF6": False,
            "PPM1D": False,
            "PRPF8": False,
            "PTPN11": False,
            "SETBP1": False,
            "STAG2": False,
            "WT1": False
        }
    }

    # -------------------------------------------------------
    # Prompt #1: Clinical blood counts
    # -------------------------------------------------------
    clinical_prompt = f"""
The user has pasted a free-text hematological report.
Please extract the following clinical values from the text and format them into a valid JSON object.
For numerical fields, provide the value with appropriate units as indicated.
If a value is not found, set it to null.

Extract these fields:
"clinical_values": {{
    "HB": null,  // Hemoglobin in g/dL
    "PLT": null,  // Platelets in 10^9/L
    "ANC": null,  // Absolute neutrophil count in 10^9/L
    "Age": null   // Patient age in years
}}

Return valid JSON with only these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #2: Cytogenetic details and karyotype complexity
    # -------------------------------------------------------
    cytogenetics_prompt = f"""
The user has pasted a free-text hematological report.
Please extract cytogenetic abnormalities and karyotype complexity from the text and format them into a valid JSON object.
For boolean fields, use true/false. For karyotype_complexity, choose the most appropriate category based on the report.
If an abnormality is not mentioned, set it to false.

Extract these fields:
"cytogenetics": {{
    "karyotype_complexity": "Normal (no abnormalities)",  // Choose one: "Normal (no abnormalities)", "Single abnormality", "Double abnormality", "Complex (3 abnormalities)", "Very complex (>3 abnormalities)"
    "del5q": false,  // del(5q) or 5q-
    "del7q": false,  // del(7q)
    "del7_minus7": false,  // -7 or del(7)
    "del11q": false,  // del(11q)
    "del12p": false,  // del(12p)
    "del17_17p": false,  // del(17p) or -17
    "del20q": false,  // del(20q)
    "plus8": false,  // +8 or trisomy 8
    "plus19": false,  // +19
    "i17q": false,  // i(17q)
    "inv3_t3q_del3q": false,  // inv(3) or t(3q) or del(3q)
    "minusY": false  // -Y
}}

Return valid JSON with only these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #3: TP53 details
    # -------------------------------------------------------
    tp53_prompt = f"""
The user has pasted a free-text hematological report.
Please extract detailed information about TP53 mutations from the text and format it into a valid JSON object.

For "TP53mut", select from:
- "0" (no TP53 mutations)
- "1" (single TP53 mutation)
- "2 or more" (multiple TP53 mutations)

For "TP53maxvaf", provide the maximum variant allele frequency as a percentage (0-100).
For "TP53loh", set to true if there is evidence of loss of heterozygosity or false if not mentioned.

Extract these fields:
"tp53_details": {{
    "TP53mut": "0",  // "0", "1", or "2 or more"
    "TP53maxvaf": 0,  // Maximum VAF as percentage
    "TP53loh": false  // Loss of heterozygosity
}}

Return valid JSON with only these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #4: Additional gene mutations for IPSS-M
    # -------------------------------------------------------
    mutations_prompt = f"""
The user has pasted a free-text hematological report.
Please extract information about the following gene mutations and format it into a valid JSON object.
For each gene, set the value to true if the text indicates the gene is mutated; otherwise false.

Extract these fields:
"gene_mutations": {{
    "ASXL1": false,
    "RUNX1": false,
    "SF3B1": false,
    "SRSF2": false,
    "U2AF1": false,
    "EZH2": false,
    "DNMT3A": false,
    "MLL_PTD": false,  // Also known as KMT2A-PTD
    "FLT3": false,     // Any FLT3 mutation
    "CBL": false,
    "NRAS": false,
    "KRAS": false,
    "IDH2": false,
    "NPM1": false,
    "ETV6": false
}}

Return valid JSON with only these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    # -------------------------------------------------------
    # Prompt #5: Residual genes for Nres2 calculation
    # -------------------------------------------------------
    residual_prompt = f"""
The user has pasted a free-text hematological report.
Please extract information about the following "residual" gene mutations and format it into a valid JSON object.
For each gene, set the value to true if the text indicates the gene is mutated; otherwise false.
These genes contribute to the Nres2 score in the IPSS-M calculator.

Extract these fields:
"residual_genes": {{
    "BCOR": false,
    "BCORL1": false,
    "CEBPA": false,
    "ETNK1": false,
    "GATA2": false,
    "GNB1": false,
    "IDH1": false,
    "NF1": false,
    "PHF6": false,
    "PPM1D": false,
    "PRPF8": false,
    "PTPN11": false,
    "SETBP1": false,
    "STAG2": false,
    "WT1": false
}}

Return valid JSON with only these keys and no extra text.

Here is the free-text hematological report to parse:
{report_text}
    """

    try:
        # Parallelize the prompt calls
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_clinical = executor.submit(get_json_from_prompt, clinical_prompt)
            future_cytogenetics = executor.submit(get_json_from_prompt, cytogenetics_prompt)
            future_tp53 = executor.submit(get_json_from_prompt, tp53_prompt)
            future_mutations = executor.submit(get_json_from_prompt, mutations_prompt)
            future_residual = executor.submit(get_json_from_prompt, residual_prompt)

            # Gather results when all are complete
            clinical_data = future_clinical.result()
            cytogenetics_data = future_cytogenetics.result()
            tp53_data = future_tp53.result()
            mutations_data = future_mutations.result()
            residual_data = future_residual.result()

        # Merge all data into one dictionary
        parsed_data = {}
        parsed_data.update(clinical_data)
        parsed_data.update(cytogenetics_data)
        parsed_data.update(tp53_data)
        parsed_data.update(mutations_data)
        parsed_data.update(residual_data)

        # Fill missing keys from required structure
        for key, val in required_json_structure.items():
            if key not in parsed_data:
                parsed_data[key] = val
            elif isinstance(val, dict):
                for sub_key, sub_val in val.items():
                    if sub_key not in parsed_data[key]:
                        parsed_data[key][sub_key] = sub_val

        # Debug print
        print("Parsed IPSS-M/R Data JSON:")
        print(json.dumps(parsed_data, indent=2))
        return parsed_data

    except json.JSONDecodeError:
        st.error("❌ Failed to parse AI response into JSON for IPSS-M/R data.")
        print("❌ JSONDecodeError: Could not parse AI JSON response for IPSS-M/R data.")
        return {}
    except Exception as e:
        st.error(f"❌ Error communicating with OpenAI for IPSS-M/R data: {str(e)}")
        print(f"❌ Exception in IPSS-M/R data parsing: {str(e)}")
        return {}

# Function to prepare the combined data for IPSS-M calculation
def prepare_ipssm_input(aml_data: dict, ipssm_data: dict) -> dict:
    """
    Combines AML and IPSS-M/R data into the format required by the IPSS-M calculator.
    
    Args:
        aml_data: Dictionary with AML genetic data
        ipssm_data: Dictionary with IPSS-M/R specific data
        
    Returns:
        Dictionary formatted for IPSS-M calculator input
    """
    # Extract clinical values
    hb = ipssm_data.get("clinical_values", {}).get("HB")
    plt = ipssm_data.get("clinical_values", {}).get("PLT")
    anc = ipssm_data.get("clinical_values", {}).get("ANC")
    age = ipssm_data.get("clinical_values", {}).get("Age")
    
    # Get bone marrow blast percentage from AML data
    bm_blast = aml_data.get("blasts_percentage")
    
    # Get TP53 details
    tp53mut = ipssm_data.get("tp53_details", {}).get("TP53mut", "0")
    tp53maxvaf = ipssm_data.get("tp53_details", {}).get("TP53maxvaf", 0) / 100  # Convert to decimal
    tp53loh = 1 if ipssm_data.get("tp53_details", {}).get("TP53loh", False) else 0
    
    # Get cytogenetic details and calculate category
    cytogenetics = ipssm_data.get("cytogenetics", {})
    
    # Combine gene mutations from both datasets
    gene_mutations = {
        # Core mutations
        "ASXL1": aml_data.get("MDS_related_mutation", {}).get("ASXL1", False) or ipssm_data.get("gene_mutations", {}).get("ASXL1", False),
        "RUNX1": aml_data.get("MDS_related_mutation", {}).get("RUNX1", False) or ipssm_data.get("gene_mutations", {}).get("RUNX1", False),
        "SF3B1": aml_data.get("MDS_related_mutation", {}).get("SF3B1", False) or ipssm_data.get("gene_mutations", {}).get("SF3B1", False),
        "SRSF2": aml_data.get("MDS_related_mutation", {}).get("SRSF2", False) or ipssm_data.get("gene_mutations", {}).get("SRSF2", False),
        "U2AF1": aml_data.get("MDS_related_mutation", {}).get("U2AF1", False) or ipssm_data.get("gene_mutations", {}).get("U2AF1", False),
        "EZH2": aml_data.get("MDS_related_mutation", {}).get("EZH2", False) or ipssm_data.get("gene_mutations", {}).get("EZH2", False),
        
        # Additional mutations
        "DNMT3A": ipssm_data.get("gene_mutations", {}).get("DNMT3A", False),
        "MLL_PTD": ipssm_data.get("gene_mutations", {}).get("MLL_PTD", False),
        "FLT3": aml_data.get("ELN2024_risk_genes", {}).get("FLT3_ITD", False) or ipssm_data.get("gene_mutations", {}).get("FLT3", False),
        "CBL": ipssm_data.get("gene_mutations", {}).get("CBL", False),
        "NRAS": aml_data.get("ELN2024_risk_genes", {}).get("NRAS", False) or ipssm_data.get("gene_mutations", {}).get("NRAS", False),
        "KRAS": aml_data.get("ELN2024_risk_genes", {}).get("KRAS", False) or ipssm_data.get("gene_mutations", {}).get("KRAS", False),
        "IDH2": aml_data.get("ELN2024_risk_genes", {}).get("IDH2", False) or ipssm_data.get("gene_mutations", {}).get("IDH2", False),
        "NPM1": aml_data.get("AML_defining_recurrent_genetic_abnormalities", {}).get("NPM1", False) or ipssm_data.get("gene_mutations", {}).get("NPM1", False),
        "ETV6": ipssm_data.get("gene_mutations", {}).get("ETV6", False)
    }
    
    # Combine residual genes
    residual_genes = {
        # From MDS-related mutations
        "BCOR": aml_data.get("MDS_related_mutation", {}).get("BCOR", False) or ipssm_data.get("residual_genes", {}).get("BCOR", False),
        "STAG2": aml_data.get("MDS_related_mutation", {}).get("STAG2", False) or ipssm_data.get("residual_genes", {}).get("STAG2", False),
        
        # From residual_genes
        "BCORL1": ipssm_data.get("residual_genes", {}).get("BCORL1", False),
        "CEBPA": ipssm_data.get("residual_genes", {}).get("CEBPA", False),
        "ETNK1": ipssm_data.get("residual_genes", {}).get("ETNK1", False),
        "GATA2": ipssm_data.get("residual_genes", {}).get("GATA2", False),
        "GNB1": ipssm_data.get("residual_genes", {}).get("GNB1", False),
        "IDH1": aml_data.get("ELN2024_risk_genes", {}).get("IDH1", False) or ipssm_data.get("residual_genes", {}).get("IDH1", False),
        "NF1": ipssm_data.get("residual_genes", {}).get("NF1", False),
        "PHF6": ipssm_data.get("residual_genes", {}).get("PHF6", False),
        "PPM1D": ipssm_data.get("residual_genes", {}).get("PPM1D", False),
        "PRPF8": ipssm_data.get("residual_genes", {}).get("PRPF8", False),
        "PTPN11": aml_data.get("ELN2024_risk_genes", {}).get("PTPN11", False) or ipssm_data.get("residual_genes", {}).get("PTPN11", False),
        "SETBP1": ipssm_data.get("residual_genes", {}).get("SETBP1", False),
        "WT1": ipssm_data.get("residual_genes", {}).get("WT1", False)
    }
    
    # Create the final input dictionary for IPSS-M calculator
    ipssm_input = {
        # Clinical data
        "HB": hb,
        "PLT": plt,
        "BM_BLAST": bm_blast,
        "ANC": anc,
        
        # Cytogenetics
        "CYTO_IPSSR": None,  # Will be calculated by the calculator
        "del5q": 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_5q", False) or cytogenetics.get("del5q", False) else 0,
        "del7q": 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_7q", False) or cytogenetics.get("del7q", False) else 0,
        "del7_minus7": 1 if aml_data.get("MDS_related_cytogenetics", {}).get("-7", False) or cytogenetics.get("del7_minus7", False) else 0,
        "del17_17p": 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_17p", False) or cytogenetics.get("del17_17p", False) else 0,
        "complex": 1 if aml_data.get("MDS_related_cytogenetics", {}).get("Complex_karyotype", False) or cytogenetics.get("karyotype_complexity") in ["Complex (3 abnormalities)", "Very complex (>3 abnormalities)"] else 0,
        
        # For age-adjusted IPSS-R
        "AGE": age,
        
        # TP53 status
        "TP53mut": tp53mut if isinstance(tp53mut, str) else "0",
        "TP53maxvaf": tp53maxvaf,
        "TP53loh": tp53loh
    }
    
    # Add gene mutations
    for gene, value in gene_mutations.items():
        ipssm_input[gene] = 1 if value else 0
    
    # Add residual genes
    for gene, value in residual_genes.items():
        ipssm_input[gene] = 1 if value else 0
    
    # Add additional cytogenetic details
    if cytogenetics:
        ipssm_input["del11q"] = 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_11q", False) or cytogenetics.get("del11q", False) else 0
        ipssm_input["del12p"] = 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_12p", False) or cytogenetics.get("del12p", False) else 0
        ipssm_input["del20q"] = 1 if aml_data.get("MDS_related_cytogenetics", {}).get("del_20q", False) or cytogenetics.get("del20q", False) else 0
        ipssm_input["plus8"] = 1 if aml_data.get("MDS_related_cytogenetics", {}).get("+8", False) or cytogenetics.get("plus8", False) else 0
        ipssm_input["plus19"] = 1 if cytogenetics.get("plus19", False) else 0
        ipssm_input["i17q"] = 1 if aml_data.get("MDS_related_cytogenetics", {}).get("i_17q", False) or cytogenetics.get("i17q", False) else 0
        ipssm_input["inv3_t3q_del3q"] = 1 if cytogenetics.get("inv3_t3q_del3q", False) else 0
        ipssm_input["minusY"] = 1 if cytogenetics.get("minusY", False) else 0
    
    return ipssm_input


if __name__ == "__main__":
    # If arguments are provided, run the CLI
    if len(sys.argv) > 1:
        main()
    # Otherwise run the demo
    else:
        demo() 