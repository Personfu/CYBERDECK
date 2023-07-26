#!/bin/bash
# FLLC CyberDeck — DFRobot/Waveshare 3.5" TFT LCD Installer
# For Raspberry Pi 400 CyberDeck builds
# Inspired by SATUNIX/CYBERDECK LCD_INSTALLER.sh
#
# Display: DFRobot DFR0928 or Waveshare 3.5" TFT (SPI)
# Overlay: waveshare35a
# Config:  rotate=270, invertx=1, swapxy=1
#
# Run: sudo ./lcd_install.sh
# Then: reboot

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  FLLC CYBERDECK — LCD DISPLAY INSTALLER                 ║"
echo "║  DFRobot / Waveshare 3.5\" TFT for Pi400                ║"
echo "╚══════════════════════════════════════════════════════════╝"

if [ "$(id -u)" -ne 0 ]; then
    echo "[ERROR] Run with sudo: sudo ./lcd_install.sh"
    exit 1
fi

# Install dependencies
echo "[*] Installing display dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends \
    raspberrypi-kernel-headers \
    xserver-xorg-input-evdev

# Clone waveshare driver if not present
DRIVER_DIR="/tmp/LCD-show"
if [ ! -d "$DRIVER_DIR" ]; then
    echo "[*] Cloning LCD driver..."
    git clone https://github.com/goodtft/LCD-show.git "$DRIVER_DIR"
fi

# Backup existing config
BOOT_CONFIG="/boot/config.txt"
if [ -f "$BOOT_CONFIG" ]; then
    cp "$BOOT_CONFIG" "${BOOT_CONFIG}.bak.$(date +%s)"
    echo "[*] Backed up $BOOT_CONFIG"
fi

# Add dtoverlay if not present
if ! grep -q "waveshare35a" "$BOOT_CONFIG" 2>/dev/null; then
    echo "" >> "$BOOT_CONFIG"
    echo "# FLLC CyberDeck — DFRobot 3.5\" TFT display" >> "$BOOT_CONFIG"
    echo "dtoverlay=waveshare35a,rotate=270,invertx=1,swapxy=1" >> "$BOOT_CONFIG"
    echo "[*] Added waveshare35a overlay to $BOOT_CONFIG"
else
    echo "[*] waveshare35a overlay already present in $BOOT_CONFIG"
fi

echo ""
echo "[✓] LCD install complete. Reboot to activate display."
echo "    sudo reboot"
echo ""
echo "    Display config in $BOOT_CONFIG:"
echo "    dtoverlay=waveshare35a,rotate=270,invertx=1,swapxy=1"
