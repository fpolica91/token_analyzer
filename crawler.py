import requests
import json
import time
import os

def scrape_tokens():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Create directory for raw HTML files if it doesn't exist
    if not os.path.exists('raw_pages'):
        os.makedirs('raw_pages')

    for page in range(1, 19):  # Pages 1-18
        url = f"https://etherscan.io/tokens?ps=100&p={page}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                # Save raw HTML
                with open(f'raw_pages/page_{page}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"Saved page {page}")
            else:
                print(f"Failed to get page {page}: Status code {response.status_code}")
        
        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
        
        # Sleep between requests
        time.sleep(3)

if __name__ == "__main__":
    scrape_tokens()