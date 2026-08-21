"""
Document Parser Service
Parses documents using LLM API and extracts structured information
"""

import json
import logging
from typing import Dict, Any, Optional

from .llm_service import get_llm_service
from .csv_utils import extract_csv_schema, format_csv_schema_for_prompt
from ..document_types import get_document_type, list_document_type_names

logger = logging.getLogger(__name__)


def _validate_sql_columns(sql_query: str, available_columns: list) -> Dict[str, Any]:
    """
    Validate that SQL query only uses available columns

    Args:
        sql_query: SQL query to validate
        available_columns: List of available column names from CSV

    Returns:
        Dict with validation result and invalid columns
    """
    import re

    # Extract column references from SQL
    # Look for identifiers after SELECT, WHERE, ORDER BY, GROUP BY, CASE, etc.
    sql_upper = sql_query.upper()
    available_upper = {col.upper(): col for col in available_columns}

    # Find all identifiers (word-like patterns)
    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', sql_query)

    # Filter out SQL keywords
    sql_keywords = {
        'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'GROUP', 'HAVING',
        'AS', 'AND', 'OR', 'NOT', 'IN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'SUM', 'AVG', 'COUNT', 'MAX', 'MIN', 'ROUND', 'CAST', 'INTERVAL',
        'DATE', 'DATE_TRUNC', 'CURRENT_DATE', 'BETWEEN', 'LIKE', 'IS', 'NULL',
        'TRUE', 'FALSE', 'DISTINCT', 'JOIN', 'ON', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
        'LIMIT', 'OFFSET', 'ASC', 'DESC', 'EXTRACT', 'YEAR', 'MONTH', 'DAY'
    }

    found_identifiers = set()
    for identifier in identifiers:
        if identifier.upper() not in sql_keywords:
            found_identifiers.add(identifier)

    # Check which identifiers are not in available columns
    invalid_columns = []
    for identifier in found_identifiers:
        if identifier.upper() not in available_upper:
            invalid_columns.append(identifier)

    return {
        "valid": len(invalid_columns) == 0,
        "invalid_columns": invalid_columns,
        "available_columns": available_columns
    }


def parse_document_with_llm(
    document_text: str,
    document_type: str = "custom",
    custom_prompt: Optional[str] = None,
    custom_instructions: Optional[str] = None,
    csv_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Parse a document using LLM API with CSV schema context

    Args:
        document_text: The document content to parse
        document_type: Type of document (sla, insurance, contract, custom)
        custom_prompt: Override the default prompt for this document type
        custom_instructions: Additional instructions to append to the prompt
        csv_path: Path to CSV file for schema extraction (optional)

    Returns:
        Dictionary with extracted information and metadata
    """
    try:
        llm_service = get_llm_service()

        # Extract CSV schema if CSV path provided
        csv_schema_info = ""
        csv_schema_context = {}
        table_name = None
        if csv_path:
            try:
                from .csv_utils import get_table_name_from_csv
                from .math_engine import get_math_engine

                csv_schema_context = extract_csv_schema(csv_path, sample_rows=1)
                if not csv_schema_context.get("error"):
                    # Get the table name that will be used
                    math_engine = get_math_engine()
                    table_name = math_engine.get_table_name_from_file(csv_path)

                    csv_schema_info = format_csv_schema_for_prompt(csv_schema_context, table_name=table_name)
                    logger.info(f"CSV schema extracted: {csv_schema_context.get('headers', [])}")
                    logger.info(f"Table name for SQL: {table_name}")
                else:
                    logger.warning(f"CSV schema extraction error: {csv_schema_context.get('error')}")
            except Exception as e:
                logger.warning(f"Failed to extract CSV schema: {type(e).__name__}: {str(e)}")

        # Use custom prompt if provided, otherwise use document type configuration
        if custom_prompt:
            system_prompt = "You are an expert document analyzer. Provide analysis in valid JSON format."
            full_prompt = f"{custom_prompt}\n{csv_schema_info}\n\n---\nDocument:\n{document_text}"
            response = llm_service.call_claude(full_prompt, system_prompt)
            extracted = llm_service.extract_json_from_response(response["content"])
        else:
            # Use document type configuration
            response = llm_service.analyze_document(
                document_text,
                document_type=document_type,
                custom_instructions=custom_instructions or "",
                csv_schema_info=csv_schema_info
            )
            extracted = response["extraction"]

        # Check if extraction resulted in an error
        extraction_error = response.get("extraction_error", False)
        error_type = response.get("extraction_error_type", None)

        if extraction_error:
            logger.warning(f"Document parsing returned error response. Type: {error_type}, Message: {extracted.get('error', 'Unknown error')}")
            return {
                "status": "error",
                "error": extracted.get("error", "LLM returned an error response"),
                "error_type": error_type,
                "extracted_terms": {},
                "document_type": document_type,
                "model_used": response.get("model_used", "unknown"),
                "cached": response.get("cached", False),
                "usage": response.get("usage", {}),
                "details": extracted,
            }

        logger.info(f"Document parsed successfully. Type: {document_type}, Model: {response.get('model_used', 'unknown')}")

        # Validate SQL if CSV schema is available
        sql_query = extracted.get("sql_query", "")
        available_columns = csv_schema_context.get("headers", [])
        if sql_query and available_columns:
            validation_result = _validate_sql_columns(sql_query, available_columns)
            if not validation_result["valid"]:
                logger.warning(f"SQL uses invalid columns: {validation_result['invalid_columns']}")
                extracted["sql_validation_warning"] = {
                    "message": "SQL uses columns that may not exist in the data",
                    "invalid_columns": validation_result['invalid_columns'],
                    "available_columns": available_columns,
                    "suggestion": f"Available columns are: {', '.join(available_columns)}"
                }

        return {
            "status": "success",
            "extracted_terms": extracted,
            "document_type": document_type,
            "model_used": response.get("model_used", "unknown"),
            "cached": response.get("cached", False),
            "usage": response.get("usage", {}),
            "thinking": response.get("thinking", ""),
        }

    except Exception as e:
        logger.error(f"Error parsing document: {type(e).__name__}: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__,
            "extracted_terms": {},
            "document_type": document_type,
        }


def get_supported_document_types() -> list:
    """Get list of supported document types"""
    return list_document_type_names()


def get_document_type_info(doc_type: str) -> Dict[str, Any]:
    """Get information about a specific document type"""
    doc_config = get_document_type(doc_type)
    return {
        "name": doc_config.name,
        "description": doc_config.description,
        "expected_outputs": doc_config.expected_outputs,
        "examples": doc_config.examples or []
    }
