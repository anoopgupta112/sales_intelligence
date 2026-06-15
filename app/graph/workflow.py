import logging
import uuid
from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END

from app.graph.state import WorkflowState
from app.agents.research import run_research_agent, ResearchReport
from app.agents.qualify import run_qualification_agent, QualificationResult
from app.agents.outreach import run_outreach_agent, OutreachDraft
import app.db.session as db_session
from app.db.models import Lead, ResearchReport as DBReport, OutreachMessage, WorkflowRun
from app.repositories.leads import lead_repository
from app.repositories.reports import report_repository
from app.repositories.messages import message_repository
from app.repositories.workflows import workflow_run_repository

logger = logging.getLogger("platform.graph.workflow")

# ----------------- GRAPH NODES -----------------

async def discover_companies_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: discover_companies"""
    logger.info(f"[{state['request_id']}] Node: discover_companies")
    target = state.get("target_criteria", {})
    industry = target.get("industry", "Robotics")
    
    # Generate mock discovered companies based on target criteria
    companies = []
    if "robotics" in industry.lower():
        companies = [
            {"company_name": "Acme Corp", "domain": "acme.com", "industry": "Manufacturing & Robotics"},
            {"company_name": "Apex Automation", "domain": "apexautomation.io", "industry": "Industrial Robotics"}
        ]
    elif "internet" in industry.lower() or "software" in industry.lower():
        companies = [
            {"company_name": "Hooli", "domain": "hooli.xyz", "industry": "Internet Software & Services"},
            {"company_name": "Pied Piper", "domain": "piedpiper.io", "industry": "Compression Algorithms"}
        ]
    else:
        # Default mock companies
        companies = [
            {"company_name": f"Global {industry} Inc", "domain": f"global{industry.lower().replace(' ', '')}.com", "industry": industry},
            {"company_name": f"{industry.split()[0]} Tech", "domain": f"{industry.split()[0].lower()}tech.io", "industry": industry}
        ]
        
    # Write to database (leads table)
    async with db_session.async_session_maker() as db:
        for comp in companies:
            # Check if lead already exists
            existing_lead = await lead_repository.get_by_company_name(db, comp["company_name"])
            if not existing_lead:
                await lead_repository.create(db, obj_in={
                    "company_name": comp["company_name"],
                    "domain": comp["domain"],
                    "industry": comp["industry"],
                    "status": "discovered"
                })
        await db.commit()
        
    return {"companies": companies, "workflow_status": "RUNNING"}

async def research_companies_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: research_companies"""
    logger.info(f"[{state['request_id']}] Node: research_companies")
    companies = state.get("companies", [])
    reports: List[Dict[str, Any]] = []
    
    async with db_session.async_session_maker() as db:
        for comp in companies:
            company_name = comp["company_name"]
            
            # Execute CrewAI research agent
            report_pydantic: ResearchReport = await run_research_agent(company_name)
            report_dict = report_pydantic.model_dump()
            reports.append(report_dict)
            
            # Update Lead and save ResearchReport in DB
            lead = await lead_repository.get_by_company_name(db, company_name)
            if lead:
                lead.status = "researched"
                lead.industry = report_pydantic.industry
                # Check if report already exists for this lead
                existing_report = await report_repository.get_by_lead_id(db, lead.id)
                if not existing_report:
                    await report_repository.create(db, obj_in={
                        "lead_id": lead.id,
                        "profile": report_pydantic.profile,
                        "industry": report_pydantic.industry,
                        "growth_signals": report_pydantic.growth_signals,
                        "hiring_signals": report_pydantic.hiring_signals,
                        "tech_adoption": report_pydantic.technology_adoption_signals,
                        "risks": report_pydantic.risks,
                        "raw_report": f"Compiled report for {company_name} in {report_pydantic.industry}."
                    })
        await db.commit()
        
    return {"research_reports": reports}

async def qualify_companies_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: qualify_companies"""
    logger.info(f"[{state['request_id']}] Node: qualify_companies")
    reports = state.get("research_reports", [])
    target = state.get("target_criteria", {})
    qualification_results = []
    
    async with db_session.async_session_maker() as db:
        for rep in reports:
            # Parse report dictionary back to Pydantic for the agent
            report_pydantic = ResearchReport(**rep)
            
            # Execute qualification agent
            qual_result: QualificationResult = await run_qualification_agent(target, report_pydantic)
            qual_dict = qual_result.model_dump()
            qual_dict["company_name"] = report_pydantic.company_name
            qualification_results.append(qual_dict)
            
            # Update Lead in DB
            lead = await lead_repository.get_by_company_name(db, report_pydantic.company_name)
            if lead:
                lead.status = "qualified" if qual_result.is_icp_match else "disqualified"
                lead.score = qual_result.score
        await db.commit()
        
    return {"qualification_results": qualification_results}

async def generate_outreach_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: generate_outreach"""
    logger.info(f"[{state['request_id']}] Node: generate_outreach")
    reports = state.get("research_reports", [])
    quals = state.get("qualification_results", [])
    outreach_drafts = []
    
    # Map qualifications by company name
    qual_map = {q["company_name"]: q for q in quals}
    
    async with db_session.async_session_maker() as db:
        for rep in reports:
            company_name = rep["company_name"]
            qual = qual_map.get(company_name)
            
            # Only generate outreach drafts for matching ICP scores >= 70
            if qual and qual.get("score", 0) >= 70:
                report_pydantic = ResearchReport(**rep)
                qual_pydantic = QualificationResult(**qual)
                
                # Execute outreach copywriting agent
                draft_pydantic: OutreachDraft = await run_outreach_agent(report_pydantic, qual_pydantic)
                draft_dict = draft_pydantic.model_dump()
                draft_dict["company_name"] = company_name
                outreach_drafts.append(draft_dict)
                
                # Save OutreachMessage in DB
                lead = await lead_repository.get_by_company_name(db, company_name)
                if lead:
                    # Check if message already exists
                    existing_msgs = await message_repository.get_by_lead_id(db, lead.id)
                    if not existing_msgs:
                        await message_repository.create(db, obj_in={
                            "lead_id": lead.id,
                            "email_subject": draft_pydantic.email_subject,
                            "email_body": draft_pydantic.email_body,
                            "linkedin_message": draft_pydantic.linkedin_message,
                            "sales_angle": draft_pydantic.sales_angle,
                            "status": "draft"
                        })
        await db.commit()
        
    return {"outreach_drafts": outreach_drafts, "workflow_status": "AWAITING_REVIEW"}

async def human_review_node(state: WorkflowState) -> Dict[str, Any]:
    """Node: human_review (Acts as transition / completion marker after user approval)"""
    logger.info(f"[{state['request_id']}] Node: human_review")
    
    # This node completes the workflow once the user issues a review
    async with db_session.async_session_maker() as db:
        for draft in state.get("outreach_drafts", []):
            company_name = draft["company_name"]
            lead = await lead_repository.get_by_company_name(db, company_name)
            if lead:
                # Update status of outreach messages to finalized/draft
                messages = await message_repository.get_by_lead_id(db, lead.id)
                for msg in messages:
                    msg.status = "finalized"
        await db.commit()
        
    return {"workflow_status": "COMPLETED"}

# ----------------- BUILD GRAPH -----------------

workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("discover_companies", discover_companies_node)
workflow.add_node("research_companies", research_companies_node)
workflow.add_node("qualify_companies", qualify_companies_node)
workflow.add_node("generate_outreach", generate_outreach_node)
workflow.add_node("human_review", human_review_node)

# Set edges
workflow.add_edge(START, "discover_companies")
workflow.add_edge("discover_companies", "research_companies")
workflow.add_edge("research_companies", "qualify_companies")
workflow.add_edge("qualify_companies", "generate_outreach")
workflow.add_edge("generate_outreach", "human_review")
workflow.add_edge("human_review", END)

# Compile graph
app_workflow = workflow.compile()
