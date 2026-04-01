"""
Подготовка MRL Eye Dataset к формату:

dataset_root/
  train/
    open/
    closed/
  val/
    open/
    closed/

Скрипт ожидает распакованный оригинальный MRL‑датасет (папка вроде mrlEyes_2018_01)
и по имени файла определяет класс:

- 0 = closed (закрытый глаз)
- 1 = open  (открытый глаз)

Пример запуска:

    python -m src.training.prepare_mrl_dataset ^
        --mrl-root C:\data\mrlEyes_2018_01 ^
        --out-root C:\data\mrl_prepared ^
        --val-fraction 0.2
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Dict, List


def parse_label_from_filename(name: str) -> int | None:
    """
    Пытаемся вытащить метку 0/1 из имени файла MRL.
    В большинстве вариантов датасета в имени есть блоки с 0 или 1,
    где 0 = closed, 1 = open.
    Если ничего похожего не нашли — возвращаем None.
    """
    stem = Path(name).stem
    parts = stem.split("_")
    for p in parts:
        if p in {"0", "1"}:
            return int(p)
    return None


def collect_images(mrl_root: Path) -> Dict[int, List[Path]]:
    images: Dict[int, List[Path]] = {0: [], 1: []}
    for path in mrl_root.rglob("*.png"):
        label = parse_label_from_filename(path.name)
        if label is None:
            continue
        if label in images:
            images[label].append(path)
    return images


def split_train_val(
    items: List[Path],
    val_fraction: float,
    seed: int = 42,
) -> tuple[list[Path], list[Path]]:
    rnd = random.Random(seed)
    items_shuffled = items[:]
    rnd.shuffle(items_shuffled)
    val_size = int(len(items_shuffled) * val_fraction)
    val = items_shuffled[:val_size]
    train = items_shuffled[val_size:]
    return train, val


def copy_group(paths: List[Path], target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    for src in paths:
        dst = target_dir / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Подготовка MRL Eye Dataset к train/val/open/closed структуре")
    parser.add_argument("--mrl-root", type=str, required=True, help="Путь к распакованному mrlEyes_2018_01")
    parser.add_argument(
        "--out-root",
        type=str,
        required=True,
        help="Куда сохранить подготовленный датасет (dataset_root)",
    )
    parser.add_argument(
        "--val-fraction",
        type=float,
        default=0.2,
        help="Доля данных, идущая в валидацию (по умолчанию 0.2)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed для случайного разделения train/val")

    args = parser.parse_args()
    mrl_root = Path(args.mrl_root)
    out_root = Path(args.out_root)

    if not mrl_root.exists():
        raise SystemExit(f"Папка с MRL датасетом не найдена: {mrl_root}")

    images_by_label = collect_images(mrl_root)
    closed_paths = images_by_label[0]
    open_paths = images_by_label[1]

    print(f"Найдено {len(open_paths)} открытых и {len(closed_paths)} закрытых глаз")

    train_open, val_open = split_train_val(open_paths, args.val_fraction, args.seed)
    train_closed, val_closed = split_train_val(closed_paths, args.val_fraction, args.seed)

    # train
    copy_group(train_open, out_root / "train" / "open")
    copy_group(train_closed, out_root / "train" / "closed")
    # val
    copy_group(val_open, out_root / "val" / "open")
    copy_group(val_closed, out_root / "val" / "closed")

    print("Готово.")
    print(f"train/open:   {len(train_open)}")
    print(f"train/closed: {len(train_closed)}")
    print(f"val/open:     {len(val_open)}")
    print(f"val/closed:   {len(val_closed)}")


if __name__ == "__main__":
    main()

