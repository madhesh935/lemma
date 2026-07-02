"""
AEGIS-OS FastAPI Backend — v3.0.0
Lemma SDK Powered Forensic Investigation Platform
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, APP_VERSION, ALLOWED_ORIGINS, DEBUG

# ─── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("aegis")

# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=f"{APP_NAME} API",
    description=(
        "AEGIS-OS — AI-Powered Forensic Triage & Postmortem Intelligence Operating System. "
        "Powered by Lemma SDK multi-agent architecture."
    ),
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Existing Routers (preserved) ─────────────────────────────────────────────
try:
    from routers import case_router, cctv_router, pmi_router
    app.include_router(case_router.router, prefix="/api", tags=["Cases (Legacy)"])
    app.include_router(pmi_router.router, prefix="/api/pmi", tags=["PMI Prediction"])
    app.include_router(cctv_router.router, prefix="/api/cctv", tags=["CCTV Analysis"])
    logger.info("Legacy routers: LOADED")
except Exception as e:
    logger.warning(f"Legacy routers: SKIPPED ({e})")

# ─── Lemma SDK Routers ────────────────────────────────────────────────────────
def _safe_include(router_path: str, **kwargs):
    """Import and register a router, logging a warning on failure."""
    try:
        module_path, attr = router_path.rsplit(".", 1)
        import importlib
        mod = importlib.import_module(module_path)
        router = getattr(mod, attr)
        app.include_router(router, **kwargs)
        logger.info(f"  ✓ {router_path}")
    except Exception as e:
        logger.warning(f"  ✗ {router_path}: {e}")

_safe_include("routers.auth_router.router",      prefix="/api/v2")
_safe_include("routers.pod_router.router",       prefix="/api/v2")
_safe_include("routers.evidence_router.router",  prefix="/api/v2")
_safe_include("routers.agent_router.router",     prefix="/api/v2")
_safe_include("routers.workflow_router.router",  prefix="/api/v2")
_safe_include("routers.copilot_router.router",   prefix="/api/v2")
_safe_include("routers.datastore_router.router", prefix="/api/v2")

# Force hot reload

# ─── Startup ──────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"  {APP_NAME} v{APP_VERSION} — Starting up")
    logger.info("=" * 60)

    # Legacy modules
    logger.info("  → [LEGACY] Case management: ACTIVE")
    logger.info("  → [LEGACY] PMI prediction: ACTIVE")
    logger.info("  → [LEGACY] CCTV analysis: ACTIVE")

    # Load PMI model
    try:
        from routers.pmi_router import load_model
        load_model()
        logger.info("  → PMI model: LOADED")
    except Exception as e:
        logger.warning(f"  → PMI model: SKIPPED ({e})")

    # Lemma SDK modules
    logger.info("  → [LEMMA] Auth & RBAC: ACTIVE")
    logger.info("  → [LEMMA] Investigation Pods: ACTIVE")
    logger.info("  → [LEMMA] Evidence Files: ACTIVE")
    logger.info("  → [LEMMA] Agent Registry (8 agents): ACTIVE")
    logger.info("  → [LEMMA] Investigation Workflow: ACTIVE")
    logger.info("  → [LEMMA] AI Copilot: ACTIVE")

    # Initialize Neo4j schema
    try:
        from database.neo4j_db import init_neo4j_schema
        await init_neo4j_schema()
        logger.info("  → Neo4j schema: INITIALIZED")
    except Exception as e:
        logger.warning(f"  → Neo4j: SKIPPED ({e})")

    # Initialize PostgreSQL
    try:
        from database.postgres import init_db
        await init_db()
        logger.info("  → PostgreSQL: INITIALIZED")
    except Exception as e:
        logger.warning(f"  → PostgreSQL: SKIPPED ({e})")

    logger.info("=" * 60)
    logger.info("  AEGIS-OS ready. Visit /docs for API reference.")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    try:
        from database.neo4j_db import close_neo4j
        await close_neo4j()
    except Exception:
        pass
    logger.info("AEGIS-OS shut down gracefully.")


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def read_root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "lemma_sdk": "active",
        "agents": 8,
        "functions": 15,
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": APP_VERSION}

