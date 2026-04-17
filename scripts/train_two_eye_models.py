"""
Последовательно обучает две модели для open/closed eyes:
- ResNet-18
- MobileNetV3-Small

Также сохраняет отдельные CSV логи, чтобы потом построить графики для презентации.

Пример:
  python scripts/train_two_eye_models.py --data-root training/data/prepared --epochs 6
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--models-dir", default="models")
    ap.add_argument("--max-train", type=int, default=8000, help="Подвыборка для быстрого обучения (0 = без ограничения)")
    ap.add_argument("--max-val", type=int, default=2000, help="Подвыборка для быстрого обучения (0 = без ограничения)")
    args = ap.parse_args()

    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    jobs = [
        (
            "resnet18",
            models_dir / "eye_state_resnet18.pth",
            models_dir / "eye_state_resnet18.csv",
        ),
        (
            "mobilenetv3",
            models_dir / "eye_state_mobilenetv3.pth",
            models_dir / "eye_state_mobilenetv3.csv",
        ),
    ]

    for model_name, weights_path, csv_path in jobs:
        run(
            [
                py,
                "-m",
                "src.training.train_eye_classifier",
                "--data-root",
                args.data_root,
                "--model",
                model_name,
                "--output",
                str(weights_path),
                "--log-csv",
                str(csv_path),
                "--epochs",
                str(args.epochs),
                "--batch-size",
                str(args.batch_size),
                "--lr",
                str(args.lr),
                "--max-train",
                str(args.max_train),
                "--max-val",
                str(args.max_val),
            ]
        )

    print("Готово. Веса и логи сохранены в", models_dir)


if __name__ == "__main__":
    main()

