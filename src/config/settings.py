from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


SETTINGS_FILE = Path("app_settings.json")


@dataclass
class AppSettings:
    exposure_low_thresh: int = 10
    exposure_high_thresh: int = 245
    exposure_extreme_fraction: float = 0.10
    sharpness_threshold: float = 80.0
    # Доп. проверка закрытых глаз обученной MediaPipe (по умолчанию выкл. — стабильнее только MediaPipe)
    use_cnn_eye_check: bool = False
    eye_classifier_weights: str = "models/eye_state_mediapipe.pth"


def load_settings() -> AppSettings:
    if not SETTINGS_FILE.exists():
        return AppSettings()
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return AppSettings(
            exposure_low_thresh=int(raw.get("exposure_low_thresh", 10)),
            exposure_high_thresh=int(raw.get("exposure_high_thresh", 245)),
            exposure_extreme_fraction=float(raw.get("exposure_extreme_fraction", 0.10)),
            sharpness_threshold=float(raw.get("sharpness_threshold", 80.0)),
            use_cnn_eye_check=bool(raw.get("use_cnn_eye_check", False)),
            eye_classifier_weights=str(raw.get("eye_classifier_weights", "models/eye_state_resnet18.pth")),
        )
    except Exception:
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    SETTINGS_FILE.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")

