"""
AML Treatment Recommendations Algorithm
Based on the consensus guideline approach by Tom Coats et al.

Citation: Coats T, Bean D, Basset A, Sirkis T, Brammeld J, Johnson S, et al. 
A novel algorithmic approach to generate consensus treatment guidelines in adult acute myeloid leukaemia. 
Br J Haematol. 2022;196:1337–1343. https://doi.org/10.1111/bjh.18013
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional


def determine_treatment_eligibility(patient_data: dict) -> List[str]:
    """
    Determine which treatments a patient is eligible for based on UK funding criteria.
    Based on the detailed eligibility rules from Coats et al.
    
    Args:
        patient_data (dict): Patient's parsed genetic and clinical data
        
    Returns:
        List[str]: List of eligible treatments
    """
    eligible_treatments = []
    
    # Always eligible treatments
    eligible_treatments.extend(["DA", "FLAG-IDA"])
    
    # DA+GO eligibility: De novo AML AND CD33 positive AND cytogenetic risk Favourable/Intermediate/Unknown
    is_de_novo = _is_de_novo_aml(patient_data)
    cd33_positive = _is_cd33_positive(patient_data)
    cyto_test_result = _get_cytogenetic_test_result(patient_data)
    
    if (is_de_novo and 
        cd33_positive and 
        cyto_test_result in ["Favourable", "Intermediate", "Unknown"]):
        eligible_treatments.append("DA+GO")
    
    # DA+Midostaurin eligibility: Newly diagnosed AND FLT3-mutation-positive
    is_newly_diagnosed = _is_newly_diagnosed(patient_data)
    has_flt3 = _has_flt3_mutation(patient_data)
    
    if is_newly_diagnosed and has_flt3:
        eligible_treatments.append("DA+Midostaurin")
    
    # CPX-351 eligibility: Untreated AND (prior MDS/CMML OR disease-defining cytogenetic abnormality OR therapy-related)
    is_untreated = _is_untreated(patient_data)
    has_prior_mds_cmml = _has_prior_mds_cmml(patient_data)
    has_disease_defining_cyto = _has_disease_defining_cytogenetic_abnormality(patient_data)
    is_therapy_related = _is_therapy_related_aml(patient_data)
    
    if (is_untreated and 
        (has_prior_mds_cmml or has_disease_defining_cyto or is_therapy_related)):
        eligible_treatments.append("CPX-351")
    
    return eligible_treatments


def _is_de_novo_aml(patient_data: dict) -> bool:
    """
    Determine if this is de novo AML (not therapy-related or arising from MDS/MPN).
    """
    qualifiers = patient_data.get("qualifiers", {})
    
    # Check for therapy-related factors
    therapy_related = (qualifiers.get("therapy_related", False) or
                      qualifiers.get("previous_chemotherapy", False) or
                      qualifiers.get("previous_radiotherapy", False))
    
    # Check for prior MDS/MPN
    prior_mds_mpn = (qualifiers.get("previous_MDS", False) or
                     qualifiers.get("previous_MPN", False) or
                     qualifiers.get("previous_MDS/MPN", False))
    
    return not (therapy_related or prior_mds_mpn)


def _is_newly_diagnosed(patient_data: dict) -> bool:
    """
    Determine if this is newly diagnosed AML.
    In most cases we assume this is true unless specified otherwise.
    """
    # Check for any indication of relapsed/refractory disease
    qualifiers = patient_data.get("qualifiers", {})
    
    relapsed_refractory = (qualifiers.get("relapsed", False) or
                          qualifiers.get("refractory", False) or
                          qualifiers.get("secondary", False))
    
    return not relapsed_refractory


def _is_untreated(patient_data: dict) -> bool:
    """
    Determine if this is untreated AML.
    This typically means newly diagnosed and not previously treated.
    """
    return _is_newly_diagnosed(patient_data)


def _is_cd33_positive(patient_data: dict) -> bool:
    """
    Determine if CD33 is positive based on parsed flow cytometry data.
    CD33 expression is critical for DA+GO eligibility.
    """
    # First check if CD33 status was parsed from the report
    cd33_status = patient_data.get("cd33_positive")
    if cd33_status is not None:
        return cd33_status
    
    # Check if CD33 percentage was provided
    cd33_percentage = patient_data.get("cd33_percentage")
    if cd33_percentage is not None:
        # Consider positive if ≥20% of blasts express CD33
        return cd33_percentage >= 20
    
    # If no flow cytometry data available, CD33 status is unknown
    # Do NOT assume positive - this should be determined by actual testing
    return False


def _get_cytogenetic_test_result(patient_data: dict) -> str:
    """
    Determine cytogenetic test result category based on ELN 2017 criteria.
    Returns: Favourable, Intermediate, Adverse, or Unknown
    """
    # Check for favourable cytogenetics (CBF and Non-CBF)
    if _has_favourable_cbf(patient_data) or _has_favourable_non_cbf(patient_data):
        return "Favourable"
    
    # Check for adverse cytogenetics
    if _has_adverse_cytogenetics(patient_data):
        return "Adverse"
    
    # Check if cytogenetic data is missing
    if _has_missing_cytogenetic_data(patient_data):
        return "Unknown"
    
    return "Intermediate"


def _has_favourable_cbf(patient_data: dict) -> bool:
    """Check for favourable CBF leukemias: t(8;21) or inv(16)/t(16;16)."""
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    
    return (aml_genes.get("RUNX1_RUNX1T1", False) or 
            aml_genes.get("t_8_21", False) or
            aml_genes.get("CBFB_MYH11", False) or
            aml_genes.get("inv_16", False) or
            aml_genes.get("t_16_16", False))


def _has_favourable_non_cbf(patient_data: dict) -> bool:
    """Check for favourable non-CBF: mutated NPM1 and FLT3-ITD negative."""
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    mds_mutations = patient_data.get("MDS_related_mutation", {})
    
    npm1_mutated = aml_genes.get("NPM1_mutation", False)
    flt3_itd = (mds_mutations.get("FLT3", False) or 
                aml_genes.get("FLT3_ITD", False))
    
    return npm1_mutated and not flt3_itd


def _has_adverse_cytogenetics(patient_data: dict) -> bool:
    """Check for adverse cytogenetics based on ELN 2017 criteria."""
    mds_cyto = patient_data.get("MDS_related_cytogenetics", {})
    
    return (mds_cyto.get("Complex_karyotype", False) or
            mds_cyto.get("-5", False) or
            mds_cyto.get("del_5q", False) or
            mds_cyto.get("-7", False) or
            mds_cyto.get("del_7q", False) or
            mds_cyto.get("-17", False) or
            mds_cyto.get("del_17p", False))


def _has_missing_cytogenetic_data(patient_data: dict) -> bool:
    """Check if cytogenetic data is missing or not available."""
    return patient_data.get("no_cytogenetics_data", False)


def _has_prior_mds_cmml(patient_data: dict) -> bool:
    """Check for prior history of MDS or CMML."""
    qualifiers = patient_data.get("qualifiers", {})
    
    return (qualifiers.get("previous_MDS", False) or
            qualifiers.get("previous_CMML", False) or
            qualifiers.get("previous_MDS/MPN", False))


def _has_disease_defining_cytogenetic_abnormality(patient_data: dict) -> bool:
    """
    Check for disease-defining cytogenetic abnormalities that qualify for CPX-351.
    These are typically MDS-related cytogenetic changes.
    """
    return _has_myelodysplasia_related_changes(patient_data)


def _has_flt3_mutation(patient_data: dict) -> bool:
    """Check for FLT3 mutations (ITD or TKD)."""
    mds_mutations = patient_data.get("MDS_related_mutation", {})
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    
    return (mds_mutations.get("FLT3", False) or 
            aml_genes.get("FLT3_ITD", False) or
            aml_genes.get("FLT3_TKD", False))


def _is_therapy_related_aml(patient_data: dict) -> bool:
    """Check if this is therapy-related AML."""
    qualifiers = patient_data.get("qualifiers", {})
    
    return (qualifiers.get("therapy_related", False) or
            qualifiers.get("previous_chemotherapy", False) or
            qualifiers.get("previous_radiotherapy", False))


def _has_myelodysplasia_related_changes(patient_data: dict) -> bool:
    """Check for myelodysplasia-related changes."""
    # Check for MDS-related mutations
    mds_mutations = patient_data.get("MDS_related_mutation", {})
    has_mds_mutations = any(mds_mutations.values()) if mds_mutations else False
    
    # Check for MDS-related cytogenetics
    mds_cyto = patient_data.get("MDS_related_cytogenetics", {})
    has_mds_cyto = any(mds_cyto.values()) if mds_cyto else False
    
    # Check for dysplastic changes
    dysplasia = patient_data.get("number_of_dysplastic_lineages", 0)
    
    return has_mds_mutations or has_mds_cyto or (dysplasia and dysplasia > 0)


def get_consensus_treatment_recommendation(patient_data: dict, patient_age: int, eln_risk: str) -> Dict:
    """
    Get treatment recommendation based on the detailed Coats consensus algorithm.
    Uses the Delphi survey results with specific age cutoffs (60 years) and ELN 2017 criteria.
    
    Args:
        patient_data (dict): Patient's parsed data
        patient_age (int): Patient's age
        eln_risk (str): ELN risk category
        
    Returns:
        Dict: Treatment recommendation with rationale
    """
    # Check for APL first (special case)
    if _is_apl(patient_data):
        return {
            "recommended_treatment": "ATRA + Arsenic ± Chemotherapy",
            "rationale": "APL with PML-RARA fusion requires specific treatment with ATRA and arsenic compounds.",
            "eligible_treatments": ["ATRA + Arsenic ± Chemotherapy"],
            "eln_risk": "APL",
            "age_group": "≥60 years" if patient_age >= 60 else "<60 years",
            "considerations": [
                "Initiate ATRA immediately upon APL suspicion",
                "Monitor for differentiation syndrome", 
                "Consider dexamethasone prophylaxis",
                "Molecular monitoring for PML-RARA transcript"
            ]
        }
    
    # Determine patient characteristics using detailed ELN 2017 criteria
    eligible_treatments = determine_treatment_eligibility(patient_data)
    detailed_eln_risk = _determine_detailed_eln_risk(patient_data)
    
    # Map patient age to consensus cohort (age cutoff is 60 in the detailed algorithm)
    age_group_for_lookup = 40 if patient_age < 60 else 65  # Represents younger vs older cohorts
    age_group_label = "<60 years" if patient_age < 60 else "≥60 years"
    
    # Create clinical scenario (combination of ELN risk and eligibility profile)
    patient_scenario = _create_clinical_scenario(detailed_eln_risk, eligible_treatments)
    
    # Look up consensus recommendation from the pre-established database
    consensus_recommendation = _lookup_consensus_treatment(patient_scenario, age_group_for_lookup)
    
    # Generate detailed rationale and considerations
    rationale = _generate_treatment_rationale(consensus_recommendation, detailed_eln_risk, eligible_treatments, patient_age)
    considerations = _generate_clinical_considerations(consensus_recommendation, patient_data, patient_age)
    
    return {
        "recommended_treatment": consensus_recommendation,
        "rationale": rationale,
        "eligible_treatments": eligible_treatments,
        "eln_risk": detailed_eln_risk,
        "age_group": age_group_label,
        "considerations": considerations,
        "clinical_scenario": patient_scenario
    }


def _is_apl(patient_data: dict) -> bool:
    """Check if this is APL (PML-RARA positive)."""
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    return aml_genes.get("PML_RARA", False)


def _determine_detailed_eln_risk(patient_data: dict) -> str:
    """
    Determine detailed ELN risk category using ELN 2017 criteria.
    Returns more specific categories: Favourable (CBF), Favourable (Non-CBF), Intermediate, Adverse
    """
    if _has_favourable_cbf(patient_data):
        return "Favourable (CBF)"
    elif _has_favourable_non_cbf(patient_data):
        return "Favourable (Non-CBF)"
    elif _has_adverse_cytogenetics(patient_data):
        return "Adverse"
    else:
        return "Intermediate"


def _create_clinical_scenario(eln_risk: str, eligible_treatments: List[str]) -> str:
    """
    Create clinical scenario string combining ELN risk and treatment eligibility profile.
    This represents the unique scenario used in the Delphi survey.
    """
    # Sort treatments for consistent scenario naming
    treatments_sorted = sorted(eligible_treatments)
    treatments_str = "+".join(treatments_sorted)
    return f"{eln_risk}_{treatments_str}"


def _lookup_consensus_treatment(scenario: str, age_group: int) -> str:
    """
    Look up consensus treatment from the pre-established database.
    This represents the results from the two-round Delphi survey.
    """
    # Consensus database based on the 22 scenarios from the paper
    # This is a simplified representation of the actual survey results
    
    consensus_db = {
        # Favourable CBF scenarios
        ("Favourable (CBF)_DA+DA+GO+FLAG-IDA", 40): "DA+GO",
        ("Favourable (CBF)_DA+DA+GO+FLAG-IDA", 65): "DA",
        ("Favourable (CBF)_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 40): "DA+Midostaurin",
        ("Favourable (CBF)_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 65): "DA+Midostaurin",
        
        # Favourable Non-CBF scenarios  
        ("Favourable (Non-CBF)_DA+DA+GO+FLAG-IDA", 40): "DA+GO",
        ("Favourable (Non-CBF)_DA+DA+GO+FLAG-IDA", 65): "DA",
        ("Favourable (Non-CBF)_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 40): "DA+Midostaurin",
        ("Favourable (Non-CBF)_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 65): "DA+Midostaurin",
        
        # Intermediate scenarios
        ("Intermediate_DA+DA+GO+FLAG-IDA", 40): "DA+GO",
        ("Intermediate_DA+DA+GO+FLAG-IDA", 65): "DA",
        ("Intermediate_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 40): "DA+Midostaurin",
        ("Intermediate_DA+DA+GO+DA+Midostaurin+FLAG-IDA", 65): "DA+Midostaurin",
        ("Intermediate_CPX-351+DA+FLAG-IDA", 40): "FLAG-IDA",
        ("Intermediate_CPX-351+DA+FLAG-IDA", 65): "CPX-351",
        ("Intermediate_CPX-351+DA+DA+Midostaurin+FLAG-IDA", 40): "DA+Midostaurin",
        ("Intermediate_CPX-351+DA+DA+Midostaurin+FLAG-IDA", 65): "CPX-351",
        
        # Adverse scenarios
        ("Adverse_DA+FLAG-IDA", 40): "FLAG-IDA",
        ("Adverse_DA+FLAG-IDA", 65): "DA",
        ("Adverse_CPX-351+DA+FLAG-IDA", 40): "CPX-351",
        ("Adverse_CPX-351+DA+FLAG-IDA", 65): "CPX-351",
        ("Adverse_CPX-351+DA+DA+Midostaurin+FLAG-IDA", 40): "CPX-351",
        ("Adverse_CPX-351+DA+DA+Midostaurin+FLAG-IDA", 65): "CPX-351",
    }
    
    # Look up the specific scenario
    lookup_key = (scenario, age_group)
    if lookup_key in consensus_db:
        return consensus_db[lookup_key]
    
    # Default fallback based on eligibility and age if exact scenario not found
    treatments = scenario.split("_")[1].split("+")
    
    if "CPX-351" in treatments:
        return "CPX-351"
    elif "DA+Midostaurin" in treatments:
        return "DA+Midostaurin"
    elif "DA+GO" in treatments and age_group == 40:
        return "DA+GO"
    elif age_group == 40:
        return "FLAG-IDA"
    else:
        return "DA"


def _generate_treatment_rationale(treatment: str, eln_risk: str, eligible_treatments: List[str], age: int) -> str:
    """Generate detailed rationale for the treatment recommendation."""
    
    if treatment == "ATRA + Arsenic ± Chemotherapy":
        return "APL-specific therapy for PML-RARA positive acute promyelocytic leukemia based on international guidelines."
    
    age_desc = "younger" if age < 60 else "older"
    
    rationales = {
        "DA+GO": f"Consensus recommendation for {age_desc} patients with {eln_risk.lower()} risk AML and CD33-positive disease. "
                f"Gemtuzumab ozogamicin provides additional anti-leukemic activity when combined with standard induction.",
        
        "DA+Midostaurin": f"Strong consensus for FLT3-mutated AML across all risk groups. "
                         f"FLT3 inhibition with midostaurin significantly improves outcomes in {eln_risk.lower()} risk disease.",
        
        "CPX-351": f"Preferred treatment for {age_desc} patients with therapy-related or MDS-related AML. "
                  f"Superior outcomes compared to standard DA, especially in adverse risk patients.",
        
        "FLAG-IDA": f"Intensive salvage-type regimen recommended for younger patients with {eln_risk.lower()} risk AML "
                   f"when other targeted options are not available.",
        
        "DA": f"Standard induction therapy appropriate for {age_desc} patients with {eln_risk.lower()} risk AML. "
             f"Well-tolerated with established efficacy."
    }
    
    return rationales.get(treatment, f"Consensus treatment recommendation for {eln_risk.lower()} risk AML in {age_desc} patients.")


def _generate_clinical_considerations(treatment: str, patient_data: dict, age: int) -> List[str]:
    """Generate clinical considerations based on treatment and patient factors."""
    
    considerations = []
    
    # Treatment-specific considerations
    if "GO" in treatment:
        considerations.extend([
            "Monitor for hepatotoxicity and veno-occlusive disease",
            "Ensure adequate CD33 expression confirmed",
            "Consider consolidation with high-dose cytarabine"
        ])
    
    if "Midostaurin" in treatment:
        considerations.extend([
            "Continue midostaurin through consolidation and maintenance",
            "Monitor QTc interval regularly",
            "Drug interactions with azole antifungals"
        ])
    
    if "CPX-351" in treatment:
        considerations.extend([
            "Requires experienced hematology center",
            "Prolonged cytopenias expected",
            "Enhanced supportive care needs"
        ])
    
    if "FLAG-IDA" in treatment:
        considerations.extend([
            "Intensive regimen - ensure good performance status",
            "Requires experienced transplant center",
            "Enhanced infection prophylaxis needed"
        ])
    
    # Risk-based considerations
    eln_risk = _determine_detailed_eln_risk(patient_data)
    if "Adverse" in eln_risk:
        considerations.extend([
            "Consider early allogeneic transplant evaluation",
            "Poor prognosis - discuss with patient",
            "Consider clinical trial enrollment"
        ])
    elif "Intermediate" in eln_risk:
        considerations.extend([
            "Consider allogeneic transplant in first remission",
            "Molecular monitoring for MRD"
        ])
    elif "Favourable" in eln_risk:
        considerations.extend([
            "Excellent prognosis expected",
            "Focus on consolidation therapy"
        ])
    
    # Age-specific considerations
    if age >= 60:
        considerations.extend([
            "Assess fitness for intensive therapy",
            "Consider comorbidities and performance status",
            "Enhanced supportive care protocols"
        ])
    
    return considerations


def _get_cytogenetic_risk(patient_data: dict) -> str:
    """
    Legacy function for display compatibility.
    Maps detailed ELN risk to simpler cytogenetic risk categories.
    """
    detailed_risk = _determine_detailed_eln_risk(patient_data)
    
    if "Favourable" in detailed_risk:
        return "Favorable"
    elif "Adverse" in detailed_risk:
        return "Adverse"
    else:
        return "Intermediate"


def _get_consensus_recommendation(eligible_treatments: List[str], eln_risk: str, age_group: str, patient_data: dict) -> Dict:
    """
    Get consensus recommendation based on a simplified version of the Coats algorithm.
    This represents the consensus database from the Delphi survey.
    """
    
    # Special case: APL (PML-RARA)
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    if aml_genes.get("PML_RARA", False):
        return {
            "treatment": "ATRA + Arsenic ± Chemotherapy",
            "rationale": "APL-specific therapy for PML-RARA positive acute promyelocytic leukemia",
            "considerations": ["Monitor for differentiation syndrome", "Coagulopathy management", "Molecular monitoring"]
        }
    
    # Favorable risk scenarios
    if eln_risk == "Favorable":
        if "DA+GO" in eligible_treatments and age_group == "young":
            return {
                "treatment": "DA+GO",
                "rationale": "Favorable risk young patient with CD33-positive disease benefits from gemtuzumab ozogamicin",
                "considerations": ["Monitor for hepatotoxicity", "Consider consolidation therapy", "Excellent prognosis expected"]
            }
        elif "DA+Midostaurin" in eligible_treatments:
            return {
                "treatment": "DA+Midostaurin",
                "rationale": "FLT3-mutated favorable risk AML benefits from FLT3 inhibition",
                "considerations": ["Continue midostaurin through consolidation", "Monitor QTc interval", "Consider MRD-directed therapy"]
            }
        else:
            return {
                "treatment": "DA",
                "rationale": "Standard induction for favorable risk AML",
                "considerations": ["Excellent prognosis with standard therapy", "Consider consolidation", "Monitor for relapse"]
            }
    
    # Intermediate risk scenarios
    elif eln_risk in ["Intermediate", "Intermediate-Adverse"]:
        if "DA+Midostaurin" in eligible_treatments:
            return {
                "treatment": "DA+Midostaurin",
                "rationale": "FLT3-mutated intermediate risk benefits significantly from FLT3 inhibition",
                "considerations": ["Essential to continue midostaurin", "Consider allogeneic transplant in CR1", "Monitor MRD"]
            }
        elif "CPX-351" in eligible_treatments and age_group == "older":
            return {
                "treatment": "CPX-351",
                "rationale": "Superior outcomes for older patients with therapy-related or MDS-related AML",
                "considerations": ["Requires experienced center", "Monitor for prolonged cytopenias", "Consider transplant if fit"]
            }
        elif "DA+GO" in eligible_treatments and age_group == "young":
            return {
                "treatment": "DA+GO",
                "rationale": "Young intermediate risk patients benefit from intensified induction",
                "considerations": ["Consider allogeneic transplant in CR1", "Monitor response", "Molecular monitoring"]
            }
        else:
            treatment = "FLAG-IDA" if age_group == "young" else "DA"
            return {
                "treatment": treatment,
                "rationale": f"Standard intensive therapy appropriate for {age_group} intermediate risk patients",
                "considerations": ["Consider allogeneic transplant", "Monitor treatment response", "Supportive care important"]
            }
    
    # Adverse risk scenarios
    else:  # Adverse risk
        if "CPX-351" in eligible_treatments:
            return {
                "treatment": "CPX-351",
                "rationale": "Superior outcomes for adverse risk AML, especially with MDS-related changes",
                "considerations": ["Strong transplant candidate if CR achieved", "Requires experienced center", "Poor prognosis"]
            }
        elif age_group == "young":
            treatment = "DA+Midostaurin" if "DA+Midostaurin" in eligible_treatments else "FLAG-IDA"
            return {
                "treatment": treatment,
                "rationale": "Intensive therapy for young adverse risk patients",
                "considerations": ["Urgent transplant evaluation", "Consider novel agents", "Poor prognosis with standard therapy"]
            }
        else:
            return {
                "treatment": "DA or Hypomethylating agents",
                "rationale": "Older adverse risk patients - consider fitness for intensive therapy",
                "considerations": ["Evaluate transplant eligibility", "Consider clinical trials", "Palliative care discussion"]
            }


def display_treatment_recommendations(patient_data: dict, eln_risk: str, patient_age: Optional[int] = None):
    """
    Display treatment recommendations in Streamlit interface.
    
    Args:
        patient_data (dict): Patient's parsed genetic and clinical data
        eln_risk (str): ELN risk classification
        patient_age (Optional[int]): Patient's age (if available)
    """
    
    st.markdown("### AML Treatment Recommendations")
    
    # Citation
    with st.expander("📚 Reference", expanded=False):
        st.markdown("""
        **Citation:** Coats T, Bean D, Basset A, Sirkis T, Brammeld J, Johnson S, et al. 
        A novel algorithmic approach to generate consensus treatment guidelines in adult acute myeloid leukaemia. 
        *Br J Haematol.* 2022;196:1337–1343. 
        
        **DOI:** [https://doi.org/10.1111/bjh.18013](https://doi.org/10.1111/bjh.18013)
        
        **Note:** This implementation is a simplified version of the Coats algorithm for educational purposes. 
        Clinical decisions should always involve multidisciplinary team discussion and consideration of individual patient factors.
        """)
    
    # Age input if not provided
    if patient_age is None:
        st.markdown("#### Patient Age Required")
        patient_age = st.number_input("Enter patient age:", min_value=18, max_value=100, value=65, step=1)
        if st.button("Get Treatment Recommendation"):
            st.session_state["treatment_age"] = patient_age
            st.rerun()
        return
    
    # Get treatment recommendation
    recommendation = get_consensus_treatment_recommendation(patient_data, patient_age, eln_risk)
    
    # Display recommendation
    st.markdown("#### Consensus Treatment Recommendation")
    
    # Treatment recommendation box
    treatment_color = _get_treatment_color(recommendation["recommended_treatment"])
    st.markdown(f"""
    <div style="background-color: {treatment_color}; padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 2px solid #0066cc;">
        <h3 style="margin: 0; color: #0066cc;">🎯 {recommendation['recommended_treatment']}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Rationale
    st.markdown("#### Rationale")
    st.markdown(recommendation["rationale"])
    
    # Key considerations
    if recommendation["considerations"]:
        st.markdown("#### Key Clinical Considerations")
        for consideration in recommendation["considerations"]:
            st.markdown(f"• {consideration}")
    
    # Show details in expandable sections
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("Treatment Eligibility Analysis", expanded=False):
            st.markdown("**Eligible Treatments:**")
            for treatment in recommendation["eligible_treatments"]:
                st.markdown(f"✅ {treatment}")
            
            st.markdown("**Eligibility Criteria Applied:**")
            
            # CD33 status
            cd33_positive = _is_cd33_positive(patient_data)
            cd33_percentage = patient_data.get("cd33_percentage")
            
            if patient_data.get("cd33_positive") is not None:
                cd33_status = "Positive" if cd33_positive else "Negative"
            elif cd33_percentage is not None:
                cd33_status = f"{'Positive' if cd33_positive else 'Negative'} ({cd33_percentage}%)"
            else:
                cd33_status = "Unknown - Flow cytometry required"
            
            st.markdown(f"• **CD33 Status:** {cd33_status}")
            
            # FLT3 status
            flt3_status = "Present" if _has_flt3_mutation(patient_data) else "Not detected"
            st.markdown(f"• **FLT3 Mutation:** {flt3_status}")
            
            # Therapy-related
            tr_status = "Yes" if _is_therapy_related_aml(patient_data) else "No"
            st.markdown(f"• **Therapy-related AML:** {tr_status}")
            
            # MDS-related changes
            mds_status = "Yes" if _has_myelodysplasia_related_changes(patient_data) else "No"
            st.markdown(f"• **Myelodysplasia-related changes:** {mds_status}")
    
    with col2:
        with st.expander("Risk Stratification Details", expanded=False):
            st.markdown(f"**ELN Risk Category:** {eln_risk}")
            st.markdown(f"**Cytogenetic Risk:** {_get_cytogenetic_risk(patient_data)}")
            st.markdown(f"**Age Group:** {recommendation['age_group'].title()} ({patient_age} years)")
            
            # Risk factors
            st.markdown("**Key Risk Factors:**")
            
            # Favorable markers
            aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
            if any([aml_genes.get("RUNX1_RUNX1T1"), aml_genes.get("CBFB_MYH11"), 
                   aml_genes.get("inv_16"), aml_genes.get("t_8_21")]):
                st.markdown("• Favorable cytogenetics detected")
            
            # Adverse markers
            mds_cyto = patient_data.get("MDS_related_cytogenetics", {})
            if any([mds_cyto.get("Complex_karyotype"), mds_cyto.get("-7"), 
                   mds_cyto.get("del_7q"), mds_cyto.get("-5"), mds_cyto.get("del_5q")]):
                st.markdown("• Adverse cytogenetics detected")
            
            # FLT3
            if _has_flt3_mutation(patient_data):
                st.markdown("• FLT3 mutation present")
    
    # Disclaimer
    st.markdown("---")
    st.markdown("""
    **⚠️ Important Disclaimer:** 
    These recommendations are based on a simplified algorithmic approach and should not replace clinical judgment. 
    Treatment decisions should always involve multidisciplinary team discussion, consideration of comorbidities, 
    performance status, patient preferences, and local treatment protocols.
    """)


def _get_treatment_color(treatment: str) -> str:
    """Get color for treatment recommendation box."""
    if "ATRA" in treatment or "APL" in treatment:
        return "#e8f5e8"  # Light green for APL
    elif "CPX-351" in treatment:
        return "#fff3cd"  # Light yellow for CPX-351
    elif "Midostaurin" in treatment:
        return "#d1ecf1"  # Light blue for targeted therapy
    else:
        return "#f8f9fa"  # Light gray for standard therapy 