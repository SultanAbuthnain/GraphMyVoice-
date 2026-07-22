"""
app/agents/nodes/mindmap_builder.py
─────────────────────────────────────
Node 5: Mindmap Builder
Converts the extracted goals/plans/tasks JSON into nodes[] + edges[]
format that React Flow / Markmap can render directly.
Also maps transcript chunks to source_ref timestamps for each node.
"""

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
    edge_counter = 0

    # ── Root node ─────────────────────────────────────────────────────────────
    topic = extracted.get("topic", "Untitled")
    root_id = "node_root"
    nodes.append(
        MindmapNodeDict(
            id=root_id,
            parent_id=None,
            label=topic,
            node_type="root",
            order_index=0,
            source_ref=None,
        )
    )

    # ── Goals ─────────────────────────────────────────────────────────────────
    for g_idx, goal in enumerate(extracted.get("goals", [])):
        goal_node_id = f"node_{goal['id']}"
        keywords = goal["title"].split()
        nodes.append(
            MindmapNodeDict(
                id=goal_node_id,
                parent_id=root_id,
                label=goal["title"],
                node_type="goal",
                order_index=g_idx,
                source_ref=_find_source_ref(keywords, chunks),
            )
        )
        edge_counter += 1
        edges.append(MindmapEdgeDict(id=f"e{edge_counter}", source=root_id, target=goal_node_id))

        # ── Plans ─────────────────────────────────────────────────────────────
        for p_idx, plan in enumerate(goal.get("plans", [])):
            plan_node_id = f"node_{plan['id']}"
            keywords = plan["title"].split()
            nodes.append(
                MindmapNodeDict(
                    id=plan_node_id,
                    parent_id=goal_node_id,
                    label=plan["title"],
                    node_type="plan",
                    order_index=p_idx,
                    source_ref=_find_source_ref(keywords, chunks),
                )
            )
            edge_counter += 1
            edges.append(MindmapEdgeDict(id=f"e{edge_counter}", source=goal_node_id, target=plan_node_id))

            # ── Tasks ──────────────────────────────────────────────────────────
            for t_idx, task in enumerate(plan.get("tasks", [])):
                task_node_id = f"node_{task['id']}"
                keywords = task["title"].split()
                nodes.append(
                    MindmapNodeDict(
                        id=task_node_id,
                        parent_id=plan_node_id,
                        label=task["title"],
                        node_type="task",
                        order_index=t_idx,
                        source_ref=_find_source_ref(keywords, chunks),
                    )
                )
                edge_counter += 1
                edges.append(MindmapEdgeDict(id=f"e{edge_counter}", source=plan_node_id, target=task_node_id))

    log.info("Mindmap built", nodes=len(nodes), edges=len(edges))
    return {
        "mindmap_nodes": nodes,
        "mindmap_edges": edges,
        "current_step": "validating",
        "error": None,
    }
