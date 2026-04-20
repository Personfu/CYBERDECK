# FLLC CyberDeck MK-1.0 (Raspberry Pi 400) — CLAUDE.md

## Project Identity

This is a **Raspberry Pi 400 CyberDeck** — a portable network auditing ops console
and IoT peripheral workbench. Pi400 builds and the broader cyberdeck community.

The Pi400 connects to test environments as an ops hub

## Core Tool: F600_AstraAudit.py (v6.0.0)

CLI ops console wrapping:
- **Network tools**: bettercap, tshark, tcpdump, nmap, hashcat
- **Cyberdeck peripherals**: Flipper Zero, Proxmark3, HackRF/SDR, O.MG Cable, Shark Jack, WiFi Pineapple
- **Pi400 hardware**: GPIO/I2C/SPI/UART, system diagnostics
- **Session logging**: all tool runs logged to ~/CYBERDECK/sessions/ as JSON

## Hardware Focus

- Raspberry Pi 400 (keyboard SBC, Kali ARM 64-bit)
- DFRobot 3.5" TFT (SPI, waveshare35a overlay)
- TP-Link TL-WN722N (external WiFi, monitor mode via driver patch)
- Adafruit CyberDeck enclosure
- ANKO 5V/2A USB-C battery pack
- Flipper Zero, Proxmark3 RDV4, HackRF One, O.MG Cable, Shark Jack (optional peripherals)

## See Also

- `README.md` — full setup and usage
- `docs/ARCHITECTURE.md` — system design
- `docs/SAFETY_BOUNDARY.md` — what this tool does NOT do
- `docs/HARDWARE_WORKFLOWS.md` — peripheral integration guide
