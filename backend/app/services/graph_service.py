import uuid
import logging
from datetime import datetime
from neo4j import AsyncGraphDatabase
from app.config import settings

logger = logging.getLogger(__name__)

_driver = None


def get_neo4j_driver():
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


async def init_graph_schema(driver):
    async with driver.session() as session:
        await session.run("CREATE CONSTRAINT player_id IF NOT EXISTS FOR (p:Player) REQUIRE p.player_id IS UNIQUE")
        await session.run("CREATE CONSTRAINT identity_id IF NOT EXISTS FOR (i:Identity) REQUIRE i.identity_id IS UNIQUE")
        await session.run("CREATE CONSTRAINT device_id IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE")
        await session.run("CREATE CONSTRAINT world_node_key IF NOT EXISTS FOR (n:WorldNode) REQUIRE n.node_key IS UNIQUE")
        await session.run("CREATE CONSTRAINT artifact_id IF NOT EXISTS FOR (a:Artifact) REQUIRE a.artifact_id IS UNIQUE")


async def ensure_player_node(driver, player_id: str, handle: str):
    async with driver.session() as session:
        await session.run(
            "MERGE (p:Player {player_id: $player_id}) SET p.handle = $handle",
            player_id=player_id, handle=handle,
        )


async def record_operation_in_graph(driver, operation, artifacts: list):
    async with driver.session() as session:
        player_id = str(operation.player_id)
        device_id = str(operation.device_id)
        node_id = str(operation.node_id)
        op_id = str(operation.id)

        await session.run(
            "MERGE (d:Device {device_id: $device_id}) "
            "SET d.forensic_trace_level = $trace",
            device_id=device_id, trace=0,
        )

        await session.run(
            "MERGE (n:WorldNode {node_key: $node_key}) "
            "SET n.name = $name, n.category = $category, n.tier = $tier",
            node_key=getattr(operation, 'node_key', node_id),
            name=getattr(operation, 'node_name', 'Unknown'),
            category=getattr(operation, 'node_category', 'unknown'),
            tier=getattr(operation, 'node_tier', 1),
        )

        await session.run(
            "MATCH (p:Player {player_id: $pid}), (d:Device {device_id: $did}) "
            "MERGE (p)-[:OPERATES]->(d)",
            pid=player_id, did=device_id,
        )

        await session.run(
            "MATCH (d:Device {device_id: $did}), (n:WorldNode {node_key: $nk}) "
            "MERGE (d)-[:ACCESSED {operation_id: $oid, at: $at}]->(n)",
            did=device_id, nk=getattr(operation, 'node_key', node_id),
            oid=op_id, at=datetime.utcnow().isoformat(),
        )

        if operation.identity_id:
            identity_id = str(operation.identity_id)
            await session.run(
                "MERGE (i:Identity {identity_id: $iid}) SET i.alias = $alias",
                iid=identity_id, alias="unknown",
            )
            await session.run(
                "MATCH (p:Player {player_id: $pid}), (i:Identity {identity_id: $iid}) "
                "MERGE (p)-[:USES]->(i)",
                pid=player_id, iid=identity_id,
            )
            await session.run(
                "MATCH (i:Identity {identity_id: $iid}), (n:WorldNode {node_key: $nk}) "
                "MERGE (i)-[:ACCESSED {operation_id: $oid}]->(n)",
                iid=identity_id, nk=getattr(operation, 'node_key', node_id), oid=op_id,
            )

        for artifact in artifacts:
            artifact_id = str(artifact.id)
            await session.run(
                "MERGE (a:Artifact {artifact_id: $aid}) "
                "SET a.artifact_type = $atype, a.severity = $sev, a.created_at = $cat",
                aid=artifact_id,
                atype=artifact.artifact_type,
                sev=artifact.severity,
                cat=artifact.created_at.isoformat(),
            )

            await session.run(
                "MATCH (a:Artifact {artifact_id: $aid}), (n:WorldNode {node_key: $nk}) "
                "MERGE (a)-[:LEFT_AT]->(n)",
                aid=artifact_id, nk=getattr(operation, 'node_key', node_id),
            )

            await session.run(
                "MATCH (a:Artifact {artifact_id: $aid}), (d:Device {device_id: $did}) "
                "MERGE (a)-[:IMPLICATES {weight: $sev}]->(d)",
                aid=artifact_id, did=device_id, sev=artifact.severity,
            )

            if operation.identity_id:
                await session.run(
                    "MATCH (a:Artifact {artifact_id: $aid}), (i:Identity {identity_id: $iid}) "
                    "MERGE (a)-[:IMPLICATES {weight: $sev}]->(i)",
                    aid=artifact_id, iid=str(operation.identity_id), sev=artifact.severity,
                )


async def get_player_trace_graph(driver, player_id: str) -> dict:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH path = (p:Player {player_id: $pid})-[*1..4]-(n)
            WITH p, collect(DISTINCT n) as neighbors, collect(DISTINCT relationships(path)) as rels
            RETURN p, neighbors, rels
            """,
            pid=player_id,
        )

        nodes = []
        edges = []
        seen_nodes = set()
        seen_edges = set()

        player_node = {
            "id": player_id,
            "type": "Player",
            "label": "YOU",
            "properties": {},
            "risk_score": 0,
        }
        nodes.append(player_node)
        seen_nodes.add(player_id)

        result2 = await session.run(
            """
            MATCH (p:Player {player_id: $pid})-[r]->(n)
            RETURN type(r) as rel_type, n, id(n) as node_id, properties(r) as rel_props
            UNION
            MATCH (p:Player {player_id: $pid})<-[r]-(n)
            RETURN type(r) as rel_type, n, id(n) as node_id, properties(r) as rel_props
            UNION
            MATCH (p:Player {player_id: $pid})-[*2..3]-(n)
            WITH p, n
            MATCH (n)-[r]->(m)
            RETURN type(r) as rel_type, m as n, id(m) as node_id, properties(r) as rel_props
            """,
            pid=player_id,
        )

        records = await result2.data()
        for record in records:
            node = record.get("n", {})
            if not node:
                continue

            node_id = str(record.get("node_id", ""))
            if node_id not in seen_nodes:
                labels = list(node.labels) if hasattr(node, 'labels') else []
                node_type = labels[0] if labels else "Unknown"
                risk = min(10, node.get("severity", 3)) / 10.0 if node_type == "Artifact" else 0.0

                nodes.append({
                    "id": node_id,
                    "type": node_type,
                    "label": node.get("alias") or node.get("name") or node.get("node_key") or node.get("artifact_type") or node_id[:8],
                    "properties": dict(node),
                    "risk_score": risk,
                })
                seen_nodes.add(node_id)

        return {"nodes": nodes, "edges": edges}


async def calculate_identity_exposure(driver, identity_id: str) -> float:
    async with driver.session() as session:
        result = await session.run(
            "MATCH (a:Artifact)-[:IMPLICATES]->(i:Identity {identity_id: $iid}) "
            "RETURN count(a) as artifact_count, sum(a.severity) as total_severity",
            iid=identity_id,
        )
        record = await result.single()
        if not record:
            return 0.0
        count = record["artifact_count"] or 0
        severity = record["total_severity"] or 0
        return min(1.0, (count * 0.05 + severity * 0.01))


async def find_identity_overlaps(driver, player_id: str) -> list[dict]:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Player {player_id: $pid})-[:USES]->(i1:Identity)-[:ACCESSED]->(n:WorldNode)
            MATCH (p)-[:USES]->(i2:Identity)-[:ACCESSED]->(n)
            WHERE i1.identity_id <> i2.identity_id
            RETURN i1.identity_id as id1, i1.alias as alias1,
                   i2.identity_id as id2, i2.alias as alias2,
                   n.node_key as node_key, n.name as node_name
            """,
            pid=player_id,
        )
        records = await result.data()
        return [
            {
                "identity_1": r["id1"],
                "alias_1": r["alias1"],
                "identity_2": r["id2"],
                "alias_2": r["alias2"],
                "shared_node": r["node_key"],
                "node_name": r["node_name"],
                "severity": "CRITICAL",
            }
            for r in records
        ]


async def get_investigation_path(driver, player_id: str) -> list[dict]:
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (p:Player {player_id: $pid})-[*1..5]-(a:Artifact)
            WHERE NOT a.is_wiped = true
            WITH a ORDER BY a.severity DESC LIMIT 1
            MATCH path = shortestPath((p:Player {player_id: $pid})-[*]-(a))
            RETURN [node IN nodes(path) | {
                type: labels(node)[0],
                label: COALESCE(node.handle, node.alias, node.node_key, node.artifact_type, 'unknown'),
                id: COALESCE(node.player_id, node.identity_id, node.device_id, node.node_key, node.artifact_id)
            }] as path_nodes
            """,
            pid=player_id,
        )
        record = await result.single()
        if not record:
            return []
        return record["path_nodes"]


async def wipe_artifact_from_graph(driver, artifact_id: str):
    async with driver.session() as session:
        await session.run(
            "MATCH (a:Artifact {artifact_id: $aid}) "
            "SET a.is_wiped = true "
            "WITH a MATCH (a)-[r:IMPLICATES]->() DELETE r",
            aid=artifact_id,
        )


async def close_driver():
    global _driver
    if _driver:
        await _driver.close()
        _driver = None
