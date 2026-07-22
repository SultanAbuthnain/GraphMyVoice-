# Project: Audio-to-Mindmap Learning Assistant

## 1. One-line description
A web platform where a user uploads an audio recording of a lecture or meeting, and the system automatically generates an interactive mind map of the goals, plans, and tasks discussed. The user can review the mind map, add personal notes, and check off tasks as completed.

## 2. Goals
- Turn unstructured spoken content (lecture/meeting) into a structured, navigable visual summary.
- Let the user annotate the output (notes) and track action items (checkboxes) persistently across sessions.
- Demonstrate a multi-agent, stateful, production-ready AI system (course requirement: agent patterns, state graphs, multi-agent orchestration, guardrails, deployment).

## 3. High-level architecture

```
[Browser: React/Next.js Frontend]
        |
        | REST/WebSocket
        v
[FastAPI Backend]
        |
        v
[LangGraph Orchestrator]  <-- the "brain": a stateful graph, not a single LLM call
   |        |          |            |
   v        v          v            v
[Transcription  [Extraction   [Structuring   [Guardrail/
 Agent]          Agent]        Agent]         Validator Agent]
   |                                              |
   v                                              v
[Whisper STT API]                        [Content/safety checks]
        |
        v
[Structured JSON: goals / plans / tasks / relationships]
        |
        v
[PostgreSQL: sessions, mindmap_nodes, notes, tasks]
        |
        v
[Frontend renders interactive mind map + notes + checkboxes]
```

## 4. Tech stack recommendation

| Layer | Choice | Why |
|---|---|---|
| Frontend | React (Next.js) + Tailwind | Fast iteration, good ecosystem for interactive graphs |
| Mind map rendering | React Flow or Markmap | Both support editable, interactive node graphs |
| Backend API | FastAPI (Python) | Matches the course's Python-based agent stack |
| Agent orchestration | LangGraph | Directly matches Day 2 of the course (State Graphs) |
| LLM | Claude API (Anthropic) | Structured JSON output, function/tool calling |
| Speech-to-text | Whisper (OpenAI API or local `whisper.cpp`) | Reliable, handles long audio with chunking |
| Database | PostgreSQL | Relational structure fits goals→plans→tasks hierarchy well |
| Auth | JWT-based simple auth (or Supabase/Auth0 if time allows) | Needed for per-user notes/tasks persistence |
| Deployment | Docker + docker-compose, then a cloud target (Render/Railway/AWS) | Matches Day 5 of the course |
| Monitoring | LangSmith or simple structured logging | Matches Day 4 (production monitoring) |

## 5. Multi-agent design (LangGraph)

Model this as a **stateful graph**, not a single prompt. Suggested nodes:

1. **Ingestion Node** — receives uploaded audio file, validates format/size/duration, stores raw file.
2. **Transcription Agent** — calls Whisper; if audio is long, chunks it (e.g. every 5–10 min) and stitches transcripts together with timestamps.
3. **Guardrail Node (pre-processing)** — checks transcript isn't empty/garbled, filters unsafe/irrelevant content, enforces max token length before extraction.
4. **Extraction Agent** — takes the transcript and produces **structured JSON only** (no free text) with this shape:
   ```json
   {
     "topic": "string",
     "goals": [
       {
         "id": "g1",
         "title": "string",
         "plans": [
           {
             "id": "p1",
             "title": "string",
             "tasks": [
               {"id": "t1", "title": "string", "owner": "string|null", "due": "string|null"}
             ]
           }
         ]
       }
     ]
   }
   ```
   Use the LLM's structured-output / tool-calling mode to enforce this schema (avoid free-form hallucinated text).
5. **Structuring/Mindmap Builder Agent** — converts the JSON hierarchy into mind-map node/edge format the frontend can render (id, parentId, label, type).
6. **Guardrail Node (post-processing)** — sanity-check: every task must trace back to a sentence/timestamp in the transcript (reduces hallucination); reject or flag orphaned nodes.
7. **Persistence Node** — writes the mind map, and initializes empty notes/task-status rows, to the database.
8. **Human-in-the-loop Node** — after generation, the user can edit nodes, add notes, or request regeneration of a specific branch (this reuses the LangGraph checkpoint/state so regeneration doesn't restart from scratch).

State object passed through the graph should hold: `audio_path`, `transcript`, `chunks`, `extracted_json`, `mindmap`, `validation_flags`, `user_id`, `session_id`.

## 6. Database schema (minimum viable)

```
sessions(id, user_id, title, audio_path, created_at, status)
mindmap_nodes(id, session_id, parent_id, label, node_type[goal|plan|task], order_index)
tasks(node_id -> mindmap_nodes.id, is_checked boolean, due_date, owner)
notes(id, node_id -> mindmap_nodes.id, user_id, content, created_at)
```

## 7. API endpoints (draft)

```
POST   /sessions/upload            -> upload audio, kicks off LangGraph pipeline (async job)
GET    /sessions/{id}/status       -> poll pipeline progress (transcribing / extracting / done)
GET    /sessions/{id}/mindmap      -> get full mind map JSON
PATCH  /nodes/{id}                 -> edit node label / regenerate branch
POST   /nodes/{id}/notes           -> add a note to a node
PATCH  /tasks/{node_id}            -> toggle task checked/unchecked
```

Use a background job/queue (Celery, or simple FastAPI BackgroundTasks for MVP) since transcription + LLM extraction on a long recording can take minutes — don't block the HTTP request.

## 8. Guardrails & security (course requirement, Day 4)

- Validate file type/size/duration before processing (prevent abuse).
- Rate-limit uploads per user.
- Sanitize all LLM outputs before rendering (no raw HTML injection into frontend).
- Enforce structured-output schema strictly; reject and retry if the LLM returns malformed JSON.
- Add a "hallucination check" step: each generated task should be traceable to transcript content.
- Never expose API keys client-side — proxy all LLM/Whisper calls through the backend.

## 9. Deployment (course requirement, Day 5)

- Containerize backend + frontend + Postgres with `docker-compose` for local dev.
- CI: basic GitHub Actions to run tests + build images.
- Deploy to a cloud target (Railway/Render/AWS ECS) with environment-based secrets.
- Add basic logging/monitoring (structured logs, request IDs, LangGraph run traces).

## 10. Suggested build order (for iterative "vibe coding")

1. Backend skeleton (FastAPI) + Postgres schema + file upload endpoint.
2. Whisper integration — audio in, transcript out, stored in DB.
3. LangGraph pipeline: transcript in, structured JSON goals/plans/tasks out (test with hardcoded transcript first).
4. Guardrail/validation node.
5. Frontend: render mind map from JSON (start static, then wire to live API).
6. Add notes + task checkbox persistence (full CRUD).
7. Add human-in-the-loop regeneration of a branch.
8. Dockerize everything, deploy to cloud.
9. Add monitoring/logging layer.

## 11. Open questions to resolve with your teammate before coding

- Which LLM/Whisper provider (cost vs. quality vs. offline capability)?
- Auth: full user accounts, or a simpler session-token-per-upload model for MVP?
- How long can uploaded audio be (affects chunking strategy)?
- Real-time transcript streaming (nice-to-have) vs. batch processing only (simpler MVP)?
