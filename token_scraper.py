import requests
from bs4 import BeautifulSoup
import time

def scrape_addresses(page_num):
    url = f"https://etherscan.io/tokens?ps=100&p={page_num}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all token links and extract addresses
        addresses = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/token/' in href:
                address = href.split('/token/')[-1]
                print(f"Found address: {address}")
                addresses.append(address)
                
        # Save addresses immediately
        with open('token_addresses.txt', 'a') as f:
            for address in addresses:
                f.write(address + '\n')
                
        print(f"Saved {len(addresses)} addresses from page {page_num}")
        return len(addresses)
        
    except Exception as e:
        print(f"Error on page {page_num}: {str(e)}")
        return 0

def main():
    total = 0
    for page in range(1, 19):  # 18 pages
        count = scrape_addresses(page)
        total += count
        time.sleep(3)  # Be nice to Etherscan
        
    print(f"Total addresses scraped: {total}")

if __name__ == "__main__":
    main()