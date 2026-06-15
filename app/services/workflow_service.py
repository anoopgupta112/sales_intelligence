import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import app.db.session as db_session
from app.repositories.workflows import workflow_run_repository
from app.repositories.leads import lead_repository
from app.repositories.messages import message_repository
from app.repositories.logs import agent_log_repository
from app.db.models import WorkflowRun, Lead, OutreachMessage
from app.graph.workflow import app_workflow

logger = logging.getLogger("platform.services.workflow")

class WorkflowService:
    async def start_workflow(self, target_criteria: Dict[str, Any]) -> str:
        """Create a new workflow run and trigger execution in the background."""
        run_id = str(uuid.uuid4())
        
        initial_state = {
            "request_id": run_id,
            "target_criteria": target_criteria,
            "companies": [],
            "research_reports": [],
            "qualification_results": [],
            "outreach_drafts": [],
            "workflow_status": "RUNNING",
            "errors": []
        }
        
        # Save workflow run to database
        async with db_session.async_session_maker() as db:
            await workflow_run_repository.create(db, obj_in={
                "id": run_id,
                "target_criteria": target_criteria,
                "current_step": "START",
                "status": "RUNNING",
                "variables": initial_state,
                "errors": []
            })
            # Audit log start
            await agent_log_repository.create(db, obj_in={
                "workflow_run_id": run_id,
                "agent_name": "System",
                "log_message": f"Workflow run {run_id} started with criteria {target_criteria}.",
                "execution_time": 0.0,
                "cost": 0.0
            })
            await db.commit()
            
        # Run workflow in background
        asyncio.create_task(self._execute_workflow_background(run_id, initial_state))
        
        return run_id

    async def _execute_workflow_background(self, run_id: str, state: Dict[str, Any]):
        """Execute the LangGraph workflow nodes asynchronously in background."""
        logger.info(f"[{run_id}] Starting background execution...")
        start_time = datetime.now(timezone.utc)
        
        try:
            # Execute steps up to generate_outreach (which updates state status to AWAITING_REVIEW)
            # We run discover_companies -> research_companies -> qualify_companies -> generate_outreach
            steps = ["discover_companies", "research_companies", "qualify_companies", "generate_outreach"]
            current_state = state
            
            for step in steps:
                # Update current step in DB
                async with db_session.async_session_maker() as db:
                    run = await workflow_run_repository.get(db, run_id)
                    if run:
                        run.current_step = step
                        await db.commit()
                
                # Execute node using CompiledGraph
                # We can call the compiled workflow with the state dictionary
                # In LangGraph, app.ainvoke(current_state) runs the whole graph.
                # To run step by step or handle pauses, we run nodes manually or check after completion.
                # Since we are orchestrating, let's run the graph to the interrupt or final output.
                # Let's run the nodes sequentially to ensure proper database synchronization.
                
            # Run the compiled LangGraph workflow up to generate_outreach node.
            # In our LangGraph, the nodes run sequentially and return the final state when reaching generate_outreach.
            # Let's run graph execution using LangGraph ainvoke
            result_state = await app_workflow.ainvoke(current_state)
            
            # Save updated state to DB
            async with db_session.async_session_maker() as db:
                run = await workflow_run_repository.get(db, run_id)
                if run:
                    run.variables = dict(result_state)
                    run.status = result_state.get("workflow_status", "AWAITING_REVIEW")
                    run.current_step = "human_review" if run.status == "AWAITING_REVIEW" else "END"
                    
                    # Record audit log
                    latency = (datetime.now(timezone.utc) - start_time).total_seconds()
                    await agent_log_repository.create(db, obj_in={
                        "workflow_run_id": run_id,
                        "agent_name": "LangGraph Engine",
                        "log_message": f"Workflow run reached status: {run.status}.",
                        "execution_time": latency,
                        "cost": 0.0
                    })
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"[{run_id}] Error in background workflow execution: {e}")
            async with db_session.async_session_maker() as db:
                run = await workflow_run_repository.get(db, run_id)
                if run:
                    run.status = "FAILED"
                    run.errors = [str(e)]
                    await db.commit()

    async def submit_human_review(self, run_id: str, approved: bool, modified_draft: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Submit approval or edits to resume the workflow run."""
        async with db_session.async_session_maker() as db:
            run = await workflow_run_repository.get(db, run_id)
            if not run:
                raise ValueError("Workflow run not found.")
                
            if run.status != "AWAITING_REVIEW":
                raise ValueError(f"Workflow cannot be reviewed in status '{run.status}'.")
                
            state = run.variables
            
            if not approved:
                run.status = "FAILED"
                run.errors = ["Workflow outreach rejected by user during human review."]
                state["workflow_status"] = "FAILED"
                run.variables = state
                await db.commit()
                return {"status": "REJECTED", "message": "Outreach rejected and workflow aborted."}
                
            # If approved, apply modification if provided
            if modified_draft:
                state["outreach_drafts"] = [modified_draft]
                
            # Execute the final human_review node
            # In our graph: human_review -> END
            run.status = "RUNNING"
            run.current_step = "human_review"
            await db.commit()
            
            # Execute human review step asynchronously
            asyncio.create_task(self._complete_workflow_after_review(run_id, state))
            
            return {"status": "APPROVED", "message": "Workflow approved. Finalizing messages."}

    async def _complete_workflow_after_review(self, run_id: str, state: Dict[str, Any]):
        """Runs the final node and transitions to COMPLETED."""
        try:
            # Manually run the human_review node logic
            # Update status to finalized/approved
            async with db_session.async_session_maker() as db:
                for draft in state.get("outreach_drafts", []):
                    company_name = draft["company_name"]
                    lead = await lead_repository.get_by_company_name(db, company_name)
                    if lead:
                        lead.status = "outreach_generated"
                        # Create or update outreach draft message
                        messages = await message_repository.get_by_lead_id(db, lead.id)
                        if messages:
                            msg = messages[0]
                            msg.email_subject = draft.get("email_subject", msg.email_subject)
                            msg.email_body = draft.get("email_body", msg.email_body)
                            msg.linkedin_message = draft.get("linkedin_message", msg.linkedin_message)
                            msg.sales_angle = draft.get("sales_angle", msg.sales_angle)
                            msg.status = "sent"  # transitioned to sent
                        else:
                            await message_repository.create(db, obj_in={
                                "lead_id": lead.id,
                                "email_subject": draft["email_subject"],
                                "email_body": draft["email_body"],
                                "linkedin_message": draft["linkedin_message"],
                                "sales_angle": draft["sales_angle"],
                                "status": "sent"
                            })
                
                run = await workflow_run_repository.get(db, run_id)
                if run:
                    state["workflow_status"] = "COMPLETED"
                    run.status = "COMPLETED"
                    run.current_step = "END"
                    run.variables = state
                    await db.commit()
                    
        except Exception as e:
            logger.error(f"[{run_id}] Error completing workflow after review: {e}")
            async with db_session.async_session_maker() as db:
                run = await workflow_run_repository.get(db, run_id)
                if run:
                    run.status = "FAILED"
                    run.errors = [str(e)]
                    await db.commit()

workflow_service = WorkflowService()
