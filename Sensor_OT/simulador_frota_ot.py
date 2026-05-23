import time
import json
import random
import threading
import sys
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

class SensorIndustrial(threading.Thread):
    def __init__(self, sensor_id, modo_ataque=False):
        super().__init__()
        self.sensor_id = sensor_id
        self.modo_ataque = modo_ataque
        self.ativo = True
        self.topic_telemetria = f"stacholski/industria/sensor/{sensor_id}"
        self.topic_comando = f"stacholski/industria/comando/{sensor_id}"
        
        self.client = mqtt.Client(f"Client_OT_{sensor_id}_{random.randint(100,999)}")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        self.client.subscribe(self.topic_comando)

    def on_message(self, client, userdata, msg):
        comando = msg.payload.decode('utf-8')
        if comando == "SHUTDOWN":
            print(f"\n[⚡] SOC ORDENOU SHUTDOWN PARA: {self.sensor_id}. Desligando...")
            self.ativo = False

    def run(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        
        while self.ativo:
            if self.modo_ataque:
                temp, pressao = round(random.uniform(400, 950), 2), round(random.uniform(150, 300), 2)
                status = "CRITICAL_OVERHEAT"
            else:
                temp, pressao = round(random.uniform(170, 185), 2), round(random.uniform(30, 45), 2)
                status = "NORMAL"

            payload = {
                "sensor_id": self.sensor_id,
                "timestamp": time.time(),
                "temperatura_celsius": temp,
                "pressao_psi": pressao,
                "status": status
            }
            self.client.publish(self.topic_telemetria, json.dumps(payload))
            
            # Printa apenas os ataques para não poluir a tela com 50 máquinas normais
            if self.modo_ataque:
                print(f"[> ALERTA] {self.sensor_id} enviando anomalia...")
            
            time.sleep(0.5 if self.modo_ataque else 5.0)

        self.client.loop_stop()
        self.client.disconnect()

# --- Configuração da Frota ---
quantidade_maquinas = 5
maquina_infectada = "caldeira_03" # Qual máquina sofrerá o ataque?

print(f"[*] Iniciando chão de fábrica com {quantidade_maquinas} máquinas...")

sensores = []
for i in range(1, quantidade_maquinas + 1):
    nome_maquina = f"caldeira_0{i}"
    # Ativa o modo de ataque apenas na máquina escolhida
    sob_ataque = (nome_maquina == maquina_infectada)
    
    sensor = SensorIndustrial(nome_maquina, modo_ataque=sob_ataque)
    sensores.append(sensor)
    sensor.start()
    print(f"[+] Máquina {nome_maquina} operando (Ataque: {sob_ataque})")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[-] Encerrando frota...")
    for s in sensores:
        s.ativo = False