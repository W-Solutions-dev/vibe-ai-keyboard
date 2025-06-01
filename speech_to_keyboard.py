#!/usr/bin/env python3
"""
Local Speech-to-Text Keyboard
Converts speech to text and types it as if it were keyboard input.
Press F9 to toggle listening on/off.
Press Ctrl+C to exit.
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
import webrtcvad
from collections import deque

class SpeechToKeyboard:
    def __init__(self, model_size="base", language="en"):
        """
        Initialize the speech-to-text keyboard.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code for recognition
        """
        print(f"Loading Whisper {model_size} model... This may take a moment on first run.")
        self.model = whisper.load_model(model_size)
        self.language = language
        
        # Audio settings
        self.RATE = 16000
        self.CHUNK = 480  # 30ms at 16kHz
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        
        # Voice activity detection
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream = None
        
        # Keyboard controller
        self.keyboard_controller = Controller()
        
        # State
        self.listening = False
        self.running = True
        self.audio_queue = queue.Queue()
        
        # Audio buffer for collecting speech segments
        self.speech_buffer = deque(maxlen=100)  # ~3 seconds of audio
        self.silence_threshold = 15  # Number of silent chunks before processing
        
        print(f"Model loaded successfully!")
        
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
        if self.listening:
            self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)
    
    def is_speech(self, audio_chunk):
        """Check if audio chunk contains speech."""
        try:
            return self.vad.is_speech(audio_chunk, self.RATE)
        except:
            return False
    
    def process_audio(self):
        """Process audio from the queue."""
        speech_frames = []
        silence_count = 0
        is_speaking = False
        
        while self.running:
            try:
                # Get audio chunk from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                if self.is_speech(audio_chunk):
                    if not is_speaking:
                        print("\n[Listening...]", end='', flush=True)
                        is_speaking = True
                    
                    speech_frames.append(audio_chunk)
                    silence_count = 0
                else:
                    if is_speaking:
                        silence_count += 1
                        speech_frames.append(audio_chunk)
                        
                        # If enough silence, process the speech
                        if silence_count >= self.silence_threshold:
                            print(" [Processing...]", end='', flush=True)
                            self.recognize_and_type(speech_frames)
                            speech_frames = []
                            silence_count = 0
                            is_speaking = False
                            
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
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_np,
                language=self.language,
                fp16=False,
                temperature=0.1
            )
            
            text = result['text'].strip()
            
            if text:
                print(f" [{text}]")
                # Type the recognized text
                self.keyboard_controller.type(text + " ")
            else:
                print(" [No speech detected]")
                
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
        print("\n=== Local Speech-to-Text Keyboard ===")
        print("Press F9 to toggle listening on/off")
        print("Press Ctrl+C to exit")
        print("=====================================\n")
        
        # Set up hotkey listener
        hotkey_listener = self.setup_hotkeys()
        
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

def main():
    """Main entry point."""
    # You can change the model size here:
    # tiny, base, small, medium, large
    # Larger models are more accurate but slower
    speech_keyboard = SpeechToKeyboard(model_size="base", language="en")
    speech_keyboard.run()

if __name__ == "__main__":
    main() 