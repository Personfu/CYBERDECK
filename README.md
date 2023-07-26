# FLLC CyberDeck MK-1.0 (Raspberry Pi 400)

> **Portable network auditing ops console & IoT peripheral workbench** — Pi400 cyberdeck, CLI-first, cyberpunk ops
>
> Built for the Pi 400 keyboard-computer, DFRobot 3.5" TFT, TP-Link WiFi adapter, and Adafruit CyberDeck enclosure.
> Inspired by [SATUNIX/CYBERDECK](https://github.com/SATUNIX/CYBERDECK) — budget Pi 400 hardware builds.
> **This is NOT a MACOBOX clone. No voltage measurement. The Pi400 is the ops hub.**

![status](https://img.shields.io/badge/STATUS-ACTIVE-00ffd6?style=flat-square)
![platform](https://img.shields.io/badge/PLATFORM-Pi400%20%7C%20Kali%20ARM-ff66ac?style=flat-square)
![license](https://img.shields.io/badge/LICENSE-GPLv3-333?style=flat-square)

---

## What Is This?

A **Pi400 CyberDeck CLI ops console** (`F600_AstraAudit.py` v6.0.0) plus a local-first web platform:

| Category | Tools |
|----------|-------|
| **Network Capture** | Bettercap, TShark, Tcpdump, Nmap, Hashcat |
| **Analyst Recon** | Wireless (aircrack-ng), ARP scan, Service enum, PCAP analysis, DNS recon |
| **CyberDeck Peripherals** | Flipper Zero, Proxmark3 RDV4, HackRF/SDR, O.MG Cable, Shark Jack, WiFi Pineapple |
| **Pi400 Ops** | GPIO/I2C/SPI/UART, system diagnostics, session log browser, tool dependency checker |
| **Web Platform** | Project console, hardware sessions, IoT inventory, reporting, optional local AI |

---

## Hardware BOM (Budget CyberDeck)

| # | Component | Notes |
|---|-----------|-------|
| 1 | **Raspberry Pi 400** | Keyboard-integrated SBC, USB-C power |
| 2 | **DFRobot 3.5" TFT** | SPI display, waveshare35a overlay |
| 3 | **Adafruit CyberDeck** | Enclosure / mounting kit |
| 4 | **ANKO Battery Pack** | 5V / 2A USB-C — tested stable under load |
| 5 | **TP-Link TL-WN722N v2/v3** | External WiFi — needs driver patch |

### Display Config (`/boot/config.txt`)
```
dtoverlay=waveshare35a,rotate=270,invertx=1,swapxy=1
```

### Driver Patches
```bash
# Clone this repo
git clone https://github.com/Personfu/CyberDeck.git
cd CyberDeck

# Pi400 driver setup (from SATUNIX/CYBERDECK heritage)
sudo ./scripts/lcd_install.sh     # DFRobot/waveshare TFT
sudo ./scripts/tplink_patch.sh    # TL-WN722N monitor-mode
```

---

## Quick Start (Docker Compose)

```bash
cd infra/docker
docker compose up --build
```

| Service | URL | Tech |
|---------|-----|------|
| Web UI | http://localhost:3000 | Express + cyberpunk HTML |
| API | http://localhost:8000 | FastAPI + Pydantic |
| Health | http://localhost:8000/healthz | → `{"status": "ONLINE"}` |

### Default Login
| Username | Password |
|----------|----------|
| `admin` | `cyberdeck` |

**Change immediately** via the API or settings page.

---

## Pages

| # | Page | Route |
|---|------|-------|
| 1 | Dashboard | `/` |
| 2 | Projects | `/projects` |
| 3 | Project Detail | `/projects/:id` |
| 4 | Targets (in project) | via project detail |
| 5 | Hardware Sessions | `/sessions` |
| 6 | Session Detail | `/sessions/:id` |
| 7 | Reports | `/reports` |
| 8 | Report Detail / Print | `/reports/:id` |
| 9 | Settings (AI config) | `/settings` |
| 10 | Safety Boundary | `/safety` |

---

## API Routes

```
GET    /healthz
POST   /auth/login
GET    /projects
POST   /projects
GET    /projects/{id}
GET    /projects/{id}/targets
POST   /projects/{id}/targets
GET    /projects/{id}/targets/export.csv
POST   /projects/{id}/targets/import
GET    /projects/{id}/sessions
POST   /projects/{id}/sessions
GET    /reports
POST   /reports/generate
GET    /reports/{id}
GET    /reports/{id}/view
POST   /upload
GET    /uploads/{artifact_id}/{filename}
GET    /artifacts
GET    /settings/ai
POST   /settings/ai
POST   /ai/summarize
POST   /ai/draft-finding
POST   /ai/suggest-names
POST   /ai/cluster
POST   /ai/assist-report
```

---

## Seed Data

The API seeds on first boot with realistic Pi400 CyberDeck data:

- **Project**: `PI400-BENCH-LAB` — bench lab hardware documentation
- **Project**: `PASSIVE-IOT-INVENTORY` — lab IoT device tracking
- **Targets**: ESP32 sensor, DFRobot TFT, TP-Link WN722N, Pi400 host
- **Sessions**: UART on ESP32, SPI on DFRobot TFT
- **Report**: Pi400 CyberDeck bench assessment with severity-rated findings

---

## Reports & Severity Matrix

Reports include a full severity matrix:

| Level | CVSS | Color |
|-------|------|-------|
| **CRITICAL** | 9.0–10.0 | Red |
| **HIGH** | 7.0–8.9 | Orange |
| **MEDIUM** | 4.0–6.9 | Yellow |
| **LOW** | 0.1–3.9 | Cyan |
| **INFO** | 0.0 | Gray |

Export to PDF: open report → click **PRINT / EXPORT TO PDF** → browser saves as PDF.

---

## Local AI (Optional)

| Backend | Config |
|---------|--------|
| `none` | Default — app works fully, no LLM needed |
| `ollama` | `POST /settings/ai {"backend":"ollama","config":{"endpoint":"http://localhost:11434","model":"llama3"}}` |
| `openai-compatible-local` | Any `/v1/chat/completions` endpoint (LM Studio, vLLM, LocalAI) |

AI is used **only** for: summarisation, draft findings, evidence clustering, naming suggestions, report writing.
AI is **never** used for: payload generation, exploitation, credential harvesting, evasion.

---

## Tests

```bash
cd apps/api
pip install -r reqs.txt
pytest test_api.py -v
```

Covers: health, auth, CRUD, upload, CSV import/export, AI adapters, full E2E happy path, severity matrix verification.

---

## CI/CD (GitHub Actions)

| Workflow | Triggers | Jobs |
|----------|----------|------|
| `ci.yml` | push main/develop, PRs | pytest, LaTeX PDF build, Docker build matrix, Compose smoke test |
| `release.yml` | `v*` tags | GHCR image push, GitHub Release with PDF artifacts |

---

## LaTeX Documentation

```bash
cd docs/latex
latexmk -pdf architecture.tex safety_boundary.tex hardware_workflows.tex reporting.tex local_ai.tex setup_guide.tex
```

PDFs are built automatically in CI and attached to releases.

---

## Safety Boundary

This platform is for **authorized network auditing and lab documentation**. See [`docs/SAFETY_BOUNDARY.md`](docs/SAFETY_BOUNDARY.md).

---

## CLI Ops Console — Quick Start

```bash
# Run directly on Pi400
python3 F600_AstraAudit.py

# Or make it a system command
chmod +x F600_AstraAudit.py
sudo ln -sf $(pwd)/F600_AstraAudit.py /usr/local/bin/cyberdeck
cyberdeck
```

All sessions logged to `~/CYBERDECK/sessions/`, captures to `~/CYBERDECK/captures/`.

---

## Repository Layout

```
├── F600_AstraAudit.py  CLI ops console (v6.0.0) — the main cyberdeck tool
├── apps/api/          FastAPI backend (auth, CRUD, upload, CSV, AI, reports)
├── apps/web/          Express + cyberpunk HTML UI
├── apps/worker/       Background report generation
├── docs/              Markdown documentation
├── docs/latex/        LaTeX source → PDF (built in CI)
├── hardware/          Session templates (UART, I2C, SPI, JTAG, eMMC)
├── infra/docker/      docker-compose.yml
├── scripts/           Pi400 setup scripts (LCD, TP-Link, etc.)
├── data/              Runtime data (gitignored)
└── .github/workflows/ CI + release pipelines
```

---

## Credits & Heritage

- **SATUNIX/CYBERDECK** — original Pi400 CyberDeck build scripts and hardware BOM
- **David Bombal** — TP-Link TL-WN722N driver patch method
- **Adafruit** — CyberDeck enclosure design
- **DFRobot / Waveshare** — 3.5" TFT display drivers

This project is **not affiliated with** MACOBOX, Lab401, or any commercial pentesting hardware vendor.
It is an independent, open-source documentation platform inspired by the CyberDeck maker community.

---

**FLLC Engineering Division** · Internal Use · MIT License
