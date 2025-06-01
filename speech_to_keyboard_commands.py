#!/usr/bin/env python3
"""
Speech-to-Text Keyboard with Command Support
Includes voice commands like "press enter", "new line", etc.
Commands are disabled by default for security.
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
from datetime import datetime

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
    
    return root_logger

# Get logger for this module
logger = logging.getLogger(__name__)

class CommandHandler:
    """Handle voice commands with security restrictions."""
    
    # Define allowed commands (whitelist approach for security)
    SAFE_COMMANDS = {
        # Text navigation
        "new line": lambda kb: kb.press(Key.enter),
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
        
        text_lower = text.lower().strip()
        
        # Check if it's a command
        if text_lower in self.SAFE_COMMANDS:
            logger.info(f"Executing command: {text_lower}")
            try:
                self.SAFE_COMMANDS[text_lower](self.keyboard)
                return ""  # Don't type the command text
            except Exception as e:
                logger.error(f"Failed to execute command: {e}", exc_info=True)
                return text
        
        # Check for command at the end of text
        for cmd, func in self.SAFE_COMMANDS.items():
            if text_lower.endswith(cmd):
                # Type the text before the command
                prefix = text[:-len(cmd)].rstrip()
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
    def __init__(self, model_size="base", language="en", enable_commands=False):
        """Initialize with security-focused defaults."""
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
        
        # Audio settings
        self.RATE = 16000
        self.CHUNK = 480
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(2)
        logger.debug(f"VAD initialized with aggressiveness level 2")
        
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
        
        self.silence_threshold = 15
        
        # Performance tracking
        self.recognition_count = 0
        self.total_recognition_time = 0
        
        print("Model loaded successfully!")
        
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
        if self.listening:
            self.audio_queue.put(in_data)
            logger.debug(f"Audio chunk queued - {len(in_data)} bytes")
        return (in_data, pyaudio.paContinue)
    
    def is_speech(self, audio_chunk):
        """Check if audio chunk contains speech."""
        try:
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
        is_speaking = False
        
        while self.running:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                if self.is_speech(audio_chunk):
                    if not is_speaking:
                        print("\n[Listening...]", end='', flush=True)
                        logger.info("Speech detected, starting capture")
                        is_speaking = True
                    
                    speech_frames.append(audio_chunk)
                    silence_count = 0
                else:
                    if is_speaking:
                        silence_count += 1
                        speech_frames.append(audio_chunk)
                        
                        if silence_count >= self.silence_threshold:
                            print(" [Processing...]", end='', flush=True)
                            logger.info(f"Speech ended, processing {len(speech_frames)} frames")
                            self.recognize_and_type(speech_frames)
                            speech_frames = []
                            silence_count = 0
                            is_speaking = False
                            
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
            
            logger.debug(f"Processing {len(audio_np)/self.RATE:.2f} seconds of audio")
            
            result = self.model.transcribe(
                audio_np,
                language=self.language,
                fp16=False,
                temperature=0.1
            )
            
            recognition_time = time.time() - start_time
            self.recognition_count += 1
            self.total_recognition_time += recognition_time
            
            text = result['text'].strip()
            
            if text:
                logger.info(f"Recognized: '{text}' (took {recognition_time:.2f}s)")
                
                # Process through command handler
                processed_text = self.command_handler.process_text(text)
                
                if processed_text:
                    print(f" [{processed_text}]")
                    self.keyboard_controller.type(processed_text + " ")
                    logger.info(f"Typed: '{processed_text}'")
                else:
                    print(f" [Command executed: {text}]")
            else:
                print(" [No speech detected]")
                logger.debug("No speech detected in audio")
                
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
            print("- 'new line' or 'press enter'")
            print("- 'press tab', 'press space'")
            print("- 'copy', 'paste', 'cut'")
            print("- 'select all', 'undo', 'redo'")
            print("- Navigation: 'go left/right/up/down'")
        
        print("=====================================\n")
        
        hotkey_listener = self.setup_hotkeys()
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