import os
import json
import time
import requests
import threading
import paho.mqtt.client as mqtt

# ==============================================================================
# CONFIGURAÇÕES DE AMBIENTE
# ==============================================================================
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = 1883
SOC_URL = os.getenv("SOC_URL", "http://zerotrust-soc:8080/api/v1/incidents/report")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")

# ==============================================================================
# MOTOR DE INTELIGÊNCIA ARTIFICIAL (ESTÁVEL)
# ==============================================================================
def investigar_com_ia(event_source, description, mitre_tag):
    prompt = f"Analise este alerta de segurança XDR. Origem: {event_source}. MITRE ATT&CK Detectado: {mitre_tag}. Descrição: {description}. Forneça a Gravidade, o Objetivo do Atacante e uma Ação de Contenção em 3 linhas curtas e objetivas."
    
    payload = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=45)
        if response.status_code == 200:
            return response.json().get("response", "Erro interno na resposta da IA.")
        return "IA indisponível no momento."
    except Exception as e:
        return f"Erro de conexão com o Motor de IA: {str(e)}"

def processar_ia_background(sensor_id, event_source, description, mitre_tag):
    print(f"[⏳ IA] Iniciando análise de Root Cause para {sensor_id} em background...")
    
    analise_ia = investigar_com_ia(event_source, description, mitre_tag)
    
    # Payload clássico que gerou o Incidente #5
    payload_soc = {
        "sensor_id": sensor_id,
        "alert_type": "IA_ANALYSIS_COMPLETED",
        "description": analise_ia,
        "timestamp": time.time()
    }
    
    try:
        requests.post(SOC_URL, json=payload_soc)
        print(f"[✅ IA] Análise concluída e enviada ao SOC Central para {sensor_id}.")
    except Exception as e:
        print(f"[-] Erro ao encaminhar relatório ao SOC: {str(e)}")

# ==============================================================================
# EVENTOS DO BROKER MQTT
# ==============================================================================
def on_connect(client, userdata, flags, rc):
    print("[+] Conectado ao Broker MQTT do Zero-Trust XDR com sucesso!")
    client.subscribe("stacholski/it/sensor/#")
    client.subscribe("stacholski/ot/sensor/#")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        sensor_id = data.get("sensor_id", "DESCONHECIDO")
        
        alert_status = data.get("status", "")
        mitre_tag = data.get("mitre_technique", "N/A")
        is_ot_incident = (data.get("event_type") == "CRITICAL_OVERHEAT")
        
        is_suspicious = (alert_status == "SUSPICIOUS_ACTIVITY")
        is_high_risk = (alert_status == "HIGH_RISK_ACTIVITY")
        is_critical = (alert_status == "CRITICAL_ATTACK")

        if is_ot_incident or is_suspicious or is_high_risk or is_critical:
            
            if is_critical or is_ot_incident:
                print(f"[⚡ URGENTE] Ordem de contenção enviada! Isolando máquina ({sensor_id})...")
                client.publish(f"stacholski/containment/{sensor_id}", "ISOLATE_HOST")
            elif is_high_risk:
                print(f"[🚨 ATENÇÃO] Atividade de Alto Risco em {sensor_id}. Escalando para SOC...")
            elif is_suspicious:
                print(f"[🔍 MONITORANDO] Comportamento anômalo em {sensor_id}.")

            descricao_ataque = f"Processo: {data.get('process_name')} | CMD: {data.get('command_line')}"
            
            thread_ia = threading.Thread(
                target=processar_ia_background, 
                args=(sensor_id, data.get('event_source', 'WMI/Psutil-EDR'), descricao_ataque, mitre_tag)
            )
            thread_ia.start()
            
    except json.JSONDecodeError:
        pass
    except Exception as e:
        print(f"[-] Erro no processamento de telemetria: {str(e)}")

# ==============================================================================
# INICIALIZAÇÃO RESILIENTE
# ==============================================================================
if __name__ == "__main__":
    print("[*] Iniciando Cérebro XDR (Cross-Layer Detection and Response)...")
    
    client = mqtt.Client("XDR_Forwarder_Agent")
    client.on_connect = on_connect
    client.on_message = on_message

    conectado = False
    while not conectado:
        try:
            client.connect(BROKER, PORT, 60)
            conectado = True
        except ConnectionRefusedError:
            print("[-] Broker MQTT ainda não está pronto. Tentando novamente em 3 segundos...")
            time.sleep(3)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[-] Desligando Motor XDR...")
        client.disconnect()