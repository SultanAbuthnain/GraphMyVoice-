"""
app/agents/state.py
────────────────────
The single GraphState TypedDict that flows through every node in the pipeline.
Every node reads from this state and returns a partial dict to update it.
"""

from typing import Any, TypedDict


class TranscriptChunk(TypedDict):
    text: str
    start: float   # seconds from audio start
    end: float


class MindmapNodeDict(TypedDict):
    id: str
    parent_id: str | None
    type: str               # goal | plan | task | topic | note_ref
    label: str
    description: str | None
    position_x: float
    position_y: float
    order_index: int


class MindmapEdgeDict(TypedDict):
    id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str


class GraphState(TypedDict):
    # ── Session context ─────────────────────────────────────────────────────
    session_id: str
    user_id: str
    audio_path: str
    language: str           # "auto" | "ar" | "en" | ...

    # ── Transcription outputs ────────────────────────────────────────────────
    transcript: str         # full stitched transcript
    chunks: list[TranscriptChunk]  # per-chunk with timestamps

    # ── Extraction outputs ───────────────────────────────────────────────────
    extracted_json: dict    # {topic, goals: [{id, title, plans: [...]}]}

    # ── Mindmap outputs ──────────────────────────────────────────────────────
    mindmap_nodes: list[MindmapNodeDict]
    mindmap_edges: list[MindmapEdgeDict]

    # ── Validation ───────────────────────────────────────────────────────────
    validation_flags: list[str]   # human-readable issues found
    validation_score: float        # 0.0–1.0 hallucination coverage

    # ── Control flow ────────────────────────────────────────────────────────
    current_step: str
    error: str | None
    retry_count: int               # tracks extraction retries (max 3)
