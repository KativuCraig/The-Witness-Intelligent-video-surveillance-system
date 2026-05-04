from dataclasses import dataclass
from typing import Optional


@dataclass
class DetectionResult:
    """
    Standard result returned by any detection model.
    """

    label: Optional[str]          # VIOLENCE | WEAPON | THEFT | None
    confidence: float             # 0.0 - 1.0
    timestamp: float              # seconds in video
    frame_path: Optional[str]     # saved frame path (if any)
