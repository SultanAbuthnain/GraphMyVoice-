"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Task } from "@/lib/types";

export default function TaskList({ sessionId }: { sessionId: string }) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .listTasks(sessionId)
      .then(setTasks)
      .catch((err) => console.error("failed to load tasks", err))
      .finally(() => setLoading(false));
  }, [sessionId]);

  const toggle = async (task: Task) => {
    const next = !task.is_done;
    setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, is_done: next } : t))); // optimistic
    try {
      await api.toggleTask(sessionId, task.id, next);
    } catch (err) {
      console.error("failed to update task", err);
      setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, is_done: !next } : t))); // revert
    }
  };

  const doneCount = tasks.filter((t) => t.is_done).length;

  return (
    <div className="rounded-2xl bg-ink-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-paper">المهام</h3>
        {tasks.length > 0 && (
          <span className="font-mono text-xs text-ink-600">
            {doneCount}/{tasks.length}
          </span>
        )}
      </div>

      {loading && <p className="text-sm text-ink-600">جارٍ التحميل…</p>}
      {!loading && tasks.length === 0 && <p className="text-sm text-ink-600">لا توجد مهام مستخرجة بعد.</p>}

      <ul className="space-y-1.5">
        {tasks.map((task) => (
          <li key={task.id}>
            <label className="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 hover:bg-ink-950">
              <input
                type="checkbox"
                checked={task.is_done}
                onChange={() => toggle(task)}
                className="h-4 w-4 rounded border-ink-800 bg-ink-950 text-signal-amber accent-signal-amber"
              />
              <span className={`text-sm ${task.is_done ? "text-ink-600 line-through" : "text-paper"}`}>
                {task.title}
              </span>
            </label>
          </li>
        ))}
      </ul>
    </div>
  );
}
