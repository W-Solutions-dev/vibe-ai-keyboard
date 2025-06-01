# 🎙️ Vibe AI Keyboard - Local Speech-to-Text System

[![GitHub Repository](https://img.shields.io/badge/GitHub-vibe--ai--keyboard-blue)](https://github.com/W-Solutions-dev/vibe-ai-keyboard)

A local, privacy-focused speech-to-text system that acts like a USB keyboard. When enabled, it listens to your speech and types the recognized text directly into any application, just as if you were typing on a physical keyboard.

> **🌟 Note**: This project is 100% vibe coded with a human in the loop. Every feature is crafted through the collaborative dance between human creativity and AI assistance, ensuring both innovation and practical usability. This project came alive through approximately 1000 Claude Opus requests, with continuous refinement and improvement planned for the future.

## 🎯 The Vibe Developer's Vision

**Original Intent**: Create a faster, smarter way to interact with your OS by thinking outside the box. 

Voice is just the beginning. The vision extends to:
- **🧠 AI-Enhanced Interaction**: Natural language commands that understand context
- **💾 Memory & Context**: Remember your preferences, common phrases, and workflows
- **🗄️ Personal Knowledge Base**: Store and retrieve information through voice
- **🤖 Intelligent Automation**: Chain commands and create voice-triggered macros
- **👁️ Visual Understanding**: Combine voice with screenshot analysis for true UI automation

This isn't just about typing with your voice - it's about reimagining how we interact with computers.

## 🌐 Cross-Platform Support

This project works on both **Linux** and **Windows** systems! 

⚠️ **Note**: Windows support has been implemented but is not yet thoroughly tested. We welcome feedback and issue reports from Windows users to help improve compatibility.

## 🤝 Contributing & Issues

We welcome contributions and feedback! Please use our issue templates:
- 🐛 **Bug Reports**: Help us fix problems
- 🚀 **Feature Requests**: Share your ideas
- 🪟 **Windows Testing**: Report your Windows experience

**Your feedback shapes this project!** Whether it's a bug, a feature idea, or Windows compatibility feedback, we want to hear from you.

## Features

- **100% Local**: Uses OpenAI's Whisper model running entirely on your machine - no cloud services required
- **Cross-Platform**: Works on Linux and Windows
- **System-wide Input**: Works in any application that accepts keyboard input
- **Toggle On/Off**: Press F9 to enable/disable listening
- **Voice Activity Detection**: Automatically detects when you start and stop speaking
- **Low Latency**: Processes speech in real-time as you pause
- **Privacy First**: All processing happens locally, your voice never leaves your computer (see [Privacy Implementation](PRIVACY_IMPLEMENTATION.md) for technical details)
- **Optional Voice Commands**: Safe keyboard control commands (disabled by default)
- **Native Typing**: Acts like a USB keyboard - no special drivers needed
- **Visual Feedback**: Clear UI indicators for active/paused state

## Requirements

- Python 3.8+
- Linux (tested on Ubuntu/Debian) or Windows 10/11
- Microphone
- ~1-2GB disk space for the Whisper model

## Installation

### 🐧 Linux Installation

#### Quick Setup

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

#### Manual Installation

##### 1. Install System Dependencies

```bash
# Install PortAudio (required for PyAudio)
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# Install pip if not already installed
sudo apt-get install python3-pip

# Optional: Install ffmpeg (improves Whisper performance)
sudo apt-get install ffmpeg
```

##### 2. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

##### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 🪟 Windows Installation

#### Quick Setup

Open PowerShell and run:

```powershell
# Run the Windows setup script
.\setup_windows.ps1

# Options:
.\setup_windows.ps1 -DryRun  # See what would be done without changes
.\setup_windows.ps1 -Debug    # Enable debug logging
.\setup_windows.ps1 -Force    # Force reinstall
```

The PowerShell script includes:
- Python version checking
- Virtual environment creation
- Dependency installation
- Component testing

#### Manual Installation

##### 1. Install Prerequisites

1. **Python 3.8+**: Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Visual C++ Build Tools** (optional but recommended):
   - Some packages may require compilation
   - Download from [Microsoft](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

##### 2. Create Virtual Environment

```powershell
# Open PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **Note**: If you get an execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

##### 3. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 🐳 Docker Installation (Coming Soon)

Docker support is planned for easy cross-platform deployment.

## Usage

### Basic Usage (Text Only)

**Linux:**
```bash
python speech_to_keyboard.py
```

**Windows:**
```powershell
python speech_to_keyboard.py
```

- Press **F9** to toggle listening on/off
- Speak naturally - text appears where your cursor is
- Press **Ctrl+C** to exit

### With Voice Commands (Use Cautiously)

**Linux:**
```bash
python speech_to_keyboard_commands.py --enable-commands
```

**Windows:**
```powershell
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
# Linux
python speech_to_keyboard_lite.py --continuous

# Windows
python speech_to_keyboard_lite.py --continuous
```

## Platform-Specific Notes

### 🐧 Linux Notes

- **ALSA warnings**: These are normal and can be ignored
- **Wayland**: Some features may be limited compared to X11
- **Permissions**: Ensure your user has audio device access

### 🪟 Windows Notes

- **Antivirus**: May flag keyboard simulation - this is normal
- **Admin rights**: Not required for normal operation
- **Windows Defender**: Add an exception if needed

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

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

This means you are free to:
- ✅ Use this software for any purpose
- ✅ Change the software to suit your needs
- ✅ Share the software with your friends and neighbors
- ✅ Share the changes you make

Under the following conditions:
- 📋 You must include the license and copyright notice with each and every distribution
- 🔓 You must share any modifications under the same license
- 📖 You must make the source code available when you distribute the software

## Automated Development

This project features AI-driven development capabilities including:
- **Automatic Issue Resolution**: The AI assistant can read GitHub issues, implement fixes, and push commits autonomously
- **Smart Git Management**: All version control operations are handled by AI following semantic versioning
- **Continuous Improvement**: Issues are automatically addressed while maintaining code quality and consistency
- **Human-in-the-Loop Option**: By default, AI presents proposed solutions for human review before implementation

### Issue Resolution Modes
1. **Supervised Mode (Default)**: AI analyzes issues and proposes solutions for human approval
2. **Autonomous Mode**: When explicitly requested, AI implements fixes without waiting for approval

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

### 🫀 Biometric & Sensor Integration (Privacy-First)
Expand interaction capabilities with local biometric processing:
- **Heart Rate Monitoring**: Voice stress analysis and command confirmation
- **Gesture Recognition**: Camera-based hand gestures for commands
- **Eye Tracking**: Gaze-based cursor control with voice activation
- **Emotion Detection**: Adapt system behavior based on user state
- **Multi-Modal Input**: Combine voice + gesture + biometrics

**Privacy guarantees:**
- All processing happens locally on device
- No cloud services or external APIs
- Optional opt-in for each sensor type
- Data never leaves the user's machine
- Open-source processing libraries only

**🔒 Our Privacy Pledge**: We as vibe developers will NEVER request to snoop on any of your data. NEVER. Your biometric data, video feeds, and sensor inputs stay on YOUR machine. Period.

### 📹 Video & Visual Input (100% Local)
Advanced visual capabilities while maintaining privacy:
- **Lip Reading**: Improve accuracy in noisy environments
- **Speaker Identification**: Multi-user support with voice profiles
- **Visual Context**: Understand what's on screen while speaking
- **Document Camera**: Voice-controlled document scanning
- **Sign Language**: Basic sign language recognition

**Technical approach:**
- Use local ML models (MediaPipe, OpenCV)
- Process video streams in real-time
- No frame data stored unless explicitly requested
- Configurable privacy modes (audio-only, video blur, etc.)

**🛡️ Privacy by Design**: Every video feature is built with privacy first. No telemetry, no analytics, no data collection. Your face, your voice, your data - it all stays with you.

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