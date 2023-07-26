import pytest
import os
import tempfile
import hashlib
import json

# Use temp directory for test data so tests are isolated
_test_data_dir = tempfile.mkdtemp(prefix="cyberdeck_test_")
os.environ["DATA_DIR"] = _test_data_dir
os.environ["JWT_SECRET"] = "test-secret"
os.makedirs(os.path.join(_test_data_dir, "reports"), exist_ok=True)
os.makedirs(os.path.join(_test_data_dir, "uploads"), exist_ok=True)

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── helpers ──
def _login():
    """Login and return auth header dict."""
    r = client.post("/auth/login", json={"username": "admin", "password": "cyberdeck"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ONLINE"

# ── auth ──
def test_login_success():
    r = client.post("/auth/login", json={"username": "admin", "password": "cyberdeck"})
    assert r.status_code == 200
    assert "token" in r.json()

def test_login_failure():
    r = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert r.status_code == 401

def test_get_projects():
    response = client.get("/projects")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_project():
    response = client.post("/projects", json={
        "name": "TEST-PROJECT",
        "summary": "Test project for API testing",
        "classification": "INTERNAL",
        "authorization_scope": "Test scope"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "TEST-PROJECT"
    assert "id" in data

def test_get_project_not_found():
    response = client.get("/projects/nonexistent-id")
    assert response.status_code == 404

def test_create_target():
    # First create a project
    proj_response = client.post("/projects", json={
        "name": "TARGET-TEST-PROJECT",
        "summary": "Project for target testing"
    })
    project_id = proj_response.json()["id"]

    # Create a target
    response = client.post(f"/projects/{project_id}/targets", json={
        "name": "Test Device",
        "kind": "router",
        "vendor": "TestVendor",
        "model": "TestModel"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Device"
    assert data["project_id"] == project_id

def test_create_session():
    # First create a project
    proj_response = client.post("/projects", json={
        "name": "SESSION-TEST-PROJECT",
        "summary": "Project for session testing"
    })
    project_id = proj_response.json()["id"]

    # Create a session
    response = client.post(f"/projects/{project_id}/sessions", json={
        "interface_type": "USB",
        "connection_method": "USB-A port on Pi400",
        "adapter": "direct USB",
        "observations": "Test session"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["interface_type"] == "USB"
    assert data["project_id"] == project_id

def test_get_reports():
    response = client.get("/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_generate_report():
    # First create a project
    proj_response = client.post("/projects", json={
        "name": "REPORT-TEST-PROJECT",
        "summary": "Project for report testing"
    })
    project_id = proj_response.json()["id"]

    # Generate a report
    response = client.post("/reports/generate", json={
        "project_id": project_id,
        "title": "Test Report"
    })
    assert response.status_code == 200
    data = response.json()
    assert "id" in data

def test_get_ai_settings():
    response = client.get("/settings/ai")
    assert response.status_code == 200
    data = response.json()
    assert "backend" in data

def test_set_ai_settings():
    response = client.post("/settings/ai", json={
        "backend": "ollama",
        "config": {"endpoint": "http://localhost:11434"}
    })
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "ollama"

def test_ai_summarize_none_backend():
    """AI summarize works even with no backend configured."""
    # Reset to none
    client.post("/settings/ai", json={"backend": "none", "config": {}})
    response = client.post("/ai/summarize", json={"text": "This is a test of the UART session on the ACME router."})
    assert response.status_code == 200
    assert "result" in response.json()

def test_ai_draft_finding():
    response = client.post("/ai/draft-finding", json={"observations": "Boot logs reveal default credentials on UART console."})
    assert response.status_code == 200
    assert "result" in response.json()

def test_end_to_end_happy_path():
    """Full end-to-end: create project -> add target -> add session -> generate report -> view report."""
    # 1. Create project
    proj = client.post("/projects", json={
        "name": "E2E-TEST-PROJECT",
        "summary": "End-to-end test project",
        "classification": "INTERNAL",
        "authorization_scope": "Automated testing"
    })
    assert proj.status_code == 200
    project_id = proj.json()["id"]

    # 2. Add target
    tgt = client.post(f"/projects/{project_id}/targets", json={
        "name": "E2E Test Router",
        "kind": "router",
        "vendor": "TestCorp",
        "model": "RT-100",
        "firmware_version": "2.0.1"
    })
    assert tgt.status_code == 200

    # 3. Add hardware session
    sess = client.post(f"/projects/{project_id}/sessions", json={
        "target_id": tgt.json()["id"],
        "interface_type": "USB",
        "connection_method": "USB-A cable to Pi400",
        "adapter": "direct USB",
        "configuration": "screen /dev/ttyACM0 115200",
        "observations": "Device connected, firmware version confirmed"
    })
    assert sess.status_code == 200

    # 4. Generate report
    rpt = client.post("/reports/generate", json={
        "project_id": project_id,
        "title": "E2E Test Report"
    })
    assert rpt.status_code == 200
    report_id = rpt.json()["id"]

    # 5. View printable report
    view = client.get(f"/reports/{report_id}/view")
    assert view.status_code == 200
    assert "E2E Test Report" in view.text
    assert "PRINT / EXPORT TO PDF" in view.text

# ── file upload ──
def test_upload_and_download():
    proj = client.post("/projects", json={"name": "UPLOAD-TEST"})
    pid = proj.json()["id"]
    content = b"fake firmware image 0xFF 0x00"
    r = client.post("/upload", data={
        "project_id": pid,
        "kind": "firmware",
        "notes": "test upload"
    }, files={"file": ("firmware.bin", content, "application/octet-stream")})
    assert r.status_code == 200
    art = r.json()
    assert art["sha256"] == hashlib.sha256(content).hexdigest()
    assert art["filename"] == "firmware.bin"
    # download
    dl = client.get(f"/uploads/{art['id']}/firmware.bin")
    assert dl.status_code == 200
    assert dl.content == content

def test_list_artifacts():
    r = client.get("/artifacts")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

# ── CSV import/export ──
def test_csv_export():
    r = client.get("/projects/proj-cyberdeck-build/targets/export.csv")
    assert r.status_code == 200
    assert "name" in r.text
    assert "Raspberry Pi 400" in r.text

def test_csv_import():
    csv_content = "name,kind,vendor,model,firmware_version,environment,notes,tags\nCSV-Device,sensor,CSVCorp,S-100,3.0,lab,imported,iot;csv\n"
    proj = client.post("/projects", json={"name": "CSV-TEST"})
    pid = proj.json()["id"]
    r = client.post(
        f"/projects/{pid}/targets/import",
        files={"file": ("import.csv", csv_content.encode(), "text/csv")}
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 1
    assert r.json()["targets"][0]["name"] == "CSV-Device"
    assert "iot" in r.json()["targets"][0]["tags"]

# ── additional AI endpoints ──
def test_ai_suggest_names():
    client.post("/settings/ai", json={"backend": "none", "config": {}})
    r = client.post("/ai/suggest-names", json={"context": "unknown router device"})
    assert r.status_code == 200
    assert isinstance(r.json()["result"], list)

def test_ai_cluster():
    r = client.post("/ai/cluster", json={"items": ["photo1.jpg", "uart_log.txt", "firmware.bin"]})
    assert r.status_code == 200
    assert "result" in r.json()

# ── report with severity matrix ──
def test_seeded_report_has_severity_matrix():
    r = client.get("/reports/report-demo-1/view")
    assert r.status_code == 200
    assert "CRITICAL" in r.text
    assert "severity-high" in r.text
    assert "Severity Matrix" in r.text
