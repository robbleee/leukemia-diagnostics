#!/usr/bin/env python3
"""
Test script to check the clinical impact scoring distribution after rebalancing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Fix imports for module structure
from classifiers.aml_mds_combined import classify_combined_WHO2022, classify_combined_ICC2022
from tests.differential_diagnosis_engine.diagnosis_mapping import get_diagnosis_differences
from tests.differential_diagnosis_engine.differential_engine import DifferentialDiagnosisEngine

def test_scoring_distribution():
    """Test the new scoring distribution."""
    print("Testing new clinical impact scoring distribution...")
    print("=" * 60)
    
    engine = DifferentialDiagnosisEngine()
    
    # Run a smaller subset for quick testing
    summary = engine.run_comprehensive_test_suite(max_tests=100)
    
    print(f"\nTEST RESULTS (100 tests):")
    print(f"Total tests: {summary.total_tests}")
    print(f"Equivalent results: {summary.equivalent_results}")
    print(f"Different results: {summary.different_results}")
    print()
    
    print("Significance Distribution:")
    print(f"  🔴 High impact (critical + high): {summary.high_significance_differences}")
    print(f"  🟡 Medium impact: {summary.medium_significance_differences}")
    print(f"  🟢 Low impact (low + minimal): {summary.low_significance_differences}")
    print()
    
    # Calculate percentages
    if summary.different_results > 0:
        high_pct = (summary.high_significance_differences / summary.different_results) * 100
        medium_pct = (summary.medium_significance_differences / summary.different_results) * 100
        low_pct = (summary.low_significance_differences / summary.different_results) * 100
        
        print("Distribution of Different Results:")
        print(f"  High impact: {high_pct:.1f}%")
        print(f"  Medium impact: {medium_pct:.1f}%")
        print(f"  Low impact: {low_pct:.1f}%")
        print()
        
        # Check if distribution is more balanced
        if medium_pct > 10:
            print("✅ Better distribution achieved - significant medium impact cases found!")
        else:
            print("⚠️  Still need more medium impact cases")
    
    # Show detailed score analysis
    if engine.results:
        different_results = [r for r in engine.results if not r.are_equivalent]
        if different_results:
            scores = [r.clinical_impact_score for r in different_results]
            print(f"\nScore Analysis:")
            print(f"  Score range: {min(scores):.0f} to {max(scores):.0f}")
            print(f"  Average score: {sum(scores)/len(scores):.1f}")
            
            # Count by score ranges
            score_ranges = {
                "0": len([s for s in scores if s == 0]),
                "1-24": len([s for s in scores if 1 <= s < 25]),
                "25-49": len([s for s in scores if 25 <= s < 50]),
                "50-79": len([s for s in scores if 50 <= s < 80]),
                "80+": len([s for s in scores if s >= 80])
            }
            
            print(f"\nDetailed Score Distribution:")
            for range_name, count in score_ranges.items():
                if count > 0:
                    pct = (count / len(scores)) * 100
                    print(f"  {range_name}: {count} cases ({pct:.1f}%)")

if __name__ == "__main__":
    test_scoring_distribution() 