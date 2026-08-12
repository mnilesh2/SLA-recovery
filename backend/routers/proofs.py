from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Proof
from ..schemas import ProofResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/proofs", tags=["proofs"])


@router.get("/{proof_id}", response_model=ProofResponse)
def get_proof(
    proof_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proof = db.query(Proof).filter(Proof.id == proof_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found")
    return proof


@router.get("/by-calculation/{calculation_id}", response_model=ProofResponse)
def get_proof_by_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proof = db.query(Proof).filter(Proof.calculation_id == calculation_id).first()
    if not proof:
        raise HTTPException(status_code=404, detail="Proof not found for this calculation")
    return proof


@router.get("/search")
def search_proofs(
    cost_type: Optional[str] = None,
    approver_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proofs = db.query(Proof).all()

    results = []
    for proof in proofs:
        proof_data = proof.proof_data
        matches = True

        if cost_type:
            cost_types_in_proof = [cd["cost_type"] for cd in proof_data.get("cost_deltas", [])]
            if cost_type not in cost_types_in_proof:
                matches = False

        if approver_name:
            if proof_data.get("approver") != approver_name:
                matches = False

        if matches:
            results.append({
                "id": proof.id,
                "created_at": proof.created_at,
                "approver": proof_data.get("approver"),
                "cost_types": [cd["cost_type"] for cd in proof_data.get("cost_deltas", [])]
            })

    return results
