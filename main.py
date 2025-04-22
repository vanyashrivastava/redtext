from flask import Flask, request
import requests
import os

app = Flask(__name__)

# ✅ Environment Variables Required:
# - GROUPME_BOT_ID
# - ANTHROPIC_API_KEY

GROUPME_BOT_ID = os.environ.get("GROUPME_BOT_ID")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# 🔍 Claude Message Analysis Function
def analyze_message_with_claude(text):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    prompt = f"""
You are a safety and empowerment assistant helping people navigate harmful, coercive, or threatening messages.

A person just received this message in a group chat:

"{text}"

Please:
1. Determine if the message should be **flagged** as harmful (coercive, threatening, emotionally manipulative, or hateful).
2. If it should be flagged, explain briefly **why it’s harmful**.
3. Suggest one action they can take next, using a friendly tone and emojis.
4. If the message is safe, respond only with: "SAFE"

Respond with only 2 short sentences and keep the tone supportive.
"""

    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 150,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['content'][0]['text'].strip()
        return content
    except Exception as e:
        print("❌ Claude API error:", e)
        print("Response:", response.text)
        return "error"

# 🌐 Flask Route: GroupMe Webhook
@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    text = data.get("text")
    sender_type = data.get("sender_type")

    print(f"Received: {text} from {sender_type}")

    if sender_type != "bot":
        result = analyze_message_with_claude(text)

        if result.lower() != "safe":
            print("🚨 Claude flagged message with feedback.")
            send_groupme_message("🚨 " + result)
        else:
            print("✅ Message passed Claude safety filter.")

    return "ok", 200

# 🏠 Health check
@app.route("/", methods=["GET"])
def home():
    return "✅ Flask app is running!", 200

# 📨 Send message to GroupMe
def send_groupme_message(message):
    url = "https://api.groupme.com/v3/bots/post"
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": message
    }

    print("📤 Sending to GroupMe...")
    response = requests.post(url, json=payload)
    print(f"GroupMe response: {response.status_code} - {response.text}")

# 🚀 Start the app
if __name__ == "__main__":
    print("Testing Claude filter:")
    print(analyze_message_with_claude("If you really cared, you'd send it."))
    app.run(host="0.0.0.0", port=81)
