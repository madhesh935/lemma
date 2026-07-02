import asyncio
import time
from fastapi import APIRouter

# We will lazily import app to avoid circular imports if possible
# But actually, we can just do the workflow logic internally, OR use HTTPX async client.
# A simpler approach: we just programmatically call the router functions or do the workflow directly.
# Let's create an async verification route.
from typing import Dict, Any
from lemma.files import PodFiles
from lemma.workflows.investigation_workflow import InvestigationWorkflow

router = APIRouter(prefix="/test", tags=["E2E Test Runner"])

@router.get("/e2e-verify")
async def verify_e2e_pipeline():
    results = {
        "status": "started",
        "stages_passed": [],
        "errors": [],
        "details": {}
    }
    
    try:
        pod_id = "E2E-TEST-POD"
        
        # 1. Test File Upload (Mocking the Evidence Router)
        results["stages_passed"].append("1_init")
        
        manager = PodFiles(pod_id)
        mock_pdf_content = b"%PDF-1.4 mock autopsy report content..."
        
        # Programmatically upload
        record = await manager.upload(
            file_content=mock_pdf_content,
            original_name="mock_autopsy.pdf",
            mime_type="application/pdf",
            uploaded_by="test@aegis.gov"
        )
        results["stages_passed"].append("2_file_uploaded")
        results["details"]["upload"] = record.to_dict()
        
        # 2. Test Workflow Execution
        workflow = InvestigationWorkflow(pod_id=pod_id)
        
        # Instead of an empty context, we pass the uploaded evidence
        context = {
            "evidence_files": [
                {
                    "id": record.file_id, 
                    "type": record.evidence_type, 
                    "name": record.original_name
                }
            ]
        }
        
        state = await asyncio.wait_for(workflow.start(context), timeout=20.0)
        results["stages_passed"].append("3_workflow_executed")
        results["details"]["final_state"] = state
        
        # 3. Verify Final State
        if state.get("current_step") == "investigator_review":
            results["status"] = "success"
        else:
            results["status"] = "partial"
            results["errors"].append(f"Workflow stopped at unexpected step: {state.get('current_step')}")
            
    except Exception as e:
        results["status"] = "failed"
        import traceback
        results["errors"].append(f"{type(e).__name__}: {str(e)}")
        results["details"]["traceback"] = traceback.format_exc()
        
    return results
