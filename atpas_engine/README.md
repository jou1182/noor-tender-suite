# ATPAS Engine — مولد العروض الفنية (وحدة مدمجة)

محرك توليد العروض الفنية العربية من ATPAS، مدمج داخل منظومة النور كوحدة خدمية خلفية.

## ما تحتويه الوحدة

| العنصر | الوصف |
|---|---|
| `engine/` | محرك البناء كاملاً من ATPAS (builder, validator, resolver, style_applier, formatter…) — **كود أصلي غير معدّل** |
| `utils/` | الأدوات المطلوبة للمحرك فقط (content_library, docx_manipulator, image_processor, json_manager, company_profile) |
| `codes_registry.json` | سجل الأكواد الفنية SSOT — 70 كوداً (65 أساسياً + 5 مساندة حفر) |
| `master_config.json` | 6 أنواع مشاريع + 20 جهة مالكة + نطاقات الفئات (001–005) |
| `*_project_metadata.json` | بيانات تعريفية لكل نوع مشروع |
| `presets.json` | الأنماط الجاهزة (11) |
| `templates/style_templates/` | أنماط تنسيق 20 جهة مالكة |
| `company_profile.json` | هوية الناشر — شركة النور للمقاولات (كيان افتراضي للعرض) |

## مبدأ التكامل

الكود الأصلي لـ ATPAS **لا يُعدّل** — يُستدعى عبر محوّل رفيع يضيف مجلد هذه الوحدة إلى `sys.path`
(ملف `app/api/v1/endpoints/atpas.py`)، فيستورد `engine.builder.Builder` كما هو. هذا يحافظ على:
- سهولة مزامنة أي تحسينات مستقبلية من مستودع ATPAS المصدر.
- سلامة الـ 517 اختباراً الأصلية التي بُني المحرك عليها.

## واجهة الخدمة (REST)

- `GET  /api/v1/atpas/company` — هوية الشركة
- `GET  /api/v1/atpas/projects` — أنواع المشاريع الستة
- `GET  /api/v1/atpas/owners` — الجهات المالكة العشرون
- `GET  /api/v1/atpas/codes?project_id=wastewater` — الأكواد النشطة لمشروع
- `POST /api/v1/atpas/build` — توليد ملف Word `{project_id, owner_id, selected_codes[]}`

## ملاحظات

- ملفات المحتوى المرجعي (Word) لكل كود توضع في `templates/source_documents/` وقت التشغيل ولا تُرفع للمستودع.
- الأكواد الخمسة المساندة للحفر بلا ملفات Word بعد — تُولَّد كأقسام ذاتية المحتوى.
- الحد الأمني من ATPAS محفوظ: لا ملفات عميل حقيقية في المستودع أبداً.
