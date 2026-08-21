"""
Prompt Management
Centralized prompt templates for different document types and use cases
"""

from typing import Dict, Optional
from .document_types import get_document_type


# Default system prompts
SYSTEM_PROMPTS = {
    "sla_recovery_agent": """You are an SLA Recovery Agent. Your role is to:
1. Extract SLA rules, penalties, and thresholds from documents
2. Identify violation conditions and penalty calculations
3. Generate SQL queries using ONLY the available columns from the CSV schema
4. Return ONLY valid JSON in the specified format
5. DO NOT make up or assume column names - use ONLY the columns listed in the CSV schema
6. DO NOT include comments, explanations, or markdown in responses
7. DO NOT include SQL comments (-- or /* */)

CRITICAL: Column Usage Rules
- ONLY use columns that are explicitly listed in the CSV schema
- If you need a value that's not available in the columns, DO NOT make up a column name
- DO NOT assume column names like 'monthly_service_fee', 'amount', 'fee' etc. unless explicitly listed
- If the data you need is not available, create CASE statements to calculate it from available columns
- Example: If you need penalty, use: CASE WHEN column < threshold THEN value ELSE 0 END

IMPORTANT SQL SYNTAX RULES:
- For BOOLEAN columns: Use `WHERE column = TRUE` (NOT 'True')
- For NUMERIC columns: Use `WHERE column = 100` (NOT '100')
- For DATE columns: Use `WHERE column >= '2024-01-01'` (ISO format)
- For STRING columns: Use `WHERE column = 'value'` (WITH quotes)
- For NULL checks: Use `WHERE column IS NULL`

Respond ONLY with valid JSON - no other text.""",

    "document_analyzer": """You are an expert document analyst specializing in legal, financial, and operational documents.
Your task is to extract structured information from documents while maintaining accuracy and completeness.
Always respond in valid JSON format unless explicitly instructed otherwise.
Focus on identifying terms that have financial, operational, or compliance implications.""",

    "sql_query_generator": """You are an expert SQL query writer with deep knowledge of data analysis.
Generate SQL queries that accurately extract and calculate metrics from billing and operational data.
Ensure queries are syntactically correct and safe to execute.
Do NOT include comments in SQL queries.
Only return the SQL query with no explanations or markdown.""",

    "cost_calculator": """You are an expert financial analyst specializing in cost recovery and penalty calculations.
Analyze extracted terms and calculate accurate financial impacts.
Provide clear breakdowns of costs by type and time period.""",
}


def get_system_prompt(prompt_type: str = "document_analyzer") -> str:
    """Get a system prompt by type"""
    return SYSTEM_PROMPTS.get(prompt_type, SYSTEM_PROMPTS["document_analyzer"])


def resolve_prompt(
    document_type: str = "custom",
    custom_prompt: Optional[str] = None,
    use_default: bool = True
) -> str:
    """
    Resolve which prompt to use

    Args:
        document_type: Type of document (sla, insurance, etc.)
        custom_prompt: User-provided custom prompt
        use_default: Whether to use default if custom not provided

    Returns:
        The prompt to use
    """
    # Highest priority: custom user prompt
    if custom_prompt and custom_prompt.strip():
        return custom_prompt

    # Second priority: document type specific prompt
    doc_config = get_document_type(document_type)
    if doc_config:
        return doc_config.extraction_prompt

    # Fallback: generic custom prompt
    if use_default:
        doc_config = get_document_type("custom")
        return doc_config.extraction_prompt

    return ""


def build_document_analysis_prompt(
    document_text: str,
    document_type: str = "custom",
    custom_instructions: str = "",
    custom_prompt: Optional[str] = None
) -> str:
    """
    Build complete prompt for document analysis

    Args:
        document_text: The document to analyze
        document_type: Type of document
        custom_instructions: Additional instructions
        custom_prompt: Override prompt

    Returns:
        Complete formatted prompt
    """
    base_prompt = resolve_prompt(document_type, custom_prompt)

    prompt = f"""{base_prompt}

{f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

---
Document to Analyze:
{document_text}

Please provide your analysis in JSON format with the structure defined above."""

    return prompt


def build_sql_generation_prompt(
    extracted_terms: Dict,
    table_schema: Dict,
    custom_instructions: str = ""
) -> str:
    """
    Build prompt for generating SQL queries from extracted terms

    Args:
        extracted_terms: Terms extracted from document
        table_schema: Schema of available data
        custom_instructions: Additional instructions

    Returns:
        Formatted SQL generation prompt
    """
    prompt = f"""Based on the following extracted contract terms, generate a SQL query to identify violations and calculate costs.

EXTRACTED TERMS:
{str(extracted_terms)}

AVAILABLE DATA SCHEMA:
{str(table_schema)}

{f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

Requirements:
1. Query must be syntactically correct
2. Include all relevant columns for cost calculation
3. Group by time periods if applicable
4. Include WHERE conditions for violation detection
5. Return original and calculated cost columns

Provide the SQL query only, without explanation."""

    return prompt


def build_cost_calculation_prompt(
    extracted_terms: Dict,
    sql_results: list,
    custom_instructions: str = ""
) -> str:
    """
    Build prompt for cost calculation from query results

    Args:
        extracted_terms: Terms extracted from document
        sql_results: Results from executed query
        custom_instructions: Additional instructions

    Returns:
        Formatted cost calculation prompt
    """
    prompt = f"""Analyze the following query results against the extracted contract terms and calculate total costs.

EXTRACTED TERMS:
{str(extracted_terms)}

QUERY RESULTS (Sample):
{str(sql_results[:10]) if len(sql_results) > 0 else "No results"}
Total Rows: {len(sql_results)}

{f"Additional Instructions: {custom_instructions}" if custom_instructions else ""}

Provide:
1. Total costs by type (monetary, credits, units, etc.)
2. Costs by time period
3. Confidence in calculation
4. Any assumptions made

Return as JSON."""

    return prompt
