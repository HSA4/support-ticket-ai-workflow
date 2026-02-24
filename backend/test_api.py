#!/usr/bin/env python3
"""
Comprehensive API Test Script for Support Ticket AI Workflow
Generates a detailed test report with all endpoints, payloads, and responses.
"""

import httpx
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:8000"
REPORT_FILE = "test_results/api_test_report.md"

# Test cases
TEST_CASES = {
    "health": [
        {
            "name": "Health Check",
            "method": "GET",
            "endpoint": "/health",
            "payload": None
        }
    ],
    "info": [
        {
            "name": "API Root Information",
            "method": "GET",
            "endpoint": "/",
            "payload": None
        }
    ],
    "workflow_full": [
        {
            "name": "Technical Issue - Application Crash",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Application crashes on startup",
                    "body": "Hi, I have been trying to launch the application but it keeps crashing. I get an error code ERR-5003 every time. My order ID is ORD-12345. This is urgent!",
                    "customer_email": "john.doe@example.com"
                }
            }
        },
        {
            "name": "Billing Issue - Double Charge",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Double charged for subscription",
                    "body": "Hello, I was charged twice this month for my Pro subscription. The amounts are $29.99 on January 15th and again on January 20th. My order IDs are ORD-111 and ORD-112. Please refund the duplicate. My email is sarah@test.com.",
                    "customer_email": "sarah@test.com"
                }
            }
        },
        {
            "name": "Account Issue - Login Problem",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Cannot login to my account",
                    "body": "I have been trying to login for the past hour but keep getting an error saying invalid credentials. I am sure my password is correct. Can you help me reset or verify my account?",
                    "customer_email": "locked.user@company.org"
                }
            }
        },
        {
            "name": "Feature Request - Dark Mode",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Request for dark mode feature",
                    "body": "Hi there! I love using your application. Would it be possible to add a dark mode option? It would be great for late night work sessions. Keep up the good work!",
                    "customer_email": "happy.user@email.com"
                }
            }
        },
        {
            "name": "Critical Issue - Production Down",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "URGENT: Production system down",
                    "body": "EMERGENCY!!! Our entire production system is down and we have detected data loss. This is affecting all 500+ users. Customers cannot access their accounts. Revenue is being lost every minute. Error: 0xDEADBEEF. Need immediate assistance!!! Contact: 555-123-4567",
                    "customer_email": "admin@enterprise-corp.com",
                    "metadata": {"tier": "enterprise", "source": "phone_escalation"}
                }
            }
        }
    ],
    "workflow_classify": [
        {
            "name": "Classify Bug Report",
            "method": "POST",
            "endpoint": "/api/v1/workflow/classify",
            "payload": {
                "subject": "Bug in export feature",
                "body": "When I try to export my report to PDF, the application freezes. This happens every time without fail. Error message shows ERR-EXP-001."
            }
        }
    ],
    "workflow_extract": [
        {
            "name": "Extract Fields from Order Ticket",
            "method": "POST",
            "endpoint": "/api/v1/workflow/extract",
            "payload": {
                "subject": "Order ORD-789012 never arrived",
                "body": "My order #ORD-789012 was supposed to arrive on 2024-01-15 but I still haven't received it. You can reach me at waiting.customer@email.com or 555-987-6543. The order was for $149.99.",
                "category": "billing"
            }
        }
    ],
    "workflow_respond": [
        {
            "name": "Generate Response for Technical Issue",
            "method": "POST",
            "endpoint": "/api/v1/workflow/respond",
            "payload": {
                "subject": "Need help with installation",
                "body": "I downloaded the software but can't figure out how to install it. The instructions aren't clear.",
                "category": "technical",
                "severity": "medium",
                "extracted_fields": {"fields": []},
                "tone": "friendly"
            }
        }
    ],
    "workflow_route": [
        {
            "name": "Route Critical Billing Issue",
            "method": "POST",
            "endpoint": "/api/v1/workflow/route",
            "payload": {
                "subject": "Critical payment failure",
                "body": "Payment processing is completely down. All transactions failing. Urgent!",
                "category": "billing",
                "severity": "critical",
                "extracted_fields": {"fields": []}
            }
        }
    ],
    "edge_cases": [
        {
            "name": "Minimal Ticket Content",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Help",
                    "body": "?"
                }
            }
        },
        {
            "name": "Unicode and Special Characters",
            "method": "POST",
            "endpoint": "/api/v1/workflow/process",
            "payload": {
                "ticket": {
                    "subject": "Problème avec l'application 🚨",
                    "body": "Hola! Tengo un problema. L'application ne fonctionne pas! Error: ERR-ÜNİCÖDÉ. Email: test@例え.jp"
                }
            }
        }
    ]
}


class TestRunner:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0
        self.total_time = 0

    def run_test(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test case."""
        result = {
            "name": test_case["name"],
            "method": test_case["method"],
            "endpoint": test_case["endpoint"],
            "payload": test_case.get("payload"),
            "status_code": None,
            "response": None,
            "response_time": None,
            "success": False,
            "error": None
        }

        try:
            url = f"{self.base_url}{test_case['endpoint']}"
            start_time = time.time()

            with httpx.Client(timeout=120.0) as client:
                if test_case["method"] == "GET":
                    response = client.get(url)
                else:
                    response = client.post(
                        url,
                        json=test_case.get("payload"),
                        headers={"Content-Type": "application/json"}
                    )

            end_time = time.time()
            result["response_time"] = round(end_time - start_time, 3)
            result["status_code"] = response.status_code
            result["success"] = 200 <= response.status_code < 300

            try:
                result["response"] = response.json()
            except:
                result["response"] = response.text

            if result["success"]:
                self.passed += 1
            else:
                self.failed += 1

            self.total_time += result["response_time"]

        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
            self.failed += 1

        self.results.append(result)
        return result

    def run_all(self) -> None:
        """Run all test cases."""
        print("Running API tests...")
        for category, tests in TEST_CASES.items():
            print(f"  Testing {category}...")
            for test in tests:
                self.run_test(test)
                status = "✓" if self.results[-1]["success"] else "✗"
                print(f"    {status} {test['name']}")

    def generate_report(self) -> str:
        """Generate markdown test report."""
        report = []
        report.append("# Support Ticket AI Workflow - API Test Report\n")
        report.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Base URL:** `{self.base_url}`\n")
        report.append(f"**LLM Provider:** OpenRouter (anthropic/claude-3.5-sonnet)\n\n")

        # Summary
        report.append("## Test Summary\n\n")
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        report.append(f"| Metric | Value |\n")
        report.append(f"|--------|-------|\n")
        report.append(f"| Total Tests | {total} |\n")
        report.append(f"| Passed | {self.passed} |\n")
        report.append(f"| Failed | {self.failed} |\n")
        report.append(f"| Pass Rate | {pass_rate:.1f}% |\n")
        report.append(f"| Total Time | {self.total_time:.2f}s |\n")
        report.append(f"| Avg Response Time | {self.total_time/total:.2f}s |\n\n")

        # Detailed Results
        report.append("---\n\n")
        report.append("## Detailed Test Results\n\n")

        for category, tests in TEST_CASES.items():
            report.append(f"### {category.replace('_', ' ').title()}\n\n")

            for test in tests:
                # Find result
                result = next((r for r in self.results if r["name"] == test["name"]), None)
                if not result:
                    continue

                status_emoji = "✅" if result["success"] else "❌"
                report.append(f"#### {status_emoji} {result['name']}\n\n")

                # Request
                report.append("**Request:**\n\n")
                report.append(f"```http\n{result['method']} {result['endpoint']}\n")
                if result["payload"]:
                    report.append(f"\n{json.dumps(result['payload'], indent=2)}\n")
                report.append("```\n\n")

                # Response info
                report.append("**Response:**\n\n")
                report.append(f"- Status Code: `{result['status_code']}`\n")
                report.append(f"- Response Time: `{result['response_time']}s`\n")
                if result["error"]:
                    report.append(f"- Error: `{result['error']}`\n")
                report.append("\n")

                # Response body
                report.append("```json\n")
                if result["response"]:
                    report.append(json.dumps(result["response"], indent=2, default=str))
                report.append("\n```\n\n")
                report.append("---\n\n")

        return "".join(report)


def main():
    runner = TestRunner(BASE_URL)
    runner.run_all()
    report = runner.generate_report()

    # Save report
    with open(REPORT_FILE, "w") as f:
        f.write(report)

    print(f"\nTest report saved to: {REPORT_FILE}")
    print(f"Passed: {runner.passed}/{runner.passed + runner.failed}")

    return runner


if __name__ == "__main__":
    main()
