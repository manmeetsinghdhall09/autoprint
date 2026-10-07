# AI File Sorter

Sorts a folder's files into category folders based on **what's inside them**. It uses a local AI model that runs on your own GPU through [Ollama](https://ollama.com). File contents never leave your PC.

## Setup (once)

1. Install Ollama from https://ollama.com. On NVIDIA and AMD cards it uses your GPU automatically.
2. Download a model:
   ```
   ollama pull llama3.2
   ollama pull qwen2.5vl        (optional: lets it look at photos/screenshots)
   ```
3. Install the reader libraries for PDF, Word, Excel and PowerPoint files:
   ```
   pip install -r requirements.txt
   ```

## Use

```
python sorter.py "C:\Users\you\Downloads"                 # preview only, moves nothing
python sorter.py "C:\Users\you\Downloads" --apply         # actually move files
python sorter.py "C:\Users\you\Downloads" --recursive --vision-model qwen2.5vl --apply
python sorter.py --undo "C:\Users\you\Downloads\sort_log_20261007_120000.json"
```

You can also drag a folder onto `sort_folder.bat`.

* Files go to `<folder>\Sorted\<Category>\` (change this with `--dest`).
* Every run saves a `sort_plan_*.csv` that lists each file, where it goes, and why.
* `--apply` writes a `sort_log_*.json` that `--undo` uses to put everything back.
* Pick your own categories: `--categories Taxes School Work Photos Memes Other`
* Bigger models sort more accurately but run slower. Try `--model qwen2.5:7b` or `--model llama3.1:8b` if your GPU has 8 GB or more of VRAM.

Text, code, PDF, DOCX, XLSX and PPTX files are read by the model. Images are read too when you pass `--vision-model`. Music, video, installers, archives, and files with no readable text are sorted by file type.
System folders (Windows, Program Files, AppData, etc.), hidden files and `.git` folders are always skipped. Don't point the sorter at `C:\` itself. Use it on your personal folders: Downloads, Desktop, Documents.
