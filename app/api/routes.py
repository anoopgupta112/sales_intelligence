from datetime import timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core import security
from app.core.exceptions import CredentialsException, NotFoundException, ForbiddenException
from app.api.auth import get_current_user, RoleChecker
from app.db.models import User
from app.schemas.auth import UserRegister, UserLogin, UserOut, Token
from app.schemas.workflow import (
    LeadSearchRequest, WorkflowRunOut, LeadOut, ResearchReportOut,
    OutreachMessageOut, HumanReviewRequest, ResearchRequest, QualificationRequest, OutreachRequest
)
from app.repositories.user import user_repository
from app.repositories.leads import lead_repository
from app.repositories.workflows import workflow_run_repository
from app.repositories.reports import report_repository
from app.repositories.messages import message_repository
from app.services.workflow_service import workflow_service
from app.agents.research import run_research_agent
from app.agents.qualify import run_qualification_agent
from app.agents.outreach import run_outreach_agent

router = APIRouter(prefix="/api")

# ----------------- AUTHENTICATION ENDPOINTS -----------------

@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user (representative, manager, admin)."""
    existing_user = await user_repository.get_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    hashed_password = security.get_password_hash(user_in.password)
    user = await user_repository.create(db, obj_in={
        "email": user_in.email,
        "hashed_password": hashed_password,
        "role": user_in.role or "representative"
    })
    await db.commit()
    return user

@router.post("/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 compatible token login, retrieve JWT access token."""
    user = await user_repository.get_by_email(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
    
    access_token = security.create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}

# ----------------- SALES PLATFORM ENDPOINTS -----------------

@router.post(
    "/lead-search",
    response_model=Dict[str, str],
    dependencies=[Depends(RoleChecker(["admin", "manager"]))]
)
async def lead_search(request: LeadSearchRequest):
    """
    POST /lead-search
    Initiate lead search and discovery. Triggers the background LangGraph workflow.
    """
    run_id = await workflow_service.start_workflow(request.target_criteria)
    return {"workflow_run_id": run_id, "status": "RUNNING"}

@router.post(
    "/research",
    response_model=ResearchReportOut,
    dependencies=[Depends(RoleChecker(["admin", "manager"]))]
)
async def trigger_research(request: ResearchRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /research
    Run on-demand research on a company.
    """
    lead = await lead_repository.get(db, request.lead_id)
    if not lead:
        raise NotFoundException("Lead not found")
        
    report = await run_research_agent(request.company_name)
    
    # Save/update report
    existing_report = await report_repository.get_by_lead_id(db, lead.id)
    if existing_report:
        db_report = await report_repository.update(db, db_obj=existing_report, obj_in={
            "profile": report.profile,
            "industry": report.industry,
            "growth_signals": report.growth_signals,
            "hiring_signals": report.hiring_signals,
            "tech_adoption": report.technology_adoption_signals,
            "risks": report.risks,
            "raw_report": "On-demand execution of Company Intelligence Research Agent."
        })
    else:
        db_report = await report_repository.create(db, obj_in={
            "lead_id": lead.id,
            "profile": report.profile,
            "industry": report.industry,
            "growth_signals": report.growth_signals,
            "hiring_signals": report.hiring_signals,
            "tech_adoption": report.technology_adoption_signals,
            "risks": report.risks,
            "raw_report": "On-demand execution of Company Intelligence Research Agent."
        })
    
    lead.status = "researched"
    await db.commit()
    return db_report

@router.post(
    "/qualify",
    response_model=Dict[str, Any],
    dependencies=[Depends(RoleChecker(["admin", "manager"]))]
)
async def trigger_qualification(request: QualificationRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /qualify
    Run on-demand ICP qualification on a researched lead.
    """
    lead = await lead_repository.get(db, request.lead_id)
    if not lead:
        raise NotFoundException("Lead not found")
        
    report = await report_repository.get_by_lead_id(db, lead.id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead must have a research report before qualification."
        )
        
    from app.agents.research import ResearchReport as AgentReport
    agent_report = AgentReport(
        company_name=lead.company_name,
        profile=report.profile or "",
        industry=report.industry or "",
        growth_signals=report.growth_signals or {},
        hiring_signals=report.hiring_signals or {},
        technology_adoption_signals=report.tech_adoption or [],
        risks=report.risks or []
    )
    
    target_criteria = {"industry": "Enterprise Software", "company_size": "100-500"} # default fallback
    qual_result = await run_qualification_agent(target_criteria, agent_report)
    
    lead.status = "qualified" if qual_result.is_icp_match else "disqualified"
    lead.score = qual_result.score
    await db.commit()
    
    return {
        "lead_id": lead.id,
        "is_icp_match": qual_result.is_icp_match,
        "score": qual_result.score,
        "priority": qual_result.prioritization,
        "rationale": qual_result.rationale
    }

@router.post(
    "/outreach",
    response_model=OutreachMessageOut,
    dependencies=[Depends(RoleChecker(["admin", "manager"]))]
)
async def trigger_outreach(request: OutreachRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /outreach
    Generate outreach messages for a qualified lead.
    """
    lead = await lead_repository.get(db, request.lead_id)
    if not lead or lead.status != "qualified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead must be in 'qualified' status to generate outreach."
        )
        
    report = await report_repository.get_by_lead_id(db, lead.id)
    if not report:
        raise NotFoundException("Research report not found")
        
    from app.agents.research import ResearchReport as AgentReport
    from app.agents.qualify import QualificationResult as AgentQual
    
    agent_report = AgentReport(
        company_name=lead.company_name,
        profile=report.profile or "",
        industry=report.industry or "",
        growth_signals=report.growth_signals or {},
        hiring_signals=report.hiring_signals or {},
        technology_adoption_signals=report.tech_adoption or [],
        risks=report.risks or []
    )
    
    agent_qual = AgentQual(
        is_icp_match=True,
        score=lead.score or 75,
        prioritization="High",
        rationale="Qualified lead"
    )
    
    draft = await run_outreach_agent(agent_report, agent_qual)
    
    existing_messages = await message_repository.get_by_lead_id(db, lead.id)
    if existing_messages:
        db_message = await message_repository.update(db, db_obj=existing_messages[0], obj_in={
            "email_subject": draft.email_subject,
            "email_body": draft.email_body,
            "linkedin_message": draft.linkedin_message,
            "sales_angle": draft.sales_angle,
            "status": "draft"
        })
    else:
        db_message = await message_repository.create(db, obj_in={
            "lead_id": lead.id,
            "email_subject": draft.email_subject,
            "email_body": draft.email_body,
            "linkedin_message": draft.linkedin_message,
            "sales_angle": draft.sales_angle,
            "status": "draft"
        })
        
    await db.commit()
    return db_message

@router.get(
    "/workflow/{id}",
    response_model=WorkflowRunOut,
    dependencies=[Depends(RoleChecker(["admin", "manager", "representative"]))]
)
async def get_workflow_status(id: str, db: AsyncSession = Depends(get_db)):
    """
    GET /workflow/{id}
    Retrieve the status and state values of a specific workflow run.
    """
    run = await workflow_run_repository.get(db, id)
    if not run:
        raise NotFoundException("Workflow run not found")
    return run

@router.post(
    "/workflow/{id}/review",
    response_model=Dict[str, Any],
    dependencies=[Depends(RoleChecker(["admin", "manager"]))]
)
async def review_workflow(id: str, review: HumanReviewRequest):
    """
    POST /workflow/{id}/review
    Review outreach drafts and approve or edit to complete the workflow.
    """
    draft_dict = review.modified_draft.model_dump() if review.modified_draft else None
    try:
        res = await workflow_service.submit_human_review(id, review.approved, draft_dict)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/lead/{id}",
    response_model=LeadOut,
    dependencies=[Depends(RoleChecker(["admin", "manager", "representative"]))]
)
async def get_lead_details(id: int, db: AsyncSession = Depends(get_db)):
    """
    GET /lead/{id}
    Get lead firmographics, status, score, and related research report details.
    """
    lead = await lead_repository.get(db, id)
    if not lead:
        raise NotFoundException("Lead not found")
    return lead
