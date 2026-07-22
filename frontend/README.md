# Voice → Mindmap — Frontend ( Mohammed Alfarraj)

يغطي هذا المجلد جميع مهام الطالب محمد الفراج من التقسيم:

- واجهة رفع الملف الصوتي + شاشة progress أثناء المعالجة (`components/UploadPanel.tsx`, `components/ProgressTimeline.tsx`)
- الخريطة الذهنية التفاعلية باستخدام React Flow (`components/MindMap.tsx`)
- نوتس + checkboxes مربوطة بقاعدة البيانات (`components/NotesPanel.tsx`, `components/TaskList.tsx`)
- تصميم قاعدة البيانات (`db/schema.sql`)
- إعداد الـ Deployment (`Dockerfile`, أدناه)

## بنية المشروع

```
mindmap-frontend/
├── app/
│   ├── page.tsx                 # صفحة الرفع الرئيسية
│   ├── session/[id]/page.tsx    # مساحة عمل الجلسة (progress → mindmap/notes/tasks)
│   ├── layout.tsx
│   └── globals.css
├── components/
│   ├── UploadPanel.tsx
│   ├── ProgressTimeline.tsx
│   ├── MindMap.tsx
│   ├── NotesPanel.tsx
│   └── TaskList.tsx
├── lib/
│   ├── api.ts                   # عميل REST يطابق endpoints الـ FastAPI
│   └── types.ts                 # الأنواع المشتركة — اتفقوا عليها مع فريق الـ Backend أولًا
├── db/
│   └── schema.sql                # سكيمة PostgreSQL: sessions, mindmap_nodes, mindmap_edges, notes, tasks
├── Dockerfile
└── .env.example
```

## نقطة الاتفاق الحرجة مع الزميل سلطان

قبل ما مانبدى بالتوازي، اتفقنا سوا على:

1. **شكل استجابة `/sessions/{id}/mindmap`** — الشكل المفترض موجود في `lib/types.ts` (`MindmapResponse` = `{ session_id, nodes[], edges[] }`). لو الـ AI agent يرجّع شكل مختلف، عدّلوا `types.ts` و `api.ts` مرة وحدة بدل ما يصير فيه تعارض لاحقًا.
2. **قيم `status` في الجلسة** — معرّفة في `SessionStatus` و `PIPELINE_STAGES` (uploaded → transcribing → extracting → structuring → validating → completed/failed). لازم الـ backend يرجّع نفس القيم بالضبط.
3. **endpoints الملاحظات والمهام** (`/sessions/{id}/notes`, `/sessions/{id}/tasks`) مو موجودة صراحة في الدايجرام الأصلي — أضفتها كافتراض معقول عشان الـ checkboxes تنحفظ. أكدوا الأسماء النهائية مع الطالب الأول.

## التشغيل محليًا

```bash
npm install
cp .env.example .env.local   # عدّل NEXT_PUBLIC_API_BASE إذا الباكند مو على 8000
npm run dev
```

يفتح على `http://localhost:3000`.

## قاعدة البيانات

طبّق السكيمة على Postgres محلي أو على Neon/Supabase:

```bash
psql "$DATABASE_URL" -f db/schema.sql
```

الجداول: `sessions`, `mindmap_nodes`, `mindmap_edges`, `notes`, `tasks` — تطابق تمامًا الصندوق الأخير في الدايجرام المعماري.

## الـ Deployment

### الخيار الأول (الأسرع) — Vercel

1. ادفع الكود إلى GitHub.
2. اربط المستودع بـ Vercel، فريم وورك = Next.js (يتعرف تلقائيًا).
3. أضف متغير البيئة `NEXT_PUBLIC_API_BASE` بعنوان الباكند المنشور (Render/Railway/Fly.io).
4. Deploy — كل push على main يحدّث النسخة تلقائيًا.

### الخيار الثاني — Docker (لو الفريق يفضل حاوية موحدة)

```bash
docker build -t mindmap-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE=https://your-backend.example.com mindmap-frontend
```

### قاعدة البيانات في الإنتاج

استخدموا Postgres مُدار (Neon أو Supabase أو Railway Postgres) — طبّقوا `db/schema.sql` عليه، وحطوا الـ connection string في متغيرات بيئة الباكند (مو الفرونت اند، لأن الفرونت اند ما يتكلم مع Postgres مباشرة، فقط عبر REST API).

## ملاحظات تصميم

الثيم داكن مقصود (`ink` + `paper` + `signal-teal/amber/coral` في `tailwind.config.js`) بدل الافتراضي الشائع (خلفية كريمية + accent تراكوتا) — العنصر المميز هو الـ waveform bars اللي تظهر أثناء الرفع والمعالجة، تعكس إنه المنتج مبني على الصوت.
# GraphMyVoice-
