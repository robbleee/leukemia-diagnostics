#!/usr/bin/env python3
"""Debug script to check significance level assignments."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from tests.differential_diagnosis_engine.diagnosis_mapping import get_diagnosis_differences

def test_significance_assignment():
    """Test how significance is being assigned."""
    print("Testing significance assignment...")
    
    # Test case that should be medium impact
    test_case = {
        "blasts_percentage": 8,
        "AML_defining_recurrent_genetic_abnormalities": {},
        "MDS_related_mutation": {"SF3B1": True},
        "MDS_related_cytogenetics": {},
        "Biallelic_TP53_mutation": {},
        "qualifiers": {}
    }
    
    # Run classifications
    who_result, who_derivation, who_disease_type = classify_combined_WHO2022(test_case, not_erythroid=False)
    icc_result, icc_derivation, icc_disease_type = classify_combined_ICC2022(test_case)
    
    # Analyze differences
    difference_analysis = get_diagnosis_differences(who_result, icc_result)
    
    print(f"WHO: {who_result}")
    print(f"ICC: {icc_result}")
    print(f"Score: {difference_analysis['clinical_impact_score']}")
    print(f"Significance: {difference_analysis['significance']}")
    print(f"Are equivalent: {difference_analysis['are_equivalent']}")
    print()
    
    # Check several test cases
    test_cases = [
        {
            "name": "SF3B1 MDS terminology",
            "data": {
                "blasts_percentage": 4,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {"SF3B1": True},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {},
                "qualifiers": {}
            }
        },
        {
            "name": "Blast terminology difference",
            "data": {
                "blasts_percentage": 8,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {},
                "qualifiers": {}
            }
        },
        {
            "name": "TP53 terminology",
            "data": {
                "blasts_percentage": 12,
                "AML_defining_recurrent_genetic_abnormalities": {},
                "MDS_related_mutation": {},
                "MDS_related_cytogenetics": {},
                "Biallelic_TP53_mutation": {"1_x_TP53_mutation_50_percent_vaf": True},
                "qualifiers": {}
            }
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        
        who_result, _, _ = classify_combined_WHO2022(case['data'], not_erythroid=False)
        icc_result, _, _ = classify_combined_ICC2022(case['data'])
        
        difference_analysis = get_diagnosis_differences(who_result, icc_result)
        
        print(f"  WHO: {who_result}")
        print(f"  ICC: {icc_result}")
        print(f"  Score: {difference_analysis['clinical_impact_score']}")
        print(f"  Significance: {difference_analysis['significance']}")
        print(f"  Equivalent: {difference_analysis['are_equivalent']}")

if __name__ == "__main__":
    test_significance_assignment() 