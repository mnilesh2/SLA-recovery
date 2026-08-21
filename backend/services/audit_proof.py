"""
Audit Proof Generator Service
Creates complete compliance documentation for audit trails
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models import (
    Approval, Calculation, Query, CostBreakdown, User, Proof, Document
)

logger = logging.getLogger(__name__)


class ProofGenerator:
    """Generates complete audit proofs for compliance"""

    def generate_proof(
        self,
        db: Session,
        approval: Approval,
        approver: User
    ) -> Dict[str, Any]:
        """
        Generate complete audit proof documentation

        Args:
            db: Database session
            approval: Approval record
            approver: User who approved

        Returns:
            Complete proof object
        """
        try:
            # Get related entities
            calculation = db.query(Calculation).filter(
                Calculation.id == approval.calculation_id
            ).first()

            if not calculation:
                return {"status": "error", "message": "Calculation not found"}

            query = db.query(Query).filter(Query.id == calculation.query_id).first()
            document = db.query(Document).filter(Document.id == query.document_id).first()
            cost_breakdowns = db.query(CostBreakdown).filter(
                CostBreakdown.calculation_id == calculation.id
            ).all()

            # Build proof object
            proof_content = {
                "proof_id": str(hashlib.sha256(f"{approval.id}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:16]),
                "proof_date": datetime.utcnow().isoformat(),
                "approval_date": approval.approval_date.isoformat() if approval.approval_date else None,

                # Document information
                "document": {
                    "id": document.id,
                    "filename": document.filename,
                    "document_type": document.document_type,
                    "upload_date": document.upload_date.isoformat() if document.upload_date else None,
                },

                # Extracted contract terms
                "contract_terms": query.extracted_terms if query.extracted_terms else {},

                # SQL query used
                "sql_query": query.query_text,
                "query_confidence": query.extraction_confidence,

                # Calculation results
                "calculation_results": {
                    "execution_status": calculation.execution_status,
                    "rows_processed": calculation.result_rows_count,
                    "sample_evidence": calculation.result_data[:20] if calculation.result_data else [],
                    "sanity_check_status": calculation.sanity_check_status,
                    "sanity_check_details": calculation.sanity_check_details,
                },

                # Cost breakdown
                "cost_breakdown": [
                    {
                        "cost_type": cb.cost_type,
                        "original_cost": cb.original_cost,
                        "calculated_cost": cb.calculated_cost,
                        "delta_cost": cb.delta_cost,
                        "cost_unit": cb.cost_unit,
                        "cost_currency": cb.cost_currency,
                        "period": {
                            "start": cb.period_start.isoformat() if cb.period_start else None,
                            "end": cb.period_end.isoformat() if cb.period_end else None,
                        },
                        "details": cb.cost_details if cb.cost_details else {}
                    }
                    for cb in cost_breakdowns
                ],

                # Total costs
                "cost_summary": self._calculate_summary(cost_breakdowns),

                # Approval signature
                "approval": {
                    "approved_by": approver.username,
                    "approver_email": approver.email,
                    "approval_date": approval.approval_date.isoformat() if approval.approval_date else None,
                    "approver_comments": approval.approver_comments,
                    "requires_escalation": approval.requires_escalation,
                },

                # Audit metadata
                "metadata": {
                    "system_version": "1.0",
                    "generation_method": "automated",
                    "compliance_scope": ["financial", "operational", "audit"],
                }
            }

            # Calculate proof hash for integrity verification
            proof_hash = self._calculate_proof_hash(proof_content)
            proof_content["proof_hash"] = proof_hash

            logger.info(f"Proof generated successfully: {proof_content['proof_id']}")
            return {
                "status": "success",
                "proof_content": proof_content,
                "proof_hash": proof_hash
            }

        except Exception as e:
            logger.error(f"Error generating proof: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    def _calculate_summary(self, cost_breakdowns: list) -> Dict[str, Any]:
        """Calculate cost summary from breakdowns"""
        summary = {
            "total_original": 0,
            "total_calculated": 0,
            "total_delta": 0,
            "by_type": {},
            "by_currency": {}
        }

        for cb in cost_breakdowns:
            cost_type = cb.cost_type
            currency = cb.cost_currency or "USD"

            # By type
            if cost_type not in summary["by_type"]:
                summary["by_type"][cost_type] = {
                    "original": 0,
                    "calculated": 0,
                    "delta": 0
                }

            summary["by_type"][cost_type]["original"] += cb.original_cost
            summary["by_type"][cost_type]["calculated"] += cb.calculated_cost
            summary["by_type"][cost_type]["delta"] += cb.delta_cost

            # By currency
            if currency not in summary["by_currency"]:
                summary["by_currency"][currency] = 0
            summary["by_currency"][currency] += cb.calculated_cost

            # Totals
            summary["total_original"] += cb.original_cost
            summary["total_calculated"] += cb.calculated_cost
            summary["total_delta"] += cb.delta_cost

        return summary

    def _calculate_proof_hash(self, proof_content: Dict) -> str:
        """Calculate SHA256 hash of proof content for integrity verification"""
        # Remove existing hash for calculation
        content_copy = proof_content.copy()
        if "proof_hash" in content_copy:
            del content_copy["proof_hash"]

        # Serialize to JSON
        content_json = json.dumps(content_copy, sort_keys=True, default=str)

        # Calculate hash
        return hashlib.sha256(content_json.encode()).hexdigest()

    def verify_proof_integrity(self, proof_content: Dict) -> bool:
        """Verify proof integrity using stored hash"""
        stored_hash = proof_content.get("proof_hash")
        if not stored_hash:
            logger.warning("No proof hash found")
            return False

        calculated_hash = self._calculate_proof_hash(proof_content)
        return calculated_hash == stored_hash


# Global proof generator instance
_proof_generator = None


def get_proof_generator() -> ProofGenerator:
    """Get or create the global proof generator instance"""
    global _proof_generator
    if _proof_generator is None:
        _proof_generator = ProofGenerator()
    return _proof_generator
