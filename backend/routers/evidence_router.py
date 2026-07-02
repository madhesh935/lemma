"""
AEGIS-OS Evidence Router — File upload and management for Investigation Pods.
"""
import uuid
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from fastapi.responses import FileResponse

from lemma.files import PodFiles
from auth.jwt_handler import get_current_user
from auth.rbac import require_investigator
from lemma.functions.notifier import send_notification

router = APIRouter(prefix="/pods/{pod_id}/files", tags=["Evidence Files"])

# Per-pod file managers
_FILE_MANAGERS: Dict[str, PodFiles] = {}


def _get_file_manager(pod_id: str) -> PodFiles:
    if pod_id not in _FILE_MANAGERS:
        _FILE_MANAGERS[pod_id] = PodFiles(pod_id)
    return _FILE_MANAGERS[pod_id]


@router.post("", status_code=201)
async def upload_evidence_files(
    pod_id: str,
    files: List[UploadFile] = File(...),
    current_user: Dict = Depends(require_investigator),
):
    """Upload one or more evidence files to a pod."""
    manager = _get_file_manager(pod_id)
    uploaded = []
    errors = []

    for upload_file in files:
        try:
            content = await upload_file.read()
            record = await manager.upload(
                file_content=content,
                original_name=upload_file.filename or "unknown",
                mime_type=upload_file.content_type,
                uploaded_by=current_user.get("email"),
            )
            uploaded.append(record.to_dict())

            send_notification(
                "evidence_uploaded", f"Evidence Uploaded: {upload_file.filename}",
                f"Type: {record.evidence_type} | Size: {record.file_size:,} bytes",
                pod_id=pod_id, severity="info"
            )
        except Exception as e:
            errors.append({"file": upload_file.filename, "error": str(e)})

    return {
        "uploaded": uploaded,
        "errors": errors,
        "total_uploaded": len(uploaded),
    }


@router.get("")
async def list_evidence_files(pod_id: str, current_user: Dict = Depends(get_current_user)):
    """List all evidence files for a pod."""
    manager = _get_file_manager(pod_id)
    files = manager.list()
    return {
        "files": [f.to_dict() for f in files],
        "stats": manager.stats(),
    }


@router.get("/{file_id}")
async def get_evidence_file(
    pod_id: str,
    file_id: str,
    current_user: Dict = Depends(get_current_user),
):
    """Get metadata for a specific evidence file."""
    manager = _get_file_manager(pod_id)
    record = manager.get(file_id)
    if not record:
        raise HTTPException(404, f"File {file_id} not found in pod {pod_id}.")
    return record.to_dict()


@router.get("/{file_id}/download")
async def download_evidence_file(
    pod_id: str,
    file_id: str,
    current_user: Dict = Depends(get_current_user),
):
    """Download an evidence file (with chain-of-custody logging)."""
    manager = _get_file_manager(pod_id)
    record = manager.get(file_id)
    if not record:
        raise HTTPException(404, f"File {file_id} not found.")
    record.add_custody_entry("downloaded", user_id=current_user.get("sub"))
    return FileResponse(
        path=record.stored_path,
        filename=record.original_name,
        media_type=record.mime_type,
    )


@router.delete("/{file_id}")
async def delete_evidence_file(
    pod_id: str,
    file_id: str,
    current_user: Dict = Depends(require_investigator),
):
    """Delete an evidence file (lead investigator+ only)."""
    manager = _get_file_manager(pod_id)
    deleted = manager.delete(file_id, user_id=current_user.get("sub"))
    if not deleted:
        raise HTTPException(404, f"File {file_id} not found.")
    return {"message": "File deleted.", "file_id": file_id}
