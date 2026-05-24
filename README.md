# Plataforma de Defesa Ativa e Observabilidade Zero-Trust (IT/OT Convergence)

Uma plataforma integrada de cibersegurança baseada em arquitetura orientada a eventos (EDA). O sistema monitora telemetria industrial (OT) e endpoints corporativos (IT) em tempo real. Ele realiza a Análise de Causa Raiz (RCA) na borda utilizando modelos de linguagem locais (LLM) e orquestra a mitigação automática de ameaças através de um motor SOAR, integrado a um backend Java com validação Zero-Trust.

## Arquitetura do Ecossistema

1. **Agente EDR Windows (NGAV & Leviathan DNA):** Agente de endpoint operando em tempo real no Windows. Utiliza monitoramento de processos e FIM (File Integrity Monitoring) para detectar ransomware, extrair hashes e perfilar comportamentos anômalos (como ofuscação de comandos PowerShell e varreduras DNS), sem depender exclusivamente de assinaturas estáticas.
2. **Cão de Guarda XDR (Ecossistema Docker):** Agente de detecção cruzada em contêiner que monitora barramentos MQTT. Identifica anomalias, aplica regras de contenção de rede imediatas e atua como ponte para o motor de IA.
3. **Mapeamento de Ameaças Assíncrono (Ollama / Llama 3.2):** Motor de inferência local e privado. Executado em uma thread paralela pelo orquestrador XDR para garantir que o tempo de processamento da IA não gere latência no bloqueio da ameaça. Mapeia táticas para os frameworks MITRE ATT&CK.
4. **SOC Central e SOAR (Java Spring Boot API):** Backend corporativo que protege a ingestão de dados através de uma barreira criptográfica estrita. Persiste trilhas de auditoria imutáveis em banco de dados relacional (H2) e processa comandos de isolamento.
5. **Painel de Operações (Dashboard Web):** Interface atualizada dinamicamente via polling assíncrono para visualização de incidentes.

## Pré-requisitos para Execução Local

Para provisionar o ambiente, certifique-se de ter os seguintes componentes instalados:

* **Sistema Operacional:** Windows 10 / 11 (para o Agente EDR)
* **Conteinerização:** Docker Desktop (Docker Compose)
* **Ambiente Java:** Amazon Corretto JDK 21
* **Ambiente Python:** Python 3.10 ou superior
* **Ambiente de IA:** Ollama Client para Windows

## Como Rodar a Plataforma

Siga a sequência abaixo para inicializar as camadas da arquitetura:

### 1. Inicialização do Motor de IA
Certifique-se de que o serviço do Ollama está em execução e inicie o modelo local:
```powershell
ollama run llama3.2
```
*(Feche o prompt interativo digitando `/bye` assim que o modelo for carregado na memória).*

### 2. Inicialização da Infraestrutura e SOC (Docker & Java)
Inicie a infraestrutura em contêineres (Broker MQTT, Forwarder XDR) e o Backend Java:
```powershell
# Para o ecossistema Docker
docker-compose up --build -d

# Para o Backend Java
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\zerotrust-soc"
.\mvnw spring-boot:run
```
A API e o Dashboard estarão disponíveis em `http://localhost:8080`.

### 3. Configuração do Agente EDR (Windows Endpoint)
Navegue até o diretório de sensores e configure o ambiente virtual Python:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\Sensor_OT"
python -m venv venv
.\venv\Scripts\Activate
pip install psutil watchdog paho-mqtt==1.6.1 requests wmi
```

### 4. Execução do EDR e Simulação de Ameaças
Com o ambiente virtual ativo, inicie o agente de endpoint:
```powershell
python agente_edr_real.py
```
Para validar o pipeline de detecção, abra um terminal PowerShell separado e execute um payload ofuscado ou altere arquivos no diretório de honeypot. A lógica de contenção e a análise da IA refletirão automaticamente no painel do SOC.

## Políticas de Segurança Zero-Trust Aplicadas

* **Autenticação Estrita de Cabeçalho:** A API REST valida obrigatoriamente a presença do cabeçalho customizado `X-SOC-Token`. Requisições não autenticadas sofrem descarte imediato (HTTP 401 Unauthorized), prevenindo injeção de dados ou falsificação de alertas.
* **Prevenção de Fadiga de Alertas:** O agente XDR implementa lógica de debounce. Alertas redundantes consecutivos de um mesmo ativo comprometido são suprimidos, protegendo o pipeline do backend e o motor de IA contra condições de Negação de Serviço internas.