"""
Cost Engine Service
Aggregates and analyzes costs from calculation results
"""

import logging
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CostEngine:
    """Analyzes and aggregates costs from query results"""

    def __init__(self):
        self.cost_types = ["monetary", "credits", "units", "hours", "percentage", "custom"]

    def extract_costs(
        self,
        results: List[Dict],
        extracted_terms: Dict[str, Any],
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Extract and categorize costs from query results

        Args:
            results: Query results
            extracted_terms: Extracted terms from document
            config: Cost extraction configuration

        Returns:
            Dict with categorized costs
        """
        if not results:
            logger.warning("No results to extract costs from")
            return self._empty_cost_breakdown()

        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(results)

            # Identify cost columns (columns ending in _monetary, _credits, _units, etc.)
            cost_breakdown = self._identify_cost_columns(df)

            # Aggregate costs
            aggregated = self._aggregate_costs(df, cost_breakdown)

            return {
                "status": "success",
                "costs_by_type": aggregated["by_type"],
                "costs_by_period": aggregated.get("by_period", {}),
                "total_costs": aggregated["totals"],
                "cost_columns_detected": cost_breakdown,
                "sample_data": results[:10] if len(results) > 0 else []
            }

        except Exception as e:
            logger.error(f"Error extracting costs: {e}")
            return {
                "status": "error",
                "message": str(e),
                "costs_by_type": {},
                "total_costs": {}
            }

    def _identify_cost_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Identify which columns contain costs"""
        cost_columns = {}

        for cost_type in self.cost_types:
            pattern = f"_{cost_type}"
            matching_cols = [col for col in df.columns if pattern in col.lower()]
            if matching_cols:
                cost_columns[cost_type] = matching_cols

        # Also check for common cost column names
        common_patterns = {
            "monetary": ["cost", "amount", "price", "fee", "charge", "penalty"],
            "credits": ["credit", "adjustment", "discount"],
            "hours": ["hours", "duration", "time"]
        }

        for cost_type, patterns in common_patterns.items():
            if cost_type not in cost_columns:
                matching_cols = [
                    col for col in df.columns
                    if any(p in col.lower() for p in patterns)
                ]
                if matching_cols:
                    cost_columns[cost_type] = matching_cols

        return cost_columns

    def _aggregate_costs(
        self,
        df: pd.DataFrame,
        cost_breakdown: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Aggregate costs by type and period"""
        aggregated = {
            "by_type": {},
            "by_period": {},
            "totals": {}
        }

        for cost_type, columns in cost_breakdown.items():
            total = 0
            for col in columns:
                if col in df.columns:
                    # Sum numeric values
                    try:
                        col_sum = pd.to_numeric(df[col], errors='coerce').sum()
                        total += col_sum if not pd.isna(col_sum) else 0
                    except:
                        pass

            aggregated["by_type"][cost_type] = {
                "total": float(total),
                "average": float(total / len(df)) if len(df) > 0 else 0,
                "columns": columns
            }
            aggregated["totals"][cost_type] = float(total)

        # Grand total
        aggregated["totals"]["all"] = sum(v for k, v in aggregated["totals"].items() if k != "all")

        return aggregated

    def _empty_cost_breakdown(self) -> Dict[str, Any]:
        """Return empty cost breakdown structure"""
        return {
            "status": "success",
            "costs_by_type": {},
            "costs_by_period": {},
            "total_costs": {
                "all": 0
            },
            "cost_columns_detected": {},
            "sample_data": []
        }

    def calculate_delta(
        self,
        original_costs: Dict[str, float],
        calculated_costs: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate delta between original and calculated costs"""
        delta = {}
        for cost_type in set(list(original_costs.keys()) + list(calculated_costs.keys())):
            orig = original_costs.get(cost_type, 0)
            calc = calculated_costs.get(cost_type, 0)
            delta[cost_type] = float(calc - orig)

        return delta

    def validate_costs(
        self,
        costs: Dict[str, float],
        sanity_checks: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Validate calculated costs"""
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }

        # Check for negative costs
        for cost_type, amount in costs.items():
            if cost_type != "all" and amount < 0:
                validation["warnings"].append(f"Negative cost detected for {cost_type}: {amount}")

        # Check for NaN or infinity
        for cost_type, amount in costs.items():
            if pd.isna(amount) or pd.isnull(amount):
                validation["errors"].append(f"NaN/Null cost for {cost_type}")
                validation["valid"] = False

        return validation


# Global cost engine instance
_cost_engine = None


def get_cost_engine() -> CostEngine:
    """Get or create the global cost engine instance"""
    global _cost_engine
    if _cost_engine is None:
        _cost_engine = CostEngine()
    return _cost_engine
