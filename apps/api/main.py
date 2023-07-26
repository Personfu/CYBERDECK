from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, uuid, hashlib, csv, io, secrets, hmac
from datetime import datetime, timedelta
from typing import List, Optional
from jinja2 import Template
from models import Project, DeviceTarget, HardwareSession, EvidenceArtifact, Report, AgentTask
from ai_adapter import get_adapter

DATA_DIR = os.environ.get('DATA_DIR', '/data')
DATA_FILE = DATA_DIR + '/state.json'
REPORT_DIR = DATA_DIR + '/reports'
UPLOAD_DIR = DATA_DIR + '/uploads'
JWT_SECRET = os.environ.get('JWT_SECRET', 'cyberdeck-secret-change-me')
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR, exist_ok=True)
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="FLLC CyberDeck API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def load_state():
    if not os.path.exists(DATA_FILE):
        return {"projects":[],"targets":[],"sessions":[],"artifacts":[],"reports":[],"tasks":[],"settings":{}}
    with open(DATA_FILE,'r') as f:
        return json.load(f)

def save_state(state):
    with open(DATA_FILE,'w') as f:
        json.dump(state, f, default=str, indent=2)

# ═══════════════════════════════════════════════════════════════════════
# AUTH — lightweight JWT (HMAC-SHA256, no external library needed)
# ═══════════════════════════════════════════════════════════════════════
import base64

def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()

def _b64d(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + '=' * pad)

def _make_jwt(payload: dict) -> str:
    header = _b64e(json.dumps({"alg":"HS256","typ":"JWT"}).encode())
    body = _b64e(json.dumps(payload, default=str).encode())
    sig = _b64e(hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"

def _verify_jwt(token: str) -> dict:
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("bad token")
    header, body, sig = parts
    expected = _b64e(hmac.new(JWT_SECRET.encode(), f"{header}.{body}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        raise ValueError("invalid signature")
    payload = json.loads(_b64d(body))
    if datetime.fromisoformat(payload['exp']) < datetime.utcnow():
        raise ValueError("expired")
    return payload

def verify_token(authorization: Optional[str] = Header(None)):
    """Dependency: extracts and verifies JWT. Returns username or raises 401."""
    if authorization is None:
        raise HTTPException(401, "missing Authorization header")
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(401, "invalid auth scheme")
    try:
        payload = _verify_jwt(token)
        return payload.get('sub', 'unknown')
    except Exception as e:
        raise HTTPException(401, f"auth failed: {e}")

class LoginIn(BaseModel):
    username: str
    password: str

@app.post('/auth/login')
def login(body: LoginIn):
    state = load_state()
    users = state.get('users', {})
    pw_hash = hashlib.sha256(body.password.encode()).hexdigest()
    stored = users.get(body.username)
    if stored is None or stored != pw_hash:
        raise HTTPException(401, "invalid credentials")
    token = _make_jwt({
        "sub": body.username,
        "iat": datetime.utcnow().isoformat(),
        "exp": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    })
    return {"token": token, "username": body.username}

@app.get('/healthz')
def healthz():
    return {"status": "ONLINE"}

@app.get('/projects')
def get_projects():
    state = load_state()
    return state.get('projects', [])

class ProjectIn(BaseModel):
    name: str
    summary: str = ""
    classification: str = "INTERNAL"
    authorization_scope: str = ""

@app.post('/projects')
def create_project(p: ProjectIn):
    state = load_state()
    proj = Project(name=p.name, summary=p.summary, classification=p.classification, authorization_scope=p.authorization_scope)
    state.setdefault('projects', []).append(proj.model_dump())
    save_state(state)
    return proj

@app.get('/projects/{project_id}')
def get_project(project_id: str):
    state = load_state()
    for p in state.get('projects', []):
        if p.get('id') == project_id:
            return p
    raise HTTPException(status_code=404, detail='project not found')

@app.get('/projects/{project_id}/targets')
def get_targets(project_id: str):
    state = load_state()
    return [t for t in state.get('targets', []) if t.get('project_id') == project_id]

class TargetIn(BaseModel):
    name: str
    kind: str = 'generic'
    vendor: str = ''
    model: str = ''
    firmware_version: str = ''
    environment: str = 'lab'
    notes: str = ''
    tags: List[str] = []

@app.post('/projects/{project_id}/targets')
def create_target(project_id: str, t: TargetIn):
    state = load_state()
    tgt = DeviceTarget(project_id=project_id, name=t.name, kind=t.kind, vendor=t.vendor, model=t.model, firmware_version=t.firmware_version, environment=t.environment, notes=t.notes, tags=t.tags)
    state.setdefault('targets', []).append(tgt.model_dump())
    save_state(state)
    return tgt

@app.get('/projects/{project_id}/sessions')
def get_sessions(project_id: str):
    state = load_state()
    return [s for s in state.get('sessions', []) if s.get('project_id') == project_id]

class SessionIn(BaseModel):
    target_id: str = None
    interface_type: str = 'USB'
    connection_method: str = 'direct'
    adapter: str = ''
    configuration: str = ''
    observations: str = ''

@app.post('/projects/{project_id}/sessions')
def create_session(project_id: str, s: SessionIn):
    state = load_state()
    sess = HardwareSession(project_id=project_id, target_id=s.target_id, interface_type=s.interface_type, connection_method=s.connection_method, adapter=s.adapter, configuration=s.configuration, observations=s.observations)
    state.setdefault('sessions', []).append(sess.model_dump())
    save_state(state)
    return sess

@app.get('/reports')
def list_reports():
    state = load_state()
    return state.get('reports', [])

class ReportGenIn(BaseModel):
    project_id: str
    title: str = ''

REPORT_TEMPLATE = '''<!doctype html>
<html>
<head>
  <title>{{title}}</title>
  <style>
    @media print {
      .no-print { display:none !important }
      body { background:#fff; color:#000; }
      .header { background:#fff; border-color:#000; }
      h1,.section h2 { color:#000; }
      .chip { background:#eee; color:#000; border-color:#ccc; }
      .severity-critical { background:#fdd; color:#900; }
      .severity-high { background:#fed; color:#960; }
      .severity-medium { background:#ffd; color:#660; }
      .severity-low { background:#dff; color:#066; }
      .severity-info { background:#eee; color:#666; }
    }
    @page { margin: 1.5cm; }
    * { box-sizing: border-box; }
    body { background:#0b0b0b; color:#dfffe0; font-family:'Segoe UI',Arial,sans-serif; margin:0; padding:0; }
    .header { padding:40px; border-bottom:3px solid #00ffd6; background:#050505; text-align:center; }
    h1 { text-transform:uppercase; letter-spacing:3px; margin:0 0 10px; color:#00ffd6; font-size:28px; }
    .subtitle { color:#888; font-size:14px; }
    .chip { display:inline-block; padding:5px 14px; background:#001a1a; color:#0f0; margin:4px; border-radius:4px; font-size:11px; border:1px solid #003; text-transform:uppercase; }
    .content { padding:30px; max-width:950px; margin:0 auto; }
    .section { background:#0a0a0a; border:1px solid #222; border-radius:8px; padding:24px; margin:24px 0; }
    .section h2 { color:#00ffd6; text-transform:uppercase; font-size:14px; border-bottom:1px solid #333; padding-bottom:12px; margin:0 0 16px; letter-spacing:1px; }
    table { width:100%; border-collapse:collapse; margin:12px 0; }
    th,td { text-align:left; padding:10px 12px; border-bottom:1px solid #222; font-size:13px; }
    th { color:#0ff; text-transform:uppercase; font-size:11px; background:#060606; }
    .severity-critical { background:#3a0000; color:#ff4444; font-weight:bold; }
    .severity-high { background:#3a1a00; color:#ff9944; font-weight:bold; }
    .severity-medium { background:#3a3a00; color:#ffdd44; }
    .severity-low { background:#003a3a; color:#44ddff; }
    .severity-info { background:#1a1a1a; color:#888; }
    .btn { background:#00ffd6; color:#000; border:none; padding:14px 28px; cursor:pointer; font-weight:bold; text-transform:uppercase; border-radius:4px; font-size:14px; }
    .btn:hover { background:#00ccaa; }
    .footer { text-align:center; padding:30px; color:#555; font-size:11px; border-top:1px solid #222; }
    .meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
    .meta-item { padding:8px; background:#060606; border-radius:4px; }
    .meta-label { color:#0ff; font-size:10px; text-transform:uppercase; }
    .meta-value { color:#bbb; font-size:13px; margin-top:4px; }
    .severity-matrix { margin:20px 0; }
    .severity-matrix td:first-child { width:100px; text-align:center; border-radius:4px; }
    ul { padding-left:20px; }
    li { padding:4px 0; color:#bbb; }
  </style>
</head>
<body>
  <div class="header">
    <h1>{{title}}</h1>
    <div class="subtitle">FLLC CyberDeck &mdash; Authorized Hardware Analysis Report</div>
    <div style="margin-top:12px">
      <span class="chip">{{state}}</span>
      <span class="chip">Generated: {{generated_at}}</span>
      <span class="chip">Classification: {{classification}}</span>
    </div>
  </div>
  <div class="content">
    <div class="section">
      <h2>Project Information</h2>
      <div class="meta-grid">
        <div class="meta-item"><div class="meta-label">Project ID</div><div class="meta-value">{{project_id}}</div></div>
        <div class="meta-item"><div class="meta-label">Project Name</div><div class="meta-value">{{project_name}}</div></div>
        <div class="meta-item"><div class="meta-label">Authorization Scope</div><div class="meta-value">{{authorization_scope}}</div></div>
        <div class="meta-item"><div class="meta-label">Analyst</div><div class="meta-value">{{analyst}}</div></div>
      </div>
    </div>

    <div class="section">
      <h2>Authorization Statement</h2>
      <p>This assessment was conducted under authorized scope. All activities documented herein were performed with explicit written permission from the device owner. Testing was limited to the scope defined in the project authorization.</p>
    </div>

    <div class="section">
      <h2>Executive Summary</h2>
      <p>{{summary}}</p>
    </div>

    <div class="section">
      <h2>Scope</h2>
      <p>{{scope}}</p>
    </div>

    {% if targets %}
    <div class="section">
      <h2>Inventory Summary</h2>
      <table>
        <tr><th>Device</th><th>Kind</th><th>Vendor</th><th>Model</th><th>Firmware</th></tr>
        {% for t in targets %}
        <tr><td>{{t.name}}</td><td>{{t.kind}}</td><td>{{t.vendor}}</td><td>{{t.model}}</td><td>{{t.firmware_version}}</td></tr>
        {% endfor %}
      </table>
    </div>
    {% endif %}

    <div class="section">
      <h2>Severity Matrix Reference</h2>
      <table class="severity-matrix">
        <tr><th>Level</th><th>CVSS Range</th><th>Description</th></tr>
        <tr><td class="severity-critical">CRITICAL</td><td>9.0 &ndash; 10.0</td><td>Immediate risk, full device compromise possible</td></tr>
        <tr><td class="severity-high">HIGH</td><td>7.0 &ndash; 8.9</td><td>Significant risk, exploitation likely without mitigation</td></tr>
        <tr><td class="severity-medium">MEDIUM</td><td>4.0 &ndash; 6.9</td><td>Moderate risk, exploitation possible under conditions</td></tr>
        <tr><td class="severity-low">LOW</td><td>0.1 &ndash; 3.9</td><td>Minor risk, limited impact</td></tr>
        <tr><td class="severity-info">INFO</td><td>0.0</td><td>Informational observation, no direct risk</td></tr>
      </table>
    </div>

    <div class="section">
      <h2>Findings</h2>
      {% if findings %}
      <table>
        <tr><th>#</th><th>Title</th><th>Severity</th><th>CVSS</th><th>Status</th><th>Description</th></tr>
        {% for f in findings %}
        <tr>
          <td>{{loop.index}}</td>
          <td>{{f.title}}</td>
          <td class="severity-{{f.severity|lower}}">{{f.severity}}</td>
          <td>{{f.cvss}}</td>
          <td>{{f.status}}</td>
          <td>{{f.description}}</td>
        </tr>
        {% endfor %}
      </table>
      {% else %}
      <p>No findings recorded.</p>
      {% endif %}
    </div>

    {% if evidence %}
    <div class="section">
      <h2>Evidence References</h2>
      <table>
        <tr><th>Artifact</th><th>Kind</th><th>SHA-256</th><th>Notes</th></tr>
        {% for e in evidence %}
        <tr><td>{{e.filename or e.path}}</td><td>{{e.kind}}</td><td style="font-family:monospace;font-size:10px">{{e.sha256[:16]}}...</td><td>{{e.notes}}</td></tr>
        {% endfor %}
      </table>
    </div>
    {% endif %}

    {% if sessions %}
    <div class="section">
      <h2>Connection Sessions</h2>
      <table>
        <tr><th>Interface</th><th>Method</th><th>Adapter</th><th>Observations</th></tr>
        {% for s in sessions %}
        <tr><td>{{s.interface_type}}</td><td>{{s.connection_method}}</td><td>{{s.adapter}}</td><td>{{s.observations}}</td></tr>
        {% endfor %}
      </table>
    </div>
    {% endif %}

    <div class="section">
      <h2>Analyst Notes</h2>
      <p>{{analyst_notes or 'No additional notes.'}}</p>
    </div>

    <div class="section">
      <h2>Recommendations</h2>
      <ul>
        {% for r in recommendations %}
        <li>{{r}}</li>
        {% endfor %}
      </ul>
    </div>

    <div class="section">
      <h2>Appendix</h2>
      <p>Session templates, pin maps, and raw captures are available in the project evidence store.</p>
    </div>

    <div class="section no-print">
      <h2>Export to PDF</h2>
      <p>Press <strong>Ctrl+P</strong> (or <strong>Cmd+P</strong> on macOS) and select <em>Save as PDF</em>.</p>
      <button class="btn" onclick="window.print()">PRINT / EXPORT TO PDF</button>
    </div>
  </div>
  <div class="footer">
    FLLC CyberDeck v2.0 &mdash; Authorized Hardware Analysis Platform &mdash; Confidential
  </div>
</body>
</html>'''

def render_report_html(report, state=None):
    tpl = Template(REPORT_TEMPLATE)
    project = {}
    targets = []
    sessions = []
    evidence = []
    if state:
        for p in state.get('projects', []):
            if p.get('id') == report.get('project_id'):
                project = p
                break
        targets = [t for t in state.get('targets', []) if t.get('project_id') == report.get('project_id')]
        sessions = [s for s in state.get('sessions', []) if s.get('project_id') == report.get('project_id')]
        evidence = [a for a in state.get('artifacts', []) if a.get('project_id') == report.get('project_id')]
    return tpl.render(
        title=report.get('title'),
        state=report.get('state'),
        generated_at=report.get('generated_at'),
        project_id=report.get('project_id'),
        project_name=project.get('name', report.get('project_id', '')),
        classification=project.get('classification', 'INTERNAL'),
        authorization_scope=project.get('authorization_scope', ''),
        analyst='FLLC Analyst',
        summary=report.get('summary'),
        scope=project.get('authorization_scope', 'See project authorization.'),
        findings=report.get('findings', []),
        targets=targets,
        sessions=sessions,
        evidence=evidence,
        analyst_notes=report.get('analyst_notes', ''),
        recommendations=report.get('recommendations', [
            'Continue authorized device assessment procedures',
            'Document all hardware interface sessions with photos',
            'Maintain evidence chain of custody with SHA-256 verification',
            'Review and update firmware on identified devices',
            'Implement findings remediation per severity matrix'
        ])
    )

@app.post('/reports/generate')
def generate_report(r: ReportGenIn):
    state = load_state()
    # Gather project info for richer report
    project = {}
    for p in state.get('projects', []):
        if p.get('id') == r.project_id:
            project = p
            break
    report = Report(project_id=r.project_id, title=r.title or f"Report for {project.get('name', r.project_id)}")
    report.generated_at = datetime.utcnow()
    report.state = 'READY'
    report.summary = f"Authorized hardware analysis report for project {project.get('name', r.project_id)}. " \
                     f"Assessment conducted under scope: {project.get('authorization_scope', 'N/A')}."
    report_dict = report.model_dump()
    state.setdefault('reports', []).append(report_dict)
    save_state(state)
    rid = report.id
    html = render_report_html(report_dict, state)
    path = os.path.join(REPORT_DIR, f"{rid}.html")
    with open(path, 'w') as f:
        f.write(html)
    return {"id": rid}

@app.get('/reports/{report_id}')
def get_report(report_id: str):
    state = load_state()
    for r in state.get('reports', []):
        if r.get('id') == report_id:
            return r
    raise HTTPException(status_code=404, detail='report not found')

@app.get('/reports/{report_id}/view', response_class=HTMLResponse)
def view_report(report_id: str):
    path = os.path.join(REPORT_DIR, f"{report_id}.html")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return HTMLResponse(content=f.read(), status_code=200)
    raise HTTPException(status_code=404, detail='report artifact not found')

# --- AI Endpoints ---

class AISummarizeIn(BaseModel):
    text: str

@app.post('/ai/summarize')
def ai_summarize(body: AISummarizeIn):
    state = load_state()
    ai_settings = state.get('settings', {}).get('ai', None)
    adapter = get_adapter(ai_settings)
    result = adapter.summarize(body.text)
    return {"result": result}

class AIDraftFindingIn(BaseModel):
    observations: str

@app.post('/ai/draft-finding')
def ai_draft_finding(body: AIDraftFindingIn):
    state = load_state()
    ai_settings = state.get('settings', {}).get('ai', None)
    adapter = get_adapter(ai_settings)
    result = adapter.draft_finding(body.observations)
    return {"result": result}

class AISuggestNamesIn(BaseModel):
    context: str

@app.post('/ai/suggest-names')
def ai_suggest_names(body: AISuggestNamesIn):
    state = load_state()
    ai_settings = state.get('settings', {}).get('ai', None)
    adapter = get_adapter(ai_settings)
    result = adapter.suggest_names(body.context)
    return {"result": result}

class AIClusterIn(BaseModel):
    items: List[str]

@app.post('/ai/cluster')
def ai_cluster(body: AIClusterIn):
    state = load_state()
    ai_settings = state.get('settings', {}).get('ai', None)
    adapter = get_adapter(ai_settings)
    result = adapter.cluster_evidence(body.items)
    return {"result": result}

@app.post('/ai/assist-report')
def ai_assist_report(body: dict):
    state = load_state()
    ai_settings = state.get('settings', {}).get('ai', None)
    adapter = get_adapter(ai_settings)
    result = adapter.assist_report(body)
    return {"result": result}

# ═══════════════════════════════════════════════════════════════════════
# FILE UPLOAD
# ═══════════════════════════════════════════════════════════════════════

@app.post('/upload')
async def upload_file(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    target_id: str = Form(""),
    session_id: str = Form(""),
    kind: str = Form("file"),
    notes: str = Form("")
):
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"file exceeds {MAX_UPLOAD_BYTES} bytes")

    artifact_id = str(uuid.uuid4())
    sha = hashlib.sha256(contents).hexdigest()
    dest_dir = os.path.join(UPLOAD_DIR, artifact_id)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, file.filename)
    with open(dest_path, 'wb') as f:
        f.write(contents)

    artifact = {
        "id": artifact_id,
        "project_id": project_id,
        "target_id": target_id,
        "session_id": session_id,
        "kind": kind,
        "path": f"uploads/{artifact_id}/{file.filename}",
        "sha256": sha,
        "notes": notes,
        "created_at": datetime.utcnow().isoformat(),
        "filename": file.filename,
        "size": len(contents)
    }
    state = load_state()
    state.setdefault('artifacts', []).append(artifact)
    save_state(state)
    return artifact

@app.get('/uploads/{artifact_id}/{filename}')
def download_file(artifact_id: str, filename: str):
    path = os.path.join(UPLOAD_DIR, artifact_id, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "file not found")
    return FileResponse(path, filename=filename)

@app.get('/artifacts')
def list_artifacts(project_id: str = None):
    state = load_state()
    arts = state.get('artifacts', [])
    if project_id:
        arts = [a for a in arts if a.get('project_id') == project_id]
    return arts

# ═══════════════════════════════════════════════════════════════════════
# CSV IMPORT / EXPORT
# ═══════════════════════════════════════════════════════════════════════

CSV_FIELDS = ['name','kind','vendor','model','firmware_version','environment','notes','tags']

@app.get('/projects/{project_id}/targets/export.csv')
def export_targets_csv(project_id: str):
    state = load_state()
    targets = [t for t in state.get('targets', []) if t.get('project_id') == project_id]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, extrasaction='ignore')
    writer.writeheader()
    for t in targets:
        row = {k: t.get(k, '') for k in CSV_FIELDS}
        if isinstance(row.get('tags'), list):
            row['tags'] = ';'.join(row['tags'])
        writer.writerow(row)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename=targets-{project_id}.csv'}
    )

@app.post('/projects/{project_id}/targets/import')
async def import_targets_csv(project_id: str, file: UploadFile = File(...)):
    contents = (await file.read()).decode('utf-8')
    reader = csv.DictReader(io.StringIO(contents))
    state = load_state()
    imported = []
    for row in reader:
        tags = [t.strip() for t in row.get('tags', '').split(';') if t.strip()]
        tgt = DeviceTarget(
            project_id=project_id,
            name=row.get('name', 'Imported'),
            kind=row.get('kind', 'generic'),
            vendor=row.get('vendor', ''),
            model=row.get('model', ''),
            firmware_version=row.get('firmware_version', ''),
            environment=row.get('environment', 'lab'),
            notes=row.get('notes', ''),
            tags=tags
        )
        state.setdefault('targets', []).append(tgt.model_dump())
        imported.append(tgt.model_dump())
    save_state(state)
    return {"imported": len(imported), "targets": imported}


@app.get('/settings/ai')
def get_ai_settings():
    state = load_state()
    return state.get('settings', {}).get('ai', {"backend": "none"})

class AiIn(BaseModel):
    backend: str
    config: dict = {}

@app.post('/settings/ai')
def set_ai_settings(a: AiIn):
    state = load_state()
    state.setdefault('settings', {})['ai'] = {"backend": a.backend, "config": a.config}
    save_state(state)
    return state['settings']['ai']

@app.on_event('startup')
def ensure_seed():
    if not os.path.exists(DATA_FILE):
        admin_pw_hash = hashlib.sha256('cyberdeck'.encode()).hexdigest()
        now = datetime.utcnow().isoformat()
        state = {
            "users": {"admin": admin_pw_hash},
            "projects": [
                {"id": "proj-cyberdeck-build", "name": "CYBERDECK-MK1-BUILD", "summary": "Pi400 CyberDeck MK-1.0 build documentation. Budget portable deck: Pi400 keyboard computer, DFRobot 3.5in TFT, TP-Link WN722N, Adafruit enclosure, ANKO battery. Inspired by SATUNIX/CYBERDECK.", "classification": "INTERNAL", "authorization_scope": "Personal build — owned hardware only", "created_at": now, "updated_at": now},
                {"id": "proj-iot-inventory", "name": "IOT-DEVICE-INVENTORY", "summary": "Full catalog of CyberDeck peripherals and IoT tools. Firmware versions, serial numbers, connection methods, USB enumeration. CSV import/export.", "classification": "INTERNAL", "authorization_scope": "Owned equipment inventory — documentation only", "created_at": now, "updated_at": now},
                {"id": "proj-test-env", "name": "TEST-ENVIRONMENT-SESSIONS", "summary": "Connection sessions from Pi400 CyberDeck to lab test environments. WiFi surveys, SDR recordings, RFID reads, network taps — all on owned/authorized networks.", "classification": "INTERNAL", "authorization_scope": "Authorized lab networks and owned test devices only", "created_at": now, "updated_at": now}
            ],
            "targets": [
                {"id": "tgt-rpi400", "project_id": "proj-cyberdeck-build", "name": "Raspberry Pi 400", "kind": "sbc", "vendor": "Raspberry Pi Foundation", "model": "Pi 400 (4GB)", "firmware_version": "Kali ARM 2023.1 64-bit", "environment": "cyberdeck", "notes": "Keyboard-integrated SBC — the compute heart of the CyberDeck. USB-C power, dual micro-HDMI, USB 3.0+2.0. Running Kali Linux ARM.", "tags": ["pi400", "cyberdeck", "host", "kali", "arm64"]},
                {"id": "tgt-dfrobot-tft", "project_id": "proj-cyberdeck-build", "name": "DFRobot 3.5in TFT Display", "kind": "display", "vendor": "DFRobot", "model": "DFR0928 (waveshare35a compatible)", "firmware_version": "N/A", "environment": "cyberdeck", "notes": "SPI TFT on Pi400 GPIO header. Uses waveshare35a dtoverlay. LCD_INSTALLER.sh configures display and touch input.", "tags": ["display", "spi", "cyberdeck", "tft"]},
                {"id": "tgt-tplink", "project_id": "proj-cyberdeck-build", "name": "TP-Link TL-WN722N WiFi Adapter", "kind": "wifi-adapter", "vendor": "TP-Link", "model": "TL-WN722N v2/v3", "firmware_version": "rtl8188eus (patched)", "environment": "cyberdeck", "notes": "External USB WiFi — monitor mode after driver patch. TPLINK_PATCH.sh automates David Bombal method. Budget alternative to Alfa.", "tags": ["wifi", "usb", "monitor-mode", "cyberdeck"]},
                {"id": "tgt-adafruit-case", "project_id": "proj-cyberdeck-build", "name": "Adafruit CyberDeck Enclosure", "kind": "enclosure", "vendor": "Adafruit", "model": "Pi400 CyberDeck Kit", "firmware_version": "N/A", "environment": "cyberdeck", "notes": "Mounts TFT above Pi400 keyboard. Battery underneath. Looks like a Yu-Gi-Oh card deck.", "tags": ["enclosure", "3d-print", "cyberdeck"]},
                {"id": "tgt-anko-battery", "project_id": "proj-cyberdeck-build", "name": "ANKO USB-C Battery Pack", "kind": "power", "vendor": "ANKO", "model": "5V 2A USB-C Power Bank", "firmware_version": "N/A", "environment": "cyberdeck", "notes": "Portable power. 5V/2A USB-C. Tested stable with Pi400 + TFT + WiFi adapter under load.", "tags": ["battery", "power", "usb-c", "cyberdeck"]},
                {"id": "tgt-flipper-zero", "project_id": "proj-iot-inventory", "name": "Flipper Zero", "kind": "multi-tool", "vendor": "Flipper Devices", "model": "Flipper Zero", "firmware_version": "0.98.3", "environment": "field", "notes": "Sub-GHz, 125kHz/13.56MHz RFID, IR, iButton, GPIO, USB HID. Connects to Pi400 via USB for firmware updates and log download.", "tags": ["flipper", "rfid", "sub-ghz", "ir", "nfc", "multi-tool"]},
                {"id": "tgt-proxmark3", "project_id": "proj-iot-inventory", "name": "Proxmark 3 RDV4.01", "kind": "rfid-tool", "vendor": "Proxmark", "model": "RDV4.01", "firmware_version": "Iceman FW latest", "environment": "lab", "notes": "LF+HF RFID read/write/emulate/sniff. USB serial to Pi400. pm3 client runs natively on Kali ARM.", "tags": ["proxmark", "rfid", "lf", "hf", "nfc"]},
                {"id": "tgt-chameleon-ultra", "project_id": "proj-iot-inventory", "name": "Chameleon Ultra", "kind": "rfid-emulator", "vendor": "ChameleonTiny", "model": "Chameleon Ultra", "firmware_version": "2.0", "environment": "field", "notes": "LF+HF RFID emulator/reader. BLE + USB to Pi400 for firmware and slot management.", "tags": ["chameleon", "rfid", "emulator", "ble"]},
                {"id": "tgt-hackrf", "project_id": "proj-iot-inventory", "name": "HackRF One + PortaPack H4M", "kind": "sdr", "vendor": "Great Scott Gadgets / PortaPack", "model": "HackRF One + H4M", "firmware_version": "Mayhem FW 2.0", "environment": "field", "notes": "SDR 1MHz-6GHz TX/RX. PortaPack adds standalone screen with Mayhem firmware. USB to Pi400 for GNU Radio / SDR++. Also standalone.", "tags": ["hackrf", "sdr", "portapack", "rf"]},
                {"id": "tgt-tinysa", "project_id": "proj-iot-inventory", "name": "TinySA Ultra+", "kind": "spectrum-analyzer", "vendor": "TinySA", "model": "Ultra+", "firmware_version": "1.4", "environment": "field", "notes": "Portable spectrum analyzer. USB to Pi400 for screenshots and frequency logging.", "tags": ["tinysa", "spectrum", "rf", "analyzer"]},
                {"id": "tgt-pineapple", "project_id": "proj-iot-inventory", "name": "Hak5 WiFi Pineapple Mark VII", "kind": "wifi-audit", "vendor": "Hak5", "model": "WiFi Pineapple Mark VII", "firmware_version": "2.1.2", "environment": "lab", "notes": "WiFi auditing platform. Ethernet to Pi400 USB-Ethernet adapter. Dashboard at 172.16.42.1:1471.", "tags": ["hak5", "wifi", "pineapple"]},
                {"id": "tgt-shark-jack", "project_id": "proj-iot-inventory", "name": "Hak5 Shark Jack", "kind": "network-tool", "vendor": "Hak5", "model": "Shark Jack", "firmware_version": "1.1.0", "environment": "field", "notes": "Keyring network auditor. Ethernet plug for nmap/loot. Results to Pi400 via USB.", "tags": ["hak5", "ethernet", "network"]},
                {"id": "tgt-packet-squirrel", "project_id": "proj-iot-inventory", "name": "Hak5 Packet Squirrel MkII", "kind": "network-tap", "vendor": "Hak5", "model": "Packet Squirrel MkII", "firmware_version": "2.0", "environment": "lab", "notes": "Inline Ethernet tap — pcap, logging, VPN. SSH from Pi400 over USB-C networking.", "tags": ["hak5", "ethernet", "tap", "pcap"]},
                {"id": "tgt-plunder-bug", "project_id": "proj-iot-inventory", "name": "Hak5 Plunder Bug", "kind": "lan-tap", "vendor": "Hak5", "model": "Plunder Bug", "firmware_version": "N/A", "environment": "lab", "notes": "Passive LAN tap. USB Ethernet on Pi400. tcpdump/Wireshark for capture.", "tags": ["hak5", "ethernet", "passive", "tap"]},
                {"id": "tgt-rubber-ducky", "project_id": "proj-iot-inventory", "name": "Hak5 Rubber Ducky (USB-C)", "kind": "hid-tool", "vendor": "Hak5", "model": "USB Rubber Ducky (2024)", "firmware_version": "latest", "environment": "lab", "notes": "USB keystroke injection. DuckyScript payloads developed on Pi400.", "tags": ["hak5", "usb", "hid", "ducky"]},
                {"id": "tgt-bash-bunny", "project_id": "proj-iot-inventory", "name": "Hak5 Bash Bunny MkII", "kind": "usb-tool", "vendor": "Hak5", "model": "Bash Bunny MkII", "firmware_version": "1.8", "environment": "lab", "notes": "Multi-mode USB tool: HID, Ethernet, storage. Payload dev on Pi400. Loot via mass storage.", "tags": ["hak5", "usb", "bunny"]},
                {"id": "tgt-omg-cable", "project_id": "proj-iot-inventory", "name": "O.MG Cable Elite (2024)", "kind": "usb-implant", "vendor": "O.MG / Hak5", "model": "O.MG Cable Elite USB-C", "firmware_version": "2024", "environment": "lab", "notes": "WiFi-enabled USB cable with covert HID. Managed from Pi400 via WiFi web interface.", "tags": ["omg", "usb", "wifi", "cable"]},
                {"id": "tgt-omg-detector", "project_id": "proj-iot-inventory", "name": "O.MG Malicious Cable Detector", "kind": "usb-defense", "vendor": "O.MG / Hak5", "model": "O.MG Detector (2023)", "firmware_version": "2023", "environment": "field", "notes": "Inline USB-A dongle detecting rogue/implanted cables. LED pass/fail.", "tags": ["omg", "usb", "detector", "defense"]},
                {"id": "tgt-screen-crab", "project_id": "proj-iot-inventory", "name": "Hak5 Screen Crab", "kind": "hdmi-capture", "vendor": "Hak5", "model": "Screen Crab", "firmware_version": "1.0", "environment": "lab", "notes": "HDMI inline capture. Screenshots/video to Pi400 via WiFi or USB.", "tags": ["hak5", "hdmi", "capture"]},
                {"id": "tgt-pikvm", "project_id": "proj-iot-inventory", "name": "PiKVM v4 Plus", "kind": "kvm-remote", "vendor": "PiKVM", "model": "v4 Plus", "firmware_version": "3.291", "environment": "lab", "notes": "Hardware KVM over IP. HDMI capture + USB HID emulation. Browser-accessible from Pi400.", "tags": ["pikvm", "kvm", "hdmi", "remote"]},
                {"id": "tgt-termdriver2", "project_id": "proj-iot-inventory", "name": "TermDriver 2", "kind": "serial-adapter", "vendor": "TermDriver", "model": "TermDriver 2", "firmware_version": "latest", "environment": "lab", "notes": "USB serial adapter with built-in screen. Monitor serial traffic while logging on Pi400.", "tags": ["serial", "usb", "debug"]},
                {"id": "tgt-i2cdriver", "project_id": "proj-iot-inventory", "name": "I2CDriver", "kind": "bus-tool", "vendor": "Excamera Labs", "model": "I2CDriver", "firmware_version": "latest", "environment": "lab", "notes": "USB I2C controller with display. Python API on Pi400 for scripted I2C interaction.", "tags": ["i2c", "bus", "usb"]},
                {"id": "tgt-spidriver", "project_id": "proj-iot-inventory", "name": "SPIDriver", "kind": "bus-tool", "vendor": "Excamera Labs", "model": "SPIDriver", "firmware_version": "latest", "environment": "lab", "notes": "USB SPI controller with display. Python API on Pi400 for flash read/write.", "tags": ["spi", "bus", "usb"]},
                {"id": "tgt-minisniffer", "project_id": "proj-iot-inventory", "name": "BugBlat miniSniffer v2", "kind": "usb-analyzer", "vendor": "BugBlat", "model": "miniSniffer v2", "firmware_version": "latest", "environment": "lab", "notes": "USB protocol analyzer. Inline between Pi400 and target USB device.", "tags": ["usb", "sniffer", "protocol"]},
                {"id": "tgt-dl533n", "project_id": "proj-iot-inventory", "name": "DL533N USB RFID Reader/Writer", "kind": "rfid-rw", "vendor": "D-Logic", "model": "DL533N", "firmware_version": "latest", "environment": "lab", "notes": "USB 13.56MHz RFID reader/writer. LibNFC compatible on Pi400. MIFARE, NTAG, DESFire.", "tags": ["rfid", "nfc", "usb", "reader"]},
                {"id": "tgt-rfid-detector", "project_id": "proj-iot-inventory", "name": "RFID Field Detector Ultra", "kind": "rfid-detect", "vendor": "Generic", "model": "LF/HF/UHF Detector", "firmware_version": "N/A", "environment": "field", "notes": "Passive RFID field detection. LED indicators for 125kHz, 13.56MHz, UHF. Standalone pocket tool.", "tags": ["rfid", "detector", "passive"]},
                {"id": "tgt-esp-rfid", "project_id": "proj-iot-inventory", "name": "ESP RFID Tool", "kind": "rfid-logger", "vendor": "Corey Harding", "model": "ESP RFID Tool", "firmware_version": "latest", "environment": "lab", "notes": "Wiegand RFID sniffer/logger. WiFi web interface accessible from Pi400.", "tags": ["esp", "rfid", "wiegand", "wifi"]},
                {"id": "tgt-pandwarf", "project_id": "proj-iot-inventory", "name": "PandwaRF Rogue Pro", "kind": "rf-capture", "vendor": "PandwaRF", "model": "Rogue Pro", "firmware_version": "latest", "environment": "field", "notes": "Multi-frequency RF remote capture/replay. BLE + USB to Pi400.", "tags": ["pandwarf", "rf", "sub-ghz"]},
                {"id": "tgt-flux-cap", "project_id": "proj-iot-inventory", "name": "Flux Capacitor (Flipper)", "kind": "rf-addon", "vendor": "Rabbit Labs", "model": "Flux Capacitor", "firmware_version": "N/A", "environment": "field", "notes": "CC1101 external radio for Flipper Zero. Extends sub-GHz range.", "tags": ["flipper", "addon", "cc1101"]},
                {"id": "tgt-ir-blaster", "project_id": "proj-iot-inventory", "name": "IR Blaster (Flipper)", "kind": "ir-addon", "vendor": "Rabbit Labs", "model": "IR Blaster", "firmware_version": "N/A", "environment": "field", "notes": "7x IR LED module for Flipper Zero. Extended IR range.", "tags": ["flipper", "addon", "ir"]},
                {"id": "tgt-awok", "project_id": "proj-iot-inventory", "name": "AWOK Dual Touch v3", "kind": "wardriving", "vendor": "AWOK", "model": "Dual Touch v3", "firmware_version": "latest", "environment": "field", "notes": "WiFi wardriving device for Flipper Zero. Touch-screen managed, GPS-logged.", "tags": ["flipper", "addon", "wardriving", "wifi"]},
                {"id": "tgt-alfa", "project_id": "proj-iot-inventory", "name": "Alfa AWUS036ACHM", "kind": "wifi-adapter", "vendor": "Alfa", "model": "AWUS036ACHM", "firmware_version": "mt76 (built-in)", "environment": "lab", "notes": "Dual-band USB WiFi adapter. Native Linux support. Monitor mode + injection. Premium alternative to TP-Link WN722N.", "tags": ["alfa", "wifi", "usb", "monitor-mode"]},
                {"id": "tgt-icopy-xs", "project_id": "proj-iot-inventory", "name": "iCopy-XS", "kind": "rfid-copier", "vendor": "iCopy", "model": "iCopy-XS", "firmware_version": "latest", "environment": "field", "notes": "Standalone RFID copier. EM4100, T5577, MIFARE Classic, NTAG. No Pi400 connection needed.", "tags": ["icopy", "rfid", "standalone"]},
                {"id": "tgt-chameleon-lite", "project_id": "proj-iot-inventory", "name": "Chameleon Lite", "kind": "rfid-emulator", "vendor": "ChameleonTiny", "model": "Chameleon Lite", "firmware_version": "latest", "environment": "field", "notes": "Low-cost HF 13.56MHz RFID emulator. MIFARE + 14A. USB to Pi400.", "tags": ["chameleon", "rfid", "emulator"]},
                {"id": "tgt-skimmerguard", "project_id": "proj-iot-inventory", "name": "SkimmerGuard", "kind": "card-defense", "vendor": "SkimmerGuard", "model": "SkimmerGuard", "firmware_version": "N/A", "environment": "field", "notes": "Portable card skimmer detector for ATMs. Insert-and-detect. Standalone.", "tags": ["skimmer", "detector", "defense"]}
            ],
            "sessions": [
                {"id": "sess-tplink-setup", "project_id": "proj-cyberdeck-build", "target_id": "tgt-tplink", "interface_type": "USB", "connection_method": "USB-A port on Pi400", "adapter": "direct USB", "configuration": "TPLINK_PATCH.sh: installs rtl8188eus, blacklists r8188eu, reboot required", "observations": "After patch: iwconfig shows wlan1 with rtl8188eus. airmon-ng start wlan1 creates wlan1mon. Monitor mode confirmed.", "artifacts": [], "created_at": now},
                {"id": "sess-tft-setup", "project_id": "proj-cyberdeck-build", "target_id": "tgt-dfrobot-tft", "interface_type": "GPIO/SPI", "connection_method": "Pi400 40-pin GPIO header", "adapter": "direct header", "configuration": "LCD_INSTALLER.sh: adds dtoverlay=waveshare35a to /boot/config.txt, configures touch via evdev", "observations": "Display working after reboot. Touch input calibrated. Framebuffer /dev/fb1. X11 on 3.5-inch screen functional.", "artifacts": [], "created_at": now},
                {"id": "sess-flipper-usb", "project_id": "proj-test-env", "target_id": "tgt-flipper-zero", "interface_type": "USB", "connection_method": "USB-C to USB-A cable", "adapter": "direct USB", "configuration": "Shows as USB serial + mass storage. screen /dev/ttyACM0 for CLI. SD card accessible via mass storage mode.", "observations": "FW updated to 0.98.3. Sub-GHz captures downloaded. IR databases synced. SD card contents browsable.", "artifacts": [], "created_at": now},
                {"id": "sess-proxmark-usb", "project_id": "proj-test-env", "target_id": "tgt-proxmark3", "interface_type": "USB", "connection_method": "USB-C to USB-A cable", "adapter": "direct USB", "configuration": "Device at /dev/ttyACM0. Run: pm3 to connect. Iceman client native on Kali ARM.", "observations": "LF and HF antennas functional. Reads EM4100, T5577, MIFARE Classic 1k confirmed. Full Iceman command set available.", "artifacts": [], "created_at": now},
                {"id": "sess-hackrf-sdr", "project_id": "proj-test-env", "target_id": "tgt-hackrf", "interface_type": "USB", "connection_method": "USB micro-B to USB-A cable", "adapter": "direct USB", "configuration": "hackrf_info confirms device. SDR++ or GQRX for waterfall. GNU Radio for DSP flows.", "observations": "HackRF detected. Wideband spectrum capture working. PortaPack H4M standalone with Mayhem firmware for field use without Pi400.", "artifacts": [], "created_at": now},
                {"id": "sess-pineapple-eth", "project_id": "proj-test-env", "target_id": "tgt-pineapple", "interface_type": "Ethernet", "connection_method": "Ethernet cable to Pi400 USB-Ethernet adapter", "adapter": "USB-to-Ethernet dongle", "configuration": "Pi400 eth1=172.16.42.42/24. Dashboard: http://172.16.42.1:1471. SSH: root@172.16.42.1", "observations": "Dashboard accessible. Recon running. Client probes visible. Authorized test network only.", "artifacts": [], "created_at": now}
            ],
            "artifacts": [],
            "reports": [
                {
                    "id": "report-demo-1",
                    "project_id": "proj-cyberdeck-build",
                    "title": "CyberDeck MK-1.0 Build Report",
                    "state": "READY",
                    "summary": "Complete build documentation for the Raspberry Pi 400 CyberDeck MK-1.0. Budget portable deck using Pi400, DFRobot TFT, TP-Link WN722N, Adafruit enclosure, ANKO battery. All driver patches documented. Full IoT peripheral inventory of 30+ devices cataloged with connection sessions.",
                    "findings": [
                        {"title": "TL-WN722N v2/v3 requires out-of-tree driver", "severity": "MEDIUM", "cvss": "N/A", "status": "PATCHED", "description": "Default kernel driver lacks monitor mode. TPLINK_PATCH.sh automates David Bombal method — aircrack-ng rtl8188eus driver, blacklists r8188eu."},
                        {"title": "DFRobot TFT needs dtoverlay in /boot/config.txt", "severity": "LOW", "cvss": "N/A", "status": "DOCUMENTED", "description": "waveshare35a dtoverlay required. LCD_INSTALLER.sh automates configuration and touch calibration."},
                        {"title": "Pi400 power draw under full peripheral load", "severity": "INFO", "cvss": "N/A", "status": "NOTED", "description": "Pi400 + TFT + WiFi + USB peripherals can exceed 2A. ANKO 5V/2A tested stable. Higher capacity recommended for extended field sessions."},
                        {"title": "Kali ARM 64-bit is the recommended OS", "severity": "INFO", "cvss": "N/A", "status": "NOTED", "description": "Kali 2023.1+ ARM 64-bit provides pre-installed tooling: aircrack-ng, nmap, wireshark, proxmark client, hashcat, bettercap, tcpdump."}
                    ],
                    "generated_at": now
                }
            ],
            "tasks": [],
            "settings": {"ai": {"backend": "none"}}
        }
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(state, f, default=str, indent=2)
            html = render_report_html(state['reports'][0], state)
            with open(os.path.join(REPORT_DIR, 'report-demo-1.html'), 'w') as rf:
                rf.write(html)
            print('Seeded CyberDeck MK-1.0 data to', DATA_FILE)
        except Exception as e:
            print('Failed to write initial state', e)
