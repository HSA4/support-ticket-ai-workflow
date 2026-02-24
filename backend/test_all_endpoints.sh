#!/bin/bash
BASE_URL="http://localhost:8000"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT="test_results/test_report_${TIMESTAMP}.md"

echo "# Support Ticket AI Workflow - API Test Report" > $REPORT
echo "" >> $REPORT
echo "**Generated:** $(date)" >> $REPORT
echo "**Base URL:** $BASE_URL" >> $REPORT
echo "" >> $REPORT

# Function to test endpoint and save results
test_endpoint() {
    local method=$1
    local endpoint=$2
    local payload=$3
    local test_name=$4
    
    echo "### $test_name" >> $REPORT
    echo "" >> $REPORT
    
    # Request section
    echo "#### Request" >> $REPORT
    echo '```' >> $REPORT
    echo "$method $endpoint" >> $REPORT
    if [ -n "$payload" ]; then
        echo "" >> $REPORT
        echo "$payload" | python3 -m json.tool 2>/dev/null || echo "$payload"
    fi
    echo '```' >> $REPORT
    echo "" >> $REPORT
    
    # Execute request
    if [ -n "$payload" ]; then
        response=$(curl -s -X $method "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$payload" \
            -w "\n---STATUS:%{http_code}---TIME:%{time_total}s---")
    else
        response=$(curl -s -X $method "${BASE_URL}${endpoint}" \
            -w "\n---STATUS:%{http_code}---TIME:%{time_total}s---")
    fi
    
    # Extract status and time
    status=$(echo "$response" | grep -oP '---STATUS:\K\d+')
    time=$(echo "$response" | grep -oP '---TIME:\K[0-9.]+')
    body=$(echo "$response" | sed 's/---STATUS:.*---//')
    
    # Response section
    echo "#### Response" >> $REPORT
    echo "- **Status Code:** $status" >> $REPORT
    echo "- **Response Time:** ${time}s" >> $REPORT
    echo "" >> $REPORT
    echo '```json' >> $REPORT
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    echo '```' >> $REPORT
    echo "" >> $REPORT
    echo "---" >> $REPORT
    echo "" >> $REPORT
}

# ============================================
# 1. Health Check
# ============================================
echo "## 1. Health Check" >> $REPORT
echo "" >> $REPORT

test_endpoint "GET" "/health" "" "1.1 Health Check"

# ============================================
# 2. Root/API Info
# ============================================
echo "## 2. API Information" >> $REPORT
echo "" >> $REPORT

test_endpoint "GET" "/" "" "2.1 Root Endpoint"

# ============================================
# 3. Full Workflow
# ============================================
echo "## 3. Full Workflow Processing" >> $REPORT
echo "" >> $REPORT

# Technical ticket
test_endpoint "POST" "/api/v1/workflow/process" '{
  "ticket": {
    "subject": "Application crashes on startup",
    "body": "Hi, I have been trying to launch the application but it keeps crashing. I get an error code ERR-5003 every time. My order ID is ORD-12345. This is urgent!",
    "customer_email": "john.doe@example.com"
  }
}' "3.1 Technical Issue - Application Crash"

# Billing ticket
test_endpoint "POST" "/api/v1/workflow/process" '{
  "ticket": {
    "subject": "Double charged for subscription",
    "body": "Hello, I was charged twice this month for my Pro subscription. The amounts are $29.99 each. My order IDs are ORD-111 and ORD-112. Please refund the duplicate.",
    "customer_email": "sarah@test.com"
  }
}' "3.2 Billing Issue - Double Charge"

# Account issue
test_endpoint "POST" "/api/v1/workflow/process" '{
  "ticket": {
    "subject": "Cannot login to my account",
    "body": "I have been trying to login for the past hour but keep getting an error saying invalid credentials. I am sure my password is correct. Can you help?",
    "customer_email": "locked.user@company.org"
  }
}' "3.3 Account Issue - Login Problem"

# Feature request
test_endpoint "POST" "/api/v1/workflow/process" '{
  "ticket": {
    "subject": "Request for dark mode feature",
    "body": "Hi there! I love using your application. Would it be possible to add a dark mode option? It would be great for late night work sessions. Keep up the good work!",
    "customer_email": "happy.user@email.com"
  }
}' "3.4 Feature Request - Dark Mode"

# Critical issue
test_endpoint "POST" "/api/v1/workflow/process" '{
  "ticket": {
    "subject": "URGENT: Production system down - data loss",
    "body": "EMERGENCY!!! Our entire production system is down and we have detected data loss. This is affecting all 500+ users. Customers cannot access their accounts. Revenue is being lost every minute. Error: 0xDEADBEEF. Need immediate assistance!!! Contact: 555-123-4567",
    "customer_email": "admin@enterprise-corp.com",
    "metadata": {"tier": "enterprise", "source": "phone_escalation"}
  }
}' "3.5 Critical Issue - Production Down"

echo "Test report saved to: $REPORT"
cat $REPORT
