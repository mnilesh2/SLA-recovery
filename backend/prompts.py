"""SLA document parsing prompt — now generic and configurable."""

from ..pipeline_config import PipelineConfig


DEFAULT_PROMPT = f"""You are an SLA (Service Level Agreement) expert. Analyze the provided SLA document carefully and extract:

1. **Penalty Clauses**: List all specific penalty conditions, amounts, and triggers
2. **Service Level Targets**: Extract all uptime %, response time, error rate, or other SLA metrics with their targets
3. **Calculation Formulas**: Identify how penalties are calculated (e.g., "penalty = hours_missed * $X/hour")
4. **Applicable Periods**: Note time periods, exclusions (maintenance windows), and conditions that apply

Based on the CSV data structure provided, generate a SQL query that:
- Identifies all breaches and violations based on the extracted SLA terms
- Calculates penalties/credits using the extracted formulas
- Groups results by time period to match the SLA measurement period
- Returns columns named with configured suffixes for cost calculations
- Uses ONLY the exact column names provided in the CSV schema

CRITICAL INSTRUCTIONS FOR SQL GENERATION:
1. The CSV table is named '{PipelineConfig.TABLE_NAME}'
2. Use column names EXACTLY as provided (case-sensitive)
3. Generate VALID DuckDB SYNTAX ONLY (NOT PostgreSQL):
   - Use TRY_CAST(column AS FLOAT) for safe type conversion (returns NULL on failure, not error)
   - Use CASE WHEN ... THEN 1 ELSE 0 END for conditional counting
   - DO NOT use CAST(), use TRY_CAST() instead
   - DO NOT use :: operator (PostgreSQL syntax)
4. Handle mixed-type columns safely:
   - Some CSV columns may contain both numbers and text (e.g., status labels alongside numeric readings)
   - Always use TRY_CAST to safely handle mixed types
   - Filter with: WHERE TRY_CAST(column AS FLOAT) IS NOT NULL before numeric comparison
5. IMPORTANT: Return columns with configured cost-type suffixes for penalty calculations:
   - Use suffixes: {", ".join(PipelineConfig.suffix_list())}
   - Example output columns: penalty_monetary, sla_credits_monetary, incident_count_credits
6. Calculate ALL penalties based on the document (uptime shortfalls, SLA misses, breach incidents)
7. Make sure all column aliases end with one of the configured suffixes
8. RESPOND ONLY WITH PURE JSON - NO MARKDOWN CODE BLOCKS, NO BACKTICKS, NO EXPLANATION TEXT
9. Start response with {{ and end with }}

{{
    "extracted_terms": "All extracted clauses, targets, formulas, and periods as a single paragraph",
    "sql_query": "SELECT ... with columns ending in configured suffixes for cost calculation"
}}"""


def resolve_prompt(custom_prompt: str = None, csv_schema: dict = None) -> str:
    """Resolve the final prompt with CSV schema context appended."""
    prompt = custom_prompt if (custom_prompt and custom_prompt.strip()) else DEFAULT_PROMPT

    if csv_schema and csv_schema.get('headers'):
        import json
        schema_info = f"""
CSV DATA STRUCTURE:
- Total rows: {csv_schema.get('row_count', 0)}
- Columns: {', '.join(csv_schema['headers'])}
- Column data types: {json.dumps(csv_schema.get('dtypes', {}), indent=2)}
- Sample data (first 3 rows):
{json.dumps(csv_schema.get('sample_data', []), indent=2)}

CRITICAL INSTRUCTIONS:
1. Use ONLY the column names listed above in your SQL query
2. The table name is '{PipelineConfig.TABLE_NAME}'
3. Map the SLA document metrics to the closest matching column from the available columns
4. If exact column match not found, use similar columns (e.g., 'uptime_minutes' instead of 'uptime_percent')
5. Generate SQL that will execute without errors against DuckDB
"""
        prompt += schema_info

    return prompt
