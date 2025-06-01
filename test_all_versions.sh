#!/bin/bash
# Test script to verify all speech keyboard versions have unified features

echo "=== Testing All Speech Keyboard Versions ==="
echo "This script will verify that all versions share the same core features"
echo

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment activated"
echo

# Function to test a version
test_version() {
    local script=$1
    local name=$2
    
    echo "Testing $name ($script)..."
    
    # Check if script exists
    if [ ! -f "$script" ]; then
        echo "  ❌ Script not found!"
        return 1
    fi
    
    # Check for key features in the code
    echo -n "  Checking configuration support... "
    if grep -q "load_config" "$script"; then
        echo "✓"
    else
        echo "❌"
    fi
    
    echo -n "  Checking pre-buffer system... "
    if grep -q "pre_buffer" "$script"; then
        echo "✓"
    else
        echo "❌"
    fi
    
    echo -n "  Checking false positive filtering... "
    if grep -q "false_positives" "$script"; then
        echo "✓"
    else
        echo "❌"
    fi
    
    # Test if it runs with --help
    echo -n "  Testing --help flag... "
    if python "$script" --help > /dev/null 2>&1; then
        echo "✓"
    else
        echo "❌"
    fi
    
    echo
}

# Test all versions
test_version "speech_to_keyboard.py" "Main Version"
test_version "speech_to_keyboard_commands.py" "Commands Version"
test_version "speech_to_keyboard_enhanced.py" "Enhanced Version"
test_version "speech_to_keyboard_lite.py" "Lite Version"

echo "=== Feature Comparison ==="
echo "Checking which features each version has:"
echo

# Create comparison table
printf "%-25s %-15s %-15s %-15s %-15s\n" "Feature" "Main" "Commands" "Enhanced" "Lite"
printf "%-25s %-15s %-15s %-15s %-15s\n" "-------" "----" "--------" "--------" "----"

# Check each feature
features=(
    "config file:load_config"
    "pre-buffer:pre_buffer"
    "false positives:false_positives"
    "energy filtering:calculate_energy"
    "noise calibration:calibrating"
    "VAD:webrtcvad"
    "duplicate detection:duplicate_threshold"
)

for feature_check in "${features[@]}"; do
    IFS=':' read -r feature pattern <<< "$feature_check"
    printf "%-25s" "$feature"
    
    for script in speech_to_keyboard.py speech_to_keyboard_commands.py speech_to_keyboard_enhanced.py speech_to_keyboard_lite.py; do
        if grep -q "$pattern" "$script" 2>/dev/null; then
            printf " %-14s" "✓"
        else
            printf " %-14s" "-"
        fi
    done
    echo
done

echo
echo "=== Summary ==="
echo "All versions should now share the core features:"
echo "- Configuration file support (speech_config.json)"
echo "- Pre-buffer system for capturing beginning of speech"
echo "- False positive filtering"
echo "- Main and Commands have full features"
echo "- Enhanced has most features"
echo "- Lite has essential features for lightweight operation" 