"""
app/agents/nodes/mindmap_builder.py
─────────────────────────────────────
Node 5: Mindmap Builder
Converts the extracted goals/plans/tasks JSON into nodes[] + edges[]
format that React Flow / Markmap can render directly.
Also maps transcript chunks to source_ref timestamps for each node.
"""

import uuid
import structlog
from app.agents.state import GraphState, MindmapNodeDict, MindmapEdgeDict

logger = structlog.get_logger()


def _find_source_ref(keywords: list[str], chunks: list[dict]) -> dict | None:
    """
    Find the transcript chunk(s) that best match a node's title keywords.
    Returns {timestamp_start, timestamp_end} or None.
    """
    if not chunks or not keywords:
        return None

    best_chunk = None
    best_score = 0

    for chunk in chunks:
        text_lower = chunk["text"].lower()
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > best_score:
            best_score = score
            best_chunk = chunk

    if best_chunk and best_score > 0:
        def fmt(secs: float) -> str:
            m, s = divmod(int(secs), 60)
            h, m = divmod(m, 60)
            return f"{h:02d}:{m:02d}:{s:02d}"

        return {
            "timestamp_start": fmt(best_chunk["start"]),
            "timestamp_end": fmt(best_chunk["end"]),
        }
    return None


async def mindmap_builder_node(state: GraphState) -> dict:
    """
    LangGraph node: transform extracted_json → nodes[] + edges[].
    """
    log = logger.bind(session_id=state["session_id"], node="mindmap_builder")
    log.info("Building mindmap nodes and edges")

    extracted = state.get("extracted_json", {})
    chunks = state.get("chunks", [])

    nodes: list[MindmapNodeDict] = []
    edges: list[MindmapEdgeDict] = []

    # ── Root node ─────────────────────────────────────────────────────────────
    topic = extracted.get("topic", "Untitled")
    root_id = str(uuid.uuid4())
    nodes.append(
        MindmapNodeDict(
            id=root_id,
            parent_id=None,
            type="topic",
            label=topic,
            description="Main Topic extracted from audio",
            position_x=0.0,
            position_y=0.0,
            order_index=0,
        )
    )

    y_offset = 100

    # ── Goals ─────────────────────────────────────────────────────────────────
    for g_idx, goal in enumerate(extracted.get("goals", [])):
        goal_node_id = str(uuid.uuid4())
        nodes.append(
            MindmapNodeDict(
                id=goal_node_id,
                parent_id=root_id,
                type="goal",
                label=goal["title"],
                description=None,
                position_x=float(g_idx * 250),
                position_y=float(y_offset),
                order_index=g_idx,
            )
        )
        edges.append(MindmapEdgeDict(
            id=str(uuid.uuid4()), 
            source_node_id=root_id, 
            target_node_id=goal_node_id, 
            relationship_type="has_goal"
        ))

        # ── Plans ─────────────────────────────────────────────────────────────
        for p_idx, plan in enumerate(goal.get("plans", [])):
            plan_node_id = str(uuid.uuid4())
            nodes.append(
                MindmapNodeDict(
                    id=plan_node_id,
                    parent_id=goal_node_id,
                    type="plan",
                    label=plan["title"],
                    description=None,
                    position_x=float(g_idx * 250 + p_idx * 150),
                    position_y=float(y_offset + 100),
                    order_index=p_idx,
                )
            )
            edges.append(MindmapEdgeDict(
                id=str(uuid.uuid4()), 
                source_node_id=goal_node_id, 
                target_node_id=plan_node_id, 
                relationship_type="has_plan"
            ))

            # ── Tasks ──────────────────────────────────────────────────────────
            for t_idx, task in enumerate(plan.get("tasks", [])):
                task_node_id = str(uuid.uuid4())
                nodes.append(
                    MindmapNodeDict(
                        id=task_node_id,
                        parent_id=plan_node_id,
                        type="task",
                        label=task["title"],
                        description=None,
                        position_x=float(g_idx * 250 + p_idx * 150),
                        position_y=float(y_offset + 200 + t_idx * 60),
                        order_index=t_idx,
                    )
                )
                edges.append(MindmapEdgeDict(
                    id=str(uuid.uuid4()), 
                    source_node_id=plan_node_id, 
                    target_node_id=task_node_id, 
                    relationship_type="has_task"
                ))

    log.info("Mindmap built", nodes=len(nodes), edges=len(edges))
    return {
        "mindmap_nodes": nodes,
        "mindmap_edges": edges,
        "current_step": "validating",
        "error": None,
    }
