#!/usr/bin/env python3
"""
Enhanced Speech-to-Text Keyboard with Additional Features
- Multi-language support
- Custom wake words
- Voice feedback
- Performance monitoring
- Advanced filtering
Cross-platform: Works on Linux and Windows
"""

import sys
import time
import threading
import queue
import json
import os
import numpy as np
import pyaudio
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key
import webrtcvad
from collections import deque
import argparse
import logging
from datetime import datetime
import platform
import subprocess
import signal

# Detect platform
PLATFORM = platform.system()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_runtime.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Running on {PLATFORM}")

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

class SpeechToKeyboard:
    def __init__(self, config_file="speech_config.json"):
        """
        Initialize the speech-to-text keyboard with configuration file.
        
        Args:
            config_file: Path to JSON configuration file
        """
        # Load configuration
        self.load_config(config_file)
        
        print(f"Loading Whisper {self.config['whisper']['model_size']} model... This may take a moment on first run.")
        self.model = whisper.load_model(self.config['whisper']['model_size'])
        
        # Audio settings from config
        self.RATE = self.config['audio']['rate']
        self.CHUNK = self.config['audio']['chunk_size']
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = self.config['audio']['channels']
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(self.config['detection']['vad_aggressiveness'])
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        self.audio_queue = queue.Queue()
        
        # Detection parameters from config
        self.silence_threshold = self.config['detection']['silence_threshold_chunks']
        self.min_speech_chunks = self.config['detection']['min_speech_chunks']
        self.energy_multiplier = self.config['detection']['energy_threshold_multiplier']
        self.consecutive_speech = self.config['detection']['consecutive_speech_chunks']
        self.calibration_seconds = self.config['detection']['calibration_duration_seconds']
        
        # Audio buffer settings from config
        self.speech_buffer = deque(maxlen=150)
        
        # Pre-buffer to capture audio before speech detection
        self.pre_buffer_size = self.config['detection'].get('pre_buffer_chunks', 15)
        self.pre_buffer = deque(maxlen=self.pre_buffer_size)
        
        # Energy-based filtering
        self.noise_levels = deque(maxlen=50)
        self.energy_threshold = 0.01
        self.calibrating = True
        
        print(f"Model loaded successfully!")
        print(f"Pre-buffer: {self.pre_buffer_size} chunks (~{self.pre_buffer_size * 30}ms)")
        print(f"Calibrating noise level... Please remain quiet for {self.calibration_seconds} seconds.")
        
    def load_config(self, config_file):
        """Load configuration from JSON file."""
        default_config = {
            "audio": {
                "rate": 16000,
                "chunk_size": 480,
                "channels": 1
            },
            "detection": {
                "vad_aggressiveness": 3,
                "consecutive_speech_chunks": 3,
                "silence_threshold_chunks": 30,
                "min_speech_chunks": 10,
                "pre_buffer_chunks": 15,
                "energy_threshold_multiplier": 1.5,
                "noise_floor_multiplier": 3,
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
                "min_text_length": 3,
                "false_positives": []
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults
                self.config = self._merge_configs(default_config, loaded_config)
                print(f"Loaded configuration from {config_file}")
            except Exception as e:
                print(f"Error loading config file: {e}. Using defaults.")
                self.config = default_config
        else:
            print(f"Config file not found. Using defaults.")
            self.config = default_config
            # Save default config for reference
            try:
                with open(config_file, 'w') as f:
                    json.dump(default_config, f, indent=4)
                print(f"Created default config file: {config_file}")
            except:
                pass
    
    def _merge_configs(self, default, loaded):
        """Recursively merge loaded config with defaults."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
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
            except Exception as e:
                print(f"Error starting audio stream: {e}")
                print("Please check your microphone is connected and permissions are granted.")
    
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
            
            # Check if energy is above threshold
            if energy < self.energy_threshold * self.energy_multiplier:
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
        calibration_total = int(self.calibration_seconds * self.RATE / self.CHUNK)
        
        while self.running:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Calibration phase
                if self.calibrating:
                    calibration_chunks += 1
                    self.calculate_energy(audio_chunk)
                    
                    if calibration_chunks >= calibration_total:
                        if self.noise_levels:
                            # Set energy threshold based on noise floor
                            noise_floor = np.mean(list(self.noise_levels))
                            self.energy_threshold = max(0.005, noise_floor * 3)
                            print(f"Calibration complete. Noise floor: {noise_floor:.4f}, Threshold: {self.energy_threshold:.4f}")
                        self.calibrating = False
                    continue
                
                # Always add to pre-buffer when not speaking
                if not is_speaking:
                    self.pre_buffer.append(audio_chunk)
                
                if self.is_speech(audio_chunk):
                    speech_count += 1
                    if not is_speaking and speech_count >= self.consecutive_speech:
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
            # Convert audio frames to numpy array
            audio_data = b''.join(audio_frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Additional check: ensure audio has sufficient energy
            if np.max(np.abs(audio_np)) < 0.01:
                print(" [Audio too quiet]")
                return
            
            # Transcribe with Whisper
            whisper_config = self.config['whisper']
            result = self.model.transcribe(
                audio_np,
                language=whisper_config['language'],
                fp16=False,
                temperature=whisper_config['temperature'],
                no_speech_threshold=whisper_config['no_speech_threshold'],
                logprob_threshold=whisper_config['logprob_threshold']
            )
            
            text = result['text'].strip()
            
            # Apply filtering
            filter_config = self.config['filtering']
            
            # Check against false positives
            if text.lower() in [fp.lower() for fp in filter_config['false_positives']]:
                print(" [Filtered: false positive]")
                return
            
            # Check minimum length
            if len(text) < filter_config['min_text_length']:
                print(" [Filtered: too short]")
                return
            
            # If all checks pass, type the text
            print(f" [{text}]")
            self.keyboard_controller.type(text + " ")
                
        except Exception as e:
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
        print("\n=== Enhanced Speech-to-Text Keyboard ===")
        print("Press F9 to toggle listening on/off")
        print("Press Ctrl+C to exit")
        print("========================================\n")
        
        # Show current settings
        print("Current settings:")
        print(f"  VAD Aggressiveness: {self.config['detection']['vad_aggressiveness']}/3")
        print(f"  Silence threshold: {self.silence_threshold} chunks (~{self.silence_threshold * 30}ms)")
        print(f"  Min speech duration: {self.min_speech_chunks} chunks (~{self.min_speech_chunks * 30}ms)")
        print(f"  Model: {self.config['whisper']['model_size']}")
        print(f"  Language: {self.config['whisper']['language']}")
        print()
        
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
            if self.audio:
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
        if PLATFORM == "Windows":
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
    parser = argparse.ArgumentParser(description="Enhanced Speech-to-Text Keyboard")
    parser.add_argument("--config", default="speech_config.json", 
                        help="Path to configuration file (default: speech_config.json)")
    args = parser.parse_args()
    
    # Kill any existing instances before starting
    kill_existing_instances()
    
    speech_keyboard = SpeechToKeyboard(config_file=args.config)
    speech_keyboard.run()

if __name__ == "__main__":
    main() 