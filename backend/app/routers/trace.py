import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player, TraceArtifact
from app.services.graph_service import (
    get_neo4j_driver, get_player_trace_graph,
    calculate_identity_exposure, find_identity_overlaps,
    get_investigation_path, wipe_artifact_from_graph,
)

router = APIRouter(prefix="/trace", tags=["trace"])


@router.get("/graph")
async def trace_graph(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    try:
        driver = get_neo4j_driver()
        graph = await get_player_trace_graph(driver, str(player.id))
        return graph
    except Exception as e:
        result = await db.execute(
            select(TraceArtifact).where(
                TraceArtifact.player_id == player.id,
                TraceArtifact.is_wiped == False,
            )
        )
        artifacts = list(result.scalars().all())
        return {
            "nodes": [
                {
                    "id": str(a.id),
                    "type": "Artifact",
                    "label": a.artifact_type,
                    "properties": {"severity": a.severity},
                    "risk_score": a.severity / 10.0,
                }
                for a in artifacts
            ],
            "edges": [],
            "fallback": True,
        }


@router.get("/identity-overlaps")
async def identity_overlaps(player: Player = Depends(get_current_player)):
    try:
        driver = get_neo4j_driver()
        return await find_identity_overlaps(driver, str(player.id))
    except Exception:
        return []


@router.get("/investigation-path")
async def investigation_path(player: Player = Depends(get_current_player)):
    try:
        driver = get_neo4j_driver()
        return await get_investigation_path(driver, str(player.id))
    except Exception:
        return []


@router.get("/risk-score")
async def risk_score(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TraceArtifact).where(
            TraceArtifact.player_id == player.id,
            TraceArtifact.is_wiped == False,
        )
    )
    artifacts = list(result.scalars().all())
    if not artifacts:
        return {"risk_score": 0.0, "artifact_count": 0, "max_severity": 0}

    total_severity = sum(a.severity for a in artifacts)
    risk = min(1.0, total_severity * 0.01 + len(artifacts) * 0.02)

    return {
        "risk_score": round(risk, 3),
        "artifact_count": len(artifacts),
        "max_severity": max(a.severity for a in artifacts),
    }


@router.post("/wipe")
async def wipe_artifact(
    body: dict,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    artifact_id = body.get("artifact_id")
    if not artifact_id:
        raise HTTPException(status_code=400, detail="artifact_id required")

    try:
        art_uuid = uuid.UUID(str(artifact_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact_id")

    result = await db.execute(
        select(TraceArtifact).where(
            TraceArtifact.id == art_uuid,
            TraceArtifact.player_id == player.id,
        )
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    artifact.is_wiped = True
    await db.commit()

    try:
        driver = get_neo4j_driver()
        await wipe_artifact_from_graph(driver, str(art_uuid))
    except Exception:
        pass

    return {"wiped": True, "artifact_id": str(art_uuid), "message": "Artifact removed from trace graph."}
