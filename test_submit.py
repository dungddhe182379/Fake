"""Test parse và submit form"""
import requests
from bs4 import BeautifulSoup
import re

# Test 1: Parse form
print("="*80)
print("TEST 1: PARSE FORM")
print("="*80)

edit_url = "https://docs.google.com/forms/d/1rg6bgY4aSxGpkBq-TRBQfq0rgFHue4YXogmL5dKn8_E/edit"
published_id = "1FAIpQLSepw7dKiFkjXwTizw_Ictx_BHXGPjLUAV1hqse3Ea231kwNUw"

viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"
print(f"Fetching: {viewform_url}\n")

resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
print(f"Status: {resp.status_code}")

# Check FB_PUBLIC_LOAD_DATA_
if 'FB_PUBLIC_LOAD_DATA_' in resp.text:
    print("✓ Found FB_PUBLIC_LOAD_DATA_")
    
    # Extract JSON
    match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.*?\]);', resp.text, re.DOTALL)
    if match:
        import json
        try:
            data = json.loads(match.group(1))
            if data and len(data) > 1 and data[1] and len(data[1]) > 1:
                questions_array = data[1][1]
                print(f"✓ Found {len(questions_array)} items in questions array\n")
                
                # Parse questions
                questions = []
                for idx, q_data in enumerate(questions_array):
                    if not isinstance(q_data, list) or len(q_data) < 4:
                        continue
                    
                    q_type = q_data[3] if len(q_data) > 3 else None
                    q_text = q_data[1] if len(q_data) > 1 else None
                    
                    # Skip section headers (type 8)
                    if q_type == 8:
                        continue
                    
                    # Get entry_id
                    if len(q_data) > 4 and q_data[4] and isinstance(q_data[4], list):
                        if len(q_data[4]) > 0 and isinstance(q_data[4][0], list) and len(q_data[4][0]) > 0:
                            entry_id = f"entry.{q_data[4][0][0]}"
                            questions.append({
                                'question': q_text,
                                'entry_id': entry_id,
                                'type': q_type
                            })
                
                print(f"✓ Parsed {len(questions)} questions:\n")
                for q in questions[:5]:
                    print(f"  - {q['question'][:50]}... ({q['entry_id']})")
                
                # Test 2: Submit
                print("\n" + "="*80)
                print("TEST 2: SUBMIT FORM")
                print("="*80)
                
                submit_url = f"https://docs.google.com/forms/d/e/{published_id}/formResponse"
                print(f"Submit URL: {submit_url}\n")
                
                # Create payload for first question
                if questions:
                    payload = {
                        questions[0]['entry_id']: 'Test Response'
                    }
                    
                    print(f"Payload: {payload}")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0',
                        'Referer': viewform_url
                    }
                    
                    resp = requests.post(submit_url, data=payload, headers=headers, allow_redirects=False)
                    print(f"\nResponse Status: {resp.status_code}")
                    print(f"Response Headers: {dict(resp.headers)}")
                    print(f"Response Text Length: {len(resp.text)}")
                    print(f"Response Text (first 500 chars):\n{resp.text[:500]}")
                    
                    # Check for success indicators
                    if resp.status_code in [200, 302]:
                        if 'formResponse' in resp.text or 'submissionConfirmation' in resp.text or resp.status_code == 302:
                            print("\n✅ SUBMIT SUCCESS!")
                        else:
                            print("\n⚠️ Unexpected response")
                    else:
                        print(f"\n❌ SUBMIT FAILED: Status {resp.status_code}")
                        
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
else:
    print("❌ No FB_PUBLIC_LOAD_DATA_ found")
