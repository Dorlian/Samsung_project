"""
Собирает итоговую статистику по двум моделям из CSV логов
и рисует сводный png для презентации.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from PIL import Image, ImageDraw, ImageFont


def read_last_row(csv_path: Path) -> Dict[str, str]:
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Пустой CSV: {csv_path}")
    return rows[-1]


def draw_summary(rows: list[dict[str, str]], out_path: Path) -> None:
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        title_font = ImageFont.load_default()
        font = ImageFont.load_default()

    d.text((60, 40), "Сравнение моделей open/closed eyes", fill="black", font=title_font)
    headers = ["Модель", "Epoch", "Train acc", "Val acc", "Train loss", "Val loss"]
    xs = [60, 300, 450, 620, 800, 1010]
    y0 = 140
    for x, htext in zip(xs, headers):
        d.text((x, y0), htext, fill=(30, 30, 30), font=font)
    d.line((60, y0 + 40, 1180, y0 + 40), fill=(0, 0, 0), width=2)

    for i, row in enumerate(rows):
        y = y0 + 70 + i * 90
        vals = [
            row["model"],
            row["epoch"],
            row["train_acc"],
            row["val_acc"],
            row["train_loss"],
            row["val_loss"],
        ]
        for x, v in zip(xs, vals):
            d.text((x, y), str(v), fill=(0, 0, 0), font=font)

    img.save(out_path)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", nargs="+", required=True, help="Список CSV логов моделей")
    ap.add_argument("--out", default="assets/eye_models_summary.png")
    args = ap.parse_args()

    rows = [read_last_row(Path(p)) for p in args.csv]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    draw_summary(rows, out)
    print("Готово:", out)


if __name__ == "__main__":
    main()

