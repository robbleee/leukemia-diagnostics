#!/usr/bin/env python3
"""
Combine CRUK and NIHR Clinical Trials Data

This script merges the clinical trials data from both CRUK and NIHR sources
into a single unified JSON file with proper metadata and source tracking.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_trials_data(file_path, source_name):
    """Load trials data from JSON file and add source metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            trials = json.load(f)
        
        logger.info(f"Loaded {len(trials)} trials from {source_name}")
        
        # Add source metadata to each trial
        for trial in trials:
            trial['data_source'] = source_name
            trial['source_file'] = str(file_path)
        
        return trials
    
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from {file_path}: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        return []

def add_trial_ids(trials):
    """Add unique trial IDs to each trial."""
    for i, trial in enumerate(trials, 1):
        trial['trial_id'] = i
    return trials

def create_combined_metadata(cruk_trials, nihr_trials):
    """Create metadata for the combined dataset."""
    return {
        "dataset_info": {
            "name": "Combined UK Clinical Trials - Leukemia",
            "description": "Combined clinical trials data from CRUK and NIHR sources for leukemia research",
            "created_date": datetime.now().isoformat(),
            "total_trials": len(cruk_trials) + len(nihr_trials),
            "sources": {
                "cruk": {
                    "name": "Cancer Research UK Clinical Trials Database",
                    "url": "https://www.cancerresearchuk.org/find-a-clinical-trial",
                    "trial_count": len(cruk_trials),
                    "description": "Clinical trials from Cancer Research UK database"
                },
                "nihr": {
                    "name": "NIHR Be Part of Research",
                    "url": "https://bepartofresearch.nihr.ac.uk/",
                    "trial_count": len(nihr_trials),
                    "description": "Clinical trials from NHS Research and Development database"
                }
            }
        },
        "data_quality": {
            "cruk_trials_with_eligibility": sum(1 for trial in cruk_trials if trial.get('who_can_enter', '').strip()),
            "nihr_trials_with_eligibility": sum(1 for trial in nihr_trials if trial.get('who_can_enter', '').strip()),
            "total_trials_with_eligibility": sum(1 for trial in cruk_trials + nihr_trials if trial.get('who_can_enter', '').strip())
        },
        "field_mapping": {
            "common_fields": [
                "trial_id", "title", "link", "description", "type", "status", 
                "cancer_types", "locations", "who_can_enter", "data_source"
            ],
            "cruk_specific_fields": [
                "recruitment_start", "recruitment_start_iso", "recruitment_end", 
                "recruitment_end_iso", "chief_investigator", "supported_by",
                "contact_phone", "contact_email", "location_panel"
            ],
            "nihr_specific_fields": [
                "location_panel"
            ]
        }
    }

def combine_trials():
    """Main function to combine CRUK and NIHR trials data."""
    logger.info("Starting to combine clinical trials data...")
    
    # File paths
    cruk_file = Path("cruk_clinical_trials.json")
    nihr_file = Path("nihr_clinical_trials.json")
    output_file = Path("combined_clinical_trials.json")
    
    # Load data from both sources
    cruk_trials = load_trials_data(cruk_file, "CRUK")
    nihr_trials = load_trials_data(nihr_file, "NIHR")
    
    if not cruk_trials and not nihr_trials:
        logger.error("No trial data loaded from either source. Exiting.")
        return
    
    # Combine all trials
    all_trials = cruk_trials + nihr_trials
    
    # Add unique trial IDs
    all_trials = add_trial_ids(all_trials)
    
    # Create metadata
    metadata = create_combined_metadata(cruk_trials, nihr_trials)
    
    # Create final combined structure
    combined_data = {
        "metadata": metadata,
        "trials": all_trials
    }
    
    # Save combined data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully saved combined data to {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 COMBINED CLINICAL TRIALS DATASET CREATED")
        print("="*60)
        print(f"📁 Output File: {output_file}")
        print(f"📊 Total Trials: {len(all_trials)}")
        print(f"   • CRUK Trials: {len(cruk_trials)}")
        print(f"   • NIHR Trials: {len(nihr_trials)}")
        print(f"📋 Trials with Eligibility Criteria: {metadata['data_quality']['total_trials_with_eligibility']}")
        print(f"📅 Created: {metadata['dataset_info']['created_date']}")
        print("="*60)
        
        # File size info
        file_size = output_file.stat().st_size
        if file_size > 1024*1024:
            size_str = f"{file_size/(1024*1024):.1f}MB"
        elif file_size > 1024:
            size_str = f"{file_size/1024:.1f}KB"
        else:
            size_str = f"{file_size}B"
        
        print(f"💾 File Size: {size_str}")
        print("✅ Combination completed successfully!")
        
    except Exception as e:
        logger.error(f"Error saving combined data: {str(e)}")

if __name__ == "__main__":
    combine_trials() 