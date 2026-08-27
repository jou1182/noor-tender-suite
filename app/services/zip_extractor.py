"""ZIP extraction service — استخراج أرشيفات الكراسات تلقائياً.

يُفكّ ملف ZIP المرفوع إلى ملفاته الأصلية داخل مجلد المنافسة، ويسجّل كل
ملف مستخرج كمستند مستقل — مع حواجز أمان:
- حد حجم غير مضغوط (zip bomb)
- رفض المسارات الخادعة (path traversal داخل الأرشيف)
- حد عدد الملفات
- تجاهل ملفات النظام غير المفيدة (__MACOSX، .DS_Store، مجلدات فارغة)

ومع سياسة التخزين النظيف: الأرشيف الأصلي يُحذف بعد الاستخراج الناجح
(لا تضاعف تخزين نفس البيانات) — ويمكن تعطيل ذلك بـkeep_archive=True.
"""

import os
import zipfile
from typing import Any, Dict, List, Tuple

MAX_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024  # 2GB بعد الفك
MAX_FILES_PER_ARCHIVE = 500
JUNK_PREFIXES = ("__MACOSX/", "__MACOSX\\")
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

ALLOWED_EXTS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".txt", ".md", ".csv",
    ".dxf", ".dwg", ".rvt", ".ifc", ".xer",
}


def _is_junk(name: str) -> bool:
    base = os.path.basename(name)
    return (
        base in JUNK_NAMES
        or name.startswith(JUNK_PREFIXES)
        or base.startswith("._")
        or not base  # مداخل مجلدات
    )


def safe_extract_zip(
    zip_path: str,
    dest_dir: str,
    keep_archive: bool = False,
) -> Tuple[List[str], List[str], Dict[str, Any]]:
    """يفكّ الأرشيف بأمان. يرجع (extracted_paths, skipped, stats).

    extracted_paths: مسارات الملفات الصالحة المستخرجة
    skipped: أسماء تجاهلناها (نوع غير مدعوم / عناصر نفايات)
    stats: {total_uncompressed, files_extracted, files_skipped, original_deleted}
    """
    extracted: List[str] = []
    skipped: List[str] = []
    total_uncompressed = 0
    os.makedirs(dest_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if len(names) > MAX_FILES_PER_ARCHIVE:
            raise ValueError(f"الأرشيف يحوي {len(names)} ملفاً — الحد {MAX_FILES_PER_ARCHIVE}")

        # فحص الحجم غير المضغوط قبل الفك (حماية zip bomb)
        for info in zf.infolist():
            total_uncompressed += info.file_size
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ValueError(f"الحجم بعد الفك يتجاوز الحد ({total_uncompressed // (1024*1024)}MB)")

        for info in zf.infolist():
            name = info.filename
            if info.is_dir() or _is_junk(name):
                continue
            base = os.path.basename(name)
            ext = os.path.splitext(base)[1].lower()
            if ext not in ALLOWED_EXTS:
                skipped.append(name)
                continue

            # منع path traversal: الاسم النهائي basename فقط داخل dest_dir
            safe_name = base.replace(" ", "_")
            dest = os.path.realpath(os.path.join(dest_dir, safe_name))
            if not dest.startswith(os.path.realpath(dest_dir) + os.sep):
                skipped.append(name)
                continue

            # تجنّب الكتابة فوق ملف بنفس الاسم: لاحقة رقمية
            final = dest
            i = 1
            while os.path.exists(final):
                stem, e = os.path.splitext(dest)
                final = f"{stem}_{i}{e}"
                i += 1

            with zf.open(info) as source, open(final, "wb") as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            extracted.append(final)

    # سياسة التخزين النظيف: الأرشيف الأصلي يُحذف بعد نجاح الفك (منع تضاعف الحجم)
    original_deleted = False
    if extracted and not keep_archive:
        try:
            os.remove(zip_path)
            original_deleted = True
        except OSError:
            pass

    return extracted, skipped, {
        "total_uncompressed": total_uncompressed,
        "files_extracted": len(extracted),
        "files_skipped": len(skipped),
        "original_deleted": original_deleted,
    }


# ------------------------------------------------------------ adapter API ---

def is_zip(filename: str) -> bool:
    """هل اسم الملف أرشيف ZIP؟ (يُستخدم في نقطة الرفع قبل الحفص)."""
    return (filename or "").lower().endswith(".zip")


def extract_zip_to_docs(zip_path: str, dest_dir: str) -> Dict[str, Any]:
    """غلاف متوافق مع نقطة الرفع: يلفّ safe_extract_zip في قاموس واحد.

    يرجع: {accepted: [paths], error: str|None, stats: {...}}
    عند فشل كامل (لا ملفات صالحة) يُرفع error مع بقاء accepted فارغاً.
    """
    try:
        extracted, skipped, stats = safe_extract_zip(zip_path, dest_dir, keep_archive=False)
    except ValueError as exc:
        return {"accepted": [], "error": str(exc), "stats": {}}
    except Exception as exc:  # noqa: BLE001 — أرشيف تالف/مقفل
        return {"accepted": [], "error": f"ZIP extraction failed: {exc}", "stats": {}}

    return {
        "accepted": extracted,
        "error": None if extracted else "لا ملفات صالحة داخل الأرشيف",
        "stats": {**stats, "skipped": skipped},
    }
