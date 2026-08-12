from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel


# Auth schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "reviewer"


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentUpload(BaseModel):
    custom_prompt: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: datetime

    class Config:
        from_attributes = True


# Query schemas
class QueryResponse(BaseModel):
    id: int
    sql_query: str
    extracted_terms: str
    prompt_used: str
    used_custom_prompt: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Cost breakdown schemas
class CostBreakdownResponse(BaseModel):
    id: int
    cost_type: str
    original_value: float
    calculated_value: float
    currency: Optional[str]

    class Config:
        from_attributes = True


# Calculation schemas
class CalculationResponse(BaseModel):
    id: int
    validation_status: str
    validation_errors: Optional[str]
    raw_result_rows: Optional[Any]
    cost_breakdowns: List[CostBreakdownResponse]
    created_at: datetime

    class Config:
        from_attributes = True


# Approval schemas
class ApprovalRequest(BaseModel):
    status: str  # approved or rejected
    comment: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: int
    calculation_id: int
    approver_id: int
    status: str
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Proof schemas
class ProofResponse(BaseModel):
    id: int
    calculation_id: int
    proof_data: Any
    created_at: datetime

    class Config:
        from_attributes = True


# Audit log schemas
class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: int
    details: Optional[Any]
    created_at: datetime

    class Config:
        from_attributes = True
