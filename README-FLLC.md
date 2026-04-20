# FLLC CyberDeck (Raspberry Pi400)

**A local-first, cyberpunk-inspired hardware analysis and authorized device assessment workbench.**

Built for:
- Project/target/session/evidence/report tracking
- Hardware interface analysis (UART, I2C, SPI, JTAG/SWD, eMMC)
- Passive IoT inventory management
- Evidence capture and chain-of-custody tracking
- Local AI assistance (summarization, drafting, clustering)
- Printable HTML reports with PDF export

**Inspired by MACOBOX and SATUNIX CYBERDECK projects.**

---

## Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd fllc-cyberdeck

# Start with Docker Compose
cd infra/docker
docker compose up --build
```

- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/healthz

---

## Repository Structure

```
/apps/web        - Express.js web frontend (cyberpunk theme)
/apps/api        - FastAPI backend (Python 3.11+)
/apps/worker     - Background worker for report generation
/packages/ui     - Shared UI components (future)
/packages/config - Shared configuration (future)
/data            - SQLite database, artifacts, reports
/docs            - Documentation
/hardware        - Hardware session templates (UART, I2C, SPI, JTAG, eMMC)
/scripts         - Utility scripts
/infra/docker    - Docker Compose configuration
```

---

## Features

### Project Console
- Track projects, targets, hardware sessions, evidence, reports
- Authorization scope management
- Classification levels (INTERNAL, CONFIDENTIAL, etc.)

### Hardware Analysis Workspace
- Document UART, I2C, SPI, JTAG/SWD, eMMC sessions
- Pin mapping and voltage notes
- Photo and artifact references
- Analyst observations

### Passive IoT Inventory
- Manual inventory entries
- Tags, notes, firmware versions
- Serial identifiers and ownership tracking

### Reporting
- Auto-generated HTML reports
- Print CSS for clean output
- Browser Print-to-PDF export
- Executive summary, findings, recommendations

### Local AI Assistant
- Adapter abstraction: none, ollama, openai-compatible-local
- Summarization, draft findings, evidence clustering
- Report writing assistance
- **Never used for exploitation or payload generation**

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /healthz | Health check |
| GET | /projects | List all projects |
| POST | /projects | Create project |
| GET | /projects/{id} | Get project details |
| GET | /projects/{id}/targets | List targets |
| POST | /projects/{id}/targets | Create target |
| GET | /projects/{id}/sessions | List sessions |
| POST | /projects/{id}/sessions | Create session |
| GET | /reports | List reports |
| POST | /reports/generate | Generate report |
| GET | /reports/{id} | Get report |
| GET | /reports/{id}/view | View HTML report |
| GET | /settings/ai | Get AI settings |
| POST | /settings/ai | Update AI settings |

---

## Testing

```bash
# Run API tests
cd apps/api
pip install -r reqs.txt
pytest test_api.py -v

# Or with Docker
docker compose exec api pytest test_api.py -v
```

---

## Safety Boundary

This platform is for **authorized lab and field documentation only**.

**Prohibited:**
- Exploit execution
- Brute forcing / credential harvesting
- Malware/payload generation
- Evasion workflows
- Persistence mechanisms
- One-click attacks

**Permitted:**
- Authorized hardware analysis
- Evidence capture and tracking
- Session documentation
- Report generation
- AI-assisted summarization (non-offensive)

See `docs/SAFETY_BOUNDARY.md` for details.

---

## Documentation

- `docs/ARCHITECTURE.md` - System architecture
- `docs/SAFETY_BOUNDARY.md` - Security constraints
- `docs/REPORTING.md` - Report generation
- `docs/LOCAL_AI.md` - AI adapter configuration
- `docs/HARDWARE_WORKFLOWS.md` - Hardware session workflows

---

## Hardware Templates

Located in `/hardware/`:
- `session-template-uart.md`
- `session-template-i2c.md`
- `session-template-spi.md`
- `session-template-jtag.md`
- `session-template-emmc.md`

Each template includes authorization checks, voltage verification, wiring notes, and artifact tracking.

---

## Tech Stack

- **Frontend**: Express.js, HTML/CSS/JS (cyberpunk theme)
- **Backend**: FastAPI, Pydantic, Python 3.11+
- **Worker**: Python 3.11+ (stdlib)
- **Storage**: SQLite, local filesystem
- **Runtime**: Docker Compose

---

## Known Limitations

- Single-user mode (no authentication)
- SQLite for simplicity (not for production scale)
- AI adapters are stubbed (integration pending)
- File uploads not implemented (artifact references only)

---

© FLLC, 2026. For internal authorized use only.
