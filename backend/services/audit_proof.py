"""Audit proof generation — immutable proof record of calculation and approval."""

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

        # Extracted terms is a string (paragraph), not a structured dict
        # Just store it as-is in the proof
        extracted_terms_str = extracted_terms
        if isinstance(extracted_terms, str):
            # It's already a string, use it directly
            extracted_terms_str = extracted_terms
        else:
            # For backward compat, if somehow it's already a dict, stringify it
            extracted_terms_str = json.dumps(extracted_terms) if not isinstance(extracted_terms, str) else extracted_terms

        proof = {
            "generated_at": datetime.utcnow().isoformat(),
            "approver": approver_name,
            "extracted_terms": extracted_terms_str,  # Plain string summary
            "executed_sql_formula": sql_query,
            "raw_evidence_rows": calculation_data.get("result", {}).get("rows", []) if calculation_data.get("result") else [],
            "evidence_columns": calculation_data.get("result", {}).get("columns", []) if calculation_data.get("result") else [],
            "cost_breakdowns": [
                {
                    "cost_type": bd["cost_type"],
                    "calculated_value": bd["calculated_value"],
                    "currency": bd.get("currency"),
                    "note": "Original value is not tracked in current pipeline design"
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
