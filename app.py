import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from typing import Optional

import whisper


VIDEO_TYPES = [
    ("Видео файлы", "*.mp4 *.mkv *.avi *.mov *.flv *.wmv *.webm"),
    ("Все файлы", "*.*"),
]


def format_srt_time(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    secs = (total_ms % 60_000) // 1000
    millis = total_ms % 1000
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


class SubtitlerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Китайские субтитры из видео")
        self.root.geometry("700x260")
        self.root.resizable(False, False)

        self.video_path = tk.StringVar()
        self.status = tk.StringVar(value="Выберите видео и нажмите 'Создать субтитры'")
        self.output_dir: Optional[str] = None

        self.model_name = tk.StringVar(value="small")
        self.language = tk.StringVar(value="zh")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Видео файл:").pack(anchor="w")

        row = ttk.Frame(frame)
        row.pack(fill="x", pady=(6, 14))

        path_entry = ttk.Entry(row, textvariable=self.video_path)
        path_entry.pack(side="left", fill="x", expand=True)

        ttk.Button(row, text="Открыть видео", command=self.pick_video).pack(side="left", padx=(8, 0))

        options = ttk.Frame(frame)
        options.pack(fill="x", pady=(0, 10))

        ttk.Label(options, text="Модель:").pack(side="left")
        ttk.Combobox(
            options,
            textvariable=self.model_name,
            values=["tiny", "base", "small", "medium", "large"],
            width=10,
            state="readonly",
        ).pack(side="left", padx=(8, 16))

        ttk.Label(options, text="Язык:").pack(side="left")
        ttk.Combobox(
            options,
            textvariable=self.language,
            values=["zh", "zh-cn", "zh-tw"],
            width=10,
            state="readonly",
        ).pack(side="left", padx=(8, 0))

        self.generate_button = ttk.Button(frame, text="Создать субтитры", command=self.start_transcription)
        self.generate_button.pack(anchor="w", pady=(2, 14))

        self.open_folder_button = ttk.Button(
            frame,
            text="Открыть папку результата",
            command=self.open_output_folder,
            state="disabled",
        )
        self.open_folder_button.pack(anchor="w", pady=(0, 10))

        help_text = (
            "Результат: рядом с видео будут созданы файлы:\n"
            "- <имя_видео>_subtitles.txt\n"
            "- <имя_видео>_subtitles.srt"
        )
        ttk.Label(frame, text=help_text).pack(anchor="w", pady=(12, 0))

        status_frame = ttk.Frame(frame)
        status_frame.pack(side="bottom", fill="x", pady=(10, 0))
        ttk.Label(status_frame, textvariable=self.status, foreground="#1f5f8b").pack(anchor="w")
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=660)
        self.progress.pack(fill="x", pady=(6, 0))

    def pick_video(self) -> None:
        file_path = filedialog.askopenfilename(title="Выберите видео", filetypes=VIDEO_TYPES)
        if file_path:
            self.video_path.set(file_path)

    def start_transcription(self) -> None:
        selected = self.video_path.get().strip()
        if not selected:
            self.status.set("Сначала выберите видео файл.")
            return

        if not os.path.exists(selected):
            self.status.set("Ошибка: указанный видео файл не существует.")
            return

        self.generate_button.config(state="disabled")
        self.open_folder_button.config(state="disabled")
        self.status.set("Обработка... это может занять несколько минут.")
        self.progress.start(10)

        worker = threading.Thread(target=self._transcribe, args=(selected,), daemon=True)
        worker.start()

    def _transcribe(self, video_file: str) -> None:
        try:
            model = whisper.load_model(self.model_name.get())
            result = model.transcribe(video_file, language=self.language.get(), task="transcribe", verbose=False)

            segments = result.get("segments", [])
            stem = Path(video_file).with_suffix("")
            txt_path = f"{stem}_subtitles.txt"
            srt_path = f"{stem}_subtitles.srt"

            with open(txt_path, "w", encoding="utf-8") as txt_out:
                for seg in segments:
                    line = seg.get("text", "").strip()
                    if line:
                        txt_out.write(line + "\n")

            with open(srt_path, "w", encoding="utf-8") as srt_out:
                for i, seg in enumerate(segments, start=1):
                    start = format_srt_time(float(seg.get("start", 0.0)))
                    end = format_srt_time(float(seg.get("end", 0.0)))
                    text = seg.get("text", "").strip()
                    if not text:
                        continue
                    srt_out.write(f"{i}\n{start} --> {end}\n{text}\n\n")

            self.root.after(0, self._on_success, txt_path, srt_path, str(Path(video_file).parent))
        except Exception as exc:
            self.root.after(0, self._on_error, str(exc))

    def _on_success(self, txt_path: str, srt_path: str, output_dir: str) -> None:
        self.progress.stop()
        self.generate_button.config(state="normal")
        self.output_dir = output_dir
        self.open_folder_button.config(state="normal")
        self.status.set(f"Готово: сохранено {Path(txt_path).name} и {Path(srt_path).name}")

    def _on_error(self, error_text: str) -> None:
        self.progress.stop()
        self.generate_button.config(state="normal")
        self.status.set(f"Ошибка: {error_text}. Проверьте whisper и ffmpeg.")

    def open_output_folder(self) -> None:
        if not self.output_dir:
            self.status.set("Папка результата пока недоступна.")
            return
        if not os.path.isdir(self.output_dir):
            self.status.set("Папка результата не найдена.")
            return
        os.startfile(self.output_dir)


def main() -> None:
    root = tk.Tk()
    SubtitlerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
