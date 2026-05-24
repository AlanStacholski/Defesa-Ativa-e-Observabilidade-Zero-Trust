# Active Defense & Zero-Trust Observability Platform (IT/OT Convergence)

An integrated cybersecurity platform based on Event-Driven Architecture (EDA). The system monitors industrial telemetry (OT) and corporate endpoints (IT) in real-time. It performs edge Root Cause Analysis (RCA) using local Large Language Models (LLMs) and orchestrates automated threat mitigation through a SOAR engine, integrated with a Java backend enforced by Zero-Trust validation.

## Ecosystem Architecture

1. **Windows EDR Agent (NGAV & Leviathan DNA):** A real-time endpoint agent running on Windows. It utilizes process monitoring and File Integrity Monitoring (FIM) to detect ransomware, extract executable hashes, and profile malicious behavior (such as obfuscated PowerShell payloads and DNS reconnaissance) without relying solely on static signatures.
2. **XDR Forwarder (Docker Ecosystem):** A containerized cross-detection agent that monitors MQTT network buses. It identifies security anomalies, enforces immediate network containment, and acts as a bridge to the AI engine.
3. **Asynchronous Threat Mapping (Ollama / Llama 3.2):** Local, private inference engine. It is executed in a parallel thread by the XDR Forwarder to ensure the AI's processing time does not create latency in the incident containment pipeline. It maps tactics to the MITRE ATT&CK frameworks.
4. **Central SOC and SOAR (Java Spring Boot API):** Corporate backend protecting data ingestion through a strict cryptographic barrier. It persists immutable audit trails in a relational database (H2) and handles automated isolation commands.
5. **Operations Dashboard (Web UI):** Responsive interface updated dynamically via asynchronous polling for real-time incident visualization.

## Prerequisites for Local Execution

To provision the environment, ensure the following components are installed:

* **Operating System:** Windows 10 / 11 (for the EDR Agent)
* **Containerization:** Docker Desktop (Docker Compose)
* **Java Environment:** Amazon Corretto JDK 21
* **Python Environment:** Python 3.10 or higher
* **AI Environment:** Ollama Client for Windows

## How to Run the Platform

Follow the sequence below to initialize the distinct architectural layers:

### 1. Local AI Engine Initialization
Ensure the Ollama background service is running and start the local model:
```powershell
ollama run llama3.2
```
*(Close the interactive prompt by typing `/bye` once the model is loaded into memory).*

### 2. Infrastructure & SOC Initialization (Docker & Java)
Start the complete containerized infrastructure (MQTT Broker, XDR Forwarder) and the Java Backend:
```powershell
# For the Docker ecosystem
docker-compose up --build -d

# For the Java Backend
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\zerotrust-soc"
.\mvnw spring-boot:run
```
The API and Dashboard will be available at `http://localhost:8080`.

### 3. EDR Agent Setup (Windows Endpoint)
Navigate to the sensor directory and configure the Python virtual environment:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\Sensor_OT"
python -m venv venv
.\venv\Scripts\Activate
pip install psutil watchdog paho-mqtt==1.6.1 requests wmi
```

### 4. EDR Execution and Threat Simulation
With the virtual environment active, start the endpoint agent:
```powershell
python agente_edr_real.py
```
To validate the behavioral detection pipeline, open a separate PowerShell terminal and execute an obfuscated payload or a file manipulation test inside the honeypot directory. The containment logic and the AI root cause analysis will be reflected automatically on the SOC dashboard.

## Applied Zero-Trust Security Policies

* **Strict Header Authentication:** The REST API strictly validates the presence of the custom header `X-SOC-Token`. Unauthenticated requests suffer an immediate drop (HTTP 401 Unauthorized), preventing data injection or alert spoofing.
* **Alert Fatigue Prevention:** The XDR agent implements debounce logic. Consecutive redundant alerts from the same compromised asset are suppressed, protecting the backend's processing pipeline and the AI engine from internal Denial of Service conditions.
