import yfinance as yf
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

# 1. Setup your Alpaca configuration
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# Instantiate the client pointed securely at the paper sandbox
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# 2. Define the asset we want to check and parameters
TARGET_TICKER = 'NVDA'
PULLBACK_PCT = 0.05
LOOKBACK_DAYS = 20
CASH_ALLOCATION = 5000 # Max dollar amount to risk on this trade

def check_market_and_execute():
    try:
        # Check our open positions first so we don't double-buy
        positions = trading_client.get_all_positions()
        already_own = any(p.symbol == TARGET_TICKER for p in positions)
        
        if already_own:
            print(f"Skipping evaluation: You already hold an open position in {TARGET_TICKER}.")
            return

        # Fetch the most recent 30 days of data to find the local peak
        df = yf.download(TARGET_TICKER, period='1mo', progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Calculate the local high up to yesterday
        recent_peak = float(df['High'].iloc[-LOOKBACK_DAYS:-1].max())
        current_price = float(df['Close'].iloc[-1])
        
        target_buy_price = recent_peak * (1 - PULLBACK_PCT)
        
        print(f"--- Monitoring {TARGET_TICKER} ---")
        print(f"Recent {LOOKBACK_DAYS}-Day Peak: ${recent_peak:.2f}")
        print(f"Target Buy Trigger (5% Dip): ${target_buy_price:.2f}")
        print(f"Current Market Price: ${current_price:.2f}")

        # 3. Execution Signal Trigger
        if current_price <= target_buy_price:
            print(f"\n[SIGNAL TRIGGERED] {TARGET_TICKER} has dipped 5% from its high!")
            
            # Calculate fractional shares based on our cash allocation goal
            shares_to_buy = round(CASH_ALLOCATION / current_price, 4)
            
            # Prepare the order structure
            order_data = MarketOrderRequest(
                symbol=TARGET_TICKER,
                qty=shares_to_buy,
                side=OrderSide.BUY,
                time_in_force=TimeInForce.DAY
            )
            
            # Submit the trade to your Alpaca Paper Dashboard
            print(f"Submitting paper order: Buying {shares_to_buy} shares of {TARGET_TICKER}...")
            submitted_order = trading_client.submit_order(order_data=order_data)
            print(f"Order successfully placed! Order ID: {submitted_order.id}")
        else:
            print(f"\nCondition not met. {TARGET_TICKER} is currently trading above the buy zone.")
            
    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    check_market_and_execute()