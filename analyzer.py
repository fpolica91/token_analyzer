import asyncio
import aiohttp
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Set
import json

class PumpDataCollector:
    def __init__(self, etherscan_api_key: str, dex_api_key: str = None):
        self.etherscan_key = etherscan_api_key
        self.dex_api_key = dex_api_key
        self.etherscan_base = "https://api.etherscan.io/api"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_successful_pumps(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Find tokens that had successful pumps in the given date range"""
        
        # First get all tokens that entered our market cap range
        potential_tokens = await self._get_tokens_in_range(start_date, end_date)
        
        pump_data = []
        for token in potential_tokens:
            # Get price and volume history
            price_history = await self._get_price_history(token['address'], start_date, end_date)
            
            # Check if meets pump criteria
            pump_info = self._analyze_pump_pattern(price_history, token)
            if pump_info:
                pump_data.append(pump_info)
                
        return pd.DataFrame(pump_data)

    async def _get_tokens_in_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get tokens that entered our market cap range during the period"""
        tokens = []
        
        # Get list of tokens with market caps in our range
        params = {
            'module': 'token',
            'action': 'tokenlist',
            'apikey': self.etherscan_key,
            'starttime': int(start_date.timestamp()),
            'endtime': int(end_date.timestamp())
        }
        
        async with self.session.get(self.etherscan_base, params=params) as response:
            data = await response.json()
            print(data)
            if data['status'] == '1':
                for token in data['result']:
                    market_cap = float(token.get('market_cap', 0))
                    if 500_000 <= market_cap <= 20_000_000:
                        tokens.append({
                            'address': token['contractAddress'],
                            'symbol': token['symbol'],
                            'initial_market_cap': market_cap
                        })
        
        return tokens

    async def _get_price_history(self, token_address: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get detailed price and volume history for a token"""
        # Get trades from Uniswap
        swaps = await self._get_uniswap_swaps(token_address, start_date, end_date)
        
        # Get transfer events
        transfers = await self._get_token_transfers(token_address, start_date, end_date)
        
        # Combine and process data
        return self._process_historical_data(swaps, transfers)

    async def _get_uniswap_swaps(self, token_address: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all Uniswap swap events for the token"""
        # Implementation depends on which DEX API/Archive node we're using
        # This is a placeholder for the actual implementation
        pass

    async def _get_token_transfers(self, token_address: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get all token transfer events"""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': token_address,
            'startblock': await self._get_block_number(start_date),
            'endblock': await self._get_block_number(end_date),
            'apikey': self.etherscan_key
        }
        
        async with self.session.get(self.etherscan_base, params=params) as response:
            data = await response.json()
            return data.get('result', [])

    def _analyze_pump_pattern(self, price_history: pd.DataFrame, token_info: Dict) -> Dict:
        """Analyze if token had a pump meeting our criteria"""
        if price_history.empty:
            return None
            
        # Calculate returns
        price_history['returns'] = price_history['price'].pct_change()
        
        # Look for our target pump patterns
        max_return = price_history['returns'].max()
        if max_return >= 0.5:  # 50% minimum pump
            pump_start = price_history['returns'].idxmax()
            pump_data = {
                'token_address': token_info['address'],
                'symbol': token_info['symbol'],
                'pump_start_date': pump_start,
                'initial_market_cap': token_info['initial_market_cap'],
                'max_return': max_return,
                'time_to_peak': self._calculate_time_to_peak(price_history, pump_start),
                'pre_pump_metrics': self._get_pre_pump_metrics(price_history, pump_start)
            }
            return pump_data
            
        return None

    def _calculate_time_to_peak(self, price_history: pd.DataFrame, pump_start: datetime) -> timedelta:
        """Calculate how long it took to reach peak price"""
        peak_time = price_history['price'].idxmax()
        return peak_time - pump_start

    def _get_pre_pump_metrics(self, price_history: pd.DataFrame, pump_start: datetime) -> Dict:
        """Get metrics from the period before the pump"""
        pre_pump_period = price_history[price_history.index < pump_start].last('5D')
        
        return {
            'volume_increase': pre_pump_period['volume'].pct_change().mean(),
            'unique_buyers': len(pre_pump_period['buyers'].unique()),
            'avg_trade_size': pre_pump_period['volume'].mean() / pre_pump_period['num_trades'].mean(),
            'buy_sell_ratio': pre_pump_period['buy_volume'].sum() / pre_pump_period['sell_volume'].sum(),
            'lp_changes': pre_pump_period['lp_tokens'].pct_change().mean()
        }

    async def _get_block_number(self, timestamp: datetime) -> int:
        """Get nearest block number for a timestamp"""
        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': int(timestamp.timestamp()),
            'closest': 'before',
            'apikey': self.etherscan_key
        }
        
        async with self.session.get(self.etherscan_base, params=params) as response:
            data = await response.json()
            return int(data['result'])

async def main():
    # Example usage
    
    collector = PumpDataCollector(etherscan_api_key="QWC99R35T4QMK5VX17NBWBTA2B5NAFH499")
    
    start_date = datetime.now() - timedelta(days=360)  # Last 6 months
    end_date = datetime.now()
    
    async with collector:
        pump_data = await collector.get_successful_pumps(start_date, end_date)
        print(pump_data)

    # Save results
    pump_data.to_csv('historical_pumps.csv', index=False)
    
    # # Print summary
    # print(f"Found {len(pump_data)} pump events")
    # print("\nAverage returns:", pump_data['max_return'].mean())
    # print("Average time to peak:", pump_data['time_to_peak'].mean())
    
    # # Analyze pre-pump metrics
    # pre_pump_metrics = pd.DataFrame([p for p in pump_data['pre_pump_metrics']])
    # print("\nPre-pump metrics averages:")
    # print(pre_pump_metrics.mean())
    
    # print(pump_data.columns)

if __name__ == "__main__":
    asyncio.run(main())