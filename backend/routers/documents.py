import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Document, Query, CustomPrompt, AuditLog
from ..schemas import DocumentResponse
from ..auth import get_current_user
from ..services.file_storage import save_uploaded_file, extract_text_from_file
from ..services.document_parser import parse_document_with_llm
from ..prompts import resolve_prompt

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    document: UploadFile = File(...),
    data_csv: UploadFile = File(...),
    custom_prompt: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    doc_content = document.file.read()
    csv_content = data_csv.file.read()

    doc_path = save_uploaded_file(doc_content, document.filename)
    csv_path = save_uploaded_file(csv_content, data_csv.filename)

    doc_text = extract_text_from_file(doc_path)

    db_document = Document(
        user_id=current_user.id,
        filename=document.filename,
        file_path=doc_path,
        document_text=doc_text,
        data_csv_path=csv_path
    )

    if custom_prompt and custom_prompt.strip():
        db_custom_prompt = CustomPrompt(
            user_id=current_user.id,
            prompt_text=custom_prompt,
            name=f"Custom prompt for {document.filename}"
        )
        db.add(db_custom_prompt)
        db.flush()
        db_document.custom_prompt_id = db_custom_prompt.id

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    audit_log = AuditLog(
        user_id=current_user.id,
        action="upload",
        entity_type="document",
        entity_id=db_document.id,
        details={"filename": document.filename}
    )
    db.add(audit_log)
    db.commit()

    return db_document


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.post("/{document_id}/parse")
def parse_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_query = db.query(Query).filter(Query.document_id == document_id).first()
    if existing_query:
        raise HTTPException(status_code=400, detail="Document already parsed")

    prompt = resolve_prompt(
        custom_prompt=document.custom_prompt.prompt_text if document.custom_prompt else None
    )

    parsed_result = parse_document_with_llm(document.document_text, prompt)

    extracted_terms = json.dumps(parsed_result.get("extracted_terms", {}))
    sql_query = parsed_result.get("sql_query", "")

    db_query = Query(
        document_id=document_id,
        sql_query=sql_query,
        extracted_terms=extracted_terms,
        prompt_used=prompt,
        used_custom_prompt=bool(document.custom_prompt)
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)

    audit_log = AuditLog(
        user_id=current_user.id,
        action="parse",
        entity_type="document",
        entity_id=document_id,
        details={"query_id": db_query.id}
    )
    db.add(audit_log)
    db.commit()

    return {
        "query_id": db_query.id,
        "sql_query": db_query.sql_query,
        "extracted_terms": extracted_terms,
        "prompt_used_custom": db_query.used_custom_prompt
    }
