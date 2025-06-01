# Windows Setup Script for Speech-to-Text Keyboard
# Run this script in PowerShell as Administrator if needed for some installations
# Usage: .\setup_windows.ps1

param(
    [switch]$DryRun,
    [switch]$Debug,
    [switch]$Force,
    [switch]$Help
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = Join-Path $ScriptDir "setup_windows.log"
$VenvDir = Join-Path $ScriptDir "venv"
$StateFile = Join-Path $ScriptDir ".setup_state_windows"
$LogsDir = Join-Path $ScriptDir "logs"

# Show help
if ($Help) {
    Write-Host "Usage: .\setup_windows.ps1 [options]"
    Write-Host "Options:"
    Write-Host "  -DryRun    Show what would be done without making changes"
    Write-Host "  -Debug     Enable debug logging"
    Write-Host "  -Force     Force reinstall even if already set up"
    Write-Host "  -Help      Show this help message"
    exit 0
}

# Logging function
function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to log file
    Add-Content -Path $LogFile -Value $logEntry
    
    # Write to console with colors
    switch ($Level) {
        "INFO" { Write-Host "[INFO] $Message" -ForegroundColor Green }
        "WARN" { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[ERROR] $Message" -ForegroundColor Red }
        "DEBUG" { 
            if ($Debug) {
                Write-Host "[DEBUG] $Message" -ForegroundColor Blue
            }
        }
    }
}

# State management functions
function Save-State {
    param(
        [string]$Step,
        [string]$Status
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$Step:$Status:$timestamp" | Add-Content -Path $StateFile
}

function Test-State {
    param(
        [string]$Step
    )
    if (Test-Path $StateFile) {
        $content = Get-Content $StateFile
        return $content -match "^$Step`:completed:"
    }
    return $false
}

function Reset-State {
    if (Test-Path $StateFile) {
        Remove-Item $StateFile
        Write-Log "INFO" "Reset installation state"
    }
}

# Check if command exists
function Test-Command {
    param([string]$Command)
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

# Run command with dry-run support
function Invoke-SetupCommand {
    param(
        [string]$Command,
        [scriptblock]$ScriptBlock
    )
    
    Write-Log "DEBUG" "Running: $Command"
    
    if ($DryRun) {
        Write-Log "INFO" "[DRY-RUN] Would execute: $Command"
        return $true
    }
    
    try {
        & $ScriptBlock
        return $true
    }
    catch {
        Write-Log "ERROR" "Command failed: $Command - $_"
        return $false
    }
}

# Start setup
Write-Host "=== Local Speech-to-Text Keyboard Setup for Windows ===" -ForegroundColor Cyan
Write-Host "Log file: $LogFile"
Write-Host ""

# Create logs directory
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
    Write-Log "INFO" "Created logs directory: $LogsDir"
}

Write-Log "INFO" "Starting Windows setup script"
Write-Log "INFO" "Script directory: $ScriptDir"
Write-Log "INFO" "Dry-run mode: $DryRun"
Write-Log "INFO" "Debug mode: $Debug"

# Handle force flag
if ($Force) {
    Write-Log "INFO" "Force flag set, resetting state"
    Reset-State
}

# Step 1: Check Python 3
if (Test-State "python_check") {
    Write-Log "INFO" "Python check already completed, skipping"
} else {
    Write-Log "INFO" "Checking for Python 3..."
    
    if (Test-Command "python") {
        $pythonVersion = python --version 2>&1
        Write-Log "INFO" "Python found: $pythonVersion"
        
        # Check if it's Python 3.8+
        if ($pythonVersion -match "Python 3\.([8-9]|1[0-9])") {
            Write-Host "✓ Python 3.8+ found" -ForegroundColor Green
            Save-State "python_check" "completed"
        } else {
            Write-Log "ERROR" "Python 3.8+ required, found: $pythonVersion"
            Write-Host "✗ Python 3.8+ required" -ForegroundColor Red
            Write-Host "Please install Python from https://www.python.org/downloads/"
            exit 1
        }
    } else {
        Write-Log "ERROR" "Python not found"
        Write-Host "✗ Python not found" -ForegroundColor Red
        Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/"
        Write-Host "Make sure to check 'Add Python to PATH' during installation"
        exit 1
    }
}

# Step 2: Check for Visual C++ Build Tools (required for some packages)
if (Test-State "build_tools_check") {
    Write-Log "INFO" "Build tools check already completed, skipping"
} else {
    Write-Log "INFO" "Checking for Visual C++ Build Tools..."
    
    # Check if Visual Studio or Build Tools are installed
    $vsWhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
    
    if (Test-Path $vsWhere) {
        Write-Host "✓ Visual Studio/Build Tools found" -ForegroundColor Green
        Save-State "build_tools_check" "completed"
    } else {
        Write-Log "WARN" "Visual C++ Build Tools not found"
        Write-Host "⚠ Visual C++ Build Tools not found" -ForegroundColor Yellow
        Write-Host "Some Python packages may fail to install without it."
        Write-Host "You can download it from: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
        Write-Host "Continuing anyway..."
    }
}

# Step 3: Create virtual environment
if (Test-State "virtualenv") {
    Write-Log "INFO" "Virtual environment already exists, skipping"
} else {
    if (Test-Path $VenvDir) {
        Write-Log "WARN" "Virtual environment directory exists but not marked as complete"
        if ($Force) {
            Write-Log "INFO" "Force flag set, removing existing virtual environment"
            Invoke-SetupCommand "Remove virtual environment" {
                Remove-Item -Recurse -Force $VenvDir
            }
        } else {
            Write-Host "Virtual environment exists. Use -Force to recreate" -ForegroundColor Yellow
            exit 1
        }
    }
    
    Write-Log "INFO" "Creating virtual environment..."
    Write-Host "Creating virtual environment..."
    
    $success = Invoke-SetupCommand "Create virtual environment" {
        python -m venv $VenvDir
    }
    
    if ($success) {
        Save-State "virtualenv" "completed"
    }
}

# Step 4: Activate virtual environment and install dependencies
if (-not $DryRun) {
    Write-Log "INFO" "Activating virtual environment"
    
    # Activate virtual environment
    $activateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
    } else {
        Write-Log "ERROR" "Virtual environment activation script not found"
        exit 1
    }
    
    # Upgrade pip
    if (Test-State "pip_upgrade") {
        Write-Log "INFO" "Pip already upgraded, skipping"
    } else {
        Write-Log "INFO" "Upgrading pip..."
        Write-Host "Upgrading pip..."
        
        $success = Invoke-SetupCommand "Upgrade pip" {
            python -m pip install --upgrade pip
        }
        
        if ($success) {
            Save-State "pip_upgrade" "completed"
        }
    }
    
    # Install Python dependencies
    if (Test-State "python_deps") {
        Write-Log "INFO" "Python dependencies already installed, checking..."
        
        # Verify key dependencies
        $missingDeps = @()
        $modules = @("whisper", "pyaudio", "pynput", "webrtcvad", "numpy")
        
        foreach ($module in $modules) {
            try {
                python -c "import $module" 2>$null
            } catch {
                $missingDeps += $module
            }
        }
        
        if ($missingDeps.Count -gt 0) {
            Write-Log "WARN" "Missing dependencies: $($missingDeps -join ', ')"
            Write-Host "Some dependencies are missing, reinstalling..." -ForegroundColor Yellow
            
            Invoke-SetupCommand "Install requirements" {
                pip install -r requirements.txt
            }
        } else {
            Write-Log "INFO" "All dependencies verified"
            Write-Host "✓ All dependencies already installed" -ForegroundColor Green
        }
    } else {
        Write-Log "INFO" "Installing Python dependencies..."
        Write-Host "Installing Python dependencies..."
        Write-Host "This may take several minutes..."
        
        if (Test-Path "requirements.txt") {
            $success = Invoke-SetupCommand "Install requirements" {
                pip install -r requirements.txt
            }
            
            if ($success) {
                Save-State "python_deps" "completed"
            }
        } else {
            Write-Log "ERROR" "requirements.txt not found"
            Write-Host "Error: requirements.txt not found" -ForegroundColor Red
            exit 1
        }
    }
}

# Step 5: Run component tests
if (-not $DryRun -and (Test-Path "test_setup.py")) {
    Write-Log "INFO" "Running component tests..."
    Write-Host ""
    Write-Host "Running component tests..."
    
    try {
        python test_setup.py
        Write-Log "INFO" "Component tests passed"
        Save-State "tests" "completed"
    } catch {
        Write-Log "ERROR" "Component tests failed"
        Write-Host "Component tests failed. Check the log for details." -ForegroundColor Red
    }
}

# Setup complete
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Log "INFO" "Setup completed successfully"

# Show summary
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "--------"

if (Test-Path $StateFile) {
    Write-Host "Completed steps:"
    Get-Content $StateFile | ForEach-Object {
        $parts = $_.Split(':')
        if ($parts.Count -ge 3) {
            Write-Host "  ✓ $($parts[0]) (completed at $($parts[2]))" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "To run the speech-to-text keyboard:" -ForegroundColor Yellow
Write-Host "  1. Activate the virtual environment: .\venv\Scripts\Activate.ps1"
Write-Host "  2. Run the program: python speech_to_keyboard.py"
Write-Host ""
Write-Host "For voice commands (use with caution):"
Write-Host "  python speech_to_keyboard_commands.py --enable-commands"
Write-Host ""
Write-Host "First run will download the Whisper model (~140MB)"
Write-Host ""
Write-Host "Logs saved to: $LogFile"

# If debug mode, show recent log entries
if ($Debug) {
    Write-Host ""
    Write-Host "Recent log entries:" -ForegroundColor Blue
    Get-Content $LogFile -Tail 10
} 