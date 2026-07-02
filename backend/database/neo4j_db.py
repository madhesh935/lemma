"""
AEGIS-OS Neo4j Connection Manager.
Handles the knowledge graph for relationships between entities.
"""
from typing import Optional, List, Dict, Any
import logging

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE

logger = logging.getLogger("aegis.neo4j")

# Lazy import — neo4j is optional
try:
    from neo4j import AsyncGraphDatabase, AsyncDriver
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logger.warning("neo4j package not installed. Graph features disabled.")

_driver: Optional[Any] = None


async def get_neo4j_driver():
    """Get or create the Neo4j async driver."""
    global _driver
    if not NEO4J_AVAILABLE:
        return None
    if _driver is None:
        try:
            _driver = AsyncGraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
            )
            await _driver.verify_connectivity()
            logger.info(f"Neo4j connected to {NEO4J_URI}")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}. Graph features disabled.")
            _driver = None
    return _driver


async def close_neo4j():
    """Close Neo4j driver on shutdown."""
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


async def run_cypher(query: str, params: Dict[str, Any] = None) -> List[Dict]:
    """Execute a Cypher query and return all records as dicts."""
    driver = await get_neo4j_driver()
    if not driver:
        return []
    params = params or {}
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(query, params)
        records = await result.data()
        return records


async def init_neo4j_schema():
    """Create constraints and indexes for the knowledge graph."""
    constraints = [
        "CREATE CONSTRAINT case_id IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT person_id IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT evidence_id IF NOT EXISTS FOR (e:Evidence) REQUIRE e.id IS UNIQUE",
        "CREATE CONSTRAINT location_id IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT vehicle_id IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE",
        "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (ev:Event) REQUIRE ev.id IS UNIQUE",
    ]
    for q in constraints:
        try:
            await run_cypher(q)
        except Exception:
            pass  # Already exists
    logger.info("Neo4j schema initialized.")


# ─── Graph Operations ─────────────────────────────────────────────────────────

async def upsert_case_node(pod_id: str, title: str, status: str) -> bool:
    """Create or update a Case node."""
    q = """
    MERGE (c:Case {id: $id})
    SET c.title = $title, c.status = $status
    RETURN c.id AS id
    """
    result = await run_cypher(q, {"id": pod_id, "title": title, "status": status})
    return len(result) > 0


async def upsert_person_node(
    person_id: str, pod_id: str, name: str, role: str, risk_level: str = "unknown"
) -> bool:
    q = """
    MERGE (p:Person {id: $id})
    SET p.name = $name, p.role = $role, p.riskLevel = $risk_level
    WITH p
    MATCH (c:Case {id: $pod_id})
    MERGE (p)-[:LINKED_TO {confidence: 0.8}]->(c)
    RETURN p.id AS id
    """
    result = await run_cypher(q, {
        "id": person_id, "pod_id": pod_id, "name": name,
        "role": role, "risk_level": risk_level
    })
    return len(result) > 0


async def upsert_evidence_node(
    evidence_id: str, pod_id: str, name: str, ev_type: str
) -> bool:
    q = """
    MERGE (e:Evidence {id: $id})
    SET e.name = $name, e.type = $type
    WITH e
    MATCH (c:Case {id: $pod_id})
    MERGE (e)-[:BELONGS_TO]->(c)
    RETURN e.id AS id
    """
    result = await run_cypher(q, {
        "id": evidence_id, "pod_id": pod_id, "name": name, "type": ev_type
    })
    return len(result) > 0


async def link_person_to_evidence(person_id: str, evidence_id: str) -> bool:
    q = """
    MATCH (p:Person {id: $person_id})
    MATCH (e:Evidence {id: $evidence_id})
    MERGE (p)-[:IDENTIFIED_IN]->(e)
    RETURN p.id AS id
    """
    result = await run_cypher(q, {"person_id": person_id, "evidence_id": evidence_id})
    return len(result) > 0


async def upsert_location_node(
    location_id: str, name: str, lat: float, lng: float
) -> bool:
    q = """
    MERGE (l:Location {id: $id})
    SET l.name = $name, l.lat = $lat, l.lng = $lng
    RETURN l.id AS id
    """
    result = await run_cypher(q, {"id": location_id, "name": name, "lat": lat, "lng": lng})
    return len(result) > 0


async def link_person_to_location(
    person_id: str, location_id: str, timestamp: str
) -> bool:
    q = """
    MATCH (p:Person {id: $person_id})
    MATCH (l:Location {id: $location_id})
    MERGE (p)-[r:PRESENT_AT {timestamp: $timestamp}]->(l)
    RETURN p.id AS id
    """
    result = await run_cypher(q, {
        "person_id": person_id, "location_id": location_id, "timestamp": timestamp
    })
    return len(result) > 0


async def get_case_graph(pod_id: str) -> Dict[str, Any]:
    """Return all nodes and relationships for a case graph."""
    q = """
    MATCH (c:Case {id: $pod_id})
    OPTIONAL MATCH (c)<-[:BELONGS_TO]-(e:Evidence)
    OPTIONAL MATCH (c)<-[:LINKED_TO]-(p:Person)
    OPTIONAL MATCH (p)-[r:PRESENT_AT]->(l:Location)
    OPTIONAL MATCH (p)-[contact:CONTACTED]->(p2:Person)
    RETURN
      collect(DISTINCT {id: c.id, label: c.title, type: 'case'}) AS cases,
      collect(DISTINCT {id: e.id, label: e.name, type: 'evidence', evType: e.type}) AS evidence,
      collect(DISTINCT {id: p.id, label: p.name, type: 'person', role: p.role}) AS persons,
      collect(DISTINCT {id: l.id, label: l.name, type: 'location', lat: l.lat, lng: l.lng}) AS locations
    """
    result = await run_cypher(q, {"pod_id": pod_id})
    if not result:
        return {"nodes": [], "edges": []}
    row = result[0]
    nodes = []
    for category in ["cases", "evidence", "persons", "locations"]:
        for item in (row.get(category) or []):
            if item and item.get("id"):
                nodes.append(item)
    return {"nodes": nodes, "edges": []}
