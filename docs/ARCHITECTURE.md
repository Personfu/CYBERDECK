# FLLC CyberDeck MK-1.0 — Architecture

## Overview

FLLC CyberDeck is a **Raspberry Pi 400 network auditing ops console and IoT peripheral workbench**.
It runs as three Docker containers (web UI, API, worker) plus a standalone CLI tool (`F600_AstraAudit.py`)
that wraps network auditing tools and cyberdeck IoT peripherals.

**This is NOT** a MACOBOX clone or voltage measurement tool.
The Pi400 connects to test environments — it does not probe or measure.

## System Diagram

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│   Web UI    │─────▶│   FastAPI API    │─────▶│   Worker    │
│ Express:3000│      │    :8000         │      │ Python bg   │
└─────────────┘      └───────┬─────────┘      └──────┬──────┘
                             │                        │
                     ┌───────▼─────────┐      ┌──────▼──────┐
                     │  /data/         │      │ /data/      │
                     │  state.json     │      │ reports/    │
                     │                 │      │ uploads/    │
                     └─────────────────┘      └─────────────┘
                     ┌─────────────────┐
                     │ Ollama :11434   │  (optional)
                     └─────────────────┘
```

## Services

| Service | Tech | Port | Role |
|---------|------|------|------|
| `api` | FastAPI / Python 3.11 | 8000 | REST API, auth (JWT), state, uploads, CSV |
| `web` | Express / Node 18 | 3000 | Static HTML UI, API proxy |
| `worker` | Python 3.11 | — | Background report generation |
| `ollama` | Ollama (optional) | 11434 | Local LLM for AI features |

## Data Model

| Entity | Key Fields |
|--------|-----------|
| Project | id, name, summary, classification, authorization_scope |
| DeviceTarget | id, project_id, name, kind, vendor, model, firmware_version, tags |
| HardwareSession | id, project_id, target_id, interface_type, voltage, pin_map, observations |
| EvidenceArtifact | id, project_id, kind, path, sha256, notes |
| Report | id, project_id, title, state, findings[], generated_at |
| AgentTask | id, project_id, mode, state |

## Authentication

- JWT bearer tokens via `POST /auth/login`
- Default: `admin` / `cyberdeck` (change immediately)
- HMAC-SHA256 signed, 24h expiry

## Pi400 CyberDeck Hardware Context

This platform is designed around the SATUNIX/CYBERDECK hardware BOM:

- **Pi 400** — keyboard SBC running Kali ARM
- **DFRobot 3.5" TFT** — SPI display with waveshare35a overlay
- **TP-Link TL-WN722N** — external WiFi with driver patch
- **Adafruit CyberDeck enclosure** — mounting & portability
- **ANKO 5V/2A battery** — portable power via USB-C

## Directory Layout

```
apps/api/        FastAPI backend
apps/web/        Express + HTML UI
apps/worker/     Background worker
docs/            Markdown docs
docs/latex/      LaTeX → PDF (CI-built)
hardware/        Session templates
infra/docker/    docker-compose.yml
scripts/         Pi400 setup scripts
```