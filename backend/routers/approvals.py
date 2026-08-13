import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Calculation, Approval, Proof, AuditLog
from ..schemas import ApprovalRequest, ApprovalResponse
from ..auth import get_current_user, require_role
from ..services.audit_proof import AuditProofGenerator

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.post("/{calculation_id}/approve", response_model=ApprovalResponse)
def approve_calculation(
    calculation_id: int,
    approval_data: ApprovalRequest,
    current_user: User = Depends(require_role("approver", "admin")),
    db: Session = Depends(get_db)
):
    calculation = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")

    if calculation.validation_status != "passed":
        raise HTTPException(status_code=400, detail="Can only approve passed calculations")

    existing_approval = db.query(Approval).filter(Approval.calculation_id == calculation_id).first()
    if existing_approval:
        raise HTTPException(status_code=400, detail="Calculation already has an approval decision")

    db_approval = Approval(
        calculation_id=calculation_id,
        approver_id=current_user.id,
        status=approval_data.status,
        comment=approval_data.comment
    )
    db.add(db_approval)
    db.flush()

    if approval_data.status == "approved":
        query = calculation.query
        document = query.document

        # JSON column is already deserialized by SQLAlchemy
        result_data = calculation.raw_result_rows if calculation.raw_result_rows else {}

        proof_data = AuditProofGenerator.generate_proof(
            calculation_data={"result": result_data},
            extracted_terms=query.extracted_terms,
            sql_query=query.sql_query,
            approver_name=current_user.username,
            cost_breakdowns=[
                {
                    "cost_type": bd.cost_type,
                    "original_value": bd.original_value,
                    "calculated_value": bd.calculated_value,
                    "currency": bd.currency
                }
                for bd in calculation.cost_breakdowns
            ]
        )

        db_proof = Proof(
            calculation_id=calculation_id,
            proof_data=proof_data
        )
        db.add(db_proof)

    db.commit()
    db.refresh(db_approval)

    audit_log = AuditLog(
        user_id=current_user.id,
        action=approval_data.status,
        entity_type="calculation",
        entity_id=calculation_id,
        details={"comment": approval_data.comment}
    )
    db.add(audit_log)
    db.commit()

    return db_approval


@router.get("/pending")
def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pending_calculations = db.query(Calculation).filter(
        Calculation.validation_status == "passed",
        ~Calculation.approval.any()
    ).all()

    return [
        {
            "calculation_id": calc.id,
            "document_name": calc.query.document.filename,
            "created_at": calc.created_at,
            "cost_breakdowns": [
                {
                    "cost_type": bd.cost_type,
                    "calculated_value": bd.calculated_value
                }
                for bd in calc.cost_breakdowns
            ]
        }
        for calc in pending_calculations
    ]
