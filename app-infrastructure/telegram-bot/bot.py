import os
import asyncio
import httpx
import logging
import html
from datetime import datetime
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

# Конфігурація з .env
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOKI_URL = os.getenv("LOKI_URL")
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

if not BOT_TOKEN or not CHAT_ID:
    logger.error("❌ КРИТИЧНО: Токени не знайдені в .env!")
else:
    logger.info(f"✅ Бот запущений. Chat ID: {CHAT_ID}")

active_alerts = set()

async def send_to_telegram(message: str):
    """Надсилає екрановане повідомлення в Telegram"""
    async with httpx.AsyncClient() as client:
        try:
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
            response = await client.post(TELEGRAM_URL, json=payload, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Telegram error: {response.text}")
        except Exception as e:
            logger.error(f"Telegram connection error: {e}")

async def get_loki_logs(container_name: str):
    """Отримує логи з Loki та безпечно екранує їх для HTML"""
    if not LOKI_URL:
        return "LOKI_URL не налаштовано."

    # Спочатку шукаємо критичні помилки
    query = f'{{container="{container_name}"}} |~ "(?i)error|fail|exception|critical|fatal"'
    
    async with httpx.AsyncClient() as client:
        try:
            params = {"query": query, "limit": 10, "direction": "backward"}
            response = await client.get(LOKI_URL, params=params, timeout=5.0)
            results = response.json().get("data", {}).get("result", [])
            
            if not results:
                # Якщо помилок немає, беремо просто останні рядки
                params["query"] = f'{{container="{container_name}"}}'
                response = await client.get(LOKI_URL, params=params)
                results = response.json().get("data", {}).get("result", [])

            lines = []
            for res in results:
                for val in res.get("values", []):
                    # html.escape захищає від помилок "can't parse entities"
                    safe_log = html.escape(val[1][:200]) 
                    lines.append(f"<code>{safe_log}</code>")
            
            return "\n".join(lines) if lines else "<i>Логи в Loki відсутні</i>"
        except Exception as e:
            return f"<i>Не вдалося отримати логи: {html.escape(str(e))}</i>"

async def heartbeat_loop():
    """Надсилає статус системи раз на годину"""
    while True:
        await asyncio.sleep(3600)
        if not active_alerts:
            now = datetime.now().strftime("%H:%M:%S")
            await send_to_telegram(f"🛡 <b>Heartbeat [{now}]</b>\nСистема моніторингу в нормі.")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_loop())

@app.post("/alert")
async def handle_alert(request: Request):
    """Обробка вебхуків від Alertmanager"""
    try:
        data = await request.json()
        alerts = data if isinstance(data, list) else data.get('alerts', [])

        for alert in alerts:
            status = alert.get('status', 'firing')
            labels = alert.get('labels', {})
            # Екрануємо всі динамічні дані
            summary = html.escape(alert.get('annotations', {}).get('summary', 'No summary'))
            alert_name = html.escape(labels.get('alertname', 'Unknown Alert'))
            container = html.escape(labels.get('container', labels.get('service', 'unknown')))
            
            if status == 'firing':
                active_alerts.add(alert_name)
                logs = await get_loki_logs(container)
                message = (
                    f"🚨 <b>ALERT FIRING: {alert_name}</b>\n"
                    f"📦 <b>Container:</b> <code>{container}</code>\n"
                    f"📝 <b>Summary:</b> {summary}\n\n"
                    f"📄 <b>Last Logs:</b>\n{logs}"
                )
            else:
                active_alerts.discard(alert_name)
                message = f"✅ <b>RESOLVED: {alert_name}</b>\n📦 <b>Container:</b> {container}\n🟢 Система стабілізована."

            await send_to_telegram(message)
            
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)