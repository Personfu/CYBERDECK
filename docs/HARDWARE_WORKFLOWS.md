# Hardware Workflows — FLLC CyberDeck MK-1.0 (Pi400)

## Overview

The Pi400 CyberDeck is a portable network auditing and IoT ops console.
The Pi400 connects to test environments via USB peripherals, WiFi adapters,
and the GPIO header. **No voltage measurement** — the Pi400 is the ops hub.

## CyberDeck Peripheral Integration

| Device | Connection | Use Case |
|--------|-----------|----------|
| **Flipper Zero** | USB serial `/dev/ttyACM0` | Sub-GHz capture, RFID read, IR, GPIO |
| **Proxmark3 RDV4** | USB serial `/dev/ttyACM0` | LF/HF RFID read, write, emulate, clone |
| **HackRF One** | USB | SDR receive, transmit, spectrum sweep |
| **O.MG Cable** | WiFi AP `192.168.4.1` | USB implant payload push, exfil |
| **Shark Jack** | Ethernet `172.16.24.1` | LAN tap, auto-nmap, loot retrieval |
| **WiFi Pineapple** | Ethernet/WiFi `172.16.42.1` | Rogue AP, recon, client enumeration |
| **TP-Link TL-WN722N** | USB WiFi | Monitor mode, packet injection |
| **Chameleon Ultra** | USB serial | RFID emulation (Proxmark alternative) |
| **PiKVM v4** | Ethernet | Remote KVM access to target machines |
| **PortaPack H4M** | Standalone SDR | Field RF capture (transfer files to Pi) |

## Network Auditing Tools

| Tool | Purpose |
|------|---------|
| **Bettercap** | MITM, ARP spoofing, network recon, web UI |
| **TShark** | Deep packet capture & protocol analysis |
| **Tcpdump** | Lightweight packet capture |
| **Nmap** | Port scanning, service detection, OS fingerprint |
| **Hashcat** | Offline hash cracking (GPU-limited on Pi) |

## Session Templates

Templates in `/hardware/`:

| Template | Interface | Typical Use |
|----------|-----------|-------------|
| `session-template-uart.md` | UART | Serial console, boot logs (e.g. ESP32) |
| `session-template-i2c.md` | I2C | EEPROM reads, sensor buses |
| `session-template-spi.md` | SPI | Flash dumps, display config (e.g. DFRobot TFT) |
| `session-template-jtag.md` | JTAG/SWD | Debug access, firmware extraction |
| `session-template-emmc.md` | eMMC | Storage reads, partition analysis |

## Pi400 GPIO Header

The Pi400 exposes the standard 40-pin GPIO header:
- SPI0: MOSI=GPIO10, MISO=GPIO9, SCLK=GPIO11, CE0=GPIO8, CE1=GPIO7
- I2C1: SDA=GPIO2, SCL=GPIO3
- UART0: TX=GPIO14, RX=GPIO15

Use `gpio` tool in F600_AstraAudit.py for I2C scan, SPI probe, UART minicom.

## Session Logging

All tool sessions are automatically logged to `~/CYBERDECK/sessions/` as JSON files
with timestamp, tool name, and configuration details.

## Evidence Capture

- Upload files via `POST /upload` with SHA-256 computed automatically
- Packet captures auto-saved to `~/CYBERDECK/captures/`
- Link artifacts to sessions via the project/session/target IDs

See also: `docs/latex/hardware_workflows.tex`