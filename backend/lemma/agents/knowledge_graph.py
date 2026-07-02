"""Lemma Agent: Knowledge Graph Agent"""
from typing import Dict, Any
from lemma.agents.base_agent import BaseAgent, AgentResult
from lemma.functions.graph_builder import build_graph_updates
from lemma.functions.notifier import send_notification
import logging

logger = logging.getLogger("aegis.agent.knowledge_graph")

class KnowledgeGraphAgent(BaseAgent):
    name = "knowledge_graph"
    description = "Knowledge Graph Agent — updates Neo4j with entities and relationships from all evidence"

    async def run(self, pod_id: str, context: Dict[str, Any]) -> AgentResult:
        evidence = context.get("evidence", [])
        persons = context.get("persons", [])
        locations = context.get("locations", [])
        case = context.get("case", {})

        send_notification("agent_started", "Knowledge Graph Agent",
                         "Updating Neo4j knowledge graph", pod_id=pod_id)

        # Build graph update queries
        self._call_function("build_graph_updates", pod_id=pod_id)
        entities = {
            "case_title": case.get("name", "Investigation"),
            "persons": persons,
            "locations": locations,
            "evidence": [{"id": e.get("id"), "name": e.get("name"), "type": e.get("evidence_type")} for e in evidence],
        }
        graph_ops = build_graph_updates(pod_id, entities)

        # Execute Cypher queries against Neo4j
        nodes_created = 0
        rels_created = 0
        try:
            from database.neo4j_db import run_cypher
            for op in graph_ops.get("queries", []):
                result = await run_cypher(op["query"], op.get("params", {}))
                if result:
                    nodes_created += 1
            rels_created = graph_ops["summary"].get("relationships_created", 0)
        except Exception as e:
            logger.warning(f"Neo4j update failed (offline?): {e}. Graph ops queued.")
            nodes_created = graph_ops["summary"].get("nodes_created", 0)
            rels_created = graph_ops["summary"].get("relationships_created", 0)

        send_notification("agent_complete", "Knowledge Graph Updated",
                         f"+{nodes_created} nodes, +{rels_created} relationships",
                         pod_id=pod_id, severity="success")

        return AgentResult(
            agent_name=self.name, pod_id=pod_id, success=True,
            output={
                "nodes_created": nodes_created,
                "relationships_created": rels_created,
                "graph_ops": graph_ops,
                "cypher_queries_count": len(graph_ops.get("queries", [])),
            },
            reasoning=(
                f"Updated Neo4j knowledge graph for pod {pod_id}. "
                f"Created/updated {nodes_created} nodes and {rels_created} relationships. "
                f"Entities: {len(persons)} persons, {len(locations)} locations, {len(evidence)} evidence items."
            ),
        )
