#!/usr/bin/env python3
"""
Test script for the AML treatment parser
Demonstrates how to use the parser with sample medical reports
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.treatment_parser import parse_treatment_data, validate_treatment_data
from utils.aml_treatment_recommendations import get_consensus_treatment_recommendation, determine_treatment_eligibility
import json

def test_sample_reports():
    """Test the parser with various sample reports."""
    
    # Sample report 1: Favorable CBF AML
    report_1 = """
    65-year-old female with acute myeloid leukemia.
    
    Flow cytometry: 80% blasts, CD33 positive in 90% of cells.
    
    Cytogenetics: t(8;21)(q22;q22) detected.
    
    Molecular: RUNX1-RUNX1T1 fusion confirmed by RT-PCR.
    
    History: No prior malignancy, chemotherapy, or radiation exposure.
    """
    
    # Sample report 2: FLT3-mutated AML
    report_2 = """
    45-year-old male, newly diagnosed AML.
    
    Flow cytometry: 85% blasts, CD33 expression in 75% of cells.
    
    Molecular testing: NPM1 mutation detected, FLT3-ITD positive with high allelic ratio.
    
    Cytogenetics: Normal karyotype 46,XY.
    
    No history of MDS or prior therapy.
    """
    
    # Sample report 3: Secondary AML with MDS-related changes
    report_3 = """
    72-year-old male with AML arising from MDS diagnosed 6 months ago.
    
    Flow cytometry: 65% blasts, CD33 negative.
    
    Cytogenetics: Complex karyotype with monosomy 7 and deletion 5q.
    
    Molecular: ASXL1 and RUNX1 mutations detected.
    
    Morphology: Dysplastic changes in all three lineages.
    """
    
    # Sample report 4: APL
    report_4 = """
    38-year-old female with acute promyelocytic leukemia.
    
    Flow cytometry: Abnormal promyelocytes, CD33 positive.
    
    Cytogenetics: t(15;17)(q24;q21) detected.
    
    Molecular: PML-RARA fusion confirmed.
    
    Coagulopathy present with DIC.
    """
    
    reports = [
        ("Favorable CBF AML", report_1, 65),
        ("FLT3-mutated AML", report_2, 45),
        ("Secondary AML", report_3, 72),
        ("APL", report_4, 38)
    ]
    
    print("=" * 80)
    print("AML TREATMENT PARSER TEST RESULTS")
    print("=" * 80)
    
    for i, (case_name, report, age) in enumerate(reports, 1):
        print(f"\n--- CASE {i}: {case_name} ---")
        print(f"Patient Age: {age} years")
        
        # Parse the report
        print("\n📋 Parsing report...")
        parsed_data = parse_treatment_data(report)
        
        if not parsed_data:
            print("❌ Failed to parse report")
            continue
        
        # Validate data
        parsed_data = validate_treatment_data(parsed_data)
        
        # Display key findings
        print("\n🔍 Key Findings:")
        
        # Clinical qualifiers
        qualifiers = parsed_data.get("qualifiers", {})
        if any(qualifiers.values()):
            print("  Clinical History:")
            for key, value in qualifiers.items():
                if value:
                    print(f"    • {key.replace('_', ' ').title()}")
        
        # CD33 status
        cd33_pos = parsed_data.get("cd33_positive")
        cd33_pct = parsed_data.get("cd33_percentage")
        if cd33_pct is not None:
            print(f"  CD33: {cd33_pct}% ({'Positive' if cd33_pct >= 20 else 'Negative'})")
        elif cd33_pos is not None:
            print(f"  CD33: {'Positive' if cd33_pos else 'Negative'}")
        
        # Genetic abnormalities
        aml_genes = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        positive_genes = [gene for gene, present in aml_genes.items() if present]
        if positive_genes:
            print(f"  AML-defining genes: {', '.join(positive_genes)}")
        
        # MDS-related features
        mds_mutations = parsed_data.get("MDS_related_mutation", {})
        mds_positive = [gene for gene, present in mds_mutations.items() if present]
        if mds_positive:
            print(f"  MDS-related mutations: {', '.join(mds_positive)}")
        
        mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
        cyto_positive = [abnorm for abnorm, present in mds_cyto.items() if present]
        if cyto_positive:
            print(f"  MDS-related cytogenetics: {', '.join(cyto_positive)}")
        
        # Get treatment eligibility
        print("\n🎯 Treatment Eligibility:")
        try:
            eligible_treatments = determine_treatment_eligibility(parsed_data)
            for treatment in eligible_treatments:
                print(f"  ✅ {treatment}")
        except Exception as e:
            print(f"  ❌ Error determining eligibility: {e}")
        
        # Get consensus recommendation
        print("\n🏥 Consensus Recommendation:")
        try:
            eln_risk = "Intermediate"  # Simplified for demo
            recommendation = get_consensus_treatment_recommendation(parsed_data, age, eln_risk)
            print(f"  Recommended: {recommendation['recommended_treatment']}")
            print(f"  Rationale: {recommendation['rationale']}")
        except Exception as e:
            print(f"  ❌ Error getting recommendation: {e}")
        
        print("\n" + "-" * 60)


def test_field_mapping():
    """Test that all required fields are properly mapped."""
    
    print("\n" + "=" * 80)
    print("FIELD MAPPING VALIDATION")
    print("=" * 80)
    
    # Test with empty report to get default structure
    empty_data = parse_treatment_data("")
    
    required_fields = {
        "qualifiers": {
            "therapy_related", "previous_chemotherapy", "previous_radiotherapy",
            "previous_MDS", "previous_MPN", "previous_MDS/MPN", "previous_CMML",
            "relapsed", "refractory", "secondary"
        },
        "AML_defining_recurrent_genetic_abnormalities": {
            "RUNX1_RUNX1T1", "t_8_21", "CBFB_MYH11", "inv_16", "t_16_16",
            "NPM1_mutation", "FLT3_ITD", "FLT3_TKD", "PML_RARA"
        },
        "MDS_related_mutation": {
            "FLT3", "ASXL1", "BCOR", "EZH2", "RUNX1", "SF3B1",
            "SRSF2", "STAG2", "U2AF1", "ZRSR2", "UBA1", "JAK2"
        },
        "MDS_related_cytogenetics": {
            "Complex_karyotype", "-5", "del_5q", "-7", "del_7q", "-17", "del_17p"
        }
    }
    
    # Check if all required fields are present
    all_present = True
    
    for category, expected_fields in required_fields.items():
        print(f"\n{category}:")
        if category in empty_data and isinstance(empty_data[category], dict):
            actual_fields = set(empty_data[category].keys())
            missing = expected_fields - actual_fields
            extra = actual_fields - expected_fields
            
            if missing:
                print(f"  ❌ Missing fields: {missing}")
                all_present = False
            if extra:
                print(f"  ⚠️  Extra fields: {extra}")
            if not missing and not extra:
                print(f"  ✅ All {len(expected_fields)} fields present")
        else:
            print(f"  ❌ Category missing or not a dict")
            all_present = False
    
    # Check top-level fields
    top_level_fields = {"cd33_positive", "cd33_percentage", "number_of_dysplastic_lineages", "no_cytogenetics_data"}
    for field in top_level_fields:
        if field in empty_data:
            print(f"✅ {field}: present")
        else:
            print(f"❌ {field}: missing")
            all_present = False
    
    print(f"\n{'✅ All required fields validated!' if all_present else '❌ Some fields are missing!'}")


if __name__ == "__main__":
    test_sample_reports()
    test_field_mapping()
    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80) 