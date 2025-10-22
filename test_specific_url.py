# -*- coding: utf-8 -*-
"""Debug specific form URL"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "https://docs.google.com/forms/d/1ummF3CUEX0OhJfFZszk_04AGpbUFx3uDmsicysHL9ew/edit"

print(f"Testing URL: {url}\n")

# Fetch
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
print(f"Status: {resp.status_code}")
print(f"HTML size: {len(resp.text)} chars\n")

soup = BeautifulSoup(resp.text, 'html.parser')

# Check 1: FB_PUBLIC_LOAD_DATA_
print("="*80)
print("CHECK 1: FB_PUBLIC_LOAD_DATA_")
print("="*80)

fb_found = False
for script in soup.find_all('script'):
    if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string:
        fb_found = True
        print("FOUND!")
        
        match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);', script.string, re.DOTALL)
        if match:
            json_str = match.group(1)
            print(f"JSON length: {len(json_str)} chars")
            
            try:
                data = json.loads(json_str)
                print(f"Parsed! Type: {type(data)}, Length: {len(data)}")
                
                if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
                    if len(data[1]) > 1 and isinstance(data[1][1], list):
                        questions = data[1][1]
                        print(f"\nQuestions array: {len(questions)} items")
                        
                        for i, q in enumerate(questions[:3]):
                            if isinstance(q, list) and len(q) > 3:
                                print(f"\n  Question {i}:")
                                print(f"    [1]: {q[1] if len(q) > 1 else 'N/A'}")
                                print(f"    [3] (type): {q[3] if len(q) > 3 else 'N/A'}")
                    else:
                        print("ERROR: data[1][1] is not a list or too short")
                        print(f"data[1][1]: {data[1][1] if len(data[1]) > 1 else 'N/A'}")
                else:
                    print("ERROR: Unexpected structure")
                    print(f"data[0]: {data[0]}")
                    print(f"data[1]: {data[1] if len(data) > 1 else 'N/A'}")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
                print(f"First 500 chars: {json_str[:500]}")
        else:
            print("Regex did not match")
        break

if not fb_found:
    print("NOT FOUND!\n")

# Check 2: data-params
print("\n" + "="*80)
print("CHECK 2: data-params attributes")
print("="*80)

params_elems = soup.find_all(attrs={'data-params': True})
print(f"Found {len(params_elems)} elements with data-params")

for i, elem in enumerate(params_elems[:3]):
    params = elem.get('data-params', '')
    print(f"\n  Element {i}:")
    print(f"    Tag: {elem.name}")
    print(f"    Params: {params[:150]}...")

# Check 3: Meta og:url
print("\n" + "="*80)
print("CHECK 3: Meta og:url")
print("="*80)

meta_og = soup.find('meta', property='og:url')
if meta_og:
    og_url = meta_og.get('content', '')
    print(f"Found: {og_url}")
    
    match = re.search(r'/forms/d/e/([a-zA-Z0-9_-]+)/viewform', og_url)
    if match:
        pub_id = match.group(1)
        print(f"Published ID: {pub_id}")
else:
    print("NOT FOUND")

# Check 4: Search for any pattern
print("\n" + "="*80)
print("CHECK 4: Search for question patterns")
print("="*80)

patterns = [
    ('entry.', resp.text.count('entry.')),
    ('1FAIpQLS', resp.text.count('1FAIpQLS')),
    ('FB_PUBLIC_LOAD_DATA_', resp.text.count('FB_PUBLIC_LOAD_DATA_')),
    ('data-params', resp.text.count('data-params')),
    ('viewform', resp.text.count('viewform')),
]

for pattern, count in patterns:
    print(f"  '{pattern}': {count} occurrences")

# Check 5: Check if requiring sign in
print("\n" + "="*80)
print("CHECK 5: Access restrictions")
print("="*80)

if 'sign in' in resp.text.lower() or 'đăng nhập' in resp.text.lower():
    print("WARNING: May require sign in")
if 'permission' in resp.text.lower() or 'quyền' in resp.text.lower():
    print("WARNING: May require permissions")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if fb_found:
    print("This form HAS FB_PUBLIC_LOAD_DATA_ - should parse OK")
else:
    print("This form DOES NOT have FB_PUBLIC_LOAD_DATA_")
    print("Possible reasons:")
    print("  1. Workspace/Enterprise form")
    print("  2. Requires sign in / permissions")
    print("  3. Different rendering engine")
