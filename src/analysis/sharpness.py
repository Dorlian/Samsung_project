from enum import Enum
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


class SharpnessReason(Enum):
    OK = "резкость в норме"
    BLURRY = "смаз / размытое изображение"


def variance_of_laplacian(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def is_sharp_enough(image_path: Path, threshold: float = 80.0) -> Tuple[bool, SharpnessReason]:
    """
    Оценка резкости по дисперсии Лапласа.

    :param image_path: путь к изображению
    :param threshold: порог, ниже которого считаем кадр размытым
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return False, SharpnessReason.BLURRY

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    score = variance_of_laplacian(gray)

    if score < threshold:
        return False, SharpnessReason.BLURRY
    return True, SharpnessReason.OK

