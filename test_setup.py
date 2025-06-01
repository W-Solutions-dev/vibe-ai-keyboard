#!/usr/bin/env python3
"""
Test script to verify all components are working correctly
"""

import sys

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    modules = [
        ("numpy", "NumPy"),
        ("pyaudio", "PyAudio"),
        ("whisper", "OpenAI Whisper"),
        ("pynput", "pynput"),
        ("webrtcvad", "WebRTC VAD")
    ]
    
    all_ok = True
    for module, name in modules:
        try:
            __import__(module)
            print(f"✓ {name} imported successfully")
        except ImportError as e:
            print(f"✗ Failed to import {name}: {e}")
            all_ok = False
    
    return all_ok

def test_audio():
    """Test audio input."""
    print("\nTesting audio input...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        # List audio devices
        print("\nAvailable audio input devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                print(f"  [{i}] {info['name']} ({info['maxInputChannels']} channels)")
        
        # Try to open default input
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024
            )
            print("\n✓ Successfully opened audio input stream")
            stream.close()
        except Exception as e:
            print(f"\n✗ Failed to open audio stream: {e}")
            return False
        
        p.terminate()
        return True
        
    except Exception as e:
        print(f"✗ Audio test failed: {e}")
        return False

def test_whisper():
    """Test Whisper model loading."""
    print("\nTesting Whisper model...")
    try:
        import whisper
        print("Loading tiny model (this may take a moment on first run)...")
        model = whisper.load_model("tiny")
        print("✓ Whisper model loaded successfully")
        
        # Test with dummy audio
        import numpy as np
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        result = model.transcribe(dummy_audio)
        print("✓ Whisper inference test passed")
        return True
        
    except Exception as e:
        print(f"✗ Whisper test failed: {e}")
        return False

def test_keyboard():
    """Test keyboard simulation."""
    print("\nTesting keyboard simulation...")
    try:
        from pynput.keyboard import Controller
        keyboard = Controller()
        print("✓ Keyboard controller initialized")
        print("  (Note: Actual typing test skipped to avoid unwanted input)")
        return True
    except Exception as e:
        print(f"✗ Keyboard test failed: {e}")
        return False

def main():
    print("=== Speech-to-Text Keyboard Component Test ===\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Audio Test", test_audio),
        ("Whisper Test", test_whisper),
        ("Keyboard Test", test_keyboard)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        results.append(test_func())
    
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ All tests passed ({passed}/{total})")
        print("\nYour system is ready to run the speech-to-text keyboard!")
        print("Run: python speech_to_keyboard.py")
        return 0
    else:
        print(f"✗ Some tests failed ({passed}/{total} passed)")
        print("\nPlease check the errors above and ensure all dependencies are installed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 