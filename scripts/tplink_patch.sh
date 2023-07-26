#!/bin/bash
# FLLC CyberDeck — TP-Link TL-WN722N v2/v3 Driver Patch
# For Raspberry Pi 400 running Kali Linux ARM
# Inspired by SATUNIX/CYBERDECK TPLINK_PATCH.sh
# Credit: David Bombal for the original patch method
#
# Chipset: RTL8188EUS (v2) or RTL8188FTV (v3)
# Driver:  aircrack-ng/rtl8188eus
#
# Run: sudo ./tplink_patch.sh
# Then: reboot

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  FLLC CYBERDECK — TP-LINK TL-WN722N DRIVER PATCH       ║"
echo "║  For Pi400 Kali ARM — monitor mode support              ║"
echo "╚══════════════════════════════════════════════════════════╝"

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] Run with sudo: sudo ./tplink_patch.sh"
    exit 1
fi

# Install build dependencies
echo "[*] Installing build dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    build-essential \
    dkms \
    bc \
    raspberrypi-kernel-headers \
    git

# Blacklist default r8188eu driver
echo "[*] Blacklisting default r8188eu driver..."
if ! grep -q "blacklist r8188eu" /etc/modprobe.d/blacklist.conf 2>/dev/null; then
    echo "blacklist r8188eu" >> /etc/modprobe.d/blacklist.conf
fi

# Clone aircrack-ng driver
DRIVER_DIR="/tmp/rtl8188eus"
if [ -d "$DRIVER_DIR" ]; then
    rm -rf "$DRIVER_DIR"
fi
echo "[*] Cloning aircrack-ng rtl8188eus driver..."
git clone https://github.com/aircrack-ng/rtl8188eus.git "$DRIVER_DIR"

# Build and install
cd "$DRIVER_DIR"
echo "[*] Building driver (this may take a few minutes on Pi400)..."
make -j$(nproc) 2>&1 | tail -5
echo "[*] Installing driver..."
make install

# Load module
echo "[*] Loading rtl8188eus module..."
modprobe 8188eu 2>/dev/null || true

echo ""
echo "[✓] TP-Link TL-WN722N driver patch complete."
echo "    Reboot to ensure clean module loading: sudo reboot"
echo ""
echo "    After reboot, verify with:"
echo "    iwconfig"
echo "    airmon-ng"
