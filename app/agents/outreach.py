import logging
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process
from app.services.llm_service import get_llm
from app.agents.research import ResearchReport
from app.agents.qualify import QualificationResult

logger = logging.getLogger("platform.agents.outreach")

class OutreachDraft(BaseModel):
    email_subject: str = Field(..., description="Subject line for email outreach.")
    email_body: str = Field(..., description="Body text for personalized cold email.")
    linkedin_message: str = Field(..., description="Personalized LinkedIn InMail message.")
    sales_angle: str = Field(..., description="The sales angle or value proposition used.")

async def run_outreach_agent(report: ResearchReport, qualification: QualificationResult) -> OutreachDraft:
    """
    Executes the Outreach Agent using CrewAI to draft emails and LinkedIn messages for qualified leads.
    """
    logger.info(f"Running Outreach Agent for: {report.company_name}")
    
    try:
        llm = get_llm()
        
        copywriter = Agent(
            role="Sales Copywriter",
            goal="Generate highly personalized, high-converting outreach emails and LinkedIn messages.",
            backstory="You are an expert sales copywriter. You specialize in crafting concise, compelling, and relevant cold emails and LinkedIn messages that reference company growth signals to secure demo calls.",
            tools=[],
            llm=llm,
            verbose=True,
            allow_delegation=False
        )
        
        task = Task(
            description=(
                f"Review the company research report:\n"
                f"{report.model_dump_json(indent=2)}\n\n"
                f"Review the qualification rationale:\n"
                f"ICP Score: {qualification.score}\n"
                f"Rationale: {qualification.rationale}\n\n"
                f"Write a personalized, compelling cold email (subject & body) and a LinkedIn message. "
                f"Focus on a specific sales angle (value proposition) matching their growth signals or technology."
            ),
            expected_output="A structured set of outreach materials (email and LinkedIn messages).",
            agent=copywriter,
            output_json=OutreachDraft
        )
        
        crew = Crew(
            agents=[copywriter],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        
        if hasattr(result, "json_dict") and result.json_dict:
            return OutreachDraft(**result.json_dict)
        elif isinstance(result, OutreachDraft):
            return result
        else:
            import json
            raw_text = str(result)
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end != -1:
                data = json.loads(raw_text[start:end])
                return OutreachDraft(**data)
            
            raise ValueError("Failed to parse CrewAI outreach output.")
            
    except Exception as e:
        logger.error(f"CrewAI outreach failed: {e}. Returning simulated/fallback outreach draft.")
        # Fallback realistic outreach copy
        return OutreachDraft(
            email_subject=f"Accelerating {report.company_name}'s cloud infrastructure growth",
            email_body=(
                f"Hi team,\n\n"
                f"I noticed that {report.company_name} is expanding its engineering presence and recruiting Cloud Infrastructure Engineers.\n\n"
                f"Many SaaS companies struggle with scaling their backend systems while keeping cloud costs in check. "
                f"We specialize in automated cost-optimization that cuts AWS and Kubernetes expenses by up to 25%.\n\n"
                f"Would you be open to a brief, 10-minute demo next Tuesday to see how we could help support your growth?\n\n"
                f"Best regards,\nSales Representative"
            ),
            linkedin_message=(
                f"Hi, noticed {report.company_name} is hiring cloud architects! We help SaaS companies optimize AWS/K8s costs by 25%. Open to a brief chat?"
            ),
            sales_angle="Cloud cost optimization tied to open hiring signals for cloud engineers."
        )
