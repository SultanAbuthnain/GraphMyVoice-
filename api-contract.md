# 📋 API Contract — Audio-to-Mindmap Learning Assistant
> اتفاقية بين الطالب الأول (Backend) والطالب الثاني (Frontend)  
> **لا تتغير هذه الوثيقة بدون موافقة الطرفين**

---

## Base URL
```
Development:  http://localhost:8000/api/v1
Production:   https://your-domain.com/api/v1
```

## Authentication Header
```http
Authorization: Bearer <jwt_token>
```

---

## 1. `POST /sessions/upload`
**رفع ملف صوتي وبدء المعالجة**

### Request
```http
POST /api/v1/sessions/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `File` | ✅ | ملف صوتي (.mp3 / .wav / .m4a / .ogg) |
| `title` | `string` | ✅ | عنوان الجلسة |
| `language` | `string` | ❌ | لغة الصوت (default: `"auto"`) |

### Response `202 Accepted`
```json
{
  "session_id": "sess_01J5K8XZ3MNPQ7R2T4VWXY9AB",
  "title": "محاضرة البرمجة - الأسبوع الأول",
  "status": "queued",
  "created_at": "2026-07-22T21:00:00Z",
  "estimated_duration_seconds": 120,
  "message": "تم استلام الملف وبدأت المعالجة",
  "poll_url": "/api/v1/sessions/sess_01J5K8XZ3MNPQ7R2T4VWXY9AB/status"
}
```

### Error Responses
```json
// 400 - ملف غير صالح
{
  "error": "invalid_file",
  "message": "نوع الملف غير مدعوم. الأنواع المقبولة: mp3, wav, m4a, ogg",
  "code": 400
}

// 413 - حجم كبير
{
  "error": "file_too_large",
  "message": "حجم الملف يتجاوز الحد المسموح (500MB)",
  "code": 413
}

// 429 - Rate Limit
{
  "error": "rate_limit_exceeded",
  "message": "تجاوزت الحد المسموح. يمكنك رفع 3 ملفات كل ساعة.",
  "retry_after_seconds": 1800,
  "code": 429
}
```

---

## 2. `GET /sessions/{id}/status`
**استطلاع حالة المعالجة — يُستدعى كل 3 ثوانٍ (polling)**

### Request
```http
GET /api/v1/sessions/sess_01J5K8XZ3MNPQ7R2T4VWXY9AB/status
Authorization: Bearer <token>
```

### Response `200 OK`

#### الحالات الممكنة لـ `status`
| Status | المعنى | النسبة المئوية |
|--------|--------|----------------|
| `queued` | في قائمة الانتظار | 0% |
| `transcribing` | Whisper يحول الصوت لنص | 10-40% |
| `extracting` | LLM يستخرج الأهداف والمهام | 40-70% |
| `building_mindmap` | بناء خريطة الـ Nodes | 70-85% |
| `validating` | Guardrail يتحقق من النتائج | 85-95% |
| `done` | اكتملت المعالجة | 100% |
| `failed` | فشلت المعالجة | - |

```json
{
  "session_id": "sess_01J5K8XZ3MNPQ7R2T4VWXY9AB",
  "status": "transcribing",
  "progress_percent": 25,
  "current_step": "transcribing",
  "steps": [
    { "name": "ingestion",      "label": "استلام الملف",        "status": "done",        "completed_at": "2026-07-22T21:00:05Z" },
    { "name": "transcribing",   "label": "تفريغ الصوت",         "status": "in_progress", "completed_at": null },
    { "name": "extracting",     "label": "استخراج المحتوى",     "status": "pending",     "completed_at": null },
    { "name": "building_mindmap","label": "بناء الخريطة الذهنية","status": "pending",     "completed_at": null },
    { "name": "validating",     "label": "التحقق من الجودة",    "status": "pending",     "completed_at": null },
    { "name": "saving",         "label": "حفظ النتائج",         "status": "pending",     "completed_at": null }
  ],
  "started_at": "2026-07-22T21:00:03Z",
  "updated_at": "2026-07-22T21:00:30Z",
  "error": null
}
```

#### عند الفشل
```json
{
  "session_id": "sess_01J5K8XZ3MNPQ7R2T4VWXY9AB",
  "status": "failed",
  "progress_percent": 35,
  "current_step": "extracting",
  "steps": [ "..." ],
  "error": {
    "code": "extraction_failed",
    "message": "فشل استخراج المحتوى بعد 3 محاولات",
    "retryable": true
  }
}
```

---

## 3. `GET /sessions/{id}/mindmap`
**استرجاع الخريطة الذهنية الكاملة**

### Request
```http
GET /api/v1/sessions/sess_01J5K8XZ3MNPQ7R2T4VWXY9AB/mindmap
Authorization: Bearer <token>
```

### Response `200 OK`

```json
{
  "session_id": "sess_01J5K8XZ3MNPQ7R2T4VWXY9AB",
  "title": "محاضرة البرمجة - الأسبوع الأول",
  "topic": "مقدمة في بناء AI Agents باستخدام LangGraph",
  "generated_at": "2026-07-22T21:05:00Z",
  "transcript_preview": "في هذه المحاضرة سنتعلم كيفية بناء وكلاء ذكاء اصطناعي...",

  "extracted": {
    "goals": [
      {
        "id": "g1",
        "title": "فهم مفهوم AI Agents",
        "plans": [
          {
            "id": "p1",
            "title": "دراسة أنماط الـ Agent الأساسية",
            "tasks": [
              {
                "id": "t1",
                "title": "قراءة مقال ReAct Pattern",
                "owner": null,
                "due": null
              },
              {
                "id": "t2",
                "title": "تطبيق مثال Tool Calling",
                "owner": "الطالب",
                "due": "2026-07-25"
              }
            ]
          },
          {
            "id": "p2",
            "title": "استكشاف LangGraph State Graphs",
            "tasks": [
              {
                "id": "t3",
                "title": "بناء graph بسيط بـ 3 nodes",
                "owner": null,
                "due": "2026-07-28"
              }
            ]
          }
        ]
      },
      {
        "id": "g2",
        "title": "تطبيق Guardrails على مستوى الإنتاج",
        "plans": [
          {
            "id": "p3",
            "title": "تصميم validation logic",
            "tasks": [
              {
                "id": "t4",
                "title": "كتابة JSON schema validator",
                "owner": null,
                "due": null
              }
            ]
          }
        ]
      }
    ]
  },

  "nodes": [
    {
      "id": "node_root",
      "parent_id": null,
      "label": "مقدمة في بناء AI Agents باستخدام LangGraph",
      "type": "root",
      "order_index": 0,
      "source_ref": null,
      "note": null,
      "task_status": null
    },
    {
      "id": "node_g1",
      "parent_id": "node_root",
      "label": "فهم مفهوم AI Agents",
      "type": "goal",
      "order_index": 0,
      "source_ref": { "timestamp_start": "00:01:30", "timestamp_end": "00:02:45" },
      "note": null,
      "task_status": null
    },
    {
      "id": "node_p1",
      "parent_id": "node_g1",
      "label": "دراسة أنماط الـ Agent الأساسية",
      "type": "plan",
      "order_index": 0,
      "source_ref": { "timestamp_start": "00:02:45", "timestamp_end": "00:05:00" },
      "note": null,
      "task_status": null
    },
    {
      "id": "node_t1",
      "parent_id": "node_p1",
      "label": "قراءة مقال ReAct Pattern",
      "type": "task",
      "order_index": 0,
      "source_ref": { "timestamp_start": "00:03:10", "timestamp_end": "00:03:45" },
      "note": null,
      "task_status": {
        "is_checked": false,
        "due_date": null,
        "owner": null
      }
    },
    {
      "id": "node_t2",
      "parent_id": "node_p1",
      "label": "تطبيق مثال Tool Calling",
      "type": "task",
      "order_index": 1,
      "source_ref": { "timestamp_start": "00:04:00", "timestamp_end": "00:04:30" },
      "note": null,
      "task_status": {
        "is_checked": false,
        "due_date": "2026-07-25",
        "owner": "الطالب"
      }
    },
    {
      "id": "node_t3",
      "parent_id": "node_p2",
      "label": "بناء graph بسيط بـ 3 nodes",
      "type": "task",
      "order_index": 0,
      "source_ref": { "timestamp_start": "00:08:00", "timestamp_end": "00:08:40" },
      "note": "مهم جداً للمشروع النهائي",
      "task_status": {
        "is_checked": true,
        "due_date": "2026-07-28",
        "owner": null
      }
    }
  ],

  "edges": [
    { "id": "e1", "source": "node_root", "target": "node_g1" },
    { "id": "e2", "source": "node_root", "target": "node_g2" },
    { "id": "e3", "source": "node_g1",   "target": "node_p1" },
    { "id": "e4", "source": "node_g1",   "target": "node_p2" },
    { "id": "e5", "source": "node_p1",   "target": "node_t1" },
    { "id": "e6", "source": "node_p1",   "target": "node_t2" },
    { "id": "e7", "source": "node_p2",   "target": "node_t3" }
  ],

  "stats": {
    "total_goals": 2,
    "total_plans": 3,
    "total_tasks": 4,
    "tasks_completed": 1,
    "audio_duration_seconds": 1847,
    "transcript_word_count": 3200,
    "validation_score": 0.94
  }
}
```

---

## 4. `PATCH /nodes/{id}`
**تعديل label لـ node أو طلب إعادة توليد فرع**

### Request
```http
PATCH /api/v1/nodes/node_t1
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "label": "قراءة مقال ReAct Pattern والتلخيص",
  "regenerate_branch": false
}
```

### Response `200 OK`
```json
{
  "id": "node_t1",
  "label": "قراءة مقال ReAct Pattern والتلخيص",
  "updated_at": "2026-07-22T22:00:00Z",
  "regeneration_job_id": null
}
```

#### عند طلب إعادة التوليد (`regenerate_branch: true`)
```json
{
  "id": "node_g1",
  "label": "فهم مفهوم AI Agents",
  "updated_at": "2026-07-22T22:00:00Z",
  "regeneration_job_id": "regen_XYZ789",
  "message": "جاري إعادة توليد الفرع، تابع الحالة عبر /sessions/{id}/status"
}
```

---

## 5. `POST /nodes/{id}/notes`
**إضافة ملاحظة على node**

### Request
```http
POST /api/v1/nodes/node_t1/notes
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "content": "راجع هذا المصدر: https://arxiv.org/abs/2210.03629"
}
```

### Response `201 Created`
```json
{
  "id": "note_ABC123",
  "node_id": "node_t1",
  "user_id": "user_789",
  "content": "راجع هذا المصدر: https://arxiv.org/abs/2210.03629",
  "created_at": "2026-07-22T22:05:00Z"
}
```

---

## 6. `PATCH /tasks/{node_id}`
**تبديل حالة Task (checked / unchecked)**

### Request
```http
PATCH /api/v1/tasks/node_t1
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "is_checked": true,
  "due_date": "2026-07-30",
  "owner": "أحمد"
}
```

### Response `200 OK`
```json
{
  "node_id": "node_t1",
  "is_checked": true,
  "due_date": "2026-07-30",
  "owner": "أحمد",
  "updated_at": "2026-07-22T22:10:00Z"
}
```

---

## 7. `GET /sessions` _(Bonus — قائمة الجلسات)_
```http
GET /api/v1/sessions?page=1&limit=10
Authorization: Bearer <token>
```

### Response `200 OK`
```json
{
  "sessions": [
    {
      "id": "sess_01J5K8XZ3MNPQ7R2T4VWXY9AB",
      "title": "محاضرة البرمجة - الأسبوع الأول",
      "status": "done",
      "created_at": "2026-07-22T21:00:00Z",
      "stats": {
        "total_tasks": 4,
        "tasks_completed": 1
      }
    },
    {
      "id": "sess_ANOTHER_ID",
      "title": "اجتماع الفريق - التخطيط",
      "status": "transcribing",
      "created_at": "2026-07-22T20:00:00Z",
      "stats": null
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 10
}
```

---

## ملاحظات مشتركة بين الطالبين

### Node Types
| type | الوصف | اللون المقترح للـ Frontend |
|------|--------|--------------------------|
| `root` | الموضوع الرئيسي | 🟣 بنفسجي |
| `goal` | هدف | 🔵 أزرق |
| `plan` | خطة | 🟢 أخضر |
| `task` | مهمة قابلة للتتبع | 🟠 برتقالي |

### Polling Strategy للـ Frontend
```
while (status !== "done" && status !== "failed") {
  wait 3 seconds
  GET /sessions/{id}/status
}
```

### Error Format الموحد
```json
{
  "error": "error_code_snake_case",
  "message": "رسالة واضحة للمستخدم",
  "code": 400,
  "details": {}  // optional
}
```

### HTTP Status Codes المتفق عليها
| Code | الاستخدام |
|------|-----------|
| `200` | نجاح (GET/PATCH) |
| `201` | تم الإنشاء (POST) |
| `202` | تم الاستلام، المعالجة تجري (upload) |
| `400` | خطأ في البيانات المرسلة |
| `401` | غير مصرح |
| `404` | العنصر غير موجود |
| `413` | حجم الملف كبير |
| `422` | بيانات غير صالحة (Validation Error) |
| `429` | تجاوز Rate Limit |
| `500` | خطأ داخلي في السيرفر |
