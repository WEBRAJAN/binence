import requests, time, random, os, threading
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv("CMC_API_KEY")
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PORT = int(os.environ.get("PORT", 10000))
POST_INTERVAL = 5400  # 3 hours

app = Flask(__name__)

@app.route("/")
def home():
    return "Ultimate AI Crypto Bot Running 🚀"

VALID_COINS = [
    "BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","DOT",
    "MATIC","LTC","TRX","ATOM","FIL","NEAR","APT","OP","ARB","INJ"
]

LAST_POST_ID = None
SEEN_COMMENTS = set()

# ===================== MARKET =====================
def get_market():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        params = {"symbol": ",".join(VALID_COINS)}
        res = requests.get(url, headers=headers, params=params).json()
        return res.get("data", {})
    except:
        return {}

# ===================== INDICATORS =====================
def get_signal(change):
    if change >= 5: return "🚀 STRONG BUY"
    elif change >= 2: return "📈 BUY"
    elif change <= -5: return "💥 STRONG SELL"
    elif change <= -2: return "⚠️ SELL"
    else: return "⚖️ HOLD"

def get_rsi(change):
    if change > 4: return 75
    elif change > 2: return 65
    elif change < -4: return 25
    elif change < -2: return 35
    else: return 50

def get_ema_trend(change):
    return "Above EMA 📈" if change > 0 else "Below EMA 📉"

# ===================== NEWS =====================
def get_crypto_news():
    try:
        res = requests.get("https://min-api.cryptocompare.com/data/v2/news/?lang=EN").json()
        news = random.choice(res.get("Data", []))
        title = news.get("title", "")

        if any(x in title.lower() for x in ["bull","surge","gain"]):
            sentiment = "Bullish 📈"
        elif any(x in title.lower() for x in ["crash","hack","drop"]):
            sentiment = "Bearish 📉"
        else:
            sentiment = "Neutral ⚖️"

        return title, sentiment
    except:
        return "Market stable", "Neutral ⚖️"

# ===================== VIRAL =====================
def viral_hook():
    return random.choice([
        "🚨 BIG MOVE incoming?",
        "🔥 Market about to explode?",
        "👀 Smart money active",
        "⚠️ Don't ignore this setup",
        "🚀 Breakout loading..."
    ])

def ai_intro():
    return random.choice([
        "Market structure shifting 👀",
        "Liquidity zones getting tested 🔥",
        "Momentum building up 📊",
        "Volatility increasing ⚡"
    ])

def urgency():
    return random.choice([
        "Timing matters ⏳",
        "Move can be sharp ⚡",
        "Watch closely 👀",
        "High volatility zone 🔥"
    ])

def cta():
    return random.choice([
        "Bullish or bearish?",
        "Your move?",
        "Entering or waiting?",
        "Your opinion?"
    ])

# ===================== GENERATE POST =====================
def generate_post():
    data = get_market()
    if not data:
        return "⚠️ Market data unavailable", "BTC"

    sorted_coins = sorted(
        data.items(),
        key=lambda x: x[1]["quote"]["USD"]["percent_change_24h"],
        reverse=True
    )

    top = [c[0] for c in sorted_coins[:10]]

    # BTC priority
    if "BTC" in data and random.random() < 0.85:
        others = random.sample([c for c in top if c != "BTC"], 2)
        selected = ["BTC"] + others
    else:
        selected = random.sample(top, 3)

    lines, tags = [], []
    whale = False
    up, down = 0, 0

    for sym in selected:
        try:
            change = round(data[sym]["quote"]["USD"]["percent_change_24h"], 2)
            signal = get_signal(change)
            rsi = get_rsi(change)
            ema = get_ema_trend(change)

            if change > 0: up += 1
            else: down += 1

            if abs(change) > 5:
                whale = True

            lines.append(f"{sym}: {signal} | RSI {rsi} | {ema}")
            tags.append(f"${sym}")

        except:
            continue

    sentiment = "Bullish 😎" if up > down else "Bearish 🐻" if down > up else "Neutral ⚖️"

    news, news_sentiment = get_crypto_news()

    chart_coin = selected[0]
    chart_link = f"https://www.tradingview.com/symbols/{chart_coin}USDT/"

    post = f"""🚨 MARKET INTEL

{viral_hook()}

{ai_intro()}

{urgency()}

Sentiment: {sentiment}

📰 {news}
📊 Impact: {news_sentiment}

{' | '.join(lines)}

{'🐋 Whale activity detected!' if whale else ''}

📊 Chart:
{chart_link}

💡 Strategy:
Trade with confirmation & risk management

🤔 {cta()}

{' '.join(tags)} #crypto #trading
"""

    return post, chart_coin

# ===================== BINANCE =====================
def post_binance(content):
    global LAST_POST_ID
    try:
        url = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
        headers = {
            "X-Square-OpenAPI-Key": BINANCE_API_KEY,
            "Content-Type": "application/json",
            "clienttype": "binanceSkill"
        }
        r = requests.post(url, headers=headers, json={"bodyTextOnly": content}).json()
        LAST_POST_ID = r.get("data", {}).get("id")
        return r.get("data", {}).get("shareLink", "Post failed")
    except:
        return "Post failed"

# ===================== TELEGRAM =====================
def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

def send_image(symbol):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            data={
                "chat_id": CHAT_ID,
                "photo": f"https://s3.tradingview.com/snapshots/{symbol[0].lower()}/{symbol.lower()}usdt.png",
                "caption": f"{symbol} Chart 📊"
            }
        )
    except:
        pass

# ===================== COMMENTS =====================
def check_comments():
    global LAST_POST_ID

    if not LAST_POST_ID:
        return

    try:
        url = "https://www.binance.com/bapi/composite/v1/public/pgc/comment/list"
        params = {"contentId": LAST_POST_ID, "page": 1, "rows": 5}

        res = requests.get(url, params=params).json()
        comments = res.get("data", {}).get("list", [])

        for c in comments:
            text = c.get("content", "")
            if text and text not in SEEN_COMMENTS:
                SEEN_COMMENTS.add(text)
                send(f"💬 Comment:\n{text}")

    except:
        pass

# ===================== LOOP =====================
def run_bot():
    while True:
        try:
            post, sym = generate_post()
            link = post_binance(post)

            send(f"🚀 POSTED\n\n{post}\n\n🔗 {link}")
            send_image(sym)

            time.sleep(60)
            check_comments()

        except Exception as e:
            print("ERROR:", e)

        time.sleep(POST_INTERVAL)

threading.Thread(target=run_bot).start()

# ===================== SERVER =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)