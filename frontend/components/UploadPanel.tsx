"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";

interface UploadPanelProps {
  onUploaded: (sessionId: string) => void;
}

const ACCEPTED_TYPES = ["audio/mpeg", "audio/mp4", "audio/wav", "audio/x-m4a", "audio/webm"];

export default function UploadPanel({ onUploaded }: UploadPanelProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);

      if (ACCEPTED_TYPES.length && !ACCEPTED_TYPES.includes(file.type) && !file.name.match(/\.(mp3|wav|m4a|webm)$/i)) {
        setError("صيغة غير مدعومة. جرّب mp3, wav, m4a, أو webm.");
        return;
      }

      setFileName(file.name);
      setIsUploading(true);
      try {
        const session = await api.uploadSession(file, file.name.replace(/\.[^/.]+$/, ""));
        onUploaded(session.id);
      } catch (err) {
        setError(err instanceof Error ? err.message : "فشل الرفع. حاول مرة أخرى.");
      } finally {
        setIsUploading(false);
      }
    },
    [onUploaded]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) handleFile(file);
      }}
      className={`relative rounded-2xl border-2 border-dashed p-10 text-center transition-colors
        ${isDragging ? "border-signal-teal bg-ink-800" : "border-ink-800 bg-ink-900"}`}
    >
      {/* signature: idle waveform bars */}
      <div className="mx-auto mb-6 flex h-12 items-end justify-center gap-1" aria-hidden="true">
        {[0.4, 0.7, 1, 0.55, 0.85, 0.35, 0.65].map((h, i) => (
          <span
            key={i}
            className={`w-1.5 rounded-full bg-signal-teal ${isUploading ? "animate-wave" : ""}`}
            style={{ height: `${h * 100}%`, animationDelay: `${i * 90}ms` }}
          />
        ))}
      </div>

      <h2 className="mb-1 text-lg font-semibold text-paper">ارفع تسجيلك الصوتي</h2>
      <p className="mb-6 text-sm text-ink-600">اسحب الملف هنا، أو اختره من جهازك — mp3, wav, m4a, webm</p>

      <input
        ref={inputRef}
        type="file"
        accept="audio/*"
        className="sr-only"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
        }}
      />

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={isUploading}
        className="rounded-full bg-signal-teal px-6 py-2.5 text-sm font-semibold text-ink-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isUploading ? "جارٍ الرفع…" : "اختر ملفًا"}
      </button>

      {fileName && !error && (
        <p className="mt-4 text-xs text-ink-600">{fileName}</p>
      )}
      {error && (
        <p className="mt-4 text-sm text-signal-coral" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
