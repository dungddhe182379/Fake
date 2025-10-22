#!/usr/bin/env python3
"""Debug script to analyze why form parsing fails"""

import requests
from bs4 import BeautifulSoup
import re
import json

def test_form_parsing(url):
    print(f"\n{'='*80}")
    print(f"Testing URL: {url}")
    print(f"{'='*80}\n")
    
    # Fetch
    print("📥 Fetching...")
    resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    print(f"✅ Status: {resp.status_code}, Length: {len(resp.text)} chars")
    
    # Parse
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Method 1: FB_PUBLIC_LOAD_DATA_
    print("\n🔍 Method 1: FB_PUBLIC_LOAD_DATA_")
    scripts = soup.find_all('script')
    fb_found = False
    
    for script in scripts:
        if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string:
            fb_found = True
            print("✅ Found FB_PUBLIC_LOAD_DATA_ script")
            
            match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);', script.string, re.DOTALL)
            if match:
                json_str = match.group(1)
                print(f"✅ Extracted JSON: {len(json_str)} chars")
                
                try:
                    data = json.loads(json_str)
                    print(f"✅ Parsed JSON - Type: {type(data)}, Length: {len(data) if isinstance(data, list) else 'N/A'}")
                    
                    if isinstance(data, list) and len(data) > 1:
                        print(f"\nStructure Analysis:")
                        print(f"  data[0]: {type(data[0])} = {data[0]}")
                        print(f"  data[1]: {type(data[1])}")
                        
                        if isinstance(data[1], list) and len(data[1]) > 1:
                            print(f"  data[1][0]: {type(data[1][0])} = {str(data[1][0])[:100]}")
                            print(f"  data[1][1]: {type(data[1][1])} - Length: {len(data[1][1]) if isinstance(data[1][1], list) else 'N/A'}")
                            
                            if isinstance(data[1][1], list):
                                print(f"\n📋 Questions array has {len(data[1][1])} items")
                                
                                for i, item in enumerate(data[1][1][:3]):  # First 3 items
                                    print(f"\n  Item {i}:")
                                    print(f"    Type: {type(item)}")
                                    if isinstance(item, list):
                                        print(f"    Length: {len(item)}")
                                        print(f"    [0]: {item[0] if len(item) > 0 else 'N/A'}")
                                        print(f"    [1]: {item[1] if len(item) > 1 else 'N/A'}")
                                        print(f"    [3]: {item[3] if len(item) > 3 else 'N/A'} (type code)")
                                        print(f"    [4]: {str(item[4])[:100] if len(item) > 4 else 'N/A'}")
                                
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
                    print(f"First 500 chars of JSON: {json_str[:500]}")
            else:
                print("❌ Regex did not match")
                print(f"Script preview: {script.string[:500]}")
            break
    
    if not fb_found:
        print("❌ FB_PUBLIC_LOAD_DATA_ NOT FOUND")
        print("\n🔍 Checking for alternative patterns...")
        
        # Check for other common patterns
        patterns = [
            'FB_PUBLIC_LOAD_DATA_',
            'var data =',
            '"data"',
            'formData',
            'questions',
            'viewform',
        ]
        
        for pattern in patterns:
            count = resp.text.count(pattern)
            print(f"  '{pattern}': {count} occurrences")
    
    # Method 2: Check if it's a viewform page
    print("\n🔍 Method 2: Check page type")
    if '/edit' in url:
        print("✅ This is an EDIT URL")
    elif '/viewform' in url:
        print("✅ This is a VIEWFORM URL")
    else:
        print("⚠️ Unknown URL type")
    
    # Method 3: Check for data-params
    print("\n🔍 Method 3: data-params attribute")
    elements_with_params = soup.find_all(attrs={'data-params': True})
    print(f"Found {len(elements_with_params)} elements with data-params")
    
    for elem in elements_with_params[:3]:
        params = elem.get('data-params', '')
        print(f"  {elem.name}: {params[:100]}...")

if __name__ == '__main__':
    # Test both URLs
    url1 = "https://docs.google.com/forms/d/11Lr6ny1JkIESBdGKIXD0QIAQVMdIaj0I7MwfcUbOooQ/edit"
    url2 = "https://docs.google.com/forms/d/1uRBbUfEWsI_TBTvqYQc1XpD4LKPy2Q7YnnOTGd7-AHo/edit"
    
    print("🎯 TESTING URL 1 (WORKING)")
    test_form_parsing(url1)
    
    print("\n\n")
    print("🎯 TESTING URL 2 (NOT WORKING)")
    test_form_parsing(url2)
