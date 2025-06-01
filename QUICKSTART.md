# 🚀 Quick Start Guide - Speech-to-Text Keyboard

Get up and running in minutes! This guide covers the essentials for both Linux and Windows.

## 📋 Prerequisites

- Python 3.8 or higher
- Microphone
- ~1-2GB free disk space
- **Linux**: Ubuntu/Debian-based system (or equivalent)
- **Windows**: Windows 10/11 with PowerShell

## ⚡ Installation

### Linux Installation (2 minutes)

```bash
# 1. Clone or download the project
git clone https://github.com/yourusername/speech-to-text-keyboard.git
cd speech-to-text-keyboard

# 2. Run setup script
./setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Test the installation
python test_setup.py
```

### Windows Installation (3 minutes)

```powershell
# 1. Clone or download the project
git clone https://github.com/yourusername/speech-to-text-keyboard.git
cd speech-to-text-keyboard

# 2. Run setup script (PowerShell)
.\setup_windows.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 4. Test the installation
python test_setup.py
```

## 🎯 Basic Usage

### Start the program:

**Linux:**
```bash
python speech_to_keyboard.py
```

**Windows:**
```powershell
python speech_to_keyboard.py
```

### Controls:
- **F9** - Toggle listening on/off
- **Ctrl+C** - Exit the program

## 🎤 Usage Tips

1. **First run** downloads the Whisper model (~140MB)
2. **Speak naturally** - pause briefly between sentences
3. **Clear speech** works best - avoid mumbling
4. **Background noise** reduces accuracy

## 🛠️ Quick Troubleshooting

### Linux Issues

**No audio input detected:**
```bash
# Check audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav && aplay test.wav
```

**ALSA warnings:**
- These are normal and can be ignored

### Windows Issues

**Python not found:**
- Make sure Python is in your PATH
- Reinstall Python and check "Add to PATH"

**Permission denied:**
- Run PowerShell as Administrator
- Check antivirus settings

**Build tools error:**
- Install Visual C++ Build Tools from Microsoft

## 🚨 Common Commands

### With Voice Commands (Optional)

**Enable commands:**
```bash
# Linux
python speech_to_keyboard_commands.py --enable-commands

# Windows
python speech_to_keyboard_commands.py --enable-commands
```

When using `speech_to_keyboard_commands.py` with `--enable-commands`:

| Say | Action |
|-----|--------|
| "new line" | Shift+Enter (soft line break) |
| "enter" or "press enter" | Enter (new paragraph) |
| "press tab" | Tab key |
| "press space" | Space key |
| "copy" | Ctrl+C |
| "paste" | Ctrl+V |
| "cut" | Ctrl+X |
| "select all" | Ctrl+A |
| "undo" | Ctrl+Z |
| "redo" | Ctrl+Y |
| "go left/right/up/down" | Arrow keys |
| "page up/down" | Page navigation |
| "home/end" | Line navigation |
| "backspace/delete" | Text deletion |

## 📊 Performance Options

### Use smaller model for speed:
```bash
# Edit speech_config.json
{
  "whisper": {
    "model_size": "tiny"  // Change from "base" to "tiny"
  }
}
```

### Model comparison:
- **tiny**: Fastest, less accurate (39M params)
- **base**: Balanced (default) (74M params) 
- **small**: Better accuracy, slower (244M params)

## 🔒 Security Note

- **Default**: Only types text, no system commands
- **With --enable-commands**: Limited safe commands only
- **Never allows**: System shutdown, Alt+F4, sudo, etc.

## 💡 Pro Tips

1. **Reduce false positives**: Adjust `min_text_length` in config
2. **Better accuracy**: Use "small" model if you have good hardware
3. **Multiple languages**: Change `language` in config (e.g., "es", "fr", "de")
4. **Logs**: Check `logs/runtime.log` for debugging

## 🆘 Need Help?

1. Run component test: `python test_setup.py`
2. Check logs: `logs/setup.log` or `logs/runtime.log`
3. Try with debug: `python speech_to_keyboard.py --debug`
4. Platform-specific help:
   - **Linux**: Check microphone permissions
   - **Windows**: Check Windows Defender settings

---
**Ready to go?** Start with `python speech_to_keyboard.py` and press F9 to begin! 🎉 