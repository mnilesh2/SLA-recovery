"""
Documents Router
Document upload, parsing, and management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
from datetime import datetime

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Document
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])


@router.post("/upload")
def upload_document(
    document: UploadFile = File(...),
    data_csv: UploadFile = File(...),
    custom_prompt: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload SLA document and billing data CSV

    Args:
        document: SLA document (PDF/TXT)
        data_csv: Billing data CSV file
        custom_prompt: Optional custom prompt for LLM
        current_user: Current authenticated user
        db: Database session

    Returns:
        Document object with ID and metadata
    """
    try:
        logger.info(f"=== Upload Document Started ===")
        logger.info(f"User: {current_user.username} (ID: {current_user.id})")
        logger.info(f"Document file: {document.filename}")
        logger.info(f"CSV file: {data_csv.filename}")
        logger.info(f"Custom prompt: {custom_prompt[:50] if custom_prompt else 'None'}...")

        # Create uploads directory if it doesn't exist
        logger.info(f"Creating/checking upload directory: {settings.upload_dir}")
        os.makedirs(settings.upload_dir, exist_ok=True)

        # Save the document file
        doc_filename = f"{current_user.id}_{datetime.utcnow().timestamp()}_{document.filename}"
        doc_path = os.path.join(settings.upload_dir, doc_filename)
        logger.info(f"Document path: {doc_path}")

        with open(doc_path, "wb") as f:
            content = document.file.read()
            f.write(content)

        # Read document content
        if doc_filename.endswith('.pdf'):
            text_content = f"[PDF Content - {doc_filename}]"  # Basic placeholder
        else:
            text_content = content.decode('utf-8')

        # Save CSV file
        csv_filename = f"{current_user.id}_{datetime.utcnow().timestamp()}_{data_csv.filename}"
        csv_path = os.path.join(settings.upload_dir, csv_filename)

        with open(csv_path, "wb") as f:
            f.write(data_csv.file.read())

        # Create database record
        doc = Document(
            filename=document.filename,
            file_path=doc_path,
            text_content=text_content,
            uploaded_by=current_user.id,
            file_size=len(content),
            mime_type=document.content_type,
            status="uploaded",
            doc_metadata={
                "csv_path": csv_path,
                "csv_filename": data_csv.filename,
                "custom_prompt": custom_prompt
            }
        )

        logger.info(f"Adding document to database...")
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"✅ Document successfully uploaded: ID={doc.id}, filename={document.filename}")
        logger.info(f"=== Upload Document Completed ===")

        return {
            "id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "upload_date": doc.upload_date,
            "csv_filename": data_csv.filename
        }

    except Exception as e:
        logger.error(f"❌ Error uploading document: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error uploading document: {str(e)}"
        )


@router.get("/{doc_id}")
def get_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get document details

    Args:
        doc_id: Document ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Document details
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "upload_date": doc.upload_date,
        "document_type": doc.document_type
    }


@router.post("/{doc_id}/parse")
def parse_document(
    doc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse document with LLM using CSV schema context

    Args:
        doc_id: Document ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Parsed query and validation results
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        from ..services.document_parser import parse_document_with_llm
        from ..models import Query

        logger.info(f"=== Parsing Document Started ===")
        logger.info(f"Document ID: {doc_id}, Filename: {doc.filename}")

        # Get CSV path from document metadata
        csv_path = doc.doc_metadata.get("csv_path") if doc.doc_metadata else None
        custom_prompt = doc.doc_metadata.get("custom_prompt") if doc.doc_metadata else None

        logger.info(f"CSV path: {csv_path}")
        logger.info(f"Custom prompt: {custom_prompt[:50] if custom_prompt else 'None'}...")

        # Parse document with LLM
        parse_result = parse_document_with_llm(
            document_text=doc.text_content,
            document_type="sla",
            custom_prompt=custom_prompt,
            csv_path=csv_path
        )

        logger.info(f"Parse result status: {parse_result.get('status')}")

        if parse_result.get("status") == "error":
            logger.error(f"Document parsing failed: {parse_result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document parsing failed: {parse_result.get('error')}"
            )

        # Extract the SQL query from the parsed result
        extracted_terms = parse_result.get("extracted_terms", {})
        query_text = extracted_terms.get("sql_query", "")

        if not query_text:
            logger.warning(f"No SQL query found in extracted terms")
            query_text = "SELECT * FROM sample_billing_data"

        logger.info(f"Generated query: {query_text}")

        # Create Query record
        query = Query(
            document_id=doc.id,
            query_text=query_text,
            query_type="cost_analysis",
            extraction_confidence=0.85,
            prompt_used="default" if not custom_prompt else "custom",
            prompt_text=custom_prompt or "Default SLA analysis prompt",
            model_used=parse_result.get("model_used", settings.llm_model),
            is_validated=False,
            validation_status="pending"
        )

        db.add(query)
        db.commit()
        db.refresh(query)

        doc.status = "parsed"
        db.commit()

        logger.info(f"✅ Document {doc_id} parsed successfully")
        logger.info(f"=== Parsing Document Completed ===")

        return {
            "query_id": query.id,
            "query_text": query.query_text,
            "status": "parsed",
            "confidence": query.extraction_confidence,
            "model_used": parse_result.get("model_used"),
            "extraction_details": extracted_terms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error parsing document: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing document: {str(e)}"
        )
