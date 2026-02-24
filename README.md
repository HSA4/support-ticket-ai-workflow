# Support Ticket AI Workflow

An intelligent support ticket processing system that uses AI to automatically classify, extract information, generate responses, and route tickets to the appropriate teams.

## Features

- **Automatic Classification** - Categorizes tickets (technical, billing, account, feature_request, bug_report, general) and assigns severity levels (critical, high, medium, low)
- **Field Extraction** - Extracts structured data (order IDs, error codes, emails, phone numbers) from ticket content
- **Response Generation** - Creates contextual, empathetic response drafts
- **Intelligent Routing** - Routes tickets to appropriate teams based on classification
- **Duplicate Detection** - Identifies potential duplicate tickets
- **Fallback Support** - Rule-based fallback when AI is unavailable
- **OpenRouter Integration** - Supports multiple LLM providers via OpenRouter

## Requirements

- Python 3.11+
- PostgreSQL 15+ (optional, for persistence)
- OpenRouter API key (or OpenAI API key)

## Quick Start

### Option 1: Run Without Docker

```bash
# Clone the repository
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run the application
python run.py
```

The API will be available at `http://localhost:8000`

### Option 2: Run With Docker

```bash
# Clone the repository
cd backend

# Configure environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f app
```

The API will be available at `http://localhost:8000`

### Option 3: Run With Docker (Development Mode)

```bash
# Run with hot-reload enabled
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# LLM Provider Configuration
LLM_PROVIDER=openrouter

# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-api-key-here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Support Ticket AI Workflow

# Model Configuration
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
FALLBACK_MODEL=openai/gpt-4o-mini
MAX_TOKENS=4096
TEMPERATURE=0.3

# Database Configuration
DATABASE_URL=postgresql+asyncpg://ticketuser:ticketpass@localhost:5432/ticket_workflow

# Feature Flags
ENABLE_AI_CLASSIFICATION=true
ENABLE_AI_EXTRACTION=true
ENABLE_RESPONSE_GENERATION=true

# Workflow Configuration
WORKFLOW_TIMEOUT_SECONDS=30
AI_CONFIDENCE_THRESHOLD=0.6
```

### Available Models (OpenRouter)

| Model | Description | Use Case |
|-------|-------------|----------|
| `anthropic/claude-3.5-sonnet` | Recommended, best quality | Production |
| `anthropic/claude-3-haiku` | Fast and cheap | Development |
| `openai/gpt-4o` | OpenAI GPT-4 | Alternative |
| `openai/gpt-4o-mini` | Fast, affordable | Cost optimization |
| `google/gemini-pro-1.5` | Google's model | Alternative |

## API Endpoints

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API documentation |

### Workflow Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/workflow/process` | Full workflow (classify, extract, respond, route) |
| POST | `/api/v1/workflow/classify` | Classification only |
| POST | `/api/v1/workflow/extract` | Field extraction only |
| POST | `/api/v1/workflow/respond` | Response generation only |
| POST | `/api/v1/workflow/route` | Routing decision only |

### Example: Process a Ticket

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Application crashes on startup",
      "body": "Hi, I have been trying to launch the application but it keeps crashing. I get an error code ERR-5003 every time. This is urgent!",
      "customer_email": "john.doe@example.com"
    }
  }'
```

### Example Response

```json
{
  "ticket_id": "3e10eb75-043e-43ee-8e6e-b4d0fe864066",
  "classification": {
    "category": "technical",
    "category_confidence": 0.95,
    "severity": "high",
    "severity_confidence": 0.85,
    "secondary_categories": ["bug_report"],
    "reasoning": "Application crash on startup with specific error code",
    "keywords_matched": ["crashes", "error code", "ERR-5003"],
    "urgency_indicators": ["urgent", "keeps crashing"]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "error_code",
        "value": "ERR-5003",
        "confidence": 1.0
      }
    ]
  },
  "response_draft": {
    "content": "Hello john.doe,\n\nThank you for reaching out...",
    "tone": "friendly",
    "suggested_actions": ["Please try clearing your browser cache..."]
  },
  "routing": {
    "team": "technical_support",
    "priority": "high",
    "reasoning": "Routed based on technical category with high priority"
  },
  "total_duration_ms": 17143
}
```

## API Examples

### 1. Health Check

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-24T19:29:56.721568",
  "version": "1.0.0",
  "ai_enabled": true
}
```

---

### 2. Process Ticket - Technical Issue

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Application crashes on startup",
      "body": "Hi, I have been trying to launch the application but it keeps crashing. I get an error code ERR-5003 every time. This is urgent!",
      "customer_email": "john.doe@example.com"
    }
  }'
```

**Response:**
```json
{
  "ticket_id": "3e10eb75-043e-43ee-8e6e-b4d0fe864066",
  "classification": {
    "category": "technical",
    "category_confidence": 0.95,
    "severity": "high",
    "severity_confidence": 0.85,
    "secondary_categories": ["bug_report"],
    "keywords_matched": ["crashes", "error code", "ERR-5003"],
    "urgency_indicators": ["urgent"]
  },
  "routing": {
    "team": "technical_support",
    "priority": "high"
  }
}
```

---

### 3. Process Ticket - Billing Issue

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Double charged for subscription",
      "body": "Hello, I was charged twice this month for my Pro subscription. The amounts are $29.99 on January 15th and again on January 20th. My order IDs are ORD-111 and ORD-112. Please refund the duplicate.",
      "customer_email": "sarah@test.com"
    }
  }'
```

**Response:**
```json
{
  "classification": {
    "category": "billing",
    "category_confidence": 0.98,
    "severity": "high"
  },
  "extracted_fields": {
    "fields": [
      {"name": "order_id", "value": ["ORD-111", "ORD-112"], "confidence": 1.0},
      {"name": "product_name", "value": "Pro subscription", "confidence": 0.9}
    ]
  },
  "routing": {
    "team": "billing_team",
    "priority": "high"
  }
}
```

---

### 4. Process Ticket - Critical Issue (Escalation)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "URGENT: Production system down",
      "body": "EMERGENCY!!! Our entire production system is down and we have detected data loss. This is affecting all 500+ users. Error: 0xDEADBEEF.",
      "customer_email": "admin@enterprise-corp.com"
    }
  }'
```

**Response:**
```json
{
  "classification": {
    "category": "technical",
    "severity": "critical",
    "severity_confidence": 0.98,
    "urgency_indicators": ["URGENT", "EMERGENCY", "production system down"]
  },
  "routing": {
    "team": "escalation_team",
    "priority": "urgent"
  }
}
```

---

### 5. Process Ticket - Feature Request

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Request for dark mode feature",
      "body": "Hi there! I love using your application. Would it be possible to add a dark mode option?",
      "customer_email": "happy.user@email.com"
    }
  }'
```

**Response:**
```json
{
  "classification": {
    "category": "feature_request",
    "category_confidence": 0.95,
    "severity": "low"
  },
  "routing": {
    "team": "product_team",
    "priority": "normal"
  }
}
```

---

### 6. Classify Only

```bash
curl -X POST http://localhost:8000/api/v1/workflow/classify \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Bug in export feature",
    "body": "When I try to export my report to PDF, the application freezes. This happens every time without fail. Error message shows ERR-EXP-001."
  }'
```

**Response:**
```json
{
  "category": "bug_report",
  "category_confidence": 0.92,
  "severity": "high",
  "severity_confidence": 0.85,
  "secondary_categories": ["technical"],
  "keywords_matched": ["bug", "export", "freezes", "error"],
  "urgency_indicators": ["every time without fail"]
}
```

---

### 7. Extract Fields Only

```bash
curl -X POST http://localhost:8000/api/v1/workflow/extract \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Order ORD-789012 never arrived",
    "body": "My order #ORD-789012 was supposed to arrive on 2024-01-15. You can reach me at waiting.customer@email.com or 555-987-6543. The order was for $149.99.",
    "category": "billing"
  }'
```

**Response:**
```json
{
  "fields": [
    {"name": "order_id", "value": "ORD-789012", "confidence": 1.0},
    {"name": "account_email", "value": "waiting.customer@email.com", "confidence": 1.0},
    {"name": "phone_number", "value": "555-987-6543", "confidence": 0.95}
  ],
  "missing_required": [],
  "validation_errors": []
}
```

---

### 8. Generate Response Only

```bash
curl -X POST http://localhost:8000/api/v1/workflow/respond \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Need help with installation",
    "body": "I downloaded the software but cannot figure out how to install it.",
    "category": "technical",
    "severity": "medium",
    "extracted_fields": {"fields": []},
    "tone": "friendly"
  }'
```

**Response:**
```json
{
  "content": "Hello,\n\nThank you for reaching out about the installation issue.\n\nHere are the steps to install the software:\n  1. Locate the downloaded file\n  2. Double-click the installer\n  3. Follow the on-screen prompts\n\nWe aim to respond within 24 hours.\n\nBest regards,\nCustomer Support Team",
  "tone": "friendly",
  "suggested_actions": [
    "Locate the downloaded file",
    "Double-click the installer",
    "Follow the on-screen prompts"
  ],
  "requires_escalation": false
}
```

---

### 9. Route Only

```bash
curl -X POST http://localhost:8000/api/v1/workflow/route \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Critical payment failure",
    "body": "Payment processing is completely down. All transactions failing. Urgent!",
    "category": "billing",
    "severity": "critical",
    "extracted_fields": {"fields": []}
  }'
```

**Response:**
```json
{
  "team": "escalation_team",
  "priority": "urgent",
  "reasoning": "Critical severity requires escalation team",
  "alternative_teams": ["billing_team", "technical_support"],
  "confidence": 0.95
}
```

---

### 10. With Options

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Need help understanding the dashboard",
      "body": "I am new to the platform and having trouble understanding the analytics dashboard."
    },
    "options": {
      "response_tone": "formal",
      "enable_parallel": true,
      "skip_response_generation": false
    }
  }'
```

---

### 11. Minimal Content (Edge Case)

```bash
curl -X POST http://localhost:8000/api/v1/workflow/process \
  -H "Content-Type: application/json" \
  -d '{
    "ticket": {
      "subject": "Help",
      "body": "?"
    }
  }'
```

**Response:**
```json
{
  "classification": {
    "category": "general",
    "category_confidence": 0.9,
    "severity": "low",
    "reasoning": "The ticket contains only minimal information"
  },
  "response_draft": {
    "content": "Hello,\n\nThank you for contacting our support team...\n\nPlease provide any additional details..."
  }
}
```

---

### 12. Python Client Example

```python
import httpx
import asyncio

async def process_ticket():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/workflow/process",
            json={
                "ticket": {
                    "subject": "Application crashes on startup",
                    "body": "I get an error code ERR-5003 every time.",
                    "customer_email": "user@example.com"
                }
            },
            timeout=60.0
        )

        result = response.json()
        print(f"Category: {result['classification']['category']}")
        print(f"Severity: {result['classification']['severity']}")
        print(f"Team: {result['routing']['team']}")

asyncio.run(process_ticket())
```

---

### 13. JavaScript/Fetch Example

```javascript
async function processTicket() {
  const response = await fetch('http://localhost:8000/api/v1/workflow/process', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      ticket: {
        subject: 'Application crashes on startup',
        body: 'I get an error code ERR-5003 every time.',
        customer_email: 'user@example.com'
      }
    })
  });

  const result = await response.json();
  console.log('Category:', result.classification.category);
  console.log('Team:', result.routing.team);
}

processTicket();
```

## Testing

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html
```

### Run API Tests

```bash
# Ensure the application is running
python run.py

# In another terminal, run API tests
source venv/bin/activate
python test_api.py
```

### Run with Postman

1. Import `postman_collection.json` into Postman
2. Import `postman_environment.json` for environment variables
3. Run the collection

## Test Results

### Summary (2026-02-24)

| Metric | Value |
|--------|-------|
| Total Tests | 13 |
| Passed | 13 |
| Failed | 0 |
| Pass Rate | 100% |
| Avg Response Time | ~9.4s |

### Classification Accuracy

| Ticket Type | Accuracy | Confidence |
|-------------|----------|------------|
| Technical | 100% | 95%+ |
| Billing | 100% | 98%+ |
| Account | 100% | 95%+ |
| Feature Request | 100% | 95%+ |
| Critical Issues | 100% | 95%+ |

### Field Extraction

| Field Type | Accuracy | Confidence |
|------------|----------|------------|
| Error Codes | 100% | 100% |
| Order IDs | 100% | 100% |
| Email Addresses | 100% | 100% |
| Phone Numbers | 100% | 100% |
| Priority Keywords | 95% | 90% |

### Routing Accuracy

| Category | Severity | Correct Team | Accuracy |
|----------|----------|--------------|----------|
| technical | high | technical_support | 100% |
| billing | high | billing_team | 100% |
| account | high | account_management | 100% |
| feature_request | low | product_team | 100% |
| technical | critical | escalation_team | 100% |

Detailed test results are available in `test_results/api_test_report.md`

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py           # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py     # Dependency injection
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── tickets.py      # Ticket endpoints
│   │       └── workflow.py     # Workflow endpoints
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py          # Database session
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── ticket.py       # Ticket ORM model
│   │       └── workflow_run.py # Workflow run model
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── ticket.py           # Ticket schemas
│   │   └── workflow.py         # Workflow schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py       # OpenRouter/LLM integration
│   │   └── workflow/
│   │       ├── __init__.py
│   │       ├── orchestrator.py # Pipeline orchestration
│   │       ├── classifiers.py  # Classification logic
│   │       ├── extractors.py   # Field extraction
│   │       ├── generators.py   # Response generation
│   │       ├── routers.py      # Team routing
│   │       └── validators.py   # Input validation
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── classification.py   # Classification prompts
│   │   ├── extraction.py       # Extraction prompts
│   │   ├── response.py         # Response prompts
│   │   └── routing.py          # Routing prompts
│   └── repositories/
│       ├── __init__.py
│       └── ticket.py           # Data access layer
├── config/
│   ├── categories.yaml         # Category definitions
│   ├── severities.yaml         # Severity levels
│   └── routing_rules.yaml      # Routing rules
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Pytest fixtures
│   ├── fixtures/
│   │   └── sample_tickets.json # Test data
│   ├── test_classification.py
│   ├── test_extraction.py
│   ├── test_routing.py
│   └── test_workflow.py
├── test_results/
│   ├── api_test_report.md      # Full test report
│   └── test_summary.md         # Test summary
├── Dockerfile
├── docker-compose.yml
├── docker-compose.dev.yml
├── requirements.txt
├── run.py                      # Application runner
├── test_api.py                 # API test script
├── postman_collection.json     # Postman collection
├── postman_environment.json    # Postman environment
├── .env.example
└── README.md
```

## Technology Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| LLM Provider | OpenRouter |
| Default Model | anthropic/claude-3.5-sonnet |
| Database | PostgreSQL (optional) |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Async HTTP | httpx |
| Retry Logic | tenacity |
| Testing | pytest, pytest-asyncio |

## Categories & Teams

### Ticket Categories

| Category | Description |
|----------|-------------|
| `technical` | Technical issues, bugs, errors |
| `billing` | Payment, subscription, refund issues |
| `account` | Login, password, account access |
| `feature_request` | Feature suggestions, enhancements |
| `bug_report` | Bug reports, defects |
| `general` | General inquiries |

### Severity Levels

| Severity | SLA | Description |
|----------|-----|-------------|
| `critical` | 1 hour | System down, data loss, security issues |
| `high` | 4 hours | Major feature broken, significant impact |
| `medium` | 24 hours | Feature partially working |
| `low` | 72 hours | Minor issue, general inquiry |

### Routing Teams

| Team | Handles |
|------|---------|
| `technical_support` | Technical issues, bugs |
| `billing_team` | Payment, subscription issues |
| `account_management` | Account access, security |
| `product_team` | Feature requests |
| `escalation_team` | Critical issues |

## Troubleshooting

### Common Issues

**1. OpenRouter API errors**
```bash
# Verify API key is set
echo $OPENROUTER_API_KEY

# Test API connectivity
curl -s http://localhost:8000/health
```

**2. Database connection errors**
```bash
# Start PostgreSQL with Docker
docker-compose up -d db

# Or disable database (runs in-memory)
# Set DATABASE_URL to empty string
```

**3. Port already in use**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process or change port
APP_PORT=8001 python run.py
```

### Logs

```bash
# View application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f app
```
