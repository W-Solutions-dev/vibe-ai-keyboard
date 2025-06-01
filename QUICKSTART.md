# QUICKSTART - Speech-to-Text Keyboard

## Quick Setup (Ubuntu/Debian)
```bash
# 1. Run setup (installs dependencies)
./setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the program
python speech_to_keyboard.py
```

## Usage
- **F9**: Toggle listening on/off
- **Ctrl+C**: Exit program

## Troubleshooting False Detections

If the program is detecting breathing, keyboard sounds, or typing random text like "thank you":

### Option 1: Use the Enhanced Version (Recommended)
The enhanced version has better noise filtering and is configurable:
```bash
python speech_to_keyboard_enhanced.py
```

### Option 2: Adjust Sensitivity Settings
Edit `speech_config.json` to tune detection:
```json
{
    "detection": {
        "vad_aggressiveness": 3,           // 1-3, higher = less sensitive
        "silence_threshold_chunks": 30,     // Increase for longer pauses
        "min_speech_chunks": 10,           // Increase to ignore short sounds
        "energy_threshold_multiplier": 2.0, // Increase to ignore quiet sounds
        "consecutive_speech_chunks": 5      // Increase for more strict detection
    }
}
```

### Option 3: Quick Fixes
- **Too sensitive?** Increase values in `speech_config.json`
- **Picking up breathing?** Increase `energy_threshold_multiplier` to 2.5 or 3.0
- **False text like "thank you"?** Add to `false_positives` list in config

## First Run
- Downloads Whisper model (~140MB) on first use
- Calibrates to your environment noise level (2 seconds)
- ALSA warnings on Linux are normal and can be ignored

## Features
- ✅ 100% local processing (no cloud)
- ✅ Works in any application
- ✅ Auto-calibrates to background noise
- ✅ Filters out breathing and keyboard sounds
- ✅ Configurable sensitivity

## Models
- **tiny**: Fastest, less accurate
- **base**: Default, balanced (recommended)
- **small/medium**: Better accuracy, slower
- **large**: Best accuracy, requires GPU

## Multilingual Support

### Auto Language Detection
The default configuration now supports automatic language detection! You can speak in any language Whisper supports:
```bash
# Already configured for auto-detection
python speech_to_keyboard.py
```

### Supported Languages
Whisper supports 100+ languages including:
- English, Dutch, German, French, Spanish, Italian
- Chinese, Japanese, Korean, Arabic, Hindi
- And many more!

### Using Specific Language
To force a specific language, edit `speech_config.json`:
```json
{
    "whisper": {
        "language": "nl"  // For Dutch only
        // or
        "language": "en"  // For English only
        // or  
        "language": null  // For auto-detection (default)
    }
}
```

### Mixed Language Example
With auto-detection enabled, you can seamlessly switch:
- "Hello, how are you?" → Types in English
- "Hoe gaat het met je?" → Types in Dutch
- "Comment allez-vous?" → Types in French

### Multilingual Config
Use the example multilingual config:
```bash
python speech_to_keyboard.py --config speech_config_multilang.json
```

### Tips for Multilingual Use
- **Larger models** (small/medium) work better for non-English languages
- **Clear pronunciation** helps with language detection
- **Add language-specific filler words** to false_positives (e.g., "eh", "euh" for Dutch)

## Need Commands?
For voice commands (use with caution):
```bash
python speech_to_keyboard_commands.py --enable-commands
```

## Quick Test
```bash
# Test your setup
python test_setup.py

# Interactive test
./test_helper.sh
```

## Common Issues
- **No audio detected**: Check microphone permissions
- **High CPU usage**: Use 'tiny' model or reduce sensitivity
- **Too many false positives**: Increase thresholds in config
- **Missing audio**: Run `setup.sh` again

### Known Issues & Solutions

**First words cut off?**
- This has been fixed! The system now uses a pre-buffer to capture ~450ms before speech detection
- Adjust `pre_buffer_chunks` in `speech_config.json` if needed
- Test with: `python test_prebuffer.py`

**False detections?**
- Increase `energy_threshold_multiplier` in config
- Add common false positives to the `false_positives` list
- Use the enhanced version for better filtering 