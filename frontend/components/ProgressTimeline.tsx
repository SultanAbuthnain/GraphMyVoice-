"use client";

import { PIPELINE_STAGES, type Session } from "@/lib/types";

export default function ProgressTimeline({ session }: { session: Session }) {
  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.key === session.status);
  const failed = session.status === "failed";

  return (
    <div className="rounded-2xl bg-ink-900 p-6">
      <ol className="flex flex-col gap-4">
        {PIPELINE_STAGES.map((stage, i) => {
          const isDone = !failed && i < currentIndex;
          const isCurrent = !failed && i === currentIndex;
          return (
            <li key={stage.key} className="flex items-center gap-3">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-mono
                  ${isDone ? "bg-signal-teal text-ink-950" : ""}
                  ${isCurrent ? "border-2 border-signal-teal text-signal-teal" : ""}
                  ${!isDone && !isCurrent ? "border border-ink-800 text-ink-600" : ""}`}
              >
                {isDone ? "✓" : i + 1}
              </span>
              <span className={isCurrent ? "font-medium text-paper" : "text-ink-600"}>
                {stage.label}
              </span>
              {isCurrent && (
                <span className="ms-auto flex gap-1" aria-hidden="true">
                  {[0, 1, 2].map((d) => (
                    <span
                      key={d}
                      className="h-1.5 w-1.5 animate-wave rounded-full bg-signal-teal"
                      style={{ animationDelay: `${d * 150}ms` }}
                    />
                  ))}
                </span>
              )}
            </li>
          );
        })}
      </ol>

      {failed && (
        <p className="mt-4 rounded-lg bg-signal-coral/10 p-3 text-sm text-signal-coral" role="alert">
          فشلت المعالجة: {session.error_message ?? "خطأ غير معروف"}
        </p>
      )}
    </div>
  );
}
