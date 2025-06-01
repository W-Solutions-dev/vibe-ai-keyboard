# 🎙️ Vibe AI Keyboard - Local Speech-to-Text System

[![GitHub Repository](https://img.shields.io/badge/GitHub-vibe--ai--keyboard-blue)](https://github.com/W-Solutions-dev/vibe-ai-keyboard)

A local, privacy-focused speech-to-text system that acts like a USB keyboard. When enabled, it listens to your speech and types the recognized text directly into any application, just as if you were typing on a physical keyboard.

> **🌟 Note**: This project is 100% vibe coded with a human in the loop. Every feature is crafted through the collaborative dance between human creativity and AI assistance, ensuring both innovation and practical usability. This project came alive through approximately 500 Claude Opus max requests, with continuous refinement and improvement planned for the future.

## Features

- **100% Local**: Uses OpenAI's Whisper model running entirely on your machine - no cloud services required
- **System-wide Input**: Works in any application that accepts keyboard input
- **Toggle On/Off**: Press F9 to enable/disable listening
- **Voice Activity Detection**: Automatically detects when you start and stop speaking
- **Low Latency**: Processes speech in real-time as you pause
- **Privacy First**: All processing happens locally, your voice never leaves your computer
- **Optional Voice Commands**: Safe keyboard control commands (disabled by default)

## Requirements

- Python 3.8+
- Linux (tested on Ubuntu/Debian)
- Microphone
- ~1-2GB disk space for the Whisper model

## Installation

### Quick Setup

```bash
# Run the enhanced setup script
./setup.sh

# Options:
./setup.sh --dry-run  # See what would be done without changes
./setup.sh --debug    # Enable debug logging
./setup.sh --force    # Force reinstall
```

The setup script is idempotent (safe to run multiple times) and includes:
- Automatic dependency checking
- Progress tracking and resume capability
- Detailed logging to `setup.log`
- Component testing

### Manual Installation

#### 1. Install System Dependencies

```bash
# Install PortAudio (required for PyAudio)
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# Install pip if not already installed
sudo apt-get install python3-pip

# Optional: Install ffmpeg (improves Whisper performance)
sudo apt-get install ffmpeg
```

#### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 4. First Run

The first time you run the program, it will download the Whisper model (about 140MB for the base model):

```bash
python speech_to_keyboard.py
```

## Usage

### Basic Usage (Text Only)

```bash
python speech_to_keyboard.py
```

- Press **F9** to toggle listening on/off
- Speak naturally - text appears where your cursor is
- Press **Ctrl+C** to exit

### With Voice Commands (Use Cautiously)

```bash
python speech_to_keyboard_commands.py --enable-commands
```

Available voice commands:
- **"new line"** or **"press enter"** - Insert a new line
- **"press tab"**, **"press space"** - Navigation
- **"copy"**, **"paste"**, **"cut"** - Clipboard operations
- **"select all"**, **"undo"**, **"redo"** - Text editing
- **"go left/right/up/down"** - Cursor movement
- **"backspace"**, **"delete"** - Text deletion

### Lightweight Version

For faster performance with lower accuracy:

```bash
python speech_to_keyboard_lite.py --continuous
```

## Security Considerations

### Default Security Model

By default, the application:
- **Only types text** - no system commands or mouse control
- **Requires manual activation** - F9 to enable
- **Shows visual feedback** - you see what's being typed
- **Runs with user privileges** - no elevated access

### Voice Commands Security

When voice commands are enabled (`--enable-commands`):

**Allowed Operations** (Whitelist):
- Basic text navigation and editing
- Clipboard operations (copy/paste)
- Cursor movement

**Blocked Operations**:
- System commands (shutdown, reboot)
- Window management (Alt+F4)
- Terminal/console access
- Privilege escalation (sudo)
- Any unrecognized commands

The command handler uses a **whitelist approach** - only explicitly allowed commands work.

### Best Practices

1. **Run without commands** for maximum security
2. **Be aware of your surroundings** when using voice input
3. **Disable when not needed** (F9 toggles off)
4. **Review logs** if suspicious activity occurs
5. **Use in trusted environments** only

## Configuration

### Model Size

You can change the Whisper model size in `speech_to_keyboard.py`:

```python
# In main() function, change model_size parameter:
speech_keyboard = SpeechToKeyboard(model_size="base", language="en")
```

Available models:
- `tiny`: 39M parameters, ~1GB RAM, fastest but least accurate
- `base`: 74M parameters, ~1GB RAM, good balance (default)
- `small`: 244M parameters, ~2GB RAM, better accuracy
- `medium`: 769M parameters, ~5GB RAM, even better accuracy
- `large`: 1550M parameters, ~10GB RAM, best accuracy but slowest

### Language

Change the language parameter to recognize other languages:

```python
speech_keyboard = SpeechToKeyboard(model_size="base", language="es")  # Spanish
```

Common language codes: `en` (English), `es` (Spanish), `fr` (French), `de` (German), `it` (Italian), `pt` (Portuguese), `zh` (Chinese), `ja` (Japanese)

## How It Works

1. **Audio Capture**: Continuously captures audio from your microphone when enabled
2. **Voice Detection**: Uses WebRTC VAD to detect when you're speaking
3. **Speech Buffering**: Collects your speech until you pause
4. **Recognition**: Processes the audio through Whisper to convert to text
5. **Command Processing**: Optionally interprets voice commands (if enabled)
6. **Keyboard Simulation**: Types the recognized text using pynput

## Troubleshooting

### First Words Being Cut Off

If you're experiencing the first words of your speech being cut off, this has been fixed with a pre-buffer system. The system now:

1. **Pre-buffers audio**: Continuously stores the last ~450ms of audio before speech is detected
2. **Instant detection**: Starts recording immediately when speech is detected
3. **Includes pre-buffer**: Adds the pre-buffered audio to ensure no words are lost

You can adjust the pre-buffer size in `speech_config.json`:
```json
"pre_buffer_chunks": 15  // Increase for more pre-buffer (each chunk = 30ms)
```

Test the pre-buffer behavior:
```bash
python test_prebuffer.py
```

### "ALSA lib" errors
These warnings are normal on Linux and can be ignored. The program will still work correctly.

### No audio input
1. Check your microphone is connected and working:
   ```bash
   arecord -l  # List recording devices
   ```
2. Make sure your user has permission to access audio devices

### Poor recognition accuracy
- Try a larger model (e.g., "small" or "medium")
- Speak more clearly and ensure low background noise
- Check your microphone quality

### High CPU usage
- Use a smaller model (e.g., "tiny")
- The first inference is always slower; subsequent recognitions are faster

### Testing Components
```bash
python test_setup.py  # Run component tests
```

## License

This project uses:
- OpenAI Whisper (MIT License)
- Various Python libraries under their respective licenses

## Automated Development

This project features AI-driven development capabilities including:
- **Automatic Issue Resolution**: The AI assistant can read GitHub issues, implement fixes, and push commits autonomously
- **Smart Git Management**: All version control operations are handled by AI following semantic versioning
- **Continuous Improvement**: Issues are automatically addressed while maintaining code quality and consistency

This capability was verified through issue #1, demonstrating the seamless integration between human requests and AI implementation.

## TODO / Roadmap

### 🎯 AI-Driven Visual UI Control
Implement an intelligent UI automation system that can:
- **Voice-activated screenshot analysis**: "Click yes on that system prompt"
- **Visual element detection**: Use computer vision/OCR to locate UI elements
- **Coordinate calculation**: Determine exact click positions from screenshots
- **Action execution**: Perform mouse movements and clicks
- **Verification system**: Confirm actions were completed successfully
- **Context awareness**: Understand different types of UI elements (buttons, links, dialogs)

**Technical approach:**
- Integrate with screenshot libraries (PIL/Pillow, pyautogui)
- Use OCR (Tesseract) or AI vision models for text/element detection
- Implement safety confirmations for destructive actions
- Create a permission system for different action types

### 🔊 AI Voice Feedback System
Add bidirectional communication capabilities:
- **Text-to-Speech responses**: AI speaks back to the user
- **Clarification requests**: "I didn't understand, could you repeat?"
- **Action confirmations**: "Clicking the Yes button now"
- **Error explanations**: "I cannot find that button on screen"
- **Command suggestions**: "Did you mean to say...?"

**Implementation ideas:**
- Integrate local TTS (pyttsx3, gTTS offline mode)
- Create conversation context management
- Add configurable voice personalities
- Implement interrupt handling for ongoing speech

### 📊 Enhanced Logging System
Comprehensive logging infrastructure:
- **Dual log system**: Separate setup.log and runtime.log
- **Verbosity levels**: DEBUG, INFO, WARNING, ERROR with easy toggling
- **Structured logging**: JSON format option for parsing
- **Log rotation**: Automatic file rotation to prevent huge files
- **Performance metrics**: Track recognition speed, accuracy
- **Action audit trail**: Log all commands and UI actions

### 🔐 Security Enhancements
- **Screenshot privacy**: Blur/redact sensitive information
- **Action allowlist**: Define permitted applications/windows
- **Confirmation mode**: Require verbal confirmation for clicks
- **Session recording**: Optional recording of all actions for review

### 🚀 Performance Optimizations
- **GPU acceleration**: Utilize CUDA for faster Whisper inference
- **Model caching**: Keep frequently used models in memory
- **Streaming recognition**: Process audio in real-time chunks
- **Parallel processing**: Handle recognition and actions concurrently

### 🔧 Developer Experience
- **Plugin system**: Allow custom command extensions
- **Configuration UI**: GUI for settings management
- **Testing framework**: Automated tests for voice commands
- **Documentation generator**: Auto-generate command documentation

### 📦 Distribution & Packaging Strategy
Make the project easily installable and usable by end users:

**PyPI Package Distribution:**
- Create `setup.py` with proper metadata and dependencies
- Build wheel distributions for faster installation
- Publish to PyPI as `speech-to-keyboard` package
- Enable simple installation: `pip install speech-to-keyboard`
- Handle model downloads automatically on first run

**Docker Containerization:**
- Multi-stage Dockerfile for optimized image size
- Pre-download Whisper models in container
- Handle audio device passthrough properly
- Support for both CPU and GPU variants
- Docker Compose for easy local deployment

**Desktop Integration:**
- Native installers for major platforms (AppImage, snap, deb)
- Automatic desktop entry creation
- System tray integration for easy access
- Auto-start option on system boot

**Binary Distribution:**
- Use PyInstaller/Nuitka for standalone executables
- Bundle all dependencies including Python runtime
- Create platform-specific installers
- Code signing for trusted distribution

**Implementation approach:**
```bash
# Future installation methods:
pip install speech-to-keyboard          # From PyPI
docker run speech-to-keyboard           # Docker image
snap install speech-to-keyboard         # Snap package
./speech-to-keyboard.AppImage           # Portable Linux app
apt install speech-to-keyboard          # Debian/Ubuntu package
``` 