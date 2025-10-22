"""Check raw data-params to see what's after JSON"""
import requests
from bs4 import BeautifulSoup

published_id = "1FAIpQLSfAzjNq_wsV_7z-b4fvQHSHFtyNmZ_LRgxrgSc6gIEJK4BuVA"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
soup = BeautifulSoup(resp.text, 'html.parser')

divs = soup.find_all('div', attrs={'data-params': True})
print(f"Found {len(divs)} divs\n")

for idx, div in enumerate(divs[:3]):  # First 3 only
    params = div.get('data-params', '')
    print(f"DIV {idx}:")
    print(f"Length: {len(params)}")
    print(f"First 500 chars:")
    print(params[:500])
    print(f"\nLast 200 chars:")
    print(params[-200:])
    print("="*80 + "\n")
