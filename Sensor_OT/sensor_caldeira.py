import time
import json
import random
import sys
import paho.mqtt.client as mqtt
import os

BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_TELEMETRIA = "stacholski/industria/sensor/caldeira_01"
TOPIC_COMANDO = "stacholski/industria/comando/caldeira_01" # Novo tópico para receber ordens

modo_ataque = "--attack" in sys.argv
ativo = True # Variável de controle de estado

def on_message(client, userdata, msg):
    global ativo
    comando = msg.payload.decode('utf-8')
    if comando == "SHUTDOWN":
        print("\n[!!!] COMANDO DE CONTENÇÃO RECEBIDO DO SOC CENTRAL [!!!]")
        print("[!] Desligando equipamento imediatamente para evitar danos catastróficos...")
        ativo = False

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Conectado ao Broker MQTT com sucesso!")
        client.subscribe(TOPIC_COMANDO) # Passa a escutar as ordens do SOC
    else:
        print(f"[-] Falha ao conectar. Código: {rc}")

client = mqtt.Client("Sensor_OT_Local")
client.on_connect = on_connect
client.on_message = on_message

print("[*] Iniciando conexão com a rede OT...")
client.connect(BROKER, PORT, 60)
client.loop_start()

try:
    print(f"[*] Sensor operando em modo: {'ATAQUE (Anomalia)' if modo_ataque else 'NORMAL'}")
    print("[*] Pressione CTRL+C para parar.\n")
    
    while ativo:
        if modo_ataque:
            temperatura = round(random.uniform(400.0, 950.0), 2)
            pressao = round(random.uniform(150.0, 300.0), 2)
            status = "CRITICAL_OVERHEAT"
        else:
            temperatura = round(random.uniform(170.0, 185.0), 2)
            pressao = round(random.uniform(30.0, 45.0), 2)
            status = "NORMAL"

        payload = {"sensor_id": "caldeira_01", "timestamp": time.time(), "temperatura_celsius": temperatura, "pressao_psi": pressao, "status": status}
        client.publish(TOPIC_TELEMETRIA, json.dumps(payload))
        print(f"[>] Telemetria: {payload}")
        
        time.sleep(0.5 if modo_ataque else 2.0)

    # Se saiu do while, é porque o ativo virou False (recebeu SHUTDOWN)
    print("[-] Equipamento offline. Sistema isolado da rede.")
    client.loop_stop()
    client.disconnect()
    os._exit(0)

except KeyboardInterrupt:
    print("\n[-] Desligando sensor manualmente...")
    client.loop_stop()
    client.disconnect()