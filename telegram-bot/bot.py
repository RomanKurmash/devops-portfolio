from flask import Flask, request, jsonify
import requests
import os
import logging

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOT_TOKEN = "8422673774:AAEAnEm-aQmsMncyuUPPIt081vbasiJvZ_0"
CHAT_ID = "874334948"
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/alert', methods=['POST'])
def alert():
    try:
        data = request.json
        if not data:
            logger.error("No JSON data received")
            return jsonify({"status": "error", "message": "No data"}), 400
        
        alerts = data.get('alerts', [])
        logger.info(f"Received {len(alerts)} alerts")
        
        for alert in alerts:
            status = alert.get('status', 'firing')
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            service = labels.get('service', labels.get('job', 'unknown'))
            severity = labels.get('severity', 'warning')
            summary = annotations.get('summary', 'No summary')
            description = annotations.get('description', 'No description')
            
            if status == 'firing':
                message = f"🚨 ALERT: {service}\n🔴 {summary}\n📝 {description}\n⚡ {severity.upper()}"
            else:
                message = f"✅ RESOLVED: {service}\n🟢 {summary}"
            
            # Send to Telegram
            payload = {
                'chat_id': CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(TELEGRAM_URL, json=payload, timeout=10)
            logger.info(f"Telegram response: {response.status_code}")
            
        return jsonify({"status": "success"})
    
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Telegram bot server...")
    app.run(host='0.0.0.0', port=8080, debug=False)