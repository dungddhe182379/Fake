"""Check which questions are REQUIRED"""
import requests
from bs4 import BeautifulSoup
import re
import json

published_id = "1FAIpQLSepw7dKiFkjXwTizw_Ictx_BHXGPjLUAV1hqse3Ea231kwNUw"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)

# Extract FB_PUBLIC_LOAD_DATA_
match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.*?\]);', resp.text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    questions_array = data[1][1]
    
    print("="*80)
    print("CHECK REQUIRED QUESTIONS")
    print("="*80)
    
    for idx, q_data in enumerate(questions_array):
        if not isinstance(q_data, list) or len(q_data) < 4:
            continue
        
        q_text = q_data[1] if len(q_data) > 1 else None
        q_type = q_data[3] if len(q_data) > 3 else None
        
        # Skip section headers
        if q_type == 8:
            continue
        
        # Check if required
        # Usually at q_data[4][0][4] or similar
        is_required = False
        if len(q_data) > 4 and q_data[4] and isinstance(q_data[4], list):
            if len(q_data[4]) > 0 and isinstance(q_data[4][0], list):
                # Check various positions for required flag
                for item in q_data[4][0]:
                    if isinstance(item, list):
                        # Look for [True] or similar
                        if len(item) > 4:
                            is_required = bool(item[4] if len(item) > 4 else False)
                            break
        
        # Alternative: Check q_data[4][0] array length and values
        has_required_marker = False
        if len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 6:
            # Required is usually at index 4-8
            for i in range(4, min(len(q_data[4][0]), 10)):
                if q_data[4][0][i] == 1 or q_data[4][0][i] is True:
                    has_required_marker = True
                    break
        
        print(f"\nQ{idx}: {q_text[:50]}...")
        print(f"  Type: {q_type}")
        print(f"  q_data[4][0] length: {len(q_data[4][0]) if len(q_data) > 4 and q_data[4] else 0}")
        if len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 6:
            print(f"  q_data[4][0][4-9]: {q_data[4][0][4:10]}")
        print(f"  Required?: {is_required or has_required_marker}")
