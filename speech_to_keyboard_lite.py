#!/usr/bin/env python3
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

class SimpleSpeechKeyboard:
    def __init__(self, model_size="tiny", continuous=False, config_file="speech_config.json"):
        """Initialize with minimal configuration."""
        # Load configuration
        self.config = self.load_config(config_file)
        
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        self.continuous = continuous
        
        # Audio settings from config
        self.RATE = self.config['audio']['rate']
        self.CHUNK = self.config['audio']['chunk_size']
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = self.config['audio']['channels']
        
        # Pre-buffer for capturing beginning of speech
        self.pre_buffer_size = self.config['speech_detection']['pre_buffer_chunks']
        self.pre_buffer = deque(maxlen=self.pre_buffer_size)
        
        # False positive filtering
        self.false_positives = set(self.config['filtering']['false_positives'])
        self.min_text_length = self.config['filtering']['min_text_length']
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        print(f"Ready! Press F9 to start/stop listening.")
        print(f"Pre-buffer: {self.pre_buffer_size} chunks (~{self.pre_buffer_size * 30}ms)")
        
    def load_config(self, config_file):
        """Load configuration from file, use defaults if not found."""
        default_config = {
            "audio": {
                "rate": 16000,
                "chunk_size": 1024,
                "channels": 1
            },
            "speech_detection": {
                "pre_buffer_chunks": 10,  # Smaller for lite version
            },
            "whisper": {
                "temperature": 0.0,
                "no_speech_threshold": 0.6
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
                    loaded_config = json.load(f)
                    # Merge with defaults (in case some keys are missing)
                    for key in default_config:
                        if key not in loaded_config:
                            loaded_config[key] = default_config[key]
                    return loaded_config
            except Exception as e:
                print(f"Error loading config file: {e}. Using defaults.")
                return default_config
        else:
            return default_config
    
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
    
    def record_and_transcribe(self):
        """Record audio and transcribe in chunks."""
        if not self.listening or not self.stream:
            return
            
        # Record for a fixed duration
        duration = 3 if not self.continuous else 2  # seconds
        frames = []
        
        for _ in range(0, int(self.RATE / self.CHUNK * duration)):
            if not self.listening:
                break
            try:
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)
            except:
                break
        
        if frames:
            # Convert to numpy array
            audio_data = b''.join(frames)
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe
            try:
                result = self.model.transcribe(
                    audio_np,
                    language="en",
                    fp16=False,
                    temperature=self.config['whisper']['temperature'],
                    no_speech_threshold=self.config['whisper']['no_speech_threshold']
                )
                
                text = result['text'].strip()
                
                # Filter out false positives
                if text and text not in self.false_positives and len(text) > self.min_text_length:
                    # Don't add extra spaces, let user control spacing
                    print(f"📝 {text}")
                    self.keyboard_controller.type(text)
                elif text:
                    print(f"[Filtered: {text}]")
                    
            except Exception as e:
                print(f"Error: {e}")
    
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
                    self.record_and_transcribe()
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

def main():
    parser = argparse.ArgumentParser(description="Speech-to-Text Keyboard")
    parser.add_argument(
        "--model", 
        choices=["tiny", "base", "small"],
        default="tiny",
        help="Whisper model size (default: tiny)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Continuous mode (shorter recording chunks)"
    )
    
    args = parser.parse_args()
    
    app = SimpleSpeechKeyboard(
        model_size=args.model,
        continuous=args.continuous
    )
    app.run()

if __name__ == "__main__":
    main() 