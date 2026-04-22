from __future__ import annotations

import sys
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from concurrent.futures import ThreadPoolExecutor, as_completed

from src.config.settings import AppSettings, load_settings, save_settings
from src.ui.gallery import AlbumGallery
from src.utils.file_ops import iter_images_for_sorting, prepare_output_dirs, move_with_reason

if TYPE_CHECKING:
    from src.analysis.pipeline import AnalysisResult, PhotoAnalyzer

# Светлая минималистичная тема (mac-like)
COLORS = {
    "bg": "#f5f5f7",
    "surface": "#ffffff",
    "fg": "#1d1d1f",
    "muted": "#6e6e73",
    "line": "#e5e5ea",
    "accent": "#0071e3",
    "accent_hover": "#2487ea",
    "success": "#28a745",
    "danger": "#ff3b30",
}


def _apply_theme(root: tk.Tk) -> None:
    root.configure(bg=COLORS["bg"])
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    c = COLORS
    style.configure(".", background=c["bg"], foreground=c["fg"], fieldbackground=c["surface"])
    style.configure("TFrame", background=c["bg"])
    style.configure("TLabel", background=c["bg"], foreground=c["fg"])
    style.configure("TLabelframe", background=c["bg"], foreground=c["fg"], bordercolor=c["line"], relief="solid")
    style.configure("TLabelframe.Label", background=c["bg"], foreground=c["accent"])
    style.configure("TNotebook", background=c["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=c["surface"], foreground=c["muted"], padding=(16, 9), borderwidth=0)
    style.map("TNotebook.Tab", foreground=[("selected", c["fg"])], background=[("selected", c["surface"])])
    style.configure(
        "TButton",
        background=c["accent"],
        foreground="#ffffff",
        padding=(12, 8),
        font=("SF Pro Text", 10, "bold"),
        borderwidth=0,
    )
    style.map("TButton", background=[("active", c["accent_hover"]), ("disabled", "#d2d2d7")])
    style.configure("Danger.TButton", background=c["danger"], foreground="#ffffff", borderwidth=0)
    style.map("Danger.TButton", background=[("active", "#ff6b63")])
    style.configure("Secondary.TButton", background="#ebebef", foreground=c["fg"], borderwidth=0, padding=(10, 8))
    style.map("Secondary.TButton", background=[("active", "#dcdce1")])
    style.configure("Nav.TButton", background=c["bg"], foreground=c["muted"], borderwidth=0, padding=(12, 10))
    style.map("Nav.TButton", background=[("active", "#e9e9ef")], foreground=[("active", c["fg"])])
    style.configure("NavActive.TButton", background="#e9f2ff", foreground=c["accent"], borderwidth=0, padding=(12, 10))
    style.configure("Horizontal.TProgressbar", troughcolor="#e5e5ea", background=c["accent"], thickness=8)


class PhotoAssistantApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        _apply_theme(self)
        self.title("ВКадре")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.after(30, self._apply_maximized_if_possible)

        self.source_dir: Optional[Path] = None
        self._stop_event = threading.Event()
        self._analysis_running = False
        self.analyzer: PhotoAnalyzer | None = None
        self._analysis_load_error: str | None = None
        self.settings = load_settings()

        self._build_ui()
        self._startup_log()
        self.after(50, self._load_analysis_stack)
        self.after_idle(self._focus_main_window)

    def _focus_main_window(self) -> None:
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass

    def _apply_maximized_if_possible(self) -> None:
        try:
            self.state("zoomed")
        except tk.TclError:
            pass

    def _load_analysis_stack(self) -> None:
        """Импорт cv2/pipeline в фоне — иначе exe блокирует главный поток до mainloop и UI «мёртвый»."""

        def load() -> None:
            try:
                from src.analysis.pipeline import PhotoAnalyzer as _PhotoAnalyzer

                analyzer = _PhotoAnalyzer()
            except Exception as e:  # noqa: BLE001
                self.after(0, lambda err=e: self._on_analysis_load_failed(err))
                return
            self.after(0, lambda a=analyzer: self._on_analysis_load_ready(a))

        threading.Thread(target=load, daemon=True).start()

    def _on_analysis_load_failed(self, err: BaseException) -> None:
        self._analysis_load_error = str(err)
        self.log(f"Не удалось загрузить модуль анализа: {err}")

    def _on_analysis_load_ready(self, analyzer: PhotoAnalyzer) -> None:
        self.analyzer = analyzer
        self.log("Движок анализа готов")
        self._sync_start_button_state()

    def _sync_start_button_state(self) -> None:
        if self._analysis_running:
            return
        can_start = self.source_dir is not None and self.analyzer is not None
        self.start_btn.configure(state=tk.NORMAL if can_start else tk.DISABLED)

    def _workspace(self) -> Optional[Path]:
        return self.source_dir

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg=COLORS["surface"], height=64)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(
            header,
            text="ВКадре",
            font=("SF Pro Display", 17, "bold"),
            bg=COLORS["surface"],
            fg=COLORS["fg"],
        ).pack(side=tk.LEFT, padx=20, pady=14)
        tk.Label(
            header,
            text="Быстрая сортировка фотографий",
            font=("SF Pro Text", 10),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
        ).pack(side=tk.LEFT, pady=15)

        root_body = ttk.Frame(self)
        root_body.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(root_body, bg=COLORS["surface"], width=220)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="Рабочие разделы",
            font=("SF Pro Text", 10),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
        ).pack(anchor=tk.W, padx=14, pady=(14, 8))

        self.nav_analyze_btn = ttk.Button(sidebar, text="Анализ", style="NavActive.TButton", command=lambda: self._show_page("analyze"))
        self.nav_analyze_btn.pack(fill=tk.X, padx=12, pady=4)
        self.nav_gallery_btn = ttk.Button(sidebar, text="Альбомы", style="Nav.TButton", command=lambda: self._show_page("gallery"))
        self.nav_gallery_btn.pack(fill=tk.X, padx=12, pady=4)
        self.nav_settings_btn = ttk.Button(
            sidebar, text="Настройки", style="Nav.TButton", command=lambda: self._show_page("settings")
        )
        self.nav_settings_btn.pack(fill=tk.X, padx=12, pady=4)

        ttk.Separator(sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=12, pady=10)
        tk.Label(
            sidebar,
            text="Совет: сначала выберите папку,\nпотом запустите анализ.",
            justify=tk.LEFT,
            font=("SF Pro Text", 10),
            bg=COLORS["surface"],
            fg=COLORS["muted"],
        ).pack(anchor=tk.W, padx=14)

        # Main area
        self.page_host = ttk.Frame(root_body, padding=12)
        self.page_host.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.page_analyze = ttk.Frame(self.page_host)
        self.page_gallery = ttk.Frame(self.page_host)
        self.page_settings = ttk.Frame(self.page_host)
        self.page_analyze.pack(fill=tk.BOTH, expand=True)
        self._build_analyze_tab(self.page_analyze)
        self.gallery = AlbumGallery(self.page_gallery, self._workspace, COLORS)
        self.gallery.pack(fill=tk.BOTH, expand=True)
        self._build_settings_tab(self.page_settings)
        self._active_page = "analyze"

    def _build_analyze_tab(self, parent: ttk.Frame) -> None:
        row1 = ttk.Frame(parent)
        row1.pack(fill=tk.X, pady=(0, 12))
        self.folder_label = ttk.Label(row1, text="Папка не выбрана", font=("SF Pro Text", 10))
        self.folder_label.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(row1, text="Папка", command=self.select_folder, style="Secondary.TButton").pack(
            side=tk.LEFT, padx=4
        )
        self.start_btn = ttk.Button(row1, text="Запустить анализ", command=self.start_analysis, state=tk.DISABLED)
        self.start_btn.pack(side=tk.LEFT, padx=4)
        self.stop_btn = ttk.Button(
            row1, text="Остановить", command=self.stop_analysis, state=tk.DISABLED, style="Danger.TButton"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=4)

        ttk.Button(row1, text="Открыть удачные", command=self.open_good_folder, style="Secondary.TButton").pack(
            side=tk.RIGHT, padx=4
        )
        ttk.Button(row1, text="Открыть неудачные", command=self.open_bad_folder, style="Secondary.TButton").pack(
            side=tk.RIGHT, padx=4
        )

        pf = ttk.LabelFrame(parent, text="Статус", padding=8)
        pf.pack(fill=tk.X, pady=(0, 12))
        self.progress_var = tk.DoubleVar(value=0.0)
        ttk.Progressbar(pf, variable=self.progress_var, maximum=100, mode="determinate").pack(fill=tk.X, pady=(0, 8))
        self.stats_var = tk.StringVar(value="0 обработано  •  0 удачных  •  0 неудачных")
        ttk.Label(pf, textvariable=self.stats_var, font=("SF Pro Text", 10)).pack(anchor=tk.W)

        lf = ttk.LabelFrame(parent, text="Лента", padding=4)
        lf.pack(fill=tk.BOTH, expand=True)
        self.log_text = tk.Text(
            lf,
            height=18,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=COLORS["surface"],
            fg=COLORS["fg"],
            insertbackground=COLORS["fg"],
            relief=tk.FLAT,
            padx=8,
            pady=8,
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(lf, command=self.log_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=sb.set)

    def _startup_log(self) -> None:
        self.log("Готово")

    def _build_settings_tab(self, parent: ttk.Frame) -> None:
        card = ttk.LabelFrame(parent, text="Критерии анализа", padding=12)
        card.pack(fill=tk.X, pady=(8, 12))

        self.low_var = tk.IntVar(value=self.settings.exposure_low_thresh)
        self.high_var = tk.IntVar(value=self.settings.exposure_high_thresh)
        self.frac_var = tk.DoubleVar(value=self.settings.exposure_extreme_fraction * 100.0)
        self.sharp_var = tk.DoubleVar(value=self.settings.sharpness_threshold)
        self.cnn_eye_var = tk.BooleanVar(value=self.settings.use_cnn_eye_check)

        def row(title: str, widget: tk.Widget, hint: str) -> None:
            r = ttk.Frame(card)
            r.pack(fill=tk.X, pady=6)
            ttk.Label(r, text=title, width=38).pack(side=tk.LEFT)
            widget.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))
            ttk.Label(r, text=hint, foreground=COLORS["muted"]).pack(side=tk.LEFT)

        low_scale = ttk.Scale(card, from_=0, to=80, variable=self.low_var, orient=tk.HORIZONTAL)
        row("Недосвет (темные пиксели <=)", low_scale, "0..80")

        high_scale = ttk.Scale(card, from_=180, to=255, variable=self.high_var, orient=tk.HORIZONTAL)
        row("Пересвет (светлые пиксели >=)", high_scale, "180..255")

        frac_scale = ttk.Scale(card, from_=1, to=35, variable=self.frac_var, orient=tk.HORIZONTAL)
        row("Доля выбитых пикселей, %", frac_scale, "1..35")

        sharp_scale = ttk.Scale(card, from_=10, to=350, variable=self.sharp_var, orient=tk.HORIZONTAL)
        row("Порог резкости (Laplacian)", sharp_scale, "10..350")

        cnn_row = ttk.Frame(card)
        cnn_row.pack(fill=tk.X, pady=6)
        ttk.Label(cnn_row, text="Доп. проверка глаз (mediapipe, models/eye_state_resnet18.pth)", width=38).pack(
            side=tk.LEFT
        )
        ttk.Checkbutton(cnn_row, variable=self.cnn_eye_var).pack(side=tk.LEFT, padx=(8, 8))
        ttk.Label(
            cnn_row,
            text="по умолч. выкл.; только при необходимости",
            foreground=COLORS["muted"],
        ).pack(side=tk.LEFT)

        act = ttk.Frame(card)
        act.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(act, text="Сохранить", command=self._save_settings).pack(side=tk.LEFT)
        ttk.Button(act, text="Сбросить", style="Secondary.TButton", command=self._reset_settings).pack(side=tk.LEFT, padx=8)

        note = ttk.Label(
            parent,
            text="Изменения применяются к новым запускам анализа и сохраняются в app_settings.json",
            foreground=COLORS["muted"],
        )
        note.pack(anchor=tk.W, pady=(0, 6))

    def _save_settings(self) -> None:
        low = int(round(self.low_var.get()))
        high = int(round(self.high_var.get()))
        if high <= low:
            messagebox.showwarning("Настройки", "Порог пересвета должен быть выше порога недосвета.")
            return
        self.settings = AppSettings(
            exposure_low_thresh=max(0, min(80, low)),
            exposure_high_thresh=max(180, min(255, high)),
            exposure_extreme_fraction=max(0.01, min(0.35, float(self.frac_var.get()) / 100.0)),
            sharpness_threshold=max(10.0, min(350.0, float(self.sharp_var.get()))),
            use_cnn_eye_check=bool(self.cnn_eye_var.get()),
            eye_classifier_weights=self.settings.eye_classifier_weights,
        )
        save_settings(self.settings)
        self.log("Настройки сохранены")
        messagebox.showinfo("Настройки", "Критерии сохранены.")

    def _reset_settings(self) -> None:
        self.settings = AppSettings()
        self.low_var.set(self.settings.exposure_low_thresh)
        self.high_var.set(self.settings.exposure_high_thresh)
        self.frac_var.set(self.settings.exposure_extreme_fraction * 100.0)
        self.sharp_var.set(self.settings.sharpness_threshold)
        self.cnn_eye_var.set(self.settings.use_cnn_eye_check)
        save_settings(self.settings)
        self.log("Настройки сброшены")

    def _show_page(self, page: str) -> None:
        if page == self._active_page:
            return
        self.page_analyze.pack_forget()
        self.page_gallery.pack_forget()
        self.page_settings.pack_forget()
        if page == "gallery":
            self.page_gallery.pack(fill=tk.BOTH, expand=True)
            self.gallery.refresh_albums()
            self.nav_gallery_btn.configure(style="NavActive.TButton")
            self.nav_analyze_btn.configure(style="Nav.TButton")
            self.nav_settings_btn.configure(style="Nav.TButton")
        elif page == "settings":
            self.page_settings.pack(fill=tk.BOTH, expand=True)
            self.nav_settings_btn.configure(style="NavActive.TButton")
            self.nav_analyze_btn.configure(style="Nav.TButton")
            self.nav_gallery_btn.configure(style="Nav.TButton")
        else:
            self.page_analyze.pack(fill=tk.BOTH, expand=True)
            self.nav_analyze_btn.configure(style="NavActive.TButton")
            self.nav_gallery_btn.configure(style="Nav.TButton")
            self.nav_settings_btn.configure(style="Nav.TButton")
        self._active_page = page

    def log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
        self.update_idletasks()

    def select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Папка с фотографиями")
        if not folder:
            return
        self.source_dir = Path(folder)
        self.folder_label.configure(text=str(self.source_dir))
        self._sync_start_button_state()
        self.log("Папка выбрана")
        self.gallery.refresh_albums()

    def stop_analysis(self) -> None:
        if self._analysis_running:
            self._stop_event.set()
            self.log("Остановка...")

    def start_analysis(self) -> None:
        if not self.source_dir:
            messagebox.showwarning("Папка", "Сначала выберите папку.")
            return
        if self._analysis_running:
            return
        if self.analyzer is None:
            if self._analysis_load_error:
                messagebox.showerror("Анализ", f"Модуль анализа не загружен:\n{self._analysis_load_error}")
            else:
                messagebox.showinfo("Анализ", "Подождите несколько секунд — загружается движок анализа.")
            return

        self._stop_event.clear()
        self._analysis_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)

        good_dir, bad_dir = prepare_output_dirs(self.source_dir)
        image_files = list(iter_images_for_sorting(self.source_dir))
        total = len(image_files)
        if total == 0:
            messagebox.showinfo("Нет файлов", "Нет .jpg / .jpeg / .png в папке (включая подпапки).")
            self._finish_analysis_ui()
            return

        self.log(f"К обработке: {total} фото")

        batch_size = 4

        def worker() -> None:
            from src.analysis.pipeline import AnalysisResult

            processed = good_count = bad_count = 0
            idx = 0

            def update_ui(name: str, verdict: str, pv: int, gv: int, bv: int) -> None:
                self.log(f"{name}: {verdict}")
                if total > 0:
                    self.progress_var.set(min(100.0, pv / total * 100.0))
                self.stats_var.set(f"{pv} обработано  •  {gv} удачных  •  {bv} неудачных")

            try:
                while idx < len(image_files) and not self._stop_event.is_set():
                    batch = image_files[idx : idx + batch_size]
                    idx += len(batch)
                    with ThreadPoolExecutor(max_workers=min(batch_size, len(batch))) as ex:
                        futs = {ex.submit(self.analyzer.analyze, p, self.settings): p for p in batch}
                        for fut in as_completed(futs):
                            if self._stop_event.is_set():
                                break
                            path = futs[fut]
                            try:
                                result: AnalysisResult = fut.result()
                            except Exception as e:  # noqa: BLE001
                                self.after(0, self.log, f"[ОШИБКА] {path.name}: {e}")
                                continue
                            target = good_dir if result.is_good else bad_dir
                            move_with_reason(path, target, result.reason)
                            processed += 1
                            if result.is_good:
                                good_count += 1
                                v = "УДАЧНОЕ"
                            else:
                                bad_count += 1
                                v = f"НЕУДАЧНОЕ ({result.reason})"
                            self.after(0, update_ui, path.name, v, processed, good_count, bad_count)
            finally:

                def finish() -> None:
                    self._finish_analysis_ui()
                    if self._stop_event.is_set():
                        self.log(f"Остановлено: {processed}/{total}")
                    else:
                        self.log("Анализ завершён.")
                    self.gallery.refresh_albums()

                self.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_analysis_ui(self) -> None:
        self._analysis_running = False
        self._sync_start_button_state()
        self.stop_btn.configure(state=tk.DISABLED)

    def open_good_folder(self) -> None:
        if self.source_dir:
            d = self.source_dir / "Удачные"
            if d.exists():
                self._open_dir(d)

    def open_bad_folder(self) -> None:
        if self.source_dir:
            d = self.source_dir / "Неудачные"
            if d.exists():
                self._open_dir(d)

    @staticmethod
    def _open_dir(path: Path) -> None:
        if sys.platform.startswith("win"):
            import os

            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            import subprocess

            subprocess.Popen(["open", str(path)])
        else:
            import subprocess

            subprocess.Popen(["xdg-open", str(path)])


def main() -> None:
    app = PhotoAssistantApp()
    app.mainloop()


if __name__ == "__main__":
    main()
