import json
from datetime import datetime

seed = {
    "projects": [
        {
            "id": "proj-cyberdeck-build",
            "name": "CYBERDECK-MK1-BUILD",
            "summary": "Pi400 CyberDeck MK-1.0 build documentation and IoT peripheral catalog",
            "classification": "INTERNAL",
            "authorization_scope": "Personal build — owned hardware only",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "proj-iot-inventory",
            "name": "IOT-DEVICE-INVENTORY",
            "summary": "Catalog of CyberDeck peripherals and IoT tools with firmware tracking",
            "classification": "INTERNAL",
            "authorization_scope": "Owned equipment inventory — documentation only",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ],
    "targets": [
        {
            "id": "tgt-rpi400",
            "project_id": "proj-cyberdeck-build",
            "name": "Raspberry Pi 400",
            "kind": "sbc",
            "vendor": "Raspberry Pi Foundation",
            "model": "Pi 400 (4GB)",
            "firmware_version": "Kali ARM 2023.1 64-bit",
            "environment": "cyberdeck",
            "notes": "Keyboard-integrated SBC — the compute heart of the CyberDeck",
            "tags": ["pi400", "cyberdeck", "host", "kali"]
        }
    ],
    "sessions": [
        {
            "id": "sess-tplink-setup",
            "project_id": "proj-cyberdeck-build",
            "target_id": "tgt-rpi400",
            "interface_type": "USB",
            "connection_method": "USB-A port on Pi400",
            "adapter": "direct USB",
            "configuration": "TPLINK_PATCH.sh: installs rtl8188eus, blacklists r8188eu",
            "observations": "Monitor mode confirmed after reboot",
            "artifacts": [],
            "created_at": datetime.utcnow().isoformat()
        }
    ],
    "artifacts": [],
    "reports": [
        {
            "id": "report-demo-1",
            "project_id": "proj-cyberdeck-build",
            "title": "CyberDeck MK-1.0 Build Report",
            "state": "READY",
            "summary": "Complete build documentation for Pi400 CyberDeck MK-1.0",
            "findings": [],
            "generated_at": datetime.utcnow().isoformat()
        }
    ],
    "tasks": [],
    "settings": {"ai": {"backend": "none"}}
}

if __name__ == "__main__":
    import os
    data_dir = os.environ.get("DATA_DIR", "/data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "state.json"), "w") as f:
        json.dump(seed, f, indent=2)
    print(f"Seeded {data_dir}/state.json")
