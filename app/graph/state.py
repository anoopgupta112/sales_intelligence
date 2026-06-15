from typing import TypedDict, List, Dict, Any, Optional

class WorkflowState(TypedDict):
    request_id: str
    target_criteria: Dict[str, Any]
    companies: List[Dict[str, Any]]                # List of discovered companies (name, domain)
    research_reports: List[Dict[str, Any]]         # List of ResearchReport dictionary contents
    qualification_results: List[Dict[str, Any]]    # List of QualificationResult dictionary contents
    outreach_drafts: List[Dict[str, Any]]          # List of OutreachDraft dictionary contents
    workflow_status: str                           # RUNNING, AWAITING_REVIEW, COMPLETED, FAILED
    errors: List[str]                              # Record of execution errors
