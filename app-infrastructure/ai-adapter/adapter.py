import os
import time
import json
import httpx
import asyncio
from dotenv import load_dotenv

load_dotenv()

LOKI_URL = os.getenv("LOKI_URL", "http://loki:3100/loki/api/v1/query_range")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
ALERTMANAGER_URL = os.getenv("ALERTMANAGER_URL", "http://alertmanager:9093/api/v2/alerts")
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "60"))
LOKI_QUERY = os.getenv("LOKI_QUERY", '{container=~"wordpress-app|nginx-proxy"}')
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")

async def fetch_logs(client, url, query, start_ns, end_ns):
    print(f"Fetching logs from Loki for query: {query}")
    params = {
        "query": query,
        "start": str(int(start_ns)),
        "end": str(int(end_ns)),
        "limit": 1000
    }
    try:
        response = await client.get(url, params=params, timeout=10.0)
        print(f"Loki responded with status code: {response.status_code}")
        if response.status_code != 200:
            return []
        logs = []
        data = response.json().get("data", {})
        results = data.get("result", [])
        for res in results:
            stream = res.get("stream", {})
            container = stream.get("container", "unknown")
            for val in res.get("values", []):
                logs.append(f"[{container}] {val[1]}")
        print(f"Fetched {len(logs)} log lines.")
        return logs
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []

async def analyze_logs(client, url, model, logs_text):
    print("Sending logs to Ollama for analysis...")
    prompt = f"""Analyze these system logs for security anomalies, malicious activity, hacking attempts, or critical errors:

{logs_text}

Return a JSON object with the following fields:
- risk_score: an integer between 0 and 10 (0 means perfectly safe, 10 means active critical security breach)
- threat_found: boolean indicating if any security threat or anomaly was found
- affected_container: the name of the container that is targeted or generating the logs (e.g., wordpress-app, nginx-proxy)
- problem_type: choose the most appropriate category from the following 10 types:
  1. "SQL Injection"
  2. "Remote Code Execution"
  3. "Brute-force Attack"
  4. "Cross-Site Scripting"
  5. "Unauthorized Access"
  6. "Database Connection Failure"
  7. "Out of Memory Crash"
  8. "High Error Rate"
  9. "Service Timeout"
  10. "Resource Exhaustion"
- description: a concise summary of what was found in the logs
- recommendations: key steps to mitigate the issue

Example JSON:
{{
  "risk_score": 8,
  "threat_found": true,
  "affected_container": "nginx-proxy",
  "problem_type": "SQL Injection",
  "description": "Multiple failed login attempts to /wp-login.php from IP 192.168.1.50 indicating brute-force attack",
  "recommendations": "Block IP 192.168.1.50 using firewall or fail2ban"
}}"""

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    try:
        response = await client.post(f"{url}/api/generate", json=payload, timeout=60.0)
        print(f"Ollama responded with status code: {response.status_code}")
        if response.status_code != 200:
            return None
        result = json.loads(response.json().get("response", "{}"))
        print(f"Analysis result: {result}")
        return result
    except Exception as e:
        print(f"Error analyzing logs: {e}")
        return None

async def send_alert(client, url, analysis):
    print(f"Sending alert to Alertmanager for risk score {analysis.get('risk_score')}")
    risk_score = int(analysis.get("risk_score", 7))
    severity = "critical" if risk_score >= 8 else "warning"
    problem_type = str(analysis.get("problem_type", "SecOps AI Anomaly Detected"))
    payload = [
        {
            "labels": {
                "alertname": "SecOpsAIAnomalyDetected",
                "severity": severity,
                "risk_score": str(risk_score),
                "container": str(analysis.get("affected_container", "unknown")),
                "problem_type": problem_type
            },
            "annotations": {
                "summary": f"SecOps AI: {problem_type}",
                "description": str(analysis.get("description", "No description provided")),
                "recommendations": str(analysis.get("recommendations", "No recommendations provided"))
            },
            "generatorURL": "http://ai-adapter:8082"
        }
    ]
    try:
        response = await client.post(url, json=payload, timeout=10.0)
        print(f"Alertmanager responded with status code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending alert: {e}")
        return False

async def main():
    print("SecOps AI Adapter service started.")
    async with httpx.AsyncClient() as client:
        last_run_time = time.time() - SCAN_INTERVAL
        while True:
            await asyncio.sleep(SCAN_INTERVAL)
            current_time = time.time()
            start_ns = last_run_time * 1e9
            end_ns = current_time * 1e9
            print(f"Running scan loop for time range: {start_ns} to {end_ns}")
            try:
                logs = await fetch_logs(client, LOKI_URL, LOKI_QUERY, start_ns, end_ns)
                if logs:
                    logs_text = "\n".join(logs[-100:])
                    analysis = await analyze_logs(client, OLLAMA_URL, LLM_MODEL, logs_text)
                    if analysis and analysis.get("threat_found") and int(analysis.get("risk_score", 0)) >= 7:
                        await send_alert(client, ALERTMANAGER_URL, analysis)
                else:
                    print("No logs fetched in this interval.")
                last_run_time = current_time
            except Exception as e:
                print(f"Error in main scan loop: {e}")

if __name__ == "__main__":
    asyncio.run(main())
