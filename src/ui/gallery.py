"""
Встроенный просмотр альбомов (Удачные / Неудачные) с превью и сеткой миниатюр.
"""
from __future__ import annotations

import sys
import tkinter as tk
import shutil
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PIL import Image, ImageTk
from tkinter import ttk, messagebox


IMAGE_EXT = {".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"}
THUMB_SIZE = (140, 140)
PREVIEW_MAX = (720, 520)


def collect_albums(base: Path) -> List[Tuple[str, Path]]:
    out: List[Tuple[str, Path]] = []
    if not base or not base.is_dir():
        return out
    good = base / "Удачные"
    if good.is_dir():
        # Общий альбом удачных
        out.append(("✓ Удачные (все)", good))
        # И отдельные подпапки внутри удачных (если есть)
        for sub in sorted(good.iterdir(), key=lambda p: p.name.lower()):
            if sub.is_dir():
                out.append((f"✓ Удачные / {sub.name}", sub))
    bad = base / "Неудачные"
    if bad.is_dir():
        for sub in sorted(bad.iterdir(), key=lambda p: p.name.lower()):
            if sub.is_dir():
                out.append((f"✗ Неудачные / {sub.name}", sub))
    return out


def list_images(folder: Path) -> List[Path]:
    if not folder.is_dir():
        return []
    # Файлы могут лежать в подпапках (например, по причинам сортировки),
    # поэтому отображаем рекурсивно весь альбом.
    return sorted(
        [p for p in folder.rglob("*") if p.is_file() and p.suffix in IMAGE_EXT],
        key=lambda p: p.name.lower(),
    )


class AlbumGallery(ttk.Frame):
    def __init__(self, parent, get_workspace: Callable[[], Optional[Path]], colors: dict, **kw) -> None:
        super().__init__(parent, **kw)
        self._get_workspace = get_workspace
        self._colors = colors
        self._thumb_refs: List[ImageTk.PhotoImage] = []
        self._preview_ref: Optional[ImageTk.PhotoImage] = None
        self._selected_image: Optional[Path] = None
        self._selected_images: set[Path] = set()
        self._thumb_frames: dict[Path, tk.Frame] = {}
        self._wheel_bound = False
        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(top, text="Обновить", command=self.refresh_albums, style="Secondary.TButton").pack(side=tk.LEFT)
        self.move_target_var = tk.StringVar(value="")
        self.move_target = ttk.Combobox(top, textvariable=self.move_target_var, state="readonly", width=34)
        self.move_target.pack(side=tk.RIGHT, padx=6)
        ttk.Button(top, text="Перенести фото", command=self.move_selected_image, style="Secondary.TButton").pack(
            side=tk.RIGHT, padx=6
        )
        ttk.Label(
            top,
            text="",
            foreground=self._colors.get("muted", "#888"),
        ).pack(side=tk.LEFT, padx=16)

        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        left = ttk.Frame(paned, width=240)
        paned.add(left, weight=0)
        ttk.Label(left, text="Альбомы", foreground=self._colors.get("muted", "#888")).pack(anchor=tk.W, pady=(0, 6))
        self.album_list = tk.Listbox(
            left,
            height=22,
            font=("SF Pro Text", 10),
            bg=self._colors["surface"],
            fg=self._colors["fg"],
            selectbackground=self._colors["accent"],
            selectforeground="#ffffff",
            relief=tk.FLAT,
            highlightthickness=0,
        )
        sb1 = ttk.Scrollbar(left, command=self.album_list.yview)
        self.album_list.config(yscrollcommand=sb1.set)
        self.album_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)
        self.album_list.bind("<<ListboxSelect>>", self._on_album_pick)

        right = ttk.Frame(paned)
        paned.add(right, weight=1)

        preview_frame = tk.Frame(right, bg=self._colors["surface"])
        preview_frame.pack(fill=tk.X, pady=(0, 8))
        self.preview_label = tk.Label(
            preview_frame,
            bg=self._colors["surface"],
            fg=self._colors["muted"],
            text="Выберите фото внизу",
            pady=24,
        )
        self.preview_label.pack(expand=True)

        grid_outer = ttk.Frame(right)
        grid_outer.pack(fill=tk.BOTH, expand=True)
        self._thumb_canvas = tk.Canvas(
            grid_outer,
            bg=self._colors["bg"],
            highlightthickness=0,
        )
        scroll = ttk.Scrollbar(grid_outer, orient=tk.VERTICAL, command=self._thumb_canvas.yview)
        self.thumb_inner = tk.Frame(self._thumb_canvas, bg=self._colors["bg"])
        self.thumb_inner.bind(
            "<Configure>",
            lambda e: self._thumb_canvas.configure(scrollregion=self._thumb_canvas.bbox("all")),
        )
        self._thumb_canvas.create_window((0, 0), window=self.thumb_inner, anchor=tk.NW)

        def on_wheel(event) -> None:
            if sys.platform == "darwin":
                self._thumb_canvas.yview_scroll(int(-1 * event.delta), "units")
            else:
                self._thumb_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def on_wheel_linux(event) -> None:
            if event.num == 4:
                self._thumb_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self._thumb_canvas.yview_scroll(1, "units")

        def on_enter(_):
            if not self._wheel_bound:
                self._thumb_canvas.bind_all("<MouseWheel>", on_wheel)
                self._thumb_canvas.bind_all("<Button-4>", on_wheel_linux)
                self._thumb_canvas.bind_all("<Button-5>", on_wheel_linux)
                self._wheel_bound = True

        def on_leave(_):
            self._thumb_canvas.unbind_all("<MouseWheel>")
            self._thumb_canvas.unbind_all("<Button-4>")
            self._thumb_canvas.unbind_all("<Button-5>")
            self._wheel_bound = False

        self._thumb_canvas.bind("<Enter>", on_enter)
        self._thumb_canvas.bind("<Leave>", on_leave)
        self._thumb_canvas.configure(yscrollcommand=scroll.set)
        self._thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._album_paths: List[Path] = []
        self._album_labels: List[str] = []

    def refresh_albums(self) -> None:
        base = self._get_workspace()
        self.album_list.delete(0, tk.END)
        self._album_paths.clear()
        self._album_labels.clear()
        self._clear_thumbs()
        self.preview_label.configure(image="", text="Выберите альбом")
        self._preview_ref = None
        self._selected_image = None
        self._selected_images.clear()
        if not base:
            return
        for label, path in collect_albums(base):
            self.album_list.insert(tk.END, label)
            self._album_paths.append(path)
            self._album_labels.append(label)
        self.move_target["values"] = self._album_labels
        if self._album_labels:
            self.move_target_var.set(self._album_labels[0])
        if self._album_paths:
            self.album_list.selection_set(0)
            self._load_album(0)

    def _on_album_pick(self, _evt=None) -> None:
        sel = self.album_list.curselection()
        if not sel:
            return
        self._load_album(int(sel[0]))

    def _load_album(self, index: int) -> None:
        if index < 0 or index >= len(self._album_paths):
            return
        folder = self._album_paths[index]
        self._clear_thumbs()
        self.preview_label.configure(image="", text=f"Загрузка… ({folder.name})")
        self._preview_ref = None
        self._selected_image = None
        self._selected_images.clear()
        images = list_images(folder)
        cols = 5
        for i, path in enumerate(images):
            row, col = divmod(i, cols)
            try:
                img = Image.open(path)
                img.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
                ph = ImageTk.PhotoImage(img)
                self._thumb_refs.append(ph)
            except Exception:
                continue
            fr = tk.Frame(
                self.thumb_inner,
                bg=self._colors["surface"],
                padx=6,
                pady=6,
                highlightthickness=1,
                highlightbackground="#ececf1",
            )
            fr.grid(row=row, column=col, padx=4, pady=4, sticky=tk.NW)
            self._thumb_frames[path] = fr
            lbl = tk.Label(fr, image=ph, bg=self._colors["surface"], cursor="hand2")
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, p=path: self._select_single_and_preview(p))
            lbl.bind("<Control-Button-1>", lambda e, p=path: self._toggle_selection_and_preview(p))
        self._thumb_canvas.update_idletasks()
        self._thumb_canvas.configure(scrollregion=self._thumb_canvas.bbox("all"))
        if not images:
            self.preview_label.configure(text="Нет изображений в этом альбоме")

    def _clear_thumbs(self) -> None:
        self._thumb_refs.clear()
        self._thumb_frames.clear()
        for w in self.thumb_inner.winfo_children():
            w.destroy()

    def _refresh_thumb_selection_ui(self) -> None:
        for path, frame in self._thumb_frames.items():
            if path in self._selected_images:
                frame.configure(highlightbackground=self._colors["accent"], highlightthickness=2)
            else:
                frame.configure(highlightbackground="#ececf1", highlightthickness=1)

    def _select_single_and_preview(self, path: Path) -> None:
        self._selected_images.clear()
        self._selected_images.add(path)
        self._refresh_thumb_selection_ui()
        self._show_preview(path)

    def _toggle_selection_and_preview(self, path: Path) -> None:
        if path in self._selected_images:
            self._selected_images.remove(path)
        else:
            self._selected_images.add(path)
        self._refresh_thumb_selection_ui()
        self._show_preview(path)

    def _show_preview(self, path: Path) -> None:
        try:
            img = Image.open(path)
            img.thumbnail(PREVIEW_MAX, Image.Resampling.LANCZOS)
            self._preview_ref = ImageTk.PhotoImage(img)
            self.preview_label.configure(image=self._preview_ref, text="")
            self._selected_image = path
        except Exception as e:
            self.preview_label.configure(image="", text=str(e))

    def move_selected_image(self) -> None:
        selected = [p for p in self._selected_images if p.exists()]
        if not selected and self._selected_image is not None and self._selected_image.exists():
            selected = [self._selected_image]
        if not selected:
            messagebox.showinfo("Перенос", "Сначала выберите фото в альбоме.")
            return
        target_label = self.move_target_var.get().strip()
        if not target_label or target_label not in self._album_labels:
            messagebox.showwarning("Перенос", "Выберите целевой альбом.")
            return
        target_idx = self._album_labels.index(target_label)
        target_dir = self._album_paths[target_idx]
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        moved = 0
        for src in selected:
            if src.parent.resolve() == target_dir.resolve():
                continue
            dst = target_dir / src.name
            i = 1
            while dst.exists():
                dst = target_dir / f"{src.stem}_{i}{src.suffix}"
                i += 1
            try:
                shutil.move(str(src), str(dst))
                moved += 1
            except Exception as e:  # noqa: BLE001
                messagebox.showerror("Перенос", f"Не удалось перенести {src.name}:\n{e}")
                return

        self.refresh_albums()
        messagebox.showinfo("Перенос", f"Перенесено: {moved} фото в «{target_label}».")
