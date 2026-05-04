from abc import ABC, abstractmethod
from .contracts import DetectionResult


class BaseCrimeDetector(ABC):
    """
    Abstract base class for all crime detectors.
    """

    @abstractmethod
    def analyze_frame(self, frame, timestamp: float) -> DetectionResult:
        pass
