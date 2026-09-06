# 🛡️ ThreatCheckerBot

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Desktop-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Watch Demo on YouTube](https://img.shields.io/badge/Watch_Demo_on_YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/shorts/8xJ_-rKenSs?feature=share)

**ThreatCheckerBot** is an automated Threat Intelligence Telegram Bot designed to streamline Indicators of Compromise (IoC) analysis. It queries popular threat scan engines, aggregates security telemetry into a unified report, and leverages powerful Large Language Models (LLMs) via the **OpenRouter API** to provide an intelligent, human-readable **Security Verdict**.

---

## 📖 Project Description

Analyzing security indicators manually across multiple threat intelligence platforms can be time-consuming. **ThreatCheckerBot** automates this workflow directly inside Telegram:

1. **IoC Reception**: The user submits an Indicator of Compromise (**IPv4**, **URL**, **Domain**, or **Filehash**) to the Telegram Bot.
2. **Multi-Engine Scanning**: The bot queries API endpoints across popular security services, including:
   - 🦠 **VirusTotal**
   - 🛡️ **AbuseIPDB**
   - 🔍 **Shodan**
   - 🌊 **Pulsedive**
   - 🌐 **URLScan.io** *(and others)*
3. **Report Aggregation**: Raw response data is collected and formatted into a concise **IoC Scan Report**.
4. **AI Verdict Generation**: The report is dispatched to the **OpenRouter API**, where a powerful free LLM evaluates the findings, contextualizes the risk, and issues a final **AI Verdict**.
5. **Delivery**: The complete Scan Report along with the AI Verdict is delivered directly to the user as a Telegram message.

---

## ✨ Key Features

- ⚡ **Multi-Source OSINT Aggregation**: Concurrent scans across multiple threat intelligence providers.
- 🧠 **AI-Powered Assessment**: Deep contextual analysis and risk scoring provided by OpenRouter LLMs.
- 🎯 **Wide IoC Support**: Handles IPv4 addresses, domain names, URLs, and file hashes (MD5, SHA-1, SHA-256).
- 🐳 **Containerized Deployment**: Easy automated deployment using Docker Desktop and a Python launcher script.
- 💬 **Instant Telegram Reporting**: Formatted Markdown reports delivered straight to your chat or SOC group.

---

## 🔄 Workflow Architecture

```text
[ User (Telegram) ]
        │
        │ 1. Submits IoC (IP / Domain / URL / Hash)
        ▼
[ ThreatCheckerBot ]
        │
        ├──► 2. Queries Scan APIs ──► [ VirusTotal | AbuseIPDB | Shodan | Pulsedive ]
        │                                                     │
        │ 3. Formats Scan Data into Brief Report ◄────────────┘
        │
        ├──► 4. Dispatches Report ─► [ OpenRouter API (Free LLM) ]
        │                                         │
        │ 5. Returns AI Verdict ◄─────────────────┘
        ▼
[ Final Scan Report + AI Verdict Delivered to Telegram ]
```

## 📋 Prerequisites

Before running **ThreatCheckerBot**, ensure your system meets the following requirements:

* 🐍 **Python 3.14** (or Python 3.10+)
* 🐳 **Docker Desktop for Windows** (installed and running)
* 🔑 **Required API Keys**:
  * **Telegram Bot Token** (obtained from [@BotFather](https://t.me/BotFather))
  * **OpenRouter API Key** (for AI report assessment)
  * **Threat Intelligence API Keys** (*VirusTotal, AbuseIPDB, Shodan, Pulsedive, URLScan.io*, etc.)

---

## 🚀 Getting Started & Setup

You do **not** need to manually clone or download the entire repository. The file downloading, integrity checking, environment configuration, and container deployment are handled automatically by `startup_script.py`.

### 1. Download the Startup Script
Download **only** the `startup_script.py` file from this repository to your local computer.

### 2. Run the Script
Open your terminal or command prompt and execute:

```bash
python startup_script.py
```

Let the script download all the necessary project files to your computer.

### 3. Fill the `vars.env` file with your API Keys
Open the `vars.env` file with any text editor of your choice and replace all `insert_your_api_key_here` with your own API Keys:

<p align="center">
<img width="920" height="376" alt="image" src="https://github.com/user-attachments/assets/ba510222-90af-489c-8778-73c8986923b7" />
</p>

### 4. Re-run the `startup_script.py` file
Open your terminal or command prompt and execute:

```bash
python startup_script.py
```

The script will check all the files and then start building the conteinerized app:
<p align="center">
<img width="786" height="241" alt="image" src="https://github.com/user-attachments/assets/87342813-27be-4919-bb5e-637b0d9ce68d" />
</p>

