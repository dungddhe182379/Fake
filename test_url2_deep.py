#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find alternative parsing methods for URL 2"""

import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

url = "https://docs.google.com/forms/d/1uRBbUfEWsI_TBTvqYQc1XpD4LKPy2Q7YnnOTGd7-AHo/edit"

print("Analyzing URL 2 in detail...")
resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
soup = BeautifulSoup(resp.text, 'html.parser')

# Method 1: Search ALL script tags for JSON patterns
print("\n📊 Method 1: Search all scripts for JSON arrays")
scripts = soup.find_all('script')
print(f"Total scripts: {len(scripts)}")

for idx, script in enumerate(scripts):
    if not script.string:
        continue
    
    # Look for large JSON arrays
    if script.string.count('[') > 10 and len(script.string) > 1000:
        print(f"\n  Script {idx}: {len(script.string)} chars, {script.string.count('[')} brackets")
        
        # Try to find question-like patterns
        if 'entry.' in script.string or 'entry_' in script.string:
            print(f"    ✅ Contains 'entry'")
            
            # Extract first 1000 chars
            preview = script.string[:1000]
            print(f"    Preview: {preview[:200]}...")
            
            # Try to find JSON pattern
            patterns = [
                r'var [A-Z_]+ = (\[.+?\]);',
                r'= (\[\[.+?\]\]);',
                r'"questions"\s*:\s*(\[.+?\])',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, script.string[:10000], re.DOTALL)
                if match:
                    print(f"    ✅ Pattern matched: {pattern[:30]}...")
                    try:
                        data = json.loads(match.group(1))
                        print(f"    ✅ JSON parsed! Type: {type(data)}, Len: {len(data) if isinstance(data, list) else 'N/A'}")
                    except:
                        pass

# Method 2: Look in page source for specific patterns
print("\n\n📋 Method 2: Search for form structure patterns")
patterns_to_check = [
    ('entry.', resp.text.count('entry.')),
    ('entry_', resp.text.count('entry_')),
    ('"type":', resp.text.count('"type":')),
    ('freebirdFormviewerComponentsQuestionBaseRoot', resp.text.count('freebirdFormviewerComponentsQuestionBaseRoot')),
    ('data-item-id', resp.text.count('data-item-id')),
    ('data-params', resp.text.count('data-params')),
]

for pattern, count in patterns_to_check:
    print(f"  '{pattern}': {count} times")

# Method 3: Check meta tags and hidden inputs
print("\n\n🏷️ Method 3: Meta tags and inputs")
meta_tags = soup.find_all('meta')
print(f"Total meta tags: {len(meta_tags)}")

for meta in meta_tags[:20]:
    if meta.get('name') or meta.get('property'):
        print(f"  {meta.get('name') or meta.get('property')}: {str(meta.get('content'))[:100]}")

inputs = soup.find_all('input', type='hidden')
print(f"\nTotal hidden inputs: {len(inputs)}")
for inp in inputs[:10]:
    print(f"  {inp.get('name')}: {str(inp.get('value'))[:100]}")

# Method 4: Look for div with question classes
print("\n\n🎯 Method 4: Question divs")
question_divs = soup.find_all('div', class_=re.compile('question|Question'))
print(f"Divs with 'question' class: {len(question_divs)}")

# Alternative: freebirdFormviewerComponentsQuestionBaseRoot
freebird_divs = soup.find_all('div', class_=re.compile('freebird'))
print(f"Divs with 'freebird': {len(freebird_divs)}")

if freebird_divs:
    print("\n✅ Found freebird divs! Sample:")
    for i, div in enumerate(freebird_divs[:3]):
        print(f"\n  Div {i}:")
        print(f"    Classes: {div.get('class')}")
        print(f"    Attributes: {div.attrs.keys()}")
        print(f"    Text preview: {div.get_text()[:100]}")
