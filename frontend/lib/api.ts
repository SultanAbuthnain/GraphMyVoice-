import type { MindmapResponse, Note, Session, Task } from "./types";

// Point this at the FastAPI backend. Set NEXT_PUBLIC_API_BASE in .env.local
// and in your deployment platform's environment variables.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${path}: ${text || res.statusText}`);
  }
  // 204 No Content
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  // ---- pipeline endpoints (Backend/AI teammate) ----
  uploadSession(file: File, title?: string): Promise<Session> {
    const form = new FormData();
    form.append("audio", file);
    if (title) form.append("title", title);
    return request<Session>("/sessions/upload", { method: "POST", body: form });
  },

  getStatus(sessionId: string): Promise<Session> {
    return request<Session>(`/sessions/${sessionId}/status`);
  },

  getMindmap(sessionId: string): Promise<MindmapResponse> {
    return request<MindmapResponse>(`/sessions/${sessionId}/mindmap`);
  },

  // ---- notes ----
  listNotes(sessionId: string): Promise<Note[]> {
    return request<Note[]>(`/sessions/${sessionId}/notes`);
  },

  createNote(sessionId: string, content: string, nodeId?: string): Promise<Note> {
    return request<Note>(`/sessions/${sessionId}/notes`, {
      method: "POST",
      body: JSON.stringify({ content, node_id: nodeId ?? null }),
    });
  },

  deleteNote(sessionId: string, noteId: string): Promise<void> {
    return request<void>(`/sessions/${sessionId}/notes/${noteId}`, { method: "DELETE" });
  },

  // ---- tasks ----
  listTasks(sessionId: string): Promise<Task[]> {
    return request<Task[]>(`/sessions/${sessionId}/tasks`);
  },

  toggleTask(sessionId: string, taskId: string, isDone: boolean): Promise<Task> {
    return request<Task>(`/sessions/${sessionId}/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_done: isDone }),
    });
  },

  createTask(sessionId: string, title: string, nodeId?: string, dueDate?: string): Promise<Task> {
    return request<Task>(`/sessions/${sessionId}/tasks`, {
      method: "POST",
      body: JSON.stringify({ title, node_id: nodeId ?? null, due_date: dueDate ?? null }),
    });
  },
};

/** Poll session status until it reaches a terminal state (completed/failed). */
export function pollSessionStatus(
  sessionId: string,
  onUpdate: (session: Session) => void,
  intervalMs = 2000
): () => void {
  let cancelled = false;

  const tick = async () => {
    if (cancelled) return;
    try {
      const session = await api.getStatus(sessionId);
      onUpdate(session);
      if (session.status === "completed" || session.status === "failed") return;
    } catch (err) {
      console.error("status poll failed", err);
    }
    if (!cancelled) setTimeout(tick, intervalMs);
  };

  tick();
  return () => {
    cancelled = true;
  };
}
