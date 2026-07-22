"""
app/services/pipeline_service.py
──────────────────────────────────
Orchestrates the LangGraph pipeline as a FastAPI BackgroundTask.
Updates the session status in the DB as each node completes.
"""

import structlog
from sqlalchemy import update

from app.agents.graph import graph
from app.agents.state import GraphState
from app.database import AsyncSessionLocal
from app.models.session import Session

logger = structlog.get_logger()

# Map LangGraph node names → (status, progress_percent)
NODE_PROGRESS: dict[str, tuple[str, int]] = {
    "ingestion":       ("queued",          5),
    "transcription":   ("transcribing",    15),
    "guardrail_pre":   ("transcribing",    40),
    "extraction":      ("extracting",      55),
    "mindmap_builder": ("building_mindmap",75),
    "guardrail_post":  ("validating",      88),
    "persistence":     ("saving",          95),
}


async def _update_session_status(
    session_id: str,
    status: str,
    progress: int,
    current_step: str,
    error_json: dict | None = None,
):
    """Update session row in DB with current pipeline progress."""
    async with AsyncSessionLocal() as db:
        values = {
            "status": status,
            "progress_percent": progress,
            "current_step": current_step,
        }
        if error_json:
            values["error_json"] = error_json
        await db.execute(
            update(Session).where(Session.id == session_id).values(**values)
        )
        await db.commit()


async def run_pipeline(
    session_id: str,
    audio_path: str,
    user_id: str,
    language: str = "auto",
) -> None:
    """
    Run the full LangGraph pipeline for a session.
    Called as a FastAPI BackgroundTask — does NOT block the HTTP response.
    """
    log = logger.bind(session_id=session_id)
    log.info("Pipeline started", audio_path=audio_path)

    initial_state = GraphState(
        session_id=session_id,
        user_id=user_id,
        audio_path=audio_path,
        language=language,
        transcript="",
        chunks=[],
        extracted_json={},
        mindmap_nodes=[],
        mindmap_edges=[],
        validation_flags=[],
        validation_score=0.0,
        current_step="ingestion",
        error=None,
        retry_count=0,
    )

    try:
        # Stream events from LangGraph — one event per node completion
        async for event in graph.astream(initial_state, stream_mode="updates"):
            node_name = list(event.keys())[0]
            node_state = event[node_name]

            status, progress = NODE_PROGRESS.get(node_name, ("processing", 50))
            current_step = node_state.get("current_step", node_name)
            error = node_state.get("error")

            if error:
                log.error("Pipeline node failed", node=node_name, error=error)
                await _update_session_status(
                    session_id,
                    status="failed",
                    progress=progress,
                    current_step=current_step,
                    error_json={
                        "code": f"{node_name}_failed",
                        "message": error,
                        "retryable": True,
                    },
                )
                return

            await _update_session_status(
                session_id, status, progress, current_step
            )
            log.info("Node complete", node=node_name, progress=progress)

        log.info("Pipeline complete", session_id=session_id)

    except Exception as exc:
        log.error("Pipeline crashed", error=str(exc))
        await _update_session_status(
            session_id,
            status="failed",
            progress=0,
            current_step="unknown",
            error_json={"code": "pipeline_crash", "message": str(exc), "retryable": False},
        )
