import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Query, Calculation, CostBreakdown, AuditLog
from ..schemas import CalculationResponse
from ..auth import get_current_user
from ..services.math_engine import MathEngine
from ..services.cost_engine import CostEngine

router = APIRouter(prefix="/api/calculations", tags=["calculations"])


@router.get("/{calculation_id}", response_model=CalculationResponse)
def get_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    calculation = db.query(Calculation).filter(Calculation.id == calculation_id).first()
    if not calculation:
        raise HTTPException(status_code=404, detail="Calculation not found")

    return {
        "id": calculation.id,
        "validation_status": calculation.validation_status,
        "validation_errors": calculation.validation_errors,
        "raw_result_rows": calculation.raw_result_rows,
        "cost_breakdowns": [
            {
                "id": bd.id,
                "cost_type": bd.cost_type,
                "original_value": bd.original_value,
                "calculated_value": bd.calculated_value,
                "currency": bd.currency
            }
            for bd in calculation.cost_breakdowns
        ],
        "created_at": calculation.created_at
    }


@router.post("/{query_id}/validate")
def validate_calculation(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(status_code=404, detail=f"Query {query_id} not found")

        document = query.document
        if document.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

        existing_calc = db.query(Calculation).filter(Calculation.query_id == query_id).first()
        if existing_calc:
            raise HTTPException(status_code=400, detail="Calculation already exists for this query")

        if not query.sql_query:
            raise HTTPException(status_code=400, detail="Query has no SQL generated")

        if not document.data_csv_path:
            raise HTTPException(status_code=400, detail="Document has no CSV data")

        math_engine = MathEngine(csv_path=document.data_csv_path)
        validation_result = math_engine.validate_and_execute(query.sql_query)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation error: {str(e)}")

    db_calculation = Calculation(
        query_id=query_id,
        validation_status=validation_result["status"],
        validation_errors=json.dumps(validation_result["validation_errors"]) if validation_result["validation_errors"] else None,
        raw_result_rows=json.dumps(validation_result["result"]) if validation_result["result"] else None
    )
    db.add(db_calculation)
    db.flush()

    if validation_result["status"] == "passed":
        cost_breakdowns = CostEngine.aggregate_costs(validation_result["result"])
        for breakdown in cost_breakdowns:
            db_breakdown = CostBreakdown(
                calculation_id=db_calculation.id,
                cost_type=breakdown["cost_type"],
                original_value=breakdown["original_value"],
                calculated_value=breakdown["calculated_value"],
                currency=breakdown.get("currency")
            )
            db.add(db_breakdown)

    db.commit()
    db.refresh(db_calculation)

    audit_log = AuditLog(
        user_id=current_user.id,
        action="validate",
        entity_type="calculation",
        entity_id=db_calculation.id,
        details={"status": validation_result["status"]}
    )
    db.add(audit_log)
    db.commit()

    return {
        "calculation_id": db_calculation.id,
        "status": validation_result["status"],
        "errors": validation_result["validation_errors"],
        "cost_breakdowns": [
            {
                "cost_type": bd.cost_type,
                "original_value": bd.original_value,
                "calculated_value": bd.calculated_value
            }
            for bd in db_calculation.cost_breakdowns
        ] if validation_result["status"] == "passed" else []
    }
