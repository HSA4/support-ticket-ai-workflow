# Support Ticket AI Workflow - API Test Report
**Generated:** 2026-02-24 21:34:56
**Base URL:** `http://localhost:8000`
**LLM Provider:** OpenRouter (anthropic/claude-3.5-sonnet)

## Test Summary

| Metric | Value |
|--------|-------|
| Total Tests | 13 |
| Passed | 13 |
| Failed | 0 |
| Pass Rate | 100.0% |
| Total Time | 122.18s |
| Avg Response Time | 9.40s |

---

## Detailed Test Results

### Health

#### ✅ Health Check

**Request:**

```http
GET /health
```

**Response:**

- Status Code: `200`
- Response Time: `0.054s`

```json
{
  "status": "healthy",
  "timestamp": "2026-02-24T19:32:53.991862",
  "version": "1.0.0",
  "ai_enabled": true
}
```

---

### Info

#### ✅ API Root Information

**Request:**

```http
GET /
```

**Response:**

- Status Code: `200`
- Response Time: `0.017s`

```json
{
  "name": "Support Ticket AI Workflow",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### Workflow Full

#### ✅ Technical Issue - Application Crash

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Application crashes on startup",
    "body": "Hi, I have been trying to launch the application but it keeps crashing. I get an error code ERR-5003 every time. My order ID is ORD-12345. This is urgent!",
    "customer_email": "john.doe@example.com"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `17.144s`

```json
{
  "ticket_id": "3e10eb75-043e-43ee-8e6e-b4d0fe864066",
  "classification": {
    "category": "technical",
    "category_confidence": 0.95,
    "severity": "high",
    "severity_confidence": 0.85,
    "secondary_categories": [
      "bug_report"
    ],
    "reasoning": "Application crash on startup with specific error code indicates a critical technical issue preventing core functionality",
    "keywords_matched": [
      "crashes",
      "error code",
      "ERR-5003",
      "launch"
    ],
    "urgency_indicators": [
      "keeps crashing",
      "This is urgent!",
      "startup issue"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "order_id",
        "value": "ORD-12345",
        "confidence": 1.0,
        "source_span": "My order ID is ORD-12345"
      },
      {
        "name": "error_code",
        "value": "ERR-5003",
        "confidence": 1.0,
        "source_span": "I get an error code ERR-5003 every time"
      },
      {
        "name": "product_name",
        "value": "startup\nHi",
        "confidence": 0.7,
        "source_span": "on startup\nHi"
      },
      {
        "name": "priority_keywords",
        "value": [
          "urgent"
        ],
        "confidence": 1.0,
        "source_span": "This is urgent!"
      }
    ],
    "missing_required": [],
    "validation_errors": []
  },
  "response_draft": {
    "content": "Hello john.doe,\n\nThank you for reaching out about the technical issue you're experiencing.\n\nOur technical team has been notified and is investigating the problem.\n\nHere are some steps you can take:\n  1. Please try clearing your browser cache and cookies\n  2. Ensure you're using the latest version of the application\n  3. If the issue persists, please provide any error messages you see\n\nWe aim to respond within 4 hours.\n\nBest regards,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "technical_template",
    "suggested_actions": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "requires_escalation": true,
    "greeting": "Hello john.doe,",
    "acknowledgment": "Thank you for reaching out about the technical issue you're experiencing.",
    "explanation": "Our technical team has been notified and is investigating the problem.",
    "action_items": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "timeline": "We aim to respond within 4 hours.",
    "closing": "Best regards,\nCustomer Support Team"
  },
  "routing": {
    "team": "technical_support",
    "priority": "high",
    "reasoning": "Routed to technical_support based on technical category with high priority and detected fields: order_id, error_code, product_name.",
    "alternative_teams": [],
    "escalation_path": [
      "senior_technical",
      "engineering_team"
    ],
    "confidence": 0.95
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:32:54.031934",
      "completed_at": "2026-02-24T19:32:54.031936",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:32:54.032008",
      "completed_at": "2026-02-24T19:32:54.032009",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:32:58.149024",
      "completed_at": "2026-02-24T19:32:58.149029",
      "duration_ms": 4116,
      "error": null,
      "fallback_used": false,
      "tokens_used": 22499
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:33:00.196183",
      "completed_at": "2026-02-24T19:33:00.196185",
      "duration_ms": 6162,
      "error": null,
      "fallback_used": false,
      "tokens_used": 22993
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:11.153354",
      "completed_at": "2026-02-24T19:33:11.153357",
      "duration_ms": 10957,
      "error": null,
      "fallback_used": false,
      "tokens_used": 23726
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:33:11.153449",
      "completed_at": "2026-02-24T19:33:11.153450",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 17121,
  "created_at": "2026-02-24T19:33:11.153492"
}
```

---

#### ✅ Billing Issue - Double Charge

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Double charged for subscription",
    "body": "Hello, I was charged twice this month for my Pro subscription. The amounts are $29.99 on January 15th and again on January 20th. My order IDs are ORD-111 and ORD-112. Please refund the duplicate. My email is sarah@test.com.",
    "customer_email": "sarah@test.com"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `15.052s`

```json
{
  "ticket_id": "9d2e90f9-b788-4e64-a69d-ea59b0bb72a1",
  "classification": {
    "category": "billing",
    "category_confidence": 0.98,
    "severity": "high",
    "severity_confidence": 0.85,
    "secondary_categories": [
      "account"
    ],
    "reasoning": "Customer reports double billing for subscription, which involves direct financial impact and requires immediate attention for refund",
    "keywords_matched": [
      "charged twice",
      "subscription",
      "refund",
      "order IDs",
      "amounts"
    ],
    "urgency_indicators": [
      "double charged",
      "duplicate payment"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "account_email",
        "value": "sarah@test.com",
        "confidence": 1.0,
        "source_span": "My email is sarah@test.com"
      },
      {
        "name": "error_code",
        "value": "ORD-112",
        "confidence": 0.85,
        "source_span": "ORD-112"
      },
      {
        "name": "product_name",
        "value": "Pro subscription",
        "confidence": 0.9,
        "source_span": "my Pro subscription"
      },
      {
        "name": "order_id",
        "value": [
          "ORD-111",
          "ORD-112"
        ],
        "confidence": 1.0,
        "source_span": "My order IDs are ORD-111 and ORD-112"
      },
      {
        "name": "priority_keywords",
        "value": [],
        "confidence": 1.0,
        "source_span": ""
      }
    ],
    "missing_required": [],
    "validation_errors": [
      "Field 'order_id' with value '['ORD-111', 'ORD-112']' does not match expected format"
    ]
  },
  "response_draft": {
    "content": "Dear sarah,\n\nThank you for contacting us about your billing inquiry.\n\nOur billing team will review your request and get back to you shortly.\n\nHere are some steps you can take:\n  1. Please have your order ID ready for verification\n  2. Check your account settings for recent transactions\n\nWe typically resolve billing inquiries within 4 hours.\n\nSincerely,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "billing_template",
    "suggested_actions": [
      "Please have your order ID ready for verification",
      "Check your account settings for recent transactions"
    ],
    "requires_escalation": true,
    "greeting": "Dear sarah,",
    "acknowledgment": "Thank you for contacting us about your billing inquiry.",
    "explanation": "Our billing team will review your request and get back to you shortly.",
    "action_items": [
      "Please have your order ID ready for verification",
      "Check your account settings for recent transactions"
    ],
    "timeline": "We typically resolve billing inquiries within 4 hours.",
    "closing": "Sincerely,\nCustomer Support Team"
  },
  "routing": {
    "team": "billing_team",
    "priority": "high",
    "reasoning": "Routed to billing_team based on billing category with high priority and detected fields: account_email, error_code, product_name.",
    "alternative_teams": [
      "technical_support"
    ],
    "escalation_path": [
      "billing_manager",
      "finance_team"
    ],
    "confidence": 0.95
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:11.175848",
      "completed_at": "2026-02-24T19:33:11.175851",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:33:11.175949",
      "completed_at": "2026-02-24T19:33:11.175951",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:33:15.760799",
      "completed_at": "2026-02-24T19:33:15.760802",
      "duration_ms": 4584,
      "error": null,
      "fallback_used": false,
      "tokens_used": 24117
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:33:16.888026",
      "completed_at": "2026-02-24T19:33:16.888029",
      "duration_ms": 5710,
      "error": null,
      "fallback_used": false,
      "tokens_used": 24739
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:26.205529",
      "completed_at": "2026-02-24T19:33:26.205531",
      "duration_ms": 9317,
      "error": null,
      "fallback_used": false,
      "tokens_used": 25548
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:33:26.205598",
      "completed_at": "2026-02-24T19:33:26.205599",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 15029,
  "created_at": "2026-02-24T19:33:26.205628"
}
```

---

#### ✅ Account Issue - Login Problem

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Cannot login to my account",
    "body": "I have been trying to login for the past hour but keep getting an error saying invalid credentials. I am sure my password is correct. Can you help me reset or verify my account?",
    "customer_email": "locked.user@company.org"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `12.09s`

```json
{
  "ticket_id": "bb7efce0-dbd2-4e72-998a-6384a5c19fbd",
  "classification": {
    "category": "account",
    "category_confidence": 0.95,
    "severity": "high",
    "severity_confidence": 0.85,
    "secondary_categories": [
      "technical"
    ],
    "reasoning": "User is completely blocked from accessing their account, which is a core functionality issue. The problem is specifically related to login and credentials, making it primarily an account issue.",
    "keywords_matched": [
      "login",
      "password",
      "credentials",
      "account",
      "reset"
    ],
    "urgency_indicators": [
      "past hour",
      "keep getting error",
      "cannot login"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "error_code",
        "value": "invalid credentials",
        "confidence": 0.9,
        "source_span": "error saying invalid credentials"
      },
      {
        "name": "priority_keywords",
        "value": [
          "help me"
        ],
        "confidence": 0.9,
        "source_span": "help me"
      }
    ],
    "missing_required": [],
    "validation_errors": [
      "Field 'error_code' with value 'invalid credentials' does not match expected format"
    ]
  },
  "response_draft": {
    "content": "Hi locked.user,\n\nThank you for reaching out about your account.\n\nOur account management team is here to help you with your request.\n\nHere are some steps you can take:\n  1. Please verify your email address associated with the account\n  2. For security purposes, do not share your password\n\nWe'll respond to your request within 4 hours.\n\nBest regards,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "account_template",
    "suggested_actions": [
      "Please verify your email address associated with the account",
      "For security purposes, do not share your password"
    ],
    "requires_escalation": true,
    "greeting": "Hi locked.user,",
    "acknowledgment": "Thank you for reaching out about your account.",
    "explanation": "Our account management team is here to help you with your request.",
    "action_items": [
      "Please verify your email address associated with the account",
      "For security purposes, do not share your password"
    ],
    "timeline": "We'll respond to your request within 4 hours.",
    "closing": "Best regards,\nCustomer Support Team"
  },
  "routing": {
    "team": "account_management",
    "priority": "high",
    "reasoning": "Routed to account_management based on account category with high priority and detected fields: error_code, priority_keywords.",
    "alternative_teams": [
      "technical_support"
    ],
    "escalation_path": [
      "account_manager",
      "security_team"
    ],
    "confidence": 0.95
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:26.229219",
      "completed_at": "2026-02-24T19:33:26.229221",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:33:26.229304",
      "completed_at": "2026-02-24T19:33:26.229305",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:33:29.790212",
      "completed_at": "2026-02-24T19:33:29.790217",
      "duration_ms": 3559,
      "error": null,
      "fallback_used": false,
      "tokens_used": 25968
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:33:30.610803",
      "completed_at": "2026-02-24T19:33:30.610809",
      "duration_ms": 4381,
      "error": null,
      "fallback_used": false,
      "tokens_used": 26344
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:38.295858",
      "completed_at": "2026-02-24T19:33:38.295860",
      "duration_ms": 7684,
      "error": null,
      "fallback_used": false,
      "tokens_used": 27035
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:33:38.295921",
      "completed_at": "2026-02-24T19:33:38.295922",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 12066,
  "created_at": "2026-02-24T19:33:38.295948"
}
```

---

#### ✅ Feature Request - Dark Mode

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Request for dark mode feature",
    "body": "Hi there! I love using your application. Would it be possible to add a dark mode option? It would be great for late night work sessions. Keep up the good work!",
    "customer_email": "happy.user@email.com"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `12.401s`

```json
{
  "ticket_id": "599d36f6-9a8d-4fbd-b07c-9d14a6d6c44a",
  "classification": {
    "category": "feature_request",
    "category_confidence": 0.95,
    "severity": "low",
    "severity_confidence": 0.85,
    "secondary_categories": [
      "general"
    ],
    "reasoning": "User is requesting a new feature (dark mode) in a positive and non-urgent manner. This is a clear feature enhancement request rather than a technical issue or bug.",
    "keywords_matched": [
      "add",
      "dark mode",
      "option",
      "would it be possible"
    ],
    "urgency_indicators": [
      "no urgent language used",
      "positive tone"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "product_name",
        "value": "application",
        "confidence": 0.8,
        "source_span": "I love using your application"
      }
    ],
    "missing_required": [],
    "validation_errors": []
  },
  "response_draft": {
    "content": "Hello happy.user,\n\nThank you for taking the time to share your feature request with us.\n\nWe value your feedback and will consider it for future product development.\n\nHere are some steps you can take:\n  1. Your request has been logged in our feature tracking system\n  2. We'll notify you if this feature gets implemented\n\nProduct updates are typically shared in our monthly newsletter.\n\nThank you for helping us improve!\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "feature_request_template",
    "suggested_actions": [
      "Your request has been logged in our feature tracking system",
      "We'll notify you if this feature gets implemented"
    ],
    "requires_escalation": false,
    "greeting": "Hello happy.user,",
    "acknowledgment": "Thank you for taking the time to share your feature request with us.",
    "explanation": "We value your feedback and will consider it for future product development.",
    "action_items": [
      "Your request has been logged in our feature tracking system",
      "We'll notify you if this feature gets implemented"
    ],
    "timeline": "Product updates are typically shared in our monthly newsletter.",
    "closing": "Thank you for helping us improve!\nCustomer Support Team"
  },
  "routing": {
    "team": "product_team",
    "priority": "normal",
    "reasoning": "Routed to product_team based on feature_request category and detected fields: product_name.",
    "alternative_teams": [
      "technical_support"
    ],
    "escalation_path": null,
    "confidence": 0.9
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:38.319130",
      "completed_at": "2026-02-24T19:33:38.319132",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:33:38.319223",
      "completed_at": "2026-02-24T19:33:38.319224",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:33:41.499872",
      "completed_at": "2026-02-24T19:33:41.499875",
      "duration_ms": 3178,
      "error": null,
      "fallback_used": false,
      "tokens_used": 27399
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:33:42.174527",
      "completed_at": "2026-02-24T19:33:42.174532",
      "duration_ms": 3855,
      "error": null,
      "fallback_used": false,
      "tokens_used": 27775
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:50.696671",
      "completed_at": "2026-02-24T19:33:50.696672",
      "duration_ms": 8521,
      "error": null,
      "fallback_used": false,
      "tokens_used": 28418
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:33:50.696741",
      "completed_at": "2026-02-24T19:33:50.696741",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 12377,
  "created_at": "2026-02-24T19:33:50.696769"
}
```

---

#### ✅ Critical Issue - Production Down

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "URGENT: Production system down",
    "body": "EMERGENCY!!! Our entire production system is down and we have detected data loss. This is affecting all 500+ users. Customers cannot access their accounts. Revenue is being lost every minute. Error: 0xDEADBEEF. Need immediate assistance!!! Contact: 555-123-4567",
    "customer_email": "admin@enterprise-corp.com",
    "metadata": {
      "tier": "enterprise",
      "source": "phone_escalation"
    }
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `19.331s`

```json
{
  "ticket_id": "fbced87e-44f5-4cad-9296-49e8b9754629",
  "classification": {
    "category": "technical",
    "category_confidence": 0.95,
    "severity": "critical",
    "severity_confidence": 0.98,
    "secondary_categories": [
      "bug_report"
    ],
    "reasoning": "System-wide outage with data loss affecting all users and revenue impact indicates critical technical issue",
    "keywords_matched": [
      "system down",
      "data loss",
      "production",
      "error",
      "cannot access"
    ],
    "urgency_indicators": [
      "URGENT",
      "EMERGENCY",
      "affecting all 500+ users",
      "revenue is being lost",
      "immediate assistance",
      "entire production system down"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "phone_number",
        "value": "555-123-4567",
        "confidence": 1.0,
        "source_span": "Contact: 555-123-4567"
      },
      {
        "name": "error_code",
        "value": "0xDEADBEEF",
        "confidence": 1.0,
        "source_span": "Error: 0xDEADBEEF"
      },
      {
        "name": "product_name",
        "value": "ion system is down and we have detected data loss",
        "confidence": 0.7,
        "source_span": "production system is down and we have detected data loss"
      },
      {
        "name": "priority_keywords",
        "value": [
          "urgent",
          "emergency"
        ],
        "confidence": 0.9,
        "source_span": "urgent, emergency"
      }
    ],
    "missing_required": [],
    "validation_errors": []
  },
  "response_draft": {
    "content": "Hello admin,\n\nThank you for reaching out about the technical issue you're experiencing.\n\nOur technical team has been notified and is investigating the problem.\n\nHere are some steps you can take:\n  1. Please try clearing your browser cache and cookies\n  2. Ensure you're using the latest version of the application\n  3. If the issue persists, please provide any error messages you see\n\nWe aim to respond within 1 hour.\n\nBest regards,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "technical_template",
    "suggested_actions": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "requires_escalation": true,
    "greeting": "Hello admin,",
    "acknowledgment": "Thank you for reaching out about the technical issue you're experiencing.",
    "explanation": "Our technical team has been notified and is investigating the problem.",
    "action_items": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "timeline": "We aim to respond within 1 hour.",
    "closing": "Best regards,\nCustomer Support Team"
  },
  "routing": {
    "team": "escalation_team",
    "priority": "urgent",
    "reasoning": "Critical severity requires escalation team",
    "alternative_teams": [
      "technical_support"
    ],
    "escalation_path": null,
    "confidence": 0.95
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:33:50.720165",
      "completed_at": "2026-02-24T19:33:50.720167",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:33:50.720245",
      "completed_at": "2026-02-24T19:33:50.720246",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:33:55.696077",
      "completed_at": "2026-02-24T19:33:55.696080",
      "duration_ms": 4975,
      "error": null,
      "fallback_used": false,
      "tokens_used": 28865
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:33:57.846725",
      "completed_at": "2026-02-24T19:33:57.846728",
      "duration_ms": 7124,
      "error": null,
      "fallback_used": false,
      "tokens_used": 29406
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:34:10.027474",
      "completed_at": "2026-02-24T19:34:10.027477",
      "duration_ms": 12180,
      "error": null,
      "fallback_used": false,
      "tokens_used": 30216
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:34:10.027532",
      "completed_at": "2026-02-24T19:34:10.027533",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 19307,
  "created_at": "2026-02-24T19:34:10.027561"
}
```

---

### Workflow Classify

#### ✅ Classify Bug Report

**Request:**

```http
POST /api/v1/workflow/classify

{
  "subject": "Bug in export feature",
  "body": "When I try to export my report to PDF, the application freezes. This happens every time without fail. Error message shows ERR-EXP-001."
}
```

**Response:**

- Status Code: `200`
- Response Time: `4.724s`

```json
{
  "category": "bug_report",
  "category_confidence": 0.95,
  "severity": "high",
  "severity_confidence": 0.85,
  "secondary_categories": [
    "technical"
  ],
  "reasoning": "Application freezing and error code indicate a clear bug in core functionality (export feature). High severity due to complete feature failure and consistent reproducibility.",
  "keywords_matched": [
    "bug",
    "freeze",
    "error",
    "ERR-EXP-001",
    "export"
  ],
  "urgency_indicators": [
    "happens every time",
    "application freezes",
    "without fail"
  ]
}
```

---

### Workflow Extract

#### ✅ Extract Fields from Order Ticket

**Request:**

```http
POST /api/v1/workflow/extract

{
  "subject": "Order ORD-789012 never arrived",
  "body": "My order #ORD-789012 was supposed to arrive on 2024-01-15 but I still haven't received it. You can reach me at waiting.customer@email.com or 555-987-6543. The order was for $149.99.",
  "category": "billing"
}
```

**Response:**

- Status Code: `200`
- Response Time: `4.598s`

```json
{
  "fields": [
    {
      "name": "order_id",
      "value": "ORD-789012",
      "confidence": 1.0,
      "source_span": "Order #ORD-789012"
    },
    {
      "name": "account_email",
      "value": "waiting.customer@email.com",
      "confidence": 1.0,
      "source_span": "waiting.customer@email.com"
    },
    {
      "name": "phone_number",
      "value": "555-987-6543",
      "confidence": 1.0,
      "source_span": "555-987-6543"
    },
    {
      "name": "error_code",
      "value": "ORD-789012",
      "confidence": 0.85,
      "source_span": "ORD-789012"
    },
    {
      "name": "date",
      "value": "2024-01-15",
      "confidence": 0.7,
      "source_span": "2024-01-15"
    }
  ],
  "missing_required": [
    "amount"
  ],
  "validation_errors": []
}
```

---

### Workflow Respond

#### ✅ Generate Response for Technical Issue

**Request:**

```http
POST /api/v1/workflow/respond

{
  "subject": "Need help with installation",
  "body": "I downloaded the software but can't figure out how to install it. The instructions aren't clear.",
  "category": "technical",
  "severity": "medium",
  "extracted_fields": {
    "fields": []
  },
  "tone": "friendly"
}
```

**Response:**

- Status Code: `200`
- Response Time: `10.14s`

```json
{
  "content": "Hello,\n\nThank you for reaching out about the technical issue you're experiencing.\n\nOur technical team has been notified and is investigating the problem.\n\nHere are some steps you can take:\n  1. Please try clearing your browser cache and cookies\n  2. Ensure you're using the latest version of the application\n  3. If the issue persists, please provide any error messages you see\n\nWe aim to respond within 24 hours.\n\nBest regards,\nCustomer Support Team",
  "tone": "friendly",
  "template_used": "technical_template",
  "suggested_actions": [
    "Please try clearing your browser cache and cookies",
    "Ensure you're using the latest version of the application",
    "If the issue persists, please provide any error messages you see"
  ],
  "requires_escalation": false,
  "greeting": "Hello,",
  "acknowledgment": "Thank you for reaching out about the technical issue you're experiencing.",
  "explanation": "Our technical team has been notified and is investigating the problem.",
  "action_items": [
    "Please try clearing your browser cache and cookies",
    "Ensure you're using the latest version of the application",
    "If the issue persists, please provide any error messages you see"
  ],
  "timeline": "We aim to respond within 24 hours.",
  "closing": "Best regards,\nCustomer Support Team"
}
```

---

### Workflow Route

#### ✅ Route Critical Billing Issue

**Request:**

```http
POST /api/v1/workflow/route

{
  "subject": "Critical payment failure",
  "body": "Payment processing is completely down. All transactions failing. Urgent!",
  "category": "billing",
  "severity": "critical",
  "extracted_fields": {
    "fields": []
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `0.027s`

```json
{
  "team": "escalation_team",
  "priority": "urgent",
  "reasoning": "Critical severity requires escalation team",
  "alternative_teams": [
    "technical_support"
  ],
  "escalation_path": null,
  "confidence": 0.95
}
```

---

### Edge Cases

#### ✅ Minimal Ticket Content

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Help",
    "body": "?"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `10.616s`

```json
{
  "ticket_id": "9e94a75a-f911-41e2-b324-f9f517bf9e57",
  "classification": {
    "category": "general",
    "category_confidence": 0.9,
    "severity": "low",
    "severity_confidence": 0.8,
    "secondary_categories": [],
    "reasoning": "Ticket contains only 'Help' and '?' with no specific details, indicating a general inquiry without clear context or urgency",
    "keywords_matched": [
      "help"
    ],
    "urgency_indicators": []
  },
  "extracted_fields": {
    "fields": [],
    "missing_required": [],
    "validation_errors": []
  },
  "response_draft": {
    "content": "Hello,\n\nThank you for contacting our support team.\n\nWe're here to help and will address your inquiry as soon as possible.\n\nHere are some steps you can take:\n  1. Please provide any additional details that might help us assist you better\n\nWe aim to respond within 72 hours.\n\nBest regards,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "general_template",
    "suggested_actions": [
      "Please provide any additional details that might help us assist you better"
    ],
    "requires_escalation": false,
    "greeting": "Hello,",
    "acknowledgment": "Thank you for contacting our support team.",
    "explanation": "We're here to help and will address your inquiry as soon as possible.",
    "action_items": [
      "Please provide any additional details that might help us assist you better"
    ],
    "timeline": "We aim to respond within 72 hours.",
    "closing": "Best regards,\nCustomer Support Team"
  },
  "routing": {
    "team": "technical_support",
    "priority": "low",
    "reasoning": "Routed to technical_support based on general category.",
    "alternative_teams": [],
    "escalation_path": [
      "senior_technical",
      "engineering_team"
    ],
    "confidence": 0.8
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:34:29.539443",
      "completed_at": "2026-02-24T19:34:29.539445",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:34:29.539519",
      "completed_at": "2026-02-24T19:34:29.539520",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:34:32.146989",
      "completed_at": "2026-02-24T19:34:32.146995",
      "duration_ms": 2605,
      "error": null,
      "fallback_used": false,
      "tokens_used": 32103
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:34:32.971207",
      "completed_at": "2026-02-24T19:34:32.971215",
      "duration_ms": 3431,
      "error": null,
      "fallback_used": false,
      "tokens_used": 32407
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:34:40.133031",
      "completed_at": "2026-02-24T19:34:40.133034",
      "duration_ms": 7161,
      "error": null,
      "fallback_used": false,
      "tokens_used": 32954
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:34:40.133112",
      "completed_at": "2026-02-24T19:34:40.133114",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 10593,
  "created_at": "2026-02-24T19:34:40.133149"
}
```

---

#### ✅ Unicode and Special Characters

**Request:**

```http
POST /api/v1/workflow/process

{
  "ticket": {
    "subject": "Probl\u00e8me avec l'application \ud83d\udea8",
    "body": "Hola! Tengo un problema. L'application ne fonctionne pas! Error: ERR-\u00dcN\u0130C\u00d6D\u00c9. Email: test@\u4f8b\u3048.jp"
  }
}
```

**Response:**

- Status Code: `200`
- Response Time: `15.99s`

```json
{
  "ticket_id": "e7206047-9480-48d5-bc61-4a3b7b538b3b",
  "classification": {
    "category": "technical",
    "category_confidence": 0.9,
    "severity": "high",
    "severity_confidence": 0.8,
    "secondary_categories": [
      "bug_report"
    ],
    "reasoning": "The ticket describes an application error with a specific error code (ERR-\u00dcN\u0130C\u00d6D\u00c9), indicating a technical issue. The multilingual nature (French, Spanish) and presence of Unicode characters suggest possible internationalization issues.",
    "keywords_matched": [
      "error",
      "application",
      "ne fonctionne pas",
      "problema"
    ],
    "urgency_indicators": [
      "\ud83d\udea8",
      "error"
    ]
  },
  "extracted_fields": {
    "fields": [
      {
        "name": "error_code",
        "value": "ERR-\u00dcN\u0130C\u00d6D\u00c9",
        "confidence": 0.9,
        "source_span": "Error: ERR-\u00dcN\u0130C\u00d6D\u00c9"
      },
      {
        "name": "account_email",
        "value": "test@\u4f8b\u3048.jp",
        "confidence": 1.0,
        "source_span": "Email: test@\u4f8b\u3048.jp"
      },
      {
        "name": "priority_keywords",
        "value": "\ud83d\udea8",
        "confidence": 0.7,
        "source_span": "Probl\u00e8me avec l'application \ud83d\udea8"
      }
    ],
    "missing_required": [],
    "validation_errors": [
      "Field 'error_code' with value 'ERR-\u00dcN\u0130C\u00d6D\u00c9' does not match expected format",
      "Field 'account_email' with value 'test@\u4f8b\u3048.jp' does not match expected format"
    ]
  },
  "response_draft": {
    "content": "Hello test,\n\nThank you for reaching out about the technical issue you're experiencing.\n\nOur technical team has been notified and is investigating the problem.\n\nHere are some steps you can take:\n  1. Please try clearing your browser cache and cookies\n  2. Ensure you're using the latest version of the application\n  3. If the issue persists, please provide any error messages you see\n\nWe aim to respond within 4 hours.\n\nBest regards,\nCustomer Support Team",
    "tone": "friendly",
    "template_used": "technical_template",
    "suggested_actions": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "requires_escalation": true,
    "greeting": "Hello test,",
    "acknowledgment": "Thank you for reaching out about the technical issue you're experiencing.",
    "explanation": "Our technical team has been notified and is investigating the problem.",
    "action_items": [
      "Please try clearing your browser cache and cookies",
      "Ensure you're using the latest version of the application",
      "If the issue persists, please provide any error messages you see"
    ],
    "timeline": "We aim to respond within 4 hours.",
    "closing": "Best regards,\nCustomer Support Team"
  },
  "routing": {
    "team": "technical_support",
    "priority": "high",
    "reasoning": "Routed to technical_support based on technical category with high priority and detected fields: error_code, account_email, priority_keywords.",
    "alternative_teams": [],
    "escalation_path": [
      "senior_technical",
      "engineering_team"
    ],
    "confidence": 0.95
  },
  "duplicate_of": null,
  "similarity_score": null,
  "workflow_steps": [
    {
      "step_name": "validation",
      "status": "completed",
      "started_at": "2026-02-24T19:34:40.156297",
      "completed_at": "2026-02-24T19:34:40.156299",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "duplicate_detection",
      "status": "completed",
      "started_at": "2026-02-24T19:34:40.156380",
      "completed_at": "2026-02-24T19:34:40.156381",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    },
    {
      "step_name": "classification",
      "status": "completed",
      "started_at": "2026-02-24T19:34:44.745095",
      "completed_at": "2026-02-24T19:34:44.745097",
      "duration_ms": 4588,
      "error": null,
      "fallback_used": false,
      "tokens_used": 33364
    },
    {
      "step_name": "extraction",
      "status": "completed",
      "started_at": "2026-02-24T19:34:47.612944",
      "completed_at": "2026-02-24T19:34:47.612949",
      "duration_ms": 7454,
      "error": null,
      "fallback_used": false,
      "tokens_used": 33887
    },
    {
      "step_name": "response_generation",
      "status": "completed",
      "started_at": "2026-02-24T19:34:56.123063",
      "completed_at": "2026-02-24T19:34:56.123065",
      "duration_ms": 8509,
      "error": null,
      "fallback_used": false,
      "tokens_used": 34665
    },
    {
      "step_name": "routing",
      "status": "completed",
      "started_at": "2026-02-24T19:34:56.123131",
      "completed_at": "2026-02-24T19:34:56.123132",
      "duration_ms": 0,
      "error": null,
      "fallback_used": false,
      "tokens_used": null
    }
  ],
  "total_duration_ms": 15966,
  "created_at": "2026-02-24T19:34:56.123157"
}
```

---

