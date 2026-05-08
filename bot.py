import requests
import time
import random
import os
import threading
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ================= CONFIG =================
CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

BINANCE_KEYS = [
    os.getenv("BINANCE_API_KEY_1"),
    os.getenv("BINANCE_API_KEY_2"),
    os.getenv("BINANCE_API_KEY_3"),
    os.getenv("BINANCE_API_KEY_4")
]

BINANCE_KEYS = [x for x in BINANCE_KEYS if x]

POST_INTERVAL = 10800
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)

@app.route("/")
def home():
    return "Mixed Style Binance Bot Running 🚀"

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

# ================= POST GENERATOR =================
def generate_post(used_symbols):

    data = get_market_data()

    if not data:
        return "Market unavailable"

    available = [
        s for s in list(data.keys())
        if s not in used_symbols
    ]

    if not available:
        available = list(data.keys())

    symbol = random.choice(available)

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

    # ================= SHORT STYLE =================
    short_post = f"""
🚨 Smart money seems active around ${symbol} lately.

${symbol} moved {change}% in the last 24h and is currently trading near ${price}.

Volatility is slowly returning and traders are becoming emotional again.

Most people react after the move already happens.

{symbol}
"""

    # ================= LONG STYLE =================
    mood = (
        "bullish"
        if change > 0
        else "bearish"
    )

    direction = (
        "holding strong"
        if change > 0
        else "still looking weak"
    )

    long_post = f"""
A lot of traders are still underestimating ${symbol} right now.

${symbol} is currently trading near ${price} after moving {change}% in the last 24 hours and still looks {direction} short term.

It feels like liquidity conditions are improving again while most traders remain extremely {mood} emotionally.

Usually that’s when bigger moves begin.

Risk management still matters the most.

{symbol}
"""

    # ================= NEWS STYLE =================
    news_post = f"""
📢 Market sentiment around ${symbol} has started changing again.

After a {change}% move in the last 24 hours, traders are watching closely to see whether momentum continues or fades near current levels.

Price is currently trading around ${price}, and volatility has been increasing across the market recently.

A lot of traders still seem uncertain about the next major direction.

{symbol}
"""

    # ================= PSYCHOLOGY STYLE =================
    psychology_post = f"""
The interesting thing about crypto markets is how quickly sentiment changes.

Just a few days ago people were extremely fearful, and now traders are suddenly becoming optimistic again around ${symbol}.

${symbol} is trading near ${price} after moving {change}% recently.

Most traders focus too much on short term candles and ignore overall market psychology.

{symbol}
"""

    # ================= RANDOM STYLE =================
    styles = [
        short_post,
        long_post,
        news_post,
        psychology_post
    ]

    return random.choice(styles).strip()

# ================= BINANCE POST =================
def post_to_binance(content, api_key):

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

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": message
        })

    except Exception:
        pass

# ================= MAIN LOOP =================
def run_bot():

    while True:

        try:

            print("Generating mixed human posts...")

            used_symbols = []

            for index, key in enumerate(BINANCE_KEYS):

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
            print("MAIN ERROR:", e)

        print("Sleeping...")

        time.sleep(POST_INTERVAL)

# ================= START =================
threading.Thread(target=run_bot).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
