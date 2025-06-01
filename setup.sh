#!/bin/bash

# Enhanced Setup Script with Logging and Idempotency
# Features:
# - Debug logging
# - Idempotent operations (safe to run multiple times)
# - Dry-run mode
# - Detailed progress tracking
# - Error recovery

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/setup.log"
VENV_DIR="${SCRIPT_DIR}/venv"
STATE_FILE="${SCRIPT_DIR}/.setup_state"
LOGS_DIR="${SCRIPT_DIR}/logs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
DRY_RUN=false
DEBUG=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --dry-run   Show what would be done without making changes"
            echo "  --debug     Enable debug logging"
            echo "  --force     Force reinstall even if already set up"
            echo "  --help      Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Logging functions
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log to file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Log to console with colors
    case $level in
        INFO)
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        DEBUG)
            if [ "$DEBUG" = true ]; then
                echo -e "${BLUE}[DEBUG]${NC} $message"
            fi
            ;;
    esac
}

# State management functions
save_state() {
    local step=$1
    local status=$2
    echo "$step:$status:$(date '+%Y-%m-%d %H:%M:%S')" >> "$STATE_FILE"
}

check_state() {
    local step=$1
    if [ -f "$STATE_FILE" ] && grep -q "^$step:completed:" "$STATE_FILE"; then
        return 0
    fi
    return 1
}

reset_state() {
    if [ -f "$STATE_FILE" ]; then
        rm "$STATE_FILE"
        log INFO "Reset installation state"
    fi
}

# Check if running in dry-run mode
run_command() {
    local cmd="$@"
    log DEBUG "Running: $cmd"
    
    if [ "$DRY_RUN" = true ]; then
        log INFO "[DRY-RUN] Would execute: $cmd"
        return 0
    fi
    
    if eval "$cmd"; then
        return 0
    else
        local exit_code=$?
        log ERROR "Command failed with exit code $exit_code: $cmd"
        return $exit_code
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if package is installed
apt_package_installed() {
    dpkg -l "$1" 2>/dev/null | grep -q "^ii"
}

# Function to check Python module
python_module_exists() {
    python3 -c "import $1" 2>/dev/null
}

# Start setup
echo "=== Local Speech-to-Text Keyboard Setup ==="
echo "Log file: $LOG_FILE"
echo

# Create logs directory
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    log INFO "Created logs directory: $LOGS_DIR"
fi

log INFO "Starting setup script"
log INFO "Script directory: $SCRIPT_DIR"
log INFO "Dry-run mode: $DRY_RUN"
log INFO "Debug mode: $DEBUG"

# Handle force flag
if [ "$FORCE" = true ]; then
    log INFO "Force flag set, resetting state"
    reset_state
fi

# Step 1: Check Python 3
if check_state "python_check"; then
    log INFO "Python check already completed, skipping"
else
    log INFO "Checking for Python 3..."
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1)
        log INFO "Python 3 found: $PYTHON_VERSION"
        echo -e "${GREEN}✓ Python 3 found${NC}"
        save_state "python_check" "completed"
    else
        log ERROR "Python 3 not found"
        echo -e "${RED}✗ Python 3 not found. Please install Python 3.8 or higher${NC}"
        exit 1
    fi
fi

# Step 2: Install system dependencies
if check_state "system_deps"; then
    log INFO "System dependencies already installed, skipping"
else
    log INFO "Installing system dependencies..."
    echo "Installing system dependencies..."
    echo "This will require sudo privileges"
    
    # Update package list only if needed
    if [ "$DRY_RUN" = false ]; then
        LAST_UPDATE=$(stat -c %Y /var/lib/apt/lists 2>/dev/null || echo 0)
        CURRENT_TIME=$(date +%s)
        AGE=$((CURRENT_TIME - LAST_UPDATE))
        
        # Update if older than 24 hours
        if [ $AGE -gt 86400 ]; then
            log INFO "Package list is older than 24 hours, updating..."
            run_command "sudo apt-get update"
        else
            log INFO "Package list is recent, skipping update"
        fi
    fi
    
    # Check and install each package
    PACKAGES=("portaudio19-dev" "python3-pyaudio" "python3-pip" "ffmpeg")
    
    for package in "${PACKAGES[@]}"; do
        if apt_package_installed "$package"; then
            log INFO "Package $package already installed"
            echo -e "${GREEN}✓${NC} $package already installed"
        else
            log INFO "Installing $package..."
            echo "Installing $package..."
            run_command "sudo apt-get install -y $package"
        fi
    done
    
    save_state "system_deps" "completed"
fi

# Step 3: Create virtual environment
if check_state "virtualenv"; then
    log INFO "Virtual environment already exists, skipping"
else
    if [ -d "$VENV_DIR" ]; then
        log WARN "Virtual environment directory exists but not marked as complete"
        if [ "$FORCE" = true ]; then
            log INFO "Force flag set, removing existing virtual environment"
            run_command "rm -rf $VENV_DIR"
        else
            echo -e "${YELLOW}Virtual environment exists. Use --force to recreate${NC}"
            exit 1
        fi
    fi
    
    log INFO "Creating virtual environment..."
    echo "Creating virtual environment..."
    run_command "python3 -m venv $VENV_DIR"
    save_state "virtualenv" "completed"
fi

# Step 4: Activate virtual environment and install dependencies
if [ "$DRY_RUN" = false ]; then
    log INFO "Activating virtual environment"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    if check_state "pip_upgrade"; then
        log INFO "Pip already upgraded, skipping"
    else
        log INFO "Upgrading pip..."
        echo "Upgrading pip..."
        run_command "pip install --upgrade pip"
        save_state "pip_upgrade" "completed"
    fi
    
    # Install Python dependencies
    if check_state "python_deps"; then
        log INFO "Python dependencies already installed, checking..."
        
        # Verify key dependencies
        MISSING_DEPS=()
        for module in whisper pyaudio pynput webrtcvad numpy; do
            if ! python -c "import $module" 2>/dev/null; then
                MISSING_DEPS+=("$module")
            fi
        done
        
        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            log WARN "Missing dependencies: ${MISSING_DEPS[*]}"
            echo -e "${YELLOW}Some dependencies are missing, reinstalling...${NC}"
            run_command "pip install -r requirements.txt"
        else
            log INFO "All dependencies verified"
            echo -e "${GREEN}✓ All dependencies already installed${NC}"
        fi
    else
        log INFO "Installing Python dependencies..."
        echo "Installing Python dependencies..."
        echo "This may take a few minutes..."
        
        if [ -f "requirements.txt" ]; then
            run_command "pip install -r requirements.txt"
            save_state "python_deps" "completed"
        else
            log ERROR "requirements.txt not found"
            echo -e "${RED}Error: requirements.txt not found${NC}"
            exit 1
        fi
    fi
fi

# Step 5: Run component tests
if [ "$DRY_RUN" = false ] && [ -f "test_setup.py" ]; then
    log INFO "Running component tests..."
    echo
    echo "Running component tests..."
    
    if python test_setup.py; then
        log INFO "Component tests passed"
        save_state "tests" "completed"
    else
        log ERROR "Component tests failed"
        echo -e "${RED}Component tests failed. Check the log for details.${NC}"
    fi
fi

# Setup complete
echo
echo -e "${GREEN}=== Setup Complete! ===${NC}"
log INFO "Setup completed successfully"

# Show summary
echo
echo "Summary:"
echo "--------"

if [ -f "$STATE_FILE" ]; then
    echo "Completed steps:"
    while IFS=: read -r step status timestamp; do
        echo "  ✓ $step (completed at $timestamp)"
    done < "$STATE_FILE"
fi

echo
echo "To run the speech-to-text keyboard:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the program: python speech_to_keyboard.py"
echo
echo "For voice commands (use with caution):"
echo "  python speech_to_keyboard_commands.py --enable-commands"
echo
echo "First run will download the Whisper model (~140MB)"
echo
echo "Logs saved to: $LOG_FILE"

# If debug mode, show recent log entries
if [ "$DEBUG" = true ]; then
    echo
    echo "Recent log entries:"
    tail -n 10 "$LOG_FILE"
fi 