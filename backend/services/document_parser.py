import json
from ..config import settings

# Try to import OpenAI, but provide mock if not available or API key not set
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def parse_document_with_llm(document_text: str, prompt: str) -> dict:
    if not HAS_OPENAI or not settings.openai_api_key:
        return get_mock_response()

    try:
        client = OpenAI(api_key=settings.openai_api_key)
        message = client.messages.create(
            model="gpt-4-turbo-preview",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": f"{prompt}\n\n---\nDocument:\n{document_text}"
                }
            ]
        )
        response_text = message.content[0].text
        result = json.loads(response_text)
        return result
    except Exception as e:
        return get_mock_response()


def get_mock_response() -> dict:
    return {
        "extracted_terms": {
            "penalty_clauses": [
                "Service availability below 99% results in $100/hour penalty",
                "Response time above 2 seconds incurs $50/hour credit"
            ],
            "service_levels": [
                "99% uptime SLA",
                "2 second max response time",
                "99.9% data accuracy"
            ],
            "calculation_formulas": [
                "penalty = hours_below_sla * 100",
                "credit = hours_above_threshold * 50"
            ],
            "applicable_periods": [
                "Business hours (9 AM - 5 PM)",
                "Excludes scheduled maintenance windows"
            ]
        },
        "sql_query": """
            SELECT
                CAST(incident_date AS DATE) as date,
                CASE
                    WHEN uptime_percent < 99 THEN (100 - uptime_percent) * 100
                    ELSE 0
                END as penalty_monetary,
                CASE
                    WHEN avg_response_time > 2 THEN (avg_response_time - 2) * 50
                    ELSE 0
                END as credit_units,
                uptime_percent,
                avg_response_time
            FROM data
            WHERE CAST(incident_date AS DATE) >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY incident_date
        """
    }
