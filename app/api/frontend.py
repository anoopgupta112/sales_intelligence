import os
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Lead, ResearchReport, OutreachMessage
from app.api.auth import get_current_user, RoleChecker
from app.db.models import User

logger = logging.getLogger("platform.api.frontend")
router = APIRouter(tags=["Frontend"])

# Configure Jinja2 templates location
# Templates are at backend/app/templates relative to the app execution directory
templates_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_path)

@router.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serve the Jinja2 HTML dashboard page or API status JSON depending on Accept header."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return templates.TemplateResponse(request=request, name="index.html", context={})
    return JSONResponse(content={"message": "Enterprise Sales Intelligence Platform API is active."})

@router.get("/docs", response_class=HTMLResponse)
async def get_documentation_page(request: Request):
    """Serve the system architecture and flowchart docs page."""
    return templates.TemplateResponse(request=request, name="docs.html", context={})

@router.get(
    "/api/frontend/leads",
    response_model=List[Dict[str, Any]],
    dependencies=[Depends(RoleChecker(["admin", "manager", "representative"]))]
)
async def get_leads_list(db: AsyncSession = Depends(get_db)):
    """Retrieve all leads in descending order of creation for the grid layout."""
    stmt = select(Lead).order_by(Lead.id.desc())
    res = await db.execute(stmt)
    leads = res.scalars().all()
    
    result = []
    for lead in leads:
        result.append({
            "id": lead.id,
            "company_name": lead.company_name,
            "domain": lead.domain,
            "industry": lead.industry,
            "status": lead.status,
            "score": lead.score
        })
    return result

@router.get(
    "/api/frontend/lead/{lead_id}/details",
    response_model=Dict[str, Any],
    dependencies=[Depends(RoleChecker(["admin", "manager", "representative"]))]
)
async def get_lead_full_details(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve combined lead details, research report, and generated outreach message."""
    # 1. Fetch Lead
    stmt = select(Lead).where(Lead.id == lead_id)
    res = await db.execute(stmt)
    lead = res.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    # 2. Fetch Research Report
    stmt_rep = select(ResearchReport).where(ResearchReport.lead_id == lead_id)
    res_rep = await db.execute(stmt_rep)
    report = res_rep.scalar_one_or_none()
    
    # 3. Fetch Outreach Message
    stmt_msg = select(OutreachMessage).where(OutreachMessage.lead_id == lead_id)
    res_msg = await db.execute(stmt_msg)
    message = res_msg.scalar_one_or_none()
    
    return {
        "lead": {
            "id": lead.id,
            "company_name": lead.company_name,
            "domain": lead.domain,
            "industry": lead.industry,
            "status": lead.status,
            "score": lead.score
        },
        "report": {
            "profile": report.profile,
            "industry": report.industry,
            "growth_signals": report.growth_signals,
            "hiring_signals": report.hiring_signals,
            "tech_adoption": report.tech_adoption,
            "risks": report.risks
        } if report else None,
        "message": {
            "sales_angle": message.sales_angle,
            "email_subject": message.email_subject,
            "email_body": message.email_body,
            "linkedin_message": message.linkedin_message,
            "status": message.status
        } if message else None
    }
