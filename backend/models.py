from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="reviewer")  # reviewer, approver, admin
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="user")
    approvals = relationship("Approval", back_populates="approver")
    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    document_text = Column(Text)
    data_csv_path = Column(String)  # path to uploaded CSV with records to query
    custom_prompt_id = Column(Integer, ForeignKey("custom_prompts.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="documents")
    query = relationship("Query", uselist=False, back_populates="document")
    custom_prompt = relationship("CustomPrompt", back_populates="documents")


class CustomPrompt(Base):
    __tablename__ = "custom_prompts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    prompt_text = Column(Text)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="custom_prompt")


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    sql_query = Column(Text)
    extracted_terms = Column(Text)  # JSON: dict of extracted SLA terms
    prompt_used = Column(Text)  # the actual prompt text used (default or custom)
    used_custom_prompt = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="query")
    calculation = relationship("Calculation", uselist=False, back_populates="query")


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"))
    validation_status = Column(String, default="pending")  # pending, passed, failed
    validation_errors = Column(Text, nullable=True)
    raw_result_rows = Column(JSON)  # query execution result
    created_at = Column(DateTime, default=datetime.utcnow)

    query = relationship("Query", back_populates="calculation")
    cost_breakdowns = relationship("CostBreakdown", back_populates="calculation")
    approval = relationship("Approval", uselist=False, back_populates="calculation")
    proof = relationship("Proof", uselist=False, back_populates="calculation")


class CostBreakdown(Base):
    __tablename__ = "cost_breakdowns"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"))
    cost_type = Column(String)  # monetary, credits, units, custom_metric
    original_value = Column(Float)
    calculated_value = Column(Float)
    currency = Column(String, nullable=True)  # USD, EUR, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    calculation = relationship("Calculation", back_populates="cost_breakdowns")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"))
    approver_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String)  # approved, rejected, pending
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    calculation = relationship("Calculation", back_populates="approval")
    approver = relationship("User", back_populates="approvals")


class Proof(Base):
    __tablename__ = "proofs"

    id = Column(Integer, primary_key=True, index=True)
    calculation_id = Column(Integer, ForeignKey("calculations.id"))
    proof_data = Column(JSON)  # complete proof doc: clauses, SQL, evidence, deltas, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    calculation = relationship("Calculation", back_populates="proof")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)  # upload, parse, validate, approve, reject, etc.
    entity_type = Column(String)  # document, calculation, proof, etc.
    entity_id = Column(Integer)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
