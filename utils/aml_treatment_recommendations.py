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
    Determine which treatments a patient is eligible for based on their molecular profile.
    
    Args:
        patient_data (dict): Patient's parsed genetic and clinical data
        
    Returns:
        List[str]: List of eligible treatments
    """
    eligible_treatments = []
    
    # Always eligible treatments
    eligible_treatments.extend(["DA", "FLAG-IDA"])
    
    # DA+GO eligibility: CD33 positive AND cytogenetic risk not adverse
    cd33_positive = _is_cd33_positive(patient_data)
    cytogenetic_risk = _get_cytogenetic_risk(patient_data)
    
    if cd33_positive and cytogenetic_risk != "Adverse":
        eligible_treatments.append("DA+GO")
    
    # DA+Midostaurin eligibility: FLT3 mutation present
    if _has_flt3_mutation(patient_data):
        eligible_treatments.append("DA+Midostaurin")
    
    # CPX-351 eligibility: therapy-related AML OR myelodysplasia-related changes
    if _is_therapy_related_aml(patient_data) or _has_myelodysplasia_related_changes(patient_data):
        eligible_treatments.append("CPX-351")
    
    return eligible_treatments


def _is_cd33_positive(patient_data: dict) -> bool:
    """
    Determine if CD33 is positive. In most AML cases, CD33 is positive.
    This is a simplification - in practice this would require flow cytometry data.
    """
    # CD33 is positive in approximately 85-90% of AML cases
    # Without specific flow cytometry data, we assume positive unless specified otherwise
    cd33_status = patient_data.get("cd33_positive")
    if cd33_status is not None:
        return cd33_status
    
    # Default assumption: CD33 positive (can be overridden with specific data)
    return True


def _get_cytogenetic_risk(patient_data: dict) -> str:
    """
    Determine cytogenetic risk category based on genetic abnormalities.
    This uses simplified ELN-like criteria.
    """
    # Check for favorable cytogenetics
    aml_genes = patient_data.get("AML_defining_recurrent_genetic_abnormalities", {})
    
    if (aml_genes.get("RUNX1_RUNX1T1", False) or 
        aml_genes.get("CBFB_MYH11", False) or
        aml_genes.get("inv_16", False) or
        aml_genes.get("t_8_21", False)):
        return "Favorable"
    
    # Check for adverse cytogenetics
    mds_cyto = patient_data.get("MDS_related_cytogenetics", {})
    
    if (mds_cyto.get("Complex_karyotype", False) or
        mds_cyto.get("-7", False) or
        mds_cyto.get("del_7q", False) or
        mds_cyto.get("-5", False) or
        mds_cyto.get("del_5q", False)):
        return "Adverse"
    
    # Check for therapy-related or MDS-related markers (intermediate-adverse)
    if (_is_therapy_related_aml(patient_data) or 
        _has_myelodysplasia_related_changes(patient_data)):
        return "Intermediate-Adverse"
    
    return "Intermediate"


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
    Get consensus treatment recommendation based on eligibility, age, and risk.
    
    Args:
        patient_data (dict): Patient's parsed data
        patient_age (int): Patient's age
        eln_risk (str): ELN risk category
        
    Returns:
        Dict: Treatment recommendation with rationale
    """
    eligible_treatments = determine_treatment_eligibility(patient_data)
    
    # Age group categorization
    age_group = "young" if patient_age < 60 else "older"
    
    # Get recommendation based on consensus database
    recommendation = _get_consensus_recommendation(eligible_treatments, eln_risk, age_group, patient_data)
    
    return {
        "recommended_treatment": recommendation["treatment"],
        "rationale": recommendation["rationale"],
        "eligible_treatments": eligible_treatments,
        "eln_risk": eln_risk,
        "age_group": age_group,
        "considerations": recommendation["considerations"]
    }


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
            cd33_status = "Positive (assumed)" if _is_cd33_positive(patient_data) else "Negative/Unknown"
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