# SLIDE — AI Butler

> A locally-run voice assistant built around a single idea: your computer should listen to you, not the other way around.

SLIDE is a personal AI assistant that runs entirely on your own hardware. It understands voice commands in Spanish, executes tasks on your PC, and keeps a memory of what you ask it to do — no cloud required, no subscriptions, no data leaving your machine.

The assistant identifies itself as **AIDEN** (Adaptive Intelligence Dynamic Engine Node).

---

## What it can do

- **Wake word activation** — say "SLIDE", "DESPIERTA" or a few other phrases and it starts listening
- **Biometric login** — uses your webcam to confirm who you are before doing anything
- **Natural language commands** — powered by a local LLM with function calling, so it understands what you mean, not just what you literally say
- **App control** — opens applications, searches YouTube, browses Google
- **WhatsApp integration** — sends messages and makes calls to your saved contacts
- **Task scheduling** — tell it to do something at a specific time and it will
- **Voice responses** — talks back using a local TTS engine, no robotic voices
- **Self-programming** — you can tell it to learn a new skill and it writes the function itself

---

## Stack

| Layer | Technology |
|---|---|
| LLM | Ollama (hermes3) |
| Speech-to-text | FasterWhisper (medium) |
| Voice detection | Silero VAD |
| Text-to-speech | Kokoro TTS |
| Computer vision | face_recognition + OpenCV |
| UI | PySide6 + HTML/CSS/JS via QWebEngine |
| PC automation | PyAutoGUI |

---

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) running locally with the `hermes3` model pulled
- A working microphone
- Windows (some features rely on Windows APIs)

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running it

```bash
python Main.py
```

The assistant will ask you to look at the camera to authenticate. Once confirmed, it goes into standby and waits for a wake word.

---

## Project status

Active development. Core features work. Being expanded with new skills over time.

---

*Built as a personal project. Not intended for production use.*
