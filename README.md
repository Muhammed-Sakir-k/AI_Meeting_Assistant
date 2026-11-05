# AI Meeting Assistant

An AI-powered meeting documentation system for transcribing meeting audio, summarizing discussions, and extracting decisions and action items.

## Features

- Audio preprocessing and English/Malayalam transcription with Whisper.
- Action-item, question, and sentiment analysis.
- Meeting summaries, translations, and PDF/DOCX reports.
- FastAPI backend and a React dashboard.
- SQLite by default, with optional MySQL configuration.
- Optional Celery/Redis task dispatch; uploads fall back to FastAPI background tasks when no Celery worker is available.

## Requirements

- Windows 10/11
- Python 3.10 (recommended; the pinned PyTorch dependency may not support newer Python versions)
- Git
- An internet connection on first run to download AI models
- FFmpeg for audio formats that require conversion (such as MP3, M4A, and WebM)
- Node.js/npm only if you want to rebuild the frontend; a compiled dashboard is included

## Install and run on Windows

Open PowerShell and run these commands. Replace the repository URL if you cloned this project from a fork:

```powershell
git clone https://github.com/Muhammed-Sakir-k/AI_Meeting_Assistant.git
cd AI_Meeting_Assistant

# Confirm Python 3.10 is installed
py -3.10 --version

# Create and activate a virtual environment
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install the Python dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Create your local configuration (SQLite is the default)
Copy-Item .env.example .env

# Start the application
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

If PowerShell prevents virtual-environment activation, allow it for the current terminal and activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open **http://127.0.0.1:8000/** in your browser. Keep the terminal open while using the app; press **Ctrl+C** there to stop the server.

The first audio-processing run can download Whisper and Hugging Face models and may take several minutes. spaCy downloads its English model when needed. Model files are stored locally under `models/`.

### FFmpeg (for audio conversion)

Install FFmpeg and make sure `ffmpeg -version` works in a new terminal. On Windows, you can install a winget package if winget is available:

```powershell
winget install --id Gyan.FFmpeg.Shared --exact
```

Restart PowerShell after installation so the updated PATH is loaded. WAV uploads may work without FFmpeg; other audio formats can require it.

### Optional: rebuild the frontend

Node.js is not needed to run the included compiled dashboard. To rebuild it after changing frontend source:

```powershell
cd frontend
npm ci
npm run build
cd ..
```

## Configuration

Edit your local `.env` file to configure the application. Do not commit this file or put credentials in the public repository.

- SQLite is the default and requires no separate database server.
- To use MySQL, set `DB_TYPE=mysql` and configure `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`. Create the database first.
- Redis and a Celery worker are optional. Without an active worker, uploaded meetings are processed using FastAPI background tasks.
- `WHISPER_MODEL`, `WHISPER_DEVICE`, `NLP_MODEL`, and `SUMMARIZATION_MODEL` select the AI models and device.

The SQLite database (`ai_meeting_assistant.db`), uploaded audio (`uploads/`), model cache (`models/`), and `.env` are local runtime data and are excluded from Git.

## API

- `POST /upload` — Upload a meeting audio file.
- `GET /status/{id}` — Check processing status.
- `GET /transcript/{id}` — Retrieve a transcript.
- `GET /summary/{id}` — Retrieve a summary and decisions.
- `GET /actions/{id}` — Retrieve action items.
- `GET /report/{id}?format=pdf|docx` — Download a report.
- `GET /search?q={query}` — Search meetings.

## Tests

Run the integration tests from the project root with the virtual environment activated:

```powershell
python -m pytest
```

## License

No license has been specified yet. Unless a license is added, standard copyright restrictions apply to reuse of this source.
