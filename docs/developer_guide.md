# Haem.io Developer Guide

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
├── .gitignore                  # Git ignore rules
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
│   ├── aml_eln_parser.py       # ELN risk data parsing
│   ├── mds_ipss_parser.py      # IPSS risk data parsing
│   ├── clinical_trial_matcher.py # Trial matching logic
│   └── final_review_parser.py  # Post-classification review
│
├── utils/                      # Utility functions and helpers
│   ├── forms.py                # Streamlit form components
│   ├── displayers.py           # Result display functions
│   ├── pdf.py                  # PDF report generation
│   ├── transformation_utils.py # Data format conversions
│   └── aml_treatment_recommendations.py # Treatment algorithms
│
├── reviewers/                  # AI-powered clinical reviews
│   ├── aml_reviewer.py         # AML case review generation
│   └── mds_reviewer.py         # MDS case review generation
│
├── docs/                       # Documentation
│   ├── user_manual.md
│   ├── developer_guide.md
│   ├── app_functionality.md
│   └── clinical_trial_matching_system.md
│
├── tests/                      # Test suite
│   ├── test_classifiers.py
│   ├── test_parsers.py
│   └── test_utils.py
│
├── scripts/                    # Utility scripts
│   ├── test_treatment_parser.py
│   └── test_treatment_integration.py
│
├── scrapers/                   # Clinical trial data scrapers
│   ├── clinicaltrials_gov_scraper.py
│   ├── eu_clinical_trials_scraper.py
│   ├── who_ictrp_scraper.py
│   └── master_trial_scraper.py
│
├── trials-aggregator/          # Clinical trial database
│   └── clinical_trials.json
│
└── public/                     # Static assets
    └── favicon.svg
```

## Core Architecture

### Application Flow

1. **Authentication** (`app.py`): JWT-based user authentication
2. **Data Entry** (`utils/forms.py`): Manual forms or report upload
3. **Parsing** (`parsers/`): Extract structured data from reports
4. **Classification** (`classifiers/`): Apply WHO/ICC algorithms
5. **Risk Assessment** (`classifiers/`): Calculate ELN/IPSS scores
6. **Treatment Recommendations** (`utils/`): Generate therapy options
7. **Clinical Trials** (`parsers/`): Match eligible trials
8. **Report Generation** (`utils/pdf.py`): Create PDF documentation

### Key Design Patterns

- **Modular Classification**: Separate modules for different disease types
- **Parser Abstraction**: Consistent interfaces for data extraction
- **Streamlit State Management**: Session-based data persistence
- **AI Integration**: OpenAI API for complex analysis
- **Error Handling**: Graceful degradation with user feedback

## Adding New Features

### Adding a New Parser

1. **Create Parser File**:
```python
# parsers/new_disease_parser.py
import asyncio
from openai import AsyncOpenAI

async def parse_new_disease_data(report_text: str) -> dict:
    """Parse genetic data for new disease type"""
    client = AsyncOpenAI(api_key=st.secrets["openai"]["api_key"])
    
    prompt = """
    Extract genetic markers for [disease type] from this report:
    {report_text}
    
    Return JSON with:
    - genetic_markers: dict
    - blast_percentage: float
    - morphology: dict
    """
    
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt.format(report_text=report_text)}],
        temperature=0.1
    )
    
    # Parse and validate response
    return parsed_data
```

2. **Add to Main Application**:
```python
# app.py - Add to data entry page
if disease_type == "new_disease":
    parsed_data = asyncio.run(parse_new_disease_data(report_text))
```

3. **Create Tests**:
```python
# tests/test_new_parser.py
def test_new_disease_parser():
    sample_report = "..."
    result = asyncio.run(parse_new_disease_data(sample_report))
    assert "genetic_markers" in result
```

### Adding a New Classifier

1. **Create Classifier Module**:
```python
# classifiers/new_disease_classifier.py
from typing import Dict, List, Tuple

def classify_new_disease(parsed_data: Dict) -> Tuple[str, str, float]:
    """
    Classify new disease type based on WHO criteria
    
    Args:
        parsed_data: Parsed genetic and clinical data
        
    Returns:
        who_class: WHO classification
        icc_class: ICC classification  
        confidence: Confidence score (0-1)
    """
    
    # Classification logic
    if condition_a:
        return "Disease Subtype A", "Disease Subtype A", 0.9
    elif condition_b:
        return "Disease Subtype B", "Disease Subtype B", 0.8
    
    return "Unclassified", "Unclassified", 0.3
```

2. **Integration**:
```python
# classifiers/combined_classifier.py
from .new_disease_classifier import classify_new_disease

def classify_hematologic_malignancy(parsed_data: Dict) -> Dict:
    if suspected_disease == "new_disease":
        who_class, icc_class, confidence = classify_new_disease(parsed_data)
```

### Adding New Risk Assessment

1. **Create Risk Module**:
```python
# classifiers/new_disease_risk.py
def calculate_new_disease_risk(parsed_data: Dict) -> Dict:
    """Calculate risk score for new disease type"""
    
    risk_factors = []
    score = 0
    
    # Risk calculation logic
    if parsed_data.get('high_risk_marker'):
        risk_factors.append("High risk genetic marker")
        score += 2
    
    if score >= 4:
        risk_category = "High Risk"
    elif score >= 2:
        risk_category = "Intermediate Risk"
    else:
        risk_category = "Low Risk"
    
    return {
        "risk_category": risk_category,
        "risk_score": score,
        "risk_factors": risk_factors,
        "survival_estimate": get_survival_data(risk_category)
    }
```

## Testing Guidelines

### Unit Tests

```python
# tests/test_classifiers.py
import pytest
from classifiers.aml_classifier import classify_aml_who2022

def test_aml_classification_npm1():
    """Test AML classification with NPM1 mutation"""
    test_data = {
        "blasts_percentage": 25,
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1_mutation": True,
            "FLT3_ITD": False
        }
    }
    
    who_class, icc_class, confidence = classify_aml_who2022(test_data)
    assert "NPM1" in who_class
    assert confidence > 0.8
```

### Integration Tests

```python
# tests/test_integration.py
def test_full_workflow():
    """Test complete classification workflow"""
    sample_report = load_test_report("aml_npm1_sample.txt")
    
    # Parse
    parsed_data = asyncio.run(parse_genetics_report_aml(sample_report))
    
    # Classify
    result = classify_combined_WHO2022(parsed_data)
    
    # Assert expected results
    assert result["who_class"] == "AML with mutated NPM1"
    assert result["confidence"] > 0.8
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_classifiers.py

# Run with coverage
pytest --cov=classifiers tests/
```

## Code Style Guidelines

### Python Style

- Follow PEP 8 conventions
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use descriptive variable names
- Add docstrings for all public functions

### Function Documentation

```python
def classify_disease(parsed_data: Dict[str, Any]) -> Tuple[str, str, float]:
    """
    Classify hematologic malignancy based on genetic data.
    
    Args:
        parsed_data: Dictionary containing genetic markers, blast count,
                    and morphologic features
                    
    Returns:
        Tuple containing:
        - who_classification: WHO 2022 classification string
        - icc_classification: ICC 2022 classification string  
        - confidence_score: Float between 0-1 indicating certainty
        
    Raises:
        ValueError: If required genetic data is missing
        
    Example:
        >>> data = {"blasts_percentage": 30, "NPM1_mutation": True}
        >>> who, icc, conf = classify_disease(data)
        >>> print(f"Classification: {who} (confidence: {conf:.2f})")
    """
```

### Error Handling

```python
def parse_genetic_data(report_text: str) -> Dict:
    """Parse genetic data with proper error handling"""
    try:
        # Parsing logic
        result = extract_data(report_text)
        validate_data(result)
        return result
        
    except OpenAIError as e:
        st.error(f"AI parsing failed: {e}")
        return {}
        
    except ValidationError as e:
        st.warning(f"Data validation issue: {e}")
        return {}
        
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        logger.exception("Unexpected parsing error")
        return {}
```

## AI Integration Best Practices

### Prompt Engineering

```python
def create_classification_prompt(data: Dict) -> str:
    """Create well-structured prompts for AI analysis"""
    
    prompt = f"""
    You are a hematopathologist reviewing genetic data for classification.
    
    PATIENT DATA:
    - Blast percentage: {data.get('blasts_percentage', 'Unknown')}
    - Genetic markers: {format_genetic_markers(data)}
    - Morphology: {data.get('morphology', 'Not specified')}
    
    TASK:
    Classify according to WHO 2022 criteria. Consider:
    1. Blast threshold requirements
    2. Genetic abnormality significance
    3. Morphologic features
    4. Disease history
    
    RESPONSE FORMAT:
    Return JSON with classification, confidence, and rationale.
    """
    return prompt
```

### Rate Limiting

```python
import asyncio
from asyncio import Semaphore

class AIAnalyzer:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = Semaphore(max_concurrent)
        self.client = AsyncOpenAI()
    
    async def analyze_with_rate_limit(self, prompt: str) -> str:
        async with self.semaphore:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content
```

## Deployment Guidelines

### Local Development

```bash
# Development server with auto-reload
streamlit run app.py --server.runOnSave true

# Debug mode
streamlit run app.py --logger.level debug
```

### Production Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run with production settings
streamlit run app.py --server.headless true
```

### Environment Configuration

```toml
# .streamlit/config.toml
[server]
port = 8501
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#009688"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

## Contributing Workflow

### Git Workflow

1. **Fork Repository**: Create personal fork
2. **Create Branch**: `git checkout -b feature/new-classifier`
3. **Make Changes**: Implement feature with tests
4. **Test Locally**: Run full test suite
5. **Commit Changes**: Use descriptive commit messages
6. **Create Pull Request**: Include description and test results
7. **Code Review**: Address feedback from maintainers
8. **Merge**: Squash and merge approved changes

### Commit Messages

```
feat: add NPM1 mutation classifier for AML

- Implement WHO 2022 criteria for NPM1-mutated AML
- Add confidence scoring based on mutation burden
- Include comprehensive test coverage
- Update documentation with new classification rules

Closes #123
```

### Pull Request Template

```markdown
## Description
Brief description of changes made

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

## Debugging and Troubleshooting

### Common Issues

**Streamlit Session State**:
```python
# Debugging session state
if st.checkbox("Debug Session State"):
    st.write("Session State:", st.session_state)
```

**AI API Errors**:
```python
# Comprehensive error handling
try:
    response = await client.chat.completions.create(...)
except OpenAIError as e:
    st.error(f"OpenAI API Error: {e}")
    st.info("Try again or use manual entry")
except Exception as e:
    st.error(f"Unexpected error: {e}")
    logger.exception("API call failed")
```

**Data Validation**:
```python
def validate_parsed_data(data: Dict) -> List[str]:
    """Validate parsed data and return list of issues"""
    issues = []
    
    if not data.get('blasts_percentage'):
        issues.append("Missing blast percentage")
    
    if not any(data.get('genetic_markers', {}).values()):
        issues.append("No genetic markers detected")
    
    return issues
```

### Performance Monitoring

```python
import time
import logging

def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logging.info(f"{func.__name__} took {end_time - start_time:.2f}s")
        return result
    return wrapper
```

## Security Considerations

### Data Protection
- Never log patient data
- Clear session state on logout
- Use environment variables for secrets
- Validate all user inputs
- Sanitize uploaded files

### Authentication
- Use strong JWT secrets
- Implement session timeouts
- Hash passwords with bcrypt
- Validate user permissions

### Example Security Implementation
```python
def sanitize_input(user_input: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove potentially dangerous characters
    cleaned = re.sub(r'[<>"\']', '', user_input)
    return cleaned.strip()

def validate_file_upload(uploaded_file) -> bool:
    """Validate uploaded file for security"""
    if uploaded_file.size > 10_000_000:  # 10MB limit
        return False
    
    allowed_types = ['text/plain', 'application/pdf']
    if uploaded_file.type not in allowed_types:
        return False
    
    return True
```

This guide provides the foundation for contributing to and maintaining the Haem.io platform. For specific questions or clarifications, consult the existing codebase or reach out to the development team. 