"""
Быстрая подготовка MRL из zip напрямую в структуру train/val,
без полной распаковки архива в сырой каталог.
"""

from __future__ import annotations

import argparse
import random
import zipfile
from pathlib import Path


def parse_label_from_name(name: str) -> str | None:
    stem = Path(name).stem
    for part in stem.split("_"):
        if part == "0":
            return "closed"
        if part == "1":
            return "open"
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip-path", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--val-fraction", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    zip_path = Path(args.zip_path)
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(args.seed)

    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.namelist() if m.lower().endswith((".png", ".jpg", ".jpeg"))]
        items: list[tuple[str, str]] = []
        for m in members:
            label = parse_label_from_name(Path(m).name)
            if label is None:
                continue
            items.append((m, label))

        rnd.shuffle(items)
        val_count = int(len(items) * args.val_fraction)
        val_items = items[:val_count]
        train_items = items[val_count:]

        print(f"Всего изображений: {len(items)}")
        print(f"Train: {len(train_items)}")
        print(f"Val:   {len(val_items)}")

        for subset_name, subset_items in (("train", train_items), ("val", val_items)):
            for idx, (member, label) in enumerate(subset_items, start=1):
                target_dir = out_root / subset_name / label
                target_dir.mkdir(parents=True, exist_ok=True)
                target_path = target_dir / Path(member).name
                with zf.open(member) as src, target_path.open("wb") as dst:
                    dst.write(src.read())
                if idx % 5000 == 0:
                    print(f"{subset_name}: {idx}/{len(subset_items)}")


if __name__ == "__main__":
    main()

