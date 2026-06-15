import pytest
from app.agents.research import run_research_agent, ResearchReport
from app.agents.qualify import run_qualification_agent, QualificationResult
from app.agents.outreach import run_outreach_agent, OutreachDraft

@pytest.mark.asyncio
async def test_research_agent():
    """Test that the Research Agent correctly compiles structured research report."""
    company = "Acme Corp"
    report = await run_research_agent(company)
    
    assert isinstance(report, ResearchReport)
    assert report.company_name == company
    assert len(report.profile) > 0
    assert len(report.growth_signals) > 0
    assert len(report.technology_adoption_signals) > 0

@pytest.mark.asyncio
async def test_qualification_agent():
    """Test that the Qualification Agent evaluates fits against target criteria."""
    report = ResearchReport(
        company_name="Acme Corp",
        profile="Acme Corp is a warehouse robotics provider.",
        industry="Manufacturing & Robotics",
        growth_signals={"funding": "Series A"},
        hiring_signals={"roles": ["Cloud Engineer"]},
        technology_adoption_signals=["AWS"],
        risks=[]
    )
    
    criteria = {"industry": "Robotics"}
    result = await run_qualification_agent(criteria, report)
    
    assert isinstance(result, QualificationResult)
    assert result.score >= 0 and result.score <= 100
    assert result.prioritization in ["High", "Medium", "Low"]
    assert len(result.rationale) > 0

@pytest.mark.asyncio
async def test_outreach_agent():
    """Test that the Outreach Agent generates cold outreach drafts."""
    report = ResearchReport(
        company_name="Acme Corp",
        profile="Acme Corp is a warehouse robotics provider.",
        industry="Manufacturing & Robotics",
        growth_signals={"funding": "Series A"},
        hiring_signals={"roles": ["Cloud Engineer"]},
        technology_adoption_signals=["AWS"],
        risks=[]
    )
    
    qualification = QualificationResult(
        is_icp_match=True,
        score=85,
        prioritization="High",
        rationale="Strong fit in robotics."
    )
    
    draft = await run_outreach_agent(report, qualification)
    
    assert isinstance(draft, OutreachDraft)
    assert len(draft.email_subject) > 0
    assert len(draft.email_body) > 0
    assert len(draft.linkedin_message) > 0
    assert len(draft.sales_angle) > 0

def test_agent_router_llm_factory():
    """Verify that get_llm correctly instantiates ChatOpenAI for AgentRouter."""
    from app.services.llm_service import get_llm
    from app.core.config import settings
    from langchain_openai import ChatOpenAI
    
    # Save original settings
    old_provider = settings.LLM_PROVIDER
    old_key = settings.AGENT_ROUTER_API_KEY
    old_base = settings.AGENT_ROUTER_BASE_URL
    old_model = settings.AGENT_ROUTER_MODEL
    
    try:
        settings.LLM_PROVIDER = "agentrouter"
        settings.AGENT_ROUTER_API_KEY = "test_agent_router_token_xyz"
        settings.AGENT_ROUTER_BASE_URL = "https://agentrouter.org/v1"
        settings.AGENT_ROUTER_MODEL = "deepseek-r1-0528"
        
        llm = get_llm(temperature=0.5)
        
        # Check if ChatOpenAI is a mock (which it is under the local Python 3.9 mock harness)
        if type(ChatOpenAI).__name__ == "MagicMock":
            assert ChatOpenAI.called
            args = ChatOpenAI.call_args[1]
            assert args["model"] == "deepseek-r1-0528"
            assert args["api_key"] == "test_agent_router_token_xyz"
            assert args["base_url"] == "https://agentrouter.org/v1"
            assert args["temperature"] == 0.5
        else:
            assert isinstance(llm, ChatOpenAI)
            assert llm.model_name == "deepseek-r1-0528"
            assert llm.openai_api_key.get_secret_value() == "test_agent_router_token_xyz"
            assert str(llm.openai_api_base) == "https://agentrouter.org/v1"
            assert llm.temperature == 0.5
        
    finally:
        # Restore settings
        settings.LLM_PROVIDER = old_provider
        settings.AGENT_ROUTER_API_KEY = old_key
        settings.AGENT_ROUTER_BASE_URL = old_base
        settings.AGENT_ROUTER_MODEL = old_model
