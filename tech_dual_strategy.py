import yfinance as yf
import pandas as pd
import numpy as np

tickers = ['QQQ', 'SOXX', 'NVDA', 'AVGO', 'MU', 'SNDK', 'MCHP', 'ASML']
LOOKBACK_DAYS = 20

print("--- Dual-Strategy Parameter Experiment --- \n")

for ticker in tickers:
    df = yf.download(ticker, start='2024-07-01', end='2026-07-01', progress=False)
    if df.empty: continue
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['Local_High'] = df['High'].rolling(window=LOOKBACK_DAYS).max()
    
    # Strategy 1 States (Swing)
    s1_active = False
    s1_buy_price = 0
    s1_wins = 0
    s1_total = 0
    
    # Strategy 2 States (Crash Reserve)
    s2_active = False
    s2_buy_price = 0
    s2_wins = 0
    s2_total = 0

    for i in range(LOOKBACK_DAYS, len(df)):
        close = float(df['Close'].iloc[i])
        high = float(df['High'].iloc[i])
        peak = float(df['Local_High'].iloc[i-1])
        
        # --- STRATEGY 1: 5% Pullback / 12% Profit ---
        if not s1_active:
            if close <= peak * 0.95:
                s1_active = True
                s1_buy_price = close
                s1_total += 1
        else:
            if high >= s1_buy_price * 1.12:
                s1_wins += 1
                s1_active = False

        # --- STRATEGY 2: 25% Crash / 50% Profit Recovery ---
        if not s2_active:
            if close <= peak * 0.75: # 25% Drop
                s2_active = True
                s2_buy_price = close
                s2_total += 1
        else:
            if high >= s2_buy_price * 1.50: # 50% Rebound
                s2_wins += 1
                s2_active = False

    print(f"====== Ticker: {ticker} ======")
    print(f"  [Swing Strategy] Trades: {s1_total} | Targets Hit: {s1_wins} | Open Position: {s1_active}")
    print(f"  [Crash Reserve]  Trades: {s2_total} | Targets Hit: {s2_wins} | Open Position: {s2_active}")
    print("=" * 30 + "\n")