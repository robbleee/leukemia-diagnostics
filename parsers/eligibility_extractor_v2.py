import asyncio
import json
import os
import streamlit as st
from openai import AsyncOpenAI
from datetime import datetime

class EligibilityExtractorV2:
    def __init__(self, max_concurrent_requests: int = 10):
        self.client = AsyncOpenAI(api_key=st.secrets["openai"]["api_key"])
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def extract_eligibility_criteria(self, who_can_enter_text: str, trial_title: str) -> dict:
        """
        Extract decisive, programmatically matchable eligibility criteria
        """
        if not who_can_enter_text.strip():
            return {}
        
        # Define the structured format for programmatic matching
        required_json_structure = {
            "age": {
                "min_age": None,  # integer or null
                "max_age": None,  # integer or null
                "age_units": "years"  # always years for consistency
            },
            "performance_status": {
                "ecog_min": None,  # integer 0-4 or null
                "ecog_max": None,  # integer 0-4 or null
                "karnofsky_min": None,  # integer 0-100 or null
                "lansky_min": None  # integer 0-100 or null (pediatric)
            },
            "genetic_markers": {
                "required_positive": [],  # list of gene names that must be positive/mutated
                "required_negative": [],  # list of gene names that must be negative/wild-type
                "chromosomal_abnormalities": {
                    "required": [],  # e.g., ["del(5q)", "t(9;22)", "+8"]
                    "excluded": []   # chromosomal changes that exclude patient
                }
            },
            "biomarkers": {
                "cd_markers": {
                    "cd20_positive": None,  # true/false/null
                    "cd33_positive": None,  # true/false/null
                    "cd19_positive": None,  # true/false/null
                    "other_required": []    # list of other CD markers required
                },
                "protein_markers": {
                    "pd_l1_positive": None,  # true/false/null
                    "bcr_abl_positive": None,  # true/false/null
                    "philadelphia_positive": None  # true/false/null
                }
            },
            "cancer_diagnosis": {
                "required_diagnoses": [],  # exact cancer type names required
                "excluded_diagnoses": [],  # cancer types that exclude
                "disease_stage": {
                    "min_stage": None,  # e.g., "1", "2", "3", "4"
                    "max_stage": None,
                    "specific_stages": []  # list of allowed stages
                },
                "disease_status": {
                    "newly_diagnosed": None,  # true/false/null
                    "relapsed": None,         # true/false/null
                    "refractory": None,       # true/false/null
                    "in_remission": None      # true/false/null
                }
            },
            "prior_treatments": {
                "chemotherapy": {
                    "required": None,         # true/false/null
                    "min_prior_regimens": None,  # integer or null
                    "max_prior_regimens": None,  # integer or null
                    "specific_required": [],     # list of specific chemo regimens required
                    "specific_excluded": []      # list of specific chemo regimens excluded
                },
                "targeted_therapy": {
                    "required": None,         # true/false/null
                    "specific_required": [],  # list of specific targeted drugs required
                    "specific_excluded": []   # list of specific targeted drugs excluded
                },
                "immunotherapy": {
                    "required": None,         # true/false/null
                    "specific_required": [],  # list of specific immunotherapies required
                    "specific_excluded": []   # list of specific immunotherapies excluded
                },
                "stem_cell_transplant": {
                    "autologous_required": None,    # true/false/null
                    "allogeneic_required": None,    # true/false/null
                    "autologous_excluded": None,    # true/false/null
                    "allogeneic_excluded": None,    # true/false/null
                    "time_since_transplant_min_days": None,  # minimum days since transplant
                    "time_since_transplant_max_days": None   # maximum days since transplant
                },
                "radiation": {
                    "required": None,         # true/false/null
                    "excluded": None,         # true/false/null
                    "time_restrictions_days": None  # minimum days since radiation
                }
            },
            "laboratory_values": {
                "blood_counts": {
                    "hemoglobin_min_g_dl": None,     # minimum hemoglobin in g/dL
                    "platelet_min_k_ul": None,       # minimum platelets in K/μL
                    "neutrophil_min_k_ul": None,     # minimum neutrophils in K/μL
                    "white_cell_min_k_ul": None,     # minimum WBC in K/μL
                    "white_cell_max_k_ul": None      # maximum WBC in K/μL
                },
                "organ_function": {
                    "creatinine_max_mg_dl": None,    # maximum creatinine in mg/dL
                    "bilirubin_max_mg_dl": None,     # maximum bilirubin in mg/dL
                    "alt_max_times_uln": None,       # maximum ALT as times upper limit normal
                    "ast_max_times_uln": None        # maximum AST as times upper limit normal
                },
                "other_labs": {
                    "ldh_max_times_uln": None,       # maximum LDH as times ULN
                    "beta2_microglobulin_max": None  # maximum beta-2 microglobulin
                }
            },
            "medical_conditions": {
                "cardiac": {
                    "ejection_fraction_min": None,   # minimum LVEF percentage
                    "recent_mi_excluded_days": None, # exclude if MI within X days
                    "heart_failure_excluded": None   # true/false/null
                },
                "infections": {
                    "hiv_excluded": None,            # true/false/null
                    "hepatitis_b_excluded": None,    # true/false/null
                    "hepatitis_c_excluded": None,    # true/false/null
                    "active_infection_excluded": None # true/false/null
                },
                "other_cancers": {
                    "excluded": None,                # true/false/null
                    "time_since_other_cancer_min_years": None  # minimum years since other cancer
                }
            },
            "reproductive": {
                "pregnancy_excluded": None,          # true/false/null
                "breastfeeding_excluded": None,      # true/false/null
                "contraception_required": None       # true/false/null
            },
            "logistics": {
                "inpatient_required": None,          # true/false/null
                "frequent_visits_required": None     # true/false/null (>2x per week)
            }
        }

        prompt = f"""
You are a medical AI that extracts DECISIVE, PROGRAMMATICALLY MATCHABLE eligibility criteria from clinical trial text.

CRITICAL INSTRUCTIONS:
1. Extract ONLY specific, measurable criteria that can be programmatically matched against patient data
2. Use EXACT numbers when mentioned (ages, lab values, time periods)
3. Convert all time periods to consistent units (days for short periods, years for long periods)
4. Use standardized gene names (e.g., "TP53", "JAK2", "FLT3")
5. Use standardized cancer names (e.g., "acute myeloid leukemia", "chronic lymphocytic leukemia")
6. Set boolean values to true/false ONLY when explicitly stated, otherwise null
7. Extract numeric ranges precisely (min/max values)
8. Return ONLY the JSON structure below with NO additional text

EXAMPLES OF DECISIVE CRITERIA:
- "at least 18 years old" → min_age: 18
- "ECOG 0-2" → ecog_min: 0, ecog_max: 2
- "CD20 positive" → cd20_positive: true
- "no prior chemotherapy" → chemotherapy.required: false
- "hemoglobin ≥8 g/dL" → hemoglobin_min_g_dl: 8.0
- "within 6 months of transplant" → time_since_transplant_max_days: 180

Return this EXACT JSON structure:
{json.dumps(required_json_structure, indent=2)}

Clinical Trial Eligibility Text:
{who_can_enter_text}
"""

        async with self.semaphore:
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a medical AI that extracts precise, programmatically matchable eligibility criteria. Return only valid JSON with exact numeric values and standardized terms."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2500,
                    temperature=0.0
                )
                
                raw_content = response.choices[0].message.content.strip()
                
                # Remove any markdown formatting
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3]
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3]
                
                parsed_data = json.loads(raw_content)
                
                # Ensure all required fields exist with proper structure
                def ensure_structure(data, template):
                    if isinstance(template, dict):
                        if not isinstance(data, dict):
                            data = {}
                        for key, default_val in template.items():
                            if key not in data:
                                data[key] = default_val
                            else:
                                data[key] = ensure_structure(data[key], default_val)
                    elif isinstance(template, list):
                        if not isinstance(data, list):
                            data = []
                    return data
                
                parsed_data = ensure_structure(parsed_data, required_json_structure)
                
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
            trials = json.load(f)
        
        print(f"🏥 Found {len(trials)} clinical trials")
        
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
                trials[trial_idx]['structured_eligibility_v2'] = result
                processed_count += 1
                
                # Add metadata
                trials[trial_idx]['eligibility_extraction_v2_metadata'] = {
                    'processed_at': datetime.now().isoformat(),
                    'extraction_success': bool(result),
                    'extractor_version': '2.0'
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
    INPUT_FILE = "trials-aggregator/clinical_trials.json"
    OUTPUT_FILE = "trials-aggregator/clinical_trials_with_structured_eligibility_v2.json"
    
    print("🔬 Blood Cancer Clinical Trials Eligibility Extractor V2")
    print("🎯 Focus: Decisive, Programmatically Matchable Criteria")
    print("=" * 70)
    
    # Create extractor (uses st.secrets for API key)
    extractor = EligibilityExtractorV2(max_concurrent_requests=10)
    
    # Process trials
    await extractor.process_clinical_trials(INPUT_FILE, OUTPUT_FILE)
    
    print("=" * 70)
    print("🏁 Processing complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 