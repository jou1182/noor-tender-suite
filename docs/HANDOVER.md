# HANDOVER — ملف التسليم للوكيل القادم
> اقرأ هذا الملف أولاً. يلخص أين نحن في الرحلة، ماذا تغير ولماذا، وأين هي الثغرات المتبقية.
> الدليل التفصيلي للمستخدم: `docs/USER_GUIDE_AR.md` — والمعمارية الكاملة في `docs/PRD_ConTech_AI_Platform.md`.

---

## 1) هوية المشروع

**ConTech AI Platform** — منصة مؤسسية لذكاء المنافسات الإنشائية في السعودية:
ترفع حزمة RFP، يفككها سرب من 10 وكلاء LangGraph (استخراج البنود، BOQ، الجدول الزمني P6/DCMA، SBC، QA/QC، HSE، الفحص المتقاطع، الفريق الأحمر، التحكيم)، وتنتج درجة فنية /100 + مصفوفات امتثال + عرض مختوم ببلوكتشين.

- **Backend**: FastAPI + SQLAlchemy + SQLite (تطوير)/PostgreSQL (إنتاج) + Qdrant + SSE — `.venv` جاهز، نقطة الدخول `app/main.py`.
- **Frontend**: Next.js 15 App Router + Tailwind + ReactFlow — `frontend/`.
- **قاعدة البيانات الحقيقية للتطوير**: `contech.db` و`tender_db.sqlite` في الجذر.
- **لا Git repo** بعد — أول عمل موصى به للوكيل القادم: `git init` + commit أول.

## 2) حالة الجلسة الأخيرة (2026-08-25)

### ما أُنجز (كلّه مُختبر — 176 اختباراً تمر):
1. **نهاية العملاء الثابتين**: كانت القائمة العلوية تعرض 4 عملاء مزيفين (أرامكو…) من `demoData.ts`. الآن `DashboardHeader.tsx` يجلب المنافسات من `GET /api/v1/tenders` ويدير إنشاءها وحذفها. عقد معماري محمي باختبار (`test_no_static_tenants_in_header_source`) يمنع رجوع الأسماء الثابتة.
2. **زر إطلاق السرب** «انطلق أيها الوكلاء»: `POST /api/v1/tenders/{id}/launch` يعيد استخدام `_run_swarm_audit` من `app/main.py` مع ملفات المنافسة المسجلة. يرفض 422 إن لم توجد RFP+XER، و409 إن كان يعمل أصلاً. الزر في `page.tsx`.
3. **الحذف الآمن متعدد الطبقات**:
   - منافسة كاملة: `DELETE /api/v1/tenders/{id}` — امتثال + مستندات + سجلات تدقيق + ملفات قرص + المنافسة (في `app/api/v1/endpoints/tenders.py`).
   - مستند مفرد: `DELETE /api/v1/documents/{id}` — شرائح + متجهات Qdrant (فلتر document_id) + الملف تحت UPLOAD_ROOT فقط (في `documents.py`). UI بتأكيد inline في `DocumentLibrary.tsx`.
4. **غرفة تدريب الوكلاء**: `POST /api/v1/agents/{key}/preview` يجرّب مسودة الهوية (برومبت/نموذج/حرارة) عبر `llm_gateway_v2.chat` دون تخزين. 409 واضح إن لم يوجد مزود مفعّل.
5. **شاشة الوكلاء أعيد بناؤها** (`frontend/src/app/settings/page.tsx`, داكنة متسقة): الاسم الإنجليزي **لم يعد صلباً** (كان الواجهة لا تعرضه للتحرير رغم دعم الـAPI له)، الصورة والدور والحرارة قابلة للتعديل، محرر System Prompt بزر «التدريب»، زر «تجربة» للمعاينة الحية، حفظ صريح/تراجع بدل الحفظ عند blur.
6. **إصلاحات بيضية**:
   - `tests/test_security_rbac.py`: كان يسجل `dependency_overrides[get_db]` على مستوى الموديول ولا يزيله → يلوث كل اختبارات الحزمة اللاحقة بخطأ "no such table". أصبح setUp/tearDown نظيفان.
   - `tests/test_proposal_drafting.py`: اختبار مكرر باسم واحد (بايثون يبقي الأخير فقط) + تأكيدات على صيغ نصية قديمة. صُحح ليطابق السلوك المقصود.
   - إزالة تكرار استيرادات شاذة في settings/page.tsx القديم.

### نتائج التحقق النهائية:
```
pytest tests/  → 176 passed
tsc --noEmit   → 0 أخطاء
next build     → ✓ Compiled successfully (مرحلة page-data تفشل بسبب
                 مضاد فيروسات/نظام ملفات بطيء على هذا الجهاز — EISDIR readlink
                 على ملفات node_modules مختلفة كل مرة. dev server يعمل ممتازاً
                 وخدم كل الصفحات 200. ليس خطأ كود.)
اختبار حي      → دورة حياة كاملة: create→list→patch→launch(422 صح)→delete→404
                 preview بدون مزود→409 برسالة عربية قابلة للتنفيذ
                 rename name_en عبر PUT→200
```

## 3) خريطة الملفات الحرجة

| الملف | دوره |
|---|---|
| `app/api/v1/endpoints/tenders.py` | ★ جديد بالكامل — دورة حياة المنافسة |
| `app/api/v1/endpoints/documents.py` | DELETE المستند + pipeline المعايير المثبتة |
| `app/api/v1/endpoints/agents.py` | السجل + preview غرفة التدريب |
| `app/core/platform_seed.py` | بذرة الوكلاء الـ13 (10 أساسيين + 3 مساعدون) |
| `app/core/llm_gateway_v2.py` | `chat(provider, messages, temperature, model_override)` |
| `app/services/proposal_drafter.py` | قوالب المسودة الحتمية عربي/إنجليزي |
| `frontend/src/components/DashboardHeader.tsx` | ★ مبدّل مساحات العمل الديناميكي |
| `frontend/src/lib/tenders_client.ts` | ★ API client لدورة الحياة |
| `frontend/src/hooks/useTenderAudit.ts` | polling لحالة التدقيق (3s أثناء processing) |
| `tests/test_dynamic_workspaces.py` | ★ 11 اختبار حماية للسلوك الجديد |

## 4) ثغرات ومعروفات — خطة من هنا

0. **Git repo ✓ (تم 2026-08-25):** `https://github.com/jou1182/contech-ai-platform` (PRIVATE، حساب jou1182، فرع master).
   - `.gitignore` يستثني: `.env*` (عدا الأمثلة)، قواعد البيانات `*.db/*.sqlite`، `uploads/`، `qdrant_data/qdrant_storage`، النسخ الاحتياطية، الفيديو.
   - **روتين العمل من اليوم:** عدّل الكود → `git add -A && git commit -m "..."` → `git push` → ثم أعد بناء Docker إن كان التعديل يشغّل المنصة.
   - أول commit: `b68dd35` — MVP كامل (314 ملفاً، 459KB نظيف بلا أسرار).

1. **بناء الإنتاج على هذا الجهاز**: `next build` يصل "Compiled successfully" ثم يفشل في جمع بيانات الصفحات بسبب EISDIR/readlink عشوائي (مضاد فيروسات يقفل node_modules). الحلول الممكنة: استبعاد مجلد المشروع من الفحص الحي، أو البناء داخل Docker (يوجد `Dockerfile.backend` و`docker-compose.yml` وHelm charts جاهزة في `deploy/`).
2. **الخادم القديم على :8000**: عملية uvicorn قديمة كانت تعمل قبل التحديث؛ المستخدم يشغلها يدوياً — ذكّرها بإعادة التشغيل لالتقاط النقاط الجديدة.
3. **الرفع إلى Postgres/إنتاج**: `docker-compose.yml` موجود لكن غير مختبر هنا. `scripts/production_release.py` و`deploy/helm/` بانتظار المراجعة.
4. **تفاصيل UX متبقية** (من ملاحظات المالك نفسه): 
   - صفحة `/dashboard` (Portfolio) ما زالت demo data ثابتة — يجب ربطها بـGET /tenders.
   - `AgentFlowCanvas.AGENT_METAS` أسماء الوكلاء ثابتة فيه — يجب سحبها من `/agents` حتى تنعكس إعادة التسمية على اللوحة الحية.
   - توطين الواجهة (عربي RTL كامل) لم يُطبق إلا جزئياً في الرسائل.
5. **أمان**: JWT secret ثابت في `app/core/security.py` و`api_client.ts` (dev only) — يجب نقله لـenv قبل أي نشر.

## 5) أوامر سريعة

```bash
# نقرة واحدة للمستخدم: ConTech.bat على سطح المكتب (يشغل ويفتح المتصفح)

# اختبار كل شيء
.venv/Scripts/python.exe -m pytest tests/ -q -p no:cacheprovider

# تشغيل البيئة (Docker — بيئة التشغيل الفعلية)
docker compose up -d            # frontend:3000 + backend:8000 + postgres/qdrant/redis

# بعد أي تعديل على الكود (إعادة بناء الصور ثم تشغيل)
docker compose build backend frontend && docker compose up -d

# بديل التطوير المحلي السريع (بدون Docker)
.venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
cd frontend && npm run dev      # http://localhost:3000

# فحص الواجهة statically
cd frontend && npx tsc --noEmit
```

## 6) مبادئ التصميم المتبناها (لا تخرقها)

- **لا شيء ثابت في الكود يمثل بيانات مستخدم**: عملاء، منافسات، أسماء وكلاء — كلها DB.
- **الحذف يتطلب تأكيداً صريحاً ويمسح كل الطبقات** (DB + vectors + disk).
- **التعديل لا يُحفظ بالصدفة**: حفظ صريح + تراجع، والتجربة لا تخزن شيئاً.
- **الأخطاء قابلة للتنفيذ**: رسائل عربية تقول للمستخدم ماذا يفعل (409 المزود مثالاً).
- **كل سلوك جديد له اختبار حماية** في `test_dynamic_workspaces.py`.
