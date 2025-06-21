# Haem.io Technical Architecture

## System Overview

Haem.io is a cloud-based clinical decision support platform built on a modern web stack designed for scalability, reliability, and medical-grade accuracy. The system processes complex genetic and clinical data to provide real-time blood cancer classification and treatment recommendations.

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

**Key Features:**
- Responsive web interface
- Real-time data validation
- Interactive visualizations
- PDF report generation
- Session-based workflow

**Architecture Pattern:**
```python
app.py
├── Authentication Flow
├── Data Entry Page
│   ├── Manual Forms (utils/forms.py)
│   ├── Report Upload
│   └── Data Validation
├── Processing Pipeline
│   ├── Parser Selection
│   ├── Classification Engine
│   └── Risk Assessment
└── Results Display
    ├── Classification Results
    ├── Risk Stratification
    ├── Treatment Recommendations
    └── Clinical Trial Matching
```

### 2. Application Layer (Python Backend)

#### Parsers Module (`parsers/`)
**Purpose**: Extract structured data from medical reports

**Components:**
- `aml_parser.py`: AML genetic data extraction
- `mds_parser.py`: MDS genetic data extraction  
- `treatment_parser.py`: Treatment-specific parsing
- `clinical_trial_matcher.py`: Trial eligibility matching
- `aml_eln_parser.py`: ELN risk data parsing
- `mds_ipss_parser.py`: IPSS risk data parsing

**Design Pattern:**
```python
async def parse_genetics_report(report_text: str) -> Dict:
    """Standard parser interface"""
    # AI-powered extraction using OpenAI GPT-4
    # Data validation and normalization
    # Error handling and fallback mechanisms
    return structured_data
```

#### Classifiers Module (`classifiers/`)
**Purpose**: Implement WHO/ICC classification algorithms

**Components:**
- `aml_classifier.py`: WHO 2022 AML classification
- `mds_classifier.py`: WHO 2022 MDS classification
- `aml_risk_classifier.py`: ELN risk stratification
- `mds_risk_classifier.py`: IPSS/IPSS-M scoring
- `aml_mds_combined.py`: Combined classification logic

**Algorithm Architecture:**
```python
def classify_disease(parsed_data: Dict) -> ClassificationResult:
    """Evidence-based classification engine"""
    # Apply WHO 2022 criteria
    # Calculate confidence scores
    # Generate alternative diagnoses
    # Provide classification rationale
    return classification_result
```

#### Risk Assessment Engine
**Purpose**: Calculate prognostic scores and survival estimates

**Risk Systems:**
- **ELN 2022**: European LeukemiaNet AML risk stratification
- **ELN 2024**: Non-intensive therapy risk assessment
- **IPSS**: International Prognostic Scoring System for MDS
- **IPSS-M**: Molecular-enhanced MDS risk scoring

#### Treatment Recommendation Engine
**Purpose**: Generate evidence-based therapy suggestions

**Algorithm Features:**
- Age and fitness-appropriate recommendations
- Molecular marker-guided therapy selection
- Clinical trial eligibility assessment
- Consensus-based decision support

### 3. Data Architecture

#### Session State Management
```python
# Streamlit session state structure
st.session_state = {
    "user_authenticated": bool,
    "jwt_token": str,
    "parsed_data": Dict,
    "classification_results": Dict,
    "risk_assessment": Dict,
    "treatment_recommendations": List,
    "matched_trials": List,
    "formatted_patient_data": str
}
```

#### Clinical Trials Database
```json
{
  "trials": [
    {
      "title": "Trial Name",
      "description": "Trial Description", 
      "cancer_types": ["AML", "MDS"],
      "status": "open",
      "locations": ["UK", "US"],
      "who_can_enter": "Eligibility criteria",
      "link": "https://..."
    }
  ]
}
```

#### Configuration Management
```toml
# .streamlit/secrets.toml
[auth]
users = [{username = "admin", hashed_password = "..."}]

[openai]
api_key = "sk-..."

[general]
cookie_password = "secure_random_string"

[jwt]
secret_key = "jwt_secret_key"
```

### 4. Security Architecture

#### Authentication System
- **JWT Tokens**: Stateless authentication with expiration
- **bcrypt Hashing**: Secure password storage
- **Encrypted Cookies**: Session data protection
- **Role-Based Access**: AI features for authenticated users only

#### Data Protection
- **In-Memory Processing**: No persistent patient data storage
- **Session Isolation**: User data separation
- **Input Sanitization**: XSS and injection prevention
- **Secure File Upload**: Validation and size limits

#### Security Flow
```python
# Authentication pipeline
user_login() -> validate_credentials() -> generate_jwt() -> 
set_encrypted_cookie() -> protected_features_access()

# Data protection pipeline  
upload_file() -> validate_file() -> sanitize_content() ->
process_in_memory() -> clear_on_logout()
```

## External Integrations

### OpenAI API Integration

**Usage Patterns:**
- **Report Parsing**: GPT-4 for medical text extraction
- **Clinical Review**: AI-powered case analysis
- **Trial Matching**: Intelligent eligibility assessment

**Implementation:**
```python
class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=st.secrets["openai"]["api_key"])
        self.semaphore = asyncio.Semaphore(3)  # Rate limiting
    
    async def analyze_genetics(self, report: str) -> Dict:
        async with self.semaphore:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return json.loads(response.choices[0].message.content)
```

**Error Handling:**
- API rate limiting with exponential backoff
- Graceful degradation to manual entry
- Comprehensive error logging
- Fallback mechanisms for service outages

### Clinical Trial Scrapers

**Data Sources:**
- Cancer Research UK (Current)
- ClinicalTrials.gov (Future)
- EU Clinical Trials Register (Future)
- WHO ICTRP (Future)

**Scraping Architecture:**
```python
# Master scraper coordination
async def scrape_all_sources():
    scrapers = [
        CRUKScraper(),
        ClinicalTrialsGovScraper(),
        EUTrialsScraper()
    ]
    
    results = await asyncio.gather(*[
        scraper.scrape_blood_cancer_trials() 
        for scraper in scrapers
    ])
    
    return deduplicate_trials(results)
```

## Performance Architecture

### Asynchronous Processing
- **Concurrent AI Calls**: Multiple parser prompts in parallel
- **Rate Limiting**: Semaphore-based API throttling
- **Non-Blocking UI**: Streamlit async integration
- **Background Tasks**: Trial data updates

### Caching Strategy
- **Session Caching**: Parser results cached per session
- **Static Data**: Clinical trials database cached in memory
- **Computation Caching**: Risk calculations cached
- **Template Caching**: PDF report templates

### Scalability Considerations
- **Stateless Design**: Horizontal scaling capability
- **Memory Management**: Efficient session state handling
- **Load Balancing**: Multiple instance deployment
- **Database Optimization**: Efficient trial data queries

## Deployment Architecture

### Development Environment
```bash
# Local development stack
Streamlit Dev Server (localhost:8501)
├── Hot Reload: Automatic code updates
├── Debug Mode: Detailed error reporting
├── Local Secrets: .streamlit/secrets.toml
└── Development Database: Local JSON files
```

### Production Environment
```bash
# Production deployment options
Cloud Platform (AWS/GCP/Azure)
├── Container Deployment: Docker/Kubernetes
├── Load Balancer: Multiple app instances
├── SSL/TLS: HTTPS encryption
├── Monitoring: Application performance tracking
├── Logging: Centralized log management
└── Secrets Management: Cloud-based secret storage
```

### Infrastructure as Code
```yaml
# docker-compose.yml
version: '3.8'
services:
  haemio-app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_PORT=8501
    volumes:
      - ./secrets:/app/.streamlit
    restart: unless-stopped
```

## Monitoring and Observability

### Application Monitoring
- **Performance Metrics**: Response times, throughput
- **Error Tracking**: Exception monitoring and alerting
- **User Analytics**: Usage patterns and feature adoption
- **Health Checks**: Service availability monitoring

### Logging Architecture
```python
import logging
import structlog

# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = structlog.get_logger()

# Usage in application
logger.info("Classification completed", 
           user_id=user_id,
           disease_type=disease_type,
           confidence_score=confidence,
           processing_time_ms=processing_time)
```

### Alerting System
- **Error Alerts**: Immediate notification for system errors
- **Performance Alerts**: Slow response time warnings
- **Security Alerts**: Authentication failures and suspicious activity
- **Business Metrics**: Classification accuracy and user engagement

## Data Flow Architecture

### Complete Patient Processing Flow
```
Patient Report Upload
         ↓
Input Validation & Sanitization
         ↓
AI-Powered Data Extraction (Parsers)
         ↓
Data Normalization & Validation
         ↓
WHO/ICC Classification (Classifiers)
         ↓
Risk Stratification (ELN/IPSS)
         ↓
Treatment Recommendations (Algorithms)
         ↓
Clinical Trial Matching (AI Analysis)
         ↓
Results Compilation & Display
         ↓
PDF Report Generation
         ↓
Session Data Cleanup
```

### Error Handling Flow
```
User Input → Validation → Processing → Error Detection
     ↓              ↓           ↓            ↓
Sanitization → Fallback → Logging → User Notification
     ↓              ↓           ↓            ↓
Safe Processing → Manual Entry → Alert → Graceful Degradation
```

## Future Architecture Considerations

### Scalability Enhancements
- **Microservices**: Split into specialized services
- **API Gateway**: Centralized request routing
- **Message Queues**: Asynchronous task processing
- **Database Layer**: Persistent data storage for analytics

### Advanced Features
- **Machine Learning Pipeline**: Custom trained models
- **Real-time Collaboration**: Multi-user case review
- **Mobile Applications**: Native iOS/Android apps
- **Integration APIs**: EMR system connectivity

### Security Enhancements
- **OAuth 2.0**: Enterprise authentication
- **FHIR Compliance**: Healthcare data standards
- **Audit Logging**: Complete user action tracking
- **Data Encryption**: End-to-end encryption

This architecture provides a robust foundation for medical-grade software while maintaining flexibility for future enhancements and scaling requirements. 