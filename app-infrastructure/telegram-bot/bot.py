import os
import asyncio
import httpx
import logging
import html
import json
from datetime import datetime
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOKI_URL = os.getenv("LOKI_URL")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

if not BOT_TOKEN or not CHAT_ID:
    logger.error("Error: Telegram credentials not found in env.")
else:
    logger.info(f"Telegram Bot initialized. Chat ID: {CHAT_ID}")

active_alerts = set()

def safe_escape(value):
    if isinstance(value, list):
        value = "\n".join(f"- {item}" for item in value)
    return html.escape(str(value))

async def send_to_telegram(message: str):
    async with httpx.AsyncClient() as client:
        try:
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
            response = await client.post(TELEGRAM_URL, json=payload, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Telegram error: {response.text}")
        except Exception as e:
            logger.error(f"Telegram connection error: {e}")

async def get_loki_logs(container_name: str):
    if not LOKI_URL:
        return "LOKI_URL not configured."
    query = f'{{container="{container_name}"}} |~ "(?i)error|fail|exception|critical|fatal"'
    async with httpx.AsyncClient() as client:
        try:
            params = {"query": query, "limit": 10, "direction": "backward"}
            response = await client.get(LOKI_URL, params=params, timeout=5.0)
            results = response.json().get("data", {}).get("result", [])
            if not results:
                params["query"] = f'{{container="{container_name}"}}'
                response = await client.get(LOKI_URL, params=params)
                results = response.json().get("data", {}).get("result", [])
            lines = []
            for res in results:
                for val in res.get("values", []):
                    safe_log = html.escape(val[1][:200])
                    lines.append(f"<code>{safe_log}</code>")
            return "\n".join(lines) if lines else "No logs found in Loki."
        except Exception as e:
            return f"Failed to fetch logs: {html.escape(str(e))}"

async def analyze_with_llm(container_name: str, logs_text: str):
    if not OLLAMA_URL or not logs_text or "No logs found" in logs_text:
        return None
    clean_logs = logs_text.replace("<code>", "").replace("</code>", "")
    prompt = f"""Analyze the following container logs and identify the root cause of the alert/failure.
Container: {container_name}
Logs:
{clean_logs}

Return a JSON object with the following fields:
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
- extended_summary: a concise but detailed explanation of what happened based on the logs
- recommendations: what should be done to fix this issue
"""
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60.0)
            if response.status_code == 200:
                result = json.loads(response.json().get("response", "{}"))
                return result
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
        return None

async def heartbeat_loop():
    while True:
        await asyncio.sleep(7200)
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        await send_to_telegram(f"🛡 <b>Heartbeat [{now}]</b>\nВсі системи працюють у штатному режимі.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_loop())

@app.post("/alert")
async def handle_alert(request: Request):
    try:
        data = await request.json()
        alerts = data if isinstance(data, list) else data.get('alerts', [])
        for alert in alerts:
            status = alert.get('status', 'firing')
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            alert_name = safe_escape(labels.get('alertname', 'Unknown Alert'))
            
            if alert_name == "Watchdog":
                continue
                
            container = safe_escape(labels.get('container', labels.get('service', 'unknown')))
            severity = safe_escape(labels.get('severity', 'warning'))
            risk_score = safe_escape(labels.get('risk_score', '0'))
            
            if status == 'firing':
                active_alerts.add(alert_name)
                logs = await get_loki_logs(container)
                
                if alert_name == "SecOpsAIAnomalyDetected":
                    problem_type = safe_escape(labels.get('problem_type', 'AI Anomaly Detected'))
                    description = safe_escape(annotations.get('description', 'No description provided'))
                    recommendations = safe_escape(annotations.get('recommendations', 'No recommendations provided'))
                    
                    message = (
                        f"🚨 <b>[SecOps AI] {problem_type}</b>\n"
                        f"📦 <b>Container:</b> <code>{container}</code>\n"
                        f"⚠️ <b>Severity:</b> {severity} (Risk: {risk_score}/10)\n\n"
                        f"📖 <b>Extended Summary:</b>\n{description}\n\n"
                        f"💡 <b>Mitigation Steps:</b>\n{recommendations}"
                    )
                else:
                    ai_analysis = await analyze_with_llm(container, logs)
                    if ai_analysis:
                        problem_type = safe_escape(ai_analysis.get('problem_type', 'System Anomaly'))
                        extended_summary = safe_escape(ai_analysis.get('extended_summary', 'No summary provided'))
                        recommendations = safe_escape(ai_analysis.get('recommendations', 'No recommendations provided'))
                        
                        message = (
                            f"🚨 <b>ALERT FIRING: {alert_name} ({problem_type})</b>\n"
                            f"📦 <b>Container:</b> <code>{container}</code>\n"
                            f"⚠️ <b>Severity:</b> {severity}\n\n"
                            f"📖 <b>Extended Summary:</b>\n{extended_summary}\n\n"
                            f"💡 <b>Mitigation Steps:</b>\n{recommendations}\n\n"
                            f"📄 <b>Last Logs:</b>\n{logs}"
                        )
                    else:
                        summary = safe_escape(annotations.get('summary', 'No summary'))
                        message = (
                            f"🚨 <b>ALERT FIRING: {alert_name}</b>\n"
                            f"📦 <b>Container:</b> <code>{container}</code>\n"
                            f"⚠️ <b>Severity:</b> {severity}\n"
                            f"📝 <b>Summary:</b> {summary}\n\n"
                            f"📄 <b>Last Logs:</b>\n{logs}"
                        )
            else:
                active_alerts.discard(alert_name)
                message = f"✅ <b>RESOLVED: {alert_name}</b>\n📦 <b>Container:</b> <code>{container}</code>\n🟢 Система стабілізована."
                
            await send_to_telegram(message)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)