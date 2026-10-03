"""Arabic text repair for PDF extraction output."""

import re
import unicodedata

# Presentation Forms-A (FB50-FDFF) and -B (FE70-FEFF): glyph-shaped letters/ligatures that some
# PDFs yield instead of the base letters. They break keyword matching and cross-document search.
_PRESENTATION_FORMS = re.compile("[\uFB50-\uFDFF\uFE70-\uFEFF]+")


def fix_presentation_forms(text: str) -> str:
    """Map shaped Arabic glyphs back to base letters (ﻟﻠﻤﻨﺎﻓﺴﺔ -> للمنافسة). No-op for clean text."""
    if not text or not _PRESENTATION_FORMS.search(text):
        return text
    return _PRESENTATION_FORMS.sub(lambda m: unicodedata.normalize("NFKC", m.group(0)), text)
