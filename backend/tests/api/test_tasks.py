import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session
from app.models.task import Task

@pytest.fixture
async def test_session(db_session: AsyncSession) -> Session:
    session = Session(title="Test Session", audio_url="dummy.mp3")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session

@pytest.mark.asyncio
async def test_create_task(client: AsyncClient, test_session: Session):
    response = await client.post(
        f"/api/v1/sessions/{test_session.id}/tasks",
        json={
            "title": "My New Manual Task",
            "due_date": "2026-12-31"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My New Manual Task"
    assert data["is_done"] is False
    assert data["due_date"] == "2026-12-31"
    assert data["session_id"] == str(test_session.id)
    assert data["node_id"] is None

@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, db_session: AsyncSession, test_session: Session):
    # Add a task directly to the db
    task = Task(session_id=test_session.id, title="Existing Task")
    db_session.add(task)
    await db_session.commit()
    
    response = await client.get(f"/api/v1/sessions/{test_session.id}/tasks")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Existing Task"
    assert data[0]["is_done"] is False
