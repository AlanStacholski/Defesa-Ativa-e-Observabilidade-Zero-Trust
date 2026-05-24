import os
import json
import time
import socket
import hashlib
import win32api
import win32con
import win32security
import psutil
import paho.mqtt.client as mqtt
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

BROKER = "localhost"
PORT = 1883
HOSTNAME = socket.gethostname()
TELEMETRY_TOPIC = f"stacholski/it/sensor/{HOSTNAME}"

HONEYPOT_DIR = r"C:\Users\Public\Documents\Monitoramento_FIM"
if not os.path.exists(HONEYPOT_DIR):
    os.makedirs(HONEYPOT_DIR)

class RansomwareDetector(FileSystemEventHandler):
    def __init__(self):
        self.modifications = deque()
        self.TIME_WINDOW = 5.0
        self.THRESHOLD = 3

    def on_modified(self, event):
        if not event.is_directory:
            current_time = time.time()
            self.modifications.append(current_time)
            
            while self.modifications and current_time - self.modifications[0] > self.TIME_WINDOW:
                self.modifications.popleft()

            if len(self.modifications) >= self.THRESHOLD:
                print(f"\n[🔥 CRÍTICO] RANSOMWARE DETECTADO: Múltiplos arquivos criptografados!")
                payload = {
                    "sensor_id": HOSTNAME,
                    "timestamp": current_time,
                    "event_source": "FIM-Engine",
                    "process_name": "Ransomware_Behavior",
                    "command_line": f"Exploração no diretório: {HONEYPOT_DIR}",
                    "mitre_technique": "T1486 (Data Encrypted for Impact)",
                    "status": "CRITICAL_ATTACK"
                }
                client.publish(TELEMETRY_TOPIC, json.dumps(payload))
                self.modifications.clear()

def calculate_sha256(filepath):
    hash_sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return "N/A"

def leviathan_behavioral_profile(process, command_line_lower):
    traits = []
    behavior_score = 0
    mitre_tags = []

    try:
        if "encodedcommand" in command_line_lower or "-enc " in command_line_lower or "-e " in command_line_lower:
            behavior_score += 30
            traits.append("Execução de Payload Ofuscado (Base64)")
            mitre_tags.append("T1027 (Obfuscated Files or Information)")

        if "resolve-dnsname" in command_line_lower or "nslookup" in command_line_lower:
            behavior_score += 15
            traits.append("Reconhecimento de Rede / Varredura DNS")
            mitre_tags.append("T1046 (Network Service Discovery)")

        parent = process.parent()
        if parent:
            parent_name = parent.name().lower()
            suspicious_parents = ["winword.exe", "excel.exe", "powerpnt.exe"]
            if parent_name in suspicious_parents and "powershell" in process.name().lower():
                behavior_score += 80
                traits.append(f"Linhagem Maliciosa: Injetado via {parent_name}")
                mitre_tags.append("T1059 (Execution) + T1566 (Phishing)")

        exe_path = process.exe().lower()
        if "appdata\\local\\temp" in exe_path or "programdata" in exe_path:
            behavior_score += 40
            traits.append("Execução em Diretório Temporário")
            mitre_tags.append("T1036 (Masquerading)")

    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
        pass

    return behavior_score, " | ".join(traits), " + ".join(mitre_tags)

client = mqtt.Client(f"Real_EDR_Agent_{HOSTNAME}")
client.connect(BROKER, PORT, 60)
client.loop_start()

print(f"[*] Agente EDR NGAV Iniciado: {HOSTNAME}")

observer = Observer()
observer.schedule(RansomwareDetector(), HONEYPOT_DIR, recursive=True)
observer.start()

known_pids = set(psutil.pids())

def check_admin_privileges(pid):
    try:
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        token = win32security.OpenProcessToken(handle, win32con.TOKEN_QUERY)
        return win32security.GetTokenInformation(token, win32security.TokenElevation) > 0
    except Exception:
        return False

try:
    while True:
        current_pids = set(psutil.pids())
        new_pids = current_pids - known_pids

        for pid in new_pids:
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                
                if process_name and process_name.lower() not in ["svchost.exe", "conhost.exe", "taskhostw.exe"]:
                    
                    exe_path = process.exe()
                    cmdline_list = process.cmdline()
                    command_line = " ".join(cmdline_list) if cmdline_list else ""
                    
                    process_name_lower = process_name.lower()
                    command_line_lower = command_line.lower()
                    is_elevated = check_admin_privileges(pid)
                    
                    process_hash = calculate_sha256(exe_path) if exe_path else "N/A"
                    dna_score, dna_traits, dna_mitre = leviathan_behavioral_profile(process, command_line_lower)

                    alert_status = "NORMAL"
                    mitre_tech = dna_mitre if dna_mitre else "N/A"
                    critical_iocs = ["bypass", "downloadstring", "iex", "mimikatz"]
                    
                    if dna_score >= 40:
                        alert_status = "CRITICAL_ATTACK"
                        print(f"\n[🧬 LEVIATHAN DNA] Bloqueio Crítico! Score: {dna_score}/100")
                        command_line += f" | Motivo: {dna_traits}"
                    elif dna_score >= 15:
                        alert_status = "HIGH_RISK_ACTIVITY"
                        print(f"\n[🧬 LEVIATHAN DNA] Anomalia Detectada! Score: {dna_score}/100")
                        command_line += f" | Análise: {dna_traits}"
                    elif "powershell" in process_name_lower or "cmd.exe" in process_name_lower or "pwsh.exe" in process_name_lower:
                        if any(ioc in command_line_lower for ioc in critical_iocs):
                            alert_status = "CRITICAL_ATTACK"
                            mitre_tech = "T1059.001 (PowerShell) - Execution"
                            print(f"\n[🔥 CRÍTICO] Assinatura Maliciosa interceptada: {command_line}")
                        elif is_elevated:
                            alert_status = "HIGH_RISK_ACTIVITY"
                            mitre_tech = "T1078 (Valid Accounts)"
                            print(f"[⚠️ ALTO RISCO] Terminal Elevado! SHA-256: {process_hash[:16]}...")
                        else:
                            alert_status = "SUSPICIOUS_ACTIVITY"
                            mitre_tech = "T1059 (Command Interpreter)"
                            print(f"[🔍 SUSPEITO] Terminal comum (Hash: {process_hash[:16]}...)")

                    if alert_status != "NORMAL":
                        payload = {
                            "sensor_id": HOSTNAME,
                            "timestamp": time.time(),
                            "event_source": "Leviathan-NGAV",
                            "process_name": process_name,
                            "command_line": f"Hash: {process_hash} | CMD: {command_line}",
                            "mitre_technique": mitre_tech,
                            "status": alert_status
                        }
                        client.publish(TELEMETRY_TOPIC, json.dumps(payload))
            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        known_pids = current_pids
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n[-] Encerrando NGAV...")
    observer.stop()
    observer.join()
    client.loop_stop()
    client.disconnect()