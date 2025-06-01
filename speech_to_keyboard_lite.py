#!/usr/bin/env python3
"""
Speech-to-Text Keyboard Lite - Minimal version for resource-constrained systems
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
Lightweight Speech-to-Text Keyboard
Minimal version with continuous listening and reduced features.
Uses tiny model for speed over accuracy.
Cross-platform: Works on Linux and Windows
"""

import sys
import time
import threading
import queue
import numpy as np
import pyaudio
import whisper
from pynput import keyboard
from pynput.keyboard import Controller, Key
import argparse
import json
import os
from collections import deque
import platform
import webrtcvad
import subprocess
import signal

# Detect platform
PLATFORM = platform.system()
print(f"Running on {PLATFORM}")

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

class LiteSpeechKeyboard:
    def __init__(self, model_size="tiny", language="en"):
        """Initialize the lightweight speech keyboard."""
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        self.language = language
        
        # Audio settings
        self.RATE = 16000
        self.CHUNK = 480  # 30ms at 16kHz
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(3)  # Aggressive filtering
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        self.audio_queue = queue.Queue()
        
        # Simplified settings
        self.silence_threshold = 15  # ~450ms
        self.min_speech_chunks = 10  # ~300ms
        
        # Pre-buffer for better speech capture
        self.pre_buffer = deque(maxlen=10)  # ~300ms pre-buffer
        
        # Simple false positive filter
        self.false_positives = {"", ".", "!", "?", "Thank you.", "Thanks.", "thank you", "you"}
        
        # Track last typed text for proper spacing
        self.last_typed_text = ""
        
        print("Model loaded!")

    def toggle_listening(self):
        """Toggle listening state."""
        self.listening = not self.listening
        
        if self.listening:
            print("\n🎤 LISTENING...")
            self.stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
        else:
            print("\n⏸️  PAUSED")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
    
    def recognize_and_type(self, audio_frames):
        """Recognize speech and type it."""
        try:
            audio_data = b''.join(audio_frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Simple energy check
            if np.max(np.abs(audio_np)) < 0.01:
                print(" [Too quiet]", end='', flush=True)
                return
            
            # Transcribe with minimal options for speed
            result = self.model.transcribe(
                audio_np,
                language=self.language,
                fp16=False,
                temperature=0.0  # Deterministic
            )
            
            text = result['text'].strip()
            
            # Simple filtering
            if text and text not in self.false_positives and len(text) > 2:
                # Check if we need to add a space before this text
                text_to_type = text
                if self.last_typed_text:
                    # If the last typed text ended with punctuation or a letter/number,
                    # add a space before the new text
                    last_char = self.last_typed_text.rstrip()[-1] if self.last_typed_text.rstrip() else ''
                    if last_char and (last_char in '.!?,:;' or last_char.isalnum()):
                        text_to_type = ' ' + text
                
                print(f" [{text}]", end='', flush=True)
                self.keyboard_controller.type(text_to_type)
                # Update last typed text
                self.last_typed_text = text
            else:
                print(" [Filtered]", end='', flush=True)
                
        except Exception as e:
            print(f"\nError: {e}")
    
    def run(self):
        """Main loop."""
        # Set up hotkey
        def on_press(key):
            if key == keyboard.Key.f9:
                self.toggle_listening()
            elif key == keyboard.Key.esc and self.listening:
                self.toggle_listening()
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        print("\n=== Speech-to-Text Keyboard (Lite) ===")
        print("F9: Toggle listening")
        print("ESC: Stop listening")
        print("Ctrl+C: Exit")
        print("=====================================\n")
        
        try:
            while self.running:
                if self.listening:
                    self.recognize_and_type(self.pre_buffer)
                else:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\nShutting down...")
        finally:
            self.running = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.audio.terminate()
            listener.stop()

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
                            print(f"Killed existing instance (PID: {pid})")
                            # Give it a moment to clean up
                            time.sleep(0.5)
                        except ProcessLookupError:
                            # Process already gone
                            pass
                        except Exception as e:
                            print(f"Failed to kill PID {pid}: {e}")
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
                            print(f"Killed existing instance (PID: {proc.info['pid']})")
                            time.sleep(0.5)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except ImportError:
                print("psutil not available, cannot check for existing instances on Windows")
    except Exception as e:
        print(f"Error checking for existing instances: {e}")

def main():
    parser = argparse.ArgumentParser(description="Speech-to-Text Keyboard")
    parser.add_argument(
        "--model", 
        choices=["tiny", "base", "small"],
        default="tiny",
        help="Whisper model size (default: tiny)"
    )
    parser.add_argument(
        "--language",
        choices=["en", "es", "fr", "de", "it", "pt", "zh-CN", "zh-TW", "ja", "ko"],
        default="en",
        help="Language for Whisper model (default: en)"
    )
    
    args = parser.parse_args()
    
    # Kill any existing instances before starting
    kill_existing_instances()
    
    app = LiteSpeechKeyboard(
        model_size=args.model,
        language=args.language
    )
    app.run()

if __name__ == "__main__":
    main() 