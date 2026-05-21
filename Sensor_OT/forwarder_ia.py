import paho.mqtt.client as mqtt
import requests
import json
import time

# Configurações
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "stacholski/industria/sensor/caldeira_01"
OLLAMA_URL = "http://localhost:11434/api/generate"
SOC_URL = "http://localhost:8080/api/v1/incidents/report"

# Memória de estado para Supressão de Alertas (Alert Suppression)
ultimo_alerta_ia = {}
TEMPO_SUPRESSAO_SEGUNDOS = 60 # Só aciona a IA de novo após 60 segundos de silêncio

def enviar_para_soc(fonte, relatorio):
    try:
        payload = {"source": fonte, "ai_report": relatorio}
        requests.post(SOC_URL, json=payload)
    except:
        pass # Ignora erro caso o Java esteja desligado

def analisar_com_ia(sensor_id, payload_str):
    print(f"\n[!] NOVO INCIDENTE: Acionando IA para RCA do sensor {sensor_id}...")
    
    # Prompt reduzido e direto ao ponto = Resposta MUITO mais rápida
    prompt = f"""
    Análise de anomalia OT. Responda APENAS com 3 linhas curtas, sem introdução:
    1. Gravidade:
    2. Técnica MITRE ICS:
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
            
            # Envia para o Java
            enviar_para_soc(sensor_id, relatorio_completo)
            print("[+] Relatório enviado ao SOC Central.")
    except Exception as e:
        print(f"\n[-] Erro IA: {e}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    try:
        dados = json.loads(payload_str)
        status = dados.get("status")
        sensor_id = dados.get("sensor_id")

        if status == "CRITICAL_OVERHEAT":
            tempo_atual = time.time()
            
            # Lógica de Prevenção de Fadiga de Alertas
            if sensor_id in ultimo_alerta_ia:
                tempo_passado = tempo_atual - ultimo_alerta_ia[sensor_id]
                if tempo_passado < TEMPO_SUPRESSAO_SEGUNDOS:
                    # Falha persiste, mas ainda está no tempo de supressão. Não aciona IA.
                    print(f"[*] {sensor_id} continua em estado crítico. (Alerta suprimido).")
                    
                    # Opcional: Manda um ping pro Java saber que ainda tá pegando fogo
                    enviar_para_soc(sensor_id, "STATUS PERSISTENTE: Anomalia continua ocorrendo, ação imediata ainda requerida.")
                    return
            
            # Se for alerta novo (ou já passou do tempo), aciona a IA
            ultimo_alerta_ia[sensor_id] = tempo_atual
            analisar_com_ia(sensor_id, payload_str)

    except json.JSONDecodeError:
        pass

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Forwarder conectado. Escutando rede OT...")
        client.subscribe(TOPIC)

client = mqtt.Client("Forwarder_SecOps_Local")
client.on_connect = on_connect
client.on_message = on_message

print("[*] Iniciando Cão de Guarda (Com Supressão de Alertas)...")
client.connect(BROKER, PORT, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    client.disconnect()