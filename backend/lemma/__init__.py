"""
AEGIS-OS Lemma SDK
===================
A Lemma-architecture-compatible orchestration layer for forensic investigation.

Lemma Concepts implemented:
  - Pod:       InvestigationPod — isolated workspace per case
  - Datastore: Structured entity storage
  - Files:     Evidence file management
  - Functions: 15 reusable, callable forensic functions
  - Agents:    8 specialized AI agents
  - Workflow:  12-step investigation workflow with human checkpoints
"""
from lemma.pod import InvestigationPod, PodManager
from lemma.datastore import PodDatastore
from lemma.files import PodFiles, FileRecord

__all__ = [
    "InvestigationPod", "PodManager",
    "PodDatastore", "PodFiles", "FileRecord",
]

# ─── SDK Version ──────────────────────────────────────────────────────────────
LEMMA_SDK_VERSION = "1.0.0"
AEGIS_OS_VERSION = "3.0.0"
