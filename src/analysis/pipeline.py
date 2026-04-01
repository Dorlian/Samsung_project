from dataclasses import dataclass
from pathlib import Path

from src.config.settings import AppSettings

from .exposure import is_exposure_ok, ExposureReason
from .sharpness import is_sharp_enough, SharpnessReason
from .eyes import EyeStateAnalyzer, EyesReason


@dataclass
class AnalysisResult:
    is_good: bool
    reason: str


class PhotoAnalyzer:
    def __init__(self) -> None:
        self.eye_analyzer = EyeStateAnalyzer()

    def analyze(self, image_path: Path, settings: AppSettings | None = None) -> AnalysisResult:
        s = settings or AppSettings()
        # 1) Сначала глаза: закрытые глаза важнее, чем пересвет/недосвет по смыслу отбора.
        eyes_ok, eyes_reason = self.eye_analyzer.are_eyes_ok(image_path, settings=s)
        if not eyes_ok and eyes_reason == EyesReason.CLOSED:
            return AnalysisResult(is_good=False, reason=f"Глаза: {eyes_reason.value}")

        # 2) Экспозиция и резкость
        exposure_ok, exposure_reason = is_exposure_ok(
            image_path,
            low_thresh=s.exposure_low_thresh,
            high_thresh=s.exposure_high_thresh,
            extreme_fraction=s.exposure_extreme_fraction,
        )
        if not exposure_ok:
            return AnalysisResult(is_good=False, reason=f"Экспозиция: {exposure_reason.value}")

        sharp_ok, sharp_reason = is_sharp_enough(image_path, threshold=s.sharpness_threshold)
        if not sharp_ok:
            return AnalysisResult(is_good=False, reason=f"Резкость: {sharp_reason.value}")

        # 3) Лица не найдены — пейзаж/предметка при нормальном свете и резкости
        if not eyes_ok and eyes_reason == EyesReason.NO_FACE:
            return AnalysisResult(is_good=True, reason="Лица не обнаружены, резкость и экспозиция в норме")

        if not eyes_ok and eyes_reason == EyesReason.DETECTION_ERROR:
            return AnalysisResult(is_good=False, reason=f"Глаза: {eyes_reason.value}")

        return AnalysisResult(is_good=True, reason="Все проверки пройдены")

