# -*- coding: utf-8 -*-
"""Test parsing from VIEWFORM URL"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Published ID from og:url
published_id = "1FAIpQLSfAzjNq_wsV_7z-b4fvQHSHFtyNmZ_LRgxrgSc6gIEJK4BuVA"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

print(f"Testing VIEWFORM URL:\n{viewform_url}\n")

# Fetch
resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
print(f"Status: {resp.status_code}")
print(f"HTML size: {len(resp.text)} chars\n")

soup = BeautifulSoup(resp.text, 'html.parser')

# Method 1: data-params (most common in viewform)
print("="*80)
print("METHOD 1: data-params attributes")
print("="*80)

params_elems = soup.find_all(attrs={'data-params': True})
print(f"Found {len(params_elems)} elements\n")

questions = []

for i, elem in enumerate(params_elems):
    try:
        params_str = elem.get('data-params', '')
        if not params_str or not params_str.startswith('%.@.'):
            continue
        
        # Remove %.@. prefix
        json_str = params_str[4:]
        q_data = json.loads(json_str)
        
        if not isinstance(q_data, list) or len(q_data) < 4:
            continue
        
        q_text = q_data[1] if len(q_data) > 1 else None
        q_type = q_data[3] if len(q_data) > 3 else None
        entry_id = q_data[4][0][0] if len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 0 else None
        
        if q_text and entry_id:
            print(f"Question {i+1}:")
            print(f"  Text: {q_text}")
            print(f"  Type: {q_type}")
            print(f"  Entry: entry.{entry_id}")
            
            # Get options if applicable
            if q_type in [2, 4, 5] and len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 1:
                options_data = q_data[4][0][1]
                if isinstance(options_data, list):
                    options = []
                    for opt in options_data:
                        if isinstance(opt, list) and len(opt) > 0:
                            options.append(str(opt[0]))
                    print(f"  Options: {options}")
            
            questions.append({
                'text': q_text,
                'type': q_type,
                'entry': f'entry.{entry_id}'
            })
            print()
            
    except Exception as e:
        continue

print("="*80)
print(f"TOTAL QUESTIONS FOUND: {len(questions)}")
print("="*80)

if len(questions) > 0:
    print("\nSUCCESS! Viewform parsing works!")
    print("\nQuestion types found:")
    type_counts = {}
    for q in questions:
        t = q['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    
    type_names = {
        0: 'Short Answer',
        1: 'Long Answer',
        2: 'Multiple Choice',
        3: 'Dropdown',
        4: 'Checkbox',
        5: 'Linear Scale',
        7: 'Grid',
        9: 'Date',
        10: 'Time'
    }
    
    for t, count in sorted(type_counts.items()):
        print(f"  Type {t} ({type_names.get(t, 'Unknown')}): {count} questions")
else:
    print("\nFAILED! Could not parse from viewform either")
    print("This form may:")
    print("  1. Require authentication")
    print("  2. Be restricted to specific users")
    print("  3. Be closed/deleted")
