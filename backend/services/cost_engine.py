"""Cost extraction engine — detects and aggregates cost-type columns from SQL results."""

from typing import List, Dict, Any, Tuple
from ..pipeline_config import PipelineConfig


class CostEngine:
    """Single-sourced cost-type detection and aggregation."""

    @staticmethod
    def extract_cost_types(result_data: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Extract cost-type columns based on configured suffixes."""
        if not result_data or "columns" not in result_data or "rows" not in result_data:
            return [], []

        columns = result_data["columns"]
        rows = result_data["rows"]
        suffixes = PipelineConfig.suffix_list()

        # Group columns by detected suffix
        cost_columns = {}
        for col in columns:
            for suffix in suffixes:
                if col.endswith(suffix):
                    suffix_info = PipelineConfig.get_cost_type_info(suffix)
                    cost_type = suffix_info["type"]
                    if cost_type not in cost_columns:
                        cost_columns[cost_type] = []
                    cost_columns[cost_type].append(col)
                    break  # Each column matches at most one suffix

        if not cost_columns:
            return [], []

        # Aggregate values for each cost type
        cost_breakdowns = []
        for cost_type, cols in cost_columns.items():
            calculated_sum = 0

            for row_idx, row in enumerate(rows):
                for col_idx, col in enumerate(columns):
                    if col in cols:
                        try:
                            val = float(row[col_idx]) if row[col_idx] is not None else 0
                            calculated_sum += val
                        except (ValueError, TypeError):
                            pass

            # Look up currency for this cost type
            suffix = PipelineConfig.get_suffix_for_cost_type(cost_type)
            suffix_info = PipelineConfig.get_cost_type_info(suffix) if suffix else {}
            currency = suffix_info.get("currency")

            cost_breakdowns.append({
                "cost_type": cost_type,
                "original_value": 0,  # No baseline concept in current pipeline — set to 0
                "calculated_value": calculated_sum,
                "currency": currency
            })

        return list(cost_columns.keys()), cost_breakdowns

    @staticmethod
    def aggregate_costs(result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Aggregate cost types from SQL result data."""
        _, breakdowns = CostEngine.extract_cost_types(result_data)
        return breakdowns

    @staticmethod
    def get_all_cost_types(calculations: List[Dict[str, Any]]) -> List[str]:
        """Extract all unique cost types from a list of calculation dicts."""
        cost_types = set()
        for calc in calculations:
            if "cost_breakdowns" in calc:
                for breakdown in calc["cost_breakdowns"]:
                    cost_types.add(breakdown["cost_type"])
        return list(cost_types)
