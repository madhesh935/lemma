import asyncio
import traceback
from fastapi import APIRouter
from pydantic import BaseModel

from lemma.workflows.investigation_workflow import InvestigationWorkflow

router = APIRouter(prefix="/test", tags=["Test Runner"])

@router.get("/verify-workflow")
async def verify_workflow():
    results = {
        "status": "started",
        "stages_passed": [],
        "errors": []
    }
    
    try:
        # Step 1: Init workflow
        workflow = InvestigationWorkflow(pod_id="TEST-CASE-999")
        results["stages_passed"].append("initialization")
        
        # Step 2: Run workflow with a mock context
        context = {
            "evidence_files": [
                {"id": "doc_1", "type": "pdf", "name": "autopsy_report.pdf"},
                {"id": "gps_1", "type": "gps", "name": "suspect_phone.csv"}
            ]
        }
        
        # The workflow runs through stages automatically until PAUSED_FOR_HUMAN
        # We will wrap it in a timeout just in case it hangs
        state = await asyncio.wait_for(workflow.start(context), timeout=15.0)
        
        results["stages_passed"].append("workflow_execution")
        results["final_state"] = state
        
        if state.get("current_step") == "investigator_review":
            results["status"] = "success"
        else:
            results["status"] = "partial"
            results["errors"].append(f"Workflow stopped at unexpected step: {state.get('current_step')}")
            
    except Exception as e:
        results["status"] = "failed"
        results["errors"].append(f"{type(e).__name__}: {str(e)}")
        results["traceback"] = traceback.format_exc()
        
    return results
