"""
CAD Parser — DXF analytical extraction + DWG inventory registration.

  - DXF (text format): layers, blocks, text entities via ezdxf.
  - DWG (proprietary binary): inventory-only registration (requires external
    ODA File Converter for deep parsing — documented, not required).
"""

from typing import Any, Dict, List


def is_cad_file(filename: str) -> bool:
    lowered = (filename or "").lower()
    return lowered.endswith((".dxf", ".dwg"))


def extract_dxf_summary(dxf_path: str) -> Dict[str, Any]:
    """
    Analytical DXF extraction: layer names, block names, text entities,
    and entity-type counts. Raises on invalid DXF files.
    """
    import ezdxf

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    layers = sorted({layer.dxf.name for layer in doc.layers})
    blocks = sorted({block.name for block in doc.blocks if not block.name.startswith("*")})

    text_entities: List[str] = []
    entity_counts: Dict[str, int] = {}
    for entity in msp:
        dtype = entity.dxftype()
        entity_counts[dtype] = entity_counts.get(dtype, 0) + 1
        if dtype in ("TEXT", "MTEXT"):
            content = (entity.dxf.get("text", "") or "").strip()
            if content:
                text_entities.append(content[:200])

    return {
        "cad_type": "DXF",
        "layers": layers[:100],
        "layer_count": len(layers),
        "blocks": blocks[:60],
        "block_count": len(blocks),
        "entity_counts": entity_counts,
        "text_samples": text_entities[:40],
    }


def register_dwg(filename: str) -> Dict[str, Any]:
    """DWG inventory record (binary proprietary format — deep parse not supported)."""
    return {
        "cad_type": "DWG",
        "note": "DWG registered as inventory. Convert to DXF (ODA File Converter) for analytical extraction.",
        "layers": [],
        "blocks": [],
        "text_samples": [],
    }


def extract_cad_summary(file_path: str, filename: str) -> Dict[str, Any]:
    """Route DXF vs DWG."""
    lowered = (filename or "").lower()
    if lowered.endswith(".dxf"):
        return extract_dxf_summary(file_path)
    return register_dwg(filename)