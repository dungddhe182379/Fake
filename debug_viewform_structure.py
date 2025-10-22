# -*- coding: utf-8 -*-
"""Debug data-params structure"""

import requests
from bs4 import BeautifulSoup
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

published_id = "1FAIpQLSfAzjNq_wsV_7z-b4fvQHSHFtyNmZ_LRgxrgSc6gIEJK4BuVA"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
soup = BeautifulSoup(resp.text, 'html.parser')

print("="*80)
print("RAW data-params content:")
print("="*80)

params_elems = soup.find_all(attrs={'data-params': True})
print(f"Found {len(params_elems)} elements\n")

for i, elem in enumerate(params_elems):
    params = elem.get('data-params', '')
    print(f"\nElement {i}:")
    print(f"  Tag: {elem.name}")
    print(f"  Classes: {elem.get('class')}")
    print(f"  Params length: {len(params)} chars")
    print(f"  Params preview: {params[:200]}")
    print(f"  Starts with %.@.: {params.startswith('%.@.')}")
    
    # Try to find question text in parent
    parent_text = elem.get_text()[:100] if elem.get_text() else "N/A"
    print(f"  Element text: {parent_text}")

print("\n" + "="*80)
print("Search for other patterns:")
print("="*80)

# Look for div with question classes
question_divs = soup.find_all('div', {'role': 'listitem'})
print(f"Divs with role=listitem: {len(question_divs)}")

# Look for input/textarea with entry names
inputs = soup.find_all(['input', 'textarea'])
entry_inputs = [inp for inp in inputs if inp.get('name', '').startswith('entry.')]
print(f"Inputs with entry.*: {len(entry_inputs)}")

if entry_inputs:
    print("\nFound entry inputs:")
    for inp in entry_inputs[:5]:
        print(f"  {inp.get('name')}: {inp.get('aria-label', 'N/A')[:50]}")

# Check for form data in scripts
print("\n" + "="*80)
print("Check scripts for form data:")
print("="*80)

for script in soup.find_all('script'):
    if script.string:
        if 'FB_PUBLIC_LOAD_DATA_' in script.string:
            print("  Found FB_PUBLIC_LOAD_DATA_")
        if len(script.string) > 5000 and '[' in script.string:
            # Might be form data
            print(f"  Large script ({len(script.string)} chars) with arrays")
            # Try to find entry pattern
            if 'entry.' in script.string or '"entry"' in script.string:
                print("    Contains 'entry'")
                preview = script.string[:1000]
                print(f"    Preview: {preview[:200]}")
