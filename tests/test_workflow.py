import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.graph.state import WorkflowState
from app.graph.workflow import (
    discover_companies_node, research_companies_node,
    qualify_companies_node, generate_outreach_node, human_review_node
)
from app.db.models import Lead

@pytest.mark.asyncio
async def test_workflow_state_transitions(db_session: AsyncSession):
    """Test state transitions and node executions in the LangGraph workflow."""
    
    # 1. Setup initial state
    state: WorkflowState = {
        "request_id": "test_run_123",
        "target_criteria": {"industry": "Robotics"},
        "companies": [],
        "research_reports": [],
        "qualification_results": [],
        "outreach_drafts": [],
        "workflow_status": "RUNNING",
        "errors": []
    }
    
    # 2. Test discover_companies node
    disc_output = await discover_companies_node(state)
    assert len(disc_output["companies"]) > 0
    assert disc_output["workflow_status"] == "RUNNING"
    state.update(disc_output)
    
    # 3. Test research_companies node
    res_output = await research_companies_node(state)
    assert len(res_output["research_reports"]) > 0
    state.update(res_output)
    
    # 4. Test qualify_companies node
    qual_output = await qualify_companies_node(state)
    assert len(qual_output["qualification_results"]) > 0
    state.update(qual_output)
    
    # 5. Test generate_outreach node
    out_output = await generate_outreach_node(state)
    assert len(out_output["outreach_drafts"]) > 0
    assert out_output["workflow_status"] == "AWAITING_REVIEW"
    state.update(out_output)
    
    # 6. Test human_review node
    rev_output = await human_review_node(state)
    assert rev_output["workflow_status"] == "COMPLETED"
