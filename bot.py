import requests
import time
import random
import os
import threading
import google.generativeai as genai

from flask import Flask
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ================= CONFIG =================
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BINANCE_KEYS = [
    os.getenv("BINANCE_API_KEY_1"),
    os.getenv("BINANCE_API_KEY_2"),
    os.getenv("BINANCE_API_KEY_3"),
    os.getenv("BINANCE_API_KEY_4")
]

BINANCE_KEYS = [x for x in BINANCE_KEYS if x]

POST_INTERVAL = 10800
PORT = int(os.environ.get("PORT", 10000))

# ================= GEMINI =================
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# ================= FLASK =================
app = Flask(__name__)

@app.route("/")
def home():
    return "Gemini Binance Bot Running 🚀"

# ================= COINS =================
VALID_COINS = [
    "BTC","ETH","SOL","BNB","XRP",
    "DOGE","ADA","AVAX","LINK","DOT",
    "MATIC","LTC","TRX","ATOM","FIL",
    "APT","ARB","INJ","OP","SUI"
]

# ================= MARKET =================
def get_market_data():

    try:

        url = (
            "https://pro-api.coinmarketcap.com/"
            "v1/cryptocurrency/quotes/latest"
        )

        headers = {
            "X-CMC_PRO_API_KEY": CMC_API_KEY
        }

        params = {
            "symbol": ",".join(VALID_COINS)
        }

        response = requests.get(
            url,
            headers=headers,
            params=params
        )

        data = response.json()

        return data.get("data", {})

    except Exception as e:

        print("MARKET ERROR:", e)

        return {}

# ================= AI POST =================
def generate_ai_post(
    symbol,
    price,
    change
):

    prompt = f"""
Create a completely unique Binance Feed crypto post.

Rules:
- Human style writing
- Natural opinions
- Creator style
- Professional tone
- Different structure every time
- No hashtags
- No markdown
- No bullet points
- No repeated template
- 5 to 8 lines
- End only with coin name
- Mix psychology, market sentiment, volatility, trader behavior
- Make it look like a real crypto influencer wrote it

Coin: {symbol}
Price: {price}
24h Change: {change}%
"""

    try:

        response = model.generate_content(
            prompt
        )

        text = response.text.strip()

        return text

    except Exception as e:

        print("AI ERROR:", e)

        return (
            f"${symbol} is getting attention "
            f"after moving {change}% recently.\n\n"
            f"{symbol}"
        )

# ================= GENERATE POST =================
def generate_post(
    used_symbols
):

    data = get_market_data()

    if not data:
        return "Market unavailable"

    available = [
        s for s in list(data.keys())
        if s not in used_symbols
    ]

    if not available:
        available = list(data.keys())

    symbol = random.choice(
        available
    )

    used_symbols.append(symbol)

    try:

        price = round(
            data[symbol]["quote"]["USD"]["price"],
            2
        )

        change = round(
            data[symbol]["quote"]["USD"]["percent_change_24h"],
            2
        )

    except Exception:

        return "Data error"

    ai_post = generate_ai_post(
        symbol,
        price,
        change
    )

    return ai_post.strip()

# ================= BINANCE POST =================
def post_to_binance(
    content,
    api_key
):

    try:

        url = (
            "https://www.binance.com/"
            "bapi/composite/v1/public/pgc/openApi/content/add"
        )

        headers = {
            "X-Square-OpenAPI-Key": api_key,
            "Content-Type": "application/json",
            "clienttype": "binanceSkill"
        }

        payload = {
            "bodyTextOnly": content
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload
        )

        data = response.json()

        if data.get("success"):

            return (
                True,
                data.get("data", {}).get(
                    "shareLink",
                    "Posted"
                )
            )

        return False, str(data)

    except Exception as e:

        return False, str(e)

# ================= TELEGRAM =================
def send_telegram(message):

    try:

        url = (
            f"https://api.telegram.org/bot"
            f"{TELEGRAM_TOKEN}/sendMessage"
        )

        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            }
        )

    except Exception:
        pass

# ================= MAIN LOOP =================
def run_bot():

    while True:

        try:

            print(
                "Generating AI human posts..."
            )

            used_symbols = []

            for index, key in enumerate(
                BINANCE_KEYS
            ):

                post = generate_post(
                    used_symbols
                )

                post += (
                    f"\n\n🕒 "
                    f"{datetime.utcnow().strftime('%H:%M UTC')}"
                )

                success, result = post_to_binance(
                    post,
                    key
                )

                if success:

                    send_telegram(
                        f"🚀 POST SUCCESS ({index+1})\n\n"
                        f"{post}\n\n"
                        f"🔗 {result}"
                    )

                    print("POSTED")

                else:

                    send_telegram(
                        f"❌ POST FAILED ({index+1})\n\n"
                        f"{result}"
                    )

                    print("FAILED")

        except Exception as e:

            print(
                "MAIN ERROR:",
                e
            )

        print("Sleeping...")

        time.sleep(
            POST_INTERVAL
        )

# ================= START =================
threading.Thread(
    target=run_bot
).start()

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=PORT
    )
