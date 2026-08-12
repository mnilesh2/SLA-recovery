DEFAULT_PROMPT = """Analyze this SLA/service level agreement document and extract:
1. All penalty clauses and recovery conditions
2. Service level targets and thresholds
3. Calculation formulas and metrics
4. Applicable time periods and conditions

Based on the extracted information, generate a SQL query that:
- Identifies all instances where penalties apply
- Calculates penalty amounts based on extracted formulas
- Returns results with original vs. calculated costs
- Includes all supporting evidence and data points
- return only SQL query

Respond with JSON containing:
{
    "extracted_terms": {
        "penalty_clauses": [list of penalty clauses],
        "service_levels": [list of service levels],
        "calculation_formulas": [list of formulas],
        "applicable_periods": [list of time periods]
    },
    "sql_query": "SELECT ... FROM ... WHERE ..."
}"""


def resolve_prompt(custom_prompt: str = None) -> str:
    if custom_prompt and custom_prompt.strip():
        return custom_prompt
    return DEFAULT_PROMPT
