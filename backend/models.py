"""
Database Models - Complete schema for SLA Recovery Audit System
Supports multiple document types and flexible cost structures
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User accounts with roles"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="reviewer")  # admin, approver, reviewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documents = relationship("Document", back_populates="uploaded_by_user")
    approvals = relationship("Approval", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    """Uploaded documents with metadata"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    document_type = Column(String, default="custom")  # sla, insurance, contract, custom, etc.
    file_path = Column(String)
    text_content = Column(Text)  # Extracted text from PDF/file
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    mime_type = Column(String)
    status = Column(String, default="pending")  # pending, parsed, processing, complete, error
    error_message = Column(Text, nullable=True)
    doc_metadata = Column(JSON, default={})  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    queries = relationship("Query", back_populates="document")
    audit_logs = relationship("AuditLog", back_populates="document")


class CustomPrompt(Base):
    """Custom prompts for specific document types or use cases"""
    __tablename__ = "custom_prompts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    document_type = Column(String)  # sla, insurance, contract, custom
    prompt_text = Column(Text)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    prompt_metadata = Column(JSON, default={})  # Version control, tags, etc.


class Query(Base):
    """Generated SQL queries extracted from documents"""
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    query_text = Column(Text)
    query_type = Column(String)  # penalty_calculation, cost_analysis, validation, custom
    extraction_confidence = Column(Float)  # 0.0-1.0
    prompt_used = Column(String)  # name of prompt (default or custom)
    prompt_text = Column(Text)  # Full prompt text for audit trail
    model_used = Column(String)  # Which Claude model was used
    extracted_terms = Column(JSON)  # Raw extraction from LLM
    custom_instructions = Column(Text, nullable=True)
    is_validated = Column(Boolean, default=False)
    validation_status = Column(String)  # pending, valid, invalid
    validation_errors = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="queries")
    calculations = relationship("Calculation", back_populates="query")
    audit_logs = relationship("AuditLog", back_populates="query")


class Calculation(Base):
    """Query execution results and calculations - supports any data type"""
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"))
    execution_status = Column(String)  # success, error, pending
    result_rows_count = Column(Integer, default=0)
    result_columns = Column(JSON, default=[])  # List of column names in result
    result_column_types = Column(JSON, default={})  # Column name -> type mapping
    result_data = Column(JSON)  # Sample results (first N rows)
    all_results_file = Column(String, nullable=True)  # Path to full results
    execution_time_ms = Column(Float)
    error_message = Column(Text, nullable=True)
    sanity_check_status = Column(String)  # passed, failed, warning
    sanity_check_details = Column(JSON, default={})

    # SLA-specific fields
    sla_rules = Column(JSON, default=[])  # Extracted SLA rules from document
    violation_summary = Column(JSON, default={})  # Summary of violations found

    # Statistics and metadata
    summary_statistics = Column(JSON, default={})  # Type-specific statistics
    data_metadata = Column(JSON, default={})  # Generic metadata about results
    table_name = Column(String, nullable=True)  # Table used in query
    source_file = Column(String, nullable=True)  # Source CSV/data file

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    query = relationship("Query", back_populates="calculations")
    cost_breakdowns = relationship("CostBreakdown", back_populates="calculation")
    audit_logs = relationship("AuditLog", back_populates="calculation")


class CostBreakdown(Base):
    """Aggregated costs by type and period"""
    __tablename__ = "cost_breakdowns"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"))
    cost_type = Column(String)  # monetary, credits, units, custom_metric, etc.
    cost_currency = Column(String, default="USD")
    original_cost = Column(Float)  # From first pass
    calculated_cost = Column(Float)  # After recovery claim
    delta_cost = Column(Float)  # calculated - original
    cost_unit = Column(String)  # dollars, hours, units, percentage, etc.
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    cost_details = Column(JSON, default={})  # Breakdown details
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    calculation = relationship("Calculation", back_populates="cost_breakdowns")
    audit_logs = relationship("AuditLog", back_populates="cost_breakdown")


class Approval(Base):
    """Human-in-the-loop approval workflow"""
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"), unique=True)
    request_status = Column(String, default="pending")  # pending, approved, rejected, revoked
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approval_date = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    approver_comments = Column(Text, nullable=True)
    requires_escalation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    approver = relationship("User", back_populates="approvals")
    audit_logs = relationship("AuditLog", back_populates="approval")


class Proof(Base):
    """Complete audit proof documentation"""
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    approval_id = Column(Integer, ForeignKey("approvals.id"), unique=True)
    proof_content = Column(JSON)  # Complete proof as JSON
    document_id = Column(Integer, ForeignKey("documents.id"))
    # Proof includes: contract clauses, SQL, evidence rows, cost deltas, approver signature, timestamp
    proof_hash = Column(String, index=True)  # Hash for integrity verification
    is_finalized = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="proof")


class AuditLog(Base):
    """Immutable audit trail for compliance"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # upload, parse, validate, approve, reject, export, etc.
    entity_type = Column(String)  # Document, Query, Calculation, Approval, etc.
    entity_id = Column(Integer)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    query_id = Column(Integer, ForeignKey("queries.id"), nullable=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"), nullable=True)
    approval_id = Column(Integer, ForeignKey("approvals.id"), nullable=True)
    cost_breakdown_id = Column(Integer, ForeignKey("cost_breakdowns.id"), nullable=True)
    proof_id = Column(Integer, ForeignKey("proofs.id"), nullable=True)
    action_details = Column(JSON, default={})  # Detailed action information
    result_status = Column(String)  # success, error, warning
    result_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    document = relationship("Document", back_populates="audit_logs")
    query = relationship("Query", back_populates="audit_logs")
    calculation = relationship("Calculation", back_populates="audit_logs")
    approval = relationship("Approval", back_populates="audit_logs")
    cost_breakdown = relationship("CostBreakdown", back_populates="audit_logs")
    proof = relationship("Proof", back_populates="audit_logs")


# Indexes for performance
# Indexes are handled by adding them directly to the column definitions if needed
