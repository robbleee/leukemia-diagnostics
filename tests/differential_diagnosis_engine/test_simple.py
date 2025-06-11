#!/usr/bin/env python3
"""
Simple test script to debug the differential engine.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.differential_diagnosis_engine.differential_engine import DifferentialDiagnosisEngine

def test_basic_functionality():
    """Test basic functionality of the differential engine."""
    print("🔬 Testing basic functionality...")
    
    # Initialize engine
    engine = DifferentialDiagnosisEngine(output_dir="test_output")
    
    # Test each new test case generation method individually
    test_methods = [
        ("comprehensive_germline_predisposition", engine._generate_comprehensive_germline_test_cases),
        ("vaf_threshold_testing", engine._generate_vaf_threshold_test_cases),
        ("risk_stratification_boundaries", engine._generate_risk_stratification_boundary_cases),
        ("nuanced_dysplasia_patterns", engine._generate_nuanced_dysplasia_test_cases),
        ("clonal_evolution_patterns", engine._generate_clonal_evolution_test_cases),
        ("cytogenetic_complexity_gradations", engine._generate_cytogenetic_complexity_gradation_cases),
        ("microenvironment_interactions", engine._generate_microenvironment_interaction_cases),
        ("mrd_methodology_differences", engine._generate_mrd_methodology_difference_cases),
        ("prognostic_score_boundaries", engine._generate_prognostic_score_boundary_cases),
        ("lab_methodology_dependent", engine._generate_lab_methodology_dependent_cases)
    ]
    
    for method_name, method in test_methods:
        try:
            print(f"  Testing {method_name}...")
            test_cases = method()
            print(f"    ✅ Generated {len(test_cases)} test cases")
            
            # Check first test case structure
            if test_cases:
                first_case = test_cases[0]
                required_fields = [
                    "AML_defining_recurrent_genetic_abnormalities",
                    "MDS_related_mutation", 
                    "MDS_related_cytogenetics",
                    "Biallelic_TP53_mutation",
                    "qualifiers",
                    "test_focus"
                ]
                
                for field in required_fields:
                    if field not in first_case:
                        print(f"    ❌ Missing required field: {field}")
                    else:
                        print(f"    ✅ Has required field: {field}")
        
        except Exception as e:
            print(f"    ❌ Error in {method_name}: {str(e)}")
            print(f"       Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
    
    print("\n🧪 Testing targeted test case generation...")
    
    # Test targeted generation
    focus_areas = [
        "comprehensive_germline_predisposition",
        "vaf_threshold_testing", 
        "risk_stratification_boundaries",
        "mrd_methodology_differences"
    ]
    
    for focus in focus_areas:
        try:
            print(f"  Testing focus: {focus}")
            test_cases = engine.generate_targeted_test_cases(focus)
            print(f"    ✅ Generated {len(test_cases)} test cases")
        except Exception as e:
            print(f"    ❌ Error with focus {focus}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality() 