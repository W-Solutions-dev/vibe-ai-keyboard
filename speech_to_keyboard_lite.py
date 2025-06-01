#!/usr/bin/env python3
"""
Lightweight Speech-to-Text Keyboard
A simpler version using the tiny model for faster performance.
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

class SimpleSpeechKeyboard:
    def __init__(self, model_size="tiny", continuous=False):
        """Initialize with minimal configuration."""
        print(f"Loading Whisper {model_size} model...")
        self.model = whisper.load_model(model_size)
        self.continuous = continuous
        
        # Audio settings
        self.RATE = 16000
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        
        # Audio setup
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        print("Ready! Press F9 to start/stop listening.")
        
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
                    temperature=0.0,
                    no_speech_threshold=0.6
                )
                
                text = result['text'].strip()
                if text and text not in [".", " ", ""]:
                    # Add space before text if not starting with punctuation
                    if not text[0] in ".,!?;:":
                        text = " " + text
                    
                    print(f"📝 {text}")
                    self.keyboard_controller.type(text)
                    
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