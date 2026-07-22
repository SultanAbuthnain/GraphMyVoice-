"""
app/api/v1/mindmap.py
──────────────────────
Endpoint:
  GET /sessions/{id}/mindmap  → return full mind map JSON
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import UserPayload, get_current_user, get_db

router = APIRouter()


@router.get("/{session_id}/mindmap", status_code=status.HTTP_200_OK)
async def get_mindmap(
    session_id: str,
    current_user: UserPayload = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Return the complete mind map for a session, including:
    - extracted goals/plans/tasks hierarchy
    - nodes and edges ready for React Flow / Markmap
    - per-node notes and task status
    - summary stats
    """
    # TODO: query mindmap_nodes, tasks, notes tables for real data
    # Full mock response matching api-contract.md §3 exactly
    return {
        "session_id": session_id,
        "title": "محاضرة البرمجة - الأسبوع الأول",
        "topic": "مقدمة في بناء AI Agents باستخدام LangGraph",
        "generated_at": "2026-07-22T21:05:00Z",
        "transcript_preview": "في هذه المحاضرة سنتعلم كيفية بناء وكلاء ذكاء اصطناعي متقدمة باستخدام LangGraph...",

        "extracted": {
            "goals": [
                {
                    "id": "g1",
                    "title": "فهم مفهوم AI Agents",
                    "plans": [
                        {
                            "id": "p1",
                            "title": "دراسة أنماط الـ Agent الأساسية",
                            "tasks": [
                                {"id": "t1", "title": "قراءة مقال ReAct Pattern",    "owner": None,       "due": None},
                                {"id": "t2", "title": "تطبيق مثال Tool Calling",     "owner": "الطالب",   "due": "2026-07-25"},
                            ],
                        },
                        {
                            "id": "p2",
                            "title": "استكشاف LangGraph State Graphs",
                            "tasks": [
                                {"id": "t3", "title": "بناء graph بسيط بـ 3 nodes", "owner": None, "due": "2026-07-28"},
                            ],
                        },
                    ],
                },
                {
                    "id": "g2",
                    "title": "تطبيق Guardrails على مستوى الإنتاج",
                    "plans": [
                        {
                            "id": "p3",
                            "title": "تصميم validation logic",
                            "tasks": [
                                {"id": "t4", "title": "كتابة JSON schema validator", "owner": None, "due": None},
                            ],
                        }
                    ],
                },
            ]
        },

        "nodes": [
            {
                "id": "node_root",
                "parent_id": None,
                "label": "مقدمة في بناء AI Agents باستخدام LangGraph",
                "type": "root",
                "order_index": 0,
                "source_ref": None,
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_g1",
                "parent_id": "node_root",
                "label": "فهم مفهوم AI Agents",
                "type": "goal",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:01:30", "timestamp_end": "00:02:45"},
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_p1",
                "parent_id": "node_g1",
                "label": "دراسة أنماط الـ Agent الأساسية",
                "type": "plan",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:02:45", "timestamp_end": "00:05:00"},
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_p2",
                "parent_id": "node_g1",
                "label": "استكشاف LangGraph State Graphs",
                "type": "plan",
                "order_index": 1,
                "source_ref": {"timestamp_start": "00:05:00", "timestamp_end": "00:09:00"},
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_g2",
                "parent_id": "node_root",
                "label": "تطبيق Guardrails على مستوى الإنتاج",
                "type": "goal",
                "order_index": 1,
                "source_ref": {"timestamp_start": "00:10:00", "timestamp_end": "00:12:00"},
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_p3",
                "parent_id": "node_g2",
                "label": "تصميم validation logic",
                "type": "plan",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:11:00", "timestamp_end": "00:12:30"},
                "note": None,
                "task_status": None,
            },
            {
                "id": "node_t1",
                "parent_id": "node_p1",
                "label": "قراءة مقال ReAct Pattern",
                "type": "task",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:03:10", "timestamp_end": "00:03:45"},
                "note": None,
                "task_status": {"is_checked": False, "due_date": None, "owner": None},
            },
            {
                "id": "node_t2",
                "parent_id": "node_p1",
                "label": "تطبيق مثال Tool Calling",
                "type": "task",
                "order_index": 1,
                "source_ref": {"timestamp_start": "00:04:00", "timestamp_end": "00:04:30"},
                "note": None,
                "task_status": {"is_checked": False, "due_date": "2026-07-25", "owner": "الطالب"},
            },
            {
                "id": "node_t3",
                "parent_id": "node_p2",
                "label": "بناء graph بسيط بـ 3 nodes",
                "type": "task",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:08:00", "timestamp_end": "00:08:40"},
                "note": "مهم جداً للمشروع النهائي",
                "task_status": {"is_checked": True, "due_date": "2026-07-28", "owner": None},
            },
            {
                "id": "node_t4",
                "parent_id": "node_p3",
                "label": "كتابة JSON schema validator",
                "type": "task",
                "order_index": 0,
                "source_ref": {"timestamp_start": "00:11:30", "timestamp_end": "00:12:00"},
                "note": None,
                "task_status": {"is_checked": False, "due_date": None, "owner": None},
            },
        ],

        "edges": [
            {"id": "e1", "source": "node_root", "target": "node_g1"},
            {"id": "e2", "source": "node_root", "target": "node_g2"},
            {"id": "e3", "source": "node_g1",   "target": "node_p1"},
            {"id": "e4", "source": "node_g1",   "target": "node_p2"},
            {"id": "e5", "source": "node_g2",   "target": "node_p3"},
            {"id": "e6", "source": "node_p1",   "target": "node_t1"},
            {"id": "e7", "source": "node_p1",   "target": "node_t2"},
            {"id": "e8", "source": "node_p2",   "target": "node_t3"},
            {"id": "e9", "source": "node_p3",   "target": "node_t4"},
        ],

        "stats": {
            "total_goals": 2,
            "total_plans": 3,
            "total_tasks": 4,
            "tasks_completed": 1,
            "audio_duration_seconds": 780,
            "transcript_word_count": 3200,
            "validation_score": 0.94,
        },
    }
