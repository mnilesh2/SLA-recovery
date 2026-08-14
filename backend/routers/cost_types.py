from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, CostBreakdown
from backend.auth import get_current_user

router = APIRouter(prefix="/api/cost-types", tags=["cost-types"])


@router.get("/")
def get_cost_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    breakdowns = db.query(CostBreakdown).all()
    cost_types = set([bd.cost_type for bd in breakdowns])
    return {"cost_types": list(cost_types)}
