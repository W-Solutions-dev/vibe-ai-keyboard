#!/usr/bin/env python3
"""
Speech-to-Text Keyboard - Local speech recognition that types like a keyboard
Copyright (C) 2025  W Solutions

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
Local Speech-to-Text Keyboard
Converts speech to text and types it as if it were keyboard input.
Press F9 to toggle listening on/off.
Press Ctrl+C to exit.

Cross-platform: Works on Linux and Windows
"""

__version__ = "0.5.0"

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
import json
import os
import argparse
import platform
import logging
from pathlib import Path
import logging.handlers
from datetime import datetime
import subprocess
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpeechToKeyboard:
    def __init__(self, config_file="speech_config.json"):
        """
        Initialize the speech-to-text keyboard.
        
        Args:
            config_file: Path to configuration file
        """
        # Detect platform
        self.platform = platform.system()
        logger.info(f"Running on {self.platform}")
        
        # Load configuration
        self.config = self.load_config(config_file)
        
        print(f"Loading Whisper {self.config['whisper']['model_size']} model... This may take a moment on first run.")
        self.model = whisper.load_model(self.config['whisper']['model_size'])
        self.language = self.config['whisper']['language']
        
        # Audio settings from config
        self.RATE = self.config['audio']['rate']
        self.CHUNK = self.config['audio']['chunk_size']
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = self.config['audio']['channels']
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(self.config['speech_detection']['vad_aggressiveness'])
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        self.audio_queue = queue.Queue()
        
        # Audio buffer settings from config
        self.speech_buffer = deque(maxlen=100)
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
        
        print(f"Model loaded successfully!")
        print(f"Pre-buffer: {self.pre_buffer_size} chunks (~{self.pre_buffer_size * 30}ms)")
        print("Calibrating noise level... Please remain quiet for 2 seconds.")
        
        # Suppress ALSA warnings on Linux
        if self.platform == "Linux":
            self._suppress_alsa_warnings()
    
    def _suppress_alsa_warnings(self):
        """Suppress ALSA warnings on Linux."""
        try:
            from ctypes import CDLL, c_char_p, c_int
            
            # Try to load ALSA library
            try:
                asound = CDLL("libasound.so.2")
            except OSError:
                return
            
            # Set error handler to null
            asound.snd_lib_error_set_handler.argtypes = [c_char_p]
            asound.snd_lib_error_set_handler.restype = c_int
            asound.snd_lib_error_set_handler(None)
        except Exception:
            # If suppression fails, continue anyway
            pass
    
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
                return default_config
        else:
            print(f"Config file not found. Using defaults.")
            return default_config
    
    def toggle_listening(self):
        """Toggle the listening state."""
        self.listening = not self.listening
        status = "ENABLED" if self.listening else "DISABLED"
        print(f"\n[Speech-to-Text {status}]")
        
        if self.listening:
            self.start_audio_stream()
        else:
            self.stop_audio_stream()
    
    def start_audio_stream(self):
        """Start the audio input stream."""
        if self.stream is None:
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            self.stream.start_stream()
    
    def stop_audio_stream(self):
        """Stop the audio input stream."""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
    
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if self.listening or self.calibrating:
            self.audio_queue.put(in_data)
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
            return self.vad.is_speech(audio_chunk, self.RATE)
        except:
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
                # Get audio chunk from queue
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
                        print("\n[Listening...]", end='', flush=True)
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
                        
                        # If enough silence, process the speech
                        if silence_count >= self.silence_threshold:
                            # Only process if we had enough speech chunks
                            if len(speech_frames) >= self.min_speech_chunks:
                                print(" [Processing...]", end='', flush=True)
                                self.recognize_and_type(speech_frames)
                            else:
                                print(" [Too short, ignoring]")
                            
                            speech_frames = []
                            silence_count = 0
                            speech_count = 0
                            is_speaking = False
                    else:
                        # Reset speech count if we get non-speech while not speaking
                        speech_count = 0
                            
            except queue.Empty:
                continue
            except Exception as e:
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
                
                # Check if we need to add a space before this text
                text_to_type = text
                if self.last_typed_text:
                    # If the last typed text ended with punctuation or a letter/number,
                    # add a space before the new text
                    last_char = self.last_typed_text.rstrip()[-1] if self.last_typed_text.rstrip() else ''
                    if last_char and (last_char in '.!?,:;' or last_char.isalnum()):
                        text_to_type = ' ' + text
                
                # Clear the line and show what will be typed
                print(f"\r[Typing: {text}]", end='', flush=True)
                # Type the text
                self.keyboard_controller.type(text_to_type)
                # Small delay to ensure typing completes
                time.sleep(0.05)
                # Update last typed text
                self.last_typed_text = text
                logger.info(f"Typed: '{text_to_type}'")
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
            except:
                pass
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        return listener
    
    def run(self):
        """Main run loop."""
        print("\n=== Local Speech-to-Text Keyboard ===")
        print("Press F9 to toggle listening on/off")
        print("Press Ctrl+C to exit")
        print("=====================================\n")
        
        # Set up hotkey listener
        hotkey_listener = self.setup_hotkeys()
        
        # Start audio stream for calibration
        self.start_audio_stream()
        
        # Start audio processing thread
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.running = False
            self.stop_audio_stream()
            if self.stream:
                self.stream.close()
            self.audio.terminate()
            hotkey_listener.stop()
            print("Goodbye!")

def kill_existing_instances():
    """Kill any existing instances of speech keyboard before starting."""
    # Get current process ID
    current_pid = os.getpid()
    
    try:
        # Find all python processes running speech_to_keyboard
        result = subprocess.run(
            ["pgrep", "-f", "python.*speech_to_keyboard"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid_str in pids:
                if pid_str:
                    pid = int(pid_str)
                    # Don't kill ourselves
                    if pid != current_pid:
                        try:
                            os.kill(pid, signal.SIGTERM)
                            logger.info(f"Killed existing instance with PID {pid}")
                            print(f"Killed existing instance (PID: {pid})")
                            # Give it a moment to clean up
                            time.sleep(0.5)
                        except ProcessLookupError:
                            # Process already gone
                            pass
                        except Exception as e:
                            logger.warning(f"Failed to kill PID {pid}: {e}")
    except FileNotFoundError:
        # pgrep not available (Windows), try alternative method
        if platform.system() == "Windows":
            try:
                # Windows alternative using psutil if available
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'speech_to_keyboard' in cmdline and proc.info['pid'] != current_pid:
                            proc.terminate()
                            logger.info(f"Killed existing instance with PID {proc.info['pid']}")
                            print(f"Killed existing instance (PID: {proc.info['pid']})")
                            time.sleep(0.5)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                logger.warning("psutil not available, cannot check for existing instances on Windows")
    except Exception as e:
        logger.warning(f"Error checking for existing instances: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Local Speech-to-Text Keyboard')
    parser.add_argument('--config', default='speech_config.json',
                        help='Path to configuration file (default: speech_config.json)')
    args = parser.parse_args()
    
    # Kill any existing instances before starting
    kill_existing_instances()
    
    speech_keyboard = SpeechToKeyboard(config_file=args.config)
    speech_keyboard.run()

if __name__ == "__main__":
    main() 