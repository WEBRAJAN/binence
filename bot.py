import requests, time, random, os, threading
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

CMC_API_KEY = os.getenv("CMC_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 🔥 4 BINANCE KEYS (auto filter empty)
BINANCE_KEYS = [
    os.getenv("BINANCE_API_KEY_1"),
    os.getenv("BINANCE_API_KEY_2"),
    os.getenv("BINANCE_API_KEY_3"),
    os.getenv("BINANCE_API_KEY_4"),
]

BINANCE_KEYS = [k for k in BINANCE_KEYS if k]

PORT = int(os.environ.get("PORT", 10000))
POST_INTERVAL = 5400  # safer

app = Flask(__name__)

@app.route("/")
def home():
    return "Crypto Bot Running 🚀"

VALID_COINS = [
    "BTC","ETH","SOL","BNB","XRP","DOGE","ADA","AVAX","LINK","DOT",
    "MATIC","LTC","TRX","ATOM","FIL","NEAR","APT","OP","ARB","INJ"
]

LAST_POST_IDS = [None] * len(BINANCE_KEYS)
SEEN_COMMENTS = set()

# ================= MARKET =================
def get_market():
    try:
        url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": CMC_API_KEY}
        params = {"symbol": ",".join(VALID_COINS)}
        res = requests.get(url, headers=headers, params=params).json()
        return res.get("data", {})
    except:
        return {}

# ================= SIGNAL =================
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

def get_ema(change):
    return "Above EMA 📈" if change > 0 else "Below EMA 📉"

# ================= TEXT =================
def hook():
    return random.choice([
        "🚨 BIG MOVE incoming?",
        "🔥 Market about to explode?",
        "👀 Smart money active",
        "⚠️ Don't ignore this setup",
        "🚀 Breakout loading..."
    ])

def intro():
    return random.choice([
        "Market structure shifting 👀",
        "Liquidity zones getting tested 🔥",
        "Momentum building 📊",
        "Volatility increasing ⚡"
    ])

def cta():
    return random.choice([
        "Your move?",
        "Bullish or bearish?",
        "Entering or waiting?",
        "What do you think?"
    ])

# ================= POST =================
def generate_post():
    data = get_market()
    if not data:
        return "Market data unavailable", "BTC"

    coins = list(data.keys())
    selected = random.sample(coins, 3)

    lines, tags = [], []
    up, down = 0, 0

    for sym in selected:
        try:
            change = round(data[sym]["quote"]["USD"]["percent_change_24h"], 2)
            signal = get_signal(change)
            rsi = get_rsi(change)
            ema = get_ema(change)

            direction = "going up 📈" if change > 0 else "going down 📉"

            if change > 0: up += 1
            else: down += 1

            lines.append(f"{sym} ${sym} is {direction} | {signal} | RSI {rsi} | {ema}")
            tags.append(f"${sym}")

        except:
            continue

    sentiment = "Bullish 😎" if up > down else "Bearish 🐻"

    chart_coin = selected[0]
    chart = f"https://www.tradingview.com/symbols/{chart_coin}USDT/"

    final_tag = random.choice(tags)

    post = f"""🚨 MARKET INTEL

{hook()}

{intro()}

Sentiment: {sentiment}

{' | '.join(lines)}

📊 Chart:
{chart}

💡 Trade smart & manage risk

🤔 {cta()}

{final_tag} #crypto
"""

    return post, chart_coin

# ================= BINANCE =================
def post_binance(content, api_key, index):
    try:
        url = "https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add"
        headers = {
            "X-Square-OpenAPI-Key": api_key,
            "Content-Type": "application/json",
            "clienttype": "binanceSkill"
        }

        r = requests.post(url, headers=headers, json={"bodyTextOnly": content}).json()

        post_id = r.get("data", {}).get("id")
        if index < len(LAST_POST_IDS):
            LAST_POST_IDS[index] = post_id

        return r.get("data", {}).get("shareLink", "Post failed")

    except:
        return "Post failed"

# ================= TELEGRAM =================
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

# ================= COMMENTS =================
def check_comments(index):
    if index >= len(LAST_POST_IDS):
        return

    post_id = LAST_POST_IDS[index]
    if not post_id:
        return

    try:
        url = "https://www.binance.com/bapi/composite/v1/public/pgc/comment/list"
        params = {"contentId": post_id, "page": 1, "rows": 5}

        res = requests.get(url, params=params).json()
        comments = res.get("data", {}).get("list", [])

        for c in comments:
            text = c.get("content", "")
            if text and text not in SEEN_COMMENTS:
                SEEN_COMMENTS.add(text)
                send(f"💬 Comment (Acc {index+1}):\n{text}")

    except:
        pass

# ================= LOOP =================
def run_bot():
    while True:
        try:
            posts = []

            for i in range(len(BINANCE_KEYS)):
                post, sym = generate_post()
                post += f"\n\n🔥 Variant {i+1}"
                posts.append((post, sym))

            for i, (post, sym) in enumerate(posts):
                api_key = BINANCE_KEYS[i]

                link = post_binance(post, api_key, i)

                send(f"🚀 POSTED #{i+1}\n\n{post}\n\n🔗 {link}")
                send_image(sym)

                time.sleep(20)
                check_comments(i)

        except Exception as e:
            print("ERROR:", e)

        time.sleep(POST_INTERVAL)

threading.Thread(target=run_bot).start()

# ================= SERVER =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
