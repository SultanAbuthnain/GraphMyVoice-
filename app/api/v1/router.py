"""
app/api/v1/router.py
─────────────────────
Aggregates all v1 route modules into a single APIRouter.
"""

from fastapi import APIRouter

from app.api.v1 import sessions, mindmap, nodes, notes, tasks

api_router = APIRouter()

api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(mindmap.router,  prefix="/sessions", tags=["mindmap"])
api_router.include_router(nodes.router,    prefix="/nodes",    tags=["nodes"])
api_router.include_router(notes.router,    prefix="/nodes",    tags=["notes"])
api_router.include_router(tasks.router,    prefix="/tasks",    tags=["tasks"])
