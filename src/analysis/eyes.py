"""
Закрытые глаза: Face Landmarker blendshapes (eyeBlink_L/R); при наличии весов — доп. проверка ResNet-CNN.
PHOTOASSISTANT_EYE_CLOSED_CHECK=0 принудительно отключает CNN; =1 включает независимо от настроек.
"""
from enum import Enum
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, List, Optional, Tuple
import urllib.request

import cv2
import numpy as np
from PIL import Image

from src.config.settings import AppSettings
from src.models.eye_classifier import EyeStateClassifier

# Официальная модель Face Landmarker (Tasks API), ~3.5 МБ
_FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)


class EyesReason(Enum):
    OK = "глаза открыты"
    CLOSED = "закрытые глаза"
    NO_FACE = "лица не обнаружены (кадр без людей)"
    DETECTION_ERROR = "ошибка детекции глаз"


# «Спасение»: хотя бы один глаз с p(открыт) ≥ этого — точно не бракуем
RESCUE_MIN_OPEN_PROB = 0.28
# Сумма p(открыт) по двум глазам — отсекает ложные «оба закрыты» при слабых, но положительных ответах на открытые глаза
RESCUE_SUM_PROB_MIN = 0.38
# Брак только если оба глаза ниже этого (очень уверенно «закрыт»)
CNN_BOTH_MUST_BE_BELOW = 0.13
# Один кроп глаза (профиль)
CNN_SINGLE_MUST_BE_BELOW = 0.09

_LEFT_EYE_LM_IDX = [33, 133, 159, 145, 153, 154, 155, 246]
_RIGHT_EYE_LM_IDX = [362, 263, 386, 374, 380, 381, 382, 466]
# OpenCV-пары: те же идеи
OPENCV_RESCUE_MAX = 0.30
OPENCV_RESCUE_SUM = 0.50
OPENCV_BOTH_MUST_BE_BELOW = 0.15

# Оба «моргания» выше порога → веки сомкнуты (0–1). Выше — меньше ложных «закрыто».
BLINK_BOTH_CLOSED_MIN = 0.52
# Хотя бы один глаз ниже — считаем не полное смыкание (профиль / один приоткрыт)
BLINK_AT_LEAST_ONE_OPEN_MAX = 0.38

def _cnn_allowed_by_env_and_settings(settings: AppSettings) -> bool:
    v = os.environ.get("PHOTOASSISTANT_EYE_CLOSED_CHECK", "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    if v in ("1", "true", "yes", "on"):
        return True
    return settings.use_cnn_eye_check


def _create_face_mesh_legacy():
    """Старый API (mediapipe < 0.10)."""
    try:
        import mediapipe as mp  # type: ignore

        if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
            return mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=5,
                refine_landmarks=True,
            )
    except Exception:
        pass
    return None


def _ensure_landmarker_model(models_dir: Path) -> Optional[Path]:
    path = models_dir / "face_landmarker.task"
    if path.exists() and path.stat().st_size > 10_000:
        return path
    models_dir.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(_FACE_LANDMARKER_URL, path)
    except Exception:
        return None
    if path.exists() and path.stat().st_size > 10_000:
        return path
    return None


class _FaceLandmarkerWrapper:
    """Обёртка под тот же интерфейс, что и FaceMesh.process(rgb) → multi_face_landmarks."""

    def __init__(self, model_path: Path) -> None:
        import mediapipe as mp  # type: ignore
        from mediapipe.tasks.python import vision  # type: ignore
        from mediapipe.tasks.python.core import base_options as base_opt  # type: ignore

        opts = vision.FaceLandmarkerOptions(
            base_options=base_opt.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=5,
            min_face_detection_confidence=0.2,
            min_face_presence_confidence=0.2,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=False,
        )
        self._mp = mp
        self._detector = vision.FaceLandmarker.create_from_options(opts)

    def process(self, rgb: np.ndarray) -> Any:
        rgb = np.ascontiguousarray(rgb)
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        res = self._detector.detect(mp_image)
        if not res.face_landmarks:
            return SimpleNamespace(multi_face_landmarks=[], face_blendshapes=[])

        faces = []
        for face_lms in res.face_landmarks:
            lm = [SimpleNamespace(x=p.x, y=p.y, z=float(getattr(p, "z", 0.0))) for p in face_lms]
            faces.append(SimpleNamespace(landmark=lm))

        blend_per_face: List[dict] = []
        if getattr(res, "face_blendshapes", None):
            for fb_list in res.face_blendshapes:
                blend_per_face.append({b.category_name: float(b.score) for b in fb_list})
        while len(blend_per_face) < len(faces):
            blend_per_face.append({})

        return SimpleNamespace(multi_face_landmarks=faces, face_blendshapes=blend_per_face)

    def close(self) -> None:
        try:
            self._detector.close()
        except Exception:
            pass


def _create_mediapipe_face_detector(models_dir: Path) -> Any:
    """Сначала legacy FaceMesh, иначе Tasks Face Landmarker + скачивание модели."""
    legacy = _create_face_mesh_legacy()
    if legacy is not None:
        return legacy
    model_path = _ensure_landmarker_model(models_dir)
    if model_path is None:
        return None
    try:
        return _FaceLandmarkerWrapper(model_path)
    except Exception:
        return None


def _largest_face_index(multi_face_landmarks: List[Any]) -> int:
    best_i, best_a = 0, 0.0
    for i, face in enumerate(multi_face_landmarks):
        lm = face.landmark
        xs = [p.x for p in lm]
        ys = [p.y for p in lm]
        a = (max(xs) - min(xs)) * (max(ys) - min(ys))
        if a > best_a:
            best_a, best_i = a, i
    return best_i


def _blink_left_right(blend: dict) -> Tuple[Optional[float], Optional[float]]:
    """Стандарт Face Landmarker: eyeBlink_L, eyeBlink_R (0=открыт, ~1=закрыт)."""
    bl = br = None
    for k, v in blend.items():
        if k == "eyeBlink_L" or k == "eyeBlinkLeft":
            bl = float(v)
        elif k == "eyeBlink_R" or k == "eyeBlinkRight":
            br = float(v)
    return bl, br


def _eyes_closed_from_blendshapes(blend: dict) -> bool:
    if not blend:
        return False
    bl, br = _blink_left_right(blend)
    if bl is None or br is None:
        return False
    if min(bl, br) < BLINK_AT_LEAST_ONE_OPEN_MAX:
        return False
    return bl >= BLINK_BOTH_CLOSED_MIN and br >= BLINK_BOTH_CLOSED_MIN


def _cnn_says_both_eyes_closed(probs: List[float]) -> bool:
    """Ложные срабатываний меньше: сначала спасение, потом только жёсткое «оба закрыты»."""
    if not probs:
        return False
    if len(probs) >= 2:
        if max(probs) >= RESCUE_MIN_OPEN_PROB:
            return False
        if sum(probs) >= RESCUE_SUM_PROB_MIN:
            return False
        return all(p < CNN_BOTH_MUST_BE_BELOW for p in probs)
    return probs[0] < CNN_SINGLE_MUST_BE_BELOW


def _crop_eye_region(rgb, w: int, h: int, indices: List[int], lm) -> Optional[Image.Image]:
    xs = [lm[i].x * w for i in indices]
    ys = [lm[i].y * h for i in indices]
    min_x = max(int(min(xs)) - 8, 0)
    max_x = min(int(max(xs)) + 8, w - 1)
    min_y = max(int(min(ys)) - 8, 0)
    max_y = min(int(max(ys)) + 8, h - 1)
    if max_x <= min_x or max_y <= min_y:
        return None
    region = rgb[min_y:max_y, min_x:max_x]
    if region.size == 0:
        return None
    return Image.fromarray(region)


def _load_face_cascade():
    p = cv2.data.haarcascades + "haarcascade_frontalface_alt2.xml"
    c = cv2.CascadeClassifier(p)
    if c.empty():
        return None
    return c


def _gray_for_detection(bgr: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _opencv_eye_zone_pairs(bgr: np.ndarray) -> Tuple[List[Tuple[Image.Image, Image.Image]], int]:
    """
    На каждое найденное лицо — пара (левая зона, правая зона), если обе валидны.
    """
    cascade = _load_face_cascade()
    if cascade is None:
        return [], 0
    h, w = bgr.shape[:2]
    gray = _gray_for_detection(bgr)
    min_side = max(60, min(w, h) // 12)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(min_side, min_side))
    pairs: List[Tuple[Image.Image, Image.Image]] = []
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    for x, y, fw, fh in faces:
        x, y = max(0, x), max(0, y)
        fw, fh = min(fw, w - x), min(fh, h - y)
        if fw < 40 or fh < 40:
            continue
        y0 = y + int(fh * 0.18)
        y1 = y + int(fh * 0.58)
        xl0, xl1 = x + int(fw * 0.05), x + int(fw * 0.48)
        xr0, xr1 = x + int(fw * 0.52), x + int(fw * 0.95)

        def grab(xa, xb):
            xa, xb = max(0, xa), min(w, xb)
            ya, yb = max(0, y0), min(h, y1)
            if xb - xa < 16 or yb - ya < 16:
                return None
            patch = rgb[ya:yb, xa:xb]
            return Image.fromarray(patch) if patch.size else None

        left = grab(xl0, xl1)
        right = grab(xr0, xr1)
        if left is not None and right is not None:
            pairs.append((left, right))
    return pairs, len(faces)


class EyeStateAnalyzer:
    """mediapipe_active — работает ли детекция лица через Mediapipe (legacy или Face Landmarker)."""

    def __init__(self) -> None:
        models_dir = Path("models")
        self.face_mesh = _create_mediapipe_face_detector(models_dir)
        self.mediapipe_active = self.face_mesh is not None
        self._face_landmarker = isinstance(self.face_mesh, _FaceLandmarkerWrapper)
        self.uses_blendshape_eye_closure = self._face_landmarker

        self._cached_classifier: Optional[EyeStateClassifier] = None
        self._cached_weights_path: Optional[str] = None

    def _ensure_classifier(self, settings: AppSettings) -> Optional[EyeStateClassifier]:
        if not _cnn_allowed_by_env_and_settings(settings):
            return None
        path = Path(settings.eye_classifier_weights)
        if not path.is_file():
            return None
        key = str(path.resolve())
        if self._cached_classifier is not None and self._cached_weights_path == key:
            return self._cached_classifier
        self._cached_classifier = EyeStateClassifier(weights_path=path)
        self._cached_weights_path = key
        return self._cached_classifier

    def _mediapipe_pass(
        self, rgb, w: int, h: int, classifier: Optional[EyeStateClassifier]
    ) -> Tuple[bool, bool, List[Image.Image]]:
        """
        Returns: (had_any_face, closed_eyes, _)
        Брак только если CNN считает оба глаза закрытыми (с учётом спасения по max/sum prob).
        """
        if self.face_mesh is None:
            return False, False, []
        results = self.face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return False, False, []

        if classifier is None:
            return True, False, []
        try:
            for face_landmarks in results.multi_face_landmarks:
                lm = face_landmarks.landmark
                left_c = _crop_eye_region(rgb, w, h, _LEFT_EYE_LM_IDX, lm)
                right_c = _crop_eye_region(rgb, w, h, _RIGHT_EYE_LM_IDX, lm)
                probs: List[float] = []
                if left_c is not None:
                    _, p = classifier.predict_label(left_c)
                    probs.append(p)
                if right_c is not None:
                    _, p = classifier.predict_label(right_c)
                    probs.append(p)

                if _cnn_says_both_eyes_closed(probs):
                    return True, True, []
        except Exception:
            return True, False, []

        return True, False, []

    def _opencv_faces_both_zones_closed(self, bgr: np.ndarray, classifier: Optional[EyeStateClassifier]) -> bool:
        if classifier is None:
            return False
        pairs, _ = _opencv_eye_zone_pairs(bgr)
        try:
            for left, right in pairs:
                _, p0 = classifier.predict_label(left)
                _, p1 = classifier.predict_label(right)
                if max(p0, p1) >= OPENCV_RESCUE_MAX:
                    continue
                if p0 + p1 >= OPENCV_RESCUE_SUM:
                    continue
                if p0 < OPENCV_BOTH_MUST_BE_BELOW and p1 < OPENCV_BOTH_MUST_BE_BELOW:
                    return True
        except Exception:
            return False
        return False

    def are_eyes_ok(self, image_path: Path, settings: AppSettings | None = None) -> Tuple[bool, EyesReason]:
        s = settings or AppSettings()
        clf = self._ensure_classifier(s)

        image_bgr = cv2.imread(str(image_path))
        if image_bgr is None:
            return False, EyesReason.DETECTION_ERROR

        h, w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

        # Face Landmarker: blendshapes + при наличии весов — доп. CNN по кропам глаз
        if self._face_landmarker and self.face_mesh is not None:
            r = self.face_mesh.process(rgb)
            if r.multi_face_landmarks:
                idx = _largest_face_index(r.multi_face_landmarks)
                blends = getattr(r, "face_blendshapes", []) or []
                bd = blends[idx] if idx < len(blends) else {}
                if _eyes_closed_from_blendshapes(bd):
                    return False, EyesReason.CLOSED
                if clf is not None:
                    try:
                        lm = r.multi_face_landmarks[idx].landmark
                        left_c = _crop_eye_region(rgb, w, h, _LEFT_EYE_LM_IDX, lm)
                        right_c = _crop_eye_region(rgb, w, h, _RIGHT_EYE_LM_IDX, lm)
                        probs: List[float] = []
                        if left_c is not None:
                            _, p = clf.predict_label(left_c)
                            probs.append(p)
                        if right_c is not None:
                            _, p = clf.predict_label(right_c)
                            probs.append(p)
                        if _cnn_says_both_eyes_closed(probs):
                            return False, EyesReason.CLOSED
                    except Exception:
                        pass
                return True, EyesReason.OK
            _pairs, n_cv = _opencv_eye_zone_pairs(image_bgr)
            if n_cv > 0 or len(_pairs) > 0:
                return True, EyesReason.OK
            return False, EyesReason.NO_FACE

        if clf is None:
            if self.face_mesh is not None:
                r = self.face_mesh.process(rgb)
                if r.multi_face_landmarks:
                    return True, EyesReason.OK
            _pairs, n_cv = _opencv_eye_zone_pairs(image_bgr)
            if n_cv > 0 or len(_pairs) > 0:
                return True, EyesReason.OK
            return False, EyesReason.NO_FACE

        had_mp, closed_mp, _ = self._mediapipe_pass(rgb, w, h, clf)
        if closed_mp:
            return False, EyesReason.CLOSED

        # Если лицо уже нашли через Mediapipe и глаза прошли — не гоняем CNN по грубым зонам OpenCV
        # (они дают массу ложных «закрыто» на открытых глазах).
        closed_cv = False
        pairs, n_cv_faces = _opencv_eye_zone_pairs(image_bgr)
        if not had_mp:
            closed_cv = self._opencv_faces_both_zones_closed(image_bgr, clf)
            had_cv = n_cv_faces > 0 or len(pairs) > 0
        else:
            had_cv = False

        if closed_cv:
            return False, EyesReason.CLOSED

        had_face = had_mp or had_cv
        if not had_face:
            return False, EyesReason.NO_FACE

        return True, EyesReason.OK
