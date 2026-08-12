import duckdb
import pandas as pd
from typing import List, Dict, Any, Tuple


class MathEngine:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.conn = None

    def _get_connection(self):
        if self.conn is None:
            self.conn = duckdb.connect(":memory:")
        return self.conn

    def load_csv(self):
        conn = self._get_connection()
        try:
            self.df = pd.read_csv(self.csv_path)
            conn.register("data", self.df)
            return True
        except Exception as e:
            raise ValueError(f"Failed to load CSV: {str(e)}")

    def validate_sql_syntax(self, sql_query: str) -> Tuple[bool, str]:
        conn = self._get_connection()
        try:
            result = conn.execute(f"EXPLAIN {sql_query}").fetchall()
            return True, "SQL syntax is valid"
        except Exception as e:
            return False, f"SQL syntax error: {str(e)}"

    def check_columns_exist(self, sql_query: str) -> Tuple[bool, str]:
        conn = self._get_connection()
        try:
            result = conn.execute(sql_query).description
            columns = [desc[0] for desc in result]
            return True, f"Query returns columns: {', '.join(columns)}"
        except Exception as e:
            return False, f"Column error: {str(e)}"

    def execute_query(self, sql_query: str) -> Tuple[bool, Any, str]:
        conn = self._get_connection()
        try:
            result = conn.execute(sql_query).fetchall()
            columns = [desc[0] for desc in conn.description]
            return True, {"columns": columns, "rows": result}, "Query executed successfully"
        except Exception as e:
            return False, None, f"Query execution error: {str(e)}"

    def run_sanity_checks(self, result_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []
        if not result_data or "rows" not in result_data:
            return True, []

        rows = result_data["rows"]
        columns = result_data.get("columns", [])

        for col_idx, col_name in enumerate(columns):
            if "_monetary" in col_name or "_credits" in col_name or "_units" in col_name or col_name.endswith("_value"):
                for row_idx, row in enumerate(rows):
                    try:
                        val = float(row[col_idx]) if row[col_idx] is not None else 0
                        if val < 0:
                            errors.append(f"Row {row_idx}, Column '{col_name}': negative value {val} (expected >= 0)")
                    except (ValueError, TypeError):
                        pass

        return len(errors) == 0, errors

    def validate_and_execute(self, sql_query: str) -> Dict[str, Any]:
        self.load_csv()

        syntax_valid, syntax_msg = self.validate_sql_syntax(sql_query)
        if not syntax_valid:
            return {
                "status": "failed",
                "validation_errors": [syntax_msg],
                "result": None
            }

        columns_ok, columns_msg = self.check_columns_exist(sql_query)
        if not columns_ok:
            return {
                "status": "failed",
                "validation_errors": [columns_msg],
                "result": None
            }

        exec_ok, result, exec_msg = self.execute_query(sql_query)
        if not exec_ok:
            return {
                "status": "failed",
                "validation_errors": [exec_msg],
                "result": None
            }

        sanity_ok, sanity_errors = self.run_sanity_checks(result)
        if not sanity_ok:
            return {
                "status": "failed",
                "validation_errors": sanity_errors,
                "result": result
            }

        return {
            "status": "passed",
            "validation_errors": [],
            "result": result
        }
