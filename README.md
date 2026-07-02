# AEGIS-OS: Forensic Command Center & Lemma SDK Platform

AEGIS-OS is an enterprise-grade, AI-powered forensic triage and multi-agent investigation platform designed for law enforcement agencies, cybercrime divisions, and digital forensics teams. 

The platform acts as a central nervous system for complex criminal investigations. By automatically ingesting diverse evidence formats, building structured entity databases, mapping multi-dimensional relationship graphs, and running specialized cognitive agents, AEGIS-OS bridges the gap between raw, unstructured telemetry and actionable, court-ready intelligence.

Built entirely on top of the **Lemma SDK** (v1.0.0), the project showcases a highly structured implementation of autonomous, collaborative LLM agents with deterministic workflow controls and strict human-in-the-loop validation.

---

## 🏛️ System Architecture

The following block illustrates how information flows through the AEGIS-OS / Lemma SDK environment:

```
[Raw Evidence Ingestion] ────► [Cryptographic Hash & Storage] 
(Autopsies, CCTV logs,            │
 GPS logs, Chat transcripts)      ▼
                           [Forensic Parsers / OCR]
                                  │
                                  ▼
┌─────────────────────────── Lemma SDK Core ───────────────────────────┐
│                                                                     │
│  [Investigation Pod]                                                │
│  ├── Datastore (13 Entity Types) ◄───► [Neo4j Relationship Graph]   │
│  ├── Files (Chain of Custody Logs)                                  │
│  └── Workflow Engine (12-Step Durable State Machine)                │
│                                                                     │
│             ▲                                  │                    │
│             │ Run Step                         │ Spawn Agents       │
│             │                                  ▼                    │
│             │                      ┌─────────────────────────────┐  │
│             │                      │ Agent Fleet (8 LLM Agents)  │  │
│             │                      │  - Evidence Intake          │  │
│             └──────────────────────┤  - Autopsy Intel            │  │
│                                    │  - Digital Correlation      │  │
│                                    │  - Timeline Reconstruction  │  │
│                                    │  - Risk Assessment          │  │
│                                    │  - Hypothesis Gen           │  │
│                                    │  - Report Compiler          │  │
│                                    │  - Graph Builder            │  │
│                                    └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        [Human Checkpoint / Gate]
                                  │ (Lead Approval)
                                  ▼
                       [Court Briefing / PDF Report]
```

---

## 📂 Project Directory Structure

```
aiventra/
├── src/                               # Frontend Application (React, Vite, TS)
│   ├── routes/                        # Client-Side Routing (TanStack Router)
│   │   ├── index.tsx                  # Command Dashboard
│   │   ├── evidence-upload.tsx        # Evidence Ingestion Page
│   │   ├── spatial-intelligence.tsx   # Geospatial Mapping & Telemetry
│   │   └── copilot.tsx                # Interactive AI Agent Copilot
│   ├── components/
│   │   └── aegis/                     # Theme components (Sidebar, Shell, StatCards)
│   ├── lib/
│   │   └── lemma/                     # Frontend API bindings to Lemma SDK
│   └── styles.css                     # Global UI Design System & Cyber Theme
│
└── backend/                           # Backend Application (FastAPI, Python)
    ├── main.py                        # API Entrypoint
    ├── auth/                          # Authentication, JWT, and RBAC Engine
    ├── database/                      # DB Clients (Neo4j, Postgres, Chroma)
    ├── routers/                       # FastAPI Route Controllers
    └── lemma/                         # THE LEMMA SDK
        ├── pod.py                     # Case Isolation Unit (InvestigationPod)
        ├── datastore.py               # Structured Entity Datastore
        ├── files.py                   # Secure File & Custody Ledger
        ├── workflows/                 # Investigation Workflow State Machine
        ├── agents/                    # Specialized Cognitive AI Agents
        └── functions/                 # 15 Deterministic Forensic Utilities
```

---

## 🧠 The Lemma SDK Core Concepts

The SDK is organized around four principal abstractions:

### 1. Investigation Pod (`lemma.pod`)
The fundamental unit of containment in Lemma. Every case runs inside its own isolated **Pod**. 
* **State Isolation:** Agents executing in one Pod cannot access or leak data to another.
* **Component Map:** Each Pod holds its metadata, a dedicated file directory, a structured entity datastore, workflow states, and its own local **Agent Memory**.

### 2. Structured Datastore (`lemma.datastore`)
Instead of keeping agent findings in unstructured text blocks, Lemma registers every piece of intelligence into a schema-enforced, 13-category relational model. 
The supported entity types are:
* `persons` (Suspects, Victims, Witnesses)
* `locations` (Crime Scenes, Alibi locations, POIs)
* `vehicles`
* `devices` (Phones, Laptops, IP addresses)
* `events` / `timeline_events`
* `evidence_items`
* `hypotheses`
* `risk_scores`
* `notes`
* `cdr_records` (Call Detail Records)
* `contacts`

### 3. Forensic Functions (`lemma.functions`)
Rather than relying on LLMs to parse telemetry or calculate stats (which causes hallucinations), Lemma utilizes deterministic, pre-compiled Python helper functions that agents execute:
* `parse_autopsy` / `estimate_pmi`: Extracts physical body temperatures and stages of rigor mortis to scientifically calculate the Post-Mortem Interval (PMI).
* `parse_gps`: Parses raw CSV/GPX spatial coordinate streams.
* `extract_entities`: Executes named-entity recognition (NER) over witness statements.
* `reconstruct_movement`: Groups GPS coordinates into logical paths, calculate velocities, and flags potential anomalies.
* `score_risk`: Evaluates suspect profiles against structural threat models.

### 4. Base Agent & Cognitive Fleet (`lemma.agents`)
Every AI Agent inherits from `BaseAgent` and acts as a specialized worker. Agents can invoke backend functions, call the LLM engine, and write their results along with their *reasoning paths* and *tool logs* directly to the Pod's memory log, providing full audibility.

The workflow coordinates **8 agents**:
1. **Evidence Intake Agent:** Formats and processes incoming files.
2. **Autopsy Intelligence Agent:** Computes medical details and TOD.
3. **Digital Correlation Agent:** Connects cell tower registers and chat dumps.
4. **Knowledge Graph Builder:** Updates Neo4j to build semantic relationship networks.
5. **Timeline Reconstruction Agent:** Arranges geographical and digital telemetry sequentially.
6. **Risk Assessment Agent:** Detects flight indicators or escalation levels.
7. **Hypothesis Agent:** Formulates competing scenarios of the crime scene.
8. **Report Agent:** Prepares comprehensive investigative files.

---

## ⏱️ Durable 12-Step Workflow

Investigations in AEGIS-OS follow a strict, durable sequence managed by a persistent state machine in `lemma/workflows/investigation_workflow.py`:

```
[1] pod_created ➔ [2] evidence_uploaded ➔ [3] intake_running ➔ [4] intake_complete ➔
[5] autopsy_analysis ➔ [6] digital_correlation ➔ [7] graph_update ➔ [8] timeline_build ➔
[9] risk_assessment ➔ [10] hypothesis_gen ➔ [11] investigator_review (⚠️ HUMAN GATED) ➔
[12] report_generation ➔ [13] case_closed
```

* **The Human Gate (Step 11):** The pipeline automatically pauses at `investigator_review`. Agents cannot execute the final report generation until an investigator manually hits the **Approve/Resume** trigger (`POST /api/v2/workflows/{pod_id}/approve`).

---

## 🎨 Theme & Frontend Design System

AEGIS-OS implements a **"Dark Cyber Intelligence"** interface. It uses:
* **Background:** Deep rich navy (`#070B17`) with dynamic digital grids.
* **Cards & Layout:** Semi-transparent glassmorphic panels (`#0D1528` with borders `1px solid rgba(0,180,255,.22)`).
* **Typography:** Clean, high-density sans-serif UI fonts.
* **Interactive Accents:** Glow effects, neon green indicators for active statuses, and warning reds (`#FF4D6D`) for high-severity anomalies.
* **Animations:** Smooth page transitions, staggered layout builds, and active SVG loader paths built using Framer Motion.

---

## ⚙️ Quick Start Instructions

### Prerequisites
* Python 3.10+
* Node.js 18+
* Neo4j Database Instance (Local or Cloud Aura DB)

### 1. Configure the Environment
Copy `.env.example` in the root folder to `.env` and fill in your connection details:
```ini
DATABASE_URL=postgresql://user:password@localhost/aegis
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 2. Launch the Backend REST API
Navigate into the `backend` directory, install packages, and spin up the ASGI server:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The API docs will be live at `http://localhost:8000/docs`.*

### 3. Launch the Frontend Dev Server
In the root directory, install dependencies and start the Vite dev client:
```bash
npm install
npm run dev
```
Navigate to `http://localhost:5173` to start investigating.
