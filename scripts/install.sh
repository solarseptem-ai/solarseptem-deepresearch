#!/usr/bin/env bash

set -euo pipefail

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    BLUE='\033[0;34m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' BLUE='' CYAN='' BOLD='' RESET=''
fi

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*" >&2; }
step()    { echo -e "\n${BOLD}${BLUE}==>${RESET}${BOLD} $*${RESET}"; }

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${CYAN}   ░██████              ░██                       ░██████                            ░██                               ${RESET}"
echo -e "${BOLD}${CYAN}  ░██   ░██             ░██                      ░██   ░██                           ░██                               ${RESET}"
echo -e "${BOLD}${CYAN} ░██          ░███████  ░██  ░██████   ░██░████ ░██          ░███████  ░████████  ░████████  ░███████  ░█████████████  ${RESET}"
echo -e "${BOLD}${CYAN}  ░████████  ░██    ░██ ░██       ░██  ░███      ░████████  ░██    ░██ ░██    ░██    ░██    ░██    ░██ ░██   ░██   ░██ ${RESET}SolarSeptem Installer"
echo -e "${BOLD}${CYAN}         ░██ ░██    ░██ ░██  ░███████  ░██              ░██ ░█████████ ░██    ░██    ░██    ░█████████ ░██   ░██   ░██ ${RESET}"
echo -e "${BOLD}${CYAN}  ░██   ░██  ░██    ░██ ░██ ░██   ░██  ░██       ░██   ░██  ░██        ░███   ░██    ░██    ░██        ░██   ░██   ░██ ${RESET}Open AI Agent Platform"
echo -e "${BOLD}${CYAN}   ░██████    ░███████  ░██  ░█████░██ ░██        ░██████    ░███████  ░██░█████      ░████  ░███████  ░██   ░██   ░██  ${RESET}"
echo -e "${BOLD}${CYAN}                                                                       ░██                                             ${RESET}"
echo -e "${BOLD}${CYAN}                                                                       ░██                                             ${RESET}"
echo ""



# ---------------------------------------------------------------------------
# Step 1: Detect OS
# ---------------------------------------------------------------------------
step "Step 1: Detecting operating system"

OS_TYPE="unknown"

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check for WSL
    if grep -qi microsoft /proc/version 2>/dev/null; then
        OS_TYPE="WSL"
    else
        OS_TYPE="Linux"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS_TYPE="Windows (Git Bash)"
fi

info "OS detected: ${BOLD}${OS_TYPE}${RESET}"

info "python"

# ---------------------------------------------------------------------------
# Step 2: Check Python >= 3.10
# ---------------------------------------------------------------------------
step "Step 2: Checking Python version (>= 3.10 required)"

PYTHON_CMD=""


for cmd in python python3; do
    if command -v "$cmd" &>/dev/null; then
        PY_VER=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        PY_MAJOR=$(echo "$PY_VER" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VER" | cut -d. -f2)
        if [ "${PY_MAJOR}" -ge 3 ] && [ "${PY_MINOR}" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done


if [ -z "$PYTHON_CMD" ]; then
    error "Python 3.10+ not found."
    echo ""
    echo "  Please install Python 3.10 or newer:"
    case "$OS_TYPE" in
        macOS)
            echo "    brew install python@3.12"
            echo "  or download from: https://www.python.org/downloads/"
            ;;
        Linux|WSL)
            echo "    sudo apt update && sudo apt install -y python3 python3-pip  # Debian/Ubuntu"
            echo "    sudo dnf install -y python3                                 # Fedora/RHEL"
            echo "  or download from: https://www.python.org/downloads/"
            ;;
        *)
            echo "    Download from: https://www.python.org/downloads/"
            ;;
    esac
    echo ""
    exit 1
fi

PY_VERSION=$("$PYTHON_CMD" --version 2>&1)
success "Found ${PY_VERSION} (${PYTHON_CMD})"

# Determine pip command
PIP_CMD=""
for cmd in pip pip3; do
    if command -v "$cmd" &>/dev/null; then
        PIP_CMD="$cmd"
        break
    fi
done

if [ -z "$PIP_CMD" ]; then
    # Try python -m pip
    if "$PYTHON_CMD" -m pip --version &>/dev/null 2>&1; then
        PIP_CMD="$PYTHON_CMD -m pip"
    else
        error "pip not found. Please install pip:"
        echo "    $PYTHON_CMD -m ensurepip --upgrade"
        exit 1
    fi
fi



# ---------------------------------------------------------------------------
# Step 3: Install SolarSeptem
# ---------------------------------------------------------------------------
step "Step 3: Installing SolarSeptem"




step "Step 4: Done"
# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}${GREEN}SolarSeptem is installed!${RESET}"
echo ""
echo "  Next steps:"
echo "    1. Restart shell, or reload your shell config:"
echo "         bash/zsh: source ~/.bashrc  (or ~/.zshrc)"
echo "         fish:     source ~/.config/fish/config.fish"
echo "    2. Set your API key:        export ANTHROPIC_API_KEY=your_key"
echo "    3. Launch:                  soalrseptem"
echo "    4. Docs:                    https://github.com/soalrseptem-ai/soalrseptem-core"
echo ""