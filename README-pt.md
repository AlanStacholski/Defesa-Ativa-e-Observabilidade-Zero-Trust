# Plataforma de Defesa Ativa e Observabilidade Zero-Trust (IT/OT Convergence)

Uma plataforma integrada de cibersegurança híbrida baseada em arquitetura orientada a eventos (EDA). O sistema intercepta telemetria industrial (tecnologia operacional - OT) e logs de endpoints corporativos (tecnologia da informação - IT), realiza a Análise de Causa Raiz (RCA) na borda utilizando Inteligência Artificial Local (LLM) e orquestra a mitigação automática de ameaças através de um motor SOAR integrado a um backend robusto Java com validação de identidade Zero-Trust.

## 🛠️ Arquitetura do Ecossistema

1. **Chão de Fábrica e Endpoints (Simuladores Multi-threaded):** Scripts simulando redes corporativas compostas por múltiplos dispositivos gerando tráfego legítimo e logs comportamentais em tempo real (telemetria de sensores industriais e logs de criação de processos Microsoft Windows Sysmon).
2. **Cão de Guarda XDR (Python Forwarder):** Agente de detecção cruzada que monitora barramentos de rede (MQTT Client utilizando tópicos curinga `stacholski/#`), identifica anomalias de segurança e consome modelos locais de linguagem.
3. **Mapeamento de Ameaças (Ollama / Llama 3.2):** Inferência local privada de RAG para triagem rápida e classificação de táticas e técnicas alinhadas às matrizes corporativas e industriais (MITRE ATT&CK Enterprise e MITRE ATT&CK for ICS).
4. **SOC Central e SOAR (Java Spring Boot API):** Backend corporativo seguro protegendo endpoints de ingestão através de barreira criptográfica (`X-SOC-Token`), persistindo trilhas de auditoria imutáveis (Banco H2 Relacional) e executando tomadas de decisão automática para contenção e isolamento de rede.
5. **Painel de Operações (Dashboard Web):** Interface responsiva em Dark-mode atualizada dinamicamente (polling assíncrono via Fetch API) para visualização e acompanhamento de incidentes em tempo real.

---

## 📋 Pré-requisitos para Execução Local

Para provisionar o ambiente na sua máquina de desenvolvimento, garanta que os seguintes componentes estejam instalados:

* **Sistemas Operacionais:** Windows 10 / 11
* **Ambiente Java:** Amazon Corretto JDK 21 (Variáveis de ambiente `JAVA_HOME` mapeadas)
* **Ambiente Python:** Python 3.10 ou superior
* **Ambiente IA:** Ollama Client para Windows

---

## 🚀 Como Rodar a Plataforma de Forma Simples

Siga as instruções abaixo abrindo terminais PowerShell separados para cada componente do ecossistema:

### 1. Inicialização do Motor de IA Local
Certifique-se de que o serviço em segundo plano do Ollama está em execução perto do relógio do sistema e execute o download inicial do modelo compacto de alto desempenho:
```powershell
ollama run llama3.2
```
*(Você pode fechar o prompt interativo digitando `/bye` assim que carregar).*

### 2. Inicialização do SOC Central & SOAR (Backend Java)
Navegue até o diretório do projeto backend e execute o servidor web embarcado através do Maven Wrapper nativo:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\zerotrust-soc"
.\mvnw spring-boot:run
```
O console exibirá o banner do Spring indicando que a API está ativa em `http://localhost:8080` e que o banco relacional local `soc_db` foi provisionado na raiz da aplicação.

### 3. Configuração do Ambiente de Sensores (Python Venv)
Navegue até a pasta de scripts de detecção e configure as dependências isoladas:
```powershell
cd "C:\Projetos\Plataforma de Defesa Ativa e Observabilidade Zero-Trust\Sensor_OT"
python -m venv venv
.\venv\Scripts\Activate
pip install paho-mqtt==1.6.1 requests
```

### 4. Inicialização do Cão de Guarda XDR
Com o ambiente virtual `(venv)` ativo no terminal, inicialize o agente de monitoramento cruzado:
```powershell
python forwarder_ia.py
```

### 5. Execução dos Testes e Simulações de Carga (Ataque Simultâneo)
Abra novos terminais na pasta de sensores, ative o ambiente virtual (`.\venv\Scripts\Activate`) e execute os simuladores de frota para ver a orquestração defensiva isolando as máquinas infectadas de forma automatizada:

* **Para simular a Fábrica Industrial (5 Caldeiras com surto crítico na Caldeira 03):**
  ```powershell
  python simulador_frota_ot.py
  ```
* **Para simular o Escritório Corporativo (15 Máquinas Windows com injeção de payload no WIN-DESKTOP-07):**
  ```powershell
  python simulador_frota_it.py
  ```

Acesse **`http://localhost:8080`** no seu navegador para assistir às contenções automáticas sendo consolidadas no painel do SOC.

---

## 🔒 Políticas de Segurança Zero-Trust Aplicadas
* **Autenticação Baseada em Token de Dispositivo:** O cabeçalho das requisições REST obrigatoriamente valida a presença do hash de autenticação `X-SOC-Token: zt-token-secreto-2026`. Requisições não autenticadas ou com tokens fraudados sofrem drop imediato (`HTTP 401 Unauthorized`) impedindo ataques de injeção e spoofing de falsos alertas contra o SOC.
* **Prevenção de Fadiga de Alertas (Alert Suppression):** O agente XDR possui lógica de estado para controle de debounce de rede. Se um ativo comprometido continuar gerando alertas redundantes consecutivos, o forwarder suprime o acionamento repetitivo da IA e o envio de requisições POST, protegendo o pipeline de processamento do backend contra negação de serviço interna (DDoS).