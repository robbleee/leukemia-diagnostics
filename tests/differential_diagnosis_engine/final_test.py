#!/usr/bin/env python3
"""Final test to show the improved clinical impact distribution."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.differential_diagnosis_engine.differential_engine import DifferentialDiagnosisEngine

def main():
    print("🩺 BLOOD CANCER CLASSIFICATION DIFFERENCES - FINAL RESULTS")
    print("=" * 70)
    
    engine = DifferentialDiagnosisEngine()
    summary = engine.run_comprehensive_test_suite()
    
    print(f"\n📊 SUMMARY STATISTICS:")
    print(f"   Total test cases: {summary.total_tests}")
    print(f"   Cases with differences: {summary.different_results}")
    print(f"   Equivalent cases: {summary.equivalent_results}")
    
    print(f"\n🎯 CLINICAL IMPACT DISTRIBUTION:")
    print(f"   🔴 High impact (critical + high): {summary.high_significance_differences}")
    print(f"   🟡 Medium impact: {summary.medium_significance_differences}")
    print(f"   🟢 Low impact: {summary.low_significance_differences}")
    
    if summary.different_results > 0:
        high_pct = (summary.high_significance_differences / summary.different_results) * 100
        medium_pct = (summary.medium_significance_differences / summary.different_results) * 100
        low_pct = (summary.low_significance_differences / summary.different_results) * 100
        
        print(f"\n📈 PERCENTAGE BREAKDOWN:")
        print(f"   High impact: {high_pct:.1f}%")
        print(f"   Medium impact: {medium_pct:.1f}%")
        print(f"   Low impact: {low_pct:.1f}%")
        
        print(f"\n✅ SUCCESS METRICS:")
        if medium_pct >= 20:
            print(f"   ✅ Excellent medium impact representation ({medium_pct:.1f}%)")
        elif medium_pct >= 10:
            print(f"   ✅ Good medium impact representation ({medium_pct:.1f}%)")
        else:
            print(f"   ⚠️  Low medium impact representation ({medium_pct:.1f}%)")
            
        if high_pct <= 80:
            print(f"   ✅ Balanced high impact distribution ({high_pct:.1f}%)")
        else:
            print(f"   ⚠️  High impact cases dominate ({high_pct:.1f}%)")
    
    print(f"\n🏥 CLINICAL SIGNIFICANCE:")
    print(f"   This analysis identifies {summary.different_results} clinically meaningful")
    print(f"   differences between WHO 2022 and ICC 2022 classifications")
    print(f"   that could impact patient treatment decisions.")

if __name__ == "__main__":
    main() 