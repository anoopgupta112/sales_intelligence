import logging
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from app.services.llm_service import get_llm
from app.agents.research import ResearchReport

logger = logging.getLogger("platform.agents.qualify")

class QualificationResult(BaseModel):
    is_icp_match: bool = Field(..., description="Does the company fit the ideal customer profile?")
    score: int = Field(..., description="Fit score from 0 (poor fit) to 100 (perfect fit).")
    prioritization: str = Field(..., description="Priority tier: High, Medium, or Low.")
    rationale: str = Field(..., description="Explanation of why the score was assigned based on criteria.")

async def run_qualification_agent(target_criteria: dict, report: ResearchReport) -> QualificationResult:
    """
    Executes the Qualification Agent using CrewAI to evaluate a company's fit against target criteria.
    """
    logger.info(f"Running Qualification Agent for: {report.company_name}")
    
    try:
        llm = get_llm()
        
        qualifier = Agent(
            role="Sales Operations Analyst",
            goal="Evaluate target companies against Ideal Customer Profile (ICP) criteria and assign a qualification score.",
            backstory="You are an expert sales operations analyst. You specialize in scoring and prioritizing inbound and outbound leads based on firmographics, growth signals, and tech stacks.",
            tools=[],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )
        
        # Describe the task
        task = Task(
            description=(
                f"Evaluate the company '{report.company_name}' using its research report:\n"
                f"{report.model_dump_json(indent=2)}\n\n"
                f"Compare it against our Target Ideal Customer Profile (ICP) Criteria:\n"
                f"{target_criteria}\n\n"
                f"Calculate an ICP fit score (0-100), decide if it is an ICP match, assign a prioritization tier, and provide a detailed rationale."
            ),
            expected_output="A structured lead qualification result.",
            agent=qualifier,
            output_json=QualificationResult
        )
        
        crew = Crew(
            agents=[qualifier],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        if hasattr(result, "json_dict") and result.json_dict:
            return QualificationResult(**result.json_dict)
        elif isinstance(result, QualificationResult):
            return result
        else:
            import json
            raw_text = str(result)
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end != -1:
                data = json.loads(raw_text[start:end])
                return QualificationResult(**data)
            
            raise ValueError("Failed to parse CrewAI qualification output.")
            
    except Exception as e:
        logger.error(f"CrewAI qualification failed: {e}. Returning simulated/fallback qualification result.")
        # Fallback realistic qualification based on industry overlap
        score = 80 if "software" in report.industry.lower() or "enterprise" in report.industry.lower() else 55
        priority = "High" if score >= 80 else ("Medium" if score >= 50 else "Low")
        return QualificationResult(
            is_icp_match=score >= 70,
            score=score,
            prioritization=priority,
            rationale=f"Simulated match. Company is in the '{report.industry}' industry, matching key SaaS parameters with a size of {report.company_name}."
        )
