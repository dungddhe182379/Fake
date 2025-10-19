"""
Test script để parse Google Form trực tiếp
"""
import requests
from bs4 import BeautifulSoup
import re

def test_parse_form(url):
    """Test parse form với URL"""
    print("\n" + "="*70)
    print("🧪 TEST PARSE GOOGLE FORM")
    print("="*70)
    print(f"URL: {url}\n")
    
    try:
        # Fetch HTML
        print("📥 Fetching HTML...")
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"✅ Status: {resp.status_code}")
        print(f"✅ HTML length: {len(resp.text)} chars\n")
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract form ID
        form_id_match = re.search(r'/forms/d/e/([a-zA-Z0-9_-]+)', url)
        if form_id_match:
            form_id = form_id_match.group(1)
            print(f"✅ Form ID: {form_id}\n")
        
        # Find entry IDs
        print("🔍 Searching for entry IDs...")
        entry_pattern = r'entry\.(\d{9,10})'
        entry_matches = re.findall(entry_pattern, resp.text)
        
        seen = set()
        entry_ids = []
        for match in entry_matches:
            entry_id = f'entry.{match}'
            if entry_id not in seen:
                seen.add(entry_id)
                entry_ids.append(entry_id)
        
        print(f"✅ Found {len(entry_ids)} entry IDs:")
        for i, eid in enumerate(entry_ids):
            print(f"   {i+1}. {eid}")
        print()
        
        # Find question containers
        print("🔍 Searching for question containers...")
        question_containers = soup.find_all('div', {'role': 'listitem'})
        print(f"✅ Found {len(question_containers)} containers with role='listitem'\n")
        
        # Parse each question
        questions_data = []
        
        for idx, container in enumerate(question_containers):
            print(f"{'─'*70}")
            print(f"📝 QUESTION #{idx + 1}")
            print(f"{'─'*70}")
            
            # Find question text
            question_text = None
            
            # Try role="heading"
            heading = container.find('div', {'role': 'heading'})
            if heading:
                question_text = heading.get_text(strip=True)
                print(f"✅ Found text (heading): {question_text}")
            
            # Try first span with meaningful text
            if not question_text:
                spans = container.find_all('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if text and len(text) > 3 and len(text) < 500:
                        question_text = text
                        print(f"✅ Found text (span): {question_text}")
                        break
            
            if not question_text:
                print("❌ No question text found\n")
                continue
            
            # Assign entry ID
            if idx < len(entry_ids):
                entry_id = entry_ids[idx]
                print(f"✅ Entry ID: {entry_id}")
            else:
                print("❌ No entry ID available\n")
                continue
            
            # Detect question type
            print("🔍 Detecting question type...")
            
            # Check for text input
            text_input = container.find('input', attrs={'type': lambda x: x in [None, 'text']})
            textarea = container.find('textarea')
            
            # Check for radio (multiple choice)
            radio_buttons = container.find_all('div', attrs={'role': 'radio'})
            
            # Check for checkbox
            checkboxes = container.find_all('div', attrs={'role': 'checkbox'})
            
            # Check for scale
            scale_options = container.find_all(attrs={'data-value': re.compile(r'^\d+$')})
            
            options = []
            question_type = 'unknown'
            
            if radio_buttons:
                question_type = 'multiple_choice'
                print(f"✅ Type: MULTIPLE CHOICE ({len(radio_buttons)} options)")
                for radio in radio_buttons:
                    label = radio.get('aria-label', '').strip()
                    if label:
                        options.append(label)
                        print(f"   - {label}")
            
            elif checkboxes:
                question_type = 'checkbox'
                print(f"✅ Type: CHECKBOX ({len(checkboxes)} options)")
                for checkbox in checkboxes:
                    label = checkbox.get('aria-label', '').strip()
                    if label:
                        options.append(label)
                        print(f"   - {label}")
            
            elif scale_options and len(scale_options) >= 2:
                question_type = 'scale'
                print(f"✅ Type: SCALE ({len(scale_options)} options)")
                for scale in scale_options:
                    val = scale.get('data-value', '')
                    if val:
                        options.append(val)
                        print(f"   - {val}")
            
            elif textarea:
                question_type = 'long_text'
                options = ["Long answer sample"]
                print(f"✅ Type: LONG TEXT (paragraph)")
            
            elif text_input:
                question_type = 'short_text'
                options = ["Short answer sample"]
                print(f"✅ Type: SHORT TEXT")
            
            else:
                # Fallback: try data-value
                all_data_values = container.find_all(attrs={'data-value': True})
                if all_data_values:
                    question_type = 'multiple_choice'
                    print(f"✅ Type: MULTIPLE CHOICE (fallback, {len(all_data_values)} options)")
                    for elem in all_data_values:
                        val = elem.get('data-value', '').strip()
                        if val:
                            options.append(val)
                            print(f"   - {val}")
                else:
                    question_type = 'short_text'
                    options = ["Default answer"]
                    print(f"⚠️  Type: SHORT TEXT (default)")
            
            if not options:
                options = ["Sample answer"]
            
            questions_data.append({
                'text': question_text,
                'entry_id': entry_id,
                'type': question_type,
                'options': options
            })
            
            print(f"✅ Added successfully!\n")
        
        # Summary
        print("="*70)
        print(f"🎉 PARSE COMPLETE")
        print("="*70)
        print(f"Total questions: {len(questions_data)}\n")
        
        for i, q in enumerate(questions_data):
            print(f"{i+1}. [{q['type'].upper()}] {q['text'][:50]}...")
            print(f"   Entry: {q['entry_id']}")
            print(f"   Options: {len(q['options'])}\n")
        
        # Test submit
        if questions_data:
            print("\n" + "="*70)
            print("🧪 TEST SUBMIT")
            print("="*70)
            
            submit_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
            print(f"Submit URL: {submit_url}\n")
            
            # Generate sample data
            form_data = {}
            for q in questions_data:
                form_data[q['entry_id']] = q['options'][0]
            
            print("Form data:")
            for key, val in form_data.items():
                print(f"   {key} = {val}")
            
            print("\n📤 Submitting...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            submit_resp = requests.post(submit_url, data=form_data, headers=headers, allow_redirects=True)
            print(f"✅ Status: {submit_resp.status_code}")
            print(f"Response URL: {submit_resp.url}")
            print(f"Response length: {len(submit_resp.text)}")
            
            if submit_resp.status_code == 200:
                print("✅ HTTP 200 - Likely successful!")
            else:
                print(f"❌ HTTP {submit_resp.status_code} - Failed!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test với URL của bạn
    url = input("Nhập URL Google Form: ").strip()
    test_parse_form(url)
