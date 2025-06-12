# AML Treatment Parser Integration

## Overview

We have successfully integrated the specialized AML treatment parser into the main application's treatment recommendations page. This integration provides two data sources for treatment recommendations:

1. **Specialized Treatment Parser (Recommended)**: Extracts treatment-specific data fields from the original report
2. **Existing Classification Data (Fallback)**: Uses transformed data from the main AML parser

## Integration Architecture

### Files Modified/Created

- **`parsers/treatment_parser.py`**: New specialized parser for treatment data
- **`utils/transformation_utils.py`**: Data transformation utilities 
- **`app.py`**: Updated treatment tab to use new parser
- **`scripts/test_treatment_integration.py`**: Integration testing
- **`scripts/test_treatment_parser.py`**: Parser testing

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
│  • get_consensus_treatment_recommendation │
│  • display_treatment_recommendations │
└─────────────────────────────────────┘
```

## Key Features

### 🎯 **Specialized Treatment Parser**

**Advantages:**
- ✅ Extracts CD33 status and percentage (critical for DA+GO eligibility)
- ✅ Precise treatment-specific data fields
- ✅ Optimized prompts for treatment decisions
- ✅ Complete data for all treatment eligibility criteria

**Data Extracted:**
- Patient qualifiers (therapy-related, prior MDS/MPN, relapsed/refractory)
- CD33 flow cytometry (percentage and positive/negative status)
- AML-defining genetic abnormalities (PML-RARA, NPM1, CBF leukemias, FLT3)
- MDS-related mutations and cytogenetics
- Morphologic features (dysplastic lineages)

### 🔄 **Data Transformation Fallback**

**Advantages:**
- ✅ Uses existing classification data
- ✅ No additional API calls required
- ✅ Backward compatibility

**Limitations:**
- ⚠️ Missing CD33 data (affects DA+GO eligibility)
- ⚠️ Field name mapping required
- ⚠️ May miss treatment-specific nuances

## User Interface

### Treatment Tab Interface

The updated treatment tab provides:

1. **Data Source Selection**: Radio button to choose parser method
2. **Parsing Progress**: Spinner with progress indication
3. **Parsed Data Display**: Expandable section showing extracted data
4. **Treatment Recommendations**: Full consensus algorithm results
5. **Warnings**: Clear notifications about missing data (e.g., CD33 status)

### Display Components

- **📋 Clinical History & Qualifiers**: Organized by disease/treatment history
- **🔬 Flow Cytometry (CD33)**: Expression percentage and interpretation
- **🧬 Genetic Abnormalities**: AML-defining vs MDS-related
- **🧮 Cytogenetic Data**: Risk-relevant chromosomal changes
- **🔍 Morphologic Features**: Dysplastic lineages

## Treatment Eligibility Logic

### Key Eligibility Criteria

1. **DA+GO**: De novo AML + CD33 positive + Favorable/Intermediate/Unknown cytogenetics
2. **DA+Midostaurin**: Newly diagnosed + FLT3 mutation
3. **CPX-351**: Untreated + (prior MDS/CMML OR MDS-related changes OR therapy-related)

### Critical Dependencies

- **CD33 Status**: Essential for DA+GO eligibility (only available with specialized parser)
- **FLT3 Mutations**: Mapped from both AML genes and ELN2024 genes
- **Clinical History**: Precise mapping of qualifiers between parser formats

## Field Mapping

### Main Parser → Treatment Parser Mapping

| Main Parser Field | Treatment Parser Field | Notes |
|-------------------|------------------------|-------|
| `qualifiers.previous_MDS_diagnosed_over_3_months_ago` | `qualifiers.previous_MDS` | Direct mapping |
| `qualifiers.previous_cytotoxic_therapy` | `qualifiers.therapy_related` | If not "None" |
| `AML_defining_recurrent_genetic_abnormalities.NPM1` | `AML_defining_recurrent_genetic_abnormalities.NPM1_mutation` | Field name change |
| `AML_defining_recurrent_genetic_abnormalities.RUNX1::RUNX1T1` | `AML_defining_recurrent_genetic_abnormalities.RUNX1_RUNX1T1` | Format change |
| `ELN2024_risk_genes.FLT3_ITD` | `AML_defining_recurrent_genetic_abnormalities.FLT3_ITD` | Cross-category mapping |
| **N/A** | `cd33_positive` | **Missing from main parser** |
| **N/A** | `cd33_percentage` | **Missing from main parser** |

## Testing

### Test Coverage

1. **Field Transformation Tests**: Verify mapping between parser formats
2. **Treatment Eligibility Tests**: Confirm treatment algorithm works with transformed data
3. **CD33 Handling Tests**: Ensure appropriate warnings for missing data
4. **Integration Tests**: End-to-end workflow validation

### Running Tests

```bash
# Test the specialized treatment parser
python scripts/test_treatment_parser.py

# Test the integration (requires adjustment for Streamlit dependencies)
python scripts/test_treatment_integration.py
```

## Usage Recommendations

### For Best Results

1. **Use Specialized Treatment Parser**: Recommended for all new cases
   - Provides complete CD33 data
   - Treatment-optimized data extraction
   - Most accurate treatment recommendations

2. **Fallback to Existing Data**: When specialized parser fails
   - Still functional for most treatment decisions
   - Clear warnings about missing data
   - Maintains backward compatibility

### Clinical Considerations

- **CD33 Status Critical**: DA+GO eligibility requires CD33 positivity (≥20%)
- **Missing Data Warnings**: System clearly indicates when key data is unavailable
- **Manual Review**: Treatment recommendations should always be reviewed by clinical team
- **Algorithm Limitations**: Based on Coats et al. consensus - consider local protocols

## Error Handling

### Graceful Degradation

1. **Parser Failure**: Falls back to transformation method
2. **Missing Report Text**: Clear error message with guidance
3. **API Errors**: Maintains existing classification functionality
4. **Data Validation**: Validates extracted data ranges and types

### User Feedback

- Progress indicators during parsing
- Clear error messages with actionable guidance
- Warnings about missing critical data
- Success confirmations with data summaries

## Future Enhancements

### Potential Improvements

1. **CD33 Extraction from Main Parser**: Add CD33 prompts to main AML parser
2. **Caching**: Cache parsed treatment data to avoid re-parsing
3. **Batch Processing**: Support multiple reports for treatment planning
4. **Integration with ELN Risk**: Use treatment parser data for risk calculation
5. **Export Options**: PDF/CSV export of treatment recommendations

### Performance Optimizations

- Parallel processing of prompts (already implemented)
- Caching of transformation mappings
- Optimized prompt engineering for faster responses

## Conclusion

The treatment parser integration successfully bridges the gap between diagnostic classification and treatment planning. By providing both specialized parsing and intelligent data transformation, we ensure that clinicians have access to the most accurate treatment recommendations possible while maintaining system reliability and backward compatibility.

The implementation prioritizes patient safety through clear warnings about missing data and comprehensive treatment rationale, supporting evidence-based clinical decision-making. 