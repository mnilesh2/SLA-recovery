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

        try:
            math_engine = MathEngine(csv_path=document.data_csv_path)
            print(f"🔍 Validating SQL for CSV: {document.data_csv_path}")
            print(f"📝 SQL Query:\n{query.sql_query}")
            validation_result = math_engine.validate_and_execute(query.sql_query)
            print(f"✅ Validation result: {validation_result['status']}")
            if validation_result['validation_errors']:
                print(f"⚠️ Validation errors: {validation_result['validation_errors']}")
        except Exception as sql_error:
            print(f"❌ SQL execution error: {type(sql_error).__name__}: {str(sql_error)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=f"SQL execution failed: {str(sql_error)}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Exception during validation: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal validation error: {str(e)}")

    from datetime import date, datetime
    from decimal import Decimal

    def json_serializer(obj):
        """Convert non-JSON-serializable objects to JSON-compatible types."""
        # Date/DateTime objects
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        # Decimal numbers
        elif isinstance(obj, Decimal):
            return float(obj)
        # NumPy types (if used)
        elif hasattr(obj, 'tolist'):
            return obj.tolist()
        # UUID objects
        elif hasattr(obj, 'hex'):
            return str(obj)
        # Bytes
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        # Any other type - convert to string
        else:
            return str(obj)

    # Normalize non-JSON-serializable types for storage
    # validation_errors: Text column, store as JSON string
    # raw_result_rows: JSON column, store as raw dict (SQLAlchemy handles serialization)
    normalized_result = None
    if validation_result["result"]:
        # Normalize the dict to handle non-serializable types (date/Decimal/etc.)
        normalized_result = json.loads(json.dumps(validation_result["result"], default=json_serializer))

    db_calculation = Calculation(
        query_id=query_id,
        validation_status=validation_result["status"],
        validation_errors=json.dumps(validation_result["validation_errors"], default=json_serializer) if validation_result["validation_errors"] else None,
        raw_result_rows=normalized_result  # Pass dict directly to JSON column, not json.dumps()
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
