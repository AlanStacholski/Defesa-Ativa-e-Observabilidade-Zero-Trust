import time
import json
import random
import sys
import paho.mqtt.client as mqtt

# Configurações do Broker Público para teste inicial
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "stacholski/industria/sensor/caldeira_01"

# Modo de execução (Normal ou Ataque)
# Se rodarmos o script com o argumento --attack, ele simula a anomalia
modo_ataque = "--attack" in sys.argv

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Conectado ao Broker MQTT com sucesso!")
    else:
        print(f"[-] Falha ao conectar. Código: {rc}")

client = mqtt.Client("Sensor_OT_Local")
client.on_connect = on_connect

print("[*] Iniciando conexão com a rede OT...")
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    print(f"[*] Sensor operando em modo: {'ATAQUE (Anomalia)' if modo_ataque else 'NORMAL'}")
    print("[*] Pressione CTRL+C para parar.\n")
    
    while True:
        # Lógica de geração de dados baseada no modo de operação
        if modo_ataque:
            temperatura = round(random.uniform(400.0, 950.0), 2)
            pressao = round(random.uniform(150.0, 300.0), 2)
            status = "CRITICAL_OVERHEAT"
        else:
            temperatura = round(random.uniform(170.0, 185.0), 2)
            pressao = round(random.uniform(30.0, 45.0), 2)
            status = "NORMAL"

        payload = {
            "sensor_id": "caldeira_01",
            "timestamp": time.time(),
            "temperatura_celsius": temperatura,
            "pressao_psi": pressao,
            "status": status
        }

        # Publica o JSON no tópico MQTT
        client.publish(TOPIC, json.dumps(payload))
        print(f"[>] Telemetria enviada: {payload}")
        
        # Acelera o envio se estiver sob ataque (simulando DoS/ruído)
        time.sleep(0.5 if modo_ataque else 2.0)

except KeyboardInterrupt:
    print("\n[-] Desligando sensor e encerrando conexão...")
    client.loop_stop()
    client.disconnect()