from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


SETTINGS_FILE = Path("app_settings.json")


@dataclass
class AppSettings:
    exposure_low_thresh: int = 10
    exposure_high_thresh: int = 245
    exposure_extreme_fraction: float = 0.10
    sharpness_threshold: float = 80.0
    # Доп. проверка закрытых глаз обученной ResNet (по умолчанию выкл. — стабильнее только MediaPipe)
    use_cnn_eye_check: bool = False
    eye_classifier_weights: str = "models/eye_state_resnet18.pth"


def sanitize_settings(s: AppSettings) -> AppSettings:
    """Те же границы, что при сохранении из UI; защита от битого/ручного app_settings.json."""
    low = max(0, min(80, int(s.exposure_low_thresh)))
    high = max(180, min(255, int(s.exposure_high_thresh)))
    if high <= low:
        low, high = 10, 245
    frac = float(s.exposure_extreme_fraction)
    if not math.isfinite(frac):
        frac = 0.10
    frac = max(0.01, min(0.35, frac))
    sharp = float(s.sharpness_threshold)
    if not math.isfinite(sharp):
        sharp = 80.0
    sharp = max(10.0, min(350.0, sharp))
    w = str(s.eye_classifier_weights).strip() or "models/eye_state_resnet18.pth"
    return AppSettings(
        exposure_low_thresh=low,
        exposure_high_thresh=high,
        exposure_extreme_fraction=frac,
        sharpness_threshold=sharp,
        use_cnn_eye_check=bool(s.use_cnn_eye_check),
        eye_classifier_weights=w,
    )


def load_settings() -> AppSettings:
    if not SETTINGS_FILE.exists():
        return AppSettings()
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        parsed = AppSettings(
            exposure_low_thresh=int(raw.get("exposure_low_thresh", 10)),
            exposure_high_thresh=int(raw.get("exposure_high_thresh", 245)),
            exposure_extreme_fraction=float(raw.get("exposure_extreme_fraction", 0.10)),
            sharpness_threshold=float(raw.get("sharpness_threshold", 80.0)),
            use_cnn_eye_check=bool(raw.get("use_cnn_eye_check", False)),
            eye_classifier_weights=str(raw.get("eye_classifier_weights", "models/eye_state_resnet18.pth")),
        )
    except Exception:
        return AppSettings()
    fixed = sanitize_settings(parsed)
    if (
        fixed.exposure_low_thresh != parsed.exposure_low_thresh
        or fixed.exposure_high_thresh != parsed.exposure_high_thresh
        or abs(fixed.exposure_extreme_fraction - parsed.exposure_extreme_fraction) > 1e-9
        or abs(fixed.sharpness_threshold - parsed.sharpness_threshold) > 1e-6
        or fixed.use_cnn_eye_check != parsed.use_cnn_eye_check
        or fixed.eye_classifier_weights != parsed.eye_classifier_weights
    ):
        save_settings(fixed)
    return fixed


def save_settings(settings: AppSettings) -> None:
    settings = sanitize_settings(settings)
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")

