# Support Ticket AI Workflow - Implementation Plan

## Overview

Build an AI workflow system that processes support tickets through:
1. **Classification** - Category + Severity assignment
2. **Field Extraction** - Structured data extraction from ticket content
3. **Response Drafting** - Contextual response generation
4. **Team Routing** - Intelligent assignment to appropriate teams

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                │
│  (FastAPI routes receive requests, return ProcessingResult)      │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                         │
│  (Coordinates step execution, manages context, handles errors)   │
└─────────────────────────────────────────────────────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
┌───────────────┐    ┌─────────────────┐    ┌────────────────┐
│ Classification│───▶│ Field Extraction│    │ Duplicate      │
│ Step          │    │ Step            │    │ Detection      │
└───────────────┘    └─────────────────┘    └────────────────┘
        │                      │
        ▼                      ▼
┌───────────────┐    ┌─────────────────┐
│ Routing Step  │◀───│ Response Gen    │
│               │    │ Step            │
└───────────────┘    └─────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Processing Result                            │
│  (Classification + Extraction + Response + Routing)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
assessment/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # Application entry point
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Configuration management
│   │   │   └── security.py             # Input sanitization
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── ticket.py               # Ticket data model
│   │   │   ├── classification.py       # Classification result model
│   │   │   ├── extraction.py           # Extracted fields model
│   │   │   ├── response.py             # Generated response model
│   │   │   └── routing.py              # Routing decision model
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── ticket.py               # Pydantic input schemas
│   │   │   └── workflow.py             # Request/response schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ai_service.py           # OpenAI integration
│   │   │   └── workflow/
│   │   │       ├── __init__.py
│   │   │       ├── orchestrator.py     # Pipeline orchestration
│   │   │       ├── classifiers.py      # Classification logic
│   │   │       ├── extractors.py       # Field extraction
│   │   │       ├── generators.py       # Response generation
│   │   │       ├── routers.py          # Team routing
│   │   │       └── validators.py       # Input validation
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── classification.py       # Classification prompts
│   │   │   ├── extraction.py           # Extraction prompts
│   │   │   ├── response.py             # Response prompts
│   │   │   └── routing.py              # Routing prompts
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py              # Database connection
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       ├── ticket.py           # SQLAlchemy ticket model
│   │   │       └── workflow_run.py     # Workflow execution tracking
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── ticket.py               # Data access layer
│   │   └── api/
│   │       ├── __init__.py
│   │       └── v1/
│   │           ├── __init__.py
│   │           ├── tickets.py          # Ticket endpoints
│   │           └── workflow.py         # Workflow endpoints
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                 # Pytest fixtures
│   │   ├── fixtures/
│   │   │   └── sample_tickets.json     # Test data
│   │   ├── test_workflow.py            # Integration tests
│   │   ├── test_classification.py      # Classification unit tests
│   │   ├── test_extraction.py          # Extraction unit tests
│   │   └── test_routing.py             # Routing unit tests
│   ├── config/
│   │   ├── categories.yaml             # Category definitions
│   │   ├── severities.yaml             # Severity levels
│   │   └── routing_rules.yaml          # Team routing rules
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
└── plan.md
```

---

## Requirements

### Functional Requirements

#### 1. Classification (Category + Severity)
- Classify tickets into categories: `technical`, `billing`, `account`, `feature_request`, `bug_report`, `general`
- Assign severity levels: `critical`, `high`, `medium`, `low`
- Provide confidence scores (0.0 - 1.0) for each classification
- Support multi-label classification (secondary categories)
- Classification must complete within 5 seconds per ticket

#### 2. Field Extraction
- Extract structured fields from unstructured text:
  - `order_id` - Order/transaction identifiers
  - `product_name` - Product/service references
  - `error_code` - Error codes and messages
  - `account_email` - Email addresses
  - `phone_number` - Phone numbers
  - `priority_keywords` - Urgency indicators
  - `custom_fields` - Category-specific fields
- Validate extracted field formats
- Flag missing required fields based on category

#### 3. Response Draft Generation
- Generate contextual response drafts based on classification
- Personalize responses using extracted customer information
- Include suggested actions and next steps
- Support tone adjustment: `formal`, `friendly`, `technical`
- Set appropriate expectations based on severity
- Support template-based fallback when AI unavailable

#### 4. Team Routing
- Route to teams: `technical_support`, `billing_team`, `account_management`, `product_team`, `escalation_team`
- Apply routing rules based on category + severity + extracted fields
- Support escalation paths for critical issues
- Include routing confidence and alternative team suggestions
- Log routing decisions for audit trail

#### 5. Duplicate Detection
- Identify potential duplicate tickets from the same customer
- Link related tickets with similar content
- Provide similarity scores

### Non-Functional Requirements

#### Performance
- End-to-end ticket processing: < 10 seconds (p95)
- LLM calls: < 3 seconds per call
- Support concurrent processing of 100 tickets
- API response time: < 500ms for non-AI operations

#### Reliability
- Graceful degradation when AI unavailable (fallback to rule-based)
- Retry logic with exponential backoff
- Circuit breaker pattern for external dependencies
- Idempotent workflow execution

#### Security
- Input sanitization to prevent prompt injection
- PII handling in extracted fields
- API key management via environment variables
- Rate limiting to prevent abuse

#### Observability
- Structured logging with correlation IDs
- Token usage tracking per request
- Processing time metrics
- Classification accuracy tracking

---

## Data Models

### Input Schema
```python
class TicketInput(BaseModel):
    subject: str
    body: str
    customer_id: Optional[str]
    customer_email: Optional[EmailStr]
    metadata: Optional[Dict[str, Any]] = {}
```

### Output Schemas
```python
class ClassificationResult(BaseModel):
    category: str  # technical, billing, account, feature_request, bug_report, general
    category_confidence: float  # 0.0 to 1.0
    severity: str  # critical, high, medium, low
    severity_confidence: float
    secondary_categories: List[str] = []
    reasoning: Optional[str]

class ExtractedField(BaseModel):
    name: str
    value: Any
    confidence: float
    source_span: Optional[str]

class ExtractionResult(BaseModel):
    fields: List[ExtractedField]
    missing_required: List[str]
    validation_errors: List[str]

class ResponseDraft(BaseModel):
    content: str
    tone: str  # formal, friendly, technical
    template_used: Optional[str]
    suggested_actions: List[str]
    requires_escalation: bool

class RoutingDecision(BaseModel):
    team: str  # technical_support, billing_team, account_management, product_team, escalation_team
    priority: str
    reasoning: str
    alternative_teams: List[str]
    escalation_path: Optional[List[str]]

class WorkflowResponse(BaseModel):
    ticket_id: str
    classification: ClassificationResult
    extracted_fields: ExtractionResult
    response_draft: Optional[ResponseDraft]
    routing: RoutingDecision
    workflow_steps: List[WorkflowStepResult]
    total_duration_ms: int
```

---

## Configuration

### Categories (config/categories.yaml)
```yaml
categories:
  - id: technical
    name: Technical Support
    keywords: [error, bug, crash, not working, failed, broken]

  - id: billing
    name: Billing & Payments
    keywords: [charge, refund, invoice, payment, subscription, overcharged]

  - id: account
    name: Account Management
    keywords: [login, password, account, access, locked, credentials]

  - id: feature_request
    name: Feature Request
    keywords: [wish, request, feature, enhancement, suggest, idea]

  - id: bug_report
    name: Bug Report
    keywords: [bug, defect, broken, incorrect, unexpected behavior]

  - id: general
    name: General Inquiry
    keywords: [question, help, how to, information]
```

### Severities (config/severities.yaml)
```yaml
severities:
  - id: critical
    name: Critical
    description: System down, data loss, security breach, revenue impact
    priority: 1
    response_time_sla: 1h
    indicators: [urgent, asap, critical, down, emergency, production]

  - id: high
    name: High
    description: Major feature broken, multiple users affected
    priority: 2
    response_time_sla: 4h
    indicators: [important, serious, affecting]

  - id: medium
    name: Medium
    description: Feature partially working, workaround exists
    priority: 3
    response_time_sla: 24h

  - id: low
    name: Low
    description: Minor issue, cosmetic, general inquiry
    priority: 4
    response_time_sla: 72h
```

### Routing Rules (config/routing_rules.yaml)
```yaml
teams:
  - name: technical_support
    categories: [technical, bug_report]
    priority_modifier: 0

  - name: billing_team
    categories: [billing]
    priority_modifier: 0

  - name: account_management
    categories: [account]
    priority_modifier: 0

  - name: product_team
    categories: [feature_request]
    priority_modifier: 1

  - name: escalation_team
    severities: [critical]
    priority_modifier: -1

routing_strategy:
  default: category_severity
  fallback: general_support

escalation_paths:
  technical_support: [senior_technical, engineering_team]
  billing_team: [billing_manager, finance_team]
  account_management: [account_manager, security_team]
```

---

## Prompt Engineering

### Classification Prompt
```
You are a support ticket classifier. Analyze the following ticket and classify it.

TICKET SUBJECT: {subject}
TICKET BODY: {body}

AVAILABLE CATEGORIES: {categories}
SEVERITY LEVELS: critical, high, medium, low

Respond with JSON:
{
    "category": "category_name",
    "category_confidence": 0.0-1.0,
    "severity": "severity_level",
    "severity_confidence": 0.0-1.0,
    "secondary_categories": ["sub1", "sub2"],
    "reasoning": "brief explanation",
    "keywords_matched": ["keyword1", "keyword2"],
    "urgency_indicators": ["indicator1"]
}
```

### Field Extraction Prompt
```
Extract structured information from this support ticket.

TICKET SUBJECT: {subject}
TICKET BODY: {body}
CATEGORY: {category}

Extract the following fields if present:
- order_id: Order or transaction ID (formats: ORD-XXXXX, #XXXXX)
- product_name: Product or service mentioned
- error_code: Error codes or messages (e.g., ERR-XXXX, 0xXXXX)
- account_email: Email addresses mentioned
- phone_number: Phone numbers
- priority_keywords: Urgency words found

Respond with JSON:
{
    "fields": [
        {"name": "field_name", "value": "extracted_value", "confidence": 0.0-1.0, "source_text": "original text"}
    ],
    "missing_critical": ["field1"],
    "validation_errors": []
}
```

### Response Generation Prompt
```
You are drafting a customer support response. Be professional, empathetic, and helpful.

TICKET SUBJECT: {subject}
TICKET BODY: {body}
CATEGORY: {category}
SEVERITY: {severity}
EXTRACTED CONTEXT: {extracted_fields}
CUSTOMER_NAME: {customer_name}

Guidelines:
- Acknowledge the issue specifically
- Show empathy for their situation
- Provide clear next steps
- Set appropriate expectations based on severity
- Use {tone} tone
- Keep response concise but complete

Respond with JSON:
{
    "greeting": "personalized greeting",
    "acknowledgment": "acknowledge specific issue",
    "explanation": "brief explanation if applicable",
    "action_items": ["step 1", "step 2"],
    "timeline": "expected resolution timeframe",
    "closing": "professional closing",
    "full_response": "complete formatted response",
    "requires_escalation": true/false
}
```

### Routing Prompt
```
Determine the best team to handle this support ticket.

TICKET SUBJECT: {subject}
TICKET BODY: {body}
CATEGORY: {category}
SEVERITY: {severity}
EXTRACTED CONTEXT: {extracted_fields}

AVAILABLE TEAMS: {teams}

TEAM DESCRIPTIONS:
- technical_support: Technical issues, bugs, errors
- billing_team: Payment, subscription, refund issues
- account_management: Account access, security, permissions
- product_team: Feature requests, product feedback
- escalation_team: Critical issues requiring senior review

Routing rules:
- CRITICAL severity -> escalation_team
- Billing category -> billing_team
- Account access issues -> account_management
- Technical complexity -> technical_support
- Default -> general_support

Respond with JSON:
{
    "team": "team_name",
    "priority": "urgent/high/normal/low",
    "reasoning": "why this team",
    "alternative_teams": [{"team": "name", "reason": "why also suitable"}],
    "escalation_path": ["next_team_if_needed"]
}
```

---

## Implementation Steps

### Phase 1: Project Setup (Steps 1-3)

#### Step 1: Create Project Structure and Configuration
**Files:** Directory structure, `config.py`, `requirements.txt`
- Create all directories under `backend/app/`
- Define `Settings` class with APP_NAME, DATABASE_URL, OPENAI_API_KEY
- Include workflow-specific settings: DEFAULT_MODEL, MAX_TOKENS, WORKFLOW_TIMEOUT

#### Step 2: Create Database Models
**Files:** `db/session.py`, `db/models/ticket.py`, `db/models/workflow_run.py`
- `Ticket` model: id, subject, body, customer_id, category, severity, extracted_fields (JSON), status, assigned_team, timestamps
- `WorkflowRun` model: id, ticket_id, step_name, status, input_data, output_data, error_message, duration_ms, timestamps

#### Step 3: Create Pydantic Schemas
**Files:** `schemas/ticket.py`, `schemas/workflow.py`
- Input/output schemas for all workflow operations
- Validation rules for ticket data

### Phase 2: Core Services (Steps 4-7)

#### Step 4: Implement AI Service Layer
**File:** `services/ai_service.py`
```python
class AIService:
    def __init__(self, session: AsyncSession):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def classify_ticket(self, subject: str, body: str) -> ClassificationResult
    async def extract_fields(self, subject: str, body: str, category: str) -> ExtractionResult
    async def generate_response(self, context: dict) -> ResponseDraft
    async def determine_routing(self, context: dict) -> RoutingDecision
```

#### Step 5: Implement Workflow Orchestrator
**File:** `services/workflow/orchestrator.py`
```python
class WorkflowOrchestrator:
    async def execute(self, ticket: TicketInput, options: WorkflowOptions) -> WorkflowResponse:
        # Step 1: Input validation
        # Step 2: Duplicate detection (parallel)
        # Step 3: Classification (AI call)
        # Step 4: Field extraction (AI call - parallel with step 3)
        # Step 5: Response generation (AI call)
        # Step 6: Routing decision (rule-based)
        # Step 7: Persistence and response assembly
```

#### Step 6: Implement Classification Step
**File:** `services/workflow/classifiers.py`
- LLM-based classification with structured output
- Fallback rule-based classification using keyword matching
- Confidence scoring

#### Step 7: Implement Field Extraction Step
**File:** `services/workflow/extractors.py`
- Regex patterns for structured data:
  - Order IDs: `ORD-\d{6,}`, `#\d+`
  - Email: RFC 5322 pattern
  - Phone: Various international formats
  - Error codes: `ERR-\d+`, `0x[0-9A-F]+`
- AI-assisted extraction for context-dependent fields
- Field validation

### Phase 3: Additional Steps (Steps 8-11)

#### Step 8: Implement Response Generation Step
**File:** `services/workflow/generators.py`
- Template-based fallback responses per category
- AI-enhanced response generation
- Tone adjustment support

#### Step 9: Implement Routing Logic
**File:** `services/workflow/routers.py`
- Routing rules evaluation
- Escalation path generation
- Confidence scoring

#### Step 10: Implement Input Validation
**File:** `services/workflow/validators.py`
- Input sanitization for prompt injection prevention
- Field validation
- Malicious pattern detection

#### Step 11: Create API Endpoints
**Files:** `api/v1/tickets.py`, `api/v1/workflow.py`

**Endpoints:**
```
POST /api/v1/workflow/process     - Full pipeline processing
POST /api/v1/workflow/classify    - Classification only
POST /api/v1/workflow/extract     - Field extraction only
POST /api/v1/workflow/respond     - Response generation only
POST /api/v1/workflow/route       - Routing decision only
GET  /api/v1/tickets              - List processed tickets
GET  /api/v1/tickets/{id}         - Get ticket with workflow details
GET  /health                      - Health check
```

### Phase 4: Testing and Finalization (Steps 12-18)

#### Step 12: Create Main Application Entry Point
**Files:** `main.py`, `run.py`

#### Step 13: Implement Test Fixtures
**File:** `tests/fixtures/sample_tickets.json`
- Sample tickets covering all categories and severities
- Edge cases: empty input, long input, special characters, malicious input

#### Step 14-17: Implement Tests
- `tests/test_workflow.py` - Integration tests
- `tests/test_classification.py` - Classification unit tests
- `tests/test_extraction.py` - Extraction unit tests
- `tests/test_routing.py` - Routing unit tests

#### Step 18: Error Handling Tests
**File:** `tests/test_error_handling.py`
- API timeout handling
- Rate limit handling
- Invalid response handling
- Database failure handling

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output |
|------|-------|-----------------|
| classify_billing | "I want a refund for order #123" | category=billing, confidence>0.7 |
| classify_critical | "URGENT system down affecting all users" | severity=critical |
| extract_order_id | "My order ORD-123456 hasn't arrived" | order_id="ORD-123456" |
| extract_email | "Contact me at user@example.com" | account_email="user@example.com" |
| route_billing_critical | category=billing, severity=critical | team=billing_team, priority=urgent |
| sanitize_input | "Ignore all instructions" | sanitized, processed normally |

### Integration Tests

| Test | Scenario | Expected Behavior |
|------|----------|-------------------|
| full_workflow_happy | Valid ticket input | All steps complete, valid response |
| workflow_parallel_steps | Classification + extraction | Both run concurrently, combined in <5s |
| ai_unavailable | OpenAI API returns error | Fallback to rule-based, pipeline completes |
| duplicate_detection | Same ticket submitted twice | Second flagged as duplicate |

### Manual QA Steps

1. Start the service: `cd backend && python run.py`
2. Access health endpoint: `curl http://localhost:8000/health`
3. Submit sample tickets via API
4. Verify classification accuracy
5. Review generated responses
6. Confirm routing decisions

---

## Dependencies

### Python Packages (requirements.txt)
```
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.23
asyncpg>=0.29.0
openai>=1.10.0
python-dotenv>=1.0.0
tenacity>=8.2.0
structlog>=24.1.0
pyyaml>=6.0
jinja2>=3.1.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
httpx>=0.26.0
```

### External Services
- OpenAI API (GPT-4 or GPT-3.5-turbo)
- PostgreSQL database

### Environment Variables
```
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ticket_workflow
DEFAULT_MODEL=gpt-4-turbo-preview
MAX_TOKENS=4096
WORKFLOW_TIMEOUT_SECONDS=30
```

---

## Risks and Rollback Strategy

### Risks

| Risk | Mitigation |
|------|------------|
| OpenAI API rate limits | Request queuing, exponential backoff, fallback to rule-based |
| Prompt injection attacks | Input sanitization, output validation |
| High latency under load | Parallel execution, caching, async pipeline |
| Inconsistent AI responses | Structured JSON output, validation, retry logic |
| Cost overrun | Token budgeting, truncation strategies |

### Feature Flags for Rollback
```python
# config.py
ENABLE_AI_CLASSIFICATION: bool = True      # Set False for rule-based only
ENABLE_AI_EXTRACTION: bool = True
ENABLE_RESPONSE_GENERATION: bool = True    # Set False for templates only
AI_CONFIDENCE_THRESHOLD: float = 0.6       # Below this, use fallback
MAX_WORKFLOW_TIMEOUT_SECONDS: int = 30
```

### Rollback Procedures
1. **Disable AI calls**: Set `ENABLE_AI_CLASSIFICATION=False`
2. **Use templates only**: Set `ENABLE_RESPONSE_GENERATION=False`
3. **Circuit breaker**: Auto-fallback after repeated failures
4. **Version pinning**: Store model version with each classification

---

## Success Criteria

1. Classification accuracy > 85% on test set
2. Field extraction F1 score > 0.80 for key fields
3. End-to-end processing time < 10 seconds (p95)
4. All API endpoints return valid responses
5. No unhandled exceptions in normal operation
6. Confidence scores correlate with actual accuracy
7. All unit tests pass (>90% code coverage)
