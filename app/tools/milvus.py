import json
import logging
from langchain_core.tools import tool
from app.services.milvus_service import milvus_service
from app.rag.indexing import get_embedding

logger = logging.getLogger("platform.tools.milvus")

@tool("milvus_retriever")
def milvus_retriever(query: str) -> str:
    """
    Retrieve sales playbooks or company insights from the vector database.
    Input: query (e.g. 'how to pitch acme corp or enterprise cloud sales playbook')
    Output: JSON string with top relevant playbooks or company knowledge chunks.
    """
    try:
        # Generate query embedding
        query_vector = get_embedding(query)
        
        # Search the sales_playbooks collection
        results = milvus_service.search(
            collection_name="sales_playbooks",
            query_vector=query_vector,
            limit=3
        )
        
        # If no results (empty Milvus or offline), return some default mock playbooks for fallback
        if not results:
            logger.warning("Milvus search returned no playbooks. Using fallback mock playbooks.")
            # Fallback playbooks matching query keywords
            q_lower = query.lower()
            if "outreach" in q_lower or "email" in q_lower:
                return json.dumps([
                    {
                        "text": "Outreach Playbook: When drafting emails, lead with a strong growth signal (e.g., funding or office expansion). Connect this to our capability to scale their software systems efficiently.",
                        "company_name": "",
                        "source": "general_playbook"
                    }
                ], indent=2)
            elif "objection" in q_lower or "risk" in q_lower:
                return json.dumps([
                    {
                        "text": "Objection Handling Playbook: If a target has supply chain or delivery risks, highlight our predictive analytics feature which reduces inventory delays by 15%.",
                        "company_name": "",
                        "source": "objection_handling"
                    }
                ], indent=2)
            else:
                return json.dumps([
                    {
                        "text": "Enterprise Value Pitch Playbook: Focus on cloud cost optimization, automation of tedious engineering tasks, and integrations with Salesforce/AWS.",
                        "company_name": "",
                        "source": "value_pitch"
                    }
                ], indent=2)
                
        # Format results
        hits = []
        for hit in results:
            hits.append({
                "text": hit["text"],
                "company_name": hit["company_name"],
                "source": hit["source"]
            })
            
        return json.dumps(hits, indent=2)
    except Exception as e:
        logger.error(f"Error in milvus_retriever tool: {e}")
        # Graceful fallback response so the LLM doesn't break
        return json.dumps([
            {
                "text": "Default Pitch: Focus on security, cloud scalability, and seamless APIs. Acme products save developers 10 hours a week.",
                "company_name": "",
                "source": "fallback"
            }
        ], indent=2)
