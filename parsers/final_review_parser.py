import streamlit as st
import json
from openai import OpenAI

##############################
# OPENAI API CONFIG
##############################
client = OpenAI(api_key=st.secrets["openai"]["api_key"])


##############################
# GENERATE FINAL REVIEW OVERVIEW
##############################
def generate_final_overview(parsed_data: dict, original_report_text: str = "") -> str:
    """
    Generates a comprehensive clinical overview of all the parsed information and results using AI.
    This creates a detailed 5-sentence summary that will appear at the top of the report.
    
    Args:
        parsed_data (dict): The complete parsed data structure from the genetics report
        original_report_text (str): Optional original report text for additional context
        
    Returns:
        str: A comprehensive clinical overview paragraph (5 sentences)
    """
    if not parsed_data:
        return "No parsed data available for overview generation."
    
    # Gather all available information from session state
    comprehensive_data = {
        "parsed_data": parsed_data,
        "original_report": original_report_text[:1000] if original_report_text else "No original report provided"
    }
    
    # Add AML results if available
    aml_result = st.session_state.get("aml_manual_result") or st.session_state.get("aml_ai_result")
    if aml_result:
        comprehensive_data["aml_classifications"] = {
            "who_classification": aml_result.get("who_class", ""),
            "icc_classification": aml_result.get("icc_class", ""),
            "who_disease_type": aml_result.get("who_disease_type", ""),
            "icc_disease_type": aml_result.get("icc_disease_type", "")
        }
        
        # Add ELN risk if available
        try:
            from classifiers.aml_risk_classifier import classify_ELN2022
            risk_eln2022, median_os_eln2022, _ = classify_ELN2022(aml_result["parsed_data"])
            comprehensive_data["eln_risk"] = {
                "risk_category": risk_eln2022,
                "median_os": median_os_eln2022
            }
        except:
            pass
    
    # Add MDS results if available
    mds_result = st.session_state.get("mds_manual_result") or st.session_state.get("mds_ai_result")
    if mds_result:
        comprehensive_data["mds_classifications"] = {
            "who_classification": mds_result.get("who_class", ""),
            "icc_classification": mds_result.get("icc_class", ""),
            "who_disease_type": mds_result.get("who_disease_type", ""),
            "icc_disease_type": mds_result.get("icc_disease_type", "")
        }
        
        # Add IPSS risk if available
        if 'ipssm_result' in st.session_state:
            ipssm = st.session_state['ipssm_result']
            comprehensive_data["ipss_risk"] = {
                "ipssm_mean_risk": ipssm.get('means', {}).get('riskCat', ''),
                "ipssm_mean_score": ipssm.get('means', {}).get('riskScore', ''),
                "ipssr_risk": st.session_state.get('ipssr_result', {}).get('IPSSR_CAT', ''),
                "ipssr_score": st.session_state.get('ipssr_result', {}).get('IPSSR_SCORE', '')
            }
    
    # Add AI review comments if available
    ai_reviews = {}
    review_keys = [
        ("classification_review", "aml_class_review"),
        ("mrd_review", "aml_mrd_review"), 
        ("gene_review", "aml_gene_review"),
        ("additional_comments", "aml_additional_comments"),
        ("differentiation_review", "differentiation"),
        ("mds_classification_review", "mds_class_review"),
        ("mds_gene_review", "mds_gene_review"),
        ("mds_additional_comments", "mds_additional_comments")
    ]
    
    for review_type, session_key in review_keys:
        if session_key in st.session_state:
            ai_reviews[review_type] = st.session_state[session_key][:500]  # Limit length
    
    if ai_reviews:
        comprehensive_data["ai_reviews"] = ai_reviews
    
    # Convert the comprehensive data to a readable format for the AI
    data_summary = json.dumps(comprehensive_data, indent=2)
    
    # Build the enhanced prompt for generating the comprehensive overview
    prompt = f"""
    You are a specialized hematopathology AI assistant. Based on ALL the available clinical data, classifications, risk assessments, and AI reviews below, generate a comprehensive clinical overview that is exactly 5 sentences long.
    
    This overview should provide a complete clinical picture including:
    1. **Sentence 1**: Patient demographics and key laboratory findings (blast percentage, blood counts if available)
    2. **Sentence 2**: Primary genetic/molecular findings and their clinical significance
    3. **Sentence 3**: Final disease classification(s) according to WHO and/or ICC criteria
    4. **Sentence 4**: Risk stratification results (ELN for AML, IPSS for MDS) and prognostic implications
    5. **Sentence 5**: Key clinical considerations, treatment implications, or important caveats from the AI reviews
    
    **Requirements:**
    - Write EXACTLY 5 sentences, no more, no less
    - Use professional medical language suitable for a clinical report
    - Integrate information from classifications, risk assessments, and AI reviews
    - Focus on clinically actionable information
    - Mention specific genetic abnormalities, risk categories, and treatment considerations
    - Do NOT repeat the same information across sentences
    - Make each sentence substantive and informative
    
    **Complete Clinical Data:**
    {data_summary}
    
    **Instructions:**
    - Return ONLY the 5-sentence clinical overview (no JSON, no extra formatting, no bullet points)
    - Each sentence should flow naturally into the next
    - Ensure the overview tells a complete clinical story
    - Include specific details like gene names, risk categories, and percentages where relevant
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a specialized hematopathology AI that generates comprehensive 5-sentence clinical overviews for diagnostic reports."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,  # Increased for longer overview
            temperature=0.1  # Low temperature for consistent, factual output
        )
        
        overview_text = response.choices[0].message.content.strip()
        
        # Clean up any potential formatting issues
        overview_text = overview_text.replace('"', '').replace('\n\n', ' ').replace('\n', ' ')
        
        # Ensure it's not too long (but allow for longer comprehensive overview)
        if len(overview_text) > 1200:
            overview_text = overview_text[:1197] + "..."
            
        return overview_text
        
    except Exception as e:
        st.error(f"❌ Error generating comprehensive overview: {str(e)}")
        return "Error generating comprehensive clinical overview. Please review the parsed data and classification results manually."


##############################
# GENERATE SUMMARY STATISTICS
##############################
def generate_summary_stats(parsed_data: dict) -> dict:
    """
    Generates summary statistics about the parsed data for quick reference.
    
    Args:
        parsed_data (dict): The complete parsed data structure
        
    Returns:
        dict: Summary statistics including counts of positive findings
    """
    stats = {
        "total_genetic_abnormalities": 0,
        "aml_defining_abnormalities": 0,
        "mds_related_mutations": 0,
        "mds_related_cytogenetics": 0,
        "biallelic_tp53_conditions": 0,
        "qualifiers_present": 0,
        "blast_percentage": parsed_data.get("blasts_percentage", "Not specified")
    }
    
    # Count AML-defining abnormalities
    aml_def = parsed_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    stats["aml_defining_abnormalities"] = sum(1 for val in aml_def.values() if val)
    
    # Count MDS-related mutations
    mds_mut = parsed_data.get("MDS_related_mutation", {})
    stats["mds_related_mutations"] = sum(1 for val in mds_mut.values() if val)
    
    # Count MDS-related cytogenetics
    mds_cyto = parsed_data.get("MDS_related_cytogenetics", {})
    stats["mds_related_cytogenetics"] = sum(1 for val in mds_cyto.values() if val)
    
    # Count biallelic TP53 conditions
    tp53 = parsed_data.get("Biallelic_TP53_mutation", {})
    stats["biallelic_tp53_conditions"] = sum(1 for val in tp53.values() if val)
    
    # Count qualifiers
    qualifiers = parsed_data.get("qualifiers", {})
    stats["qualifiers_present"] = sum(1 for key, val in qualifiers.items() 
                                    if (isinstance(val, bool) and val) or 
                                       (isinstance(val, str) and val.strip() and val.lower() != "none"))
    
    # Total genetic abnormalities
    stats["total_genetic_abnormalities"] = (
        stats["aml_defining_abnormalities"] + 
        stats["mds_related_mutations"] + 
        stats["mds_related_cytogenetics"] + 
        stats["biallelic_tp53_conditions"]
    )
    
    return stats
