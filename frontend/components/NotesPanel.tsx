"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Note } from "@/lib/types";

export default function NotesPanel({
  sessionId,
  selectedNodeId,
}: {
  sessionId: string;
  selectedNodeId: string | null;
}) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listNotes(sessionId)
      .then(setNotes)
      .catch((err) => console.error("failed to load notes", err))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const addNote = async () => {
    const content = draft.trim();
    if (!content) return;
    setDraft("");
    try {
      const note = await api.createNote(sessionId, content, selectedNodeId ?? undefined);
      setNotes((prev) => [note, ...prev]);
    } catch (err) {
      console.error("failed to add note", err);
    }
  };

  const removeNote = async (noteId: string) => {
    setNotes((prev) => prev.filter((n) => n.id !== noteId)); // optimistic
    try {
      await api.deleteNote(sessionId, noteId);
    } catch (err) {
      console.error("failed to delete note", err);
    }
  };

  return (
    <div className="flex h-full flex-col rounded-2xl bg-ink-900 p-4">
      <h3 className="mb-3 text-sm font-semibold text-paper">
        النوتس {selectedNodeId ? "· مرتبطة بالعنصر المحدد" : ""}
      </h3>

      <div className="mb-3 flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addNote()}
          placeholder="أضف ملاحظة…"
          className="flex-1 rounded-lg border border-ink-800 bg-ink-950 px-3 py-2 text-sm text-paper placeholder:text-ink-600 focus:border-signal-teal"
        />
        <button
          onClick={addNote}
          className="rounded-lg bg-signal-teal px-3 py-2 text-sm font-semibold text-ink-950 hover:brightness-110"
        >
          إضافة
        </button>
      </div>

      <ul className="flex-1 space-y-2 overflow-y-auto">
        {loading && <li className="text-sm text-ink-600">جارٍ التحميل…</li>}
        {!loading && notes.length === 0 && (
          <li className="text-sm text-ink-600">لا توجد ملاحظات بعد.</li>
        )}
        {notes.map((note) => (
          <li
            key={note.id}
            className="group flex items-start justify-between gap-2 rounded-lg bg-ink-950 p-3 text-sm text-paper"
          >
            <span>{note.content}</span>
            <button
              onClick={() => removeNote(note.id)}
              className="text-ink-600 opacity-0 transition group-hover:opacity-100 hover:text-signal-coral"
              aria-label="حذف الملاحظة"
            >
              ✕
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
