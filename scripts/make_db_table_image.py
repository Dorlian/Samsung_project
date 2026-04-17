from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = []
    if bold:
        candidates.extend(["arialbd.ttf", "seguisb.ttf"])
    candidates.extend(["arial.ttf", "segoeui.ttf"])
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def draw_wrapped(draw: ImageDraw.ImageDraw, text: str, box: tuple[int, int, int, int], font, fill=(20, 20, 20)) -> None:
    x0, y0, x1, y1 = box
    max_width = x1 - x0 - 14
    avg_char_w = max(7, int(font.size * 0.55)) if hasattr(font, "size") else 8
    width_chars = max(10, max_width // avg_char_w)
    lines = []
    for raw in text.split("\n"):
        lines.extend(wrap(raw, width=width_chars) or [""])
    y = y0 + 10
    line_h = int((font.size if hasattr(font, "size") else 14) * 1.35)
    for line in lines:
        if y + line_h > y1 - 6:
            break
        draw.text((x0 + 7, y), line, font=font, fill=fill)
        y += line_h


def main() -> None:
    out_path = Path("Таблица_описание_БД_Фотоассистент.png")
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    title_font = get_font(52, bold=True)
    head_font = get_font(28, bold=True)
    body_font = get_font(24, bold=False)
    foot_font = get_font(22, bold=False)

    title = "Табличное описание БД (данных) проекта «Фотоассистент»"
    d.text((70, 42), title, font=title_font, fill=(15, 25, 45))

    table_x0, table_y0 = 60, 140
    table_x1, table_y1 = w - 60, h - 140
    d.rectangle((table_x0, table_y0, table_x1, table_y1), outline=(80, 95, 130), width=3)

    cols = [0.18, 0.21, 0.22, 0.19, 0.20]
    col_x = [table_x0]
    for c in cols:
        col_x.append(col_x[-1] + int((table_x1 - table_x0) * c))
    col_x[-1] = table_x1

    header_h = 88
    row_h = (table_y1 - table_y0 - header_h) // 2
    y_header = table_y0 + header_h
    y_row2 = y_header + row_h

    d.rectangle((table_x0, table_y0, table_x1, y_header), fill=(225, 236, 252), outline=(80, 95, 130), width=2)
    d.line((table_x0, y_header, table_x1, y_header), fill=(80, 95, 130), width=2)
    d.line((table_x0, y_row2, table_x1, y_row2), fill=(80, 95, 130), width=2)

    for x in col_x[1:-1]:
        d.line((x, table_y0, x, table_y1), fill=(80, 95, 130), width=2)

    headers = [
        "БД / источник",
        "Назначение",
        "Состав / классы",
        "Объем",
        "Где используется",
    ]
    for i, htxt in enumerate(headers):
        draw_wrapped(d, htxt, (col_x[i], table_y0, col_x[i + 1], y_header), head_font, fill=(20, 35, 65))

    row1 = [
        "MRL Eye Dataset",
        "Обучение CNN-моделей определения состояния глаза",
        "2 класса: open / closed",
        "84 898 изображений\nTrain: 67 919\nVal: 16 979\nopen: 21 725 (25.6%)\nclosed: 63 173 (74.4%)",
        "src/training/*\nмодели: ResNet-18, MobileNetV3",
    ]
    row2 = [
        "MediaPipe Face Landmarker (.task)",
        "Готовая предобученная модель для blink-признаков",
        "blendshapes eyeBlink_L / eyeBlink_R",
        "~3.6 МБ",
        "src/analysis/eyes.py\nосновной режим в приложении",
    ]

    for i, txt in enumerate(row1):
        draw_wrapped(d, txt, (col_x[i], y_header, col_x[i + 1], y_row2), body_font)
    for i, txt in enumerate(row2):
        draw_wrapped(d, txt, (col_x[i], y_row2, col_x[i + 1], table_y1), body_font)

    foot = "Примечание: в проекте для инференса используется MediaPipe, а CNN-модели обучаются на MRL Eye Dataset."
    d.text((64, h - 100), foot, font=foot_font, fill=(90, 95, 110))

    img.save(out_path)
    print(out_path.resolve())


if __name__ == "__main__":
    main()

