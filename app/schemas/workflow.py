from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

class LeadSearchRequest(BaseModel):
    target_criteria: Dict[str, Any] = Field(
        ...,
        description="Search criteria like industry, company size, location, technologies used"
    )

class ResearchRequest(BaseModel):
    lead_id: int
    company_name: str

class QualificationRequest(BaseModel):
    lead_id: int

class OutreachRequest(BaseModel):
    lead_id: int

class OutreachDraftSchema(BaseModel):
    email_subject: str
    email_body: str
    linkedin_message: str
    sales_angle: str

class HumanReviewRequest(BaseModel):
    approved: bool
    modified_draft: Optional[OutreachDraftSchema] = None

class LeadOut(BaseModel):
    id: int
    company_name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    status: str
    score: Optional[int] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ResearchReportOut(BaseModel):
    id: int
    lead_id: int
    profile: Optional[str] = None
    industry: Optional[str] = None
    growth_signals: Optional[Dict[str, Any]] = None
    hiring_signals: Optional[Dict[str, Any]] = None
    tech_adoption: Optional[Dict[str, Any]] = None
    risks: Optional[Dict[str, Any]] = None
    raw_report: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class OutreachMessageOut(BaseModel):
    id: int
    lead_id: int
    email_subject: str
    email_body: str
    linkedin_message: str
    sales_angle: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class WorkflowRunOut(BaseModel):
    id: str
    target_criteria: Dict[str, Any]
    current_step: str
    status: str
    variables: Dict[str, Any]
    errors: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
