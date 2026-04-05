from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import functools # <-- NEW: Brings in the caching tool!

app = FastAPI(title="My Financial Data API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# THE CACHE
# This tells Python: "Remember the last 50 company searches so we don't have to download them twice!"
@functools.lru_cache(maxsize=50)
def fetch_data_from_internet(symbol: str):
    company = yf.Ticker(symbol)
    return company.history(period="6mo")

@functools.lru_cache(maxsize=50)
def fetch_summary_from_internet(symbol: str):
    company = yf.Ticker(symbol)
    return company.history(period="1y")
# -----------------------

@app.get("/companies")
async def get_companies(): #ASYNC HANDLING 
    return {
        "companies": [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "TSLA", "name": "Tesla Inc."},
            {"symbol": "MSFT", "name": "Microsoft"},
            {"symbol": "NVDA", "name": "Nvidia"},
            {"symbol": "INFY", "name": "Infosys"}
        ]
    }

@app.get("/data/{symbol}")
async def get_stock_data(symbol: str, days: int = 30): #ASYNC HANDLING 
    
    # Use our new cached function instead of downloading directly!
    history = fetch_data_from_internet(symbol)
    
    history['7-Day MA'] = history['Close'].rolling(window=7).mean()
    history['Daily Return'] = (history['Close'] - history['Open']) / history['Open']
    history['Volatility'] = history['Daily Return'].rolling(window=30).std()
    
    clean_history = history.dropna().reset_index()
    clean_history['Date'] = clean_history['Date'].astype(str)
    
    final_data = clean_history[['Date', 'Close', '7-Day MA', 'Daily Return', 'Volatility']].tail(days)
    return final_data.to_dict(orient="records")

@app.get("/summary/{symbol}")
async def get_summary(symbol: str): # ASYNC HANDLING 
    
    # Use our new cached function!
    history = fetch_summary_from_internet(symbol)
    
    return {
        "symbol": symbol.upper(),
        "52_week_high": round(history['High'].max(), 2),
        "52_week_low": round(history['Low'].min(), 2)
    }