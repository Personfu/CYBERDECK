#!/bin/bash
# FLLC CyberDeck — Requirements & Base Setup for Pi400
# Installs Docker, Python, and base dependencies for CyberDeck platform
#
# Run: sudo ./requirements_setup.sh

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  FLLC CYBERDECK — BASE REQUIREMENTS SETUP               ║"
echo "║  Docker + Python + Dependencies for Pi400                ║"
echo "╚══════════════════════════════════════════════════════════╝"

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] Run with sudo: sudo ./requirements_setup.sh"
    exit 1
fi

echo "[*] Updating package lists..."
apt-get update -qq

echo "[*] Installing base dependencies..."
apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release

# Install Docker if not present
if ! command -v docker &>/dev/null; then
    echo "[*] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "$SUDO_USER" 2>/dev/null || true
    systemctl enable docker
    systemctl start docker
    echo "[✓] Docker installed. Log out and back in for group membership."
else
    echo "[*] Docker already installed."
fi

# Install Docker Compose plugin if not present
if ! docker compose version &>/dev/null; then
    echo "[*] Installing Docker Compose plugin..."
    apt-get install -y docker-compose-plugin
fi

echo ""
echo "[✓] Base requirements installed."
echo "    Next steps:"
echo "    1. sudo ./scripts/lcd_install.sh    # DFRobot TFT display"
echo "    2. sudo ./scripts/tplink_patch.sh   # WiFi adapter driver"
echo "    3. cd infra/docker && docker compose up --build"
