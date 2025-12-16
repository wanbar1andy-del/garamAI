import pandas as pd
import collections

# Load trades
trade_file = r"c:\garam\garam\GARAM_Data\live\live_trades.csv"

try:
    df = pd.read_csv(trade_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by time
    df = df.sort_values('timestamp')
    
    # FIFO Matching for PnL
    # Symbol -> Deque of (price, qty)
    inventory = collections.defaultdict(collections.deque)
    realized_pnl = []

    for _, row in df.iterrows():
        sym = row['symbol']
        qty = row['qty']
        price = row['price']
        
        if row['type'] == 'BUY':
            inventory[sym].append({'price': price, 'qty': qty})
        
        elif row['type'] == 'SELL':
            # Match against inventory
            remaining_sell = qty
            pnl_trade = 0
            cost_basis = 0
            
            while remaining_sell > 0 and inventory[sym]:
                batch = inventory[sym][0] # Peek first
                
                matched_qty = min(remaining_sell, batch['qty'])
                
                # Calc PnL segment
                pnl_trade += (price - batch['price']) * matched_qty
                cost_basis += batch['price'] * matched_qty
                
                # Update batch
                batch['qty'] -= matched_qty
                remaining_sell -= matched_qty
                
                if batch['qty'] <= 0:
                    inventory[sym].popleft()
            
            # Record if it's in Nov 2025
            if row['timestamp'].strftime('%Y-%m') == '2025-11':
                realized_pnl.append({
                    'date': row['timestamp'],
                    'symbol': sym,
                    'name': row['name'],
                    'pnl': pnl_trade,
                    'return': (pnl_trade / cost_basis) if cost_basis > 0 else 0
                })

    # Convert to DF
    res = pd.DataFrame(realized_pnl)
    
    if res.empty:
        print("No realized trades in Nov 2025.")
    else:
        print(f"Total Transactions in Nov 2025: {len(res)}")
        print(f"Total Realized PnL: {res['pnl'].sum():,.0f} KRW")
        
        print("\nTop 5 Loss Trades:")
        print(res.sort_values('pnl').head(5)[['date', 'symbol', 'name', 'pnl', 'return']])
        
        print("\nDaily PnL Summary:")
        print(res.groupby(res['date'].dt.date)['pnl'].sum().sort_index())

except Exception as e:
    print(f"Error: {e}")
