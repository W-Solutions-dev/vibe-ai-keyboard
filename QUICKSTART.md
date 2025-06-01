# Quick Start Guide

## 🚀 Fastest Setup (3 steps)

1. **Run the enhanced setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   
   # Options:
   ./setup.sh --dry-run  # Preview what will be done
   ./setup.sh --debug    # Show detailed logging
   ./setup.sh --force    # Force reinstall
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Run the speech keyboard:**
   ```bash
   python speech_to_keyboard.py
   ```

## 🧪 Testing Your Setup

**Use the test helper for diagnostics:**
```bash
./test_helper.sh        # Interactive menu
./test_helper.sh all    # Run all tests
./test_helper.sh audio  # Test audio devices
./test_helper.sh mic    # Test microphone
```

## 🎤 How to Use

1. **Start speaking:** Press **F9** to enable listening
2. **Stop speaking:** Press **F9** again to disable
3. **Exit program:** Press **Ctrl+C**

When enabled, everything you say will be typed wherever your cursor is!

## 🔒 Security & Voice Commands

**Basic mode (default - recommended):**
```bash
python speech_to_keyboard.py  # Text only, no commands
```

**With voice commands (use cautiously):**
```bash
python speech_to_keyboard_commands.py --enable-commands
```

Available commands when enabled:
- Say **"new line"** or **"press enter"**
- Say **"copy"**, **"paste"**, **"cut"**
- Say **"go left"**, **"go right"**, etc.

⚠️ Commands are disabled by default for security. The system blocks dangerous operations like Alt+F4, system commands, etc.

## 💡 Tips

- **First run downloads the AI model** (~140MB)
- **Speak clearly** and pause between sentences
- **Works in any application** - text editors, browsers, chat apps
- **100% offline** - no internet required after setup
- **Check logs** - Setup creates `setup.log` for troubleshooting

## 🔧 Troubleshooting

**No sound?** Check microphone:
```bash
./test_helper.sh mic    # Test and record audio
arecord -l              # List audio devices
```

**Test all components:**
```bash
./test_helper.sh all    # Comprehensive test suite
python test_setup.py    # Component verification
```

**Use lightweight version** (faster, less accurate):
```bash
python speech_to_keyboard_lite.py
```

**Check setup logs:**
```bash
./test_helper.sh logs   # View log analysis
cat setup.log           # View full log
```

## ⚡ Advanced Options

**Continuous mode** (no pauses needed):
```bash
python speech_to_keyboard_lite.py --continuous
```

**Better accuracy** (slower):
```bash
# Edit speech_to_keyboard.py and change:
model_size="small"  # or "medium"
```

**Different language:**
```bash
# Edit speech_to_keyboard.py and change:
language="es"  # Spanish, "fr" French, etc.
```

**Debug mode:**
```bash
python speech_to_keyboard_commands.py --debug
```

## 🎯 Common Issues

- **"ALSA lib" warnings:** Normal on Linux, ignore them
- **High CPU:** Use `speech_to_keyboard_lite.py` instead
- **Poor accuracy:** Try the "small" model or speak clearer
- **Setup issues:** Run `./setup.sh --force` to reinstall

Press F9 and start talking! 🎉 