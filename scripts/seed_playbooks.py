import asyncio
import logging
from app.services.milvus_service import milvus_service
from app.rag.indexing import index_documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("platform.scripts.seed")

PLAYBOOKS = [
    {
        "text": "Outreach Playbook: When writing cold emails to software managers, open with a recently observed growth signal (e.g. Series funding or expansion). Frame our automated cost-optimization platform as a way to support rapid engineering growth without ballooning server costs. Keep length under 150 words.",
        "company_name": "",
        "source": "cold_outreach_guide"
    },
    {
        "text": "Cloud Cost Optimization Value Pitch: Focus on how our platform automatically resizes underutilized Kubernetes clusters and identifies orphan EBS volumes in AWS. State that clients typically save 20-30% on their cloud bill in the first 30 days without impact to service availability.",
        "company_name": "",
        "source": "value_pitch_k8s"
    },
    {
        "text": "Objection Handling - Budget Concerns: If a prospect objects that they have no budget for new developer tools, respond with our zero-risk trial: we will perform a free cloud audit. If we do not identify at least 15% in savings, they pay nothing. If we do, we take a 10% cut of the realized savings.",
        "company_name": "",
        "source": "objection_handling_budget"
    },
    {
        "text": "Manufacturing & Robotics Integration Pitch: Highlight our special connectors for industrial ERP and warehouse management tools. Frame the product as a bridge to modernize legacy data flows to cloud data lakes.",
        "company_name": "",
        "source": "robotics_integration"
    }
]

async def main():
    logger.info("Starting sales playbooks seed script...")
    
    # Establish connection and ensure collections exist
    connected = milvus_service.connect(retries=3, delay=1.0)
    if not connected:
        logger.error("Failed to connect to Milvus. Seeding skipped.")
        return
        
    logger.info("Indexing playbooks into Milvus...")
    await index_documents("sales_playbooks", PLAYBOOKS)
    logger.info("Successfully seeded Milvus collections.")

if __name__ == "__main__":
    asyncio.run(main())
