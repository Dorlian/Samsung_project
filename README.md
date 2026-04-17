# Фотоассистент фотографа

**Репозиторий:** [Samsung_project](https://github.com/Dorlian/Samsung_project) (GitHub).

Десктоп-приложение на Python: автоматическая сортировка фотографий в папки **Удачные** и **Неудачные** по критериям:

В **корне репозитория** лежат только **`README.md`** и **`.bat`** для Windows; остальное — в подпапках (`app/`, `src/`, `requirements/`, `deploy/`, `packaging/`, `bin/` и т.д.).

- экспозиция (пересвет / недосвет),
- резкость (смаз),
- закрытые глаза (MediaPipe Face Landmarker; опционально — доп. проверка нейросетью, если есть файл весов).

---

## Быстрый старт

1. Установите **Python 3.10, 3.11 или 3.12** (с [python.org](https://www.python.org/downloads/) или через пакетный менеджер ОС).  
   На Python **3.13+** пакет `mediapipe` может быть недоступен — используйте 3.10–3.12.

2. Склонируйте или скачайте архив проекта и перейдите в его папку в терминале.

3. Создайте виртуальное окружение и установите зависимости:

**Windows (PowerShell или CMD)**

```bat
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements\requirements.txt
.\.venv\Scripts\python.exe -m app
```

Либо дважды запустите **`run.bat`** из корня проекта — скрипт подставит Python из `.venv` / `.venv312` и при необходимости установит пакеты.

**PowerShell (Windows):** из корня репозитория: **`.\bin\run.ps1`** (при ошибке политики: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`). В скрипте используйте только **прямые кавычки** с клавиатуры, не «типографские» из Word. Команды **`sh`** / **`chmod`** в обычном PowerShell нет — для **`bin/run.sh`** используйте **WSL** или **Git Bash** (файл с переводами строк **LF**, см. `.gitattributes`).

Если проект будут запускать **на другом ПК или на защите**, заранее прочитайте раздел **«Защита проекта»** ниже (несколько запасных способов, в том числе Docker).

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/requirements.txt
python -m app
```

Либо из корня проекта: **`chmod +x bin/run.sh`** один раз, затем **`./bin/run.sh`**.

**Linux:** если при запуске ошибка про отсутствие `tkinter`, установите пакет Tcl/Tk для вашей системы, например:

- Debian/Ubuntu: `sudo apt install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`

---

## Защита проекта: несколько способов запуска на чужом ноутбуке

На «домашних» ПК всё может работать, а на ноутбуке комиссии — нет: другая версия Windows, **нет Python**, **антивирус / корпоративная политика**, **нет интернета** при первом создании `.venv`, **запрет winget**, путь к проекту с **кириллицей** или очень длинный путь. Ниже — запасные варианты; на защите имеет смысл иметь **минимум два** (например: папка с **Python + venv** и отдельно **EXE с консолью**).

### Рекомендуемый порядок попыток

1. **Скопировать проект в короткий путь без кириллицы**, например `C:\PhotoAssistant\` (на части ПК это устраняет сбои у старых сборщиков и инструментов).
2. **`Фотоассистент.bat`** — создаёт `.venv`, ставит зависимости, затем запускает приложение. Нужны **Python 3.10–3.12** и **интернет** при первом запуске.
3. **`run_console.bat`** — то же окружение `.venv`, но программа в **той же консоли**; если будет ошибка, её будет видно (у обычного `Фотоассистент.bat` окно консоли можно закрыть до появления traceback).
4. **Вручную из CMD** (если bat «молчит»):  
   `cd /d C:\PhotoAssistant`  
   `py -3.12 -m venv .venv`  
   `.venv\Scripts\python.exe -m pip install -r requirements\requirements.txt`  
   `.venv\Scripts\python.exe -m app`
5. **Сборка EXE** — папка **`dist/FotoAssistant/`** целиком (не один файл). На комиссионном ПК должны быть установлены **[Visual C++ Redistributable](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist)** (x64), и иногда нужно **разрешить приложение в антивирусе** или **собрать EXE с консолью** (см. ниже).
6. **Docker** — если на ноутбуке стоят Docker Desktop и WSL2: см. раздел **«Docker»** ниже в этом README. На Windows **окно Tk из контейнера обычно неудобно**; Docker уместен как запасной способ **поднять окружение** и прогнать код/скрипты, а для демонстрации GUI надёжнее **п. 2–4** или **EXE**.

### Почему EXE «не работает» (ничего не видно)

- В основной сборке у окна **нет консоли** (`console=False`) — при падении процесса **ошибка не видна**.
- **Скопировали только `.exe`**, без соседних папок и DLL из **`dist/FotoAssistant/`**.
- **Антивирус** блокирует или удаляет файлы из папки `_internal` (типично для PyInstaller + PyTorch).
- Нет **VC++ Redistributable x64**.

**Запасной вариант:** соберите **`build_exe_console.bat`** → папка **`dist/FotoAssistantConsole/`** — при сбое останется **чёрная консоль с текстом ошибки**.

### Почему BAT может не сработать

- Не установлен **Python** или в PATH попал **Python 3.13+**, для которого **нет колеса `mediapipe`** — используйте **3.10–3.12** и при необходимости явно `py -3.12`.
- **Первый запуск без интернета** — `pip install` не завершится.
- **PowerShell** и политика выполнения не относятся к `.bat` из CMD; если запускаете скрипты **`.ps1`**, используйте **CMD** или `activate.bat`.

### Docker на ноутбуке с Windows

1. Установите **Docker Desktop** (и при необходимости **WSL2** по подсказкам установщика).
2. Из корня репозитория: `docker compose -f deploy/docker-compose.yml build`, затем `docker compose -f deploy/docker-compose.yml run --rm photo-assistant`.  
   По умолчанию используется **виртуальный дисплей**; полноценная демонстрация окон так же, как у нативного приложения, на Windows из Docker обычно **не гарантируется** — держите под рукой **запуск через Python** (п. 2–4).

---

## Что умеет

- Рекурсивный анализ `.jpg` / `.jpeg` / `.png` в выбранной папке.
- Раскладка результатов:
  - `Удачные/`
  - `Неудачные/<причина>/`
- Интерфейс: **Анализ**, **Альбомы** (миниатюры и превью), **Настройки**, остановка обработки.
- Ручной перенос одного или нескольких снимков между альбомами (в т.ч. с `Ctrl` + клик).

---

## Первый запуск анализа

1. Откройте раздел **Анализ**.
2. **Папка** — каталог с фотографиями.
3. **Запустить анализ**.
4. В **Альбомах** нажмите **Обновить**, если список не обновился.

При первом запуске модель лица MediaPipe (`face_landmarker.task`, ~3.5 МБ) **скачивается в папку `models/`** — нужен **доступ в интернет**. Без сети положите файл вручную (см. комментарии в коде `src/analysis/eyes.py` или URL в репозитории MediaPipe).

### Готовые веса CNN для глаз (`eye_state_resnet18.pth`)

В репозитории **может** лежать файл **`models/eye_state_resnet18.pth`** (десятки МБ): тогда после `git clone` дополнительная проверка глаз ResNet **работает сразу**, без обучения. Если файла в клоне нет — либо [обучите сами](training/README.md), либо попросите у автора репозитория и положите его в `models/` под тем же именем.

**Для автора репозитория** (один раз, когда файл уже есть на диске):

```bash
git add models/eye_state_resnet18.pth
git commit -m "Добавлены веса классификатора глаз"
git push
```

Лимит GitHub на один файл — **100 МБ**; типичный `state_dict` ResNet-18 укладывается. Если файл больше — используйте [Git LFS](https://git-lfs.com/) или выложите веса как **Release** на GitHub и скачивайте вручную.

---

## Настройки

В разделе **Настройки** задаются пороги экспозиции и резкости, опция **доп. проверки глаз (ResNet)**.  
Значения сохраняются в **`app_settings.json`** в каталоге запуска приложения.

**Опциональная нейросеть для глаз:** по умолчанию **выключена** в настройках — закрытые глаза определяются только **MediaPipe** (blendshapes), это обычно стабильнее. Если включить галочку в настройках и положить **`models/eye_state_resnet18.pth`**, добавится проверка ResNet. Обучение: `src/training/train_eye_classifier.py`.

Переменная окружения (необязательно):

- `PHOTOASSISTANT_EYE_CLOSED_CHECK=0` — без CNN (даже если в настройках включено);
- `=1` — принудительно включить CNN (если файл весов есть).

---

## Сборка исполняемого файла (только Windows)

Если нужен один `.exe` без установленного Python:

1. Установите зависимости в виртуальное окружение (см. выше).
2. Установите PyInstaller: `pip install pyinstaller`
3. Запустите **`build_exe.bat`** из **корня** репозитория или вручную:  
   `pyinstaller packaging/photo_assistant.spec`

Готовая сборка обычно лежит в **`dist/FotoAssistant/`**. Переносите **всю** эту папку, не один файл `.exe`.

**Для защиты / чужого ПК:** дополнительно **`build_exe_console.bat`** — консоль и без UPX (`packaging/photo_assistant_console.spec`), папка **`dist/FotoAssistantConsole/`**. В **`packaging/photo_assistant.spec`** UPX отключён.

---

## Docker (сборка и запуск в контейнере)

Нужны установленные **Docker** и **Docker Compose** (Plugin `docker compose` или классический `docker-compose`).

**Сборка образа**

В образе ставится **PyTorch CPU** (через `requirements/requirements-docker.txt` + официальный CPU-индекс), без пакетов NVIDIA.

Команды выполняйте из **корня** репозитория, указав файлы в **`deploy/`**:

```bash
docker compose -f deploy/docker-compose.yml build
```

**Запуск приложения**

По умолчанию включён **виртуальный дисплей** (`xvfb`).

```bash
docker compose -f deploy/docker-compose.yml run --rm photo-assistant
```

Корень репозитория монтируется в **`/app`** в контейнере.

Если при `run` видите **`set: pipefail: invalid option name`** — это обычно **CRLF** в `deploy/docker/entrypoint.sh` на Windows: том монтирует проект в `/app` и **перекрывает** скрипт из образа. В образе запуск идёт из **`/entrypoint.sh`** (вне `/app`), он не подменяется томом. После `git pull` выполните **`docker compose -f deploy/docker-compose.yml build --no-cache`**.

**GUI на экране хоста (Linux + X11)**

```bash
xhost +local:docker
PHOTOASSISTANT_HEADLESS=0 DISPLAY=$DISPLAY docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.linux-gui.yml run --rm photo-assistant
```

На **Windows/macOS** вывод нативного окна из Docker обычно неудобен; для повседневной работы проще запускать приложение **напрямую через Python** или **`.exe`** (см. выше).

**Разовые команды без GUI** (обучение, скрипты):

```bash
docker compose -f deploy/docker-compose.yml run --rm photo-assistant python -m src.training.train_eye_classifier --help
```

---

## Частые проблемы

| Симптом | Что сделать |
|--------|-------------|
| `ModuleNotFoundError` | Установите зависимости тем же интерпретатором: `python -m pip install -r requirements/requirements.txt` |
| Нет модуля `mediapipe` | Убедитесь в Python 3.10–3.12; при необходимости обновите pip |
| Не грузится модель лица | Проверьте интернет; убедитесь, что папка `models/` доступна для записи |
| Linux: нет `tkinter` | Установите `python3-tk` (см. выше) |
| Тяжёлый / долгий `torch` | На CPU обычно достаточно `requirements/requirements.txt`; при необходимости см. [официальную инструкцию PyTorch](https://pytorch.org/get-started/locally/) |
| EXE сразу закрывается / «ничего не происходит» | Перенесите **всю** папку `dist/FotoAssistant/`; установите [VC++ Redistributable x64](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist); проверьте антивирус; соберите **`FotoAssistantConsole`** и смотрите текст в консоли |
| BAT не находит Python | Установите Python **3.10–3.12**, галочка **Add to PATH**; или `py -3.12` из [py launcher](https://docs.python.org/3/using/windows.html#python-launcher-for-windows) |
| Сбои в папке с кириллицей в пути | Скопируйте проект в `C:\PhotoAssistant\` и запустите оттуда |
| **Все фото только в «пересвет»** на одном ПК, на других нормально | Чаще всего битый **`app_settings.json`** (слишком низкий порог «светлых» пикселей). В приложении: **Настройки → Сбросить** или удалите `app_settings.json`. В новых версиях файл при старте **автоматически приводится** к допустимым значениям |

---

## Обучение модели глаз (ResNet)

Скрипты, подготовка **MRL Eye Dataset** и запуск обучения — в **[training/README.md](training/README.md)**. Сами датасеты в git не входят (только инструкции и папки-плейсхолдеры).

---

## Структура репозитория

| Путь | Назначение |
|------|------------|
| `*.bat`, `README.md` | Корень: только запуск под Windows и документация |
| `app/__main__.py` | Точка входа GUI; запуск: `python -m app` из корня репозитория |
| `src/analysis/` | Экспозиция, резкость, глаза, общий пайплайн |
| `src/ui/gallery.py` | Альбомы и ручной перенос |
| `src/config/settings.py` | Настройки и `app_settings.json` |
| `src/models/eye_classifier.py` | Классификатор глаз (ResNet) |
| `src/training/` | Подготовка MRL и обучение `eye_state_resnet18.pth` |
| `training/README.md` | Как скачать данные и обучить модель |
| `requirements/requirements.txt` | Зависимости Python |
| `requirements/requirements-docker.txt` | Зависимости для Docker (без torch) |
| `bin/run.sh`, `bin/run.ps1` | Запуск из Unix / PowerShell (рабочий каталог — корень репо) |
| `Фотоассистент.bat`, `run.bat` | Windows: `.venv`, `pip`, `python -m app` |
| `run_console.bat` | Запуск `python -m app` **с консолью** |
| `packaging/photo_assistant*.spec`, `photo_assistant_rth.py` | PyInstaller |
| `deploy/Dockerfile`, `deploy/docker-compose*.yml` | Docker |
| `scripts/generate_project_docs.py` | Генерация пояснительной записки и презентации |

Папка **`models/`** создаётся при работе приложения; в репозитории её можно не коммитить (см. `.gitignore`).
