# SearXNG Local Web-Search Service (Docker Compose)

This directory contains the self-hosted, privacy-respecting **SearXNG** metasearch engine configured for local execution via **Docker Compose** on Windows. It is pre-configured for future integration with the **DocuChat AI RAG System** and local **Ollama** LLMs as a real-time web retrieval tool.

---

## 1. Architecture & Service Topology

| Service | Container Name | Image | Port Binding | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **SearXNG Core** | `searxng-core` | `docker.io/searxng/searxng:latest` | `127.0.0.1:8080:8080` | Web Search UI & JSON API Engine |
| **Valkey** | `searxng-valkey` | `docker.io/valkey/valkey:9-alpine` | Internal (Port 6379) | High-performance cache & state store |

### Security & Isolation Guarantees
* **Localhost Binding Only (`127.0.0.1`):** The web service binds exclusively to loopback interface `127.0.0.1:8080`, preventing unintentional exposure to your local area network (LAN) or public Wi-Fi.
* **JSON Output Enabled:** Configured with `formats: [html, json]` in `core-config/settings.yml` to allow direct programmatic consumption by Python backend agents.
* **Limiter Disabled (`limiter: false`):** Prevents automated AI queries and multi-query expansions from triggering bot-protection HTTP 429 rate limits.
* **Secret Isolation:** The cryptographic session secret is loaded dynamically from `.env` (which is excluded in `.gitignore`) and is never committed to Git.

---

## 2. Directory Structure

```
searxng/
├── core-config/
│   └── settings.yml     # Custom SearXNG settings (JSON enabled, Valkey cache, limiter off)
├── .env                 # Active local environment variables & strong secret (git-ignored)
├── .env.example         # Template with placeholder instructions
├── .gitignore           # Excludes .env, core-data/, and valkey-data/
├── docker-compose.yml   # Multi-container orchestration (SearXNG core + Valkey)
└── README.md            # Operational instructions and troubleshooting
```

---

## 3. Prerequisites & Validation (Windows PowerShell)

Before executing containers, verify that **Docker Desktop** is running:

```powershell
# Verify Docker daemon status
docker info --format 'ServerVersion: {{.ServerVersion}}, OperatingSystem: {{.OperatingSystem}}'
```

If Docker returns an error, launch Docker Desktop from your Windows Start Menu and ensure the Linux WSL2 engine has finished initializing.

---

## 4. Secret Key Management

The local `.env` has already been provisioned with a cryptographically secure 256-bit (64-character hex) secret.

To regenerate or rotate the secret at any time, run either of the following commands in PowerShell:

### Option A: Using Python (Recommended)
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### Option B: Using Native PowerShell .NET
```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

Then update `SEARXNG_SECRET` inside `searxng/.env`.

---

## 5. Container Lifecycle Commands (Windows PowerShell)

All commands must be executed from inside the `searxng` directory:

```powershell
# Navigate into the SearXNG setup folder
cd "d:\AMD Files\Projects\Git rag\searxng"
```

### A. Start the Services (Detached Mode)
```powershell
docker compose up -d
```
*Docker will pull the official `searxng/searxng:latest` and `valkey/valkey:9-alpine` images and start both containers in the background.*

### B. Inspect Service Health & Container Status
```powershell
# List container status and port mappings
docker compose ps

# View real-time resource utilization (CPU, RAM, Network I/O)
docker stats --no-stream searxng-core searxng-valkey
```

### C. View Streaming Logs
```powershell
# Follow logs for all services
docker compose logs -f

# Follow logs specifically for SearXNG Core
docker compose logs core -f --tail 100

# Follow logs for Valkey cache
docker compose logs valkey -f
```

### D. Restart Services (e.g. after modifying settings.yml)
```powershell
docker compose restart
```

### E. Stop the Services
```powershell
# Stop and remove containers and network (preserves volumes)
docker compose down

# Stop containers without removing them
docker compose stop

# Restart stopped containers
docker compose start

# Full cleanup (removes containers, networks, and persistent data volumes)
docker compose down -v
```

---

## 6. Verifying JSON Search Output

Once the containers are running (`docker compose up -d`), test the service:

### 1. Browser Test (HTML UI)
Open your web browser and navigate to:
```
http://localhost:8080
```

### 2. JSON API Search Test (PowerShell)
Execute this command to verify that the JSON output format functions correctly:

```powershell
# Perform a query for "ollama local llm" and parse the JSON results
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8080/search?q=ollama+local+llm&format=json"

# Print metadata
Write-Host "Query: $($response.query)"
Write-Host "Total Results Returned: $($response.results.Count)"

# Display top 3 search results
$response.results | Select-Object -First 3 title, url, engine | Format-Table -AutoSize
```

### 3. Direct JSON Test URL
```
http://127.0.0.1:8080/search?q=fastapi+rag&format=json
```

---

## 7. Future DocuChat AI Python Integration Snippet

When integrating SearXNG as a real-time web search tool in `backend/retrieval/web_search.py` or `backend/tools/`, use the following asynchronous Python pattern:

```python
import httpx
from typing import List, Dict, Any

async def search_searxng(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Query local SearXNG instance for real-time web search results.
    """
    url = "http://127.0.0.1:8080/search"
    params = {
        "q": query,
        "format": "json",
        "categories": "general",
        "language": "en"
    }
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
    results = []
    for item in data.get("results", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", ""),
            "engine": item.get("engine", "")
        })
    return results
```

---

## 8. Troubleshooting Guide

### Issue 1: Port 8080 is Already in Use
* **Symptom:** `Error response from daemon: Ports are not available: exposing port TCP 127.0.0.1:8080 -> 0.0.0.0:0: listen tcp 127.0.0.1:8080: bind: address already in use`
* **Diagnosis (PowerShell):**
  ```powershell
  Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object LocalAddress, LocalPort, OwningProcess
  ```
* **Solution:** If another application is using port 8080, edit `SEARXNG_PORT` in `searxng/.env`:
  ```env
  SEARXNG_PORT=8088
  ```
  Then access the service at `http://127.0.0.1:8088`.

### Issue 2: Docker Desktop Engine Not Responding
* **Symptom:** `error during connect: Get "http://%2F%2F.%2Fpipe%2Fdocker_engine/...": open //./pipe/docker_engine: The system cannot find the file specified.`
* **Solution:**
  1. Open the Docker Desktop application on Windows.
  2. Wait until the whale icon in the Windows taskbar system tray stops animating and indicates "Engine running".
  3. Ensure WSL2 integration is enabled under Docker Desktop Settings -> Resources -> WSL Integration.

### Issue 3: Rate Limiting / 429 Too Many Requests
* **Symptom:** API calls return HTTP status `429 Too Many Requests`.
* **Solution:** Confirm that `limiter: false` is set in `core-config/settings.yml` under `server:`. Restart the container stack with `docker compose restart`.

### Issue 4: Empty Search Results from Specific Search Engines
* **Symptom:** SearXNG returns 0 results or `results: []`.
* **Diagnosis:** Upstream engines (such as Google or DuckDuckGo) may occasionally rate limit or present CAPTCHAs to high-frequency IP requests.
* **Solution:** Check engine status at `http://127.0.0.1:8080/stats` in your browser. SearXNG aggregates across multiple engines (DuckDuckGo, Wikipedia, Bing, Brave, etc.), so failure of an individual engine does not compromise the metasearch query.
