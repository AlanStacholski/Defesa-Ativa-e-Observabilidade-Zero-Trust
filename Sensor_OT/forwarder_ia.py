import paho.mqtt.client as mqtt
import requests
import json
import time
import os

# Configurações XDR adaptáveis para Docker ou Local
BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = 1883
TOPIC = "stacholski/#"
# host.docker.internal permite que o container Python aceda ao Ollama que está a correr no Windows Host
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
SOC_URL = os.getenv("SOC_URL", "http://localhost:8080/api/v1/incidents/report")
ultimo_alerta_ia = {}
TEMPO_SUPRESSAO_SEGUNDOS = 60 

def enviar_para_soc(fonte, relatorio, tipo_ambiente):
    try:
        payload = {"source": fonte, "ai_report": relatorio}
        headers = {"X-SOC-Token": "zt-token-secreto-2026"} 
        
        resposta = requests.post(SOC_URL, json=payload, headers=headers)
        
        if resposta.status_code == 200:
            dados_soc = resposta.json()
            
            # Se o SOAR (Java) autorizou a ação de contenção
            if dados_soc.get("action") == "SHUTDOWN":
                if tipo_ambiente == "IT":
                    print(f"[⚡] Ordem de contenção! Isolando endpoint Windows ({fonte}) da rede...")
                    topico_alvo = f"stacholski/it/comando/{fonte}"
                    comando = "ISOLATE_NETWORK"
                else:
                    print(f"[⚡] Ordem de contenção! Desligando máquina industrial ({fonte})...")
                    topico_alvo = f"stacholski/industria/comando/{fonte}"
                    comando = "SHUTDOWN"
                    
                client.publish(topico_alvo, comando)
                
        elif resposta.status_code == 401:
            print("[-] Erro: O SOC rejeitou a conexão (Falha Zero-Trust).")
    except Exception as e:
        print(f"[-] Erro ao conectar ao Java: {e}")

def analisar_com_ia(sensor_id, payload_str, tipo_ambiente):
    print(f"\n[!] INCIDENTE {tipo_ambiente}: Acionando IA para RCA do ativo {sensor_id}...")
    
    prompt = f"""
    Você é um analista de SOC. Classifique a ameaça abaixo. 
    Se for telemetria OT (pressão/temperatura), mapeie no MITRE ICS. 
    Se for log IT (Windows/Sysmon), mapeie no MITRE Enterprise.
    
    Responda APENAS com 3 linhas curtas:
    1. Gravidade: CRÍTICO
    2. Técnica MITRE:
    3. Ação de Contenção:
    
    Dados: {payload_str}
    """

    data = {"model": "llama3.2", "prompt": prompt, "stream": True}

    try:
        response = requests.post(OLLAMA_URL, json=data, stream=True)
        if response.status_code == 200:
            print("-" * 50)
            relatorio_completo = ""
            for line in response.iter_lines():
                if line:
                    json_data = json.loads(line)
                    pedaco_texto = json_data.get("response", "")
                    print(pedaco_texto, end="", flush=True)
                    relatorio_completo += pedaco_texto
            
            print("\n" + "-" * 50)
            enviar_para_soc(sensor_id, relatorio_completo, tipo_ambiente)
            print("[+] Relatório enviado ao SOC Central.")
    except Exception as e:
        print(f"\n[-] Erro IA: {e}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    
    try:
        dados = json.loads(payload_str)
        status = dados.get("status")
        sensor_id = dados.get("sensor_id")
        
        # Identifica o tipo de ataque pelas regras de detecção
        eh_ataque_ot = (status == "CRITICAL_OVERHEAT")
        eh_ataque_it = (status == "SUSPICIOUS_ACTIVITY")

        if eh_ataque_ot or eh_ataque_it:
            tipo_ambiente = "IT" if eh_ataque_it else "OT"
            tempo_atual = time.time()
            
            # Prevenção de fadiga (silenciosa)
            if sensor_id in ultimo_alerta_ia:
                if (tempo_atual - ultimo_alerta_ia[sensor_id]) < TEMPO_SUPRESSAO_SEGUNDOS:
                    return 

            ultimo_alerta_ia[sensor_id] = tempo_atual
            analisar_com_ia(sensor_id, payload_str, tipo_ambiente)

    except json.JSONDecodeError:
        pass

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Forwarder XDR conectado. Escutando redes corporativas (IT) e industriais (OT)...")
        client.subscribe(TOPIC)

client = mqtt.Client("Forwarder_XDR_SecOps")
client.on_connect = on_connect
client.on_message = on_message

print("[*] Iniciando Cérebro XDR (Cross-Layer Detection and Response)...")

conectado = False
while not conectado:
    try:
        client.connect(BROKER, PORT, 60)
        conectado = True
    except ConnectionRefusedError:
        print("[-] Broker MQTT ainda não está pronto. Tentando novamente em 3 segundos...")
        time.sleep(3)
# ---------------------------------------

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()