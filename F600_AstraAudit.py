#!/usr/bin/env python3
"""
FLLC CYBERDECK MK-1.0 — Raspberry Pi 400 Network Audit & IoT Ops Console

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

DESCRIPTION : One-stop CLI ops console for the Pi400 CyberDeck.
              Wraps network auditing tools (bettercap, tshark, tcpdump,
              nmap, hashcat) AND cyberdeck IoT peripherals (Flipper Zero,
              Proxmark3, HackRF/SDR, O.MG cable, Shark Jack, GPIO/I2C/SPI).
              Designed for a 3.5" DFRobot TFT — menus are compact by design.
VERSION     : 6.0.0
DATE        : 2026-04-20
PLATFORM    : Raspberry Pi 400 / Kali ARM 64-bit
PROTOTYPE   : unsanitised input, global state, not thread-safe — lab use only.
"""

import os
import json
import shutil
import multiprocessing
import subprocess
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
CYBERDECK_HOME = Path.home() / "CYBERDECK"
SESSION_LOG = CYBERDECK_HOME / "sessions"
CAPTURES_DIR = CYBERDECK_HOME / "captures"
REPORTS_DIR = CYBERDECK_HOME / "reports"
LOOT_DIR = CYBERDECK_HOME / "loot"

CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
RED = "\033[31m"
MAGENTA = "\033[35m"
RESET = "\033[0m"
BOLD = "\033[1m"

BANNER = rf"""
{CYAN}{BOLD}
  ╔═══════════════════════════════════════════════════════════╗
  ║  FLLC CYBERDECK MK-1.0  ·  Raspberry Pi 400 Ops Console   ║
  ║  Network Audit  ·  IoT Peripherals  ·  Hardware Sessions  ║
  ╚═══════════════════════════════════════════════════════════╝
{RESET}"""

# ---------------------------------------------------------------------------
# Requirements (external binaries)
# ---------------------------------------------------------------------------
REQUIREMENTS = {
    "bettercap": "https://github.com/bettercap/bettercap",
    "tshark": "https://www.wireshark.org/",
    "hashcat": "https://hashcat.net/hashcat/",
    "nmap": "https://nmap.org/",
    "tcpdump": "https://www.tcpdump.org/",
    "proxmark3": "https://github.com/RfidResearchGroup/proxmark3",
    "hackrf_info": "https://github.com/greatscottgadgets/hackrf",
    "flipper": "https://docs.flipper.net/",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clear_console():
    os.system('clear')


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dirs():
    for d in [SESSION_LOG, CAPTURES_DIR, REPORTS_DIR, LOOT_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def check_tool(name):
    return shutil.which(name) is not None


def run_cmd(cmd, shell=False, capture=False):
    display = cmd if isinstance(cmd, str) else ' '.join(cmd)
    print(f"{CYAN}» {display}{RESET}")
    if capture:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.stdout
    subprocess.run(cmd, shell=shell)


def log_session(tool_name, details):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "details": details,
    }
    logfile = SESSION_LOG / f"{tool_name}_{timestamp()}.json"
    logfile.write_text(json.dumps(entry, indent=2))
    print(f"{GREEN}Session logged → {logfile}{RESET}")


def display_ip_settings():
    try:
        ip_output = subprocess.check_output("ip -br a", shell=True).decode()
        print(f"{CYAN}Interfaces:{RESET}\n{YELLOW}{ip_output}{RESET}")
    except Exception:
        print(f"{RED}Could not read network interfaces.{RESET}")


def display_usb_devices():
    try:
        usb_output = subprocess.check_output("lsusb", shell=True).decode()
        print(f"{CYAN}USB Devices:{RESET}\n{YELLOW}{usb_output}{RESET}")
    except Exception:
        print(f"{RED}lsusb not available.{RESET}")


def display_gpio_status():
    try:
        gpio_output = subprocess.check_output("pinctrl", shell=True).decode()
        lines = gpio_output.strip().split('\n')[:10]
        print(f"{CYAN}GPIO (first 10):{RESET}\n{YELLOW}" + '\n'.join(lines) + f"{RESET}")
    except Exception:
        print(f"{CYAN}GPIO: pinctrl not available (install raspi-gpio or pinctrl){RESET}")


# ===================================================================
# NETWORK AUDITING TOOLS
# ===================================================================

class Bettercap:
    def __init__(self):
        self.interface = input('Interface (e.g. wlan1): ')
        self.targets = input('Targets (leave empty for subnet): ')
        self.sniffer = input('Start sniffer? (y/n): ').lower() == 'y'
        self.proxy = input('Start proxy? (y/n): ').lower() == 'y'
        self.redirect = input('HTTP redirect address (empty=none): ')
        self.web_ui = input('Start web UI? (y/n): ').lower() == 'y'
        if self.web_ui:
            self.web_ui_iface = input('Web UI interface: ')

    @staticmethod
    def _run(cmd):
        subprocess.run(cmd, shell=True)

    def execute(self):
        bettercap_cmd = f'sudo bettercap -iface {self.interface}'
        if self.targets:
            bettercap_cmd += f' -eval "set arp.spoof.targets {self.targets}"'
        details = {"interface": self.interface, "targets": self.targets,
                   "sniffer": self.sniffer, "proxy": self.proxy}

        proc = multiprocessing.Process(target=self._run, args=(bettercap_cmd,))
        proc.start()

        if self.web_ui:
            ui_cmd = f'sudo bettercap -iface {self.web_ui_iface} -caplet http-ui'
            ui_proc = multiprocessing.Process(target=self._run, args=(ui_cmd,))
            ui_proc.start()

        proc.join()
        if self.web_ui:
            ui_proc.join()

        log_session("bettercap", details)


class Hashcat:
    def __init__(self):
        self.hashfile = input('Hash file path: ')
        self.wordlist = input('Wordlist path: ')
        self.hash_type = input('Hash type (default 0): ') or '0'
        self.attack_mode = input('Attack mode (default 0): ') or '0'
        self.rules_file = input('Rules file (empty=none): ')
        self.output_file = input('Output file (empty=none): ')

    def execute(self):
        command = ['hashcat', '-m', self.hash_type, '-a', self.attack_mode,
                   self.hashfile, self.wordlist]
        if self.rules_file:
            command.extend(['-r', self.rules_file])
        if self.output_file:
            command.extend(['-o', self.output_file])
        run_cmd(command)
        log_session("hashcat", {"hash_type": self.hash_type, "attack_mode": self.attack_mode})


class Tshark:
    def __init__(self):
        self.interface = input('Interface: ')
        self.write = input('Output file (empty=auto): ')
        if not self.write:
            self.write = str(CAPTURES_DIR / f"tshark_{timestamp()}.pcapng")
        self.capture_filter = input('Capture filter (empty=none): ')
        self.display_filter = input('Display filter (empty=none): ')

    def execute(self):
        command = ['tshark']
        if self.interface:
            command.extend(['-i', self.interface])
        if self.write:
            command.extend(['-w', self.write])
        if self.capture_filter:
            command.extend(['-f', self.capture_filter])
        if self.display_filter:
            command.extend(['-Y', self.display_filter])
        run_cmd(command)
        log_session("tshark", {"interface": self.interface, "file": self.write})


class Tcpdump:
    def __init__(self):
        self.interface = input('Interface: ')
        self.write = input('Output file (empty=auto): ')
        if not self.write:
            self.write = str(CAPTURES_DIR / f"tcpdump_{timestamp()}.pcap")
        self.capture_filter = input('Capture filter (empty=none): ')

    def execute(self):
        command = ['sudo', 'tcpdump']
        if self.interface:
            command.extend(['-i', self.interface])
        if self.write:
            command.extend(['-w', self.write])
        if self.capture_filter:
            command.append(self.capture_filter)
        run_cmd(command)
        log_session("tcpdump", {"interface": self.interface, "file": self.write})


class Nmap:
    def __init__(self):
        self.target = input('Target: ')
        self.scan_type = input('Scan type (default -sS): ') or '-sS'
        self.port_range = input('Port range (empty=default): ')
        self.output_file = input('Output file (empty=auto): ')
        if not self.output_file:
            self.output_file = str(CAPTURES_DIR / f"nmap_{timestamp()}.txt")

    def execute(self):
        command = ['sudo', 'nmap', self.scan_type]
        if self.port_range:
            command.extend(['-p', self.port_range])
        command.append(self.target)
        command.extend(['-oN', self.output_file])
        run_cmd(command)
        log_session("nmap", {"target": self.target, "scan": self.scan_type})


# ===================================================================
# CYBER ANALYST RECON & ANALYSIS TOOLS
# ===================================================================

class WirelessRecon:
    """Aircrack-ng suite — monitor mode, airodump, deauth for WPA handshake capture."""
    def __init__(self):
        self.interface = input('WiFi interface (e.g. wlan1): ') or 'wlan1'
        self.action = input('Action [monitor_on/monitor_off/airodump/deauth/crack]: ') or 'airodump'

    def execute(self):
        if self.action == 'monitor_on':
            run_cmd(f'sudo airmon-ng start {self.interface}', shell=True)
        elif self.action == 'monitor_off':
            run_cmd(f'sudo airmon-ng stop {self.interface}mon', shell=True)
        elif self.action == 'airodump':
            outfile = str(CAPTURES_DIR / f"airodump_{timestamp()}")
            channel = input('Channel (empty=all): ')
            cmd = f'sudo airodump-ng {self.interface}mon -w {outfile}'
            if channel:
                cmd += f' -c {channel}'
            run_cmd(cmd, shell=True)
        elif self.action == 'deauth':
            bssid = input('Target BSSID: ')
            count = input('Deauth packets (default 10): ') or '10'
            run_cmd(f'sudo aireplay-ng --deauth {count} -a {bssid} {self.interface}mon', shell=True)
        elif self.action == 'crack':
            capfile = input('Capture file (.cap): ')
            wordlist = input('Wordlist (default /usr/share/wordlists/rockyou.txt): ') or '/usr/share/wordlists/rockyou.txt'
            run_cmd(f'sudo aircrack-ng {capfile} -w {wordlist}', shell=True)
        log_session("wireless_recon", {"interface": self.interface, "action": self.action})


class ARPDiscover:
    """Quick ARP-based host discovery on local subnet."""
    def __init__(self):
        self.interface = input('Interface (e.g. eth0): ') or 'eth0'
        self.subnet = input('Subnet (e.g. 192.168.1.0/24, empty=auto): ')

    def execute(self):
        if not self.subnet:
            out = run_cmd(f"ip -4 addr show {self.interface} | grep inet | awk '{{print $2}}'", shell=True, capture=True)
            self.subnet = (out or '').strip() if out else '192.168.1.0/24'
        outfile = LOOT_DIR / f"arp_scan_{timestamp()}.txt"
        run_cmd(f'sudo arp-scan --interface={self.interface} {self.subnet} | tee {outfile}', shell=True)
        log_session("arp_discover", {"interface": self.interface, "subnet": self.subnet})


class ServiceEnum:
    """Nmap service version + script scan for deeper target profiling."""
    def __init__(self):
        self.target = input('Target (IP or range): ')
        self.intensity = input('Intensity [quick/full/vuln]: ') or 'quick'

    def execute(self):
        outfile = str(REPORTS_DIR / f"service_enum_{timestamp()}")
        if self.intensity == 'quick':
            cmd = f'sudo nmap -sV -sC -T4 {self.target} -oA {outfile}'
        elif self.intensity == 'full':
            cmd = f'sudo nmap -sV -sC -p- -T4 {self.target} -oA {outfile}'
        elif self.intensity == 'vuln':
            cmd = f'sudo nmap -sV --script=vuln {self.target} -oA {outfile}'
        else:
            cmd = f'sudo nmap -sV {self.target} -oA {outfile}'
        run_cmd(cmd, shell=True)
        print(f"{GREEN}Results saved → {outfile}.*{RESET}")
        log_session("service_enum", {"target": self.target, "intensity": self.intensity})


class PcapAnalyze:
    """Offline PCAP analysis — protocol hierarchy, HTTP extraction, DNS queries."""
    def __init__(self):
        self.pcap = input('PCAP file path: ')
        self.action = input('Action [hierarchy/http/dns/credentials/conversations]: ') or 'hierarchy'

    def execute(self):
        if self.action == 'hierarchy':
            run_cmd(f'tshark -r {self.pcap} -q -z io,phs', shell=True)
        elif self.action == 'http':
            run_cmd(f'tshark -r {self.pcap} -Y "http.request" -T fields -e http.host -e http.request.uri', shell=True)
        elif self.action == 'dns':
            run_cmd(f'tshark -r {self.pcap} -Y "dns.qry.name" -T fields -e dns.qry.name | sort -u', shell=True)
        elif self.action == 'credentials':
            run_cmd(f'tshark -r {self.pcap} -Y "http.authbasic or ftp.request.command==PASS or pop.request.command==PASS" -T fields -e ip.src -e http.authbasic -e ftp.request.arg -e pop.request.arg', shell=True)
        elif self.action == 'conversations':
            run_cmd(f'tshark -r {self.pcap} -q -z conv,tcp', shell=True)
        log_session("pcap_analyze", {"pcap": self.pcap, "action": self.action})


class DNSRecon:
    """DNS enumeration — subdomain brute, zone transfer, reverse lookup."""
    def __init__(self):
        self.domain = input('Target domain: ')
        self.action = input('Action [lookup/reverse/zonetransfer/brute]: ') or 'lookup'

    def execute(self):
        if self.action == 'lookup':
            run_cmd(f'dig {self.domain} ANY +noall +answer', shell=True)
            run_cmd(f'dig {self.domain} MX +short', shell=True)
            run_cmd(f'dig {self.domain} NS +short', shell=True)
        elif self.action == 'reverse':
            ip = input('IP address: ')
            run_cmd(f'dig -x {ip} +short', shell=True)
        elif self.action == 'zonetransfer':
            ns = input('Nameserver: ')
            run_cmd(f'dig @{ns} {self.domain} AXFR', shell=True)
        elif self.action == 'brute':
            wordlist = input('Subdomain wordlist (default /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt): ') or '/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt'
            run_cmd(f'for sub in $(cat {wordlist}); do dig +short $sub.{self.domain} | grep -v "^$" && echo "$sub.{self.domain}"; done', shell=True)
        log_session("dns_recon", {"domain": self.domain, "action": self.action})


class SessionReview:
    """Browse and search previous session logs."""
    def execute(self):
        logs = sorted(SESSION_LOG.glob("*.json"), reverse=True)
        if not logs:
            print(f"{YELLOW}No session logs found.{RESET}")
            return
        print(f"{BOLD}{CYAN}═══ Recent Sessions (last 20) ═══{RESET}")
        for i, log in enumerate(logs[:20]):
            data = json.loads(log.read_text())
            ts = data.get('timestamp', '?')[:19]
            tool = data.get('tool', '?')
            print(f"  {CYAN}{i+1:3d}{RESET}  {ts}  {GREEN}{tool:18s}{RESET}  {log.name}")
        choice = input(f"\n{CYAN}View log # (empty=skip): {RESET}").strip()
        if choice.isdigit() and 0 < int(choice) <= len(logs[:20]):
            content = logs[int(choice)-1].read_text()
            print(f"{YELLOW}{content}{RESET}")
        log_session("session_review", {"action": "browse"})


class ToolCheck:
    """Verify all required tools are installed on this CyberDeck."""
    def execute(self):
        all_tools = {
            **REQUIREMENTS,
            "airmon-ng": "aircrack-ng suite",
            "airodump-ng": "aircrack-ng suite",
            "arp-scan": "https://github.com/royhills/arp-scan",
            "dig": "dnsutils / bind-utils",
            "minicom": "serial terminal",
            "i2cdetect": "i2c-tools",
            "curl": "https://curl.se/",
        }
        print(f"{BOLD}{CYAN}═══ Tool Dependency Check ═══{RESET}\n")
        missing = []
        for name, url in sorted(all_tools.items()):
            found = shutil.which(name)
            status = f"{GREEN}✓{RESET}" if found else f"{RED}✗{RESET}"
            print(f"  {status}  {name:18s}  {url}")
            if not found:
                missing.append(name)
        print(f"\n  {len(all_tools) - len(missing)}/{len(all_tools)} tools available")
        if missing:
            print(f"  {RED}Missing: {', '.join(missing)}{RESET}")
        log_session("tool_check", {"missing": missing})


# ===================================================================
# CYBERDECK IoT PERIPHERAL TOOLS
# ===================================================================

class FlipperZero:
    """Flipper Zero serial CLI bridge via /dev/ttyACM*."""
    def __init__(self):
        self.port = input('Flipper serial port (default /dev/ttyACM0): ') or '/dev/ttyACM0'
        self.action = input('Action [info/subghz_rx/rfid_read/ir_rx/gpio_status]: ') or 'info'

    def execute(self):
        cmd_map = {
            "info": "device_info",
            "subghz_rx": "subghz rx",
            "rfid_read": "rfid read",
            "ir_rx": "ir rx",
            "gpio_status": "gpio mode",
        }
        flipper_cmd = cmd_map.get(self.action, "device_info")
        print(f"{CYAN}Sending to Flipper → {flipper_cmd}{RESET}")
        try:
            run_cmd(f'echo "{flipper_cmd}" > {self.port}', shell=True)
            run_cmd(f'cat {self.port}', shell=True)
        except Exception as e:
            print(f"{RED}Flipper error: {e}{RESET}")
        log_session("flipper_zero", {"port": self.port, "action": self.action})


class Proxmark3:
    """Proxmark3 RDV4 wrapper."""
    def __init__(self):
        self.action = input('Action [lf_search/hf_search/lf_read/hf_read/flash]: ') or 'hf_search'

    def execute(self):
        cmd_map = {
            "lf_search": "proxmark3 /dev/ttyACM0 -c 'lf search'",
            "hf_search": "proxmark3 /dev/ttyACM0 -c 'hf search'",
            "lf_read": "proxmark3 /dev/ttyACM0 -c 'lf read'",
            "hf_read": "proxmark3 /dev/ttyACM0 -c 'hf 14a reader'",
            "flash": "proxmark3 /dev/ttyACM0 --flash --unlock-bootloader --image /usr/share/proxmark3/firmware/fullimage.elf",
        }
        cmd = cmd_map.get(self.action, cmd_map["hf_search"])
        run_cmd(cmd, shell=True)
        log_session("proxmark3", {"action": self.action})


class HackRF:
    """HackRF One / SDR operations."""
    def __init__(self):
        self.action = input('Action [info/rx/tx/sweep]: ') or 'info'
        if self.action == 'rx':
            self.freq = input('Frequency in Hz (e.g. 433920000): ')
            self.outfile = input('Output file (empty=auto): ') or str(CAPTURES_DIR / f"hackrf_{timestamp()}.raw")
        elif self.action == 'sweep':
            self.freq_start = input('Start freq MHz (default 2400): ') or '2400'
            self.freq_end = input('End freq MHz (default 2500): ') or '2500'

    def execute(self):
        if self.action == 'info':
            run_cmd(['hackrf_info'])
        elif self.action == 'rx':
            run_cmd(['hackrf_transfer', '-r', self.outfile, '-f', self.freq, '-s', '2000000'])
        elif self.action == 'sweep':
            run_cmd(f'hackrf_sweep -f {self.freq_start}:{self.freq_end}', shell=True)
        else:
            print(f"{RED}Unknown HackRF action.{RESET}")
        log_session("hackrf", {"action": self.action})


class OMGCable:
    """O.MG Cable — connect via WiFi AP and push payloads."""
    def __init__(self):
        self.ip = input('O.MG Cable IP (default 192.168.4.1): ') or '192.168.4.1'
        self.action = input('Action [status/payload/exfil]: ') or 'status'

    def execute(self):
        if self.action == 'status':
            run_cmd(f'curl -s http://{self.ip}/status', shell=True)
        elif self.action == 'payload':
            payload_file = input('Payload script path: ')
            run_cmd(f'curl -s -X POST http://{self.ip}/payload -d @{payload_file}', shell=True)
        elif self.action == 'exfil':
            run_cmd(f'curl -s http://{self.ip}/exfiltrate', shell=True)
        log_session("omg_cable", {"ip": self.ip, "action": self.action})


class SharkJack:
    """Hak5 Shark Jack — LAN tap / network audit keyring device."""
    def __init__(self):
        self.action = input('Action [scan/payload/loot]: ') or 'scan'

    def execute(self):
        if self.action == 'scan':
            print(f"{CYAN}Shark Jack auto-scans on plug-in. Check /root/loot/ on device.{RESET}")
            run_cmd("ssh root@172.16.24.1 'cat /root/loot/nmap_*.txt' 2>/dev/null", shell=True)
        elif self.action == 'loot':
            run_cmd("scp root@172.16.24.1:/root/loot/* ./captures/sharkjack/", shell=True)
        log_session("sharkjack", {"action": self.action})


class GPIOTools:
    """Pi400 GPIO header — I2C scan, SPI probe, UART minicom."""
    def __init__(self):
        self.action = input('Action [i2c_scan/spi_probe/uart_connect/gpio_readall]: ') or 'i2c_scan'

    def execute(self):
        if self.action == 'i2c_scan':
            bus = input('I2C bus (default 1): ') or '1'
            run_cmd(f'sudo i2cdetect -y {bus}', shell=True)
        elif self.action == 'spi_probe':
            print(f"{CYAN}SPI devices:{RESET}")
            run_cmd('ls -la /dev/spidev*', shell=True)
        elif self.action == 'uart_connect':
            port = input('Serial port (default /dev/ttyS0): ') or '/dev/ttyS0'
            baud = input('Baud rate (default 115200): ') or '115200'
            run_cmd(f'sudo minicom -D {port} -b {baud}', shell=True)
        elif self.action == 'gpio_readall':
            run_cmd('pinctrl', shell=True)
        log_session("gpio", {"action": self.action})


class WiFiPineapple:
    """Hak5 WiFi Pineapple — connect to management API."""
    def __init__(self):
        self.ip = input('Pineapple IP (default 172.16.42.1): ') or '172.16.42.1'
        self.action = input('Action [status/recon/clients]: ') or 'status'

    def execute(self):
        if self.action == 'status':
            run_cmd(f'curl -sk https://{self.ip}/api/status', shell=True)
        elif self.action == 'recon':
            run_cmd(f'curl -sk https://{self.ip}/api/recon/start -X POST', shell=True)
        elif self.action == 'clients':
            run_cmd(f'curl -sk https://{self.ip}/api/clients', shell=True)
        log_session("wifi_pineapple", {"ip": self.ip, "action": self.action})


class SystemInfo:
    """Pi400 system diagnostics."""
    def execute(self):
        print(f"\n{BOLD}{CYAN}═══ Pi400 CyberDeck System Info ═══{RESET}\n")
        run_cmd("cat /proc/device-tree/model 2>/dev/null || echo 'Not a Pi'", shell=True)
        run_cmd("vcgencmd measure_temp 2>/dev/null || echo 'vcgencmd N/A'", shell=True)
        run_cmd("free -h | head -2", shell=True)
        run_cmd("df -h / | tail -1", shell=True)
        display_ip_settings()
        display_usb_devices()
        display_gpio_status()
        log_session("sysinfo", {"action": "display"})


# ===================================================================
# MAIN MENU
# ===================================================================

TOOLS = {
    # --- Network Auditing ---
    "bettercap": ("Bettercap — MITM & network recon", Bettercap),
    "tshark": ("TShark — packet capture & analysis", Tshark),
    "tcpdump": ("Tcpdump — lightweight packet capture", Tcpdump),
    "nmap": ("Nmap — port & service scanner", Nmap),
    "hashcat": ("Hashcat — hash cracking", Hashcat),
    # --- Analyst Recon ---
    "wireless": ("Wireless recon — aircrack-ng suite", WirelessRecon),
    "arpscan": ("ARP discovery — fast LAN host finder", ARPDiscover),
    "services": ("Service enum — version & vuln scripts", ServiceEnum),
    "pcap": ("PCAP analysis — offline packet inspection", PcapAnalyze),
    "dns": ("DNS recon — lookup, zone xfer, brute", DNSRecon),
    # --- CyberDeck IoT Peripherals ---
    "flipper": ("Flipper Zero — sub-GHz / RFID / IR / GPIO", FlipperZero),
    "proxmark": ("Proxmark3 RDV4 — RFID read/write/emulate", Proxmark3),
    "hackrf": ("HackRF / SDR — RF capture & sweep", HackRF),
    "omg": ("O.MG Cable — USB implant interface", OMGCable),
    "sharkjack": ("Shark Jack — LAN tap & audit", SharkJack),
    "pineapple": ("WiFi Pineapple — rogue AP & recon", WiFiPineapple),
    # --- Pi400 Hardware & Ops ---
    "gpio": ("GPIO / I2C / SPI / UART tools", GPIOTools),
    "sysinfo": ("Pi400 system diagnostics", SystemInfo),
    "sessions": ("Browse session logs", SessionReview),
    "toolcheck": ("Verify installed tools", ToolCheck),
}


class Main:
    def __init__(self):
        ensure_dirs()
        self.execute()

    def show_menu(self):
        print(BANNER)
        display_ip_settings()
        sections = [
            ("NETWORK CAPTURE", ["bettercap", "tshark", "tcpdump", "nmap", "hashcat"], GREEN),
            ("ANALYST RECON", ["wireless", "arpscan", "services", "pcap", "dns"], f"\033[38;5;208m"),
            ("CYBERDECK PERIPHERALS", ["flipper", "proxmark", "hackrf", "omg", "sharkjack", "pineapple"], MAGENTA),
            ("PI400 OPS", ["gpio", "sysinfo", "sessions", "toolcheck"], YELLOW),
        ]
        for i, (title, keys, color) in enumerate(sections):
            connector = "┌" if i == 0 else "├"
            print(f"{BOLD}{CYAN}  {connector}── {title} {'─' * (38 - len(title))}┤{RESET}")
            for key in keys:
                label = TOOLS[key][0]
                print(f"  {CYAN}│{RESET}  {color}{key:12s}{RESET} {label}")
        print(f"  {CYAN}│{RESET}  {RED}{'exit':12s}{RESET} Quit CyberDeck console")
        print(f"{BOLD}{CYAN}  └─────────────────────────────────────────┘{RESET}")

    def get_tool(self):
        while True:
            choice = input(f"\n{CYAN}cyberdeck>{RESET} ").strip().lower()
            if choice == 'exit':
                return 'exit'
            if choice in TOOLS:
                return choice
            print(f"{RED}Unknown tool '{choice}'. See menu above.{RESET}")

    def execute(self):
        while True:
            clear_console()
            self.show_menu()
            choice = self.get_tool()

            if choice == 'exit':
                print(f"{CYAN}CyberDeck shutting down.{RESET}")
                break

            _, tool_class = TOOLS[choice]
            try:
                if choice in ('sysinfo', 'sessions', 'toolcheck'):
                    tool_class().execute()
                else:
                    tool = tool_class()
                    tool.execute()
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Interrupted.{RESET}")
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")

            input(f"\n{CYAN}Press Enter to continue...{RESET}")


if __name__ == '__main__':
    Main()