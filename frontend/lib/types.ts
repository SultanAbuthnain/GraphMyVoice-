// Shared types — must stay in sync with the backend's structured-output
// JSON schema and the Postgres schema in db/schema.sql.
// Agree on this file with the Backend/AI teammate FIRST; both sides build against it.

export type SessionStatus =
  | "uploaded"
  | "transcribing"
  | "extracting"
  | "structuring"
  | "validating"
  | "completed"
  | "failed";

export interface Session {
  id: string;
  title: string;
  status: SessionStatus;
  error_message: string | null;
  audio_url: string;
  duration_sec: number | null;
  created_at: string;
  updated_at: string;
}

export type NodeType = "goal" | "plan" | "task" | "topic" | "note_ref";

export interface MindmapNode {
  id: string;
  session_id: string;
  parent_id: string | null;
  type: NodeType;
  label: string;
  description: string | null;
  position_x: number;
  position_y: number;
  order_index: number;
}

export interface MindmapEdge {
  id: string;
  session_id: string;
  source_node_id: string;
  target_node_id: string;
  relationship_type: string;
}

export interface MindmapResponse {
  session_id: string;
  nodes: MindmapNode[];
  edges: MindmapEdge[];
}

export interface Note {
  id: string;
  session_id: string;
  node_id: string | null;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  session_id: string;
  node_id: string | null;
  title: string;
  is_done: boolean;
  due_date: string | null;
}

// Ordered stages shown in the progress UI — mirrors the LangGraph pipeline.
export const PIPELINE_STAGES: { key: SessionStatus; label: string }[] = [
  { key: "uploaded", label: "تم الرفع" },
  { key: "transcribing", label: "تفريغ الصوت" },
  { key: "extracting", label: "استخراج الأفكار" },
  { key: "structuring", label: "بناء الخريطة" },
  { key: "validating", label: "التحقق (Guardrails)" },
  { key: "completed", label: "جاهز" },
];
