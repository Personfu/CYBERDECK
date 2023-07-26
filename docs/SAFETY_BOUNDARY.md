# Safety Boundary

**FLLC CyberDeck MK-1.0 (Raspberry Pi 400)** is a network auditing ops console and IoT peripheral workbench.

## What This Tool IS

- A Pi400 CyberDeck CLI ops console for authorized network auditing
- A wrapper for network tools: bettercap, tshark, tcpdump, nmap, hashcat
- An interface to cyberdeck IoT peripherals: Flipper Zero, Proxmark3 RDV4, HackRF/SDR, O.MG Cable, Shark Jack, WiFi Pineapple
- A Pi400 GPIO/I2C/SPI/UART hardware session launcher
- A hardware session documentation workbench with JSON session logging
- A passive IoT device inventory with CSV import/export
- An evidence capture system with SHA-256 integrity tracking
- A report generator with severity matrix and PDF export
- An optional AI assistant for summarisation and drafting

## What This Tool IS NOT

- NOT a MACOBOX clone or competitor — no MACOBOX adapter board, no voltage measurement
- NOT a standalone exploit framework — it wraps existing authorized tools
- NOT a malware delivery system or evasion platform
- NOT intended for production use — prototype with unsanitised input

## Authorized Use Only

All tools require explicit authorization scope before use.
The Pi400 connects to test environments — it does not measure voltage or probe buses autonomously.

## AI Constraints

AI is ONLY used for: summarisation, drafting, clustering, naming, report writing.
AI is NEVER used for: payload generation, exploitation, or any offensive capability.

See also: docs/latex/safety_boundary.tex for the printable PDF version.