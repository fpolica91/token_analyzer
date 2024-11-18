import requests
from bs4 import BeautifulSoup
import time
import csv

def clean_number(text):
    """Clean market cap values"""
    if not text:
        return 0
    try:
        return float(text.replace('$', '').replace(',', '').strip())
    except:
        return 0

def scrape_page(page_num):
    url = f"https://bscscan.com/tokens?ps=100&p={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tokens = []
        for row in soup.find_all('tr')[1:]:  # Skip header row
            try:
                # Get token link
                token_link = row.find('a', href=lambda x: x and '/token/' in x)
                if not token_link:
                    continue
                    
                # Extract base info
                address = token_link['href'].split('/token/')[-1]
                name = token_link.find('div', class_='hash-tag').text.strip()
                symbol = token_link.find('span', class_='text-muted').text.strip('()')
                
                # Get onchain market cap
                cells = row.find_all('td')
                onchain_mcap = clean_number(cells[7].text) if len(cells) > 7 else 0
                
                token = {
                    'address': address,
                    'name': name,
                    'symbol': symbol,
                    'onchain_mcap': onchain_mcap
                }
                print(f"Found: {name} ({symbol}) - {address}")
                tokens.append(token)
                
            except Exception as e:
                print(f"Error parsing row: {str(e)}")
                continue
                
        # Save page results immediately
        with open('binance.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['address', 'name', 'symbol', 'onchain_mcap'])
            # Write header if file is empty
            if f.tell() == 0:
                writer.writeheader()
            writer.writerows(tokens)
            
        print(f"Saved {len(tokens)} tokens from page {page_num}")
        return len(tokens)
        
    except Exception as e:
        print(f"Error on page {page_num}: {str(e)}")
        return 0

def main():
    total = 0
    for page in range(1, 19):  # 18 pages
        count = scrape_page(page)
        total += count
        time.sleep(3)  # Be nice to Etherscan
        
    print(f"Total tokens scraped: {total}")

if __name__ == "__main__":
    main()