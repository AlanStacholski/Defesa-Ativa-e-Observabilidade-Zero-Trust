# Active Defense & Zero-Trust Observability Platform (IT/OT Convergence)

An integrated hybrid cybersecurity platform based on Event-Driven Architecture (EDA). The system intercepts industrial telemetry (Operational Technology - OT) and corporate endpoint logs (Information Technology - IT), performs edge Root Cause Analysis (RCA) using Local Artificial Intelligence (LLMs), and orchestrates automated threat mitigation through a SOAR engine integrated with a robust Java backend featuring Zero-Trust identity validation.

## 🛠️ Ecosystem Architecture

1. **Factory Floor and Endpoints (Multi-threaded Simulators):** Scripts simulating corporate networks composed of multiple devices generating legitimate traffic and real-time behavioral logs (industrial sensor telemetry and Microsoft Windows Sysmon process creation logs).
2. **XDR Watchdog (Python Forwarder):** Cross-detection agent that monitors network buses (MQTT Client using wildcard topics `stacholski/#`), identifies security anomalies, and consumes local language models.
3. **Threat Mapping (Ollama / Llama 3.2):** Private local inference for rapid triage and classification of tactics and techniques aligned with corporate and industrial matrices (MITRE ATT&CK Enterprise and MITRE ATT&CK for ICS).
4. **Central SOC and SOAR (Java Spring Boot API):** Secure corporate backend protecting ingestion endpoints through a cryptographic barrier (`X-SOC-Token`), persisting immutable audit trails (H2 Relational Database), and executing automated decision-making for network containment and isolation.
5. **Operations Dashboard (Web UI):** Responsive dark-mode interface dynamically updated (asynchronous polling via Fetch API) for real-time incident visualization and monitoring.

---

## 📋 Prerequisites for Local Execution

To provision the environment on your development machine, ensure the following components are installed:

* **Operating Systems:** Windows 10 / 11
* **Java Environment:** Amazon Corretto JDK 21 (`JAVA_HOME` environment variables mapped)
* **Python Environment:** Python 3.10 or higher
* **AI Environment:** Ollama Client for Windows

---

## 🚀 How to Run the Platform

Follow the instructions below by opening separate PowerShell terminals for each component of the ecosystem:

### 1. Local AI Engine Initialization
Ensure the Ollama background service is running near the system clock and execute the initial download of the high-performance compact model:
```powershell
ollama run llama3.2
```
*(You can close the interactive prompt by typing `/bye` once it loads).*

### 2. Central SOC & SOAR Initialization (Java Backend)
Navigate to the backend project directory and run the embedded web server using the native Maven Wrapper:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\zerotrust-soc"
.\mvnw spring-boot:run
```
The console will display the Spring banner indicating that the API is active at `http://localhost:8080` and the local relational database `soc_db` has been provisioned at the root of the application.

### 3. Sensor Environment Setup (Python Venv)
Navigate to the detection scripts folder and configure the isolated dependencies:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\Sensor_OT"
python -m venv venv
.\venv\Scripts\Activate
pip install paho-mqtt==1.6.1 requests
```

### 4. XDR Watchdog Initialization
With the virtual environment `(venv)` active in the terminal, start the cross-monitoring agent:
```powershell
python forwarder_ia.py
```

### 5. Test Execution and Load Simulations (Simultaneous Attack)
Open new terminals in the sensor folder, activate the virtual environment (`.\venv\Scripts\Activate`), and run the fleet simulators to watch the defensive orchestration automatically isolate the infected machines:

* **To simulate the Industrial Factory (5 Boilers with a critical surge on Boiler 03):**
  ```powershell
  python simulador_frota_ot.py
  ```
* **To simulate the Corporate Office (15 Windows Machines with payload injection on WIN-DESKTOP-07):**
  ```powershell
  python simulador_frota_it.py
  ```

Access **`http://localhost:8080`** in your browser to watch the automatic containments being consolidated on the SOC dashboard.

---

## 🔒 Applied Zero-Trust Security Policies
* **Device Token-Based Authentication:** The header of REST requests strictly validates the presence of the authentication hash `X-SOC-Token: zt-token-secreto-2026`. Unauthenticated requests or those with forged tokens suffer an immediate drop (`HTTP 401 Unauthorized`), preventing injection attacks and spoofing of false alerts against the SOC.
* **Alert Fatigue Prevention (Alert Suppression):** The XDR agent features state logic for network debounce control. If a compromised asset continues to generate consecutive redundant alerts, the forwarder suppresses the repetitive triggering of the AI and the sending of POST requests, protecting the backend's processing pipeline against internal Denial of Service (DDoS) attacks.