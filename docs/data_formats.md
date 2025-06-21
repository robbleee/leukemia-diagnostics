# Haem.io Data Formats Documentation

## Overview

This document defines all data formats, schemas, and structures used throughout the Haem.io platform. Understanding these formats is essential for developers working with the system and for users preparing data inputs.

## Input Data Formats

### Raw Report Text

**Format**: Plain text string
**Description**: Unstructured medical reports uploaded by users

**Example**:
```
Flow cytometry results:
CD33: 85% positive
CD117: 70% positive
NPM1 mutation detected
FLT3-ITD: Positive (ratio 0.7)
Blast percentage: 42%
Karyotype: Normal male karyotype 46,XY
```

### Manual Entry Data

**Format**: Dictionary with structured fields
**Description**: Data entered through Streamlit forms

```python
{
    "blasts_percentage": 42.0,
    "age": 65,
    "gender": "Male",
    "ecog_status": 1,
    "genetic_markers": {
        "NPM1_mutation": True,
        "FLT3_ITD": True,
        "CEBPA_mutation": False
    },
    "cytogenetics": {
        "karyotype": "46,XY",
        "risk_category": "Normal"
    },
    "clinical_history": {
        "newly_diagnosed": True,
        "prior_mds": False,
        "therapy_related": False
    }
}
```

## Parsed Data Schemas

### AML Parsed Data

```python
{
    "blasts_percentage": float,                    # 0-100
    "age": int,                                   # Patient age
    "AML_defining_recurrent_genetic_abnormalities": {
        "NPM1_mutation": bool,
        "FLT3_ITD": bool,
        "FLT3_TKD": bool,
        "CEBPA_mutation": bool,
        "RUNX1_RUNX1T1": bool,                   # t(8;21)
        "CBFB_MYH11": bool,                      # inv(16)/t(16;16)
        "PML_RARA": bool,                        # t(15;17)
        "KMT2A_rearranged": bool,                # 11q23 rearrangements
        "DEK_NUP214": bool,                      # t(6;9)
        "BCR_ABL1": bool                         # t(9;22)
    },
    "MDS_related_mutation": {
        "SF3B1": bool,
        "SRSF2": bool,
        "U2AF1": bool,
        "ASXL1": bool,
        "EZH2": bool,
        "TET2": bool,
        "DNMT3A": bool,
        "IDH1": bool,
        "IDH2": bool,
        "RUNX1": bool,
        "TP53": bool
    },
    "ELN2024_risk_genes": {
        "FLT3_ITD": bool,
        "FLT3_TKD": bool,
        "NPM1": bool,
        "CEBPA": bool,
        "TP53": bool,
        "ASXL1": bool,
        "RUNX1": bool
    },
    "MDS_related_cytogenetics": {
        "complex_karyotype": bool,
        "monosomal_karyotype": bool,
        "del_5q": bool,
        "del_7q": bool,
        "del_17p": bool,
        "inv_3": bool,
        "t_3_3": bool
    },
    "Biallelic_TP53_mutation": {
        "TP53_mutation": bool,
        "del_17p": bool,
        "complex_karyotype": bool
    },
    "qualifiers": {
        "previous_MDS_diagnosed_over_3_months_ago": bool,
        "previous_cytotoxic_therapy": str,         # "None", "Yes", details
        "previous_MPN": bool,
        "relapsed_refractory": bool
    },
    "morphology": {
        "multilineage_dysplasia": bool,
        "erythroid_dysplasia": bool,
        "granulocytic_dysplasia": bool,
        "megakaryocytic_dysplasia": bool
    },
    "AML_differentiation": str                     # "Well", "Moderate", "Poor"
}
```

### MDS Parsed Data

```python
{
    "blasts_percentage": float,
    "age": int,
    "MDS_related_mutation": {
        "SF3B1": bool,
        "SRSF2": bool,
        "U2AF1": bool,
        "ZRSR2": bool,
        "ASXL1": bool,
        "EZH2": bool,
        "BCOR": bool,
        "STAG2": bool,
        "TET2": bool,
        "DNMT3A": bool,
        "IDH1": bool,
        "IDH2": bool,
        "RUNX1": bool,
        "TP53": bool
    },
    "cytogenetics": {
        "karyotype": str,
        "risk_category": str,                      # "Very Good", "Good", "Intermediate", "Poor", "Very Poor"
        "complex_karyotype": bool,
        "chromosome_abnormalities": List[str]
    },
    "cytopenias": {
        "hemoglobin": float,                       # g/dL
        "neutrophils": float,                      # K/µL  
        "platelets": float                         # K/µL
    },
    "morphology": {
        "ring_sideroblasts_percentage": float,
        "multilineage_dysplasia": bool,
        "erythroid_dysplasia": bool,
        "granulocytic_dysplasia": bool,
        "megakaryocytic_dysplasia": bool
    },
    "clinical_features": {
        "transfusion_dependent": bool,
        "time_from_diagnosis_months": int,
        "bone_marrow_fibrosis_grade": int          # 0-3
    }
}
```

### Treatment Parser Data

```python
{
    "patient_qualifiers": {
        "therapy_related": bool,
        "previous_MDS": bool,
        "previous_MPN": bool,
        "relapsed_refractory": bool,
        "newly_diagnosed": bool
    },
    "cd33_data": {
        "cd33_positive": bool,                     # ≥20% threshold
        "cd33_percentage": float,                  # 0-100
        "flow_cytometry_available": bool
    },
    "genetic_abnormalities": {
        # Same structure as AML parser
        "AML_defining_recurrent_genetic_abnormalities": Dict,
        "MDS_related_mutation": Dict
    },
    "morphologic_features": {
        "multilineage_dysplasia": bool,
        "mds_related_changes": bool,
        "blast_percentage": float
    },
    "cytogenetic_data": {
        "favorable_cytogenetics": bool,
        "intermediate_cytogenetics": bool,
        "adverse_cytogenetics": bool,
        "complex_karyotype": bool
    }
}
```

## Classification Output Formats

### Classification Results

```python
{
    "who_class": str,                              # WHO 2022 classification
    "icc_class": str,                              # ICC 2022 classification  
    "confidence": float,                           # 0.0-1.0
    "who_disease_type": str,                       # "AML", "MDS", "Other"
    "icc_disease_type": str,
    "classification_rationale": str,
    "alternative_diagnoses": List[Dict],
    "parsed_data": Dict,                           # Original parsed data
    "processing_timestamp": str
}
```

### Alternative Diagnoses Format

```python
{
    "diagnosis": str,
    "confidence": float,
    "rationale": str,
    "supporting_features": List[str],
    "contradicting_features": List[str]
}
```

## Risk Assessment Formats

### ELN Risk Assessment

```python
{
    "risk_category": str,                          # "Favorable", "Intermediate", "Adverse"
    "risk_score": int,                             # Numeric score
    "risk_factors": List[str],                     # Contributing factors
    "molecular_markers": {
        "favorable": List[str],
        "intermediate": List[str], 
        "adverse": List[str]
    },
    "cytogenetic_risk": str,                       # Risk from cytogenetics alone
    "age_category": str,                           # "≤60", ">60"
    "fitness_category": str,                       # "Fit", "Unfit"
    "treatment_recommendation": str,
    "survival_estimates": {
        "overall_survival_months": float,
        "disease_free_survival_months": float,
        "confidence_interval": str
    }
}
```

### IPSS Risk Assessment

```python
{
    "ipss_score": float,                           # Total IPSS score
    "risk_category": str,                          # "Very Low", "Low", "Intermediate", "High", "Very High"
    "component_scores": {
        "blast_score": float,                      # 0-2
        "cytogenetic_score": float,                # 0-4
        "cytopenias_score": float                  # 0-3
    },
    "survival_estimates": {
        "median_survival_months": float,
        "25th_percentile_months": float,
        "75th_percentile_months": float
    },
    "transformation_risk": {
        "aml_transformation_risk_25_percent": float # Months to 25% AML transformation
    },
    "prognostic_factors": List[str]
}
```

### IPSS-M Risk Assessment

```python
{
    "ipssm_score": float,
    "risk_category": str,
    "molecular_score": float,                      # Additional molecular component
    "molecular_markers": Dict,                     # Contributing molecular markers
    "survival_estimates": {
        "median_survival_months": float,
        "molecular_contribution": str              # Impact of molecular markers
    }
}
```

## Treatment Recommendation Formats

### Treatment Eligibility

```python
{
    "eligible_treatments": List[str],
    "treatment_details": {
        "DA": {
            "eligible": bool,
            "rationale": str,
            "contraindications": List[str],
            "age_appropriate": bool,
            "fitness_required": str
        },
        "DA+GO": {
            "eligible": bool,
            "cd33_requirement": bool,
            "cd33_percentage": float,
            "cytogenetic_eligibility": bool
        },
        "DA+Midostaurin": {
            "eligible": bool,
            "flt3_mutation_required": bool,
            "flt3_status": str
        },
        "CPX-351": {
            "eligible": bool,
            "indication": str,                     # "MDS-related changes", "Therapy-related"
            "age_criteria": bool
        },
        "Azacitidine+Venetoclax": {
            "eligible": bool,
            "indication": str
        }
    },
    "consensus_recommendation": str,
    "alternative_options": List[str],
    "clinical_trial_recommendation": bool,
    "supportive_care_considerations": List[str]
}
```

## Clinical Trial Formats

### Trial Database Schema

```json
{
  "title": "string",
  "description": "string",
  "cancer_types": ["string"],
  "status": "string",                             // "open", "closed", "recruiting"
  "locations": ["string"],
  "countries": ["string"],
  "who_can_enter": "string",                      // Eligibility criteria text
  "link": "string",                               // URL to trial registry
  "sponsor": "string",
  "phase": "string",                              // "Phase I", "Phase II", etc.
  "intervention": "string",
  "primary_outcome": "string",
  "estimated_enrollment": number,
  "age_minimum": number,
  "age_maximum": number,
  "gender": "string",                             // "All", "Male", "Female"
  "last_updated": "ISO8601 datetime"
}
```

### Trial Matching Results

```python
{
    "relevance_score": int,                        # 0-100
    "recommendation": str,                         # "recommend", "consider", "not_suitable"
    "explanation": str,                            # AI-generated rationale
    "matching_factors": List[str],                 # Why patient matches
    "exclusion_factors": List[str],                # Potential exclusions
    "trial_details": Dict,                         # Full trial information
    "detailed_recommendation": str,                # Enhanced analysis for top trials
    "key_strengths": List[str],
    "potential_concerns": List[str],
    "next_steps": str,
    "priority_level": str                          # "high", "medium", "low"
}
```

## Report Generation Formats

### PDF Report Data

```python
{
    "patient_info": {
        "age": int,
        "gender": str,
        "report_date": str,
        "case_id": str                             # Optional anonymized ID
    },
    "classification_summary": {
        "primary_diagnosis": str,
        "confidence_score": float,
        "diagnostic_certainty": str
    },
    "genetic_findings": {
        "key_mutations": List[str],
        "cytogenetic_abnormalities": List[str],
        "molecular_risk_factors": List[str]
    },
    "risk_assessment": {
        "risk_category": str,
        "prognostic_score": float,
        "survival_estimate": str,
        "risk_stratification_rationale": str
    },
    "treatment_recommendations": {
        "primary_recommendation": str,
        "alternative_options": List[str],
        "clinical_trial_options": List[Dict],
        "contraindications": List[str]
    },
    "clinical_notes": {
        "additional_comments": str,
        "follow_up_recommendations": str,
        "monitoring_suggestions": str
    }
}
```

## Error and Validation Formats

### Error Response Format

```python
{
    "error_type": str,                             # "ParseError", "ValidationError", "APIError"
    "error_message": str,
    "error_details": Dict,
    "suggestions": List[str],                      # User-actionable suggestions
    "fallback_options": List[str],                 # Alternative approaches
    "timestamp": str,
    "request_id": str                              # For debugging
}
```

### Validation Result Format

```python
{
    "is_valid": bool,
    "validation_errors": List[Dict],
    "validation_warnings": List[Dict],
    "missing_fields": List[str],
    "invalid_values": Dict,                        # Field -> error description
    "data_quality_score": float                    # 0.0-1.0
}
```

### Validation Error Detail

```python
{
    "field": str,                                  # Field name with error
    "error_type": str,                             # "missing", "invalid_range", "invalid_type"
    "current_value": Any,
    "expected_value": str,                         # Description of expected value
    "severity": str                                # "error", "warning", "info"
}
```

## File Upload Formats

### Supported File Types

- **Text Files**: `.txt`, `.rtf`
- **PDF Files**: `.pdf` (text extraction)
- **Image Files**: `.jpg`, `.png` (OCR processing)
- **Word Documents**: `.docx` (limited support)

### File Metadata

```python
{
    "filename": str,
    "file_size": int,                              # Bytes
    "file_type": str,                              # MIME type
    "upload_timestamp": str,
    "processing_status": str,                      # "pending", "processing", "completed", "failed"
    "extracted_text": str,
    "extraction_confidence": float,                # 0.0-1.0 for OCR quality
    "extraction_method": str                       # "direct", "ocr", "pdf_extract"
}
```

## Configuration Formats

### Secrets Configuration

```toml
# .streamlit/secrets.toml
[auth]
users = [
    {username = "string", hashed_password = "string"}
]

[openai]
api_key = "string"

[general]
cookie_password = "string"

[jwt]
secret_key = "string"
expiration_hours = number
```

### Application Configuration

```toml
# .streamlit/config.toml
[server]
port = number
headless = boolean
enableCORS = boolean

[browser]
gatherUsageStats = boolean

[theme]
primaryColor = "string"
backgroundColor = "string"
secondaryBackgroundColor = "string"
```

## API Communication Formats

### OpenAI Request Format

```python
{
    "model": "gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": "string"
        },
        {
            "role": "user", 
            "content": "string"
        }
    ],
    "temperature": float,                          # 0.0-2.0
    "max_tokens": int,
    "response_format": {"type": "json_object"}     # For structured outputs
}
```

### Session State Format

```python
{
    "user_authenticated": bool,
    "jwt_token": str,
    "username": str,
    "login_timestamp": str,
    "parsed_data": Dict,
    "classification_results": Dict,
    "risk_assessment_results": Dict,
    "treatment_recommendations": Dict,
    "matched_trials": List[Dict],
    "pdf_report_data": Dict,
    "processing_history": List[Dict],              # Audit trail
    "user_preferences": Dict,
    "debug_mode": bool
}
```

This comprehensive data format documentation serves as the authoritative reference for all data structures used in the Haem.io platform. Developers should consult this document when working with any data processing, validation, or transformation tasks. 