import asyncio
import json
import streamlit as st
from openai import AsyncOpenAI
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class ClinicalTrialMatcher:
    def __init__(self, max_concurrent_requests: int = 3):
        """Initialize the clinical trial matcher with OpenAI API"""
        self.client = AsyncOpenAI(api_key=st.secrets["openai"]["api_key"])
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        
    async def match_patient_to_trial_batch(self, patient_data: str, trial_batch: List[Dict]) -> List[Dict]:
        """
        Match a patient to a batch of 5 clinical trials using OpenAI API
        """
        async with self.semaphore:
            # Prepare the trial batch for the prompt
            trials_text = ""
            for i, trial in enumerate(trial_batch, 1):
                trials_text += f"""
TRIAL {i}:
Title: {trial.get('title', 'Unknown')}
Description: {trial.get('description', 'No description')}
Cancer Types: {trial.get('cancer_types', 'Unknown')}
Status: {trial.get('status', 'Unknown')}
Locations: {trial.get('locations', 'Unknown')}
Eligibility Criteria: {trial.get('who_can_enter', 'No criteria available')}

---
"""
            
            prompt = f"""
You are a clinical oncologist specializing in blood cancers. I will provide you with a patient's clinical data and 5 clinical trials. Your task is to evaluate which trials this patient might be eligible for and provide a relevance score.

PATIENT DATA:
{patient_data}

CLINICAL TRIALS TO EVALUATE:
{trials_text}

For each trial, please provide:
1. A relevance score from 0-100 (where 100 = perfect match, 0 = completely irrelevant)
2. A brief explanation of why the patient might or might not be eligible
3. Key matching factors (age, diagnosis, genetic markers, prior treatments, etc.)
4. Key exclusion factors (if any)

Please respond in the following JSON format:
{{
    "trial_1": {{
        "relevance_score": <0-100>,
        "explanation": "<brief explanation>",
        "matching_factors": ["<factor1>", "<factor2>"],
        "exclusion_factors": ["<factor1>", "<factor2>"],
        "recommendation": "<recommend/consider/not_suitable>"
    }},
    "trial_2": {{ ... }},
    "trial_3": {{ ... }},
    "trial_4": {{ ... }},
    "trial_5": {{ ... }}
}}

Focus on:
- Age eligibility
- Cancer type/subtype match
- Genetic/molecular markers (NPM1, FLT3, TP53, etc.)
- Disease status (newly diagnosed, relapsed, refractory)
- Prior treatments
- Performance status
- Comorbidities
- Geographic accessibility

Be conservative in your recommendations - only recommend trials where the patient clearly meets the major eligibility criteria.
"""

            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a clinical oncologist expert in blood cancer clinical trials. Provide accurate, conservative eligibility assessments."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                response_text = response.choices[0].message.content.strip()
                
                # Parse the JSON response
                try:
                    # Extract JSON from the response
                    if "```json" in response_text:
                        json_start = response_text.find("```json") + 7
                        json_end = response_text.find("```", json_start)
                        json_text = response_text[json_start:json_end].strip()
                    else:
                        json_text = response_text
                    
                    results = json.loads(json_text)
                    
                    # Combine results with trial data
                    matched_trials = []
                    for i, trial in enumerate(trial_batch, 1):
                        trial_key = f"trial_{i}"
                        if trial_key in results:
                            trial_result = results[trial_key]
                            matched_trial = {
                                **trial,  # Original trial data
                                "relevance_score": trial_result.get("relevance_score", 0),
                                "explanation": trial_result.get("explanation", "No explanation provided"),
                                "matching_factors": trial_result.get("matching_factors", []),
                                "exclusion_factors": trial_result.get("exclusion_factors", []),
                                "recommendation": trial_result.get("recommendation", "not_suitable")
                            }
                            matched_trials.append(matched_trial)
                    
                    return matched_trials
                    
                except json.JSONDecodeError as e:
                    st.error(f"Failed to parse OpenAI response as JSON: {e}")
                    return []
                    
            except Exception as e:
                st.error(f"Error calling OpenAI API: {e}")
                return []

    async def generate_detailed_recommendations(self, patient_data: str, top_trials: List[Dict]) -> List[Dict]:
        """
        Generate detailed recommendation explanations for the top matching trials
        """
        if not top_trials:
            return []
        
        # Prepare detailed trial information for the top trials
        trials_text = ""
        for i, trial in enumerate(top_trials, 1):
            trials_text += f"""
TRIAL {i}:
Title: {trial.get('title', 'Unknown')}
Description: {trial.get('description', 'No description')}
Cancer Types: {trial.get('cancer_types', 'Unknown')}
Eligibility Criteria: {trial.get('who_can_enter', 'No criteria provided')}
Current Relevance Score: {trial.get('relevance_score', 0)}
Current Matching Factors: {', '.join(trial.get('matching_factors', []))}
Locations: {trial.get('locations', 'Unknown')}

---
"""
        
        prompt = f"""
You are a senior clinical oncologist writing detailed recommendations for clinical trial enrollment. Based on the patient profile and the following clinical trials, provide comprehensive recommendation explanations.

PATIENT PROFILE:
{patient_data}

TOP MATCHING CLINICAL TRIALS:
{trials_text}

For each trial, provide a detailed recommendation explanation that includes:

1. **Clinical Rationale**: Why this trial is appropriate for this specific patient
2. **Molecular Match**: How the patient's genetic/molecular profile aligns with the trial
3. **Risk-Benefit Assessment**: Potential benefits vs risks for this patient
4. **Practical Considerations**: Logistics, location, timing considerations
5. **Alternative Options**: How this compares to standard care or other trials

Please respond in JSON format:
{{
    "trial_1": {{
        "detailed_recommendation": "<comprehensive 3-4 paragraph explanation>",
        "key_strengths": ["<strength1>", "<strength2>", "<strength3>"],
        "potential_concerns": ["<concern1>", "<concern2>"],
        "next_steps": "<what should happen next>",
        "priority_level": "<high/medium/low>"
    }},
    "trial_2": {{ ... }},
    etc.
}}

Write as if you're explaining to both the patient and their oncologist. Be thorough but accessible. Include specific medical reasoning while remaining understandable.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a senior clinical oncologist providing detailed, thoughtful clinical trial recommendations. Write comprehensive but accessible explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_text = response_text[json_start:json_end].strip()
                else:
                    json_text = response_text
                
                detailed_results = json.loads(json_text)
                
                # Enhance the trials with detailed recommendations
                enhanced_trials = []
                for i, trial in enumerate(top_trials, 1):
                    trial_key = f"trial_{i}"
                    if trial_key in detailed_results:
                        detail = detailed_results[trial_key]
                        enhanced_trial = {
                            **trial,  # Original trial data
                            "detailed_recommendation": detail.get("detailed_recommendation", ""),
                            "key_strengths": detail.get("key_strengths", []),
                            "potential_concerns": detail.get("potential_concerns", []),
                            "next_steps": detail.get("next_steps", ""),
                            "priority_level": detail.get("priority_level", "medium")
                        }
                        enhanced_trials.append(enhanced_trial)
                    else:
                        enhanced_trials.append(trial)
                
                return enhanced_trials
                
            except json.JSONDecodeError as e:
                st.warning(f"Could not parse detailed recommendations: {e}")
                return top_trials
                
        except Exception as e:
            st.warning(f"Error generating detailed recommendations: {e}")
            return top_trials
    
    async def find_matching_trials(self, patient_data: str, trials_file: str = "trials-aggregator/clinical_trials.json") -> List[Dict]:
        """
        Find matching clinical trials for a patient by processing in batches
        """
        # Load clinical trials
        try:
            with open(trials_file, 'r', encoding='utf-8') as f:
                all_trials = json.load(f)
        except Exception as e:
            st.error(f"Failed to load clinical trials: {e}")
            return []
        
        # Filter to only open trials
        open_trials = [trial for trial in all_trials if trial.get('status', '').lower() == 'open']
        
        # Process trials in batches of 5
        batch_size = 5
        all_matched_trials = []
        
        # Create batches
        trial_batches = [open_trials[i:i + batch_size] for i in range(0, len(open_trials), batch_size)]
        
        # Process batches concurrently (but limited by semaphore)
        tasks = []
        for batch in trial_batches:
            if len(batch) > 0:  # Only process non-empty batches
                task = self.match_patient_to_trial_batch(patient_data, batch)
                tasks.append(task)
        
        # Execute all tasks
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results
        for result in batch_results:
            if isinstance(result, list):
                all_matched_trials.extend(result)
            elif isinstance(result, Exception):
                st.warning(f"Error processing batch: {result}")
        
        # Sort by relevance score (highest first)
        all_matched_trials.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Generate detailed recommendations for top trials (score >= 60)
        top_trials = [t for t in all_matched_trials if t.get('relevance_score', 0) >= 60][:5]  # Top 5 high-scoring trials
        
        if top_trials:
            st.info("Generating detailed recommendations for top matching trials...")
            enhanced_top_trials = await self.generate_detailed_recommendations(patient_data, top_trials)
            
            # Replace the top trials with enhanced versions
            enhanced_trials = []
            top_trial_titles = {t.get('title', '') for t in top_trials}
            
            for trial in all_matched_trials:
                if trial.get('title', '') in top_trial_titles:
                    # Find the enhanced version
                    enhanced_version = next((et for et in enhanced_top_trials if et.get('title') == trial.get('title')), trial)
                    enhanced_trials.append(enhanced_version)
                else:
                    enhanced_trials.append(trial)
            
            return enhanced_trials
        
        return all_matched_trials

def format_patient_data_for_matching(parsed_data: Dict, free_text_input: str = None, additional_info: Dict = None) -> str:
    """
    Format patient data into a comprehensive text description for trial matching
    """
    patient_description = "PATIENT CLINICAL PROFILE:\n\n"
    
    # Basic demographics
    age = additional_info.get('age') if additional_info else None
    if not age and 'age' in parsed_data:
        try:
            age = int(parsed_data['age'])
        except (ValueError, TypeError):
            age = None
    
    if age:
        patient_description += f"Age: {age} years\n"
    
    # Performance status
    if additional_info and 'ecog_status' in additional_info:
        patient_description += f"ECOG Performance Status: {additional_info['ecog_status']}\n"
    
    # Primary diagnosis
    diagnosis = additional_info.get('primary_diagnosis') if additional_info else "Blood cancer"
    patient_description += f"Primary Diagnosis: {diagnosis}\n"
    
    # Disease status
    if additional_info:
        if additional_info.get('newly_diagnosed'):
            patient_description += "Disease Status: Newly diagnosed\n"
        elif additional_info.get('relapsed'):
            patient_description += "Disease Status: Relapsed\n"
        elif additional_info.get('refractory'):
            patient_description += "Disease Status: Refractory\n"
        elif additional_info.get('in_remission'):
            patient_description += "Disease Status: In remission\n"
    
    # Genetic/molecular markers
    patient_description += "\nGENETIC/MOLECULAR PROFILE:\n"
    
    # Blast percentage
    if parsed_data.get('blasts_percentage') is not None:
        patient_description += f"Blast percentage: {parsed_data['blasts_percentage']}%\n"
    
    # AML-defining abnormalities
    aml_abnormalities = parsed_data.get('AML_defining_recurrent_genetic_abnormalities', {})
    positive_aml_genes = [gene for gene, positive in aml_abnormalities.items() if positive]
    if positive_aml_genes:
        patient_description += f"AML-defining genetic abnormalities: {', '.join(positive_aml_genes)}\n"
    
    # MDS-related mutations
    mds_mutations = parsed_data.get('MDS_related_mutation', {})
    positive_mds_genes = [gene for gene, positive in mds_mutations.items() if positive]
    if positive_mds_genes:
        patient_description += f"MDS-related mutations: {', '.join(positive_mds_genes)}\n"
    
    # ELN2024 risk genes
    eln_genes = parsed_data.get('ELN2024_risk_genes', {})
    positive_eln_genes = [gene for gene, positive in eln_genes.items() if positive]
    if positive_eln_genes:
        patient_description += f"ELN2024 risk genes: {', '.join(positive_eln_genes)}\n"
    
    # TP53 status
    tp53_status = parsed_data.get('Biallelic_TP53_mutation', {})
    if any(tp53_status.values()):
        tp53_features = [feature for feature, positive in tp53_status.items() if positive]
        patient_description += f"TP53 mutations: {', '.join(tp53_features)}\n"
    
    # Cytogenetics
    cytogenetics = parsed_data.get('MDS_related_cytogenetics', {})
    positive_cyto = [abnormality for abnormality, positive in cytogenetics.items() if positive]
    if positive_cyto:
        patient_description += f"Cytogenetic abnormalities: {', '.join(positive_cyto)}\n"
    
    # AML differentiation
    if parsed_data.get('AML_differentiation'):
        patient_description += f"AML differentiation: {parsed_data['AML_differentiation']}\n"
    
    # Disease history
    qualifiers = parsed_data.get('qualifiers', {})
    if qualifiers.get('previous_MDS_diagnosed_over_3_months_ago'):
        patient_description += "Previous MDS diagnosis >3 months ago\n"
    if qualifiers.get('previous_cytotoxic_therapy'):
        patient_description += f"Previous cytotoxic therapy: {qualifiers['previous_cytotoxic_therapy']}\n"
    
    # Prior treatments
    if additional_info:
        if additional_info.get('prior_chemotherapy_regimens', 0) > 0:
            patient_description += f"\nPRIOR TREATMENTS:\n"
            patient_description += f"Prior chemotherapy regimens: {additional_info['prior_chemotherapy_regimens']}\n"
        
        if additional_info.get('prior_targeted_therapies'):
            patient_description += f"Prior targeted therapies: {', '.join(additional_info['prior_targeted_therapies'])}\n"
        
        if additional_info.get('autologous_transplant_date'):
            patient_description += f"Prior autologous transplant: {additional_info['autologous_transplant_date']}\n"
        
        if additional_info.get('allogeneic_transplant_date'):
            patient_description += f"Prior allogeneic transplant: {additional_info['allogeneic_transplant_date']}\n"
    
    # Laboratory values
    if additional_info:
        patient_description += "\nLABORATORY VALUES:\n"
        lab_values = ['hemoglobin_g_dl', 'platelet_count_k_ul', 'neutrophil_count_k_ul', 
                     'white_cell_count_k_ul', 'creatinine_mg_dl', 'bilirubin_mg_dl']
        
        for lab in lab_values:
            if additional_info.get(lab) is not None:
                patient_description += f"{lab.replace('_', ' ').title()}: {additional_info[lab]}\n"
    
    # Medical conditions
    if additional_info:
        patient_description += "\nMEDICAL CONDITIONS:\n"
        conditions = []
        if additional_info.get('hiv_positive'):
            conditions.append("HIV positive")
        if additional_info.get('hepatitis_b_positive'):
            conditions.append("Hepatitis B positive")
        if additional_info.get('hepatitis_c_positive'):
            conditions.append("Hepatitis C positive")
        if additional_info.get('heart_failure'):
            conditions.append("Heart failure")
        if additional_info.get('active_infection'):
            conditions.append("Active infection")
        if additional_info.get('other_cancers'):
            conditions.append("Other cancers")
        
        if conditions:
            patient_description += f"Comorbidities: {', '.join(conditions)}\n"
        else:
            patient_description += "No significant comorbidities reported\n"
    
    # Reproductive status
    if additional_info:
        if additional_info.get('pregnant'):
            patient_description += "Pregnant: Yes\n"
        if additional_info.get('breastfeeding'):
            patient_description += "Breastfeeding: Yes\n"
    
    # Add original free text if available
    if free_text_input and free_text_input.strip():
        patient_description += f"\nORIGINAL CLINICAL REPORT:\n{free_text_input}\n"
    
    return patient_description

def run_clinical_trial_matching(patient_data: str) -> List[Dict]:
    """
    Synchronous wrapper for the async clinical trial matching
    """
    matcher = ClinicalTrialMatcher()
    
    # Run the async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        results = loop.run_until_complete(matcher.find_matching_trials(patient_data))
        return results
    finally:
        loop.close()

def display_trial_matches(matched_trials: List[Dict]):
    """
    Display the matched clinical trials in a user-friendly format
    """
    if not matched_trials:
        st.warning("No clinical trials found matching the patient criteria.")
        return
    
    # Filter trials by recommendation level
    recommended_trials = [t for t in matched_trials if t.get('recommendation') == 'recommend' and t.get('relevance_score', 0) >= 70]
    consider_trials = [t for t in matched_trials if t.get('recommendation') == 'consider' and t.get('relevance_score', 0) >= 40]
    
    # Display statistics
    st.markdown("### Clinical Trial Matching Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Highly Recommended", len(recommended_trials), help="Score ≥70")
    with col2:
        st.metric("Consider", len(consider_trials), help="Score 40-69")
    with col3:
        st.metric("Total Evaluated", len(matched_trials))
    
    # Display highly recommended trials with detailed recommendations
    if recommended_trials:
        st.markdown("### Highly Recommended Trials")
        for i, trial in enumerate(recommended_trials, 1):
            score = trial.get('relevance_score', 0)
            title = trial.get('title', 'Unknown Trial')
            with st.expander(f"{title} (Score: {score})", expanded=i<=2):
                display_single_trial_with_details(trial)
    
    # Display trials to consider
    if consider_trials:
        st.markdown("### Trials to Consider")
        for trial in consider_trials[:5]:  # Limit to top 5
            score = trial.get('relevance_score', 0)
            title = trial.get('title', 'Unknown Trial')
            with st.expander(f"{title} (Score: {score})"):
                display_single_trial(trial)
    
    # Show all results in a table
    if st.checkbox("Show all trial results", value=False):
        st.markdown("### All Trial Results")
        
        # Create a summary table
        trial_data = []
        for trial in matched_trials:
            trial_data.append({
                "Title": trial.get('title', 'Unknown')[:60] + "..." if len(trial.get('title', '')) > 60 else trial.get('title', 'Unknown'),
                "Score": trial.get('relevance_score', 0),
                "Recommendation": trial.get('recommendation', 'unknown'),
                "Cancer Types": trial.get('cancer_types', 'Unknown'),
                "Locations": trial.get('locations', 'Unknown')[:50] + "..." if len(trial.get('locations', '')) > 50 else trial.get('locations', 'Unknown')
            })
        
        if trial_data:
            import pandas as pd
            df = pd.DataFrame(trial_data)
            st.dataframe(df, use_container_width=True)

def display_single_trial_with_details(trial: Dict):
    """
    Display details for a single clinical trial with enhanced recommendations
    """
    # Basic trial information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Description:** {trial.get('description', 'No description available')}")
        st.markdown(f"**Cancer Types:** {trial.get('cancer_types', 'Unknown')}")
        st.markdown(f"**Status:** {trial.get('status', 'Unknown')}")
        
    with col2:
        # Score and priority information
        score = trial.get('relevance_score', 0)
        priority = trial.get('priority_level', 'medium')
        recommendation = trial.get('recommendation', 'unknown').title()
        
        # Score color coding
        if score >= 80:
            score_color = "#28a745"  # Green
        elif score >= 60:
            score_color = "#ffc107"  # Yellow
        elif score >= 40:
            score_color = "#fd7e14"  # Orange
        else:
            score_color = "#dc3545"  # Red
        
        st.markdown(f"**Relevance Score:** <span style='color: {score_color}; font-weight: bold;'>{score}/100</span>", unsafe_allow_html=True)
        st.markdown(f"**Priority Level:** {priority.title()}")
        st.markdown(f"**Recommendation:** {recommendation}")
    
    # Detailed recommendation (if available)
    detailed_rec = trial.get('detailed_recommendation', '')
    if detailed_rec:
        st.markdown("---")
        st.markdown("#### Detailed Clinical Recommendation")
        st.markdown(detailed_rec)
        
        # Create two columns for strengths and concerns
        col_left, col_right = st.columns(2)
        
        with col_left:
            # Key strengths
            strengths = trial.get('key_strengths', [])
            if strengths:
                st.markdown("**Key Strengths:**")
                for strength in strengths:
                    st.markdown(f"• {strength}")
        
        with col_right:
            # Potential concerns
            concerns = trial.get('potential_concerns', [])
            if concerns:
                st.markdown("**Potential Concerns:**")
                for concern in concerns:
                    st.markdown(f"• {concern}")
        
        # Next steps
        next_steps = trial.get('next_steps', '')
        if next_steps:
            st.markdown("**Recommended Next Steps:**")
            st.markdown(next_steps)
    
    # Standard matching factors and exclusions
    matching_factors = trial.get('matching_factors', [])
    exclusion_factors = trial.get('exclusion_factors', [])
    
    if matching_factors or exclusion_factors:
        st.markdown("---")
        
        # Create columns for matching and exclusion factors
        if matching_factors and exclusion_factors:
            col_match, col_exclude = st.columns(2)
            
            with col_match:
                if matching_factors:
                    st.markdown("**Matching Factors:**")
                    for factor in matching_factors:
                        st.markdown(f"• {factor}")
            
            with col_exclude:
                if exclusion_factors:
                    st.markdown("**Potential Exclusion Factors:**")
                    for factor in exclusion_factors:
                        st.markdown(f"• {factor}")
        else:
            # Single column if only one type
            if matching_factors:
                st.markdown("**Matching Factors:**")
                for factor in matching_factors:
                    st.markdown(f"• {factor}")
            
            if exclusion_factors:
                st.markdown("**Potential Exclusion Factors:**")
                for factor in exclusion_factors:
                    st.markdown(f"• {factor}")
    
    # AI explanation (basic)
    explanation = trial.get('explanation', '')
    if explanation and not detailed_rec:  # Only show if no detailed recommendation
        st.markdown("---")
        st.markdown("**AI Assessment:**")
        st.markdown(explanation)
    
    # Trial details
    st.markdown("---")
    st.markdown("#### Trial Information")
    
    # Create columns for trial details
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("**Locations:**")
        st.markdown(trial.get('locations', 'Unknown'))
        
        # Contact information
        if trial.get('contact_phone'):
            st.markdown(f"**Contact:** {trial['contact_phone']}")
    
    with detail_col2:
        # Recruitment dates
        if trial.get('recruitment_start') or trial.get('recruitment_end'):
            st.markdown("**Recruitment Period:**")
            start_date = trial.get('recruitment_start', 'Unknown')
            end_date = trial.get('recruitment_end', 'Unknown')
            st.markdown(f"From {start_date} to {end_date}")
        
        # Link to trial
        if trial.get('link'):
            st.markdown(f"**More Information:** [View Trial Details]({trial['link']})")

def display_single_trial(trial: Dict):
    """
    Display details for a single clinical trial (standard version)
    """
    # Basic trial information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"**Description:** {trial.get('description', 'No description available')}")
        st.markdown(f"**Cancer Types:** {trial.get('cancer_types', 'Unknown')}")
        st.markdown(f"**Status:** {trial.get('status', 'Unknown')}")
        
    with col2:
        # Score and recommendation
        score = trial.get('relevance_score', 0)
        recommendation = trial.get('recommendation', 'unknown').title()
        
        # Score color coding
        if score >= 80:
            score_color = "#28a745"  # Green
        elif score >= 60:
            score_color = "#ffc107"  # Yellow
        elif score >= 40:
            score_color = "#fd7e14"  # Orange
        else:
            score_color = "#dc3545"  # Red
        
        st.markdown(f"**Relevance Score:** <span style='color: {score_color}; font-weight: bold;'>{score}/100</span>", unsafe_allow_html=True)
        st.markdown(f"**Recommendation:** {recommendation}")
    
    # Matching factors and exclusions
    matching_factors = trial.get('matching_factors', [])
    exclusion_factors = trial.get('exclusion_factors', [])
    
    if matching_factors or exclusion_factors:
        st.markdown("---")
        
        # Create columns for matching and exclusion factors
        if matching_factors and exclusion_factors:
            col_match, col_exclude = st.columns(2)
            
            with col_match:
                if matching_factors:
                    st.markdown("**Matching Factors:**")
                    for factor in matching_factors:
                        st.markdown(f"• {factor}")
            
            with col_exclude:
                if exclusion_factors:
                    st.markdown("**Potential Exclusion Factors:**")
                    for factor in exclusion_factors:
                        st.markdown(f"• {factor}")
        else:
            # Single column if only one type
            if matching_factors:
                st.markdown("**Matching Factors:**")
                for factor in matching_factors:
                    st.markdown(f"• {factor}")
            
            if exclusion_factors:
                st.markdown("**Potential Exclusion Factors:**")
                for factor in exclusion_factors:
                    st.markdown(f"• {factor}")
    
    # AI explanation
    explanation = trial.get('explanation', '')
    if explanation:
        st.markdown("---")
        st.markdown("**AI Assessment:**")
        st.markdown(explanation)
    
    # Trial details
    st.markdown("---")
    st.markdown("#### Trial Information")
    
    # Create columns for trial details
    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("**Locations:**")
        st.markdown(trial.get('locations', 'Unknown'))
        
        # Contact information
        if trial.get('contact_phone'):
            st.markdown(f"**Contact:** {trial['contact_phone']}")
    
    with detail_col2:
        # Recruitment dates
        if trial.get('recruitment_start') or trial.get('recruitment_end'):
            st.markdown("**Recruitment Period:**")
            start_date = trial.get('recruitment_start', 'Unknown')
            end_date = trial.get('recruitment_end', 'Unknown')
            st.markdown(f"From {start_date} to {end_date}")
        
        # Link to trial
        if trial.get('link'):
            st.markdown(f"**More Information:** [View Trial Details]({trial['link']})")