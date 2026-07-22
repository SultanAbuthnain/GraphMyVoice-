"use client";

import { useRouter } from "next/navigation";
import UploadPanel from "@/components/UploadPanel";

export default function HomePage() {
  const router = useRouter();

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6 py-16">
      <div className="mb-10 text-center">
        <p className="mb-2 font-mono text-xs uppercase tracking-widest text-signal-teal">
          voice → mindmap
        </p>
        <h1 className="text-2xl font-bold text-paper">حوّل صوتك إلى خريطة ذهنية</h1>
        <p className="mt-2 text-sm text-ink-600">
          ارفع تسجيلًا صوتيًا وخلّي الوكلاء يستخرجون الأهداف، الخطط، والمهام تلقائيًا.
        </p>
      </div>

      <UploadPanel onUploaded={(sessionId) => router.push(`/session/${sessionId}`)} />
    </main>
  );
}
