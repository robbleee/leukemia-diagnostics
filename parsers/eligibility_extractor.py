import asyncio
import json
import os
import streamlit as st
from openai import AsyncOpenAI
from datetime import datetime

class EligibilityExtractor:
    def __init__(self, max_concurrent_requests: int = 10):
        self.client = AsyncOpenAI(api_key=st.secrets["openai"]["api_key"])
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def extract_eligibility_criteria(self, who_can_enter_text: str, trial_title: str) -> dict:
        """
        Extract structured eligibility criteria from free-text 'who_can_enter' field
        Based on analysis of actual clinical trials data
        """
        if not who_can_enter_text.strip():
            return {}
        
        # Define the structured format based on actual data patterns
        required_json_structure = {
            "age_criteria": {
                "min_age": None,  # integer (extracted from "at least X years old")
                "max_age": None,  # integer (extracted from "up to X years", "between X and Y")
                "age_restrictions": []  # specific age-related text
            },
            "performance_status": {
                "ecog_status": [],           # e.g., ["0", "1", "2"] or ["0-2"]
                "karnofsky_status": [],      # e.g., ["≥60", "≥70"]
                "lansky_status": [],         # pediatric, e.g., ["≥50"]
                "general_status": []         # non-specific performance requirements
            },
            "genetic_biomarkers": {
                "required_mutations": [],    # JAK2, NPM1, FLT3, BCR-ABL, Philadelphia chromosome, etc.
                "excluded_mutations": [],    # mutations that exclude participation
                "required_biomarkers": [],   # CD33+, CD20+, PD-L1+, etc.
                "chromosomal_changes": []    # del(5q), etc.
            },
            "cancer_specifics": {
                "required_cancer_types": [],     # specific cancer types that qualify
                "excluded_cancer_types": [],     # cancer types that exclude
                "disease_stage_requirements": [], # stage requirements
                "remission_status": []           # remission/relapse requirements
            },
            "previous_treatments": {
                "required_prior_treatments": [],    # treatments that must have been received
                "excluded_prior_treatments": [],    # treatments that exclude participation
                "treatment_timing_restrictions": [], # timing requirements for previous treatments
                "stem_cell_transplant_history": []  # transplant-related requirements/restrictions
            },
            "medical_conditions": {
                "required_conditions": [],    # conditions required for entry
                "excluded_conditions": [],    # conditions that exclude entry
                "organ_function_requirements": [], # kidney, liver, heart function requirements
                "blood_test_requirements": []      # specific lab requirements
            },
            "infections_immunity": {
                "excluded_infections": [],        # HIV, Hepatitis B/C, active infections
                "vaccination_restrictions": [],   # live vaccine restrictions, etc.
                "immunosuppression_restrictions": [] # immunosuppressive medication restrictions
            },
            "reproductive_contraception": {
                "pregnancy_excluded": False,      # boolean
                "breastfeeding_excluded": False,  # boolean
                "contraception_required": False,  # boolean
                "contraception_duration": None    # e.g., "during treatment and 6 months after"
            },
            "other_restrictions": {
                "surgery_restrictions": [],       # recent surgery restrictions
                "medication_restrictions": [],    # prohibited medications
                "allergy_restrictions": [],       # drug allergies that exclude
                "substance_use_restrictions": []  # alcohol/drug use restrictions
            }
        }

        prompt = f"""
You are a medical AI specialized in extracting structured eligibility criteria from clinical trial text.
Extract eligibility information from the following clinical trial text and return ONLY valid JSON.

Trial Title: {trial_title}

Extract the following information based on EXACTLY what is mentioned in the text:

1. AGE: Look for "at least X years old", "between X and Y years", age ranges
2. PERFORMANCE STATUS: Look for ECOG (0-3), Karnofsky (≥60, ≥70), Lansky (pediatric), or general performance descriptions
3. GENETIC/BIOMARKERS: Look for specific mutations (JAK2, NPM1, FLT3, BCR-ABL, Philadelphia chromosome), biomarkers (CD33+, CD20+, PD-L1+), chromosomal changes
4. CANCER TYPES: Required cancer types vs excluded cancer types
5. PREVIOUS TREATMENTS: Required prior treatments, excluded treatments, timing restrictions, transplant history
6. MEDICAL CONDITIONS: Required conditions, excluded conditions, organ function requirements, blood test requirements
7. INFECTIONS: HIV, Hepatitis B/C, active infections, vaccination restrictions, immunosuppression
8. REPRODUCTIVE: Pregnancy exclusion, breastfeeding exclusion, contraception requirements
9. OTHER: Surgery restrictions, medication restrictions, allergies, substance use

Return this EXACT JSON structure (no extra text):
{{
  "age_criteria": {{
    "min_age": null,
    "max_age": null,
    "age_restrictions": []
  }},
  "performance_status": {{
    "ecog_status": [],
    "karnofsky_status": [],
    "lansky_status": [],
    "general_status": []
  }},
  "genetic_biomarkers": {{
    "required_mutations": [],
    "excluded_mutations": [],
    "required_biomarkers": [],
    "chromosomal_changes": []
  }},
  "cancer_specifics": {{
    "required_cancer_types": [],
    "excluded_cancer_types": [],
    "disease_stage_requirements": [],
    "remission_status": []
  }},
  "previous_treatments": {{
    "required_prior_treatments": [],
    "excluded_prior_treatments": [],
    "treatment_timing_restrictions": [],
    "stem_cell_transplant_history": []
  }},
  "medical_conditions": {{
    "required_conditions": [],
    "excluded_conditions": [],
    "organ_function_requirements": [],
    "blood_test_requirements": []
  }},
  "infections_immunity": {{
    "excluded_infections": [],
    "vaccination_restrictions": [],
    "immunosuppression_restrictions": []
  }},
  "reproductive_contraception": {{
    "pregnancy_excluded": false,
    "breastfeeding_excluded": false,
    "contraception_required": false,
    "contraception_duration": null
  }},
  "other_restrictions": {{
    "surgery_restrictions": [],
    "medication_restrictions": [],
    "allergy_restrictions": [],
    "substance_use_restrictions": []
  }}
}}

Clinical Trial Eligibility Text:
{who_can_enter_text}
"""

        async with self.semaphore:
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a medical AI that extracts structured eligibility criteria from clinical trial text. Return only valid JSON with no additional commentary."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.0
                )
                
                raw_content = response.choices[0].message.content.strip()
                
                # Remove any markdown formatting
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3]
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3]
                
                parsed_data = json.loads(raw_content)
                
                # Ensure all required fields exist
                for key, default_val in required_json_structure.items():
                    if key not in parsed_data:
                        parsed_data[key] = default_val
                    elif isinstance(default_val, dict):
                        for sub_key, sub_val in default_val.items():
                            if sub_key not in parsed_data[key]:
                                parsed_data[key][sub_key] = sub_val
                
                return parsed_data
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error for trial '{trial_title}': {str(e)}")
                return {}
            except Exception as e:
                print(f"❌ Error processing trial '{trial_title}': {str(e)}")
                return {}
    
    async def process_clinical_trials(self, input_file: str, output_file: str) -> None:
        """
        Process all clinical trials and add structured eligibility criteria
        """
        print(f"📁 Loading clinical trials from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            trials_data = json.load(f)
        
        # Extract trials array from the combined file structure
        if 'trials' in trials_data:
            trials = trials_data['trials']
            metadata = trials_data.get('metadata', {})
            dataset_info = metadata.get('dataset_info', {})
            sources = dataset_info.get('sources', {})
            cruk_count = sources.get('cruk', {}).get('trial_count', 0)
            nihr_count = sources.get('nihr', {}).get('trial_count', 0)
            print(f"🏥 Found {len(trials)} clinical trials from combined dataset ({cruk_count} CRUK + {nihr_count} NIHR)")
        else:
            # Fallback for old format
            trials = trials_data
            print(f"🏥 Found {len(trials)} clinical trials from legacy format")
        
        # Filter trials that have eligibility text
        trials_with_eligibility = [
            (i, trial) for i, trial in enumerate(trials) 
            if 'who_can_enter' in trial and trial['who_can_enter'] and trial['who_can_enter'].strip()
        ]
        
        print(f"📋 {len(trials_with_eligibility)} trials have eligibility criteria to process")
        
        # Create extraction tasks
        tasks = []
        for i, trial in trials_with_eligibility:
            task = self.extract_eligibility_criteria(
                trial['who_can_enter'], 
                trial.get('title', f'Trial {i+1}')
            )
            tasks.append((i, task))
        
        processed_count = 0
        batch_size = 10
        
        print(f"🚀 Processing in batches of {batch_size}...")
        
        # Process in batches
        for batch_start in range(0, len(tasks), batch_size):
            batch_tasks = tasks[batch_start:batch_start + batch_size]
            batch_num = batch_start // batch_size + 1
            total_batches = (len(tasks) + batch_size - 1) // batch_size
            
            print(f"⏳ Processing batch {batch_num}/{total_batches}...")
            
            # Execute batch
            batch_results = await asyncio.gather(*[task for _, task in batch_tasks])
            
            # Update trials with results
            for (trial_idx, _), result in zip(batch_tasks, batch_results):
                trials[trial_idx]['structured_eligibility'] = result
                processed_count += 1
                
                # Add metadata
                trials[trial_idx]['eligibility_extraction_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'extraction_success': bool(result),
                    'extractor_version': '1.0'
                }
            
            print(f"✅ Completed {processed_count}/{len(tasks)} extractions")
        
        # Save results
        print(f"💾 Saving results to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(trials, f, indent=2, ensure_ascii=False)
        
        print(f"🎉 Successfully processed {processed_count} trials!")
        print(f"📊 Results saved to: {output_file}")


async def main():
    """Main function to run the eligibility extraction"""
    
    # Configuration
    INPUT_FILE = "trials-aggregator/combined_clinical_trials.json"
    OUTPUT_FILE = "trials-aggregator/clinical_trials_with_structured_eligibility.json"
    
    print("🔬 Blood Cancer Clinical Trials Eligibility Extractor")
    print("=" * 60)
    
    # Create extractor (uses st.secrets for API key)
    extractor = EligibilityExtractor(max_concurrent_requests=10)
    
    # Process trials
    await extractor.process_clinical_trials(INPUT_FILE, OUTPUT_FILE)
    
    print("=" * 60)
    print("🏁 Processing complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 