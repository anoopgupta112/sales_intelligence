import json
from langchain_core.tools import tool

@tool("company_search_tool")
def company_search_tool(company_name: str) -> str:
    """
    Search for company profile and metadata.
    Input: company_name (e.g. Acme Corp)
    Output: JSON string with company metadata, including size, industry, HQ, and tech stack.
    """
    name_lower = company_name.lower()
    
    # Mock data for realistic response
    if "acme" in name_lower:
        result = {
            "company_name": "Acme Corp",
            "domain": "acme.com",
            "industry": "Manufacturing & Robotics",
            "company_size": "5000+ employees",
            "hq_location": "Chicago, IL",
            "tech_stack": ["Salesforce", "AWS", "SAP ERP", "Python", "Kubernetes"],
            "description": "Acme Corp is a global leader in manufacturing automation and robotic systems, catering to warehouse logistics."
        }
    elif "hooli" in name_lower:
        result = {
            "company_name": "Hooli",
            "domain": "hooli.xyz",
            "industry": "Internet Software & Services",
            "company_size": "10000+ employees",
            "hq_location": "Mountain View, CA",
            "tech_stack": ["Google Cloud", "Go", "Angular", "Spanner", "TensorFlow"],
            "description": "Hooli is a multinational technology conglomerate specializing in search, cloud computing, and AI systems."
        }
    else:
        # Default mock dynamic generation
        clean_name = company_name.replace("'", "").title()
        domain = f"{company_name.lower().replace(' ', '')}.io"
        result = {
            "company_name": clean_name,
            "domain": domain,
            "industry": "Enterprise SaaS",
            "company_size": "100-500 employees",
            "hq_location": "San Francisco, CA",
            "tech_stack": ["PostgreSQL", "React", "Node.js", "AWS", "HubSpot"],
            "description": f"{clean_name} is a rapidly growing enterprise software company specializing in digital workflow optimization."
        }
        
    return json.dumps(result, indent=2)
