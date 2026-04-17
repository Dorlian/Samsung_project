# Обучение классификатора «открытый / закрытый глаз»

Используется **ResNet-18** (`src/models/eye_classifier.py`), обучение — `src/training/train_eye_classifier.py`.  
Рекомендуемый источник разметки — **MRL Eye Dataset** (открытые/закрытые глаза).

## 1. Данные

1. Скачайте **MRL Eye Dataset** с официального сайта:  
   https://mrl.cs.vsb.cz/eyedataset  
   (зеркала на Kaggle тоже встречаются — ищите «MRL Eye Dataset».)

2. Распакуйте архив, чтобы получилась папка вроде `mrlEyes_2018_01` с изображениями.

3. В этом репозитории для данных зарезервированы каталоги (в git **не** попадают — только локально):
   - `training/data/raw/` — сюда положите **распакованный** оригинальный MRL (или symlink);
   - `training/data/prepared/` — сюда скрипт ниже запишет структуру `train/open`, `train/closed`, `val/...`.

## 2. Подготовка датасета к обучению

Из корня проекта (с активированным venv):

```bash
python -m src.training.prepare_mrl_dataset --mrl-root training/data/raw/mrlEyes_2018_01 --out-root training/data/prepared --val-fraction 0.2
```

Пути подставьте под свои имена папок. Параметр `--val-fraction` — доля валидации (например `0.2`).

## 3. Обучение

```bash
python -m src.training.train_eye_classifier --data-root training/data/prepared --output models/eye_state_resnet18.pth --epochs 15 --batch-size 64
```

Убедитесь, что каталог `models/` существует. После обучения скопируйте или оставьте `models/eye_state_resnet18.pth` — приложение подхватит его при включённой опции в настройках.

## 4. Зависимости

Те же, что для основного приложения: `torch`, `torchvision` (см. `requirements/requirements.txt`).

## Связь с приложением

Пайплайн анализа фото: `src/analysis/eyes.py` — при наличии файла весов и включённой проверке CNN результат учитывается вместе с MediaPipe Face Landmarker.
