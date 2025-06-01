#!/usr/bin/env python3
"""
Speech-to-Text Keyboard with Command Support
Includes voice commands like "press enter", "new line", etc.
Commands are disabled by default for security.
Cross-platform: Works on Linux and Windows
"""

import re
import sys
import time
import threading
import queue
import numpy as np
import pyaudio
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key
import webrtcvad
from collections import deque
import logging
import logging.handlers
import argparse
import os
import json
from datetime import datetime
import platform

# Detect platform
PLATFORM = platform.system()

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging with dual handlers
def setup_logging(log_level=logging.INFO, console_output=True):
    """Set up logging with file and optional console output."""
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # File handler for runtime log (always detailed)
    runtime_log = os.path.join(LOGS_DIR, 'runtime.log')
    file_handler = logging.handlers.RotatingFileHandler(
        runtime_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
    
    # Log startup
    logging.info(f"Logging initialized - Level: {logging.getLevelName(log_level)}")
    logging.info(f"Runtime log: {runtime_log}")
    logging.info(f"Platform: {PLATFORM}")
    
    return root_logger

# Get logger for this module
logger = logging.getLogger(__name__)

# Suppress ALSA warnings on Linux
if PLATFORM == "Linux":
    try:
        from ctypes import CDLL, c_char_p, c_int
        
        # Try to load ALSA library
        try:
            asound = CDLL("libasound.so.2")
            asound.snd_lib_error_set_handler.argtypes = [c_char_p]
            asound.snd_lib_error_set_handler.restype = c_int
            asound.snd_lib_error_set_handler(None)
        except OSError:
            pass
    except Exception:
        pass

class CommandHandler:
    """Handle voice commands with security restrictions."""
    
    # Define allowed commands (whitelist approach for security)
    SAFE_COMMANDS = {
        # Text navigation
        "new line": lambda kb: kb.press(Key.shift, Key.enter),  # Soft line break
        "enter": lambda kb: kb.press(Key.enter),  # Regular enter/new paragraph
        "press enter": lambda kb: kb.press(Key.enter),
        "press tab": lambda kb: kb.press(Key.tab),
        "press space": lambda kb: kb.press(Key.space),
        "backspace": lambda kb: kb.press(Key.backspace),
        "delete": lambda kb: kb.press(Key.delete),
        
        # Basic navigation (no system keys)
        "go left": lambda kb: kb.press(Key.left),
        "go right": lambda kb: kb.press(Key.right),
        "go up": lambda kb: kb.press(Key.up),
        "go down": lambda kb: kb.press(Key.down),
        "page up": lambda kb: kb.press(Key.page_up),
        "page down": lambda kb: kb.press(Key.page_down),
        "home": lambda kb: kb.press(Key.home),
        "end": lambda kb: kb.press(Key.end),
        
        # Text selection (safe)
        "select all": lambda kb: kb.press(Key.ctrl, 'a'),
        "copy": lambda kb: kb.press(Key.ctrl, 'c'),
        "paste": lambda kb: kb.press(Key.ctrl, 'v'),
        "cut": lambda kb: kb.press(Key.ctrl, 'x'),
        "undo": lambda kb: kb.press(Key.ctrl, 'z'),
        "redo": lambda kb: kb.press(Key.ctrl, 'y'),
    }
    
    # Commands that are explicitly blocked for security
    BLOCKED_PATTERNS = [
        r"alt\s*f4",  # Close window
        r"ctrl\s*alt\s*del",  # System interrupt
        r"super|windows\s*key",  # System menu
        r"shutdown|reboot|poweroff",  # System commands
        r"terminal|console|cmd",  # Terminal access
        r"sudo|admin|root",  # Privilege escalation
    ]
    
    def __init__(self, enabled=False):
        self.enabled = enabled
        self.keyboard = Controller()
        
    def is_command_safe(self, text):
        """Check if a command is safe to execute."""
        text_lower = text.lower()
        
        # Check against blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, text_lower):
                logger.warning(f"Blocked unsafe command: {text}")
                return False
        
        return True
    
    def process_text(self, text):
        """Process text and extract/execute commands if enabled."""
        if not self.enabled:
            return text  # Return unmodified text if commands disabled
        
        if not self.is_command_safe(text):
            return ""  # Block unsafe commands
        
        # Clean the text for command matching: lowercase and remove common punctuation
        text_lower = text.lower().strip()
        # Remove trailing punctuation for command matching
        text_cleaned = text_lower.rstrip('.!?,;:')
        
        # Check if it's a command
        if text_cleaned in self.SAFE_COMMANDS:
            logger.info(f"Executing command: {text_cleaned}")
            try:
                self.SAFE_COMMANDS[text_cleaned](self.keyboard)
                return ""  # Don't type the command text
            except Exception as e:
                logger.error(f"Failed to execute command: {e}", exc_info=True)
                return text
        
        # Check for command at the end of text
        for cmd, func in self.SAFE_COMMANDS.items():
            if text_cleaned.endswith(cmd):
                # Type the text before the command
                prefix = text[:-(len(cmd) + (len(text_lower) - len(text_cleaned)))].rstrip()
                if prefix:
                    return prefix
                # Execute the command
                try:
                    logger.info(f"Executing trailing command: {cmd}")
                    func(self.keyboard)
                    return ""
                except Exception as e:
                    logger.error(f"Failed to execute command: {e}", exc_info=True)
        
        return text  # Return text if no command found

class SecureSpeechKeyboard:
    def __init__(self, model_size="base", language="en", enable_commands=False, config_file="speech_config.json"):
        """Initialize with security-focused defaults."""
        # Load configuration
        self.config = self.load_config(config_file)
        
        logger.info("="*50)
        logger.info("Starting Speech-to-Text Keyboard")
        logger.info(f"Model: {model_size}, Language: {language}")
        logger.info(f"Commands: {'ENABLED' if enable_commands else 'DISABLED'}")
        logger.info(f"Process ID: {os.getpid()}")
        logger.info("="*50)
        
        print(f"Loading Whisper {model_size} model...")
        start_time = time.time()
        self.model = whisper.load_model(model_size)
        load_time = time.time() - start_time
        logger.info(f"Model loaded in {load_time:.2f} seconds")
        
        self.language = language
        
        # Command handler
        self.command_handler = CommandHandler(enabled=enable_commands)
        if enable_commands:
            print("⚠️  Voice commands are ENABLED - be careful what you say!")
            logger.warning("Voice commands enabled - security restrictions apply")
        
        # Audio settings from config
        self.RATE = self.config['audio']['rate']
        self.CHUNK = self.config['audio']['chunk_size']
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = self.config['audio']['channels']
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(self.config['speech_detection']['vad_aggressiveness'])
        logger.debug(f"VAD initialized with aggressiveness level {self.config['speech_detection']['vad_aggressiveness']}")
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Log audio devices
        logger.debug("Available audio devices:")
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                logger.debug(f"  Device {i}: {info['name']} ({info['maxInputChannels']} channels)")
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        self.audio_queue = queue.Queue()
        
        # Audio buffer settings from config
        self.silence_threshold = self.config['speech_detection']['silence_threshold_chunks']
        self.min_speech_chunks = self.config['speech_detection']['min_speech_chunks']
        
        # Pre-buffer to capture audio before speech detection
        self.pre_buffer_size = self.config['speech_detection']['pre_buffer_chunks']
        self.pre_buffer = deque(maxlen=self.pre_buffer_size)
        
        # Energy-based filtering
        self.energy_threshold = 0.01
        self.calibrating = True
        self.noise_levels = deque(maxlen=50)
        
        # Load filtering settings
        self.false_positives = set(self.config['filtering']['false_positives'])
        self.min_text_length = self.config['filtering']['min_text_length']
        
        # Duplicate detection
        self.last_text = ""
        self.last_text_time = 0
        self.duplicate_threshold = 2.0  # seconds
        
        # Track last typed text for proper spacing
        self.last_typed_text = ""
        
        # Performance tracking
        self.recognition_count = 0
        self.total_recognition_time = 0
        
        print("Model loaded successfully!")
        print(f"Pre-buffer: {self.pre_buffer_size} chunks (~{self.pre_buffer_size * 30}ms)")
        print("Calibrating noise level... Please remain quiet for 2 seconds.")
    
    def load_config(self, config_file):
        """Load configuration from file, use defaults if not found."""
        default_config = {
            "audio": {
                "rate": 16000,
                "chunk_size": 480,
                "channels": 1
            },
            "speech_detection": {
                "vad_aggressiveness": 3,
                "pre_buffer_chunks": 15,
                "silence_threshold_chunks": 30,
                "min_speech_chunks": 10,
                "energy_threshold_multiplier": 1.5,
                "noise_floor_multiplier": 3,
                "speech_detection_threshold": 1,
                "calibration_duration_seconds": 2
            },
            "whisper": {
                "model_size": "base",
                "language": "en",
                "temperature": 0.1,
                "no_speech_threshold": 0.6,
                "logprob_threshold": -1.0
            },
            "filtering": {
                "min_text_length": 2,
                "false_positives": [
                    "", ".", "!", "?", "Thank you.", "Thanks.", "thank you",
                    "Thanks for watching!", "you", "the", "uh", "um"
                ]
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config file: {e}. Using defaults.")
                logger.error(f"Config file load error: {e}", exc_info=True)
                return default_config
        else:
            logger.info(f"Config file not found. Using defaults.")
            return default_config
    
    def toggle_listening(self):
        """Toggle the listening state."""
        self.listening = not self.listening
        status = "ENABLED" if self.listening else "DISABLED"
        print(f"\n[Speech-to-Text {status}]")
        logger.info(f"Listening {status}")
        
        if self.listening:
            self.start_audio_stream()
        else:
            self.stop_audio_stream()
    
    def start_audio_stream(self):
        """Start the audio input stream."""
        if self.stream is None:
            try:
                self.stream = self.audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RATE,
                    input=True,
                    frames_per_buffer=self.CHUNK,
                    stream_callback=self.audio_callback
                )
                self.stream.start_stream()
                logger.debug("Audio stream started")
            except Exception as e:
                logger.error(f"Failed to start audio stream: {e}", exc_info=True)
                print(f"Error: Could not start audio stream - {e}")
    
    def stop_audio_stream(self):
        """Stop the audio input stream."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
                logger.debug("Audio stream stopped")
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}", exc_info=True)
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if self.listening or self.calibrating:
            self.audio_queue.put(in_data)
            logger.debug(f"Audio chunk queued - {len(in_data)} bytes")
        return (in_data, pyaudio.paContinue)
    
    def calculate_energy(self, audio_chunk):
        """Calculate the energy level of an audio chunk."""
        audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
        return np.sqrt(np.mean(audio_np ** 2))
    
    def is_speech(self, audio_chunk):
        """Check if audio chunk contains speech with energy filtering."""
        try:
            # First check energy level
            energy = self.calculate_energy(audio_chunk)
            
            # During calibration, collect noise levels
            if self.calibrating:
                self.noise_levels.append(energy)
                return False
            
            # Check if energy is above threshold (with some margin above noise floor)
            energy_multiplier = self.config['speech_detection']['energy_threshold_multiplier']
            if energy < self.energy_threshold * energy_multiplier:
                return False
            
            # Then check with VAD
            is_speech = self.vad.is_speech(audio_chunk, self.RATE)
            logger.debug(f"VAD result: {'speech' if is_speech else 'silence'}")
            return is_speech
        except Exception as e:
            logger.error(f"VAD error: {e}", exc_info=True)
            return False
    
    def process_audio(self):
        """Process audio from the queue."""
        speech_frames = []
        silence_count = 0
        speech_count = 0
        is_speaking = False
        calibration_chunks = 0
        calibration_duration = self.config['speech_detection']['calibration_duration_seconds']
        calibration_chunks_needed = int(calibration_duration * self.RATE / self.CHUNK)
        speech_threshold = self.config['speech_detection']['speech_detection_threshold']
        
        while self.running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Calibration phase
                if self.calibrating:
                    calibration_chunks += 1
                    self.calculate_energy(audio_chunk)  # Collect noise samples
                    
                    if calibration_chunks >= calibration_chunks_needed:
                        if self.noise_levels:
                            # Set energy threshold based on noise floor
                            noise_floor = np.mean(list(self.noise_levels))
                            noise_multiplier = self.config['speech_detection']['noise_floor_multiplier']
                            self.energy_threshold = max(0.01, noise_floor * noise_multiplier)
                            print(f"Calibration complete. Noise floor: {noise_floor:.4f}")
                        self.calibrating = False
                    continue
                
                # Always add to pre-buffer when not speaking
                if not is_speaking:
                    self.pre_buffer.append(audio_chunk)
                
                if self.is_speech(audio_chunk):
                    speech_count += 1
                    if not is_speaking and speech_count >= speech_threshold:
                        print("\r[Listening...]", end='', flush=True)
                        logger.info("Speech detected, starting capture")
                        is_speaking = True
                        # Add pre-buffer to speech frames to capture the beginning
                        speech_frames.extend(list(self.pre_buffer))
                        # Clear the pre-buffer
                        self.pre_buffer.clear()
                    
                    if is_speaking:
                        speech_frames.append(audio_chunk)
                    silence_count = 0
                else:
                    if is_speaking:
                        silence_count += 1
                        speech_frames.append(audio_chunk)
                        
                        if silence_count >= self.silence_threshold:
                            # Only process if we had enough speech chunks
                            if len(speech_frames) >= self.min_speech_chunks:
                                print(" [Processing...]", end='', flush=True)
                                logger.info(f"Speech ended, processing {len(speech_frames)} frames")
                                self.recognize_and_type(speech_frames)
                            else:
                                print(" [Too short, ignoring]")
                                logger.debug(f"Ignored short audio: {len(speech_frames)} frames")
                            
                            speech_frames = []
                            silence_count = 0
                            speech_count = 0
                            is_speaking = False
                            print()  # New line after processing complete
                    else:
                        # Reset speech count if we get non-speech while not speaking
                        speech_count = 0
                            
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in audio processing: {e}", exc_info=True)
                print(f"\nError in audio processing: {e}")
    
    def recognize_and_type(self, audio_frames):
        """Recognize speech and type it using keyboard simulation."""
        try:
            start_time = time.time()
            
            audio_data = b''.join(audio_frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Additional check: ensure audio has sufficient energy
            if np.max(np.abs(audio_np)) < 0.01:
                print("\r[Audio too quiet]", end='', flush=True)
                return
            
            logger.debug(f"Processing {len(audio_np)/self.RATE:.2f} seconds of audio")
            
            result = self.model.transcribe(
                audio_np,
                language=self.language,
                fp16=False,
                temperature=self.config['whisper']['temperature'],
                no_speech_threshold=self.config['whisper']['no_speech_threshold'],
                logprob_threshold=self.config['whisper']['logprob_threshold']
            )
            
            recognition_time = time.time() - start_time
            self.recognition_count += 1
            self.total_recognition_time += recognition_time
            
            text = result['text'].strip()
            
            # Filter out false positives using configuration
            if text and text not in self.false_positives and len(text) > self.min_text_length:
                # Check for duplicates
                current_time = time.time()
                if text == self.last_text and (current_time - self.last_text_time) < self.duplicate_threshold:
                    print("\r[Duplicate ignored]", end='', flush=True)
                    logger.debug(f"Ignored duplicate: '{text}'")
                    return
                
                self.last_text = text
                self.last_text_time = current_time
                
                logger.info(f"Recognized: '{text}' (took {recognition_time:.2f}s)")
                
                # Process through command handler
                processed_text = self.command_handler.process_text(text)
                
                if processed_text:
                    # Check if we need to add a space before this text
                    text_to_type = processed_text
                    if self.last_typed_text:
                        # If the last typed text ended with punctuation or a letter/number,
                        # add a space before the new text
                        last_char = self.last_typed_text.rstrip()[-1] if self.last_typed_text.rstrip() else ''
                        if last_char and (last_char in '.!?,:;' or last_char.isalnum()):
                            text_to_type = ' ' + processed_text
                    
                    # Clear the line and show what will be typed
                    print(f"\r[Typing: {processed_text}]", end='', flush=True)
                    # Type the text
                    self.keyboard_controller.type(text_to_type)
                    # Small delay to ensure typing completes
                    time.sleep(0.05)
                    # Update last typed text
                    self.last_typed_text = processed_text
                    logger.info(f"Typed: '{text_to_type}'")
                else:
                    print(f"\r[Command: {text}]", end='', flush=True)
            else:
                print("\r[Filtered out]", end='', flush=True)
                logger.debug(f"Filtered out: '{text}'")
                
        except Exception as e:
            logger.error(f"Error in recognition: {e}", exc_info=True)
            print(f"\nError in recognition: {e}")
    
    def setup_hotkeys(self):
        """Set up keyboard hotkeys."""
        def on_press(key):
            try:
                if key == keyboard.Key.f9:
                    self.toggle_listening()
            except Exception as e:
                logger.error(f"Hotkey error: {e}", exc_info=True)
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        logger.debug("Hotkey listener started")
        return listener
    
    def run(self):
        """Main run loop."""
        print("\n=== Secure Speech-to-Text Keyboard ===")
        print("Press F9 to toggle listening on/off")
        print("Press Ctrl+C to exit")
        
        if self.command_handler.enabled:
            print("\nVoice Commands Available:")
            print("- 'new line' (Shift+Enter) or 'enter'/'press enter' (Enter)")
            print("- 'press tab', 'press space'")
            print("- 'copy', 'paste', 'cut'")
            print("- 'select all', 'undo', 'redo'")
            print("- Navigation: 'go left/right/up/down'")
        
        print("=====================================\n")
        
        hotkey_listener = self.setup_hotkeys()
        
        # Start audio stream for calibration
        self.start_audio_stream()
        
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()
        logger.info("Audio processing thread started")
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            logger.info("Received shutdown signal")
        finally:
            self.running = False
            self.stop_audio_stream()
            if self.stream:
                self.stream.close()
            self.audio.terminate()
            hotkey_listener.stop()
            
            # Log performance stats
            if self.recognition_count > 0:
                avg_time = self.total_recognition_time / self.recognition_count
                logger.info(f"Performance stats: {self.recognition_count} recognitions, "
                          f"avg time: {avg_time:.2f}s")
            
            logger.info("Shutdown complete")
            print("Goodbye!")

def main():
    parser = argparse.ArgumentParser(
        description="Secure Speech-to-Text Keyboard with optional voice commands"
    )
    parser.add_argument(
        "--model",
        choices=["tiny", "base", "small", "medium"],
        default="base",
        help="Whisper model size"
    )
    parser.add_argument(
        "--language",
        default="en",
        help="Language code (e.g., en, es, fr)"
    )
    parser.add_argument(
        "--enable-commands",
        action="store_true",
        help="Enable voice commands (SECURITY WARNING: allows keyboard control)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging verbosity level"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable console logging output (still logs to file)"
    )
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level=log_level, console_output=not args.quiet)
    
    try:
        app = SecureSpeechKeyboard(
            model_size=args.model,
            language=args.language,
            enable_commands=args.enable_commands
        )
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 