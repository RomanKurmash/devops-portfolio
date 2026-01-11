import os
import asyncio
import httpx
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv()

# Ініціалізація
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

# Конфіг з ENV
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
LOKI_URL = os.getenv("LOKI_URL")
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

if not BOT_TOKEN:
    logger.error("❌ КРИТИЧНО: TELEGRAM_BOT_TOKEN не знайдено!")
else:
    logger.info(f"✅ Токен завантажено (перші 5 знаків): {BOT_TOKEN[:5]}...")

if not CHAT_ID:
    logger.error("❌ КРИТИЧНО: CHAT_ID не знайдено!")
else:
    logger.info(f"✅ Chat ID знайдено: {CHAT_ID}")

# Глобальна змінна для відстеження активних алертів
active_alerts = set()

async def send_to_telegram(message: str):
    async with httpx.AsyncClient() as client:
        try:
            payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
            await client.post(TELEGRAM_URL, json=payload, timeout=10.0)
        except Exception as e:
            logger.error(f"Telegram Send Error: {e}")

async def get_loki_logs(container_name: str):
    """Скрейпінг 'потрібних' логів (помилок) або останніх рядків"""
    # Запит шукає ключові слова error, fail, critical, або просто бере останні
    # Ми додаємо фільтр |~ "error|fail|exception|fatal"
    query = f'{{container="{container_name}"}} |~ "(?i)error|fail|exception|critical|fatal"'
    
    async with httpx.AsyncClient() as client:
        try:
            params = {
                "query": query,
                "limit": 20,
                "direction": "backward"
            }
            response = await client.get(LOKI_URL, params=params, timeout=5.0)
            if response.status_code == 200:
                results = response.json().get("data", {}).get("result", [])
                if not results:
                    # Якщо фільтр помилок нічого не дав, беремо просто останні 10 рядків
                    logger.info(f"No specific errors for {container_name}, fetching general logs")
                    params["query"] = f'{{container="{container_name}"}}'
                    params["limit"] = 10
                    response = await client.get(LOKI_URL, params=params)
                    results = response.json().get("data", {}).get("result", [])

                lines = []
                for res in results:
                    for val in res.get("values", []):
                        lines.append(f"<code>{val[1]}</code>")
                return "\n".join(lines) if lines else "Логи відсутні"
        except Exception as e:
            return f"Помилка зв'язку з Loki: {e}"

# --- Background Task: Heartbeat ---
async def heartbeat_loop():
    """Раз на годину каже, що система жива, якщо немає алертів"""
    while True:
        await asyncio.sleep(3600) # 1 година
        if not active_alerts:
            now = datetime.now().strftime("%H:%M:%S")
            await send_to_telegram(f"🛡 <b>Heartbeat [{now}]</b>\nСистема моніторингу працює в штатному режимі. Аномалій не виявлено.")
        else:
            logger.info("Heartbeat skipped: active alerts present")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_loop())

# --- Webhook Endpoint ---
@app.post("/alert")
async def handle_alert(request: Request):
    data = await request.json()
    alerts = data.get('alerts', [])
    
    for alert in alerts:
        status = alert.get('status')
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        # Витягуємо назву контейнера (лейбл 'container' має бути в алерт-рулзах)
        container = labels.get('container', labels.get('service', 'unknown'))
        alert_name = labels.get('alertname', 'Unknown Alert')
        
        if status == 'firing':
            active_alerts.add(alert_name)
            # Скрейпимо логи
            logs = await get_loki_logs(container)
            
            message = (
                f"🚨 <b>ALERT FIRING: {alert_name}</b>\n"
                f"📦 <b>Container:</b> {container}\n"
                f"📝 <b>Summary:</b> {annotations.get('summary')}\n\n"
                f"📄 <b>Relevant Logs:</b>\n{logs}"
            )
        else:
            active_alerts.discard(alert_name)
            message = f"✅ <b>RESOLVED: {alert_name}</b>\n📦 <b>Container:</b> {container}\n🟢 Система стабілізована."

        await send_to_telegram(message)
    
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)