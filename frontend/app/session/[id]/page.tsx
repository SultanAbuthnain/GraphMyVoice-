"use client";

import { useEffect, useState } from "react";
import { api, pollSessionStatus } from "@/lib/api";
import type { MindmapResponse, Session } from "@/lib/types";
import ProgressTimeline from "@/components/ProgressTimeline";
import MindMap from "@/components/MindMap";
import NotesPanel from "@/components/NotesPanel";
import TaskList from "@/components/TaskList";

export default function SessionPage({ params }: { params: { id: string } }) {
  const sessionId = params.id;
  const [session, setSession] = useState<Session | null>(null);
  const [mindmap, setMindmap] = useState<MindmapResponse | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // poll pipeline status until completed/failed
  useEffect(() => {
    const stop = pollSessionStatus(sessionId, setSession);
    return stop;
  }, [sessionId]);

  // once completed, fetch the built mindmap
  useEffect(() => {
    if (session?.status === "completed") {
      api.getMindmap(sessionId).then(setMindmap).catch(console.error);
    }
  }, [session?.status, sessionId]);

  if (!session) {
    return <main className="p-10 text-ink-600">جارٍ تحميل الجلسة…</main>;
  }

  const isReady = session.status === "completed" && mindmap;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="mb-1 text-xl font-bold text-paper">{session.title}</h1>
      <p className="mb-6 font-mono text-xs text-ink-600">session · {sessionId}</p>

      {!isReady ? (
        <div className="mx-auto max-w-md">
          <ProgressTimeline session={session} />
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          <MindMap mindmap={mindmap} onNodeClick={setSelectedNodeId} />
          <div className="flex flex-col gap-6">
            <TaskList sessionId={sessionId} />
            <NotesPanel sessionId={sessionId} selectedNodeId={selectedNodeId} />
          </div>
        </div>
      )}
    </main>
  );
}
