import yfinance as yf
import pandas as pd
import numpy as np

# 1. Define basket
tickers = ['QQQ', 'SOXX', 'NVDA', 'AVGO', 'MU', 'SNDK', 'MCHP', 'ASML']

# 2. Strategy Parameters
PULLBACK_PCT = 0.05    
PROFIT_TARGET = 0.12   
LOOKBACK_DAYS = 20     

print("--- Detailed Trade Interval Log --- \n")

for ticker in tickers:
    df = yf.download(ticker, start='2024-07-01', end='2026-07-01', progress=False)
    if df.empty:
        continue
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['Local_High'] = df['High'].rolling(window=LOOKBACK_DAYS).max()
    
    in_position = False
    buy_date = None
    buy_price = 0
    
    trade_durations = []
    completed_trades = 0

    print(f"================== {ticker} TRADES ==================")
    
    for i in range(LOOKBACK_DAYS, len(df)):
        current_date = df.index[i]
        current_close = float(df['Close'].iloc[i])
        current_high = float(df['High'].iloc[i])
        local_peak = float(df['Local_High'].iloc[i-1])
        
        if not in_position:
            # BUY SIGNAL
            if current_close <= local_peak * (1 - PULLBACK_PCT):
                in_position = True
                buy_price = current_close
                buy_date = current_date
        else:
            # SELL SIGNAL
            if current_high >= buy_price * (1 + PROFIT_TARGET):
                # Calculate calendar days between buy and sell
                duration = (current_date - buy_date).days
                trade_durations.append(duration)
                completed_trades += 1
                
                print(f"Trade #{completed_trades}: Bought {buy_date.strftime('%Y-%m-%d')} | Sold {current_date.strftime('%Y-%m-%d')} | Held for {duration} days")
                
                # Reset position state
                in_position = False
                buy_price = 0
                buy_date = None

    # Summary Stats for the Ticker
    if completed_trades > 0:
        avg_hold_time = np.mean(trade_durations)
        print(f"\n--> SUMMARY FOR {ticker}:")
        print(f"    Completed Trades: {completed_trades}")
        print(f"    Average Holding Interval: {avg_hold_time:.1f} days")
    else:
        print(f"\n--> SUMMARY FOR {ticker}: No completed trades in this window.")
        
    if in_position:
        print(f"    *Currently holding an open trade bought on {buy_date.strftime('%Y-%m-%d')}*")
    print("=" * 40 + "\n")