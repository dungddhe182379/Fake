# -*- coding: utf-8 -*-
"""Test to find viewform link from edit page"""

import requests
from bs4 import BeautifulSoup
import re
import json

def find_viewform_link_methods(edit_url):
    """Test all methods to find viewform link from edit page"""
    print(f"\n{'='*80}")
    print(f"Finding viewform link from EDIT URL")
    print(f"{'='*80}\n")
    print(f"Edit URL: {edit_url}")
    
    resp = requests.get(edit_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    results = {}
    
    # Method 1: Search in meta tags og:url
    print("\n[Method 1] Meta tag og:url")
    meta_url = soup.find('meta', property='og:url')
    if meta_url:
        url = meta_url.get('content', '')
        print(f"✅ Found: {url}")
        results['meta_og_url'] = url
    else:
        print("❌ Not found")
    
    # Method 2: Search all meta tags
    print("\n[Method 2] All meta tags with viewform")
    for meta in soup.find_all('meta'):
        content = meta.get('content', '')
        if 'viewform' in content:
            print(f"✅ {meta.get('property') or meta.get('name')}: {content}")
            results['meta_viewform'] = content
            break
    
    # Method 3: Search in script tags for viewform URL
    print("\n[Method 3] Script tags with viewform pattern")
    for script in soup.find_all('script'):
        if script.string and 'viewform' in script.string:
            # Find full viewform URL
            match = re.search(r'https://docs\.google\.com/forms/d/e/([a-zA-Z0-9_-]+)/viewform', script.string)
            if match:
                pub_id = match.group(1)
                full_url = match.group(0)
                print(f"✅ Found published ID: {pub_id}")
                print(f"   Full URL: {full_url}")
                results['script_viewform'] = full_url
                results['published_id'] = pub_id
                break
    
    # Method 4: Search for FB_PUBLIC_LOAD_DATA_ and check internal structure
    print("\n[Method 4] FB_PUBLIC_LOAD_DATA_ internal structure")
    for script in soup.find_all('script'):
        if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string:
            match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);', script.string, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    print(f"✅ Found FB_PUBLIC_LOAD_DATA_")
                    print(f"   Type: {type(data)}, Length: {len(data)}")
                    
                    # Check for published ID in various positions
                    # data[14] often contains settings/metadata
                    if len(data) > 14 and data[14]:
                        print(f"   data[14]: {str(data[14])[:200]}")
                        # Search for published ID pattern
                        data_str = str(data[14])
                        match_id = re.search(r'1FAIpQLS[a-zA-Z0-9_-]{48}', data_str)
                        if match_id:
                            results['fb_published_id'] = match_id.group(0)
                            print(f"   ✅ Found published ID in data[14]: {match_id.group(0)}")
                    
                    # Check data[10] - often contains form metadata
                    if len(data) > 10 and data[10]:
                        print(f"   data[10]: {str(data[10])[:200]}")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            break
    
    # Method 5: Search raw HTML for published ID pattern
    print("\n[Method 5] Raw HTML search for published ID pattern")
    match = re.search(r'1FAIpQLS[a-zA-Z0-9_-]{48}', resp.text)
    if match:
        pub_id = match.group(0)
        print(f"✅ Found: {pub_id}")
        results['html_published_id'] = pub_id
    else:
        print("❌ Not found")
    
    # Method 6: Search for data-initial-sign-in-url or similar
    print("\n[Method 6] data-* attributes")
    try:
        for elem in soup.find_all(True):
            if hasattr(elem, 'attrs'):
                for attr, value in elem.attrs.items():
                    if 'url' in attr.lower() and 'viewform' in str(value):
                        print(f"✅ {attr}: {value}")
                        results[f'data_attr_{attr}'] = value
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY - Found viewform links:")
    print("="*80)
    for method, value in results.items():
        print(f"{method:25s}: {str(value)[:100]}")
    
    return results

if __name__ == '__main__':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Test both URLs
    url1 = "https://docs.google.com/forms/d/11Lr6ny1JkIESBdGKIXD0QIAQVMdIaj0I7MwfcUbOooQ/edit"
    url2 = "https://docs.google.com/forms/d/1uRBbUfEWsI_TBTvqYQc1XpD4LKPy2Q7YnnOTGd7-AHo/edit"
    
    print("\n[TEST] URL 1 (Standard Form)")
    results1 = find_viewform_link_methods(url1)
    
    print("\n\n[TEST] URL 2 (Workspace Form)")
    results2 = find_viewform_link_methods(url2)
    
    # Save results
    print("\n\n" + "="*80)
    print("FINAL COMPARISON")
    print("="*80)
    print(f"\nURL 1 methods found: {len(results1)}")
    print(f"URL 2 methods found: {len(results2)}")
    
    print("\n✅ Best method for both:")
    if 'meta_og_url' in results1 and 'meta_og_url' in results2:
        print("   → Meta tag og:url (most reliable)")
    elif 'script_viewform' in results1 and 'script_viewform' in results2:
        print("   → Script tag viewform URL")
    elif 'html_published_id' in results1 and 'html_published_id' in results2:
        print("   → Raw HTML 1FAIpQLS pattern")
