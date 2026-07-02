"""Lemma Function: Knowledge Graph Builder — generates Neo4j Cypher updates."""
from typing import List, Dict, Any
import logging
logger = logging.getLogger("aegis.fn.graph")

def build_graph_updates(pod_id: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert extracted entities into Neo4j upsert operations.
    Returns Cypher queries and a summary of what would be created.
    """
    queries = []
    summary = {"nodes_created": 0, "relationships_created": 0}
    
    # Case node
    queries.append({
        "query": "MERGE (c:Case {id:$id}) SET c.title=$title, c.status='active' RETURN c",
        "params": {"id": pod_id, "title": entities.get("case_title", "Investigation")}
    })
    summary["nodes_created"] += 1

    # Person nodes
    for p in (entities.get("persons") or []):
        pid = p.get("id") or f"{pod_id}_person_{p['name'].replace(' ','_')}"
        queries.append({
            "query": """MERGE (p:Person {id:$id}) SET p.name=$name, p.role=$role
                        WITH p MATCH (c:Case {id:$pod_id}) MERGE (p)-[:LINKED_TO]->(c)""",
            "params": {"id": pid, "name": p.get("name",""), "role": p.get("role","unknown"), "pod_id": pod_id}
        })
        summary["nodes_created"] += 1; summary["relationships_created"] += 1

    # Location nodes
    for loc in (entities.get("locations") or []):
        lid = f"{pod_id}_loc_{loc.get('name','?').replace(' ','_')}"
        queries.append({
            "query": "MERGE (l:Location {id:$id}) SET l.name=$name, l.lat=$lat, l.lng=$lng",
            "params": {"id": lid, "name": loc.get("name",""), "lat": loc.get("lat",0.0), "lng": loc.get("lng",0.0)}
        })
        summary["nodes_created"] += 1

    # Evidence nodes
    for ev in (entities.get("evidence") or []):
        queries.append({
            "query": """MERGE (e:Evidence {id:$id}) SET e.name=$name, e.type=$type
                        WITH e MATCH (c:Case {id:$pod_id}) MERGE (e)-[:BELONGS_TO]->(c)""",
            "params": {"id": ev.get("id",""), "name": ev.get("name",""), "type": ev.get("type",""), "pod_id": pod_id}
        })
        summary["nodes_created"] += 1; summary["relationships_created"] += 1

    return {"queries": queries, "summary": summary}
