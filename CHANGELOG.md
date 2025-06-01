# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core speech-to-text functionality with Whisper model
- Voice activity detection for automatic speech capture
- Keyboard simulation to type recognized text
- F9 hotkey to toggle listening on/off
- Security-first command system with whitelist approach
- Comprehensive logging system with runtime.log
- Idempotent setup script with state tracking
- Interactive test helper for diagnostics
- Three application variants:
  - Main version (text only)
  - Commands version (with safe voice commands)
  - Lite version (fast, minimal features)
- Project documentation (README, QUICKSTART, .cursorrules)
- Versioning and release strategy
- Enhanced speech detection with configurable sensitivity settings
- Automatic noise floor calibration on startup
- Energy-based filtering to prevent false detections from breathing and keyboard sounds
- Configuration file support (speech_config.json) for easy tuning
- Enhanced version (speech_to_keyboard_enhanced.py) with advanced filtering
- Minimum speech duration requirement to filter out short sounds
- Consecutive speech chunk validation for more reliable detection
- Expanded false positive filtering with common misrecognized phrases
- Setuptools added to requirements for better compatibility

### Changed
- Increased VAD aggressiveness from 2 to 3 for better noise rejection
- Increased silence threshold from 15 to 30 chunks (~900ms) for more natural speech detection
- Improved Whisper transcription parameters with stricter thresholds
- Updated QUICKSTART.md with troubleshooting guide for false detections

### Fixed
- False detection of breathing sounds and keyboard noise
- Random text output like "thank you" from ambient noise
- Missing pkg_resources dependency for WebRTC VAD

### Security
- Commands disabled by default
- Whitelist approach for allowed commands
- Blocked dangerous operations (Alt+F4, shutdown, etc.)
- Command execution logging for audit trail

## [0.1.0] - 2024-12-01 (Planned)

### Added
- Initial beta release
- Basic speech-to-text keyboard functionality
- Setup and installation scripts
- Documentation and quick start guide

---

## Version History Legend

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

## Future Releases

### [0.2.0] - TBD
- Voice UI control with screenshot analysis
- Text-to-speech feedback system
- GPU acceleration support

### [0.3.0] - TBD
- PyPI package distribution
- Docker container support
- Desktop integration (system tray)

### [1.0.0] - TBD
- First stable release
- Complete documentation
- All core features implemented 