# Classification Algorithms Documentation

## Overview

Haem.io implements evidence-based classification algorithms following the WHO 2022 and ICC 2022 international standards for hematologic malignancies. This document describes the algorithmic implementation of these classification systems and risk assessment tools.

## WHO 2022 Classification

### AML Classification Algorithm

#### Decision Tree Structure

```
Patient Data Input
    ↓
Blast Count ≥20%? → No → Check for AML-defining abnormalities
    ↓ Yes
Genetic Abnormalities Present?
    ↓ Yes
├── NPM1 mutation → AML with mutated NPM1
├── CEBPA mutation → AML with mutated CEBPA  
├── RUNX1-RUNX1T1 → AML with t(8;21)(q22;q22)
├── CBFB-MYH11 → AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)
├── PML-RARA → Acute promyelocytic leukemia with PML-RARA
├── KMT2A rearrangements → AML with KMT2A rearrangement
├── DEK-NUP214 → AML with t(6;9)(p23;q34.1)
└── BCR-ABL1 → AML with BCR-ABL1
    ↓ No specific abnormalities
Myelodysplasia-related changes?
    ↓ Yes → AML with myelodysplasia-related changes
    ↓ No
Therapy-related?
    ↓ Yes → Therapy-related myeloid neoplasm
    ↓ No
AML, not otherwise specified
```

#### Implementation

```python
def classify_aml_who2022(parsed_data: Dict) -> Tuple[str, str, float]:
    """
    WHO 2022 AML Classification Algorithm
    
    Returns: (classification, rationale, confidence_score)
    """
    blast_percentage = parsed_data.get('blasts_percentage', 0)
    genetic_abnormalities = parsed_data.get('AML_defining_recurrent_genetic_abnormalities', {})
    mds_mutations = parsed_data.get('MDS_related_mutation', {})
    qualifiers = parsed_data.get('qualifiers', {})
    
    # Priority 1: AML-defining genetic abnormalities (regardless of blast count)
    if genetic_abnormalities.get('PML_RARA'):
        return "Acute promyelocytic leukemia with PML-RARA", "APL classification", 0.95
    
    if genetic_abnormalities.get('NPM1_mutation'):
        return "AML with mutated NPM1", "NPM1 mutation present", 0.9
    
    if genetic_abnormalities.get('CEBPA_mutation'):
        return "AML with mutated CEBPA", "CEBPA mutation present", 0.9
    
    # Core binding factor leukemias
    if genetic_abnormalities.get('RUNX1_RUNX1T1'):
        return "AML with t(8;21)(q22;q22);RUNX1-RUNX1T1", "CBF leukemia", 0.95
    
    if genetic_abnormalities.get('CBFB_MYH11'):
        return "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22);CBFB-MYH11", "CBF leukemia", 0.95
    
    # Other specific abnormalities
    if genetic_abnormalities.get('KMT2A_rearranged'):
        return "AML with KMT2A rearrangement", "KMT2A rearrangement", 0.85
    
    # Priority 2: Blast count requirement for other categories
    if blast_percentage >= 20:
        # Check for myelodysplasia-related changes
        if has_mds_related_changes(parsed_data):
            return "AML with myelodysplasia-related changes", "MDS-related features", 0.8
        
        # Check for therapy-related
        if qualifiers.get('previous_cytotoxic_therapy') != "None":
            return "Therapy-related myeloid neoplasm", "Prior therapy history", 0.85
        
        # Default AML NOS
        return "AML, not otherwise specified", "Meets blast criteria", 0.7
    
    # Insufficient blast count
    return "Insufficient criteria for AML", "Blast count <20%", 0.3

def has_mds_related_changes(parsed_data: Dict) -> bool:
    """Determine if patient has myelodysplasia-related changes"""
    
    # MDS-related mutations
    mds_mutations = parsed_data.get('MDS_related_mutation', {})
    if any(mds_mutations.values()):
        return True
    
    # MDS-related cytogenetics
    cytogenetics = parsed_data.get('MDS_related_cytogenetics', {})
    if any(cytogenetics.values()):
        return True
    
    # Prior MDS history
    qualifiers = parsed_data.get('qualifiers', {})
    if qualifiers.get('previous_MDS_diagnosed_over_3_months_ago'):
        return True
    
    # Multilineage dysplasia
    morphology = parsed_data.get('morphology', {})
    if morphology.get('multilineage_dysplasia'):
        return True
    
    return False
```

### MDS Classification Algorithm

```python
def classify_mds_who2022(parsed_data: Dict) -> Tuple[str, str, float]:
    """WHO 2022 MDS Classification"""
    
    blast_percentage = parsed_data.get('blasts_percentage', 0)
    ring_sideroblasts = parsed_data.get('morphology', {}).get('ring_sideroblasts_percentage', 0)
    sf3b1_mutation = parsed_data.get('MDS_related_mutation', {}).get('SF3B1', False)
    multilineage_dysplasia = parsed_data.get('morphology', {}).get('multilineage_dysplasia', False)
    
    # MDS with ring sideroblasts
    if ring_sideroblasts >= 15 or (ring_sideroblasts >= 5 and sf3b1_mutation):
        if sf3b1_mutation:
            return "MDS with ring sideroblasts and SF3B1 mutation", "Ring sideroblasts + SF3B1", 0.9
        else:
            return "MDS with ring sideroblasts", "Ring sideroblasts ≥15%", 0.85
    
    # Blast-based classification
    if blast_percentage < 5:
        if multilineage_dysplasia:
            return "MDS with multilineage dysplasia", "Multilineage dysplasia", 0.8
        else:
            return "MDS with single lineage dysplasia", "Single lineage dysplasia", 0.75
    
    elif blast_percentage < 10:
        return "MDS with excess blasts-1", "Blasts 5-9%", 0.85
    
    elif blast_percentage < 20:
        return "MDS with excess blasts-2", "Blasts 10-19%", 0.85
    
    else:
        return "Possible AML", "Blast count ≥20%", 0.6
```

## ICC 2022 Classification

### Key Differences from WHO 2022

1. **Blast Threshold**: ICC maintains 20% blast threshold for AML
2. **TP53-mutated AML/MDS**: Separate category for TP53-mutated neoplasms
3. **Hypoplastic MDS**: Distinct recognition of hypocellular MDS
4. **Genetic Risk Groups**: Enhanced molecular risk stratification

```python
def classify_icc2022(parsed_data: Dict) -> Tuple[str, str, float]:
    """ICC 2022 Classification Implementation"""
    
    tp53_status = parsed_data.get('Biallelic_TP53_mutation', {})
    blast_percentage = parsed_data.get('blasts_percentage', 0)
    
    # TP53-mutated neoplasms (ICC-specific category)
    if has_tp53_abnormalities(tp53_status):
        if blast_percentage >= 20:
            return "AML with TP53 mutation", "TP53-mutated AML", 0.9
        else:
            return "MDS with TP53 mutation", "TP53-mutated MDS", 0.9
    
    # Otherwise follows similar logic to WHO with minor modifications
    return classify_who2022_with_icc_modifications(parsed_data)

def has_tp53_abnormalities(tp53_data: Dict) -> bool:
    """Check for TP53 abnormalities"""
    return (tp53_data.get('TP53_mutation', False) or 
            tp53_data.get('del_17p', False) or
            tp53_data.get('complex_karyotype', False))
```

## Risk Assessment Algorithms

### ELN 2022 Risk Stratification

```python
def calculate_eln2022_risk(parsed_data: Dict) -> Dict:
    """
    ELN 2022 Risk Stratification for AML
    
    Returns: Risk category and contributing factors
    """
    
    genetic_abnormalities = parsed_data.get('AML_defining_recurrent_genetic_abnormalities', {})
    eln_genes = parsed_data.get('ELN2024_risk_genes', {})
    cytogenetics = parsed_data.get('MDS_related_cytogenetics', {})
    
    risk_score = 0
    risk_factors = []
    
    # Favorable risk factors
    if genetic_abnormalities.get('RUNX1_RUNX1T1') or genetic_abnormalities.get('CBFB_MYH11'):
        return {
            "risk_category": "Favorable",
            "risk_factors": ["Core binding factor leukemia"],
            "rationale": "t(8;21) or inv(16)/t(16;16)"
        }
    
    if (genetic_abnormalities.get('NPM1_mutation') and 
        not eln_genes.get('FLT3_ITD')):
        return {
            "risk_category": "Favorable", 
            "risk_factors": ["NPM1 mutation without FLT3-ITD"],
            "rationale": "NPM1+ FLT3-ITD-"
        }
    
    if genetic_abnormalities.get('CEBPA_mutation'):
        return {
            "risk_category": "Favorable",
            "risk_factors": ["CEBPA mutation"],
            "rationale": "Biallelic CEBPA mutation"
        }
    
    # Adverse risk factors
    adverse_markers = []
    
    if eln_genes.get('TP53'):
        adverse_markers.append("TP53 mutation")
        risk_score += 3
    
    if cytogenetics.get('complex_karyotype'):
        adverse_markers.append("Complex karyotype")
        risk_score += 3
    
    if cytogenetics.get('monosomal_karyotype'):
        adverse_markers.append("Monosomal karyotype")
        risk_score += 3
    
    if eln_genes.get('ASXL1'):
        adverse_markers.append("ASXL1 mutation")
        risk_score += 1
    
    if eln_genes.get('RUNX1'):
        adverse_markers.append("RUNX1 mutation")
        risk_score += 1
    
    # Risk categorization
    if risk_score >= 3 or len(adverse_markers) >= 2:
        return {
            "risk_category": "Adverse",
            "risk_factors": adverse_markers,
            "rationale": "Multiple adverse risk factors"
        }
    
    # Intermediate risk (default)
    intermediate_factors = []
    if eln_genes.get('FLT3_ITD'):
        intermediate_factors.append("FLT3-ITD mutation")
    
    return {
        "risk_category": "Intermediate",
        "risk_factors": intermediate_factors or ["No favorable or adverse markers"],
        "rationale": "Intermediate-risk genetics"
    }
```

### IPSS Risk Scoring

```python
def calculate_ipss_risk(parsed_data: Dict) -> Dict:
    """
    International Prognostic Scoring System for MDS
    """
    
    blast_percentage = parsed_data.get('blasts_percentage', 0)
    cytogenetics = parsed_data.get('cytogenetics', {})
    cytopenias = parsed_data.get('cytopenias', {})
    
    # Blast score
    if blast_percentage < 5:
        blast_score = 0
    elif blast_percentage <= 10:
        blast_score = 0.5
    elif blast_percentage <= 20:
        blast_score = 1.5
    else:
        blast_score = 2.0
    
    # Cytogenetic score
    cytogenetic_risk = cytogenetics.get('risk_category', 'Intermediate')
    if cytogenetic_risk == 'Very Good':
        cyto_score = -1
    elif cytogenetic_risk == 'Good':
        cyto_score = 0
    elif cytogenetic_risk == 'Intermediate':
        cyto_score = 1
    elif cytogenetic_risk == 'Poor':
        cyto_score = 2
    else:  # Very Poor
        cyto_score = 3
    
    # Cytopenia score
    cytopenia_count = 0
    if cytopenias.get('hemoglobin', 10) < 10:
        cytopenia_count += 1
    if cytopenias.get('neutrophils', 1.8) < 1.8:
        cytopenia_count += 1
    if cytopenias.get('platelets', 100) < 100:
        cytopenia_count += 1
    
    if cytopenia_count == 0:
        cytopenia_score = 0
    elif cytopenia_count <= 1:
        cytopenia_score = 0.5
    else:
        cytopenia_score = 1.0
    
    # Total IPSS score
    total_score = blast_score + cyto_score + cytopenia_score
    
    # Risk categorization
    if total_score <= 0:
        risk_category = "Very Low"
        median_survival = 141
    elif total_score <= 1:
        risk_category = "Low" 
        median_survival = 55
    elif total_score <= 2:
        risk_category = "Intermediate"
        median_survival = 31
    elif total_score <= 3:
        risk_category = "High"
        median_survival = 19
    else:
        risk_category = "Very High"
        median_survival = 10
    
    return {
        "ipss_score": total_score,
        "risk_category": risk_category,
        "component_scores": {
            "blast_score": blast_score,
            "cytogenetic_score": cyto_score, 
            "cytopenia_score": cytopenia_score
        },
        "survival_estimates": {
            "median_survival_months": median_survival
        }
    }
```

### IPSS-M Molecular Enhancement

```python
def calculate_ipssm_risk(parsed_data: Dict) -> Dict:
    """IPSS-M with molecular markers"""
    
    # Start with standard IPSS
    ipss_result = calculate_ipss_risk(parsed_data)
    base_score = ipss_result["ipss_score"]
    
    # Add molecular component
    mds_mutations = parsed_data.get('MDS_related_mutation', {})
    molecular_score = 0
    molecular_markers = []
    
    # Favorable molecular markers
    if mds_mutations.get('SF3B1'):
        molecular_score -= 0.5
        molecular_markers.append("SF3B1 (favorable)")
    
    # Adverse molecular markers
    if mds_mutations.get('TP53'):
        molecular_score += 1.5
        molecular_markers.append("TP53 (adverse)")
    
    if mds_mutations.get('ASXL1'):
        molecular_score += 0.5
        molecular_markers.append("ASXL1 (adverse)")
    
    if mds_mutations.get('RUNX1'):
        molecular_score += 0.5
        molecular_markers.append("RUNX1 (adverse)")
    
    if mds_mutations.get('EZH2'):
        molecular_score += 0.5
        molecular_markers.append("EZH2 (adverse)")
    
    # Calculate final IPSS-M score
    ipssm_score = base_score + molecular_score
    
    # Adjust risk category based on molecular score
    if ipssm_score <= -0.5:
        risk_category = "Very Low"
    elif ipssm_score <= 1:
        risk_category = "Low"
    elif ipssm_score <= 2.5:
        risk_category = "Moderate Low"
    elif ipssm_score <= 3.5:
        risk_category = "Moderate High"
    elif ipssm_score <= 4.5:
        risk_category = "High"
    else:
        risk_category = "Very High"
    
    return {
        "ipssm_score": ipssm_score,
        "risk_category": risk_category,
        "molecular_score": molecular_score,
        "molecular_markers": molecular_markers,
        "base_ipss": ipss_result
    }
```

## Confidence Scoring

### Algorithm Confidence Calculation

```python
def calculate_confidence_score(classification_data: Dict) -> float:
    """
    Calculate confidence score for classification
    
    Factors:
    - Presence of defining genetic abnormalities: +0.3
    - Blast count certainty: +0.2
    - Morphologic features: +0.2
    - Clinical history consistency: +0.2
    - Cytogenetic data quality: +0.1
    """
    
    confidence = 0.0
    
    # Genetic abnormalities boost confidence
    genetic_abnormalities = classification_data.get('AML_defining_recurrent_genetic_abnormalities', {})
    if any(genetic_abnormalities.values()):
        confidence += 0.3
    
    # Blast count reliability
    blast_percentage = classification_data.get('blasts_percentage')
    if blast_percentage is not None:
        if blast_percentage >= 20 or blast_percentage < 5:
            confidence += 0.2  # Clear thresholds
        else:
            confidence += 0.1  # Intermediate values
    
    # Morphologic data presence
    morphology = classification_data.get('morphology', {})
    if any(morphology.values()):
        confidence += 0.2
    
    # Clinical history
    qualifiers = classification_data.get('qualifiers', {})
    if any(qualifiers.values()):
        confidence += 0.2
    
    # Cytogenetic data
    cytogenetics = classification_data.get('MDS_related_cytogenetics', {})
    if any(cytogenetics.values()):
        confidence += 0.1
    
    return min(confidence, 1.0)  # Cap at 1.0
```

## Validation and Quality Control

### Data Quality Assessment

```python
def assess_data_quality(parsed_data: Dict) -> Dict:
    """Assess quality and completeness of parsed data"""
    
    quality_score = 0.0
    issues = []
    
    # Essential data checks
    if 'blasts_percentage' not in parsed_data:
        issues.append("Missing blast percentage")
    else:
        quality_score += 0.3
    
    # Genetic data completeness
    genetic_data = parsed_data.get('AML_defining_recurrent_genetic_abnormalities', {})
    if genetic_data:
        quality_score += 0.3
    else:
        issues.append("No genetic abnormality data")
    
    # Morphologic data
    morphology = parsed_data.get('morphology', {})
    if morphology:
        quality_score += 0.2
    else:
        issues.append("Limited morphologic data")
    
    # Clinical context
    qualifiers = parsed_data.get('qualifiers', {})
    if qualifiers:
        quality_score += 0.2
    
    return {
        "quality_score": quality_score,
        "data_completeness": "High" if quality_score >= 0.8 else "Medium" if quality_score >= 0.5 else "Low",
        "issues": issues,
        "recommendations": generate_data_recommendations(issues)
    }

def generate_data_recommendations(issues: List[str]) -> List[str]:
    """Generate recommendations for improving data quality"""
    recommendations = []
    
    if "Missing blast percentage" in issues:
        recommendations.append("Obtain bone marrow aspirate and biopsy with blast count")
    
    if "No genetic abnormality data" in issues:
        recommendations.append("Perform genetic testing including cytogenetics and molecular studies")
    
    if "Limited morphologic data" in issues:
        recommendations.append("Review morphologic features and dysplasia assessment")
    
    return recommendations
```

This algorithmic framework ensures consistent, evidence-based classification while maintaining transparency in the decision-making process. The modular design allows for easy updates as classification criteria evolve. 