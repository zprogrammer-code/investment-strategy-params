import os
from dotenv import load_dotenv
import yfinance as yf
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# 1. Configuration & Keys
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# 2. Your Vetted Tech Sandbox Basket
TECH_BASKET = ['QQQ', 'SOXX', 'NVDA', 'AVGO', 'MU', 'SNDK', 'MCHP', 'ASML']

# 3. Strategy Variables
CRASH_RESERVE_PCT = 0.40  # 40% of portfolio value is permanently locked for crashes

# S1: Nimble Swing Parameters (Weekly Baseline)
S1_DIP_FROM_SMA = 0.02   # Buy if stock drops 2% BELOW its 5-day SMA
S1_ALLOCATION = 3000     # Dollar size for a normal swing trade

# S2: Deep Crash Parameters (Emergency Drop from Peak)
S2_LOOKBACK_DAYS = 20
S2_PULLBACK_PCT = 0.25   # Triggers only on a massive 25% correction from monthly high
S2_ALLOCATION = 8000     # Heavy deployment size for major market sales

def scan_basket_and_execute():
    try:
        # --- PHASE A: DEFINE CAPITAL VARIABLES & VAULT RULES ---
        account = trading_client.get_account()
        total_portfolio = float(account.portfolio_value)
        available_cash = float(account.cash)
        
        # Enforce the Warren Buffett style safety net rule
        crash_vault_floor = total_portfolio * CRASH_RESERVE_PCT
        usable_swing_cash = available_cash - crash_vault_floor
        
        print("==================================================")
        print("      DAILY NIMBLE TECH BASKET MASTER SCAN        ")
        print("==================================================")
        print(f"Total Portfolio Value : ${total_portfolio:,.2f}")
        print(f"Total Available Cash  : ${available_cash:,.2f}")
        print(f"Locked Crash Vault   : ${crash_vault_floor:,.2f}")
        print(f"Usable Swing Capital  : ${max(0.0, usable_swing_cash):,.2f}")
        print("==================================================\n")

        # Fetch open positions to avoid duplicate trades
        open_positions = trading_client.get_all_positions()
        owned_symbols = [p.symbol for p in open_positions]

        # --- PHASE B: THE TICKER SCANNING LOOP ---
        for ticker in TECH_BASKET:
            print(f"Evaluating {ticker}...")

            if ticker in owned_symbols:
                print(f"-> Skipped: You already hold an active position in {ticker}.\n")
                continue

            # Fetch recent market data (1 month is perfect for short moving averages)
            df = yf.download(ticker, period='1mo', progress=False)
            if df.empty:
                print(f"-> Error: No data found for {ticker}.\n")
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 1. Calculate the Nimble 5-Day SMA Baseline
            df['SMA_5'] = df['Close'].rolling(window=5).mean()
            
            current_price = float(df['Close'].iloc[-1])
            sma_5_baseline = float(df['SMA_5'].iloc[-2]) # Finalized average up to yesterday
            
            # 2. Calculate the Deep Crash Peak for our emergency backup rule
            recent_peak = float(df['High'].iloc[-S2_LOOKBACK_DAYS:-1].max())

            # 3. Establish Trigger Price Points
            s1_trigger_price = sma_5_baseline * (1 - S1_DIP_FROM_SMA)  # 2% below the 5-day average
            s2_trigger_price = recent_peak * (1 - S2_PULLBACK_PCT)     # 25% below the monthly peak

            print(f"   Current Price : ${current_price:.2f}")
            print(f"   5-Day Baseline: ${sma_5_baseline:.2f}")
            print(f"   Triggers      -> Nimble Swing: ${s1_trigger_price:.2f} | Emergency Crash: ${s2_trigger_price:.2f}")

            # --- PHASE C: SIGNAL EXECUTION CHECKPOINTS ---
            
            # CHECK 1: Deep Crash Scenario (Vault Unlock)
            if current_price <= s2_trigger_price:
                print(f"   🚨 [CRASH SIGNAL TRIGGERED] {ticker} is down 25%+ from its monthly high!")
                
                if available_cash < S2_ALLOCATION:
                    print("   [WARNING] Insufficient raw cash to execute deep crash buy.\n")
                    continue
                    
                shares_to_buy = round(S2_ALLOCATION / current_price, 4)
                order_data = MarketOrderRequest(symbol=ticker, qty=shares_to_buy, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                
                print(f"   -> UNLOCKING VAULT: Buying {shares_to_buy} crash-discount shares of {ticker}...")
                submitted_order = trading_client.submit_order(order_data=order_data)
                
                available_cash -= S2_ALLOCATION
                print(f"   Order ID: {submitted_order.id}\n")

            # CHECK 2: Nimble Swing Scenario (Vault Guarded)
            elif current_price <= s1_trigger_price:
                print(f"   📈 [NIMBLE SWING TRIGGERED] {ticker} is trading below its weekly average.")
                
                # Enforce the vault protection rule!
                if usable_swing_cash < S1_ALLOCATION:
                    print(f"   ❌ [VAULT BLOCK] Order rejected. Capital locked to protect your 40% crash reserve.\n")
                    continue
                    
                shares_to_buy = round(S1_ALLOCATION / current_price, 4)
                order_data = MarketOrderRequest(symbol=ticker, qty=shares_to_buy, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
                
                print(f"   -> Executing Nimble Swing: Buying {shares_to_buy} shares of {ticker}...")
                submitted_order = trading_client.submit_order(order_data=order_data)
                
                available_cash -= S1_ALLOCATION
                usable_swing_cash -= S1_ALLOCATION
                print(f"   Order ID: {submitted_order.id}\n")
                
            else:
                print(f"   -> No trade: Stock is tracking steadily with the market trend.\n")

        print("--- Master Scan Complete ---")

    except Exception as e:
        print(f"An execution error occurred: {e}")

if __name__ == "__main__":
    scan_basket_and_execute()