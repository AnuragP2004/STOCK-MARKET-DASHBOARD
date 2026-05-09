import os
import pandas as pd
import numpy as np
import joblib
import yfinance as yf
from flask import Flask, render_template, jsonify, request
from sklearn.ensemble import RandomForestClassifier
from concurrent.futures import ThreadPoolExecutor

MODEL_PATH = 'model.pkl'

# --- AI Model (Fast Load) ---
def train_dummy_model():
    X = pd.DataFrame(np.random.uniform(10, 500, (100, 6)), columns=['sma', 'ema', 'rsi', 'macd', 'volatility', 'trend'])
    y = np.random.choice([0, 1, 2], 100)
    model = RandomForestClassifier(n_estimators=10).fit(X, y)
    joblib.dump(model, MODEL_PATH)
    return model

rf_model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else train_dummy_model()

# --- Technical Analysis ---
def quick_analysis(prices):
    df = pd.Series(prices)
    if len(df) < 2: return {"sma":0, "ema":0, "rsi":50, "macd":0, "volatility":0, "trend":0}
    sma = df.rolling(14).mean().iloc[-1]
    ema = df.ewm(span=14).mean().iloc[-1]
    return {
        "sma": float(sma or prices[-1]), "ema": float(ema), "rsi": 50.0, 
        "macd": 0.0, "volatility": float(df.std() or 1.0), "trend": 1 if prices[-1] > (sma or 0) else -1
    }

app = Flask(__name__, template_folder='.')

INDICES = {'^NSEI': 'NIFTY 50', '^BSESN': 'SENSEX', '^NSEBANK': 'BANK NIFTY'}
TOP_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'ICICIBANK.NS', 'INFY.NS', 'ITC.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'LT.NS', 'BAJFINANCE.NS',
    'HINDUNILVR.NS', 'KOTAKBANK.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'SUNPHARMA.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'TATASTEEL.NS', 'NTPC.NS',
    'TATAMOTORS.NS', 'POWERGRID.NS', 'WIPRO.NS', 'M&M.NS', 'HCLTECH.NS', 'ONGC.NS', 'ADANIENT.NS', 'JSWSTEEL.NS', 'LTIM.NS', 'GRASIM.NS',
    'ADANIPORTS.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'COALINDIA.NS', 'BAJAJ-AUTO.NS', 'EICHERMOT.NS', 'BPCL.NS', 'NESTLEIND.NS', 'DIVISLAB.NS',
    'TECHM.NS', 'CIPLA.NS', 'BAJAJFINSV.NS', 'DRREDDY.NS', 'HINDALCO.NS', 'APOLLOHOSP.NS', 'BRITANNIA.NS', 'TATACONSUM.NS', 'UPL.NS', 'HEROMOTOCO.NS',
    'BEL.NS', 'HAL.NS', 'ZOMATO.NS', 'JIOFIN.NS', 'TRENT.NS', 'DLF.NS', 'VBL.NS', 'SIEMENS.NS', 'IRFC.NS', 'PFC.NS', 'RECLTD.NS', 'CHOLAFIN.NS',
    'HAVELLS.NS', 'GAIL.NS', 'PIDILITIND.NS', 'ABB.NS', 'CANBK.NS', 'BANKBARODA.NS', 'PNB.NS', 'INDHOTEL.NS', 'POLYCAB.NS', 'TVSMOTOR.NS',
    'UNITDSPR.NS', 'COLPAL.NS', 'TATACOMM.NS', 'AUBANK.NS', 'IDFCFIRSTB.NS', 'YESBANK.NS', 'BHEL.NS', 'CONCOR.NS', 'NMDC.NS', 'SAIL.NS'
]

def fetch_single_ticker(symbol):
    try:
        t = yf.Ticker(symbol)
        info = t.fast_info
        lp = info.last_price
        pc = info.previous_close
        return {
            "ticker": symbol.replace('.NS', ''),
            "company": INDICES.get(symbol, symbol.replace('.NS', '')),
            "currentPrice": round(lp, 2),
            "change": round(lp - pc, 2),
            "changePercent": round(((lp - pc) / pc) * 100, 2),
            "volume": int(info.last_volume),
            "marketCap": int(info.market_cap),
            "high52Week": round(info.year_high, 2),
            "low52Week": round(info.year_low, 2),
            "is_index": symbol in INDICES
        }
    except: return None

@app.route('/')
def home(): return render_template('Dashboard.html')

@app.route('/api/market_data')
def get_market_data():
    all_symbols = list(INDICES.keys()) + TOP_STOCKS
    response = {"indices": [], "stocks": []}
    
    # Using 20 threads for high speed
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(fetch_single_ticker, all_symbols))
    
    for r in results:
        if r:
            if r.pop('is_index'): response["indices"].append(r)
            else: response["stocks"].append(r)
            
    return jsonify(response)

@app.route('/api/live/<symbol>')
def live_data(symbol):
    try:
        s = symbol if symbol.startswith('^') else f"{symbol}.NS"
        h = yf.Ticker(s).history(period="3mo", interval="1d")
        p = h['Close'].tolist()
        return jsonify({
            "ticker": symbol, "currentPrice": round(p[-1], 2),
            "historicalData": [{"x": d.strftime('%Y-%m-%d'), "y": round(v, 2)} for d, v in zip(h.index, p)],
            "raw_prices": p
        })
    except: return jsonify({"error": "Failed"}), 404

@app.route('/api/analyze', methods=['POST'])
def analyze():
    p = request.json.get('prices', [])
    d = quick_analysis(p)
    res = rf_model.predict(pd.DataFrame([d]))[0]
    return jsonify({**d, "final_signal": {0: "SELL", 1: "HOLD", 2: "BUY"}[res]})

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)