"""
Генерация пояснительной записки и презентации по проекту «Фотоассистент».
Шаблон презентации: presentation-template.pptx (путь задаётся ниже).
Запуск из корня проекта:
  python scripts/generate_project_docs.py
Требует: pip install python-docx python-pptx
"""

from __future__ import annotations

import os
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
# Шаблон: положите presentation-template.pptx в Downloads или укажите путь в PHOTOASSISTANT_PPTX_TEMPLATE
_default_pptx = Path.home() / "Downloads" / "presentation-template.pptx"
TEMPLATE_PPTX = Path(os.environ.get("PHOTOASSISTANT_PPTX_TEMPLATE", str(_default_pptx)))
OUT_PPTX = ROOT / "Презентация_Фотоассистент.pptx"
OUT_DOCX = ROOT / "Пояснительная_записка_Фотоассистент.docx"


def set_shape_text(shape, text: str) -> None:
    if not getattr(shape, "has_text_frame", False):
        return
    tf = shape.text_frame
    tf.clear()
    if not tf.paragraphs:
        tf.add_paragraph()
    tf.paragraphs[0].text = text


def _resolve_pptx_template() -> Path:
    if TEMPLATE_PPTX.is_file():
        return TEMPLATE_PPTX
    local = ROOT / "presentation-template.pptx"
    if local.is_file():
        return local
    raise FileNotFoundError(
        f"Нет шаблона презентации. Ожидалось: {TEMPLATE_PPTX} или {local}. "
        "Скопируйте presentation-template.pptx в Downloads или в корень проекта, либо задайте PHOTOASSISTANT_PPTX_TEMPLATE."
    )


def build_presentation() -> None:
    tpl = _resolve_pptx_template()
    pr = Presentation(str(tpl))
    slides = pr.slides

    # Слайд 1 — титул
    s = slides[0]
    set_shape_text(s.shapes[1], "ФОТОАССИСТЕНТ ФОТОГРАФА")
    set_shape_text(
        s.shapes[3],
        "Десктоп-приложение на Python для автоматической сортировки снимков по экспозиции, резкости и закрытым глазам",
    )
    set_shape_text(
        s.shapes[4],
        "Выполнили:\n_________________________\n_________________________\nМагнитогорск, 2026 г.",
    )

    # Слайд 2 — актуальность
    s = slides[1]
    set_shape_text(s.shapes[3], "Рост объёма цифровых фотографий")
    set_shape_text(
        s.shapes[5],
        "Съёмка сериями приводит к сотням и тысячам кадров; ручной отбор по качеству и «закрытым глазам» занимает много времени.",
    )

    # Слайд 3 — сравнение с аналогами (таблица по смыслу шаблона)
    s = slides[2]
    set_shape_text(s.shapes[5], "Lightroom / Bridge")
    set_shape_text(s.shapes[6], "Ручной просмотр")
    set_shape_text(s.shapes[10], "Пакетная обработка пресетами")
    set_shape_text(s.shapes[11], "Частично (в основном экспозиция/цвет)")
    set_shape_text(s.shapes[12], "Явные пороги: экспозиция, резкость, глаза")
    set_shape_text(s.shapes[15], "Редактор каталогов")
    set_shape_text(s.shapes[16], "Просмотр без авто-отбраковки по глазам")
    set_shape_text(s.shapes[17], "Узкая задача: технический отбор кадра")
    set_shape_text(s.shapes[20], "Часть RAW-пайплайна")
    set_shape_text(s.shapes[21], "Не формализовано")
    set_shape_text(s.shapes[22], "Три понятных критерия + причина в имени папки")
    set_shape_text(s.shapes[25], "Десктоп, офлайн после загрузки модели лица")
    set_shape_text(s.shapes[26], "Зависит от оператора")
    set_shape_text(s.shapes[27], "Рекурсивно .jpg / .jpeg / .png")

    # Слайд 4 — целевые «объекты» → критерии
    s = slides[3]
    set_shape_text(s.shapes[1], "Критерии отбора кадров")
    set_shape_text(s.shapes[4], "Экспозиция")
    set_shape_text(s.shapes[5], "Недосвет и пересвет по доле тёмных/светлых пикселей (настраиваемые пороги)")
    set_shape_text(s.shapes[8], "Резкость")
    set_shape_text(s.shapes[9], "Отклик оператора Лапласа; ниже порога — смаз")
    set_shape_text(s.shapes[12], "Глаза")
    set_shape_text(
        s.shapes[13],
        "MediaPipe Face Landmarker, blendshapes eyeBlink; опционально ResNet (по умолчанию выкл.)",
    )

    # Слайд 5 — преимущества
    s = slides[4]
    set_shape_text(
        s.shapes[5],
        "Прозрачные критерии",
    )
    set_shape_text(
        s.shapes[9],
        "Понятные пользователю пороги в настройках; результат — папки «Удачные» / «Неудачные» с причиной.",
    )
    set_shape_text(s.shapes[13], "Локальная обработка")
    set_shape_text(
        s.shapes[17],
        "Данные не отправляются на сервер; модель лица скачивается один раз (или офлайн при наличии .task).",
    )

    # Слайд 6 — архитектура
    s = slides[5]
    set_shape_text(s.shapes[3], "Выбор папки, список файлов, журнал, прогресс")
    set_shape_text(s.shapes[5], "Пул потоков, перенос файлов в подпапки")
    set_shape_text(s.shapes[7], "Чтение изображения, RGB/BGR, ресайз кропов глаз при необходимости")
    set_shape_text(
        s.shapes[9],
        "Пайплайн: глаза → экспозиция → резкость; решение is_good + текст причины",
    )

    # Слайд 7 — датасет
    s = slides[6]
    set_shape_text(
        s.shapes[2],
        "Для опционального классификатора глаз — MRL Eye Dataset (открытый / закрытый глаз):\n"
        "https://mrl.cs.vsb.cz/eyedataset\n\n"
        "Репозиторий проекта (код, README, веса при необходимости):\n"
        "https://github.com/Dorlian/Samsung_project",
    )

    # Слайд 8 — датасет (цифры ориентировочные для MRL)
    s = slides[7]
    set_shape_text(s.shapes[3], "Распределение классов open/closed после подготовки скриптом prepare_mrl_dataset")
    set_shape_text(
        s.shapes[5],
        "Два класса: открытый глаз, закрытый глаз. Доля валидации задаётся при подготовке (например 20 %).",
    )
    set_shape_text(
        s.shapes[7],
        "Полный MRL в git не хранится из‑за объёма; в репозитории — скрипты подготовки и обучения.",
    )

    # Слайд 9 — пример
    s = slides[8]
    set_shape_text(s.shapes[4], "Цепочка: исходная папка → анализ каждого файла → перемещение в «Удачные» или «Неудачные/<причина>».")
    set_shape_text(s.shapes[6], "Причины отбраковки")
    set_shape_text(s.shapes[7], "Скриншот UI (вставьте вручную при необходимости)")
    set_shape_text(s.shapes[8], "Фрагмент лога / статистика")

    # Слайд 10 — технологии
    s = slides[9]
    set_shape_text(s.shapes[1], "Стек: Python, OpenCV, MediaPipe, PyTorch (опционально)")
    set_shape_text(s.shapes[2], "Почему такой выбор?")
    set_shape_text(
        s.shapes[3],
        "MediaPipe — готовая лёгкая модель лица и blendshapes без тяжёлого YOLO\n"
        "OpenCV — гистограмма, Лаплас, каскады при отсутствии лица\n"
        "PyTorch — только для доп. CNN по кропам глаз (по желанию)\n"
        "Tkinter — кроссплатформенный UI без лишних зависимостей",
    )

    # Слайд 11 — график (заголовок)
    s = slides[10]
    set_shape_text(s.shapes[1], "Обучение ResNet-18 (опционально): val accuracy по эпохам — вставьте график из TensorBoard / логов")

    # Слайд 12 — сравнение моделей → режимы глаз
    s = slides[11]
    set_shape_text(s.shapes[2], "Основной")
    set_shape_text(s.shapes[3], "MediaPipe blendshapes — стабильный режим по умолчанию")
    set_shape_text(s.shapes[5], "Опция")
    set_shape_text(s.shapes[6], "ResNet по кропам — выкл. по умолчанию; включается в настройках при наличии .pth")
    set_shape_text(
        s.shapes[8],
        "На практике для отбора портретов лучше показал себя режим без доп. CNN; CNN оставлен для экспериментов.",
    )

    # Слайд 13
    s = slides[12]
    set_shape_text(s.shapes[1], "Примеры причин в папке «Неудачные»")

    # Слайд 14 — метрики
    s = slides[13]
    set_shape_text(s.shapes[4], "Пороги экспозиции")
    set_shape_text(s.shapes[6], "Порог резкости (Laplacian)")
    set_shape_text(s.shapes[8], "Пороги blink L/R (MediaPipe)")

    # Слайд 15
    s = slides[14]
    set_shape_text(s.shapes[1], "Демонстрация приложения (видео или слайды — добавьте вручную)")

    # Слайд 16 — заключение
    s = slides[15]
    set_shape_text(
        s.shapes[4],
        "Фотографы, фотостудии, мероприятия; любой пользователь, которому нужно быстро отсеять технический брак.",
    )
    set_shape_text(
        s.shapes[7],
        "Сокращение времени на первичный отбор; единообразные критерии для серии снимков.",
    )
    set_shape_text(
        s.shapes[10],
        "Новые критерии (улыбка, композиция), GPU-ускорение, пакетный exe уже описан в README.",
    )

    pr.save(str(OUT_PPTX))
    print("Презентация:", OUT_PPTX)


def build_zapiska() -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(14)

    def add_center(lines: list[str]) -> None:
        for t in lines:
            p = doc.add_paragraph(t.strip())
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_left(text: str) -> None:
        doc.add_paragraph(text)

    def add_heading(num: str, title: str) -> None:
        p = doc.add_paragraph()
        r = p.add_run(f"{num}. {title}")
        r.bold = True

    add_center(
        [
            "МИНИСТЕРСТВО НАУКИ И ВЫСШЕГО ОБРАЗОВАНИЯ РОССИЙСКОЙ ФЕДЕРАЦИИ",
            "ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ БЮДЖЕТНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ",
            "«МАГНИТОГОРСКИЙ ГОСУДАРСТВЕННЫЙ ТЕХНИЧЕСКИЙ",
            "УНИВЕРСИТЕТ ИМ. Г.И. НОСОВА»",
            "(ФГБОУ ВО «МГТУ ИМ. Г.И.НОСОВА»)",
            "Институт энергетики и автоматизированных систем",
            "Кафедра бизнес – информатики и информационных технологий",
        ]
    )
    doc.add_paragraph()
    p = doc.add_paragraph()
    r = p.add_run("ПРОЕКТНОЕ ЗАДАНИЕ")
    r.bold = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    add_center(
        [
            "по дисциплине: Компьютерное зрение и интеллектуальные системы",
            "на тему: Разработка десктоп-приложения «Фотоассистент фотографа» для автоматической сортировки "
            "фотографий по экспозиции, резкости и признаку закрытых глаз",
            "Исполнители: _________________________, студенты ___ курса, группа ___________",
            "Руководитель: _________________________, _________________________________",
            'Работа допущена к защите «___» _____________ 20__ г. __________',
            "(подпись)",
            'Работа защищена «___» _____________ 20__ г. с оценкой __________     __________',
            "    (оценка)         (подпись)",
            "Магнитогорск, 2026 г.",
        ]
    )

    doc.add_paragraph()
    add_left("Содержание")
    for line in (
        "Введение",
        "Описание структуры проекта",
        "Инструкция по установке и запуску",
        "Описание датасета",
        "Архитектура моделей и обучение",
        "Интеграция и пользовательский интерфейс",
        "Заключение",
        "Список источников",
    ):
        doc.add_paragraph(line)

    add_heading("1", "Введение")
    add_left(
        "Объём цифровой фотографии неуклонно растёт: съёмки мероприятий, портреты, репортажи сопровождаются "
        "сотнями и тысячами кадров. Значительная часть кадров не пригодна для передачи заказчику из‑за технических "
        "дефектов: неудачная экспозиция, смаз, закрытые глаза на портретах. Ручной просмотр каждого файла "
        "отнимает много времени и приводит к утомлению оператора."
        "\n\n"
        "Методы компьютерного зрения и машинного обучения позволяют автоматизировать первичный отбор: оценить "
        "распределение яркости, резкость изображения, наличие лица и состояние век по данным модели лицевых ориентиров."
        "\n\n"
        "Цель проекта — разработка десктоп-приложения на языке Python с графическим интерфейсом, выполняющего "
        "рекурсивный обход выбранной папки с файлами .jpg / .jpeg / .png и распределение снимков по каталогам "
        "«Удачные» и «Неудачные» с указанием причины отбраковки."
        "\n\n"
        "Задачи: анализ предметной области; выбор и настройка метрик; подготовка данных и обучение вспомогательного "
        "классификатора глаз (опционально); интеграция MediaPipe Face Landmarker; разработка интерфейса и тестирование."
    )

    add_heading("2", "Описание структуры проекта")
    add_left(
        "Исходный код и документация размещены в открытом репозитории GitHub: https://github.com/Dorlian/Samsung_project"
        "\n\n"
        "Корень проекта: main.py (запуск приложения), requirements.txt, run.bat и run.sh, build_exe.bat и "
        "photo_assistant.spec для сборки исполняемого файла под Windows, каталог models/ для модели MediaPipe "
        "и опционального файла весов eye_state_resnet18.pth, каталог training/ с инструкциями по данным для обучения."
        "\n\n"
        "Пакет src/analysis содержит модули экспозиции, резкости, анализа глаз и сборку пайплайна PhotoAnalyzer; "
        "src/config — сохранение порогов в app_settings.json; src/models — архитектура ResNet для глаз; "
        "src/training — скрипты prepare_mrl_dataset.py и train_eye_classifier.py; src/ui — раздел «Альбомы»; "
        "src/utils — обход файлов и перемещение в папки результатов."
    )

    add_heading("3", "Инструкция по установке и запуску")
    add_left(
        "Требуется Python 3.10–3.12. Рекомендуется создание виртуального окружения и установка зависимостей командой "
        "pip install -r requirements.txt. Запуск: python main.py или сценарии run.bat / run.sh (см. README.md в репозитории)."
        "\n\n"
        "При первом анализе изображений с лицами в каталог models/ загружается файл face_landmarker.task (необходим "
        "доступ в Интернет один раз). Опциональная нейросеть для глаз по умолчанию отключена в настройках; при "
        "включении и наличии файла весов используется дополнительная проверка кропов глаз."
    )

    add_heading("4", "Описание датасета")
    add_left(
        "Для обучения классификатора «открытый / закрытый глаз» применяется открытый MRL Eye Dataset "
        "(изображения области глаза с метками в имени файла). Официальный источник: https://mrl.cs.vsb.cz/eyedataset. "
        "Скрипт prepare_mrl_dataset.py формирует структуры train/open, train/closed, val/open, val/closed. "
        "Полный объём датасета в репозиторий не включён из‑за размера; инструкции по скачиванию приведены в training/README.md."
        "\n\n"
        "Критерии экспозиции и резкости не требуют отдельного датасета: используются классические вычисления по пикселям изображения."
    )

    add_heading("5", "Архитектура моделей и обучение")
    add_left(
        "Детекция лица и оценка смыкания век выполняется средствами MediaPipe Face Landmarker с использованием "
        "blendshape-категорий eyeBlink_L и eyeBlink_R."
        "\n\n"
        "Дополнительно реализован классификатор на базе ResNet-18 (два выхода). Обучение — скрипт train_eye_classifier.py "
        "с параметрами по умолчанию: размер входа 64×64, пакет 64, до 10 эпох, оптимизатор Adam, функция потерь — "
        "перекрёстная энтропия; лучшие веса сохраняются в models/eye_state_resnet18.pth."
        "\n\n"
        "Метрики экспозиции и резкости задаются порогами в пользовательском интерфейсе и не используют обучение на размеченном датасете."
    )

    add_heading("6", "Интеграция и пользовательский интерфейс")
    add_left(
        "Интерфейс реализован на библиотеке Tkinter. Раздел «Анализ»: выбор папки, запуск и остановка обработки, "
        "прогресс и журнал. Раздел «Альбомы»: просмотр миниатюр и ручной перенос выбранных файлов между альбомами. "
        "Раздел «Настройки»: пороги экспозиции и резкости, включение опциональной CNN для глаз; параметры сохраняются в app_settings.json."
        "\n\n"
        "Модуль pipeline.py последовательно вызывает проверку глаз, экспозиции и резкости и формирует итоговое решение по каждому файлу."
    )

    add_heading("7", "Заключение")
    add_left(
        "Разработано приложение для автоматической сортировки фотографий по экспозиции, резкости и признаку закрытых глаз. "
        "Реализованы классические методы анализа изображения, детекция лица MediaPipe и опциональное обучение свёрточного классификатора."
        "\n\n"
        "Практическая ценность — сокращение времени первичного отбора кадров. Перспективы: добавление новых критериев, "
        "улучшение устойчивости к освещению и ракурсу, оптимизация производительности."
    )

    add_heading("8", "Список использованных источников")
    for i, src in enumerate(
        [
            "MediaPipe Face Landmarker — https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker",
            "MRL Eye Dataset — https://mrl.cs.vsb.cz/eyedataset",
            "Документация PyTorch — https://pytorch.org/docs/stable/index.html",
            "Документация OpenCV — https://docs.opencv.org/",
            "Документация Python Tkinter — https://docs.python.org/3/library/tkinter.html",
        ],
        start=1,
    ):
        doc.add_paragraph(f"{i}. {src}")

    doc.save(str(OUT_DOCX))
    print("Записка:", OUT_DOCX)


def main() -> None:
    build_zapiska()
    build_presentation()


if __name__ == "__main__":
    main()
