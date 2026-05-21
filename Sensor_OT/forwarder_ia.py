import paho.mqtt.client as mqtt
import requests
import json

# Configurações
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "stacholski/industria/sensor/caldeira_01"
OLLAMA_URL = "http://localhost:11434/api/generate"

def analisar_com_ia(payload_str):
    print("\n[!] ANOMALIA DETECTADA! Acionando IA Local para Root Cause Analysis (RCA)...")
    
    prompt = f"""
    Você é um Arquiteto de Segurança e Analista de SOC nível Sênior. 
    Uma anomalia crítica foi detectada na rede OT (Tecnologia Operacional) industrial.
    
    Dados interceptados do sensor:
    {payload_str}
    
    Escreva um relatório de incidente curto e direto contendo:
    1. A gravidade do evento.
    2. Possível vetor de ataque mapeado no MITRE ATT&CK for ICS (Ex: Loss of Control, Manipulation of Control).
    3. Uma ação imediata de contenção que o time de resposta a incidentes deve tomar.
    
    Responda em português.
    """

    data = {
        "model": "llama3.2",
        "prompt": prompt,
        "stream": True
    }

    try:
        response = requests.post(OLLAMA_URL, json=data, stream=True)
        
        if response.status_code == 200:
            print("\n" + "="*50)
            print(" RELATÓRIO DE INCIDENTE (Gerado por Llama 3.2 Local)")
            print("="*50)
            
            relatorio_completo = ""
            for line in response.iter_lines():
                if line:
                    json_data = json.loads(line)
                    pedaco_texto = json_data.get("response", "")
                    print(pedaco_texto, end="", flush=True)
                    relatorio_completo += pedaco_texto  # Guarda o texto para mandar pro Java
            
            print("\n" + "="*50 + "\n")
            
            # --- NOVA INTEGRAÇÃO COM O BACKEND JAVA ---
            print("[*] Enviando relatório para o SOC Central (Java)...")
            soc_url = "http://localhost:8080/api/v1/incidents/report"
            soc_payload = {
                "source": "Sensor_OT_Caldeira_01",
                "ai_report": relatorio_completo
            }
            
            try:
                soc_response = requests.post(soc_url, json=soc_payload)
                if soc_response.status_code == 200:
                    print("[+] Incidente registrado com sucesso no SOC!")
            except Exception as e:
                print(f"[-] Erro ao conectar com o SOC Java: {e}")
                
        else:
            print(f"\n[-] Erro na IA: {response.status_code}")
    except Exception as e:
        print(f"\n[-] Erro ao comunicar com o Ollama: {e}")

def on_message(client, userdata, msg):
    payload_str = msg.payload.decode('utf-8')
    # print(f"[*] Monitorando: {payload_str}") # Descomente se quiser ver o tráfego normal
    
    try:
        dados = json.loads(payload_str)
        # Gatilho: Se o status for de superaquecimento, aciona a IA
        if dados.get("status") == "CRITICAL_OVERHEAT":
            analisar_com_ia(payload_str)
    except json.JSONDecodeError:
        pass

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[+] Forwarder conectado ao Broker. Escutando a rede OT...")
        client.subscribe(TOPIC)
    else:
        print(f"[-] Falha de conexão. Código: {rc}")

client = mqtt.Client("Forwarder_SecOps_Local")
client.on_connect = on_connect
client.on_message = on_message

print("[*] Iniciando o Cão de Guarda Zero-Trust...")
client.connect(BROKER, PORT, 60)

try:
    # Fica rodando para sempre escutando novas mensagens
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[-] Encerrando monitoramento...")
    client.disconnect()