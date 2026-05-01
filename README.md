# Rover BLE Controller - Python Native

A completely Python-native voice-controlled Rover with Web Bluetooth integration.

## Features

✅ **Python-Native Speech Recognition** - All voice processing done server-side using `SpeechRecognition`
✅ **Voice-to-Project Mapping** - Automatic keyword detection and project routing
✅ **Project Navigation** - 4 projects with distinct keywords:
   - Project 1: "generator", "system"
   - Project 2: "drone", "fire"
   - Project 3: "rickshaw", "alcohol"
   - Project 4: "water", "management"
✅ **Modern UI** - Neon-themed interface with real-time feedback
✅ **RESTful API** - All functionality exposed via Flask endpoints

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Setup

1. **Clone the repository**
```bash
cd d:\rover\Rover
```

2. **Create virtual environment** (optional but recommended)
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install system requirements** (for speech recognition)
   - **Windows**: Requires Windows Speech Recognition (built-in)
   - **Mac**: No additional setup needed
   - **Linux**: `sudo apt-get install python3-pyaudio`

## Running the App

### Local Development
```bash
python app.py
```

Then visit: `http://localhost:5000`

### Production (Vercel)
```bash
git push  # Vercel will auto-deploy
```

Then visit: `https://rover-six.vercel.app/`

## API Endpoints

### Core Endpoints

**GET `/`** - Serves main HTML interface

**GET `/api/status`** - Get current app status
```json
{
  "ble_connected": false,
  "active_project": null,
  "project_mode_active": false,
  "speech_available": true,
  "ble_available": false
}
```

### Voice Processing

**POST `/api/recognize-speech`** - Process audio file
- Input: multipart/form-data with audio file
- Output: 
```json
{
  "success": true,
  "transcript": "turn on fire system",
  "project_detected": 2
}
```

**POST `/api/process-command`** - Process text command
- Input: JSON with transcript
- Output: Project command result

### BLE Control

**POST `/api/ble/connect`** - Connect to Rover BLE device

**POST `/api/ble/disconnect`** - Disconnect from Rover

**POST `/api/project/<num>`** - Send project command (1-4)

**POST `/api/stop`** - Stop rover

## How It Works

### Voice Flow
1. User clicks "🎤 VOICE INPUT"
2. Browser records audio via Web Audio API
3. Audio file sent to Flask backend via `/api/recognize-speech`
4. Python `SpeechRecognition` processes audio with Google Speech API
5. Transcript analyzed for project keywords
6. Matching project number sent to Arduino via BLE

### Button Flow
1. User clicks project button (1-4)
2. Frontend sends POST to `/api/project/<num>`
3. Backend sends command to Arduino via BLE

## File Structure

```
Rover/
├── app.py              # Main Flask app with all logic
├── requirements.txt    # Python dependencies
├── vercel.json        # Vercel deployment config
├── templates/
│   └── index.html     # Minimal UI with fetch calls
├── api/
│   └── index.py       # Vercel serverless entry point
└── README.md          # This file
```

## Key Components

### app.py Modules

**Voice Recognition**
- `recognize_speech()` - Handles audio upload and processing
- `process_voice_command()` - Extracts project from transcript
- Uses Google Speech API via `speech_recognition` library

**BLE Communication**
- `ble_connect()` - Initiates Rover connection
- `send_project_command()` - Sends command to Arduino
- Uses `bleak` library for cross-platform BLE

**State Management**
- `AppState` class tracks connection and project status
- Shared across all requests

## Troubleshooting

### "Speech recognition not available"
- Install: `pip install SpeechRecognition`
- Or: `pip install -r requirements.txt`

### Microphone not working
- Check browser permissions (allow microphone access)
- Verify microphone is connected and working

### "BLE not available"
- Install: `pip install bleak`
- Ensure Bluetooth is enabled on your system

### Audio processing slow
- Google Speech API may take 2-5 seconds
- Normal behavior for remote processing

## Development Notes

- All voice logic is Python-based, no JavaScript speech processing
- HTML is minimal (just UI + fetch calls)
- Backend handles complex logic
- Easy to extend with additional keywords or projects
- Can add local speech recognition with `pocketsphinx` for offline support

## Future Enhancements

- [ ] Add offline speech recognition (pocketsphinx)
- [ ] Implement actual BLE communication to Arduino
- [ ] Add confidence scoring for voice matches
- [ ] Support multiple languages
- [ ] Add voice feedback (text-to-speech)
- [ ] Create mobile app wrapper

## License

MIT
