"""
Скрипт обучения модели определения состояния глаз (открыт/закрыт) на основе MRL Eye Dataset
или совместимой структуры датасета.

Ожидаемая структура папок:

dataset_root/
    train/
        open/
        closed/
    val/
        open/
        closed/

Запуск:
    python -m src.training.train_eye_classifier --data-root path/to/dataset_root --output models/eye_state_resnet18.pth
"""

from pathlib import Path
import argparse
import csv

import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from src.models.eye_classifier import EyeStateMobileNetModel, EyeStateModel
from torch.utils.data import Subset


def get_dataloaders(
    data_root: Path,
    batch_size: int = 64,
    *,
    max_train: int | None = None,
    max_val: int | None = None,
    seed: int = 42,
):
    transform = transforms.Compose(
        [
            transforms.Grayscale(num_output_channels=3),
            transforms.Resize((64, 64)),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
        ]
    )

    train_dir = data_root / "train"
    val_dir = data_root / "val"

    train_ds = datasets.ImageFolder(train_dir, transform=transform)
    val_ds = datasets.ImageFolder(val_dir, transform=transform)

    # Быстрый режим для построения графиков/демо: берём подвыборку.
    # Полное обучение может занимать долго на CPU.
    if max_train is not None and max_train > 0 and len(train_ds) > max_train:
        g = torch.Generator().manual_seed(seed)
        idx = torch.randperm(len(train_ds), generator=g)[:max_train].tolist()
        train_ds = Subset(train_ds, idx)
    if max_val is not None and max_val > 0 and len(val_ds) > max_val:
        g = torch.Generator().manual_seed(seed + 1)
        idx = torch.randperm(len(val_ds), generator=g)[:max_val].tolist()
        val_ds = Subset(val_ds, idx)

    # На Windows в некоторых окружениях num_workers>0 может приводить к зависанию.
    # Для воспроизводимости по умолчанию используем 0.
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    return train_loader, val_loader


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    for inputs, targets in loader:
        inputs, targets = inputs.to(device), targets.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = outputs.max(1)
        correct += preds.eq(targets).sum().item()
        total += targets.size(0)

    return running_loss / total, correct / total


def evaluate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    with torch.inference_mode():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, targets)

            running_loss += loss.item() * inputs.size(0)
            _, preds = outputs.max(1)
            correct += preds.eq(targets).sum().item()
            total += targets.size(0)

    return running_loss / total, correct / total


def create_model(model_name: str):
    model_name = model_name.lower().strip()
    if model_name == "resnet18":
        return EyeStateModel(pretrained=False)
    if model_name in {"mobilenetv3", "mobilenet_v3_small", "mobilenetv3_small"}:
        return EyeStateMobileNetModel(pretrained=False)
    raise ValueError(f"Неизвестная модель: {model_name}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=str, required=True, help="Корневая папка датасета (train/ и val/ внутри)")
    parser.add_argument("--output", type=str, default="models/eye_state_resnet18.pth", help="Путь для сохранения весов")
    parser.add_argument(
        "--model",
        type=str,
        default="resnet18",
        help="Архитектура: resnet18 | mobilenetv3",
    )
    parser.add_argument(
        "--log-csv",
        type=str,
        default="",
        help="Путь для CSV лога метрик по эпохам (если пусто — <output>.csv рядом с весами)",
    )
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max-train", type=int, default=0, help="Ограничить размер train выборки (0 = без ограничения)")
    parser.add_argument("--max-val", type=int, default=0, help="Ограничить размер val выборки (0 = без ограничения)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Обучаем модель с нуля, чтобы не тянуть предобученные веса из интернета
    print(f"Используем устройство: {device}")
    model = create_model(args.model).to(device)

    print("Загрузка датасета...")
    train_loader, val_loader = get_dataloaders(
        Path(args.data_root),
        batch_size=args.batch_size,
        max_train=(args.max_train or None),
        max_val=(args.max_val or None),
        seed=int(args.seed),
    )
    print("Датасет загружен.")

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val_acc = 0.0
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = Path(args.log_csv) if args.log_csv else output_path.with_suffix(".csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "epoch", "train_loss", "train_acc", "val_loss", "val_acc"])
        f.flush()

        for epoch in range(1, args.epochs + 1):
            train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
            val_loss, val_acc = evaluate(model, val_loader, criterion, device)
            print(
                f"[{args.model}] Epoch {epoch}: "
                f"train_loss={train_loss:.4f}, train_acc={train_acc:.4f}, "
                f"val_loss={val_loss:.4f}, val_acc={val_acc:.4f}"
            )

            w.writerow([args.model, epoch, f"{train_loss:.6f}", f"{train_acc:.6f}", f"{val_loss:.6f}", f"{val_acc:.6f}"])
            f.flush()

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(model.state_dict(), output_path)
                print(f"Новая лучшая модель сохранена в {output_path} (val_acc={val_acc:.4f})")


if __name__ == "__main__":
    main()

