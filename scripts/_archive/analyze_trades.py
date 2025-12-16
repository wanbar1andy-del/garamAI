
import pandas as pd
import sys

def analyze_trades():
    try:
        df = pd.read_csv('GARAM_Data/live/live_trades.csv')
        # Group by symbol and match buy/sell to calculate approximate PnL
        # This is a simplification, assuming FIFO or matched pairs
        
        trades = []
        positions = {}
        
        for idx, row in df.iterrows():
            sym = row['symbol']
            price = row['price']
            qty = row['qty']
            side = row['type']
            name = row['name']
            ts = row['timestamp']
            
            if side == 'BUY':
                if sym not in positions:
                    positions[sym] = []
                positions[sym].append({'price': price, 'qty': qty, 'ts': ts})
            elif side == 'SELL':
                if sym in positions and positions[sym]:
                    # Match with first Buy (FIFO)
                    buy = positions[sym].pop(0)
                    buy_price = buy['price']
                    # PnL
                    pnl = (price - buy_price) * qty
                    pnl_pct = (price - buy_price) / buy_price * 100
                    trades.append({
                        'symbol': sym,
                        'name': name,
                        'buy_date': buy['ts'],
                        'sell_date': ts,
                        'buy_price': buy_price,
                        'sell_price': price,
                        'qty': qty,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct
                    })
        
        # Sort by PnL % ascending (worst first)
        trades_df = pd.DataFrame(trades)
        worst = trades_df.sort_values('pnl_pct').head(10)
        
        print("Worst 10 Trades:")
        print(worst[['symbol', 'name', 'sell_date', 'pnl_pct', 'pnl']].to_string())
        
        # Check Hyosung specifically
        hyosung = trades_df[trades_df['name'].str.contains('효성') | trades_df['name'].str.contains('Hyosung') | trades_df['symbol'].isin(['298040', '298020', '004800'])]
        if not hyosung.empty:
            print("\nHyosung Trades:")
            print(hyosung[['symbol', 'name', 'sell_date', 'pnl_pct', 'pnl']].to_string())
            
    except Exception as e:
        print(e)

if __name__ == "__main__":
    analyze_trades()
