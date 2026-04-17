"""
Строит графики обучения классификатора глаз из CSV лога.

CSV создаётся скриптом:
  python -m src.training.train_eye_classifier --data-root <prepared_dataset> --output models/eye_state_resnet18.pth

По умолчанию лог будет рядом с весами: models/eye_state_resnet18.csv

Запуск:
  python scripts/plot_eye_training_from_csv.py --csv models/eye_state_resnet18.csv --out-dir assets
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont


def _load_rows(csv_path: Path) -> Tuple[str, List[int], List[float], List[float], List[float], List[float]]:
    model_name = "model"
    epochs: List[int] = []
    train_loss: List[float] = []
    train_acc: List[float] = []
    val_loss: List[float] = []
    val_acc: List[float] = []
    with csv_path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            model_name = row.get("model", model_name) or model_name
            epochs.append(int(row["epoch"]))
            train_loss.append(float(row["train_loss"]))
            train_acc.append(float(row["train_acc"]))
            val_loss.append(float(row["val_loss"]))
            val_acc.append(float(row["val_acc"]))
    return model_name, epochs, train_loss, train_acc, val_loss, val_acc


def _line_plot(
    xs: List[int],
    y1: List[float],
    y2: List[float],
    title: str,
    y_label: str,
    legend1: str,
    legend2: str,
    out_path: Path,
) -> None:
    w, h = 1200, 675
    pad = 80
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    # Базовый шрифт (если нет — Pillow подставит дефолт)
    try:
        font_title = ImageFont.truetype("arial.ttf", 34)
        font = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font_title = ImageFont.load_default()
        font = ImageFont.load_default()

    # Заголовок
    d.text((pad, 20), title, fill=(0, 0, 0), font=font_title)
    # Оси
    x0, y0 = pad, h - pad
    x1p, y1p = w - pad, pad + 40
    d.line((x0, y0, x1p, y0), fill=(40, 40, 40), width=3)
    d.line((x0, y0, x0, y1p), fill=(40, 40, 40), width=3)
    d.text((20, pad + 40), y_label, fill=(0, 0, 0), font=font)

    if not xs:
        img.save(out_path)
        return

    # Нормализация
    ymin = min(min(y1), min(y2))
    ymax = max(max(y1), max(y2))
    if abs(ymax - ymin) < 1e-9:
        ymax = ymin + 1.0
    xmin, xmax = min(xs), max(xs)
    if xmin == xmax:
        xmax = xmin + 1

    def map_x(x: int) -> float:
        return x0 + (x - xmin) / (xmax - xmin) * (x1p - x0)

    def map_y(y: float) -> float:
        return y0 - (y - ymin) / (ymax - ymin) * (y0 - y1p)

    # Сетка по Y
    for k in range(6):
        yy = y1p + k * (y0 - y1p) / 5
        d.line((x0, yy, x1p, yy), fill=(230, 230, 230), width=1)

    # Легенда
    c1 = (0, 113, 227)  # синий
    c2 = (40, 167, 69)  # зелёный
    lx, ly = w - pad - 360, pad + 10
    d.rectangle((lx, ly, lx + 20, ly + 20), fill=c1)
    d.text((lx + 28, ly - 2), legend1, fill=(0, 0, 0), font=font)
    d.rectangle((lx, ly + 32, lx + 20, ly + 52), fill=c2)
    d.text((lx + 28, ly + 30), legend2, fill=(0, 0, 0), font=font)

    def draw_series(ys: List[float], color) -> None:
        pts = [(map_x(x), map_y(y)) for x, y in zip(xs, ys)]
        for i in range(1, len(pts)):
            d.line((pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1]), fill=color, width=4)
        for px, py in pts:
            d.ellipse((px - 5, py - 5, px + 5, py + 5), fill=color)

    draw_series(y1, c1)
    draw_series(y2, c2)
    img.save(out_path)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Путь к CSV логу (epoch, train_loss, train_acc, val_loss, val_acc)")
    ap.add_argument("--out-dir", default="assets", help="Куда сохранить png")
    args = ap.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_name, xs, tr_l, tr_a, va_l, va_a = _load_rows(csv_path)
    _line_plot(
        xs,
        tr_a,
        va_a,
        title=f"{model_name}: Accuracy по эпохам",
        y_label="Accuracy",
        legend1="train_accuracy",
        legend2="val_accuracy",
        out_path=out_dir / f"{model_name}_accuracy.png",
    )
    _line_plot(
        xs,
        tr_l,
        va_l,
        title=f"{model_name}: Loss по эпохам",
        y_label="Cross-entropy loss",
        legend1="train_loss",
        legend2="val_loss",
        out_path=out_dir / f"{model_name}_loss.png",
    )
    print("Готово:", out_dir)


if __name__ == "__main__":
    main()

