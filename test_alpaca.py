from alpaca.trading.client import TradingClient

# 1. Input your keys here (make sure they are your PAPER keys!)
load_dotenv()
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

# 2. Connect to the Paper Trading environment
# Setting paper=True ensures we are strictly in the sandbox
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

try:
    # 3. Fetch account information
    account = trading_client.get_account()
    
    print("--- Connection Successful! ---")
    print(f"Account ID: {account.id}")
    print(f"Current Cash Balance: ${float(account.cash):,.2f}")
    print(f"Total Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"Trading Status: {account.status}")
    print("-------------------------------")

except Exception as e:
    print("Oops! Connection failed. Check your keys or network connection.")
    print(f"Error details: {e}")