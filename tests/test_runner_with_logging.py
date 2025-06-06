#!/usr/bin/env python3
"""
Comprehensive test runner that captures detailed test results from existing pytest files and exports to YAML.

This script runs all AML and MDS classification tests from the existing test files and captures:
- Input data from all test cases
- Expected outputs  
- Actual outputs
- Derivation logic
- Test metadata

Results are saved to detailed_test_results.yaml
"""

import sys
import os
import yaml
import json
import pytest
import inspect
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add the project root to the Python path (parent directory of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the classification functions and test modules
from classifiers.aml_classifier import classify_AML_WHO2022, classify_AML_ICC2022
from classifiers.mds_classifier import classify_MDS_WHO2022, classify_MDS_ICC2022

# Import test modules to extract test cases
import test_aml_classification
import test_mds_classification


def extract_parametrized_test_cases(test_class):
    """Extract test cases from parametrized pytest test classes."""
    test_cases = []
    
    # Get all methods in the test class
    for method_name in dir(test_class):
        method = getattr(test_class, method_name)
        
        # Check if it's a test method with parametrize decorator
        if (callable(method) and method_name.startswith('test_') and 
            hasattr(method, 'pytestmark')):
            
            # Look for parametrize marks
            for mark in method.pytestmark:
                if mark.name == 'parametrize':
                    # Extract parameter names and values
                    argnames = mark.args[0] if mark.args else ""
                    argvalues = mark.args[1] if len(mark.args) > 1 else []
                    
                    # Create individual test cases
                    for i, values in enumerate(argvalues):
                        if isinstance(argnames, str):
                            param_names = [name.strip() for name in argnames.split(',')]
                        else:
                            param_names = argnames
                        
                        if not isinstance(values, tuple):
                            values = (values,)
                        
                        # Create parameter dictionary
                        params = dict(zip(param_names, values))
                        
                        test_case = {
                            "test_class": test_class.__name__,
                            "test_method": method_name,
                            "test_name": f"{test_class.__name__}::{method_name}[{i}]",
                            "parameters": params
                        }
                        
                        test_cases.append(test_case)
    
    return test_cases


def run_single_test_case(test_case):
    """Run a single test case and capture results."""
    print(f"  Running: {test_case['test_name']}")
    
    # Extract input data and expected results from parameters
    params = test_case['parameters']
    parsed_data = params.get('parsed_data', {})
    
    # Handle different parameter formats
    expected_who = None
    expected_icc = None
    
    if 'expected_classification' in params:
        # Single classifier test - determine which classifier based on test class
        if 'WHO2022' in test_case['test_class']:
            expected_who = params['expected_classification']
        elif 'ICC2022' in test_case['test_class']:
            expected_icc = params['expected_classification']
        else:
            # For other test classes, run both
            expected_who = params['expected_classification']
            expected_icc = params['expected_classification']
    elif 'expected_who_classification' in params:
        # Dual classifier test
        expected_who = params['expected_who_classification']
        expected_icc = params['expected_icc_classification']
    elif 'expected_who_result' in params:
        # Edge case test
        expected_who = params['expected_who_result']
        expected_icc = params['expected_icc_result']
    
    result = {
        "test_name": test_case['test_name'],
        "test_class": test_case['test_class'],
        "test_method": test_case['test_method'],
        "input_data": parsed_data,
        "who_2022": None,
        "icc_2022": None
    }
    
    # Run AML classification
    if 'aml' in test_case['test_name'].lower():
        # Run WHO 2022 classification if expected
        if expected_who is not None:
            try:
                # Handle special cases for M6a tests
                special_kwargs = {}
                if (parsed_data.get('AML_differentiation') == 'M6a' and 
                    expected_who and 'define by differentiation' in expected_who):
                    special_kwargs['not_erythroid'] = True
                
                who_result, who_derivation = classify_AML_WHO2022(parsed_data, **special_kwargs)
                
                result["who_2022"] = {
                    "expected": expected_who,
                    "actual": who_result,
                    "derivation": who_derivation,
                    "success": True,
                    "matches_expected": who_result == expected_who,
                    "error": None
                }
            except Exception as e:
                result["who_2022"] = {
                    "expected": expected_who,
                    "actual": f"ERROR: {str(e)}",
                    "derivation": [],
                    "success": False,
                    "matches_expected": False,
                    "error": str(e)
                }
        
        # Run ICC 2022 classification if expected
        if expected_icc is not None:
            try:
                icc_result, icc_derivation = classify_AML_ICC2022(parsed_data)
                
                result["icc_2022"] = {
                    "expected": expected_icc,
                    "actual": icc_result,
                    "derivation": icc_derivation,
                    "success": True,
                    "matches_expected": icc_result == expected_icc,
                    "error": None
                }
            except Exception as e:
                result["icc_2022"] = {
                    "expected": expected_icc,
                    "actual": f"ERROR: {str(e)}",
                    "derivation": [],
                    "success": False,
                    "matches_expected": False,
                    "error": str(e)
                }
    
    # Run MDS classification
    elif 'mds' in test_case['test_name'].lower():
        # Run WHO 2022 classification if expected
        if expected_who is not None:
            try:
                who_result, who_derivation = classify_MDS_WHO2022(parsed_data)
                
                result["who_2022"] = {
                    "expected": expected_who,
                    "actual": who_result,
                    "derivation": who_derivation,
                    "success": True,
                    "matches_expected": who_result == expected_who,
                    "error": None
                }
            except Exception as e:
                result["who_2022"] = {
                    "expected": expected_who,
                    "actual": f"ERROR: {str(e)}",
                    "derivation": [],
                    "success": False,
                    "matches_expected": False,
                    "error": str(e)
                }
        
        # Run ICC 2022 classification if expected
        if expected_icc is not None:
            try:
                icc_result, icc_derivation = classify_MDS_ICC2022(parsed_data)
                
                result["icc_2022"] = {
                    "expected": expected_icc,
                    "actual": icc_result,
                    "derivation": icc_derivation,
                    "success": True,
                    "matches_expected": icc_result == expected_icc,
                    "error": None
                }
            except Exception as e:
                result["icc_2022"] = {
                    "expected": expected_icc,
                    "actual": f"ERROR: {str(e)}",
                    "derivation": [],
                    "success": False,
                    "matches_expected": False,
                    "error": str(e)
                }
    
    return result


def extract_and_run_aml_tests():
    """Extract and run all AML test cases."""
    print("Extracting and running AML classification tests...")
    
    aml_test_classes = [
        test_aml_classification.TestAMLWHO2022BasicClassification,
        test_aml_classification.TestAMLWHO2022FABDifferentiation,
        test_aml_classification.TestAMLWHO2022Qualifiers,
        test_aml_classification.TestAMLICC2022BasicClassification,
        test_aml_classification.TestAMLICC2022BlastThresholds,
        test_aml_classification.TestAMLICC2022Qualifiers,
        test_aml_classification.TestAMLEdgeCases,
        test_aml_classification.TestAMLComplexScenarios,
        test_aml_classification.TestAMLErrorHandling,
        test_aml_classification.TestAMLStressTests,
    ]
    
    all_test_results = []
    
    for test_class in aml_test_classes:
        print(f"Processing test class: {test_class.__name__}")
        test_cases = extract_parametrized_test_cases(test_class)
        
        for test_case in test_cases:
            result = run_single_test_case(test_case)
            all_test_results.append(result)
    
    return all_test_results


def extract_and_run_mds_tests():
    """Extract and run all MDS test cases."""
    print("Extracting and running MDS classification tests...")
    
    # Get all test classes from the MDS test module
    mds_test_classes = []
    for name in dir(test_mds_classification):
        obj = getattr(test_mds_classification, name)
        if (inspect.isclass(obj) and name.startswith('Test') and 
            obj.__module__ == test_mds_classification.__name__):
            mds_test_classes.append(obj)
    
    all_test_results = []
    
    for test_class in mds_test_classes:
        print(f"Processing test class: {test_class.__name__}")
        test_cases = extract_parametrized_test_cases(test_class)
        
        for test_case in test_cases:
            result = run_single_test_case(test_case)
            all_test_results.append(result)
    
    return all_test_results


def main():
    """Main function to run all tests and generate YAML report."""
    print("Starting comprehensive test run with detailed logging...")
    print("This will extract and run all existing AML and MDS tests with derivation capture.")
    print("=" * 80)
    
    # Extract and run all test cases
    aml_results = extract_and_run_aml_tests()
    mds_results = extract_and_run_mds_tests()
    
    # Create comprehensive results structure
    combined_results = {
        "test_run_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_test_suites": 2,
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "extraction_method": "programmatic_parametrize_parsing"
        },
        "test_suites": {
            "aml_classification": {
                "test_suite": "AML Classification",
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(aml_results),
                "test_cases": aml_results
            },
            "mds_classification": {
                "test_suite": "MDS Classification", 
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(mds_results),
                "test_cases": mds_results
            }
        },
        "summary": {
            "aml": {
                "total_tests": len(aml_results),
                "who_2022_passed": sum(1 for r in aml_results if r.get("who_2022") and r["who_2022"].get("matches_expected") == True),
                "icc_2022_passed": sum(1 for r in aml_results if r.get("icc_2022") and r["icc_2022"].get("matches_expected") == True),
                "who_2022_errors": sum(1 for r in aml_results if r.get("who_2022") and r["who_2022"].get("success") == False),
                "icc_2022_errors": sum(1 for r in aml_results if r.get("icc_2022") and r["icc_2022"].get("success") == False),
                "who_2022_total": sum(1 for r in aml_results if r.get("who_2022") is not None),
                "icc_2022_total": sum(1 for r in aml_results if r.get("icc_2022") is not None)
            },
            "mds": {
                "total_tests": len(mds_results),
                "who_2022_passed": sum(1 for r in mds_results if r.get("who_2022") and r["who_2022"].get("matches_expected") == True),
                "icc_2022_passed": sum(1 for r in mds_results if r.get("icc_2022") and r["icc_2022"].get("matches_expected") == True),
                "who_2022_errors": sum(1 for r in mds_results if r.get("who_2022") and r["who_2022"].get("success") == False),
                "icc_2022_errors": sum(1 for r in mds_results if r.get("icc_2022") and r["icc_2022"].get("success") == False),
                "who_2022_total": sum(1 for r in mds_results if r.get("who_2022") is not None),
                "icc_2022_total": sum(1 for r in mds_results if r.get("icc_2022") is not None)
            }
        }
    }
    
    # Save to YAML file
    output_file = "detailed_test_results.yaml"
    print(f"\nSaving detailed results to {output_file}...")
    
    with open(output_file, 'w') as f:
        yaml.dump(combined_results, f, default_flow_style=False, indent=2, sort_keys=False)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    aml_summary = combined_results["summary"]["aml"]
    mds_summary = combined_results["summary"]["mds"]
    
    print(f"\nAML Classification Tests:")
    print(f"  Total test cases extracted: {aml_summary['total_tests']}")
    print(f"  WHO 2022 - Passed: {aml_summary['who_2022_passed']}/{aml_summary['who_2022_total']}")
    print(f"  ICC 2022 - Passed: {aml_summary['icc_2022_passed']}/{aml_summary['icc_2022_total']}")
    print(f"  WHO 2022 - Errors: {aml_summary['who_2022_errors']}")
    print(f"  ICC 2022 - Errors: {aml_summary['icc_2022_errors']}")
    
    print(f"\nMDS Classification Tests:")
    print(f"  Total test cases extracted: {mds_summary['total_tests']}")
    print(f"  WHO 2022 - Passed: {mds_summary['who_2022_passed']}/{mds_summary['who_2022_total']}")
    print(f"  ICC 2022 - Passed: {mds_summary['icc_2022_passed']}/{mds_summary['icc_2022_total']}")
    print(f"  WHO 2022 - Errors: {mds_summary['who_2022_errors']}")
    print(f"  ICC 2022 - Errors: {mds_summary['icc_2022_errors']}")
    
    total_tests = aml_summary['total_tests'] + mds_summary['total_tests']
    total_passed = (aml_summary['who_2022_passed'] + aml_summary['icc_2022_passed'] + 
                   mds_summary['who_2022_passed'] + mds_summary['icc_2022_passed'])
    total_possible = (aml_summary['who_2022_total'] + aml_summary['icc_2022_total'] + 
                     mds_summary['who_2022_total'] + mds_summary['icc_2022_total'])
    
    print(f"\nOverall Results:")
    print(f"  Total test cases: {total_tests}")
    print(f"  Total classification attempts: {total_possible}")
    print(f"  Successful classifications: {total_passed}")
    print(f"  Success rate: {(total_passed/total_possible)*100:.1f}%" if total_possible > 0 else "N/A")
    
    print(f"\nDetailed results with derivation logic saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main() 