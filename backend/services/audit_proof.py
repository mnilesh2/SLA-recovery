import json
from datetime import datetime
from typing import Dict, Any


class AuditProofGenerator:
    @staticmethod
    def generate_proof(
        calculation_data: Dict[str, Any],
        extracted_terms: str,
        sql_query: str,
        approver_name: str,
        cost_breakdowns: list
    ) -> Dict[str, Any]:

        extracted_terms_dict = {}
        try:
            extracted_terms_dict = json.loads(extracted_terms)
        except (json.JSONDecodeError, TypeError):
            extracted_terms_dict = {"raw": extracted_terms}

        proof = {
            "generated_at": datetime.utcnow().isoformat(),
            "approver": approver_name,
            "contract_clauses": extracted_terms_dict.get("penalty_clauses", []),
            "service_levels": extracted_terms_dict.get("service_levels", []),
            "calculation_formulas": extracted_terms_dict.get("calculation_formulas", []),
            "applicable_periods": extracted_terms_dict.get("applicable_periods", []),
            "executed_sql_formula": sql_query,
            "raw_evidence_rows": calculation_data.get("result", {}).get("rows", []) if calculation_data.get("result") else [],
            "evidence_columns": calculation_data.get("result", {}).get("columns", []) if calculation_data.get("result") else [],
            "cost_deltas": [
                {
                    "cost_type": bd["cost_type"],
                    "original": bd["original_value"],
                    "final": bd["calculated_value"],
                    "delta": bd["calculated_value"] - bd["original_value"],
                    "currency": bd.get("currency")
                }
                for bd in cost_breakdowns
            ],
            "summary": {
                "total_evidence_rows": len(calculation_data.get("result", {}).get("rows", [])) if calculation_data.get("result") else 0,
                "total_cost_types": len(cost_breakdowns),
                "proof_status": "approved"
            }
        }

        return proof
