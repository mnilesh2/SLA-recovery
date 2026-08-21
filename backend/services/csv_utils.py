"""
CSV Utility Functions
Extract headers, sample data, and schema information from CSV files
"""

import csv
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_csv_schema(csv_path: str, sample_rows: int = 1) -> Dict[str, Any]:
    """
    Extract CSV headers, sample data, and inferred types from any CSV file

    Args:
        csv_path: Path to CSV file
        sample_rows: Number of sample rows to extract (default: 1)

    Returns:
        Dict with headers, sample data, column types, and file metadata
    """
    try:
        import pandas as pd

        # Try reading with pandas for better type inference
        df = pd.read_csv(csv_path, nrows=max(sample_rows + 10, 100))  # Read extra for type inference

        headers = list(df.columns)
        sample_data = df.head(sample_rows).to_dict('records')
        column_types = {}

        # Infer types from the dataframe
        for col in headers:
            col_dtype = str(df[col].dtype)

            if 'bool' in col_dtype:
                column_types[col] = "boolean"
            elif 'int' in col_dtype:
                column_types[col] = "integer"
            elif 'float' in col_dtype:
                column_types[col] = "float"
            elif 'datetime' in col_dtype or 'date' in col_dtype:
                column_types[col] = "date"
            elif 'object' in col_dtype:
                # Try to infer if it's actually a date, boolean, or number
                sample_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else ""
                inferred = _infer_type(str(sample_val))
                column_types[col] = inferred
            else:
                column_types[col] = col_dtype

        if not headers:
            logger.warning(f"No headers found in CSV: {csv_path}")
            return {
                "headers": [],
                "sample_data": [],
                "column_types": {},
                "row_count": 0,
                "total_rows": 0,
                "error": "No headers found in CSV"
            }

        logger.info(f"Extracted {len(headers)} headers from CSV: {headers}")
        logger.info(f"Column types: {column_types}")
        logger.info(f"Sample data rows: {len(sample_data)}, Total rows in file: {len(df)}")

        return {
            "headers": headers,
            "sample_data": sample_data,
            "column_types": column_types,
            "row_count": len(sample_data),
            "total_rows": len(df),
            "file_size": Path(csv_path).stat().st_size,
            "file_name": Path(csv_path).name,
            "error": None
        }

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_path}")
        return {
            "headers": [],
            "sample_data": [],
            "column_types": {},
            "row_count": 0,
            "total_rows": 0,
            "error": f"CSV file not found: {csv_path}"
        }
    except Exception as e:
        logger.error(f"Error extracting CSV schema: {type(e).__name__}: {str(e)}")
        return {
            "headers": [],
            "sample_data": [],
            "column_types": {},
            "row_count": 0,
            "total_rows": 0,
            "error": f"Error reading CSV: {str(e)}"
        }


def _infer_type(value: str) -> str:
    """Infer data type from value string"""
    if not value or value.lower() in ['null', 'none', 'na', 'n/a', '']:
        return "string"

    # Check for boolean
    if value.lower() in ['true', 'false', '1', '0']:
        return "boolean"

    # Try to infer numeric type
    try:
        float(value)
        if '.' in value:
            return "float"
        else:
            return "integer"
    except ValueError:
        pass

    # Check for date patterns
    if any(sep in value for sep in ['-', '/']):
        if len(value) in [10, 19]:  # YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
            return "date"

    return "string"


def format_csv_schema_for_prompt(csv_schema: Dict[str, Any], table_name: str = None) -> str:
    """
    Format CSV schema information for LLM prompt

    Args:
        csv_schema: CSV schema dict from extract_csv_schema()
        table_name: The actual table name that will be used in SQL

    Returns:
        Formatted string for inclusion in LLM prompt
    """
    if csv_schema.get("error"):
        return f"\n⚠️ CSV Schema Error: {csv_schema['error']}\n"

    headers = csv_schema.get("headers", [])
    sample_data = csv_schema.get("sample_data", [])
    column_types = csv_schema.get("column_types", {})
    file_name = csv_schema.get("file_name", "data")

    # Use provided table name or derive from filename
    if not table_name:
        table_name = get_table_name_from_csv(f"/tmp/{file_name}")

    prompt_text = "\n## CSV DATA SCHEMA\n"
    prompt_text += f"Table Name: `{table_name}`\n"
    prompt_text += f"Total Columns: {len(headers)}\n"
    prompt_text += "⚠️ YOU MUST ONLY USE THESE EXACT COLUMN NAMES - DO NOT MAKE UP COLUMN NAMES:\n\n"

    # Column definitions with types and sample values
    prompt_text += "### Available Columns (COMPLETE LIST):\n"
    for i, header in enumerate(headers, 1):
        col_type = column_types.get(header, "string")
        sample_val = sample_data[0].get(header, "NULL") if sample_data else "NULL"
        prompt_text += f"{i}. `{header}` ({col_type}) = {sample_val}\n"

    prompt_text += "\n### ⚠️ CRITICAL RULES:\n"
    prompt_text += f"1. SELECT ONLY FROM THESE {len(headers)} COLUMNS - NO OTHER COLUMNS EXIST\n"
    prompt_text += "2. If you need data that's not in these columns, DO NOT make up column names\n"
    prompt_text += "3. Use ONLY columns listed above (case-sensitive)\n"
    prompt_text += f"4. Table to use: FROM `{table_name}` (exactly this name)\n"
    prompt_text += f"5. Example SQL: SELECT {', '.join(headers[:3])} FROM {table_name} WHERE ...\n"
    prompt_text += "6. Do NOT add comments to SQL\n"
    prompt_text += "7. For BOOLEAN: Use `WHERE column = TRUE` (not 'True' as string)\n"
    prompt_text += "8. For NUMERIC: Use `WHERE column = 100` (not '100' as string)\n"
    prompt_text += "9. For DATE: Use `WHERE column >= '2024-01-01'` (ISO format)\n"
    prompt_text += "10. For STRING: Use `WHERE column = 'value'` (with quotes)\n\n"

    return prompt_text


def get_table_name_from_csv(csv_path: str) -> str:
    """
    Get a suitable table name from CSV filename

    Args:
        csv_path: Path to CSV file

    Returns:
        Table name (filename without extension, lowercase)
    """
    filename = Path(csv_path).stem
    return filename.lower().replace('-', '_').replace(' ', '_')


def validate_column_names(sql_query: str, available_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that SQL query uses only available columns

    Args:
        sql_query: SQL query string
        available_columns: List of available column names

    Returns:
        Tuple of (is_valid, missing_columns)
    """
    import re

    # Extract column references from SQL (simplified - may have false positives)
    # This looks for identifiers after SELECT, WHERE, ORDER BY, etc.
    column_pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:,|FROM|WHERE|ORDER|GROUP|HAVING|$|=|<|>|\))'

    found_columns = set(re.findall(column_pattern, sql_query.upper()))

    # Filter out SQL keywords
    sql_keywords = {
        'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'GROUP', 'HAVING',
        'AS', 'AND', 'OR', 'NOT', 'IN', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
        'SUM', 'AVG', 'COUNT', 'MAX', 'MIN', 'ROUND', 'CAST', 'INTERVAL',
        'DATE', 'DATE_TRUNC', 'CURRENT_DATE', 'BETWEEN', 'LIKE'
    }

    found_columns = found_columns - sql_keywords

    # Normalize available columns to uppercase for comparison
    available_upper = {col.upper() for col in available_columns}

    missing = found_columns - available_upper

    return len(missing) == 0, list(missing)
