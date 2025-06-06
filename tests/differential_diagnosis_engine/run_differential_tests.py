#!/usr/bin/env python3
"""
Main script to run differential diagnosis testing between WHO 2022 and ICC 2022 classifications.

This script provides a command-line interface to run the differential testing engine
and generate comprehensive reports on differences between the two classification systems.
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to the path to import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from tests.differential_diagnosis_engine.differential_engine import DifferentialDiagnosisEngine
from tests.differential_diagnosis_engine.diagnosis_mapping import get_test_focus_areas


def main():
    """Main function to run differential testing."""
    parser = argparse.ArgumentParser(
        description="Run differential diagnosis testing between WHO 2022 and ICC 2022 classifications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python run_differential_tests.py
  
  # Run limited tests
  python run_differential_tests.py --max-tests 100
  
  # Run specific focus area
  python run_differential_tests.py --focus blast_thresholds
  
  # Custom output directory
  python run_differential_tests.py --output-dir custom_results
  
  # Show focus areas and exit
  python run_differential_tests.py --list-focus-areas
        """
    )
    
    parser.add_argument(
        "--max-tests", 
        type=int, 
        default=None,
        help="Maximum number of tests to run (default: all tests)"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="differential_test_results",
        help="Directory to save test results (default: differential_test_results)"
    )
    
    parser.add_argument(
        "--focus",
        type=str,
        choices=["blast_thresholds", "therapy_qualifiers", "germline_qualifiers", 
                "tp53_terminology", "mds_blast_ranges", "erythroid_handling", 
                "realistic_clinical_scenarios", "age_dependent_differences", 
                "complex_cytogenetics", "comutation_patterns", "therapy_evolution", 
                "aml_vs_mds_borderline", "disease_type_disagreement", "all"],
        default="all",
        help="Focus on specific test area (default: all)"
    )
    
    parser.add_argument(
        "--list-focus-areas",
        action="store_true",
        help="List available focus areas and exit"
    )
    
    parser.add_argument(
        "--save-report",
        action="store_true",
        default=True,
        help="Save human-readable report (default: True)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Handle list focus areas
    if args.list_focus_areas:
        print("Available test focus areas:")
        print("=" * 50)
        focus_areas = get_test_focus_areas()
        for area, details in focus_areas.items():
            print(f"\n🎯 {area}")
            print(f"   Description: {details['description']}")
            print(f"   Expected: {details['expected_differences']}")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize the testing engine
    print("🧬 Initializing Differential Diagnosis Testing Engine")
    print("=" * 60)
    engine = DifferentialDiagnosisEngine(output_dir=args.output_dir)
    
    if args.verbose:
        print(f"Output directory: {args.output_dir}")
        print(f"Focus area: {args.focus}")
        print(f"Max tests: {args.max_tests or 'unlimited'}")
        print()
    
    # Run the tests
    try:
        if args.focus == "all":
            # Run comprehensive testing
            summary = engine.run_comprehensive_test_suite(test_focus="all", max_tests=args.max_tests)
        else:
            # Run focused testing
            print(f"🎯 Running focused tests for: {args.focus}")
            summary = engine.run_comprehensive_test_suite(test_focus=args.focus, max_tests=args.max_tests)
        
        # Print summary
        print("\n" + "=" * 60)
        print("🔍 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {summary.total_tests}")
        print(f"Equivalent results: {summary.equivalent_results} ({summary.equivalent_results/summary.total_tests*100:.1f}%)")
        print(f"Different results: {summary.different_results} ({summary.different_results/summary.total_tests*100:.1f}%)")
        print()
        
        print("Differences by significance:")
        print(f"  🔴 High impact: {summary.high_significance_differences}")
        print(f"  🟡 Medium impact: {summary.medium_significance_differences}")
        print(f"  🟢 Low impact: {summary.low_significance_differences}")
        print()
        
        if summary.differences_by_focus:
            print("Differences by focus area:")
            for focus, count in sorted(summary.differences_by_focus.items(), key=lambda x: x[1], reverse=True):
                print(f"  📊 {focus}: {count}")
        
        # Save results
        print("\n" + "=" * 60)
        print("💾 SAVING RESULTS")
        print("=" * 60)
        
        # Save JSON results
        json_file = engine.save_results()
        print(f"✅ JSON results saved to: {json_file}")
        
        # Save human-readable report
        if args.save_report:
            report = engine.generate_difference_report()
            report_file = os.path.join(args.output_dir, f"differential_analysis_report_{engine.test_counter}.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"✅ Analysis report saved to: {report_file}")
        
        # Show high-impact differences
        high_impact = engine.get_high_impact_differences()
        if high_impact:
            print(f"\n⚠️  Found {len(high_impact)} HIGH IMPACT differences!")
            print("These represent significant diagnostic discrepancies between WHO and ICC.")
            print("See the full report for detailed analysis.")
        else:
            print("\n✅ No high-impact differences found!")
            print("WHO and ICC classifications are largely consistent.")
        
        # Analyze patterns
        patterns = engine.analyze_difference_patterns()
        if "message" not in patterns:
            print(f"\n📈 PATTERN INSIGHTS")
            print("=" * 30)
            
            if patterns.get("blast_threshold_analysis"):
                print("Most problematic blast percentages:")
                sorted_blasts = sorted(patterns["blast_threshold_analysis"].items(), 
                                     key=lambda x: x[1], reverse=True)
                for blast_pct, count in sorted_blasts[:3]:
                    print(f"  {blast_pct}% blasts: {count} differences")
            
            if patterns.get("therapy_qualifier_analysis"):
                print("Therapy qualifier issues:")
                for therapy, count in patterns["therapy_qualifier_analysis"].items():
                    print(f"  {therapy}: {count} differences")
            
            if patterns.get("category_changes"):
                print("Top category changes:")
                sorted_changes = sorted(patterns["category_changes"].items(), 
                                      key=lambda x: x[1], reverse=True)
                for change, count in sorted_changes[:3]:
                    print(f"  {change}: {count} cases")
        
        print(f"\n🎉 Differential testing complete!")
        print(f"Results available in: {args.output_dir}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        if engine.results:
            print(f"Partial results available: {len(engine.results)} tests completed")
            engine.save_results(filename="partial_results.json")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_quick_demo():
    """Run a quick demonstration of the differential testing engine."""
    print("🧬 Running Quick Differential Testing Demo")
    print("=" * 50)
    
    engine = DifferentialDiagnosisEngine(output_dir="demo_results")
    
    # Generate a small set of test cases
    demo_cases = [
        # Blast threshold difference
        {
            "blasts_percentage": 15,
            "AML_defining_recurrent_genetic_abnormalities": {"CEBPA": True},
            "qualifiers": {}
        },
        # Therapy qualifier difference
        {
            "blasts_percentage": 25,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "qualifiers": {"previous_cytotoxic_therapy": "Immune interventions"}
        },
        # TP53 terminology difference
        {
            "blasts_percentage": 12,
            "Biallelic_TP53_mutation": {"2_x_TP53_mutations": True},
            "AML_defining_recurrent_genetic_abnormalities": {},
            "MDS_related_mutation": {},
            "MDS_related_cytogenetics": {},
            "qualifiers": {}
        },
        # Germline variant difference
        {
            "blasts_percentage": 30,
            "AML_defining_recurrent_genetic_abnormalities": {"RUNX1::RUNX1T1": True},
            "qualifiers": {"predisposing_germline_variant": "Diamond-Blackfan anemia"}
        }
    ]
    
    print(f"Running {len(demo_cases)} demo test cases...")
    
    for i, test_case in enumerate(demo_cases, 1):
        print(f"\n📋 Demo Test {i}:")
        result = engine.run_classification_comparison(test_case, f"demo_{i}")
        
        print(f"  WHO: {result.who_classification}")
        print(f"  ICC: {result.icc_classification}")
        print(f"  Equivalent: {'✅' if result.are_equivalent else '❌'}")
        
        if not result.are_equivalent:
            significance = result.difference_analysis.get("significance", "unknown")
            print(f"  Significance: {significance}")
    
    summary = engine._generate_summary()
    print(f"\n📊 Demo Summary:")
    print(f"  Total: {summary.total_tests}")
    print(f"  Differences: {summary.different_results}")
    print(f"  High impact: {summary.high_significance_differences}")
    
    # Save demo results
    demo_file = engine.save_results("demo_results.json")
    print(f"\n💾 Demo results saved to: {demo_file}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--demo":
        run_quick_demo()
    else:
        main() 