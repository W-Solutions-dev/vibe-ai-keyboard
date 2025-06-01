#!/usr/bin/env python3
"""
Test script for pre-buffer settings
Helps visualize when speech detection starts and what's captured
"""

import pyaudio
import webrtcvad
import numpy as np
from collections import deque
import time
import json
import os

def load_config(config_file="speech_config.json"):
    """Load configuration file"""
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    else:
        print(f"Config file {config_file} not found!")
        return None

def test_prebuffer():
    """Test pre-buffer visualization"""
    config = load_config()
    if not config:
        return
    
    # Audio settings
    RATE = config['audio']['rate']
    CHUNK = config['audio']['chunk_size']
    FORMAT = pyaudio.paInt16
    CHANNELS = config['audio']['channels']
    
    # Detection settings
    vad = webrtcvad.Vad(config['speech_detection']['vad_aggressiveness'])
    pre_buffer_size = config['speech_detection']['pre_buffer_chunks']
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )
    
    print("=== Pre-buffer Test ===")
    print(f"Pre-buffer size: {pre_buffer_size} chunks (~{pre_buffer_size * 30}ms)")
    print("Speak to see when detection starts!")
    print("Press Ctrl+C to exit\n")
    
    pre_buffer = deque(maxlen=pre_buffer_size)
    chunk_count = 0
    speech_count = 0
    is_speaking = False
    
    try:
        while True:
            # Read audio chunk
            audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
            chunk_count += 1
            
            # Calculate energy
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0
            energy = np.sqrt(np.mean(audio_np ** 2))
            
            # Check for speech
            try:
                is_speech = vad.is_speech(audio_chunk, RATE) and energy > 0.01
            except:
                is_speech = False
            
            # Visualize current state
            if is_speech:
                marker = "█" * int(energy * 100)
                print(f"Chunk {chunk_count:4d}: SPEECH {marker}")
                speech_count += 1
            else:
                marker = "░" * int(energy * 100) if energy > 0.005 else ""
                print(f"Chunk {chunk_count:4d}: silence {marker}")
                speech_count = 0
            
            # Show when detection would trigger
            if not is_speaking and speech_count >= config['speech_detection']['speech_detection_threshold']:
                print(f"\n>>> SPEECH DETECTED! Pre-buffer contains {len(pre_buffer)} chunks")
                print(f">>> This captures ~{len(pre_buffer) * 30}ms of audio before detection\n")
                is_speaking = True
            elif is_speaking and speech_count == 0:
                is_speaking = False
                print("\n>>> Speech ended\n")
            
            # Update pre-buffer
            if not is_speaking:
                pre_buffer.append(audio_chunk)
            
            time.sleep(0.001)  # Small delay for readability
            
    except KeyboardInterrupt:
        print("\n\nTest complete!")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    test_prebuffer() 