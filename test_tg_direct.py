import urllib.request
import json
import time

bot_token = "8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U"
chat_id = "-5466215213"

def send_tg(text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            return json.loads(res.read().decode('utf-8'))
    except Exception as e:
        return {"ok": False, "error": str(e)}

print("Testing direct alert send to Telegram Group...")
res = send_tg("🚨 *TEST ALERT: Digital Twin Replay Alert System Active* 🚨\n\nCondition: `INDOOR_FILTER_CLOG`\nHealth: `65%`\nRUL: `600 Hours`")
print("Result:", res)
