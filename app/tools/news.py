import json
from langchain_core.tools import tool

@tool("news_tool")
def news_tool(company_name: str) -> str:
    """
    Search for recent news and events for a company.
    Input: company_name (e.g. Acme Corp)
    Output: JSON string with recent events (growth signals, hiring, risks).
    """
    name_lower = company_name.lower()
    
    if "acme" in name_lower:
        events = [
            {
                "date": "2026-04-10",
                "title": "Acme Corp opens new robotic research lab in Detroit",
                "category": "growth",
                "summary": "Acme Corp announced a $50M investment in a new robotics engineering facility to accelerate AI adoption in their assembly lines."
            },
            {
                "date": "2026-05-15",
                "title": "Acme Corp begins major hiring drive for cloud architects",
                "category": "hiring",
                "summary": "Acme Corp listed 50+ open roles for AWS and Kubernetes engineers, indicating a large cloud infrastructure expansion."
            },
            {
                "date": "2026-06-01",
                "title": "Supply chain bottlenecks challenge Acme Corp warehouse output",
                "category": "risk",
                "summary": "Recent logistics reports outline minor slowdowns in steel and semiconductor supply chains, affecting Acme's custom robotics delivery times."
            }
        ]
    elif "hooli" in name_lower:
        events = [
            {
                "date": "2026-05-20",
                "title": "Hooli launches Nucleus 2.0 compression platform",
                "category": "growth",
                "summary": "Hooli unveiled its new data compression SaaS targeting cloud service providers, boasting 40% reduction in data egress costs."
            },
            {
                "date": "2026-06-10",
                "title": "Hooli faces scrutiny over data privacy policies",
                "category": "risk",
                "summary": "Regulatory authorities are reviewing Hooli's updated telemetry policies, introducing compliance risks in EU markets."
            }
        ]
    else:
        events = [
            {
                "date": "2026-05-01",
                "title": f"{company_name} raises $25M Series B for expansion",
                "category": "growth",
                "summary": f"{company_name} closed a Series B funding round to scale its sales and engineering operations internationally."
            },
            {
                "date": "2026-05-28",
                "title": f"{company_name} adds 10 new software engineer job openings",
                "category": "hiring",
                "summary": f"The company posted new technical listings seeking senior backend developers and data engineers."
            }
        ]
        
    return json.dumps(events, indent=2)
