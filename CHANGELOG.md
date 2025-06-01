# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.2] - 2025-06-01

### Fixed
- Fixed TypeError in voice commands when using keyboard shortcuts
  - All keyboard combinations (Ctrl+C, Shift+Enter, etc.) were failing due to incorrect pynput usage
  - Changed from `kb.press(Key.ctrl, 'c')` to proper press/release sequence
  - Affects all voice commands: new line, copy, paste, cut, undo, redo, select all
  - Commands now execute properly instead of throwing errors
- Fixed navigation keys getting stuck (holding down indefinitely)
  - All single key presses now properly include release() calls
  - Navigation commands no longer repeat infinitely

### Changed
- Navigation commands now use terminal-style word jumping
  - "go left/right" now uses Ctrl+arrow for word navigation instead of single character movement
  - Added tab navigation: "tab left/right", "next/previous tab" for browser/editor tab switching
  - Added line navigation: "start of line", "end of line" commands
  - Improved documentation to clearly describe navigation behavior

## [0.4.1] - 2025-06-01

### Fixed
- Add proper spacing between sentences when typing
  - Text now correctly adds a space before new sentences
  - Prevents sentences from being concatenated without spaces
  - Tracks last typed text to determine spacing needs
  - Applied fix to all speech keyboard versions
- Voice command recognition with punctuation and capitalization
  - Commands now work when Whisper adds punctuation (e.g., "New line.")
  - Case-insensitive command matching
  - Strips common punctuation (.!?,;:) before matching commands

### Changed
- "new line" command now uses Shift+Enter for soft line break
- Added "enter" as a direct command for regular Enter key
- Improved voice command documentation clarity

## [0.4.0] - 1 Jun 2025

### Added
- Comprehensive PRIVACY_IMPLEMENTATION.md document detailing HOW privacy is implemented
- Specific code examples with line numbers showing privacy enforcement
- Privacy verification methods and testing procedures
- Privacy audit script example for automated verification
- Reference to privacy implementation in README.md
- Cursor rules for maintaining privacy documentation
- Current date lookup requirement in cursor rules to prevent date errors

### Fixed
- GitHub issue templates now use proper naming convention (hyphenated lowercase)
- PROJECT_HISTORY.md date accuracy - AI now required to look up actual dates

### Changed
- Enhanced documentation to show technical privacy implementation details
- Cursor rules now enforce privacy documentation updates with code changes

## [0.3.1] - 1 Jun 2025

### Added
- Biometric sensor integration roadmap (heart rate, gesture recognition, eye tracking)
- Video and visual input features roadmap (lip reading, sign language, document scanning)
- Strong privacy pledge: vibe developers will NEVER request to snoop on user data
- Privacy-by-design guarantees for all future sensor features

### Changed
- Enhanced roadmap documentation with privacy-first approach for all features
- Emphasized 100% local processing for biometric and video features

## [0.3.0] - 1 Jun 2025

### Added
- Automated issue resolution capability - AI can read GitHub issues, implement fixes, and push commits
- Automated Development section in README documenting AI-driven development features
- Demonstration of end-to-end automation workflow (successfully resolved issue #1)
- GitHub API integration for issue discovery and tracking

### Changed
- Enhanced git workflow to support fully autonomous development cycle
- PROJECT_HISTORY.md updated with automated issue resolution milestone

### Fixed
- All dates in PROJECT_HISTORY.md corrected to proper timeline

## [0.2.1] - 1 Jun 2025

### Added
- PROJECT_HISTORY.md documenting the complete development journey
- Development history tracking requirements in .cursorrules
- Acknowledgment of ~500 Claude Opus requests in README

### Fixed
- Removed automatic trailing space after recognized text

### Changed
- Updated vibe coding note to reflect the collaborative effort

## [0.2.0] - 1 Jun 2025

### Added
- Pre-buffer system to capture audio before speech detection (fixes first words being cut off)
- Configurable pre-buffer size in speech_config.json (default: 15 chunks = ~450ms)
- test_prebuffer.py utility to visualize and test pre-buffer behavior
- Configuration file support (speech_config.json) for all tunable parameters
- Instant speech detection (reduced from 3 chunks to 1 chunk threshold)
- Dynamic configuration loading with sensible defaults

### Changed
- Speech detection now starts immediately on first detected speech chunk
- Main script now uses configuration file for all parameters
- Added argparse support for custom config file paths
- Updated documentation with pre-buffer troubleshooting guide

### Fixed
- First words of speech being cut off during recognition
- Configuration parameters are now centralized and easily adjustable

## [0.1.0] - 1 Jun 2025

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

---

## Version History Legend

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

## Future Releases

### [0.5.0] - TBD
- PyPI package distribution
- Docker container support
- Desktop integration (system tray)

### [1.0.0] - TBD
- First stable release
- Complete documentation
- All core features implemented 