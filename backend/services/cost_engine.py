from typing import List, Dict, Any, Tuple


class CostEngine:
    COST_SUFFIXES = ["_monetary", "_credits", "_units"]
    COST_TYPE_MAP = {
        "_monetary": "monetary",
        "_credits": "credits",
        "_units": "units"
    }

    @staticmethod
    def extract_cost_types(result_data: Dict[str, Any]) -> Tuple[List[str], List[Dict[str, Any]]]:
        if not result_data or "columns" not in result_data or "rows" not in result_data:
            return [], []

        columns = result_data["columns"]
        rows = result_data["rows"]

        cost_columns = {}
        for col in columns:
            for suffix in CostEngine.COST_SUFFIXES:
                if col.endswith(suffix):
                    cost_type = CostEngine.COST_TYPE_MAP[suffix]
                    if cost_type not in cost_columns:
                        cost_columns[cost_type] = []
                    cost_columns[cost_type].append(col)

        if not cost_columns:
            return [], []

        cost_breakdowns = []
        for cost_type, cols in cost_columns.items():
            original_sum = 0
            calculated_sum = 0

            for row_idx, row in enumerate(rows):
                for col_idx, col in enumerate(columns):
                    if col in cols:
                        try:
                            val = float(row[col_idx]) if row[col_idx] is not None else 0
                            calculated_sum += val
                        except (ValueError, TypeError):
                            pass

            cost_breakdowns.append({
                "cost_type": cost_type,
                "original_value": original_sum,
                "calculated_value": calculated_sum,
                "currency": "USD" if cost_type == "monetary" else None
            })

        return list(cost_columns.keys()), cost_breakdowns

    @staticmethod
    def aggregate_costs(result_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        _, breakdowns = CostEngine.extract_cost_types(result_data)
        return breakdowns

    @staticmethod
    def get_all_cost_types(calculations: List[Dict[str, Any]]) -> List[str]:
        cost_types = set()
        for calc in calculations:
            if "cost_breakdowns" in calc:
                for breakdown in calc["cost_breakdowns"]:
                    cost_types.add(breakdown["cost_type"])
        return list(cost_types)
