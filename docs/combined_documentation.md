# Haem.io - Comprehensive Documentation

**Version**: 1.0  
**Date**: December 2024  
**Platform**: Blood Cancer Classification & Clinical Decision Support

---

## Table of Contents

1. [Application Functionality](#application-functionality)
2. [Classification Algorithms](#classification-algorithms)
3. [Clinical Trial Matching System](#clinical-trial-matching-system)
4. [Data Formats](#data-formats)
5. [Developer Guide](#developer-guide)
6. [Technical Architecture](#technical-architecture)
7. [Treatment Parser Integration](#treatment-parser-integration)
8. [User Manual](#user-manual)

---

# Application Functionality

## Overview

Haem.io is a comprehensive web-based application for classifying haematologic malignancies, providing healthcare professionals and researchers with advanced tools for blood cancer diagnosis, risk assessment, and treatment planning. The platform combines automated classification algorithms with AI-powered clinical insights to deliver professional-grade oncology decision support with complete transparency and clinical reasoning.

## 1. Core Platform Features

### Web-Based Clinical Decision Support
- **Accessibility**: Browser-based application requiring no software installation
- **Cross-Platform**: Compatible with desktop, tablet, and mobile devices
- **Real-Time Processing**: Instant classification results and comprehensive analysis
- **Session Management**: Maintains user data throughout the complete workflow
- **Multi-Language Support**: International accessibility for global healthcare teams

### Advanced Security Infrastructure
- **User Authentication**: Secure login system with encrypted password storage
- **JWT Token Management**: Session-based security with automatic expiration
- **Encrypted Cookies**: Secure data transmission and storage
- **bcrypt Password Hashing**: Industry-standard password protection
- **Protected Routes**: Controlled access to sensitive medical information
- **HIPAA Compliance**: Medical-grade data protection standards
- **Session Isolation**: Complete data separation between users

### Interactive Clinical Interface
- **Modern UI Design**: Clean, intuitive medical-grade user interface
- **Responsive Layout**: Optimized for various screen sizes and devices
- **Multi-Step Workflow**: Guided process from data entry through final recommendations
- **Real-Time Feedback**: Immediate validation and progress indicators
- **Interactive Visualizations**: Dynamic charts, flowcharts, and classification trees
- **Customizable Dashboard**: Personalized view of patient data and results
- **Export Functionality**: Multiple format options for clinical documentation

## 2. Comprehensive Classification System

### Supported Malignancies (26 Total Disease Types)
The platform provides expert-level classification for the complete spectrum of haematologic malignancies:

#### Acute Leukemias
- **Acute Myeloid Leukemia (AML)** - All WHO/ICC subtypes including:
  - AML with recurrent genetic abnormalities (NPM1, CEBPA, CBF, PML-RARA, KMT2A)
  - AML with myelodysplasia-related changes
  - Therapy-related myeloid neoplasms
  - AML, not otherwise specified
- **Acute Lymphoblastic Leukemia (ALL)** - B-cell and T-cell lineages with molecular subtypes

#### Myelodysplastic Syndromes (MDS)
- **MDS with ring sideroblasts** (with/without SF3B1 mutation)
- **MDS with multilineage dysplasia**
- **MDS with single lineage dysplasia**
- **MDS with excess blasts-1 and excess blasts-2**
- **MDS with isolated del(5q)**
- **MDS, unclassifiable**

#### Myeloproliferative Neoplasms
- **Chronic Myeloid Leukemia (CML)**
- **Polycythemia Vera (PV)**
- **Essential Thrombocythemia (ET)**
- **Primary Myelofibrosis (PMF)**

#### Lymphoid Malignancies
- **B-Cell Lymphomas** - DLBCL, follicular lymphoma, mantle cell lymphoma, marginal zone lymphomas
- **T-Cell Lymphomas** - Peripheral T-cell lymphomas, anaplastic large cell lymphoma
- **Hodgkin Lymphoma** - Classical and nodular lymphocyte-predominant types
- **Chronic Lymphocytic Leukemia (CLL)** and variants
- **Hairy Cell Leukemia** and variants

#### Plasma Cell Disorders
- **Multiple Myeloma** and variants
- **Plasmacytoma**
- **Plasma cell leukemia**

#### Rare Entities
- **Histiocytic and Dendritic Cell Neoplasms**
- **Mastocytosis**
- **Blastic Plasmacytoid Dendritic Cell Neoplasm**

### Dual Classification Standards
- **WHO 2022 Classification**: Latest World Health Organization international standards
- **ICC 2022 Classification**: International Consensus Classification with molecular enhancements
- **Side-by-Side Comparison**: Direct comparison of WHO vs ICC classifications
- **Evidence-Based Algorithms**: Peer-reviewed classification criteria with literature references
- **Regular Updates**: Maintained with current medical guidelines and consensus statements

### Advanced Classification Features
- **Confidence Scoring**: Statistical reliability assessment (0-100% confidence)
- **Alternative Diagnoses**: Ranked list of differential diagnoses with rationale
- **Borderline Cases**: Special handling for diagnostically challenging cases
- **Molecular Integration**: Genetic/cytogenetic data fully integrated into classification logic

## 3. Comprehensive Data Processing Pipeline

### Multiple Specialized Parsers
The platform employs specialized AI parsers optimized for different data types:

#### AML Genetic Parser
- **Targeted Extraction**: AML-defining genetic abnormalities (NPM1, FLT3, CEBPA, CBF, PML-RARA, KMT2A, etc.)
- **MDS-Related Mutations**: SF3B1, SRSF2, U2AF1, ASXL1, EZH2, TET2, DNMT3A, IDH1/2, RUNX1, TP53
- **Cytogenetic Analysis**: Complex karyotype, monosomal karyotype, specific translocations
- **Morphologic Features**: Blast percentage, multilineage dysplasia assessment

#### MDS Genetic Parser
- **MDS-Specific Mutations**: Complete panel of MDS-associated genes
- **Ring Sideroblast Quantification**: Precise percentage extraction
- **Cytogenetic Risk Assessment**: IPSS cytogenetic risk categorization
- **Dysplastic Lineage Analysis**: Erythroid, granulocytic, megakaryocytic dysplasia

#### Treatment-Specific Parser
- **CD33 Expression Analysis**: Critical for DA+GO eligibility assessment
- **Treatment History Extraction**: Prior therapies, MDS history, relapse/refractory status
- **Performance Status Assessment**: ECOG status and fitness evaluation
- **Comorbidity Analysis**: Treatment eligibility factors

#### ELN Risk Parser
- **ELN 2022 Risk Factors**: Comprehensive molecular risk assessment
- **ELN 2024 Updates**: Non-intensive therapy risk stratification
- **Cytogenetic Risk Integration**: Complex/monosomal karyotype assessment
- **Molecular Risk Markers**: Favorable, intermediate, and adverse genetic factors

#### IPSS Risk Parser
- **Traditional IPSS Scoring**: Blast percentage, cytogenetics, cytopenias
- **IPSS-M Enhancement**: Molecular marker integration
- **Survival Prediction**: Median overall survival and progression risk
- **Treatment Planning**: Risk-adapted therapeutic recommendations

### Advanced Data Integration
- **Multi-Source Validation**: Cross-checking between different parsers
- **Data Normalization**: Standardization across various input formats
- **Quality Control**: Automated detection of inconsistencies and conflicts
- **Manual Override**: Clinician ability to modify parsed data
- **Version Control**: Tracking of data modifications and updates

## 4. Transparent Derivation Logic System

### Step-by-Step Classification Reasoning
- **Decision Tree Visualization**: Interactive flowcharts showing classification pathway
- **Criterion-by-Criterion Analysis**: Detailed breakdown of each classification step
- **Supporting Evidence**: Literature references for each diagnostic criterion
- **Alternative Pathway Analysis**: Why other diagnoses were excluded
- **Confidence Factors**: Explanation of uncertainty sources and limitations

### Interactive Classification Flowcharts
- **Dynamic Decision Trees**: Click-through classification pathways
- **Highlighting System**: Visual emphasis of key diagnostic features
- **Branch Point Explanations**: Detailed rationale for each decision point
- **What-If Analysis**: Explore how changing parameters affects classification
- **Educational Annotations**: Teaching points for trainees and students

### Comprehensive Diagnostic Rationale
- **Primary Diagnosis Justification**: Complete medical reasoning
- **Differential Diagnosis Discussion**: Why alternatives were considered/excluded
- **Molecular Correlation**: How genetic findings support the diagnosis
- **Morphologic Integration**: Correlation with pathology findings
- **Clinical Context**: Integration of patient history and presentation

## 5. Advanced Risk Assessment and Prognostic Tools

### AML Risk Stratification Systems
- **ELN 2022 Risk Assessment**: Complete European LeukemiaNet guidelines
  - Favorable risk: CBF leukemias, NPM1+/FLT3-ITD-, biallelic CEBPA
  - Intermediate risk: Cytogenetically normal without favorable/adverse features
  - Adverse risk: Complex karyotype, TP53 alterations, specific adverse mutations
- **ELN 2024 Non-Intensive Guidelines**: Updated risk assessment for elderly/unfit patients
- **Treatment-Specific Risk**: Risk assessment tailored to treatment intensity
- **Survival Predictions**: Median overall survival and disease-free survival estimates

### MDS Risk Assessment Systems
- **IPSS (International Prognostic Scoring System)**:
  - Cytogenetic risk categorization (Very Good, Good, Intermediate, Poor, Very Poor)
  - Blast percentage scoring (0-4%, 5-9%, 10-19%)
  - Cytopenia assessment (Hb, ANC, platelets)
- **IPSS-M (IPSS-Molecular)**:
  - Enhanced molecular marker integration
  - Refined risk categories with improved prognostic accuracy
  - Gene-specific risk contributions
- **Survival Modeling**: Detailed progression-free and overall survival curves
- **Treatment Planning**: Risk-adapted therapeutic algorithm recommendations

### Advanced Risk Visualization
- **Interactive Risk Charts**: Dynamic visualization of prognostic categories
- **Kaplan-Meier Curves**: Graphical survival analysis with confidence intervals
- **Risk Factor Contributions**: Quantitative analysis of individual risk elements
- **Comparative Analysis**: Patient positioning relative to published cohorts
- **Longitudinal Tracking**: Risk evolution over time with serial assessments

## 6. Comprehensive AI-Powered Clinical Analysis

### GPT-4 Clinical Review Generation
- **Complex Case Analysis**: AI-powered interpretation of challenging diagnoses
- **Gene Function Analysis**: Detailed explanation of mutation significance
- **Pathway Integration**: How mutations affect cellular processes
- **Clinical Correlation**: Integration of molecular findings with patient presentation
- **Literature Integration**: Current research findings relevant to the case

### Differential Diagnosis Engine
- **Systematic Comparison**: Detailed analysis of similar diagnoses
- **Feature Comparison Tables**: Side-by-side diagnostic criteria comparison
- **Probability Ranking**: Quantitative likelihood assessment for each differential
- **Exclusion Rationale**: Why specific diagnoses were ruled out
- **Borderline Case Management**: Special considerations for uncertain cases

### Molecular Interpretation Services
- **Mutation Significance Analysis**: Clinical relevance of each genetic finding
- **Pathway Impact Assessment**: How mutations affect disease biology
- **Therapeutic Implications**: Treatment relevance of molecular findings
- **Prognostic Impact**: How mutations influence patient outcomes
- **Novel Mutation Analysis**: Interpretation of rare or new genetic findings

### Treatment Response Prediction
- **Therapy Selection Guidance**: Molecular marker-based treatment recommendations
- **Response Probability**: Statistical likelihood of treatment success
- **Resistance Mechanism Analysis**: Potential causes of treatment failure
- **Alternative Strategy Suggestions**: Backup treatment options
- **Monitoring Recommendations**: Follow-up testing strategies

## 7. Comprehensive Treatment Decision Support

### Evidence-Based Treatment Algorithms
- **Consensus Guidelines Integration**: AML treatment consensus (Coats et al.)
- **Age-Stratified Recommendations**: Fit vs. unfit patient algorithms
- **Molecular-Guided Therapy**: Targeted treatment based on genetic profile
- **Clinical Trial Integration**: Treatment recommendations linked to trial eligibility

### Treatment Eligibility Assessment
- **Intensive Therapy Evaluation**:
  - Daunorubicin + Cytarabine + Gemtuzumab Ozogamicin (DA+GO)
  - Daunorubicin + Cytarabine + Midostaurin (DA+Midostaurin)
  - High-dose cytarabine consolidation
- **Non-Intensive Options**:
  - Hypomethylating agents (5-azacytidine, decitabine)
  - Venetoclax combinations
  - Low-dose cytarabine
- **Targeted Therapies**:
  - FLT3 inhibitors (midostaurin, gilteritinib)
  - IDH inhibitors (ivosidenib, enasidenib)
  - CD33-targeted therapy assessment

### Specialized Treatment Considerations
- **CPX-351 Eligibility**: Assessment for liposomal daunorubicin/cytarabine
- **CD33 Expression Analysis**: Critical for gemtuzumab ozogamicin eligibility
- **Transplant Evaluation**: Allogeneic stem cell transplant candidacy
- **Supportive Care Planning**: Transfusion, infection prevention, palliative care

### Treatment Monitoring Integration
- **Response Assessment Criteria**: Complete remission, partial remission definitions
- **Monitoring Schedules**: Recommended follow-up testing timelines
- **Resistance Detection**: Early identification of treatment failure
- **Dose Modification Guidelines**: Toxicity management recommendations

## 8. Advanced Clinical Trial Matching System

### AI-Powered Eligibility Assessment
- **Comprehensive Profile Matching**: 50+ clinical and molecular parameters
- **Relevance Scoring**: 0-100 scale trial compatibility assessment
- **Geographic Optimization**: Location-based trial recommendations
- **Enrollment Status**: Real-time trial availability and recruitment status

### Enhanced Trial Database
- **CRUK Integration**: 38 curated blood cancer trials with detailed eligibility
- **Multi-Registry Capability**: Architecture for ClinicalTrials.gov, EU Register expansion
- **Molecular Matching**: Genetic biomarker-based trial selection
- **Phase-Specific Recommendations**: Early-phase vs. standard treatment trials

### Intelligent Recommendation Engine
- **Priority Classification**: High/medium/low recommendation confidence
- **Clinical Rationale**: Detailed explanation of trial suitability
- **Risk-Benefit Analysis**: Treatment benefit vs. trial participation risks
- **Practical Considerations**: Travel, scheduling, insurance coverage factors

## 9. Comprehensive Report Generation System

### Professional Clinical Documentation
- **Hospital-Grade Formatting**: Professional medical report standards
- **Modular Report Components**: Customizable section selection
- **Executive Summary**: High-level findings for busy clinicians
- **Detailed Technical Analysis**: Complete methodology and results

### Multi-Format Export Options
- **PDF Generation**: Secure, formatted clinical reports
- **Data Export**: CSV/Excel format for research and analysis
- **Image Export**: High-resolution charts and flowcharts
- **Integration Ready**: HL7 FHIR compatible for EMR systems

### Report Customization Features
- **Institutional Branding**: Custom headers, logos, contact information
- **Selective Content**: Choose specific sections for different audiences
- **Version Control**: Track report revisions and updates
- **Digital Signatures**: Secure authentication for clinical use

## 10. Quality Assurance and Validation Systems

### Multi-Level Validation
- **Input Validation**: Real-time data quality checking
- **Cross-Reference Validation**: Consistency checking across data sources
- **Clinical Logic Validation**: Medical reasoning verification
- **Output Validation**: Final result reasonableness checking

### Confidence Assessment
- **Statistical Confidence**: Quantitative reliability measures
- **Clinical Confidence**: Medical judgment integration
- **Data Quality Metrics**: Input data completeness and accuracy
- **Uncertainty Quantification**: Clear communication of limitations

### Error Detection and Management
- **Automated Error Detection**: Systematic identification of inconsistencies
- **Graceful Degradation**: Maintain functionality despite incomplete data
- **User Feedback Integration**: Continuous improvement based on clinical use
- **Version Control**: Track algorithm updates and improvements

## 11. Educational and Training Features

### Interactive Learning Tools
- **Case-Based Learning**: Step-through complex diagnostic cases
- **Decision Tree Education**: Learn classification algorithms interactively
- **Molecular Pathology Integration**: Correlate genetics with disease biology
- **Literature Integration**: Current research findings and guidelines

### Training and Certification Support
- **Competency Assessment**: Self-testing on classification criteria
- **Progress Tracking**: Learning curve monitoring
- **Continuing Education**: CME-eligible educational content
- **Professional Development**: Career-long learning support

## 12. Research and Analytics Capabilities

### De-identified Data Analytics
- **Population Health Insights**: Aggregate disease pattern analysis
- **Treatment Outcome Tracking**: Therapy effectiveness monitoring
- **Biomarker Discovery**: Novel prognostic factor identification
- **Clinical Research Support**: Study design and data collection tools

### Quality Improvement Tools
- **Diagnostic Accuracy Tracking**: Performance monitoring over time
- **Inter-rater Reliability**: Consistency assessment across users
- **Guideline Adherence**: Compliance with standard-of-care recommendations
- **Outcome Correlation**: Treatment selection vs. patient outcomes

---

**Important Clinical Notice**: This comprehensive platform is designed for educational purposes and clinical decision support only. All diagnostic and treatment decisions must be made by qualified healthcare professionals with consideration of individual patient circumstances, local protocols, and current medical guidelines. The platform provides sophisticated analytical tools but does not replace clinical judgment, additional testing, or consultation with oncology specialists when appropriate.

---

# Classification Algorithms

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

### MDS Classification Algorithm

The MDS classification follows WHO 2022 criteria with specific attention to:

- Ring sideroblast percentage (≥15% or ≥5% with SF3B1 mutation)
- Blast count thresholds (0-4%, 5-9%, 10-19%)
- Multilineage vs single lineage dysplasia
- Genetic abnormalities and their classification impact

## ICC 2022 Classification

### Key Differences from WHO 2022

1. **Blast Threshold**: ICC maintains 20% blast threshold for AML
2. **TP53-mutated AML/MDS**: Separate category for TP53-mutated neoplasms
3. **Hypoplastic MDS**: Distinct recognition of hypocellular MDS
4. **Genetic Risk Groups**: Enhanced molecular risk stratification

## Risk Assessment Algorithms

### ELN 2022 Risk Stratification

The European LeukemiaNet 2022 risk stratification provides three main categories:

#### Favorable Risk
- Core binding factor leukemias: t(8;21) or inv(16)/t(16;16)
- NPM1 mutation without FLT3-ITD
- Biallelic CEBPA mutations

#### Intermediate Risk
- Wild-type NPM1 with FLT3-ITD (low allelic ratio)
- t(9;11) and other specific translocations
- Cytogenetically normal without favorable or adverse markers

#### Adverse Risk
- Complex karyotype (≥3 abnormalities)
- Monosomal karyotype
- TP53 alterations
- Specific adverse mutations (ASXL1, RUNX1 in certain contexts)

### IPSS and IPSS-M Risk Scoring

For MDS risk assessment, the system implements both traditional IPSS and molecular-enhanced IPSS-M scoring:

#### IPSS Components
- Cytogenetic risk category
- Blast percentage
- Number of cytopenias

#### IPSS-M Enhancements
- Additional molecular markers
- Refined cytogenetic risk groups
- Enhanced prognostic accuracy

---

# Clinical Trial Matching System

## Overview

The Haem.io Clinical Trial Matching System is an AI-powered platform that analyzes patient genetic profiles and clinical characteristics to identify relevant blood cancer clinical trials. The system provides intelligent, evidence-based trial recommendations to help connect patients with potentially life-saving treatment opportunities.

## Current Data Source

### Cancer Research UK (CRUK) Clinical Trials Database

The system currently utilizes blood cancer clinical trials from the Cancer Research UK website, specifically from their clinical trial finder platform.

**Current Database Characteristics:**
- **Size**: 38 curated blood cancer trials
- **Geographic Focus**: Primarily UK-based trials with some international studies
- **Quality**: High-quality, manually curated trials with comprehensive eligibility criteria
- **Coverage**: Includes trials for AML, MDS, lymphomas, CLL, multiple myeloma, CML, and other blood cancer subtypes

## System Architecture

### 1. Patient Data Processing

#### Genetic/Molecular Profile Extraction
The system automatically extracts comprehensive genetic information from uploaded laboratory reports:

- **AML-Defining Genetic Abnormalities**: NPM1, FLT3, CEBPA, CBF abnormalities, KMT2A rearrangements, TP53
- **MDS-Related Mutations**: SF3B1, SRSF2, U2AF1, ASXL1, EZH2, TET2, DNMT3A, IDH1/2, RUNX1, TP53
- **ELN2024 Risk Stratification Genes**: Favorable, intermediate, and adverse risk markers

#### Clinical Information Collection
- Demographics, performance status, disease status
- Treatment history, comorbidities, laboratory values
- Reproductive status

### 2. AI-Powered Matching Algorithm

#### OpenAI GPT-4 Integration
- **Model**: GPT-4o with temperature 0.1 for consistent recommendations
- **Processing**: Batch processing of 5 trials at a time
- **Concurrency**: Maximum 3 concurrent API requests

#### Scoring and Prioritization
- **Highly Recommended** (Score ≥70): Strong evidence of eligibility
- **Consider** (Score 40-69): Potential eligibility with uncertainty
- **Not Suitable** (Score <40): Clear exclusion factors

### 3. Enhanced Recommendations

For top-scoring trials, the system generates:
- Clinical rationale and molecular match analysis
- Risk-benefit assessment
- Practical considerations and next steps
- Priority classification

## Integration with Core Platform

- Accessible via Results Page Clinical Trials tab
- Leverages existing genetic parsing and classification results
- Maintains session data across searches
- Consistent UI with platform design

---

# Data Formats

## Overview

This document defines all data formats, schemas, and structures used throughout the Haem.io platform.

## Input Data Formats

### Raw Report Text
**Format**: Plain text string
**Description**: Unstructured medical reports uploaded by users

### Manual Entry Data
**Format**: Dictionary with structured fields
**Description**: Data entered through Streamlit forms

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
    "qualifiers": {
        "previous_MDS_diagnosed_over_3_months_ago": bool,
        "previous_cytotoxic_therapy": str,
        "previous_MPN": bool,
        "relapsed_refractory": bool
    },
    "morphology": {
        "multilineage_dysplasia": bool,
        "erythroid_dysplasia": bool,
        "granulocytic_dysplasia": bool,
        "megakaryocytic_dysplasia": bool
    }
}
```

### MDS Parsed Data
Similar structure with MDS-specific fields including cytopenias, ring sideroblasts, and MDS-specific genetic markers.

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
    "parsed_data": Dict,
    "processing_timestamp": str
}
```

## Risk Assessment Formats

### ELN Risk Assessment
```python
{
    "risk_category": str,                          # "Favorable", "Intermediate", "Adverse"
    "risk_score": int,
    "risk_factors": List[str],
    "molecular_markers": {
        "favorable": List[str],
        "intermediate": List[str], 
        "adverse": List[str]
    },
    "survival_data": Dict,
    "treatment_recommendations": List[str],
    "confidence": float
}
```

### IPSS Risk Assessment
```python
{
    "ipss_score": float,
    "ipss_category": str,                          # "Very Low", "Low", "Intermediate", "High", "Very High"
    "ipss_m_score": float,
    "ipss_m_category": str,
    "component_scores": {
        "cytogenetics": int,
        "blasts": int,
        "cytopenias": int,
        "molecular": int                           # IPSS-M only
    },
    "survival_estimates": {
        "median_os_months": float,
        "progression_risk": float
    },
    "confidence": float
}
```

---

# Developer Guide

## Quick Start

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key
- Basic understanding of Streamlit and medical terminology

### Setup
```bash
# Clone repository
git clone <repository-url>
cd bloodCancerClassify

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup secrets
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your API keys and credentials

# Run application
streamlit run app.py
```

## Project Structure

```
bloodCancerClassify/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # Project overview
├── LICENSE                     # MIT license
│
├── classifiers/                # Disease classification algorithms
│   ├── aml_classifier.py       # WHO/ICC AML classification
│   ├── mds_classifier.py       # WHO/ICC MDS classification
│   ├── aml_risk_classifier.py  # ELN risk stratification
│   ├── mds_risk_classifier.py  # IPSS/IPSS-M risk scoring
│   └── aml_mds_combined.py     # Combined classification logic
│
├── parsers/                    # Data extraction and parsing
│   ├── aml_parser.py           # AML genetic data extraction
│   ├── mds_parser.py           # MDS genetic data extraction
│   ├── treatment_parser.py     # Treatment-specific parsing
│   ├── clinical_trial_matcher.py # Trial matching logic
│   └── final_review_parser.py  # Post-classification review
│
├── utils/                      # Utility functions and helpers
│   ├── forms.py                # Streamlit form components
│   ├── displayers.py           # Result display functions
│   ├── pdf.py                  # PDF report generation
│   └── transformation_utils.py # Data format conversions
│
├── reviewers/                  # AI-powered clinical reviews
│   ├── aml_reviewer.py         # AML case review generation
│   └── mds_reviewer.py         # MDS case review generation
│
├── tests/                      # Test suite
│   ├── test_classifiers.py
│   ├── test_parsers.py
│   └── test_utils.py
│
└── scrapers/                   # Clinical trial data scrapers
    ├── clinicaltrials_gov_scraper.py
    ├── eu_clinical_trials_scraper.py
    └── who_ictrp_scraper.py
```

## Core Architecture

### Application Flow
1. **Authentication**: JWT-based user authentication
2. **Data Entry**: Manual forms or report upload
3. **Parsing**: Extract structured data from reports
4. **Classification**: Apply WHO/ICC algorithms
5. **Risk Assessment**: Calculate ELN/IPSS scores
6. **Treatment Recommendations**: Generate therapy options
7. **Clinical Trials**: Match eligible trials
8. **Report Generation**: Create PDF documentation

### Key Design Patterns
- **Modular Classification**: Separate modules for different disease types
- **Parser Abstraction**: Consistent interfaces for data extraction
- **Streamlit State Management**: Session-based data persistence
- **AI Integration**: OpenAI API for complex analysis
- **Error Handling**: Graceful degradation with user feedback

## Testing Guidelines

### Unit Tests
```python
import pytest
from classifiers.aml_classifier import classify_aml_who2022

def test_aml_classification_npm1():
    test_data = {
        "blasts_percentage": 30,
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1_mutation": True
        }
    }
    who_class, icc_class, confidence = classify_aml_who2022(test_data)
    assert "NPM1" in who_class
    assert confidence > 0.8
```

### Integration Tests
```bash
# Run comprehensive test suite
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_classifiers.py -v
python -m pytest tests/test_parsers.py -v
```

---

# Technical Architecture

## System Overview

Haem.io is a cloud-based clinical decision support platform built on a modern web stack designed for scalability, reliability, and medical-grade accuracy.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HAEM.IO PLATFORM                        │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Streamlit UI)                                       │
│  ├── Authentication Layer                                      │
│  ├── Data Entry Forms                                          │
│  ├── Results Visualization                                     │
│  └── Report Generation                                         │
├─────────────────────────────────────────────────────────────────┤
│  Application Layer (Python Backend)                            │
│  ├── Parsers Module         ├── Classifiers Module            │
│  ├── Risk Assessment        ├── Treatment Recommendations     │
│  ├── Clinical Trial Matcher ├── AI Reviewers                  │
│  └── Utility Functions      └── Report Generators             │
├─────────────────────────────────────────────────────────────────┤
│  Data Layer                                                     │
│  ├── Session State (In-Memory)                                 │
│  ├── Clinical Trials Database (JSON)                           │
│  └── Configuration Files                                       │
├─────────────────────────────────────────────────────────────────┤
│  External Services                                              │
│  ├── OpenAI API (GPT-4)                                        │
│  ├── Clinical Trial Registries                                 │
│  └── Authentication Services                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend Layer (Streamlit Framework)

**Technology Stack:**
- **Framework**: Streamlit 1.x
- **UI Components**: Native Streamlit widgets
- **State Management**: Streamlit session state
- **Styling**: Custom CSS with medical theme

### 2. Application Layer (Python Backend)

#### Parsers Module
- Extract structured data from medical reports
- AI-powered extraction using OpenAI GPT-4
- Data validation and normalization
- Error handling and fallback mechanisms

#### Classifiers Module
- Implement WHO/ICC classification algorithms
- Apply evidence-based criteria
- Calculate confidence scores
- Generate alternative diagnoses

#### Risk Assessment Engine
- Calculate prognostic scores (ELN, IPSS)
- Generate survival estimates
- Treatment eligibility assessment

### 3. Data Architecture

#### Session State Management
```python
st.session_state = {
    "user_authenticated": bool,
    "jwt_token": str,
    "parsed_data": Dict,
    "classification_results": Dict,
    "risk_assessment": Dict,
    "treatment_recommendations": List,
    "matched_trials": List
}
```

### 4. Security Architecture

#### Authentication System
- JWT Tokens with expiration
- bcrypt password hashing
- Encrypted cookies
- Role-based access control

#### Data Protection
- In-memory processing only
- Session isolation
- Input sanitization
- Secure file upload validation

## External Integrations

### OpenAI API Integration
- GPT-4 for medical text extraction
- AI-powered case analysis
- Intelligent trial matching
- Rate limiting with exponential backoff

### Clinical Trial Scrapers
- Cancer Research UK (Current)
- ClinicalTrials.gov (Future)
- EU Clinical Trials Register (Future)
- WHO ICTRP (Future)

---

# Treatment Parser Integration

## Overview

We have successfully integrated the specialized AML treatment parser into the main application's treatment recommendations page. This integration provides two data sources for treatment recommendations:

1. **Specialized Treatment Parser (Recommended)**: Extracts treatment-specific data fields
2. **Existing Classification Data (Fallback)**: Uses transformed data from main parser

## Integration Architecture

### Data Flow

```
Original Report Text
        ↓
┌─────────────────────────────────────┐
│     Treatment Tab (app.py)          │
│                                     │
│  ┌─── Option 1: Specialized Parser  │
│  │    • parse_treatment_data()      │
│  │    • Extract CD33, qualifiers    │
│  │    • Direct treatment format     │
│  │                                  │
│  └─── Option 2: Transform Existing  │
│       • transform_main_parser_      │
│         to_treatment_format()       │
│       • Map field names             │
│       • Missing: CD33 data          │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│  Treatment Recommendations          │
│  • determine_treatment_eligibility  │
│  • get_consensus_treatment_          │
│    recommendation                   │
│  • display_treatment_               │
│    recommendations                  │
└─────────────────────────────────────┘
```

## Key Features

### Specialized Treatment Parser

**Advantages:**
- Extracts CD33 status and percentage (critical for DA+GO eligibility)
- Precise treatment-specific data fields
- Optimized prompts for treatment decisions
- Complete data for all treatment eligibility criteria

**Data Extracted:**
- Patient qualifiers (therapy-related, prior MDS/MPN, relapsed/refractory)
- CD33 flow cytometry (percentage and positive/negative status)
- AML-defining genetic abnormalities
- MDS-related mutations and cytogenetics
- Morphologic features

### Data Transformation Fallback

**Advantages:**
- Uses existing classification data
- No additional API calls required
- Backward compatibility

**Limitations:**
- Missing CD33 data (affects DA+GO eligibility)
- Field name mapping required
- May miss treatment-specific nuances

## Treatment Eligibility Logic

### Key Eligibility Criteria

1. **DA+GO**: De novo AML + CD33 positive + Favorable/Intermediate/Unknown cytogenetics
2. **DA+Midostaurin**: Newly diagnosed + FLT3 mutation
3. **CPX-351**: Untreated + (prior MDS/CMML OR MDS-related changes OR therapy-related)

### Critical Dependencies

- **CD33 Status**: Essential for DA+GO eligibility
- **FLT3 Mutations**: Mapped from both AML genes and ELN2024 genes
- **Clinical History**: Precise mapping of qualifiers

## Usage Recommendations

### For Best Results

1. **Use Specialized Treatment Parser**: Recommended for all new cases
2. **Fallback to Existing Data**: When specialized parser fails

### Clinical Considerations

- CD33 status critical for DA+GO eligibility
- Missing data warnings provided
- Treatment recommendations should be reviewed by clinical team
- Algorithm based on Coats et al. consensus

---

# User Manual

## Getting Started

### What is Haem.io?

Haem.io is a web-based clinical decision support tool that helps healthcare professionals classify blood cancers using the latest WHO 2022 and ICC 2022 classification systems. The platform provides:

- Accurate disease classification
- Risk stratification (ELN, IPSS scores)
- Treatment recommendations
- Clinical trial matching
- Professional PDF reports

### Accessing the Platform

1. Navigate to the Haem.io web application
2. Log in with your credentials
3. Begin your analysis workflow

## Main Workflow

### Step 1: Data Entry

Choose your preferred method:

#### Option A: Upload Laboratory Report
- Click "Upload Report"
- Select genetics/pathology report
- AI parser extracts relevant data
- Review and confirm extracted data

#### Option B: Manual Data Entry
- Use structured forms for:
  - Patient demographics
  - Genetic markers
  - Laboratory values
  - Clinical history

### Step 2: Classification Analysis

The system automatically processes data through:
1. WHO 2022 Classification
2. ICC 2022 Classification
3. Disease type determination
4. Confidence scoring

### Step 3: Risk Assessment

#### For AML Patients:
- ELN 2022 Risk Score
- ELN 2024 Non-Intensive assessment
- Treatment eligibility analysis

#### For MDS Patients:
- IPSS Risk Score
- IPSS-M molecular assessment
- Survival estimates

### Step 4: Results Review

Navigate through results tabs:
- **Classification Tab**: Primary diagnosis with derivation logic
- **Risk Assessment Tab**: Risk categories with visualization
- **Treatment Recommendations Tab**: Evidence-based therapy options
- **Clinical Trials Tab**: Matching trials with eligibility assessment

### Step 5: Generate Reports

1. Click "Generate PDF Report"
2. Select report sections
3. Download comprehensive documentation
4. Share with healthcare team

## Key Features Guide

### Genetic Data Parsing

**Supported Report Types:**
- Flow cytometry reports
- Genetic sequencing results
- Cytogenetics reports
- Bone marrow pathology reports
- Free-text clinical notes

**Automatically Extracted Data:**
- AML-defining genetic abnormalities
- MDS-related mutations
- Cytogenetic abnormalities
- Blast percentages
- Morphologic features

### AI-Powered Features

**Clinical Reviews:**
- Gene interpretation and significance
- Additional clinical insights
- Differential diagnosis considerations
- Treatment response predictions

### Treatment Decision Support

**Evidence-Based Recommendations:**
- Consensus treatment algorithms
- Age-appropriate options
- Molecular marker-guided therapy
- Clinical trial eligibility

## Tips for Best Results

### Data Entry Best Practices

1. **Complete Information**: Provide comprehensive relevant data
2. **Accurate Dates**: Include diagnosis dates and treatment history
3. **Genetic Details**: Include mutation percentages when available
4. **Clinical Context**: Add medical history and comorbidities

### Report Upload Guidelines

1. **Clear Text**: Ensure reports are legible and high-quality
2. **Complete Reports**: Upload full genetic/pathology reports
3. **Recent Data**: Use most current available results
4. **Multiple Sources**: Upload multiple reports if available

### Interpreting Results

1. **Confidence Scores**: Higher scores indicate more certain classifications
2. **Multiple Classifications**: Consider all suggested diagnoses
3. **Risk Factors**: Understand risk scoring components
4. **Clinical Context**: Always consider patient-specific factors

## Common Workflows

### Newly Diagnosed AML

1. Upload genetics report with NPM1, FLT3, cytogenetics
2. Enter age and performance status
3. Review WHO/ICC classification
4. Check ELN risk category
5. Review treatment recommendations
6. Identify eligible clinical trials
7. Generate report for medical team

### MDS Risk Assessment

1. Enter/upload morphology and genetics data
2. Include cytogenetic results
3. Add clinical history
4. Review IPSS and IPSS-M scores
5. Understand prognostic implications
6. Consider treatment options
7. Plan follow-up monitoring

### Complex/Unclear Cases

1. Use manual entry for detailed data input
2. Enable AI clinical review features
3. Review differential diagnoses
4. Consider alternative classifications
5. Consult additional clinical resources
6. Document uncertainty in clinical notes

## Troubleshooting

### Common Issues

**Parsing Problems:**
- Ensure report text is clear and readable
- Try manual entry if automatic parsing fails
- Check genetic markers are clearly stated
- Verify report contains relevant data

**Classification Uncertainty:**
- Review input data for completeness
- Consider additional testing recommendations
- Consult differential diagnosis suggestions
- Use AI review features for complex cases

**Missing Risk Scores:**
- Verify all required data fields are complete
- Check genetic markers are properly formatted
- Ensure cytogenetic data is included
- Consider manual risk calculation if needed

## Data Privacy and Security

### Protected Information
- All patient data processed securely
- No permanent data storage on servers
- Session data automatically cleared
- Authentication protects sensitive features

### Best Practices
- Use anonymized patient identifiers
- Remove identifying information from uploads
- Log out after each session
- Follow institutional data policies

## Limitations and Disclaimers

### Important Notes
- Tool is for educational and decision support purposes only
- Always confirm results with additional clinical assessment
- Consider local treatment protocols and guidelines
- Consult with experienced haematologists for complex cases

---

**Important Notice**: This documentation is for educational purposes and clinical decision support only. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. All clinical decisions should be made by qualified healthcare professionals with consideration of individual patient circumstances.

---

*End of Combined Documentation*