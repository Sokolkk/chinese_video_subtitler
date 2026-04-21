# Chinese Video Subtitler

Программа с GUI, которая:
- открывает китайское видео по кнопке;
- распознает речь;
- создает рядом с видео файлы субтитров:
  - `*_subtitles.txt`
  - `*_subtitles.srt`

## Установка

1. Установите Python 3.9+.
2. Установите [ffmpeg](https://ffmpeg.org/download.html) и добавьте его в `PATH`.
3. Установите зависимости:

```powershell
cd C:\Users\SS\Desktop\codex\chinese_video_subtitler
pip install -r requirements.txt
```

## Запуск

```powershell
cd C:\Users\SS\Desktop\codex\chinese_video_subtitler
python app.py
```

## Как использовать

1. Нажмите `Открыть видео` и выберите файл.
2. Нажмите `Создать субтитры`.
3. Дождитесь окончания обработки.

По умолчанию язык распознавания `zh` (китайский).
