"""
Document Type Registry and Configuration
Defines document types and their extraction prompts for Claude API
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class DocumentType:
    """Configuration for a document type"""
    name: str
    description: str
    extraction_prompt: str
    expected_outputs: List[str]
    examples: Optional[List[str]] = None

    def get_full_prompt(self, document_text: str, custom_instructions: str = "") -> str:
        """Generate full prompt for Claude with document context"""
        prompt = f"""{self.extraction_prompt}

{"Additional Instructions: " + custom_instructions if custom_instructions else ""}

---
Document to Analyze:
{document_text}

Please provide your analysis in JSON format with the structure defined above."""
        return prompt


# Generic document type - works for any document
GENERIC_DOCUMENT_TYPE = DocumentType(
    name="custom",
    description="Generic document type for any contractual or business document",
    extraction_prompt="""Analyze the provided document and extract key business, financial, and operational terms.

Return a JSON object with:
{
    "document_summary": "Brief overview of the document",
    "parties_involved": ["List of parties"],
    "key_terms": {
        "financial_terms": ["All monetary amounts, penalties, credits"],
        "performance_metrics": ["Any SLAs, KPIs, or performance targets"],
        "conditions": ["Important conditions and exclusions"],
        "time_periods": ["Relevant time periods and deadlines"],
        "calculation_formulas": ["Any formulas or calculation rules mentioned"]
    },
    "penalties_and_incentives": {
        "penalties": ["Penalties for non-compliance"],
        "credits": ["Credits or incentives"],
        "rewards": ["Rewards or bonuses"]
    },
    "data_requirements": {
        "required_fields": ["Data fields needed to validate claims"],
        "calculation_approach": "How to calculate recovery amounts"
    },
    "recommended_sql_approach": "Suggested SQL logic to extract relevant data",
    "extraction_confidence": "high/medium/low"
}""",
    expected_outputs=[
        "document_summary",
        "parties_involved",
        "key_terms",
        "penalties_and_incentives",
        "data_requirements",
        "recommended_sql_approach"
    ]
)

# SLA-specific document type - SLA Recovery Agent
SLA_DOCUMENT_TYPE = DocumentType(
    name="sla",
    description="Service Level Agreement (SLA) contract - SLA Recovery Agent",
    extraction_prompt="""You are an SLA Recovery Agent. Your task is to analyze SLA documents and extract recovery rules and generate SQL queries.

INSTRUCTIONS:
1. Extract ALL SLA rules, penalties, and thresholds from the document
2. Identify violation conditions and penalty calculations
3. Generate a single, optimized SQL query to calculate SLA recovery amounts
4. Return ONLY valid JSON - no comments, no explanations

Return JSON with this EXACT structure:
{
    "sla_rules": [
        {
            "rule_id": "RULE_001",
            "metric": "uptime_percent",
            "threshold": 99.0,
            "threshold_operator": "<",
            "penalty_amount": 500,
            "penalty_type": "monetary",
            "penalty_percentage": 5,
            "description": "5% penalty per month if uptime falls below 99%",
            "applicable_period": "monthly"
        }
    ],
    "violation_conditions": [
        {
            "metric": "avg_response_time",
            "condition": "avg_response_time > 2",
            "penalty_rule": "2% credit per incident when response time exceeds 2 seconds"
        }
    ],
    "sql_query": "SELECT incident_date, CASE WHEN uptime_percent < 99 THEN (100 - uptime_percent) * 100 ELSE 0 END as penalty_monetary FROM sample_billing_data ORDER BY incident_date",
    "data_fields_required": ["incident_date", "uptime_percent", "avg_response_time", "error_rate"],
    "monthly_service_fee": 10000,
    "max_monthly_penalty_percentage": 30
}""",
    expected_outputs=[
        "sla_rules",
        "violation_conditions",
        "sql_query",
        "data_fields_required"
    ]
)

# Insurance policy document type
INSURANCE_DOCUMENT_TYPE = DocumentType(
    name="insurance",
    description="Insurance policy or claims document",
    extraction_prompt="""Analyze this insurance policy/claims document.

Extract and return JSON with:
{
    "policy_info": {
        "policy_number": "Policy number if mentioned",
        "coverage_types": ["Types of coverage"],
        "coverage_amounts": ["Coverage limits and amounts"],
        "deductibles": ["Deductible amounts and conditions"],
        "exclusions": ["What is excluded"]
    },
    "claim_terms": {
        "eligible_claims": ["What triggers a claim"],
        "claim_procedures": ["Process for claiming"],
        "supporting_documentation": ["Required documents"],
        "timeframes": ["Deadlines for claims"]
    },
    "financial_terms": {
        "premiums": "Premium amounts or structure",
        "co_pays": "Co-payment amounts",
        "reimbursements": "Reimbursement percentages"
    },
    "data_requirements": {
        "claim_fields": ["Data fields needed for claims"],
        "validation_rules": ["Rules to validate claims"]
    }
}""",
    expected_outputs=[
        "policy_info",
        "claim_terms",
        "financial_terms",
        "data_requirements"
    ]
)

# Service agreement document type
SERVICE_AGREEMENT_TYPE = DocumentType(
    name="service_agreement",
    description="General service agreement or contract",
    extraction_prompt="""Analyze this service agreement and extract commercial and operational terms.

Extract and return JSON with:
{
    "agreement_overview": {
        "service_provider": "Name of service provider",
        "service_recipient": "Name of recipient",
        "services_provided": ["List of services"],
        "effective_period": "Duration of agreement"
    },
    "financial_terms": {
        "pricing_model": "How pricing works",
        "payment_terms": "Payment schedule and terms",
        "price_adjustments": "How prices can change",
        "termination_fees": "Fees for early termination"
    },
    "service_level_targets": {
        "availability": "System/service availability targets",
        "performance": "Performance metrics and targets",
        "support_levels": "Support level agreements"
    },
    "remedies_and_escalation": {
        "breaches": ["What constitutes a breach"],
        "remediation": ["Remedies for breaches"],
        "dispute_resolution": "How disputes are resolved"
    },
    "data_mapping": {
        "metric_fields": ["Fields in data that correspond to targets"],
        "calculation_logic": "How to measure against targets"
    }
}""",
    expected_outputs=[
        "agreement_overview",
        "financial_terms",
        "service_level_targets",
        "remedies_and_escalation"
    ]
)

# Registry of all document types
DOCUMENT_TYPE_REGISTRY: Dict[str, DocumentType] = {
    "custom": GENERIC_DOCUMENT_TYPE,
    "sla": SLA_DOCUMENT_TYPE,
    "insurance": INSURANCE_DOCUMENT_TYPE,
    "service_agreement": SERVICE_AGREEMENT_TYPE,
}


def get_document_type(doc_type: str) -> DocumentType:
    """Get a document type by name, fallback to generic if not found"""
    return DOCUMENT_TYPE_REGISTRY.get(doc_type.lower(), GENERIC_DOCUMENT_TYPE)


def get_all_document_types() -> Dict[str, DocumentType]:
    """Get all registered document types"""
    return DOCUMENT_TYPE_REGISTRY.copy()


def register_document_type(doc_type: DocumentType):
    """Register a new document type"""
    DOCUMENT_TYPE_REGISTRY[doc_type.name.lower()] = doc_type


def list_document_type_names() -> List[str]:
    """Get list of all registered document type names"""
    return list(DOCUMENT_TYPE_REGISTRY.keys())
