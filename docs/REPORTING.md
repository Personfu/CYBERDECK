# Reporting — FLLC CyberDeck (Pi400)

## Report Structure
- Title page with project name, date, classification
- Project metadata (ID, authorization scope, analyst)
- Authorization statement
- Executive summary (optionally AI-assisted)
- Scope of assessment
- Inventory summary (target devices table)
- **Severity matrix reference** (CRITICAL / HIGH / MEDIUM / LOW / INFO with CVSS ranges)
- Findings table with severity, CVSS score, status, description
- Evidence references with SHA-256 hashes
- Hardware sessions table (interface, voltage, adapter, observations)
- Analyst notes
- Recommendations
- Appendix

## Severity Matrix

| Level | CVSS | Description |
|-------|------|-------------|
| CRITICAL | 9.0-10.0 | Immediate risk, full device compromise possible |
| HIGH | 7.0-8.9 | Significant risk, exploitation likely |
| MEDIUM | 4.0-6.9 | Moderate risk, exploitation possible |
| LOW | 0.1-3.9 | Minor risk, limited impact |
| INFO | 0.0 | Informational, no direct risk |

## PDF Export
1. Open report detail page (`/reports/{id}`)
2. Click **PRINT / EXPORT TO PDF** button
3. Browser print dialog opens with print CSS applied
4. Select "Save as PDF" destination

## API
```
POST /reports/generate   {"project_id": "...", "title": "..."}
GET  /reports            List all reports
GET  /reports/{id}       Report metadata (JSON)
GET  /reports/{id}/view  Rendered HTML report (printable)
```

## Demo
Seeded report available at `/reports/report-demo-1` with Pi400 CyberDeck findings.

See also: `docs/latex/reporting.tex`