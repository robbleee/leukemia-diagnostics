# Haem.io User Manual

## Getting Started

### What is Haem.io?

Haem.io is a web-based clinical decision support tool that helps healthcare professionals classify blood cancers (haematologic malignancies) using the latest WHO 2022 and ICC 2022 classification systems. The platform analyzes patient genetic data, laboratory results, and clinical information to provide:

- Accurate disease classification
- Risk stratification (ELN, IPSS scores)
- Treatment recommendations
- Clinical trial matching
- Professional PDF reports

### Accessing the Platform

1. Navigate to the Haem.io web application
2. Log in with your credentials (authentication required for AI features)
3. Begin your analysis workflow

## Main Workflow

### Step 1: Data Entry

Choose your preferred method for entering patient data:

#### Option A: Upload Laboratory Report
- Click "Upload Report" 
- Select your genetics/pathology report (PDF, text, or image)
- The AI parser will automatically extract relevant genetic markers
- Review and confirm the extracted data

#### Option B: Manual Data Entry
- Use the structured forms to enter:
  - Patient demographics (age, gender)
  - Genetic markers (mutations, cytogenetics)
  - Laboratory values (blast count, blood counts)
  - Clinical history (prior treatments, disease status)

### Step 2: Classification Analysis

The system automatically processes your data through:

1. **WHO 2022 Classification**: Latest international standard
2. **ICC 2022 Classification**: International Consensus Classification
3. **Disease Type Determination**: AML, MDS, or other blood cancer
4. **Confidence Scoring**: Reliability assessment of the classification

### Step 3: Risk Assessment

Based on your classification results:

#### For AML Patients:
- **ELN 2022 Risk Score**: Favorable, Intermediate, or Adverse risk
- **ELN 2024 Non-Intensive**: For elderly or unfit patients
- **Treatment Eligibility**: Intensive vs. non-intensive therapy options

#### For MDS Patients:
- **IPSS Risk Score**: Very Low, Low, Intermediate, High, Very High
- **IPSS-M Score**: Molecular-enhanced risk assessment
- **Survival Estimates**: Expected outcomes based on risk category

### Step 4: Results Review

Navigate through the comprehensive results tabs:

#### Classification Tab
- Primary diagnosis with confidence score
- Alternative diagnoses considered
- Step-by-step derivation logic
- Interactive classification flowchart

#### Risk Assessment Tab
- Risk category with clear visualization
- Contributing factors breakdown
- Survival curves and prognostic information
- Comparison with standard risk groups

#### Treatment Recommendations Tab
- Evidence-based therapy options
- Treatment eligibility analysis
- Consensus algorithm recommendations
- Next steps and clinical considerations

#### Clinical Trials Tab
- Matching clinical trials based on genetic profile
- Eligibility assessment for each trial
- Geographic location and contact information
- AI-powered relevance scoring

### Step 5: Generate Reports

Create professional documentation:

1. Click "Generate PDF Report"
2. Select report sections to include
3. Download comprehensive clinical report
4. Share with healthcare team or use for medical records

## Key Features Guide

### Genetic Data Parsing

**Supported Report Types:**
- Flow cytometry reports
- Genetic sequencing results
- Cytogenetics reports
- Bone marrow pathology reports
- Free-text clinical notes

**Automatically Extracted Data:**
- AML-defining genetic abnormalities (NPM1, FLT3, CEBPA, etc.)
- MDS-related mutations (SF3B1, SRSF2, ASXL1, etc.)
- Cytogenetic abnormalities
- Blast percentages
- Morphologic features

### AI-Powered Features (Authenticated Users)

**Clinical Reviews:**
- Gene interpretation and significance
- Additional clinical insights
- Differential diagnosis considerations
- Treatment response predictions

**Advanced Analysis:**
- Complex case review
- Rare disease identification
- Multi-lineage dysplasia assessment
- Therapy-related malignancy detection

### Treatment Decision Support

**Evidence-Based Recommendations:**
- Consensus treatment algorithms
- Age and fitness-appropriate options
- Molecular marker-guided therapy
- Clinical trial eligibility

**Treatment Categories:**
- Intensive chemotherapy protocols
- Hypomethylating agents
- Targeted therapies
- Supportive care measures

## Tips for Best Results

### Data Entry Best Practices

1. **Complete Information**: Provide as much relevant data as possible
2. **Accurate Dates**: Include diagnosis dates and treatment history
3. **Genetic Details**: Include mutation percentages when available
4. **Clinical Context**: Add relevant medical history and comorbidities

### Report Upload Guidelines

1. **Clear Text**: Ensure reports are legible and high-quality
2. **Complete Reports**: Upload full genetic/pathology reports
3. **Recent Data**: Use the most current available results
4. **Multiple Sources**: Upload multiple reports if available

### Interpreting Results

1. **Confidence Scores**: Higher scores indicate more certain classifications
2. **Multiple Classifications**: Consider all suggested diagnoses
3. **Risk Factors**: Understand the components of risk scoring
4. **Clinical Context**: Always consider patient-specific factors

## Common Workflows

### Newly Diagnosed AML

1. Upload genetics report with NPM1, FLT3, cytogenetics
2. Enter age and performance status
3. Review classification (WHO/ICC)
4. Check ELN risk category
5. Review treatment recommendations
6. Identify eligible clinical trials
7. Generate report for medical team

### MDS Risk Assessment

1. Enter or upload morphology and genetics data
2. Include cytogenetic results
3. Add clinical history (transfusion dependence, etc.)
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
- Check that genetic markers are clearly stated
- Verify report contains relevant haematologic data

**Classification Uncertainty:**
- Review input data for completeness
- Consider additional testing recommendations
- Consult differential diagnosis suggestions
- Use AI review features for complex cases

**Missing Risk Scores:**
- Verify all required data fields are complete
- Check that genetic markers are properly formatted
- Ensure cytogenetic data is included
- Consider manual risk calculation if needed

### Getting Help

1. **Debug Mode**: Enable to see detailed processing information
2. **Error Messages**: Read carefully for specific guidance
3. **Clinical Support**: Consult with haematology colleagues
4. **Technical Issues**: Report bugs or system problems

## Data Privacy and Security

### Protected Information
- All patient data is processed securely
- No data is stored permanently on servers
- Session data is automatically cleared
- Authentication protects sensitive features

### Best Practices
- Use anonymized patient identifiers
- Remove identifying information from uploads
- Log out after each session
- Follow institutional data policies

## Limitations and Disclaimers

### Important Notes
- This tool is for educational and decision support purposes only
- Always confirm results with additional clinical assessment
- Consider local treatment protocols and guidelines
- Consult with experienced haematologists for complex cases

### Clinical Judgment
- Use results as one component of clinical decision-making
- Consider patient-specific factors not captured in the tool
- Validate genetic results with laboratory confirmation
- Follow institutional medical guidelines

## Updates and Maintenance

The platform is regularly updated with:
- Latest classification guidelines
- New genetic markers and mutations
- Updated treatment recommendations
- Enhanced AI capabilities
- Additional clinical trial databases

For questions, support, or feedback, contact the development team or your institutional administrator. 