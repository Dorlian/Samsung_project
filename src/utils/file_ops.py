from pathlib import Path
from typing import Iterator
import shutil


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}


def iter_image_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in IMAGE_EXTENSIONS:
            yield path


def iter_images_for_sorting(root: Path) -> Iterator[Path]:
    """Как iter_image_files, но без папок Удачные/Неудачные (повторный запуск не трогает уже разобранное)."""
    skip = {"Удачные", "Неудачные"}
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in IMAGE_EXTENSIONS:
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(p in skip for p in rel.parts):
            continue
        yield path


def prepare_output_dirs(source_dir: Path) -> tuple[Path, Path]:
    good_dir = source_dir / "Удачные"
    bad_dir = source_dir / "Неудачные"
    good_dir.mkdir(exist_ok=True)
    bad_dir.mkdir(exist_ok=True)
    return good_dir, bad_dir


def move_with_reason(src: Path, base_dir: Path, reason: str) -> Path:
    """
    Перемещает файл в подпапку base_dir с именем, основанным на причине.
    Например: Неудачные/Размытие, Неудачные/Экспозиция и т.д.
    """
    reason_safe = reason.replace(":", "_").replace("/", "_").replace("\\", "_")
    target_dir = base_dir / reason_safe
    target_dir.mkdir(parents=True, exist_ok=True)
    dst = target_dir / src.name
    shutil.move(str(src), str(dst))
    return dst

