"""
Pydantic Schemas for Request/Response Validation
Type-safe data models for all API operations
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== Authentication ====================

class UserBase(BaseModel):
    username: str
    email: str
    role: str = "reviewer"


class UserCreate(UserBase):
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== Documents ====================

class DocumentUpload(BaseModel):
    document_type: str = "custom"
    custom_instructions: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    status: str
    upload_date: datetime
    file_size: int
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class DocumentParseRequest(BaseModel):
    document_id: int
    document_type: Optional[str] = "custom"
    custom_prompt: Optional[str] = None
    custom_instructions: Optional[str] = None


class DocumentParseResponse(BaseModel):
    status: str
    extracted_terms: Dict[str, Any]
    document_type: str
    model_used: str
    cached: bool
    usage: Dict[str, int]


# ==================== Queries ====================

class QueryValidationRequest(BaseModel):
    query_id: int
    data_file_path: Optional[str] = None


class QueryResponse(BaseModel):
    id: int
    document_id: int
    query_text: str
    extraction_confidence: float
    is_validated: bool
    validation_status: str
    extracted_terms: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Calculations ====================

class CalculationResponse(BaseModel):
    id: int
    query_id: int
    execution_status: str
    result_rows_count: int
    sanity_check_status: str
    result_data: List[Dict[str, Any]]
    execution_time_ms: float
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Cost Breakdown ====================

class CostBreakdownResponse(BaseModel):
    id: int
    cost_type: str
    original_cost: float
    calculated_cost: float
    delta_cost: float
    cost_unit: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    cost_details: Dict[str, Any]

    class Config:
        from_attributes = True


class CostSummaryResponse(BaseModel):
    total_original: float
    total_calculated: float
    total_delta: float
    costs_by_type: Dict[str, float]
    costs_by_period: Dict[str, float]
    currency: str = "USD"


# ==================== Approvals ====================

class ApprovalRequest(BaseModel):
    calculation_id: int
    approve: bool
    comments: Optional[str] = None
    requires_escalation: bool = False


class ApprovalResponse(BaseModel):
    id: int
    calculation_id: int
    request_status: str
    approved_by_username: Optional[str]
    approval_date: Optional[datetime]
    approver_comments: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Proofs ====================

class ProofResponse(BaseModel):
    id: int
    approval_id: int
    document_id: int
    proof_content: Dict[str, Any]
    is_finalized: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProofSearchRequest(BaseModel):
    document_id: Optional[int] = None
    approval_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 50
    offset: int = 0


# ==================== Cost Types ====================

class CostTypeQuery(BaseModel):
    cost_type: str
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class CostTypeResponse(BaseModel):
    cost_type: str
    count: int
    total_amount: float
    average_amount: float
    min_amount: float
    max_amount: float


# ==================== Dashboard ====================

class DashboardStats(BaseModel):
    total_documents: int
    total_calculations: int
    pending_approvals: int
    completed_proofs: int
    total_recovery: float
    last_7_days_recovery: float


# ==================== Audit Trail ====================

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    entity_type: str
    entity_id: int
    action_details: Dict[str, Any]
    result_status: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ==================== Generic Responses ====================

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    status: str = "success"
    message: str
    data: Optional[Any] = None
