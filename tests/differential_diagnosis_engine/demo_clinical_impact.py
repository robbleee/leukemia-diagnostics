#!/usr/bin/env python3
"""
Demonstration script showing the enhanced clinical impact assessment system.

This script creates specific test cases designed to showcase all the different
clinical impact features including treatment implications, MRD monitoring
differences, prognostic implications, and targeted therapy considerations.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.differential_diagnosis_engine.differential_engine import DifferentialDiagnosisEngine
from tests.differential_diagnosis_engine.diagnosis_mapping import get_diagnosis_differences


def create_demonstration_cases():
    """Create specific test cases to demonstrate clinical impact features."""
    
    # 1. APL vs AML case - shows emergency treatment differences
    apl_case = {
        "age": 35,
        "blasts_percentage": 60,
        "cytogenetics": ["t(15;17)(q24;q21)"],
        "mutations": ["PML-RARA"],
        "test_focus": "apl_demonstration"
    }
    
    # 2. FLT3+ AML case - shows targeted therapy implications  
    flt3_case = {
        "age": 55,
        "blasts_percentage": 75,
        "mutations": ["FLT3-ITD", "NPM1"],
        "cytogenetics": ["normal"],
        "test_focus": "targeted_therapy_demo"
    }
    
    # 3. IDH-mutated case - shows precision medicine differences
    idh_case = {
        "age": 67,
        "blasts_percentage": 45,
        "mutations": ["IDH1-R132H", "TET2"],
        "cytogenetics": ["normal"],
        "test_focus": "precision_medicine_demo"
    }
    
    # 4. Borderline blast AML/MDS case - shows treatment intensity differences
    borderline_case = {
        "age": 72,
        "blasts_percentage": 15,
        "mutations": ["RUNX1", "ASXL1"],
        "cytogenetics": ["normal"],
        "mds_related_changes": True,
        "test_focus": "treatment_intensity_demo"
    }
    
    # 5. TP53 mutated case - shows risk stratification and therapy differences
    tp53_case = {
        "age": 68,
        "blasts_percentage": 25,
        "mutations": ["TP53", "del(17p)"],
        "cytogenetics": ["complex"],
        "test_focus": "risk_stratification_demo"
    }
    
    # 6. Core binding factor AML - shows MRD monitoring differences
    cbf_case = {
        "age": 28,
        "blasts_percentage": 85,
        "cytogenetics": ["t(8;21)(q22;q22)"],
        "mutations": ["RUNX1-RUNX1T1", "KIT"],
        "test_focus": "mrd_monitoring_demo"
    }
    
    # 7. Germline predisposition case - shows family screening implications
    germline_case = {
        "age": 16,
        "blasts_percentage": 70,
        "mutations": ["CEBPA", "germline CEBPA"],
        "family_history": True,
        "test_focus": "germline_implications_demo"
    }
    
    return [apl_case, flt3_case, idh_case, borderline_case, tp53_case, cbf_case, germline_case]


def demonstrate_clinical_impact():
    """Run demonstration of clinical impact assessment."""
    
    print("🧬 CLINICAL IMPACT ASSESSMENT DEMONSTRATION")
    print("=" * 70)
    print("Showcasing sophisticated clinical impact scoring for WHO vs ICC differences")
    print()
    
    # Create engine
    engine = DifferentialDiagnosisEngine()
    
    # Create demonstration cases
    demo_cases = create_demonstration_cases()
    
    print(f"📋 Running {len(demo_cases)} demonstration cases...")
    print()
    
    # Run each test case
    high_impact_found = []
    
    for i, test_case in enumerate(demo_cases, 1):
        print(f"Testing Case #{i}: {test_case['test_focus']}")
        
        # Run the test
        result = engine.run_single_test(test_case, test_case['test_focus'])
        engine.results.append(result)
        
        # Show immediate impact
        if result.clinical_impact_score >= 50:
            high_impact_found.append(result)
            print(f"  ⚠️  HIGH IMPACT (Score: {result.clinical_impact_score})")
            print(f"  WHO: {result.who_classification}")
            print(f"  ICC: {result.icc_classification}")
        else:
            print(f"  ✅ Low impact (Score: {result.clinical_impact_score})")
        print()
    
    # Generate and display comprehensive report
    print("=" * 70)
    print("📊 COMPREHENSIVE CLINICAL IMPACT ANALYSIS")
    print("=" * 70)
    
    if high_impact_found:
        print(f"Found {len(high_impact_found)} high-impact cases!")
        print()
        
        for i, case in enumerate(high_impact_found, 1):
            print(f"HIGH IMPACT CASE #{i} (Score: {case.clinical_impact_score})")
            print("-" * 50)
            print(f"WHO: {case.who_classification}")
            print(f"ICC: {case.icc_classification}")
            print()
            
            if case.treatment_implications:
                print("💊 TREATMENT IMPLICATIONS:")
                for treatment in case.treatment_implications:
                    print(f"  • {treatment}")
                print()
            
            if case.mrd_implications:
                print("🔬 MRD MONITORING IMPLICATIONS:")
                for mrd in case.mrd_implications:
                    print(f"  • {mrd}")
                print()
            
            if case.prognostic_implications:
                print("📊 PROGNOSTIC IMPLICATIONS:")
                for prognosis in case.prognostic_implications:
                    print(f"  • {prognosis}")
                print()
            
            if case.clinical_consequences:
                print("🏥 CLINICAL CONSEQUENCES:")
                for consequence in case.clinical_consequences:
                    print(f"  • {consequence}")
                print()
            
            print("-" * 50)
            print()
    else:
        print("No high-impact differences found in this demonstration.")
        print("This could indicate good concordance between WHO and ICC systems")
        print("for these specific test cases.")
    
    # Summary statistics
    total_cases = len(engine.results)
    avg_impact = sum(r.clinical_impact_score for r in engine.results) / total_cases if total_cases > 0 else 0
    max_impact = max(r.clinical_impact_score for r in engine.results) if engine.results else 0
    
    treatment_affected = len([r for r in engine.results if r.treatment_implications])
    mrd_affected = len([r for r in engine.results if r.mrd_implications])
    prognosis_affected = len([r for r in engine.results if r.prognostic_implications])
    
    print("📈 DEMONSTRATION STATISTICS")
    print("-" * 30)
    print(f"Total cases tested: {total_cases}")
    print(f"Average impact score: {avg_impact:.1f}")
    print(f"Maximum impact score: {max_impact}")
    print(f"Cases affecting treatment: {treatment_affected} ({100*treatment_affected/total_cases:.1f}%)")
    print(f"Cases affecting MRD monitoring: {mrd_affected} ({100*mrd_affected/total_cases:.1f}%)")
    print(f"Cases affecting prognosis: {prognosis_affected} ({100*prognosis_affected/total_cases:.1f}%)")
    print()
    
    print("✅ Clinical Impact Assessment Demonstration Complete!")
    print()
    print("KEY FEATURES DEMONSTRATED:")
    print("• Treatment decision impact scoring (intensive vs supportive care)")
    print("• Targeted therapy eligibility differences (FLT3, IDH, TP53)")
    print("• MRD monitoring method differences (molecular vs flow cytometry)")
    print("• Risk stratification impacts (ELN, IPSS-M implications)")
    print("• Emergency treatment protocols (APL vs standard AML)")
    print("• Germline implications (family screening, drug considerations)")
    print("• Quantitative clinical impact scoring (0-200+ scale)")


if __name__ == "__main__":
    demonstrate_clinical_impact() 