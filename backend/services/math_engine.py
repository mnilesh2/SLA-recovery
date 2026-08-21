"""
Math Engine Service
Validates and executes SQL queries against data with support for any data types
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False

logger = logging.getLogger(__name__)


class MathEngine:
    """SQL query validator and executor using DuckDB with universal data type support"""

    def __init__(self):
        self.has_duckdb = HAS_DUCKDB
        self.supported_formats = ['.csv', '.xls', '.xlsx', '.parquet', '.json']

    def get_table_name_from_file(self, file_path: str) -> str:
        """
        Extract table name from file path

        Args:
            file_path: Path to data file

        Returns:
            Table name (original filename without extension, lowercase, underscores instead of spaces)
        """
        filename = Path(file_path).name  # Get just the filename with extension
        # Remove timestamp prefix (user_id_timestamp_filename.csv pattern)
        # Format is typically: 1_1787301669.219506_sample_billing_data.csv
        parts = filename.split('_', 2)  # Split on first two underscores to remove user_id and timestamp
        if len(parts) >= 3:
            # Remove extension from the third part
            base_name = parts[2].rsplit('.', 1)[0]
        else:
            # Fallback: just remove extension
            base_name = Path(file_path).stem

        return base_name.lower().replace('-', '_').replace(' ', '_')

    def validate_sql(
        self,
        query: str,
        data_file: Optional[str] = None,
        table_schema: Optional[Dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL syntax and schema compatibility

        Args:
            query: SQL query to validate
            data_file: Path to data file (to infer table name)
            table_schema: Expected schema (column names and types)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.has_duckdb:
            return False, "DuckDB not available"

        try:
            conn = duckdb.connect(":memory:")

            # If data file provided, load it and validate with actual schema
            if data_file and Path(data_file).exists():
                table_name = self.get_table_name_from_file(data_file)
                df = self._load_data_file(data_file)

                if df is None:
                    return False, f"Unable to load data file: {data_file}"

                # Register the dataframe with the inferred table name
                conn.register(table_name, df)

                # Try to explain the query with actual table
                try:
                    result = conn.execute(f"EXPLAIN {query}").fetchall()
                    return True, None
                except Exception as e:
                    return False, str(e)
            else:
                # Just validate syntax without actual data
                result = conn.execute(f"EXPLAIN {query}").fetchall()
                return True, None

        except Exception as e:
            logger.warning(f"SQL validation failed: {type(e).__name__}: {e}")
            return False, str(e)
        finally:
            conn.close()

    def _load_data_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load data file with support for multiple formats

        Args:
            file_path: Path to data file

        Returns:
            Pandas DataFrame or None if load fails
        """
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == '.csv':
                df = pd.read_csv(file_path)
                logger.info(f"Loaded CSV: {file_path}, shape: {df.shape}")

            elif file_ext in ['.xls', '.xlsx']:
                df = pd.read_excel(file_path)
                logger.info(f"Loaded Excel: {file_path}, shape: {df.shape}")

            elif file_ext == '.parquet':
                df = pd.read_parquet(file_path)
                logger.info(f"Loaded Parquet: {file_path}, shape: {df.shape}")

            elif file_ext == '.json':
                df = pd.read_json(file_path)
                logger.info(f"Loaded JSON: {file_path}, shape: {df.shape}")

            else:
                logger.error(f"Unsupported file format: {file_ext}")
                return None

            # Detect and convert data types
            df = self._detect_and_convert_types(df)
            return df

        except Exception as e:
            logger.error(f"Error loading data file {file_path}: {type(e).__name__}: {e}")
            return None

    def _detect_and_convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Intelligently detect and convert column data types

        Args:
            df: Pandas DataFrame to convert

        Returns:
            DataFrame with detected types
        """
        for col in df.columns:
            try:
                # Skip if already has non-object type
                if df[col].dtype == 'object':
                    # Try to convert to boolean first
                    unique_vals = df[col].dropna().unique()
                    if len(unique_vals) <= 2 and all(str(v).lower() in ['true', 'false', '1', '0', 'yes', 'no', 't', 'f', 'y', 'n'] for v in unique_vals):
                        try:
                            # Map common boolean representations
                            bool_map = {
                                'true': True, 'false': False,
                                'True': True, 'False': False,
                                'TRUE': True, 'FALSE': False,
                                '1': True, '0': False,
                                'yes': True, 'no': False,
                                'y': True, 'n': False,
                                't': True, 'f': False
                            }
                            df[col] = df[col].map(lambda x: bool_map.get(str(x), x) if pd.notna(x) else x)
                            logger.debug(f"Column '{col}' converted to boolean")
                            continue
                        except:
                            pass

                    # Try to convert to numeric
                    try:
                        converted = pd.to_numeric(df[col], errors='coerce')
                        if converted.notna().sum() / len(df) > 0.8:  # 80% valid
                            df[col] = converted
                            logger.debug(f"Column '{col}' converted to numeric")
                            continue
                    except:
                        pass

                    # Try to convert to datetime
                    try:
                        converted = pd.to_datetime(df[col], errors='coerce')
                        if converted.notna().sum() / len(df) > 0.8:  # 80% valid
                            df[col] = converted
                            logger.debug(f"Column '{col}' converted to datetime")
                            continue
                    except:
                        pass

                    # Keep as string/object
                    logger.debug(f"Column '{col}' kept as object/string")

            except Exception as e:
                logger.warning(f"Error processing column '{col}': {e}")

        return df

    def execute_query(
        self,
        query: str,
        data_file: str,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """
        Execute SQL query against data file with universal data type support

        Args:
            query: SQL query to execute
            data_file: Path to CSV, Excel, Parquet, or JSON file
            limit: Maximum rows to return in results

        Returns:
            Dict with execution results, statistics, and sanity checks
        """
        if not self.has_duckdb:
            return {
                "status": "error",
                "message": "DuckDB not available",
                "results": []
            }

        try:
            # Verify file exists
            if not Path(data_file).exists():
                return {
                    "status": "error",
                    "message": f"Data file not found: {data_file}",
                    "results": [],
                    "file_path": data_file
                }

            # Load data file
            df = self._load_data_file(data_file)
            if df is None:
                return {
                    "status": "error",
                    "message": f"Unable to load data file: {data_file}",
                    "results": [],
                    "file_path": data_file
                }

            # Get dynamic table name from file
            table_name = self.get_table_name_from_file(data_file)
            logger.info(f"Using table name: {table_name}")

            # Create DuckDB connection and register data
            conn = duckdb.connect(":memory:")
            conn.register(table_name, df)

            # Execute query - DuckDB will use the registered table name
            result = conn.execute(query).df()

            # Apply limit to sample
            if len(result) > limit:
                sample_result = result.head(limit)
                truncated = True
            else:
                sample_result = result
                truncated = False

            # Perform sanity checks
            sanity_check = self._sanity_check(result)

            # Generate statistics
            stats = self._generate_statistics(df, result)

            return {
                "status": "success",
                "message": f"Query executed successfully against {table_name}",
                "rows_count": len(result),
                "columns": list(result.columns),
                "column_types": {col: str(result[col].dtype) for col in result.columns},
                "sample_data": sample_result.to_dict('records'),
                "sample_truncated": truncated,
                "sample_limit": limit,
                "execution_time_ms": 0,
                "table_name": table_name,
                "source_file": Path(data_file).name,
                "sanity_check": sanity_check,
                "summary_statistics": stats,
                "data_schema": {
                    "input_rows": len(df),
                    "input_columns": len(df.columns),
                    "output_rows": len(result),
                    "output_columns": len(result.columns),
                }
            }

        except Exception as e:
            logger.error(f"Query execution error: {type(e).__name__}: {e}")
            import traceback
            return {
                "status": "error",
                "message": f"Query execution failed: {str(e)}",
                "error_type": type(e).__name__,
                "error_details": traceback.format_exc(),
                "results": []
            }
        finally:
            try:
                conn.close()
            except:
                pass

    def _sanity_check(self, result: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform universal sanity checks on query results across all data types

        Args:
            result: Query result DataFrame

        Returns:
            Dict with validation results and warnings
        """
        checks = {
            "has_results": len(result) > 0,
            "total_nulls": 0,
            "warnings": [],
            "info": []
        }

        if len(result) == 0:
            checks["warnings"].append("Query returned no results")
            return checks

        # Check each column for data type specific issues
        for col in result.columns:
            col_dtype = result[col].dtype
            null_count = result[col].isnull().sum()

            # Null value check (universal)
            if null_count > 0:
                null_pct = (null_count / len(result)) * 100
                checks["total_nulls"] += null_count
                if null_pct > 50:
                    checks["warnings"].append(f"Column '{col}' has {null_pct:.1f}% null values")
                else:
                    checks["info"].append(f"Column '{col}' has {null_pct:.1f}% null values")

            # Numeric column checks
            if col_dtype in ['float64', 'int64', 'int32', 'float32']:
                numeric_vals = result[col].dropna()
                if len(numeric_vals) > 0:
                    # Check for negative values (may indicate data quality issues)
                    if (numeric_vals < 0).any():
                        checks["info"].append(f"Column '{col}' contains negative numeric values")

                    # Check for extremely large values
                    if numeric_vals.max() > 1e10:
                        checks["info"].append(f"Column '{col}' contains very large values (max: {numeric_vals.max():.2e})")

                    # Check for duplicates in ID-like columns
                    if 'id' in col.lower() and len(numeric_vals) > 0:
                        if numeric_vals.duplicated().any():
                            checks["info"].append(f"Column '{col}' (ID column) has duplicate values")

            # Date column checks
            elif col_dtype == 'datetime64[ns]':
                date_vals = result[col].dropna()
                if len(date_vals) > 0:
                    checks["info"].append(f"Column '{col}' contains dates from {date_vals.min()} to {date_vals.max()}")

            # String column checks
            elif col_dtype == 'object':
                unique_count = result[col].nunique()
                if unique_count == 1:
                    checks["info"].append(f"Column '{col}' has only 1 unique value (constant)")
                elif unique_count == len(result):
                    checks["info"].append(f"Column '{col}' has all unique values")

        return checks

    def _generate_statistics(self, input_df: pd.DataFrame, result_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive statistics for results across all data types

        Args:
            input_df: Original input DataFrame
            result_df: Query result DataFrame

        Returns:
            Dict with statistics for each data type
        """
        stats = {
            "numeric": {},
            "datetime": {},
            "string": {},
            "total_columns": len(result_df.columns)
        }

        for col in result_df.columns:
            col_dtype = result_df[col].dtype
            non_null_count = result_df[col].notna().sum()

            # Numeric statistics
            if col_dtype in ['float64', 'int64', 'int32', 'float32']:
                numeric_vals = result_df[col].dropna()
                if len(numeric_vals) > 0:
                    stats["numeric"][col] = {
                        "type": str(col_dtype),
                        "count": int(non_null_count),
                        "null_count": int(result_df[col].isnull().sum()),
                        "min": float(numeric_vals.min()),
                        "max": float(numeric_vals.max()),
                        "mean": float(numeric_vals.mean()),
                        "median": float(numeric_vals.median()),
                        "sum": float(numeric_vals.sum()),
                        "std": float(numeric_vals.std()),
                    }

            # Datetime statistics
            elif col_dtype == 'datetime64[ns]':
                date_vals = result_df[col].dropna()
                if len(date_vals) > 0:
                    stats["datetime"][col] = {
                        "type": str(col_dtype),
                        "count": int(non_null_count),
                        "null_count": int(result_df[col].isnull().sum()),
                        "min": str(date_vals.min()),
                        "max": str(date_vals.max()),
                        "range_days": int((date_vals.max() - date_vals.min()).days)
                    }

            # String statistics
            elif col_dtype == 'object':
                stats["string"][col] = {
                    "type": str(col_dtype),
                    "count": int(non_null_count),
                    "null_count": int(result_df[col].isnull().sum()),
                    "unique_values": int(result_df[col].nunique()),
                    "max_length": int(result_df[col].astype(str).str.len().max()) if non_null_count > 0 else 0,
                }

        return stats


def _serialize_for_json(obj: Any) -> Any:
    """Convert non-JSON-serializable types to JSON-safe types"""
    if obj is None:
        return None
    elif isinstance(obj, (bool, int, float, str)):
        return obj
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    else:
        return str(obj)


# Global math engine instance
_math_engine = None


def get_math_engine() -> MathEngine:
    """Get or create the global math engine instance"""
    global _math_engine
    if _math_engine is None:
        _math_engine = MathEngine()
    return _math_engine
