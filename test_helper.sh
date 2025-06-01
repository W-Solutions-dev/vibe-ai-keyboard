#!/bin/bash

# Test Helper Script for Speech-to-Text Keyboard
# Provides easy testing commands and diagnostics

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
print_header() {
    echo
    echo -e "${BLUE}=== $1 ===${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Test functions
test_audio_devices() {
    print_header "Audio Device Test"
    
    echo "Checking audio system..."
    
    # Check if ALSA is working
    if command -v arecord >/dev/null 2>&1; then
        print_success "ALSA tools found"
        echo
        echo "Input devices:"
        arecord -l 2>/dev/null | grep -E "^card|device" || echo "No input devices found"
        
        echo
        echo "Default input device:"
        arecord -L 2>/dev/null | grep -E "^default|^pulse" | head -5
    else
        print_error "ALSA tools not found. Install with: sudo apt-get install alsa-utils"
    fi
    
    # Check PulseAudio
    echo
    if command -v pactl >/dev/null 2>&1; then
        print_success "PulseAudio found"
        echo "Active sources:"
        pactl list short sources 2>/dev/null | grep -v ".monitor" || echo "No sources found"
    else
        print_warning "PulseAudio not found"
    fi
}

test_microphone() {
    print_header "Microphone Test"
    
    if command -v arecord >/dev/null 2>&1; then
        echo "Recording 3 seconds of audio..."
        echo "Speak into your microphone now!"
        
        # Record
        arecord -d 3 -f cd -t wav test_recording.wav 2>/dev/null
        
        if [ -f test_recording.wav ]; then
            SIZE=$(stat -c%s test_recording.wav)
            if [ $SIZE -gt 1000 ]; then
                print_success "Recording successful (${SIZE} bytes)"
                
                # Play back if aplay is available
                if command -v aplay >/dev/null 2>&1; then
                    echo "Playing back recording..."
                    aplay test_recording.wav 2>/dev/null
                fi
            else
                print_error "Recording too small, microphone may not be working"
            fi
            rm -f test_recording.wav
        else
            print_error "Failed to create recording"
        fi
    else
        print_error "arecord not found, cannot test microphone"
    fi
}

test_python_env() {
    print_header "Python Environment Test"
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python found: $PYTHON_VERSION"
    else
        print_error "Python 3 not found"
        return 1
    fi
    
    # Check virtual environment
    if [ -d "venv" ]; then
        print_success "Virtual environment exists"
        
        # Check if activated
        if [ -n "${VIRTUAL_ENV:-}" ]; then
            print_success "Virtual environment is activated"
        else
            print_warning "Virtual environment not activated"
            echo "Run: source venv/bin/activate"
        fi
    else
        print_error "Virtual environment not found"
        echo "Run: ./setup.sh"
        return 1
    fi
}

test_dependencies() {
    print_header "Dependency Test"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Activate venv if not already
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        source venv/bin/activate
    fi
    
    echo "Testing Python module imports..."
    python test_setup.py
}

test_whisper_model() {
    print_header "Whisper Model Test"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Activate venv if not already
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        source venv/bin/activate
    fi
    
    echo "Testing Whisper model loading and inference..."
    python3 -c "
import whisper
import numpy as np
print('Loading tiny model...')
model = whisper.load_model('tiny')
print('✓ Model loaded')
print('Running test inference...')
audio = np.zeros(16000, dtype=np.float32)
result = model.transcribe(audio, fp16=False)
print('✓ Inference successful')
print(f'Result: {result}')
"
}

run_basic_test() {
    print_header "Basic Functionality Test"
    
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found"
        return 1
    fi
    
    # Activate venv if not already
    if [ -z "${VIRTUAL_ENV:-}" ]; then
        source venv/bin/activate
    fi
    
    echo "Starting speech-to-text keyboard in test mode..."
    echo "This will run for 10 seconds then exit."
    echo
    
    timeout 10 python3 -c "
import sys
sys.path.insert(0, '.')
from speech_to_keyboard_lite import SimpleSpeechKeyboard
import time
import threading

def stop_after_delay(app, delay=10):
    time.sleep(delay)
    app.running = False
    print('\nTest completed!')

app = SimpleSpeechKeyboard(model_size='tiny')
stop_thread = threading.Thread(target=stop_after_delay, args=(app, 10))
stop_thread.start()

print('Test mode: Press F9 to test toggling')
print('Will automatically exit in 10 seconds...')

try:
    app.run()
except KeyboardInterrupt:
    pass
" || true
}

check_logs() {
    print_header "Log Analysis"
    
    if [ -f "setup.log" ]; then
        echo "Setup log summary:"
        echo "Total lines: $(wc -l < setup.log)"
        echo "Errors: $(grep -c ERROR setup.log || echo 0)"
        echo "Warnings: $(grep -c WARN setup.log || echo 0)"
        echo
        echo "Last 10 log entries:"
        tail -10 setup.log
    else
        print_warning "No setup log found"
    fi
}

show_menu() {
    echo -e "${BLUE}Speech-to-Text Keyboard Test Helper${NC}"
    echo "===================================="
    echo
    echo "1) Test audio devices"
    echo "2) Test microphone (record & playback)"
    echo "3) Test Python environment"
    echo "4) Test dependencies"
    echo "5) Test Whisper model"
    echo "6) Run basic functionality test"
    echo "7) Check logs"
    echo "8) Run all tests"
    echo "9) Exit"
    echo
}

run_all_tests() {
    print_header "Running All Tests"
    
    test_audio_devices
    test_microphone
    test_python_env
    test_dependencies
    test_whisper_model
    check_logs
    
    echo
    print_header "Test Summary"
    echo "All tests completed. Check output above for any issues."
}

# Main menu loop
if [ $# -eq 0 ]; then
    while true; do
        show_menu
        read -p "Select option (1-9): " choice
        
        case $choice in
            1) test_audio_devices ;;
            2) test_microphone ;;
            3) test_python_env ;;
            4) test_dependencies ;;
            5) test_whisper_model ;;
            6) run_basic_test ;;
            7) check_logs ;;
            8) run_all_tests ;;
            9) echo "Goodbye!"; exit 0 ;;
            *) print_error "Invalid option" ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
        clear
    done
else
    # Run specific test if provided as argument
    case $1 in
        audio) test_audio_devices ;;
        mic) test_microphone ;;
        env) test_python_env ;;
        deps) test_dependencies ;;
        whisper) test_whisper_model ;;
        basic) run_basic_test ;;
        logs) check_logs ;;
        all) run_all_tests ;;
        *) echo "Usage: $0 [audio|mic|env|deps|whisper|basic|logs|all]" ;;
    esac
fi 