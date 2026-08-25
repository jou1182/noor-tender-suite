"""
SBC-304 Structural Compliance Engine.

Deterministic engineering checks against the Saudi Building Code
(SBC 304 — Concrete Structures) for:

  - Concrete compressive strength (f'c)      -> SBC 304 §5.2 / Table 4.3.1
  - Water/cement ratio (w/c)                 -> SBC 304 §5.3
  - Rebar yield strength (fy)                -> SBC 304 §3.5.3
  - Minimum concrete cover                   -> SBC 304 Sec 7.7

Checks are exposure-class and placement-aware, returning an object-based
``SBC304CheckResult`` carrying a boolean compliance verdict plus explicit
violation/warning messages that can be surfaced to engineering reviews.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ExposureClass(str, Enum):
    """SBC 304 durability/exposure classes (Table 4.3.1)."""

    S1 = "S1"  # general / benign
    S2 = "S2"  # moderate sulfate / humidity
    S3 = "S3"  # severe sulfate
    S4 = "S4"  # very severe / aggressive


class PlacementContext(str, Enum):
    """SBC 304 Sec 7.7 placement/contact contexts (drives minimum cover)."""

    CAST_AGAINST_EARTH = "CAST_AGAINST_EARTH"
    INTERIOR = "INTERIOR"
    EXTERIOR = "EXTERIOR"
    CONTINUOUSLY_SUBMERGED = "CONTINUOUSLY_SUBMERGED"


# SBC 304 Table 4.3.1 — exposure-class concrete limits.
EXPOSURE_SPECS = {
    ExposureClass.S1: {"min_fc": 25.0, "max_wc": 0.45},
    ExposureClass.S2: {"min_fc": 31.0, "max_wc": 0.45},
    ExposureClass.S3: {"min_fc": 35.0, "max_wc": 0.40},
    ExposureClass.S4: {"min_fc": 40.0, "max_wc": 0.35},
}

# SBC 304 Sec 7.7 — minimum cover by placement context (mm).
PLACEMENT_COVER_MM = {
    PlacementContext.CAST_AGAINST_EARTH: 75.0,
    PlacementContext.INTERIOR: 20.0,
    PlacementContext.EXTERIOR: 40.0,
    PlacementContext.CONTINUOUSLY_SUBMERGED: 50.0,
}

# SBC 304 §3.5.3 — rebar yield strength limits.
REBAR_STANDARD_FY = (420.0, 550.0)  # Grade 60 / Grade 80
REBAR_MAX_FY = 550.0


@dataclass
class SBC304CheckResult:
    """Structured compliance verdict for an SBC 304 material check."""

    is_compliant: bool
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    min_fc_mpa: Optional[float] = None
    max_wc: Optional[float] = None
    max_fy_mpa: Optional[float] = None
    min_cover_mm: Optional[float] = None


class Sbc304Engine:
    """Deterministic SBC 304 rule checks."""

    @staticmethod
    def evaluate_mix(
        fc_mpa: float,
        wc: float,
        exposure_class: ExposureClass = ExposureClass.S1,
    ) -> SBC304CheckResult:
        """SBC 304 §5.2/§5.3 — f'c minimum and w/c maximum per exposure class."""
        spec = EXPOSURE_SPECS[exposure_class]
        violations: List[str] = []
        if fc_mpa < spec["min_fc"]:
            violations.append(
                f"f'c {fc_mpa} MPa below SBC 304 requirement: >= {spec['min_fc']} MPa "
                f"(ExposureClass {exposure_class.value})"
            )
        if wc > spec["max_wc"]:
            violations.append(
                f"w/c {wc} exceeds SBC 304 limit: <= {spec['max_wc']} "
                f"(ExposureClass {exposure_class.value})"
            )
        return SBC304CheckResult(
            is_compliant=not violations,
            violations=violations,
            min_fc_mpa=spec["min_fc"],
            max_wc=spec["max_wc"],
        )

    @staticmethod
    def evaluate_rebar(fy_mpa: float) -> SBC304CheckResult:
        """SBC 304 §3.5.3 — fy must be a standard grade and <= 550 MPa."""
        warnings: List[str] = []
        violations: List[str] = []
        if fy_mpa not in REBAR_STANDARD_FY:
            warnings.append(
                f"fy {fy_mpa} MPa is a non-standard grade "
                f"(SBC 304 §3.5.3 standard grades: {', '.join(str(g) for g in REBAR_STANDARD_FY)} MPa)"
            )
        if fy_mpa > REBAR_MAX_FY:
            violations.append(
                f"fy {fy_mpa} MPa exceeds SBC 304 §3.5.3 maximum: <= {REBAR_MAX_FY} MPa"
            )
        return SBC304CheckResult(
            is_compliant=not violations,
            violations=violations,
            warnings=warnings,
            max_fy_mpa=REBAR_MAX_FY,
        )

    @staticmethod
    def evaluate_cover(
        cover_depth_mm: float,
        placement: PlacementContext = PlacementContext.EXTERIOR,
    ) -> SBC304CheckResult:
        """SBC 304 Sec 7.7 — minimum concrete cover by placement context."""
        min_cover = PLACEMENT_COVER_MM[placement]
        violations: List[str] = []
        if cover_depth_mm < min_cover:
            violations.append(
                f"cover {cover_depth_mm} mm below SBC 304 Sec 7.7 minimum: >= {min_cover} mm "
                f"({placement.value})"
            )
        return SBC304CheckResult(
            is_compliant=not violations,
            violations=violations,
            min_cover_mm=min_cover,
        )

    @staticmethod
    def evaluate_material(
        fc_mpa: Optional[float] = None,
        wc: Optional[float] = None,
        fy_mpa: Optional[float] = None,
        cover_depth_mm: Optional[float] = None,
        exposure_class: ExposureClass = ExposureClass.S1,
        placement: PlacementContext = PlacementContext.EXTERIOR,
    ) -> SBC304CheckResult:
        """Aggregate all provided material properties into a single verdict."""
        violations: List[str] = []
        warnings: List[str] = []
        result_meta = {}

        if fc_mpa is not None and wc is not None:
            mix = Sbc304Engine.evaluate_mix(fc_mpa, wc, exposure_class)
            violations.extend(mix.violations)
            result_meta["min_fc_mpa"] = mix.min_fc_mpa
            result_meta["max_wc"] = mix.max_wc
        if fy_mpa is not None:
            rebar = Sbc304Engine.evaluate_rebar(fy_mpa)
            violations.extend(rebar.violations)
            warnings.extend(rebar.warnings)
            result_meta["max_fy_mpa"] = rebar.max_fy_mpa
        if cover_depth_mm is not None:
            cover = Sbc304Engine.evaluate_cover(cover_depth_mm, placement)
            violations.extend(cover.violations)
            result_meta["min_cover_mm"] = cover.min_cover_mm

        return SBC304CheckResult(
            is_compliant=not violations,
            violations=violations,
            warnings=warnings,
            **result_meta,
        )