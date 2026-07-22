# Audio-to-Mindmap Backend

Backend API + AI Agents pipeline for the Audio-to-Mindmap Learning Assistant.

Built with: FastAPI · LangGraph · Claude (Anthropic) · Whisper · PostgreSQL

## Quick Start (للطالب الثاني — Mock API جاهز)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env file (لا تحتاج API keys للـ Mock)
copy .env.example .env

# 3. Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API Docs: http://localhost:8000/docs

## Mock Endpoints (جاهزة الحين)

| Method | Endpoint | الوصف |
|--------|----------|-------|
| `POST` | `/api/v1/sessions/upload` | رفع ملف صوتي |
| `GET`  | `/api/v1/sessions/{id}/status` | حالة المعالجة |
| `GET`  | `/api/v1/sessions/{id}/mindmap` | الخريطة الذهنية |
| `PATCH`| `/api/v1/nodes/{id}` | تعديل node |
| `POST` | `/api/v1/nodes/{id}/notes` | إضافة ملاحظة |
| `PATCH`| `/api/v1/tasks/{id}` | تحديث مهمة |

## Project Structure

```
app/
├── api/v1/         # FastAPI routers (Mock → Real)
├── agents/         # LangGraph pipeline (7 nodes)
│   ├── graph.py    # Graph definition + routing
│   ├── state.py    # GraphState TypedDict
│   └── nodes/      # Each agent node
├── models/         # SQLAlchemy ORM models
├── services/       # Pipeline orchestration
└── config.py       # Settings from .env
```

## API Contract

See `api-contract.md` for the full JSON schema agreed between both students.
