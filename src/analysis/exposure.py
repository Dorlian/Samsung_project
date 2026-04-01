from enum import Enum
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


class ExposureReason(Enum):
    OK = "экспозиция в норме"
    OVEREXPOSED = "пересвет"
    UNDEREXPOSED = "недосвет"


def is_exposure_ok(image_path: Path, low_thresh: int = 10, high_thresh: int = 245,
                   extreme_fraction: float = 0.1) -> Tuple[bool, ExposureReason]:
    """
    Оценка экспозиции по распределению яркости (канал V в HSV).

    :param image_path: путь к изображению
    :param low_thresh: граница недосвета (0..255)
    :param high_thresh: граница пересвета (0..255)
    :param extreme_fraction: допустимая доля "выбитых" пикселей (0..1)
    """
    img = cv2.imread(str(image_path))
    if img is None:
        return False, ExposureReason.UNDEREXPOSED

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    v = hsv[:, :, 2]

    total_pixels = v.size
    if total_pixels == 0:
        return False, ExposureReason.UNDEREXPOSED

    over_mask = v >= high_thresh
    under_mask = v <= low_thresh

    over_frac = float(np.count_nonzero(over_mask)) / float(total_pixels)
    under_frac = float(np.count_nonzero(under_mask)) / float(total_pixels)

    if over_frac > extreme_fraction:
        return False, ExposureReason.OVEREXPOSED
    if under_frac > extreme_fraction:
        return False, ExposureReason.UNDEREXPOSED

    return True, ExposureReason.OK

