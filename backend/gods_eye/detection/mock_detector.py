import random
from .base import BaseCrimeDetector
from .contracts import DetectionResult


class MockCrimeDetector(BaseCrimeDetector):
    """
    Fake detector used until ML model is integrated.
    """

    INCIDENTS = [
        ("VIOLENCE", 0.85),
        ("WEAPON", 0.90),
        ("THEFT", 0.80),
        (None, 0.0),
    ]

    def analyze_frame(self, frame, timestamp: float) -> DetectionResult:
        label, confidence = random.choice(self.INCIDENTS)

        return DetectionResult(
            label=label,
            confidence=confidence,
            timestamp=timestamp,
            frame_path=None
        )
