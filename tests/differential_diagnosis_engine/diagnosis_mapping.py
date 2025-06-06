"""
Diagnosis mapping between WHO 2022 and ICC 2022 classification systems.

This module provides mappings and utilities for comparing diagnoses between
the two classification systems, accounting for differences in terminology
and categorization.
"""

from typing import Dict, List, Set, Tuple, Optional
import re

# Core diagnosis categories for analysis
DIAGNOSIS_CATEGORIES = {
    "AML_GENETIC": "AML with specific genetic abnormalities",
    "AML_MDS_RELATED": "AML with myelodysplasia-related changes", 
    "AML_THERAPY_RELATED": "Therapy-related AML",
    "AML_NOS": "AML not otherwise specified",
    "AML_ERYTHROID": "Acute erythroid leukemia",
    "APL": "Acute promyelocytic leukemia",
    "MDS_TP53": "MDS with TP53 alterations",
    "MDS_SF3B1": "MDS with SF3B1 mutation",
    "MDS_5Q": "MDS with isolated del(5q)",
    "MDS_BLASTS": "MDS defined by blast percentage",
    "MDS_DYSPLASIA": "MDS defined by dysplasia",
    "MDS_NOS": "MDS not otherwise specified",
    "MDS_AML_HYBRID": "MDS/AML hybrid category (ICC only)",
    "NOT_AML": "Not AML - consider MDS",
    "UNCLASSIFIABLE": "Unclassifiable cases"
}

# WHO to ICC diagnosis mappings - CORRECTED based on actual classification logic
WHO_TO_ICC_MAPPINGS = {
    # AML with genetic abnormalities - these map to different nomenclature in ICC
    "AML with NPM1 mutation": "AML with mutated NPM1",
    "Acute promyelocytic leukaemia with PML::RARA fusion": "APL with t(15;17)(q24.1;q21.2)/PML::RARA",
    "AML with RUNX1::RUNX1T1 fusion": "AML with t(8;21)(q22;q22.1)/RUNX1::RUNX1T1",
    "AML with CBFB::MYH11 fusion": "AML with inv(16)(p13.1q22) or t(16;16)(p13.1;q22)/CBFB::MYH11",
    "AML with DEK::NUP214 fusion": "AML with t(6;9)(p22.3;q34.1)/DEK::NUP214",
    "AML with RBM15::MRTFA fusion": "AML (megakaryoblastic) with t(1;22)(p13.3;q13.1)/RBM15::MRTFA",
    "AML with KMT2A rearrangement": "AML with KMT2A rearrangement",  # Similar in both
    "AML with MECOM rearrangement": "AML with MECOM rearrangement",  # Similar in both  
    "AML with NUP98 rearrangement": "AML with NUP98 and other partners",
    "AML with CEBPA mutation": "AML with in-frame bZIP mutated CEBPA",
    "AML with BCR::ABL1 fusion": "AML with t(9;22)(q34.1;q11.2)/BCR::ABL1",
    
    # AML myelodysplasia-related - WHO has single category, ICC distinguishes gene vs cyto
    "AML, myelodysplasia related": "AML with myelodysplasia related gene mutation",  # Default mapping to gene variant
    
    # Default/differentiation-based AML
    "Acute myeloid leukaemia, [define by differentiation]": "AML, NOS",
    "Acute myeloid leukaemia, unknown differentiation": "AML, NOS",
    
    # Specific differentiation types - ICC doesn't subdivide these like WHO
    "Acute myeloid leukaemia with minimal differentiation": "AML, NOS",
    "Acute myeloid leukaemia without maturation": "AML, NOS",
    "Acute myeloid leukaemia with maturation": "AML, NOS",
    "Acute promyelocytic leukaemia": "APL with t(15;17)(q24.1;q21.2)/PML::RARA",
    "Acute myelomonocytic leukaemia": "AML, NOS",
    "Acute myelomonocytic leukaemia with eosinophilia": "AML, NOS",
    "Acute monoblastic leukaemia": "AML, NOS", 
    "Acute monocytic leukaemia": "AML, NOS",
    "Acute erythroid leukaemia": "AML, NOS",  # ICC doesn't have separate erythroid category
    "Pure erythroid leukaemia": "AML, NOS",
    "Acute megakaryoblastic leukaemia": "AML, NOS",
    
    # MDS with TP53 - Different terminology
    "MDS with biallelic TP53 inactivation": "MDS with mutated TP53",
    
    # MDS with SF3B1 - Different terminology  
    "MDS with low blasts and SF3B1": "MDS with mutated SF3B1",
    
    # MDS with del(5q) - Similar but slightly different names
    "MDS with low blasts and isolated 5q-": "MDS with del(5q)",
    
    # MDS blast-based - Key difference: ICC has MDS/AML category for 10-19%
    "MDS with increased blasts 1": "MDS with excess blasts",      # WHO: 5-9%, ICC: 5-9%
    "MDS with increased blasts 2": "MDS/AML",                     # WHO: 10-19%, ICC: 10-19% -> MDS/AML
    
    # MDS dysplasia-based - ICC has more specific categories
    "MDS with low blasts": "MDS, NOS with single lineage dysplasia",  # Approximate mapping
    
    # WHO-specific categories that ICC doesn't have
    "MDS, fibrotic": "MDS with excess blasts",  # ICC doesn't have fibrotic category, map to blast-based
    "MDS, hypoplastic": "MDS, NOS",  # ICC doesn't have hypoplastic category
    
    # Default MDS
    "MDS, unclassifiable": "MDS, NOS",
    
    # Not AML - same in both systems
    "Not AML, consider MDS classification": "Not AML, consider MDS classification",
}

# ICC to WHO reverse mappings (where different)
ICC_TO_WHO_MAPPINGS = {
    # Reverse the basic mappings
    "AML with mutated NPM1": "AML with NPM1 mutation",
    "AML, NOS": "Acute myeloid leukaemia, [define by differentiation]",  # Default WHO classification
    "MDS with mutated TP53": "MDS with biallelic TP53 inactivation", 
    "MDS with mutated SF3B1": "MDS with low blasts and SF3B1",
    "MDS with del(5q)": "MDS with low blasts and isolated 5q-",
    "MDS with excess blasts": "MDS with increased blasts 1",  # 5-9% range
    "MDS, NOS": "MDS, unclassifiable",  # WHO default
    
    # ICC-specific categories that don't have WHO equivalents
    "MDS/AML": "MDS with increased blasts 2",  # ICC hybrid -> WHO 10-19% category
    "AML with mutated TP53": "AML with biallelic TP53 inactivation",  # ICC AML TP53 variant
    "MDS, NOS with multilineage dysplasia": "MDS with low blasts",  # WHO doesn't distinguish lineage count in name
    "MDS, NOS with single lineage dysplasia": "MDS with low blasts",
    "MDS, NOS without dysplasia": "MDS, unclassifiable",  # Approximate mapping
    
    # Myelodysplasia-related variants
    "AML with myelodysplasia related gene mutation": "AML, myelodysplasia related",
    "AML with myelodysplasia related cytogenetic abnormality": "AML, myelodysplasia related",
}

def normalize_classification(classification: str) -> str:
    """
    Normalize a classification string by removing system suffix and extra whitespace.
    
    Args:
        classification: Raw classification string
        
    Returns:
        Normalized classification string
    """
    if not classification:
        return ""
        
    # Remove system suffixes
    classification = re.sub(r'\s*\((WHO|ICC)\s*202[0-9]\)\s*$', '', classification)
    
    # Remove extra whitespace
    classification = ' '.join(classification.split())
    
    return classification.strip()

def categorize_diagnosis(classification: str) -> str:
    """
    Categorize a diagnosis into a high-level category for comparison.
    
    Args:
        classification: Classification string
        
    Returns:
        Category from DIAGNOSIS_CATEGORIES
    """
    normalized = normalize_classification(classification).lower()
    
    # APL variants
    if any(term in normalized for term in ['promyelocytic', 'pml', 'rara', 'apl']):
        return "APL"
    
    # AML with specific genetics
    if ('aml' in normalized and any(term in normalized for term in 
        ['npm1', 'runx1', 'cbfb', 'myh11', 'dek', 'nup214', 'rbm15', 'mrtfa', 
         'kmt2a', 'mecom', 'nup98', 'cebpa', 'bzip', 'bcr', 'abl1', 'mutated npm1',
         't(8;21)', 'inv(16)', 't(16;16)', 't(6;9)', 't(1;22)', 't(9;22)',
         'in-frame bzip mutated cebpa'])):
        return "AML_GENETIC"
    
    # AML myelodysplasia-related
    if ('aml' in normalized and 'myelodysplasia' in normalized):
        return "AML_MDS_RELATED"
    
    # Therapy-related
    if any(term in normalized for term in ['therapy related', 'previous cytotoxic', 'cytotoxic therapy', 'arising post mds']):
        return "AML_THERAPY_RELATED"
    
    # Erythroid leukemia (WHO-specific)
    if 'erythroid' in normalized and 'aml' in normalized:
        return "AML_ERYTHROID"
    
    # MDS with TP53
    if ('mds' in normalized and ('tp53' in normalized or 'biallelic tp53' in normalized)):
        return "MDS_TP53"
    
    # MDS with SF3B1
    if ('mds' in normalized and 'sf3b1' in normalized):
        return "MDS_SF3B1"
    
    # MDS with del(5q)
    if ('mds' in normalized and ('5q' in normalized or 'del(5q)' in normalized)):
        return "MDS_5Q"
    
    # MDS/AML hybrid (ICC-specific)
    if 'mds/aml' in normalized:
        return "MDS_AML_HYBRID"
    
    # MDS with blasts
    if ('mds' in normalized and any(term in normalized for term in ['blasts', 'excess blasts', 'increased blasts'])):
        return "MDS_BLASTS"
    
    # MDS with dysplasia
    if ('mds' in normalized and 'dysplasia' in normalized):
        return "MDS_DYSPLASIA"
    
    # Not AML
    if 'not aml' in normalized:
        return "NOT_AML"
    
    # MDS NOS/unclassifiable
    if ('mds' in normalized and ('nos' in normalized or 'unclassifiable' in normalized)):
        return "MDS_NOS"
    
    # AML NOS
    if ('aml' in normalized and ('nos' in normalized or 'define by differentiation' in normalized or 
        'unknown differentiation' in normalized or 'minimal differentiation' in normalized or
        'without maturation' in normalized or 'with maturation' in normalized or
        'myelomonocytic' in normalized or 'monoblastic' in normalized or 'monocytic' in normalized or
        'megakaryoblastic' in normalized)):
        return "AML_NOS"
    
    return "UNCLASSIFIABLE"

def are_equivalent_diagnoses(who_classification: str, icc_classification: str) -> bool:
    """
    Determine if two classifications from different systems represent the same diagnosis.
    
    Args:
        who_classification: WHO classification
        icc_classification: ICC classification
        
    Returns:
        True if diagnoses are considered equivalent
    """
    who_norm = normalize_classification(who_classification)
    icc_norm = normalize_classification(icc_classification)
    
    # Direct match
    if who_norm == icc_norm:
        return True
    
    # Check mapping tables
    if WHO_TO_ICC_MAPPINGS.get(who_norm) == icc_norm:
        return True
    
    if ICC_TO_WHO_MAPPINGS.get(icc_norm) == who_norm:
        return True
    
    # Category-based equivalence (but treat MDS/AML hybrid as distinct)
    who_category = categorize_diagnosis(who_classification)
    icc_category = categorize_diagnosis(icc_classification)
    
    # Special case: MDS/AML hybrid should not be equivalent to regular MDS_BLASTS
    if who_category == "MDS_BLASTS" and icc_category == "MDS_AML_HYBRID":
        return False
    if who_category == "MDS_AML_HYBRID" and icc_category == "MDS_BLASTS":
        return False
    
    return who_category == icc_category

def get_diagnosis_differences(who_classification: str, icc_classification: str) -> Dict[str, any]:
    """
    Analyze differences between WHO and ICC classifications with sophisticated clinical impact assessment.
    
    Args:
        who_classification: WHO classification
        icc_classification: ICC classification
        
    Returns:
        Dictionary describing the differences with clinical impact scoring
    """
    who_norm = normalize_classification(who_classification)
    icc_norm = normalize_classification(icc_classification)
    who_category = categorize_diagnosis(who_classification)
    icc_category = categorize_diagnosis(icc_classification)
    
    # Determine basic equivalence first
    basic_equivalence = are_equivalent_diagnoses(who_classification, icc_classification)
    
    # Extract key clinical features for impact assessment
    who_features = extract_clinical_features(who_classification)
    icc_features = extract_clinical_features(icc_classification)
    
    # Only calculate clinical impact for non-equivalent cases
    # For equivalent cases, impact should be minimal (terminology only)
    if basic_equivalence:
        # For equivalent cases, check if there are any meaningful terminology differences
        if who_norm.lower() != icc_norm.lower():
            # Minimal impact for terminology differences in equivalent diagnoses
            impact_analysis = {
                "significance": "minimal",
                "difference_type": "terminology_only",
                "impact_score": 0,
                "consequences": ["Terminology difference only - same clinical entity"],
                "treatment_differences": [],
                "mrd_differences": [],
                "prognostic_differences": []
            }
        else:
            # Identical classifications
            impact_analysis = {
                "significance": "minimal",
                "difference_type": "identical",
                "impact_score": 0,
                "consequences": [],
                "treatment_differences": [],
                "mrd_differences": [],
                "prognostic_differences": []
            }
    else:
        # Calculate sophisticated clinical impact for non-equivalent cases
        impact_analysis = calculate_clinical_impact(who_features, icc_features, who_classification, icc_classification)
    
    result = {
        "who_classification": who_norm,
        "icc_classification": icc_norm,
        "who_category": who_category,
        "icc_category": icc_category,
        "are_equivalent": basic_equivalence,
        "category_match": who_category == icc_category,
        "difference_type": impact_analysis["difference_type"],
        "significance": impact_analysis["significance"],
        "clinical_impact_score": impact_analysis["impact_score"],
        "clinical_consequences": impact_analysis["consequences"],
        "treatment_implications": impact_analysis["treatment_differences"],
        "mrd_implications": impact_analysis["mrd_differences"],
        "prognostic_implications": impact_analysis["prognostic_differences"]
    }
    
    return result

def extract_clinical_features(classification: str) -> Dict[str, any]:
    """Extract clinically relevant features from a classification string."""
    features = {
        "disease_type": "Unknown",
        "has_defining_genetics": False,
        "genetic_targets": [],
        "mrd_eligible_markers": [],
        "risk_category": "Unknown",
        "requires_intensive_therapy": False,
        "requires_targeted_therapy": False,
        "has_germline_implications": False,
        "requires_special_monitoring": False
    }
    
    classification_lower = classification.lower()
    
    # Disease type determination
    if any(term in classification_lower for term in ["aml", "acute myeloid", "acute erythroid", "acute promyelocytic"]):
        features["disease_type"] = "AML"
        features["requires_intensive_therapy"] = True
    elif any(term in classification_lower for term in ["mds", "myelodysplastic", "myelodysplasia"]):
        features["disease_type"] = "MDS" 
        features["requires_intensive_therapy"] = False
    
    # Genetic targets for precision therapy
    genetic_targets = {
        "flt3": ["flt3", "flt-3"],
        "idh1": ["idh1", "idh-1"],
        "idh2": ["idh2", "idh-2"], 
        "npm1": ["npm1"],
        "cebpa": ["cebpa", "bzip"],
        "kit": ["kit", "c-kit"],
        "tp53": ["tp53", "p53"]
    }
    
    for target, variants in genetic_targets.items():
        if any(variant in classification_lower for variant in variants):
            features["genetic_targets"].append(target)
            features["has_defining_genetics"] = True
            if target in ["flt3", "idh1", "idh2"]:
                features["requires_targeted_therapy"] = True
    
    # MRD monitoring eligibility
    mrd_markers = {
        "pml_rara": ["pml", "rara", "promyelocytic", "apl", "t(15;17)"],
        "npm1": ["npm1"],
        "runx1_runx1t1": ["runx1", "aml1", "eto", "t(8;21)"],
        "cbfb_myh11": ["cbfb", "myh11", "inv(16)", "t(16;16)"],
        "kmt2a": ["kmt2a", "mll", "11q23"],
        "bcr_abl1": ["bcr", "abl", "t(9;22)"],
        "dek_nup214": ["dek", "nup214", "t(6;9)"]
    }
    
    for marker, variants in mrd_markers.items():
        if any(variant in classification_lower for variant in variants):
            features["mrd_eligible_markers"].append(marker)
            if marker == "pml_rara":
                features["requires_special_monitoring"] = True
    
    # Germline implications
    germline_indicators = ["germline", "hereditary", "familial", "associated with germline", "in the setting of"]
    if any(indicator in classification_lower for indicator in germline_indicators):
        features["has_germline_implications"] = True
    
    # Risk category inference
    if "tp53" in classification_lower or "complex" in classification_lower:
        features["risk_category"] = "High"
    elif any(marker in features["mrd_eligible_markers"] for marker in ["npm1", "runx1_runx1t1", "cbfb_myh11"]):
        features["risk_category"] = "Favorable"
    elif features["disease_type"] == "AML":
        features["risk_category"] = "Intermediate"
    
    return features

def calculate_clinical_impact(who_features: Dict, icc_features: Dict, who_class: str, icc_class: str) -> Dict[str, any]:
    """Calculate sophisticated clinical impact of classification differences."""
    
    impact_score = 0
    consequences = []
    treatment_differences = []
    mrd_differences = []
    prognostic_differences = []
    
    # 1. TREATMENT IMPACT ASSESSMENT (Most Critical)
    
    # Disease type disagreement (AML vs MDS) - MEDIUM IMPACT (further reduced)
    if who_features["disease_type"] != icc_features["disease_type"]:
        if {who_features["disease_type"], icc_features["disease_type"]} == {"AML", "MDS"}:
            impact_score += 35  # Further reduced from 45 to keep more in medium range
            consequences.append("Fundamental disease classification disagreement")
            treatment_differences.append("Intensive chemotherapy vs supportive care")
            treatment_differences.append("Stem cell transplant eligibility differs")
            treatment_differences.append("Clinical trial eligibility differs")
    
    # APL vs other AML - CRITICAL IMPACT (reduce slightly)
    apl_indicators = ["promyelocytic", "pml", "rara", "apl", "t(15;17)"]
    who_is_apl = any(indicator in who_class.lower() for indicator in apl_indicators)
    icc_is_apl = any(indicator in icc_class.lower() for indicator in apl_indicators)
    
    if who_is_apl != icc_is_apl:
        impact_score += 80  # Reduced from 90 to create more room for other factors
        consequences.append("APL vs non-APL AML disagreement")
        treatment_differences.append("ATRA/arsenic therapy vs standard chemotherapy")
        treatment_differences.append("Different bleeding precautions required")
        treatment_differences.append("Emergency treatment protocols differ")
    
    # Targeted therapy eligibility differences - MEDIUM IMPACT (reduced)
    who_targets = set(who_features["genetic_targets"])
    icc_targets = set(icc_features["genetic_targets"])
    target_differences = who_targets.symmetric_difference(icc_targets)
    
    if target_differences:
        impact_score += 25  # Further reduced from 35 to solidly medium range
        consequences.append(f"Targeted therapy eligibility differs: {target_differences}")
        for target in target_differences:
            if target == "flt3":
                treatment_differences.append("FLT3 inhibitor eligibility (midostaurin, quizartinib)")
            elif target in ["idh1", "idh2"]:
                treatment_differences.append("IDH inhibitor eligibility (ivosidenib, enasidenib)")
            elif target == "tp53":
                treatment_differences.append("TP53-directed therapy considerations")
    
    # 2. MRD MONITORING IMPACT ASSESSMENT
    
    who_mrd = set(who_features["mrd_eligible_markers"])
    icc_mrd = set(icc_features["mrd_eligible_markers"])
    mrd_marker_differences = who_mrd.symmetric_difference(icc_mrd)
    
    if mrd_marker_differences:
        # PML-RARA has highest MRD impact
        if "pml_rara" in mrd_marker_differences:
            impact_score += 35  # Reduced from 45
            mrd_differences.append("PML-RARA RT-PCR monitoring vs flow cytometry only")
            mrd_differences.append("Different response assessment criteria")
        
        # Other molecular markers - MEDIUM IMPACT
        molecular_markers = {"npm1", "runx1_runx1t1", "cbfb_myh11", "kmt2a", "bcr_abl1"}
        if molecular_markers.intersection(mrd_marker_differences):
            impact_score += 20  # Reduced from 25
            mrd_differences.append("Molecular vs flow cytometry MRD monitoring")
            mrd_differences.append("Different sensitivity and specificity")
    
    # No MRD markers in either classification
    if not who_mrd and not icc_mrd and who_features["disease_type"] == "AML":
        mrd_differences.append("Flow cytometry MRD only for both classifications")
    
    # 3. PROGNOSTIC IMPACT ASSESSMENT (Further reduced)
    
    # Risk category differences - more conservative scoring
    if who_features["risk_category"] != icc_features["risk_category"]:
        risk_impact = {
            ("High", "Favorable"): 30,  # Further reduced from 40
            ("High", "Intermediate"): 20,  # Further reduced from 30
            ("Intermediate", "Favorable"): 15,  # Reduced from 25
            ("High", "Unknown"): 15,  # Reduced from 20
            ("Intermediate", "Unknown"): 10,  # Reduced from 15
            ("Favorable", "Unknown"): 5   # Reduced from 10
        }
        
        risk_pair = (who_features["risk_category"], icc_features["risk_category"])
        reverse_pair = (icc_features["risk_category"], who_features["risk_category"])
        
        impact_value = risk_impact.get(risk_pair, risk_impact.get(reverse_pair, 0))
        impact_score += impact_value
        
        if impact_value > 0:
            prognostic_differences.append(f"Risk category: {who_features['risk_category']} vs {icc_features['risk_category']}")
            prognostic_differences.append("Different survival expectations")
            prognostic_differences.append("Different treatment intensity recommendations")
    
    # 4. TERMINOLOGY AND CLASSIFICATION REFINEMENTS (Reduced)
    
    # Subtype differences within same disease type - MEDIUM IMPACT (reduced)
    if who_features["disease_type"] == icc_features["disease_type"]:
        # Same disease type but different subtypes
        if who_class.lower() != icc_class.lower():
            # Check for meaningful subtype differences
            terminology_indicators = ["with", "nos", "unclassifiable", "mutated", "related"]
            who_has_detail = any(indicator in who_class.lower() for indicator in terminology_indicators)
            icc_has_detail = any(indicator in icc_class.lower() for indicator in terminology_indicators)
            
            if who_has_detail or icc_has_detail:
                impact_score += 20  # Reduced from 30
                consequences.append("Subtype classification differences within same disease category")
                prognostic_differences.append("Potentially different prognosis within disease type")
                
                # Additional scoring for specific meaningful differences (reduced)
                meaningful_differences = [
                    ("increased blasts", "excess blasts"),
                    ("low blasts", "with low blasts"),
                    ("unclassifiable", "nos"),
                    ("biallelic tp53", "mutated tp53"),
                    ("sf3b1", "mutated sf3b1")
                ]
                
                for who_term, icc_term in meaningful_differences:
                    if who_term in who_class.lower() and icc_term in icc_class.lower():
                        impact_score += 5  # Reduced from 10
                        consequences.append(f"Specific terminology difference: {who_term} vs {icc_term}")
                        break
    
    # 5. SPECIAL CLINICAL CONSIDERATIONS (Reduced)
    
    # Germline implications
    if who_features["has_germline_implications"] != icc_features["has_germline_implications"]:
        impact_score += 15  # Reduced from 20
        consequences.append("Germline implications differ")
        treatment_differences.append("Family screening recommendations differ")
        treatment_differences.append("Drug toxicity considerations differ")
    
    # Pediatric vs adult protocols (inferred from classification patterns)
    pediatric_indicators = ["pediatric", "childhood", "infant", "young"]
    who_pediatric = any(indicator in who_class.lower() for indicator in pediatric_indicators)
    icc_pediatric = any(indicator in icc_class.lower() for indicator in pediatric_indicators)
    
    if who_pediatric != icc_pediatric:
        impact_score += 10  # Reduced from 15
        consequences.append("Pediatric vs adult protocol eligibility")
        treatment_differences.append("Age-specific treatment protocols")
    
    # 6. THERAPY-RELATED DIFFERENCES (Reduced)
    
    # Check for therapy-related differences in classification text
    therapy_indicators = ["therapy", "treatment", "related", "secondary"]
    who_therapy = any(indicator in who_class.lower() for indicator in therapy_indicators)
    icc_therapy = any(indicator in icc_class.lower() for indicator in therapy_indicators)
    
    if who_therapy != icc_therapy:
        impact_score += 15  # Reduced from 25
        consequences.append("Therapy-related classification differs")
        treatment_differences.append("Different approach to therapy-related disease")
        prognostic_differences.append("Different prognosis for therapy-related vs de novo disease")
    
    # 7. BLAST PERCENTAGE TERMINOLOGY DIFFERENCES (Reduced)
    
    # Different blast percentage terminology but same disease type
    blast_indicators = ["increased blasts", "excess blasts", "low blasts", "blasts 1", "blasts 2"]
    who_blast_terms = [term for term in blast_indicators if term in who_class.lower()]
    icc_blast_terms = [term for term in blast_indicators if term in icc_class.lower()]
    
    if who_blast_terms != icc_blast_terms and who_features["disease_type"] == icc_features["disease_type"]:
        impact_score += 10  # Reduced from 20
        consequences.append("Blast percentage terminology differs")
        prognostic_differences.append("Different blast count implications for prognosis")
    
    # 8. GENETIC MARKER TERMINOLOGY DIFFERENCES (Reduced)
    
    # Different genetic marker terminology
    genetic_terms = ["biallelic", "mutated", "with", "related"]
    who_genetic_terms = [term for term in genetic_terms if term in who_class.lower()]
    icc_genetic_terms = [term for term in genetic_terms if term in icc_class.lower()]
    
    if who_genetic_terms != icc_genetic_terms and who_features["disease_type"] == icc_features["disease_type"]:
        impact_score += 10  # Reduced from 15
        consequences.append("Genetic marker terminology differs")
        mrd_differences.append("Different genetic marker identification may affect MRD strategy")
    
    # 9. DETERMINE FINAL SIGNIFICANCE LEVEL (Adjusted thresholds)
    
    if impact_score >= 80:
        significance = "critical"
        difference_type = "major_clinical_impact"
    elif impact_score >= 50:
        significance = "high"
        difference_type = "significant_clinical_impact"
    elif impact_score >= 25:
        significance = "medium"
        difference_type = "moderate_clinical_impact"
    elif impact_score > 0:
        significance = "low"
        difference_type = "minor_clinical_impact"
    else:
        significance = "minimal"
        difference_type = "terminology_only"
    
    return {
        "significance": significance,
        "difference_type": difference_type,
        "impact_score": impact_score,
        "consequences": consequences,
        "treatment_differences": treatment_differences,
        "mrd_differences": mrd_differences,
        "prognostic_differences": prognostic_differences
    }

def get_test_focus_areas() -> Dict[str, Dict]:
    """
    Return areas where WHO and ICC are most likely to differ, for focused testing.
    
    Returns:
        Dictionary of test focus areas with parameters
    """
    return {
        "blast_thresholds": {
            "description": "Different blast percentage requirements for AML diagnosis",
            "key_ranges": [10, 15, 19, 20, 25],
            "key_genes": ["CEBPA", "bZIP", "BCR::ABL1"],
            "expected_differences": "ICC allows AML diagnosis at ≥10% for defining abnormalities, WHO requires ≥20% for CEBPA/bZIP/BCR::ABL1"
        },
        
        "therapy_qualifiers": {
            "description": "Different accepted therapy types for qualifiers",
            "key_types": ["Immune interventions (ICC)", "Cytotoxic chemotherapy", "Ionising radiation"],
            "expected_differences": "ICC accepts 'Immune interventions', WHO does not"
        },
        
        "germline_qualifiers": {
            "description": "Different terminology for germline associations",
            "key_phrases": ["associated with", "in the setting of", "Diamond-Blackfan anemia", "germline BLM mutation"],
            "expected_differences": "WHO uses 'associated with', ICC uses 'in the setting of'; different exclusion criteria"
        },
        
        "tp53_terminology": {
            "description": "Different naming conventions for TP53 abnormalities",
            "who_term": "Biallelic TP53 inactivation",
            "icc_term": "Mutated TP53",
            "expected_differences": "Terminology differences for same biological entity"
        },
        
        "mds_blast_ranges": {
            "description": "Different MDS classifications for blast ranges",
            "key_ranges": [10, 15, 19],
            "expected_differences": "Different handling of 10-19% blast range in MDS context"
        },
        
        "erythroid_handling": {
            "description": "Different criteria for erythroid leukemia classification",
            "key_features": ["erythroid precursors", "dysplastic changes", "blast percentage"],
            "expected_differences": "Different thresholds and criteria for acute erythroid leukemia"
        },
        
        "realistic_clinical_scenarios": {
            "description": "Common real-world presentations that may cause disagreements",
            "scenarios": ["elderly_mds_with_tp53", "young_aml_with_germline", "therapy_related_complex"],
            "expected_differences": "Real-world complexity often reveals subtle classification differences"
        },
        
        "age_dependent_differences": {
            "description": "Age-related considerations in classification",
            "age_groups": ["pediatric", "young_adult", "elderly"],
            "expected_differences": "Age-specific criteria may lead to different classifications"
        },
        
        "complex_cytogenetics": {
            "description": "Complex karyotype interpretations",
            "features": ["complex_karyotype", "multiple_abnormalities", "rare_translocations"],
            "expected_differences": "Different handling of complex cytogenetic abnormalities"
        },
        
        "comutation_patterns": {
            "description": "Co-occurring mutation combinations",
            "patterns": ["TP53_plus_complex", "NPM1_plus_FLT3", "splicing_mutations"],
            "expected_differences": "Different weighting of mutation combinations"
        },
        
        "therapy_evolution": {
            "description": "Disease evolution in therapy-related cases",
            "evolution_types": ["MDS_to_AML", "therapy_related_progression", "clonal_evolution"],
            "expected_differences": "Different criteria for therapy-related disease evolution"
        },
        
        "aml_vs_mds_borderline": {
            "description": "Cases specifically targeting AML vs MDS classification disagreements",
            "key_scenarios": [
                "blast_15_with_aml_defining_mutations",
                "blast_19_with_extensive_dysplasia", 
                "therapy_related_borderline_cases",
                "erythroid_predominant_cases",
                "mixed_feature_cases"
            ],
            "expected_differences": "High likelihood of AML vs MDS disagreement due to borderline blast counts with competing features",
            "clinical_significance": "Critical for treatment decisions - AML vs MDS determines therapeutic approach"
        },
        
        "disease_type_disagreement": {
            "description": "Cases designed to cause disease type disagreements (AML vs MDS)",
            "disagreement_types": [
                "who_aml_icc_mds", 
                "who_mds_icc_aml",
                "therapy_related_ambiguous"
            ],
            "target_scenarios": [
                "20% blasts with extensive dysplasia",
                "15% blasts with CEBPA bZIP mutation",
                "borderline cases with ring sideroblasts",
                "therapy-related cases with immune interventions"
            ],
            "expected_differences": "Systematic disagreements on fundamental disease classification",
            "clinical_significance": "Maximum clinical impact - affects choice of intensive vs supportive care"
        }
    }

# Utility functions for test case generation
def generate_blast_test_cases() -> List[Dict]:
    """Generate test cases focusing on blast percentage differences."""
    test_cases = []
    
    # Critical blast percentages where WHO/ICC might differ
    blast_values = [9, 10, 15, 19, 20, 25]
    critical_genes = ["CEBPA", "bZIP", "BCR::ABL1", "NPM1"]
    
    for blast_pct in blast_values:
        for gene in critical_genes:
            test_case = {
                "blasts_percentage": blast_pct,
                "AML_defining_recurrent_genetic_abnormalities": {gene: True},
                "qualifiers": {},
                "test_focus": "blast_thresholds",
                "expected_difference": blast_pct < 20 and gene in ["CEBPA", "bZIP", "BCR::ABL1"]
            }
            test_cases.append(test_case)
    
    return test_cases

def generate_therapy_test_cases() -> List[Dict]:
    """Generate test cases focusing on therapy qualifier differences."""
    test_cases = []
    
    therapies = ["Immune interventions", "Ionising radiation", "Cytotoxic chemotherapy", "Any combination", "None"]
    base_genetics = [
        {"NPM1": True},
        {"RUNX1::RUNX1T1": True},
        {}  # No defining genetics
    ]
    
    for therapy in therapies:
        for genetics in base_genetics:
            test_case = {
                "blasts_percentage": 25.0,
                "AML_defining_recurrent_genetic_abnormalities": genetics,
                "qualifiers": {"previous_cytotoxic_therapy": therapy},
                "test_focus": "therapy_qualifiers",
                "expected_difference": therapy == "Immune interventions"
            }
            test_cases.append(test_case)
    
    return test_cases

def generate_germline_test_cases() -> List[Dict]:
    """Generate test cases focusing on germline variant differences."""
    test_cases = []
    
    variants = [
        "Diamond-Blackfan anemia",
        "germline BLM mutation", 
        "germline CEBPA mutation",
        "germline DDX41 mutation",
        "Fanconi anaemia"
    ]
    
    for variant in variants:
        test_case = {
            "blasts_percentage": 30.0,
            "AML_defining_recurrent_genetic_abnormalities": {"NPM1": True},
            "qualifiers": {"predisposing_germline_variant": variant},
            "test_focus": "germline_qualifiers", 
            "expected_difference": variant in ["Diamond-Blackfan anemia", "germline BLM mutation"]
        }
        test_cases.append(test_case)
    
    return test_cases 