"""
Calculations Router
SQL query validation and execution for cost calculations
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..auth import get_current_user
from ..models import User, Query, Calculation
from ..services.math_engine import get_math_engine, _serialize_for_json
from ..services.csv_utils import validate_column_names

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Calculations"])


@router.post("/{query_id}/validate")
def validate_calculation(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate SQL query syntax and schema

    Args:
        query_id: Query ID to validate
        current_user: Current authenticated user
        db: Database session

    Returns:
        Validation results
    """
    try:
        logger.info(f"=== SQL Validation Started ===")
        logger.info(f"Query ID: {query_id}, User: {current_user.username}")

        # Get query from database
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )

        logger.info(f"Query text: {query.query_text[:100]}...")

        # Get related document for CSV path
        document = query.document
        if not document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated document not found"
            )

        # Get CSV path from document metadata
        csv_path = None
        if document.doc_metadata:
            csv_path = document.doc_metadata.get("csv_path")

        logger.info(f"CSV path: {csv_path}")

        # Get Math Engine
        math_engine = get_math_engine()

        # Validate SQL
        is_valid, error_message = math_engine.validate_sql(
            query=query.query_text,
            data_file=csv_path
        )

        if is_valid:
            logger.info(f"✅ SQL validation passed")

            # Update query status
            query.is_validated = True
            query.validation_status = "valid"
            db.commit()

            return {
                "status": "success",
                "query_id": query_id,
                "is_valid": True,
                "message": "SQL query is valid and ready to execute",
                "validation_status": "valid"
            }
        else:
            logger.warning(f"❌ SQL validation failed: {error_message}")

            # Update query status
            query.is_validated = False
            query.validation_status = "invalid"
            db.commit()

            return {
                "status": "error",
                "query_id": query_id,
                "is_valid": False,
                "error": error_message,
                "message": "SQL query validation failed",
                "validation_status": "invalid"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Validation error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )


@router.post("/{query_id}/execute")
def execute_calculation(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute validated SQL query and store results

    Args:
        query_id: Query ID to execute
        current_user: Current authenticated user
        db: Database session

    Returns:
        Query execution results
    """
    try:
        logger.info(f"=== Query Execution Started ===")
        logger.info(f"Query ID: {query_id}, User: {current_user.username}")

        # Get query from database
        query = db.query(Query).filter(Query.id == query_id).first()
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found"
            )

        # Check if query is validated
        if not query.is_validated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query must be validated before execution"
            )

        logger.info(f"Query: {query.query_text[:100]}...")

        # Get related document for CSV path
        document = query.document
        if not document:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Associated document not found"
            )

        # Get CSV path from document metadata
        csv_path = None
        if document.doc_metadata:
            csv_path = document.doc_metadata.get("csv_path")

        if not csv_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file path not found in document metadata"
            )

        logger.info(f"CSV file: {csv_path}")

        # Get Math Engine
        math_engine = get_math_engine()

        # Execute query
        execution_result = math_engine.execute_query(
            query=query.query_text,
            data_file=csv_path,
            limit=1000
        )

        logger.info(f"Execution result status: {execution_result.get('status')}")

        if execution_result.get("status") != "success":
            logger.error(f"Execution failed: {execution_result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Query execution failed: {execution_result.get('message')}"
            )

        # Extract SLA rules from query extraction if available
        sla_rules = []
        if query.extracted_terms:
            sla_rules = query.extracted_terms.get("sla_rules", [])

        # Create calculation record with universal field names
        calculation = Calculation(
            query_id=query.id,
            execution_status="success",
            result_rows_count=execution_result.get("rows_count", 0),
            result_columns=execution_result.get("columns", []),
            result_column_types=execution_result.get("column_types", {}),
            result_data=execution_result.get("sample_data", []),
            sanity_check_status="passed" if not execution_result.get("sanity_check", {}).get("warnings") else "warning",
            sanity_check_details=execution_result.get("sanity_check", {}),

            # SLA-specific fields
            sla_rules=sla_rules,

            # Statistics and metadata
            summary_statistics=execution_result.get("summary_statistics", {}),
            data_metadata={
                "total_rows": execution_result.get("rows_count"),
                "table_name": execution_result.get("table_name"),
                "source_file": execution_result.get("source_file"),
                "data_schema": execution_result.get("data_schema", {})
            },
            table_name=execution_result.get("table_name"),
            source_file=execution_result.get("source_file")
        )

        db.add(calculation)
        db.commit()
        db.refresh(calculation)

        logger.info(f"✅ Query executed successfully. Calculation ID: {calculation.id}")
        logger.info(f"Results: {execution_result.get('rows_count')} rows, Columns: {execution_result.get('columns')}")
        if sla_rules:
            logger.info(f"SLA Rules extracted: {len(sla_rules)} rules")

        return _serialize_for_json({
            "status": "success",
            "query_id": query_id,
            "calculation_id": calculation.id,
            "message": "Query executed successfully",
            "rows_count": execution_result.get("rows_count"),
            "columns": execution_result.get("columns"),
            "column_types": execution_result.get("column_types"),
            "table_name": execution_result.get("table_name"),
            "source_file": execution_result.get("source_file"),
            "sample_data": execution_result.get("sample_data", [])[:10],
            "summary_statistics": execution_result.get("summary_statistics"),
            "sanity_check": execution_result.get("sanity_check"),
            "sla_rules": sla_rules if sla_rules else None
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Execution error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Execution error: {str(e)}"
        )


@router.get("/{calculation_id}")
def get_calculation(
    calculation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get calculation details

    Args:
        calculation_id: Calculation ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Calculation details
    """
    try:
        calculation = db.query(Calculation).filter(
            Calculation.id == calculation_id
        ).first()

        if not calculation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Calculation {calculation_id} not found"
            )

        return _serialize_for_json({
            "id": calculation.id,
            "query_id": calculation.query_id,
            "status": calculation.execution_status,
            "result_rows": calculation.result_rows_count,
            "result_columns": calculation.result_columns,
            "result_column_types": calculation.result_column_types,
            "table_name": calculation.table_name,
            "source_file": calculation.source_file,
            "sample_data": calculation.result_data,
            "summary_statistics": calculation.summary_statistics,
            "sanity_check": calculation.sanity_check_details,
            "sla_rules": calculation.sla_rules if calculation.sla_rules else [],
            "created_at": str(calculation.created_at),
            "data_metadata": calculation.data_metadata
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting calculation: {str(e)}"
        )


@router.get("/query/{query_id}/calculations")
def get_query_calculations(
    query_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all calculations for a query

    Args:
        query_id: Query ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of calculations
    """
    try:
        calculations = db.query(Calculation).filter(
            Calculation.query_id == query_id
        ).all()

        return {
            "status": "success",
            "query_id": query_id,
            "calculations": [
                {
                    "id": calc.id,
                    "status": calc.execution_status,
                    "result_rows": calc.result_rows,
                    "created_at": calc.created_at
                }
                for calc in calculations
            ]
        }

    except Exception as e:
        logger.error(f"Error getting calculations: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error getting calculations: {str(e)}"
        )
