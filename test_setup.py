#!/usr/bin/env python3
"""
Component Test Suite for Speech-to-Text Keyboard
Tests audio, model loading, and keyboard simulation
Cross-platform: Works on Linux and Windows
"""

import sys
import platform
import time
import numpy as np
import os
from pathlib import Path

# Detect platform
PLATFORM = platform.system()
print(f"Running tests on {PLATFORM}")

# Platform-specific setup
if PLATFORM == "Linux":
    # Suppress ALSA warnings
    from ctypes import CDLL, c_char_p, c_int
    try:
        asound = CDLL("libasound.so.2")
        asound.snd_lib_error_set_handler.argtypes = [c_char_p]
        asound.snd_lib_error_set_handler(None)
    except:
        pass

def test_imports():
    """Test if all required packages can be imported."""
    print("\n1. Testing imports...")
    required_packages = [
        'pyaudio',
        'whisper',
        'pynput',
        'webrtcvad',
        'numpy',
        'pydub'
    ]
    
    failed = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✓ {package} imported successfully")
        except ImportError as e:
            print(f"   ✗ Failed to import {package}: {e}")
            failed.append(package)
    
    return len(failed) == 0

def test_audio_devices():
    """Test audio device detection."""
    print("\n2. Testing audio devices...")
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        # Get default input device
        try:
            default_input = p.get_default_input_device_info()
            print(f"   ✓ Default input device: {default_input['name']}")
        except Exception as e:
            print(f"   ✗ No default input device found: {e}")
            return False
        
        # List all input devices
        input_count = 0
        print("   Available input devices:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_count += 1
                print(f"     - {info['name']} (channels: {info['maxInputChannels']})")
        
        p.terminate()
        
        if input_count > 0:
            print(f"   ✓ Found {input_count} input device(s)")
            return True
        else:
            print("   ✗ No input devices found")
            return False
            
    except Exception as e:
        print(f"   ✗ Audio device test failed: {e}")
        return False

def test_microphone_access():
    """Test if microphone can be accessed."""
    print("\n3. Testing microphone access...")
    try:
        import pyaudio
        
        p = pyaudio.PyAudio()
        
        # Try to open a stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        
        # Try to read some data
        data = stream.read(1024, exception_on_overflow=False)
        stream.close()
        p.terminate()
        
        if data:
            print("   ✓ Microphone access successful")
            return True
        else:
            print("   ✗ No data from microphone")
            return False
            
    except Exception as e:
        print(f"   ✗ Microphone access failed: {e}")
        print("   Make sure your microphone is connected and permissions are granted")
        return False

def test_whisper_model():
    """Test if Whisper model can be loaded."""
    print("\n4. Testing Whisper model loading...")
    try:
        import whisper
        
        print("   Loading tiny model for testing...")
        model = whisper.load_model("tiny")
        
        # Test with a dummy audio array
        dummy_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        result = model.transcribe(dummy_audio, fp16=False)
        
        print("   ✓ Whisper model loaded and working")
        return True
        
    except Exception as e:
        print(f"   ✗ Whisper model test failed: {e}")
        return False

def test_keyboard_simulation():
    """Test if keyboard simulation works."""
    print("\n5. Testing keyboard simulation...")
    try:
        from pynput.keyboard import Controller
        
        keyboard = Controller()
        
        # Just create the controller, don't actually type
        print("   ✓ Keyboard controller initialized")
        
        # Platform-specific checks
        if PLATFORM == "Linux":
            # Check if running under X11 or Wayland
            if os.environ.get('DISPLAY'):
                print("   ✓ Running under X11")
            elif os.environ.get('WAYLAND_DISPLAY'):
                print("   ⚠ Running under Wayland - keyboard simulation may have limitations")
        elif PLATFORM == "Windows":
            print("   ✓ Windows keyboard simulation ready")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Keyboard simulation test failed: {e}")
        if PLATFORM == "Linux":
            print("   Make sure you're running in a graphical environment")
        return False

def test_vad():
    """Test Voice Activity Detection."""
    print("\n6. Testing Voice Activity Detection...")
    try:
        import webrtcvad
        
        vad = webrtcvad.Vad(3)
        
        # Create a test frame (30ms of 16kHz audio)
        frame = b'\x00' * 960
        
        # Test if VAD can process the frame
        is_speech = vad.is_speech(frame, 16000)
        
        print(f"   ✓ VAD initialized (test frame is speech: {is_speech})")
        return True
        
    except Exception as e:
        print(f"   ✗ VAD test failed: {e}")
        return False

def test_configuration():
    """Test if configuration files are accessible."""
    print("\n7. Testing configuration...")
    config_files = ['speech_config.json', 'speech_config_multilang.json']
    found_any = False
    
    for config_file in config_files:
        if Path(config_file).exists():
            print(f"   ✓ Found {config_file}")
            found_any = True
        else:
            print(f"   ⚠ {config_file} not found (will use defaults)")
    
    return True  # Config files are optional

def main():
    """Run all tests."""
    print("=" * 60)
    print("Speech-to-Text Keyboard Component Tests")
    print(f"Platform: {PLATFORM} {platform.version()}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Audio Devices", test_audio_devices),
        ("Microphone Access", test_microphone_access),
        ("Whisper Model", test_whisper_model),
        ("Keyboard Simulation", test_keyboard_simulation),
        ("Voice Activity Detection", test_vad),
        ("Configuration", test_configuration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! The system is ready to use.")
        
        # Platform-specific instructions
        if PLATFORM == "Windows":
            print("\nTo run: python speech_to_keyboard.py")
        else:
            print("\nTo run: python speech_to_keyboard.py")
            
        return 0
    else:
        print("\n✗ Some tests failed. Please check the errors above.")
        
        # Platform-specific troubleshooting
        if PLATFORM == "Windows":
            print("\nWindows troubleshooting:")
            print("- Make sure Python is in your PATH")
            print("- Try running as Administrator if microphone access fails")
            print("- Install Visual C++ Build Tools if package installation failed")
        else:
            print("\nLinux troubleshooting:")
            print("- Make sure you have microphone permissions")
            print("- Check if PulseAudio/ALSA is working: 'arecord -l'")
            print("- For Wayland, some features may be limited")
            
        return 1

if __name__ == "__main__":
    sys.exit(main()) 