# F1 25 AI Race Engineer

> **Work in Progress — This project is unfinished and actively being developed. Expect bugs, missing features, and breaking changes.**
>
> **Vibe coded** — This project is being built with the help of Gemini, Claude, Kimi, and GitHub Copilot. The code quality reflects that. This will remain the case until I learn Python properly, so don't expect clean, idiomatic code throughout.

An AI-powered race engineer for F1 25 that reads live UDP telemetry from the game and speaks radio feedback to you in real time using a local TTS model. It monitors tyre wear, fuel, damage, lap times, and overheating — and responds like a real pit wall engineer.

---

## Requirements

- **Python 3.11.9** (recommended — other versions may work but are untested)
- **F1 25** on PC or console (with UDP telemetry enabled — see below)
- A **Gemini or OpenAI API key**
- I suggest getting a gemini key on **Google AI Studio**.
- **Linux**: `aplay` must be available (part of `alsa-utils`, pre-installed on most distros)
- **macOS**: `afplay` (ships with macOS, no action needed)
- **Windows**: No extra audio tools needed

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Foxo2345/F1-25-Race-Engineer.git
cd F1-25-Race-Engineer
```

### 2. Create a virtual environment

```bash
python3.11 -m venv venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `torch` is a large package (~2 GB). The first install will take a while. The TTS model weights are also downloaded automatically on first run.

---

## Configuration

On the first run, `config.json` is created automatically with default values. Edit it before running again, putting
your API key and changing the model if you want:

```json
{
  "udp_ip": "0.0.0.0",
  "udp_port": 20777,
  "api_provider": "gemini",
  "api_key": "YOUR_GEMINI_API_KEY_HERE",
  "api_url": "https://generativelanguage.googleapis.com/v1beta/openai",
  "ai_model": "gemini-2.5-flash",
  "backup_ai_model": "gemini-3.5-flash",
  "model_cooldown_seconds": 60,
  "personality": "friendly",
  "voice_name": "alba",
  "custom_voice_path": "",
  "wear_threshold": 10.0,
  "temp_threshold_high": 100
}
```

### Key settings

| Setting | Description |
|---|---|
| `api_provider` | `"gemini"` or `"openai"` |
| `api_key` | Your API key for the chosen provider |
| `api_url` | Base URL for the API (only change if using a custom OpenAI-compatible endpoint) |
| `ai_model` | Primary AI model to use |
| `backup_ai_model` | Fallback model if the primary hits a quota limit |
| `personality` | Engineer personality: `"friendly"`, `"professional"`, or `"aggressive"` |
| `voice_name` | Built-in TTS voice name (e.g. `"alba"`) |
| `custom_voice_path` | Path to a `.wav` file to clone a custom voice (leave empty to use `voice_name`) |
| `wear_threshold` | Tyre wear % increment that triggers an alert (default: every 10%) |
| `temp_threshold_high` | Tyre surface temperature (°C) that triggers an overheating alert |

---

## Enabling UDP Telemetry in F1 25

1. In F1 25, go to **Settings → Telemetry Settings**
2. Set **UDP Telemetry** to `On`
3. Set **UDP Broadcast Mode** to `Off`
4. Set **UDP IP Address** to the IP of the machine running this app (use `127.0.0.1` if running on the same PC)
5. Set **UDP Port** to `20777`
6. Set **UDP Send Rate** to `60Hz`
7. Set **UDP Format** to `2025`

---

## Running

Make sure your virtual environment is activated, then:

```bash
python main.py
```

The app will:
1. Load (or create) `config.json`
2. Start the TTS engine and download model weights on first run
3. Begin listening for UDP telemetry on the configured port
4. Wait until it receives a valid telemetry packet, then say **"Radio check. Connection established. Let's get to work."**

---

## Controls

| Action | What it does |
|---|---|
| **Num Lock** (global hotkey) | Triggers an immediate status update from anywhere, even mid-race in-game |
| **Enter** in the console | Same as Num Lock — requests a status update |
| **Type a question + Enter** | Ask the engineer anything (e.g. `"Should I pit this lap?"`) |
| **Ctrl+C** | Graceful shutdown |

> **Note:** The global Num Lock hotkey requires the `keyboard` library and may need administrator/root privileges on some systems. If it's unavailable, console input still works.

---

## What the Engineer Monitors

The engineer automatically triggers spoken radio messages for these events:
//At the moment though not automatically

- **Lap complete** — summary after every lap
- **Tyre wear** — alert at every `wear_threshold`% increment (default: 10%, 20%, 30%...)
- **Tyre overheating** — alert when surface temp exceeds `temp_threshold_high`
- **Damage** — alert when wing or mechanical damage increases
- **Fuel critical** — alert when less than 1.5 laps of fuel remain

---

## Project Structure

```
F1-25-Race-Engineer/
├── main.py               # Entry point — orchestrates all modules
├── config.json           # Auto-generated on first run (edit your API key here)
├── requirements.txt      # Python dependencies
├── ai/
│   └── client.py         # AI race engineer logic (Gemini / OpenAI)
├── telemetry/
│   ├── listener.py       # UDP socket listener and telemetry state
│   └── packets.py        # F1 25 UDP packet definitions (ctypes structs)
└── tts/
    ├── engine.py         # pocket-tts text-to-speech wrapper
    └── worker.py         # Background speech queue worker thread
```

---

## Troubleshooting

**No audio on Linux**
Make sure `aplay` is installed:
```bash
sudo apt install alsa-utils
```

**"keyboard" library not working on Linux**
The `keyboard` library requires root on Linux. Either run with `sudo`, or just use console input instead — the Num Lock hotkey is optional.

**TTS model not downloading**
The model weights are fetched automatically by `pocket-tts` on first run. Make sure you have an internet connection and enough disk space (~500 MB).

**No telemetry received**
- Double-check the UDP IP and port in both `config.json` and the F1 25 settings.
- If running the game on a console, set the IP in the game to your PC's local IP address (e.g. `192.168.x.x`), not `0.0.0.0`.
- Make sure no firewall is blocking UDP port `20777`.

**API quota errors**
The app automatically switches to `backup_ai_model` when the primary model hits a quota limit. If both are exhausted, it falls back to pre-written radio messages so the app keeps running.
