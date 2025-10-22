from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import random
import pandas as pd
from datetime import datetime
import io
import requests
from bs4 import BeautifulSoup
import re
import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

app = Flask(__name__)
CORS(app)

# Track background tasks
background_tasks = {}

forms = {}
responses = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create-form', methods=['POST'])
def create_form():
    data = request.json
    form_id = str(len(forms) + 1)
    forms[form_id] = {
        'title': data.get('title', 'Form'),
        'questions': data.get('questions', []),
        'created_at': datetime.now().isoformat()
    }
    return jsonify({'form_id': form_id, 'message': 'Tạo form thành công'})

@app.route('/api/generate-responses', methods=['POST'])
def generate_responses():
    data = request.json
    form_id = data.get('form_id')
    num_responses = int(data.get('num_responses', 100))
    accuracy_rate = float(data.get('accuracy_rate', 100))
    
    if form_id not in forms:
        return jsonify({'error': 'Form không tồn tại'}), 404
    
    questions = forms[form_id]['questions']
    generated_responses = []
    
    for i in range(num_responses):
        response = {'response_id': i + 1, 'timestamp': datetime.now().isoformat(), 'answers': []}
        for question in questions:
            correct = question['correct_answer']
            options = question['options']
            answer = correct if random.random() * 100 < accuracy_rate else random.choice([o for o in options if o != correct] or [correct])
            response['answers'].append({
                'question_id': question['id'],
                'answer': answer,
                'is_correct': answer == correct
            })
        generated_responses.append(response)
    
    if form_id not in responses:
        responses[form_id] = []
    responses[form_id].extend(generated_responses)
    
    stats = calculate_statistics(generated_responses, questions)
    return jsonify({'message': f'Tạo {num_responses} responses', 'statistics': stats})

def calculate_statistics(generated_responses, questions):
    total_answers = correct_answers = 0
    question_stats = {}
    
    for response in generated_responses:
        for answer in response['answers']:
            total_answers += 1
            if answer['is_correct']:
                correct_answers += 1
            q_id = answer['question_id']
            if q_id not in question_stats:
                question_stats[q_id] = {'correct': 0, 'total': 0}
            question_stats[q_id]['total'] += 1
            if answer['is_correct']:
                question_stats[q_id]['correct'] += 1
    
    for q_id in question_stats:
        stats = question_stats[q_id]
        stats['accuracy'] = round((stats['correct'] / stats['total'] * 100), 2)
        question = next((q for q in questions if q['id'] == q_id), None)
        if question:
            stats['question_text'] = question['text']
    
    return {
        'total_responses': len(generated_responses),
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'overall_accuracy': round((correct_answers / total_answers * 100), 2) if total_answers > 0 else 0,
        'question_stats': question_stats
    }

@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    data = request.json
    form_id = data.get('form_id')
    
    if form_id not in responses or form_id not in forms:
        return jsonify({'error': 'Không có dữ liệu'}), 404
    
    rows = []
    for resp in responses[form_id]:
        row = {'ID': resp['response_id'], 'Time': resp['timestamp']}
        for answer in resp['answers']:
            q = next((q for q in forms[form_id]['questions'] if q['id'] == answer['question_id']), None)
            if q:
                q_text = q.get('question', q.get('text', ''))
                row[q_text] = answer['answer']
                row[f"{q_text} (✓/✗)"] = '✓' if answer['is_correct'] else '✗'
        rows.append(row)
    
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Responses', index=False)
    output.seek(0)
    
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=f'responses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

@app.route('/api/import-json', methods=['POST'])
def import_json():
    questions_json = request.json.get('questions', [])
    if not questions_json:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400
    
    formatted = []
    for idx, q in enumerate(questions_json):
        if 'text' in q and 'options' in q:
            formatted.append({
                'id': q.get('id', f'q{idx + 1}'),
                'text': q['text'],
                'options': q['options'],
                'correct_answer': q.get('correct_answer', q['options'][0])
            })
    
    return jsonify({'message': f'Import {len(formatted)} câu hỏi', 'questions': formatted})

@app.route('/api/import-from-url', methods=['POST'])
def import_from_url():
    """Import câu hỏi từ Google Form URL - Support cả viewform và edit"""
    print("\n" + "="*60)
    print("🌐 IMPORT FROM URL REQUEST RECEIVED")
    print("="*60)
    
    try:
        url = request.json.get('url', '').strip()
        print(f"URL: {url}")
        
        if not url:
            print("❌ No URL provided")
            return jsonify({'error': 'Cung cấp URL'}), 400
        
        # Convert viewform URL to edit URL if needed
        if '/viewform' in url:
            # Convert: /viewform?usp=... → /edit
            url = url.split('/viewform')[0] + '/edit'
            print(f"✅ Converted to edit URL: {url}")
        
        form_id = extract_form_id(url)
        print(f"Form ID (from URL): {form_id}")
        
        if not form_id:
            print("❌ Invalid URL format")
            return jsonify({'error': 'URL không hợp lệ. Vui lòng dùng URL edit hoặc viewform'}), 400
        
        print("📥 Fetching form HTML...")
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.raise_for_status()
        print(f"✅ HTML fetched: {len(resp.text)} chars")
        
        # Check if form accepts responses
        if 'không còn chấp nhận phản hồi' in resp.text.lower() or 'no longer accepting' in resp.text.lower():
            print("⚠️ WARNING: Form may not be accepting responses")
            return jsonify({'error': 'Form không còn chấp nhận responses. Vui lòng kiểm tra form settings.'}), 400
        
        print("🔍 Parsing HTML with BeautifulSoup...")
        soup = BeautifulSoup(resp.text, 'html.parser')
        print("✅ BeautifulSoup created")
        
        # Try to find published form ID from edit page
        # Look for viewform link in edit page
        published_id = None
        
        # Method 1: Search in all script tags
        for script in soup.find_all('script'):
            if script.string:
                # Try multiple patterns
                patterns = [
                    r'/forms/d/e/([a-zA-Z0-9_-]+)/viewform',
                    r'"([a-zA-Z0-9_-]{56})"',  # Published IDs are typically 56 chars
                    r'formResponse["\']?\s*:\s*["\']([a-zA-Z0-9_-]{50,70})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        potential_id = match.group(1)
                        # Validate: published IDs start with "1FAIpQLS" or "1"
                        if len(potential_id) > 40:  # Published IDs are long
                            published_id = potential_id
                            print(f"✅ Found published ID (pattern {pattern[:30]}...): {published_id}")
                            break
                
                if published_id:
                    break
        
        # Method 2: Search in meta tags
        if not published_id:
            for meta in soup.find_all('meta'):
                content = meta.get('content', '')
                if 'viewform' in content or 'formResponse' in content:
                    match = re.search(r'/forms/d/e/([a-zA-Z0-9_-]+)', content)
                    if match:
                        published_id = match.group(1)
                        print(f"✅ Found published ID in meta tag: {published_id}")
                        break
        
        # Method 3: Search in entire HTML text
        if not published_id:
            # Look for the characteristic published ID pattern
            match = re.search(r'1FAIpQLS[a-zA-Z0-9_-]{48}', resp.text)
            if match:
                published_id = match.group(0)
                print(f"✅ Found published ID in HTML (1FAIpQLS pattern): {published_id}")
        
        if not published_id:
            print("⚠️ Could not find published ID, will use form ID")
            print("💡 TIP: Paste viewform URL instead of edit URL for better results")
            published_id = form_id
        
        # Parse questions - NEW CLEAN METHOD
        print("🔍 Starting parse_google_form_edit()...")
        questions_data = parse_google_form_edit(soup, resp.text)
        print(f"✅ Parse complete: {len(questions_data)} questions")
        
        if not questions_data:
            print("❌ No questions parsed!")
            return jsonify({'error': 'Không thể parse form. Vui lòng kiểm tra URL.'}), 400
        
        # Use published ID for submission URL
        submit_url = f"https://docs.google.com/forms/d/e/{published_id}/formResponse"
        print(f"📤 Submit URL: {submit_url}")
        
        print("✅ Returning success response")
        return jsonify({
            'form_id': form_id,
            'submit_url': submit_url,
            'questions': questions_data,
            'message': f'Đã import {len(questions_data)} câu hỏi từ form'
        })
    except Exception as e:
        print(f"\n❌ IMPORT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Lỗi: {str(e)}'}), 500

def parse_google_form_edit(soup, html_text):
    """
    Parse Google Form từ EDIT URL - CLEAN NEW VERSION
    Edit URL có structure rõ ràng hơn viewform
    """
    print("\n" + "="*60)
    print("🔍 PARSING GOOGLE FORM (EDIT MODE)")
    print("="*60)
    
    questions = []
    
    try:
        # Method 1: Parse từ FB_PUBLIC_LOAD_DATA_ JSON (chứa full form structure)
        print("\n📊 Method 1: Searching for FB_PUBLIC_LOAD_DATA_...")
        
        # Find the script tag containing form data
        scripts = soup.find_all('script')
        form_data = None
        
        for script in scripts:
            if script.string and 'FB_PUBLIC_LOAD_DATA_' in script.string:
                print("✅ Found FB_PUBLIC_LOAD_DATA_ script tag")
                script_text = script.string
                
                # Extract JSON data - format: var FB_PUBLIC_LOAD_DATA_ = [null, [[[...]]], ...];
                import re
                match = re.search(r'var FB_PUBLIC_LOAD_DATA_ = (\[.+?\]);', script_text, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    print(f"✅ Extracted JSON string: {len(json_str)} chars")
                    
                    try:
                        import json
                        form_data = json.loads(json_str)
                        print("✅ JSON parsed successfully")
                        
                        # DEBUG: Print structure
                        print("\n🔍 DEBUG: JSON Structure:")
                        print(f"   Type: {type(form_data)}")
                        print(f"   Length: {len(form_data) if isinstance(form_data, list) else 'N/A'}")
                        if isinstance(form_data, list) and len(form_data) > 1:
                            print(f"   form_data[1] type: {type(form_data[1])}")
                            if isinstance(form_data[1], list) and len(form_data[1]) > 1:
                                print(f"   form_data[1][1] type: {type(form_data[1][1])}")
                                print(f"   form_data[1][1] length: {len(form_data[1][1]) if isinstance(form_data[1][1], list) else 'N/A'}")
                                
                                # Print first question structure
                                if isinstance(form_data[1][1], list) and len(form_data[1][1]) > 0:
                                    print(f"\n📋 First item structure:")
                                    first_item = form_data[1][1][0]
                                    print(f"   Type: {type(first_item)}")
                                    if isinstance(first_item, list):
                                        print(f"   Length: {len(first_item)}")
                                        for idx, elem in enumerate(first_item[:10]):  # First 10 elements
                                            print(f"   [{idx}]: {type(elem)} = {str(elem)[:100]}")
                        
                        break
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON decode error: {e}")
                        continue
        
        if form_data and isinstance(form_data, list) and len(form_data) > 1:
            print("\n✅ Form data loaded from JSON")
            
            # Structure: form_data[1][1] contains array of questions
            # Each question: [entry_id, question_text, description, type, required, options...]
            try:
                questions_array = form_data[1][1]
                print(f"📋 Found {len(questions_array)} items in questions array")
                
                for idx, q_data in enumerate(questions_array):
                    if not isinstance(q_data, list) or len(q_data) < 4:
                        print(f"\n⚠️ Item {idx}: Too short (len={len(q_data) if isinstance(q_data, list) else 'N/A'}), skipping")
                        continue
                    
                    try:
                        print(f"\n📝 Parsing item {idx}:")
                        print(f"   Length: {len(q_data)}")
                        
                        # Parse question structure
                        entry_id = str(q_data[4][0][0]) if len(q_data) > 4 and q_data[4] else None
                        question_text = q_data[1] if len(q_data) > 1 else None
                        q_type = q_data[3] if len(q_data) > 3 else None
                        
                        print(f"   q_data[1] (text?): {str(q_data[1])[:80]}")
                        print(f"   q_data[3] (type?): {q_data[3]}")
                        print(f"   q_data[4] exists?: {len(q_data) > 4 and q_data[4] is not None}")
                        
                        if not entry_id or not question_text:
                            print(f"   ⚠️ Missing entry_id or question_text, skipping")
                            continue
                        
                        # Ensure entry_id format
                        if not entry_id.startswith('entry.'):
                            entry_id = f'entry.{entry_id}'
                        
                        print(f"   Entry ID: {entry_id}")
                        print(f"   Text: {question_text[:80]}...")
                        print(f"   Type Code: {q_type}")
                        
                        # Determine question type based on Google's type code
                        question_type = None
                        options = []
                        
                        if q_type == 2:  # Multiple choice (Radio)
                            question_type = 'multiple_choice'
                            # Options in q_data[4][0][1]
                            if len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 1:
                                options_data = q_data[4][0][1]
                                for opt in options_data:
                                    if isinstance(opt, list) and len(opt) > 0:
                                        option_text = opt[0]
                                        # Filter out empty strings
                                        if option_text and option_text.strip():
                                            options.append(option_text.strip())
                            print(f"   Type: Multiple Choice")
                            print(f"   Options: {options}")
                        
                        elif q_type == 4:  # Checkbox
                            question_type = 'checkbox'
                            # Options in q_data[4][0][1]
                            if len(q_data) > 4 and q_data[4] and len(q_data[4][0]) > 1:
                                options_data = q_data[4][0][1]
                                for opt in options_data:
                                    if isinstance(opt, list) and len(opt) > 0:
                                        option_text = opt[0]
                                        # Filter out empty strings
                                        if option_text and option_text.strip():
                                            options.append(option_text.strip())
                            print(f"   Type: Checkbox")
                            print(f"   Options: {options}")
                        
                        elif q_type == 0:  # Short answer (text input)
                            question_type = 'short_answer'
                            print(f"   Type: Short Answer")
                        
                        elif q_type == 1:  # Paragraph (textarea)
                            question_type = 'long_answer'
                            print(f"   Type: Long Answer")
                        
                        else:
                            print(f"   ⚠️ Unknown type code: {q_type}, skipping")
                            continue
                        
                        # Build question object
                        question = {
                            'question': question_text,
                            'type': question_type,
                            'entry_id': entry_id
                        }
                        
                        if options:
                            question['options'] = options
                        
                        questions.append(question)
                        print(f"   ✅ Added successfully")
                    
                    except Exception as e:
                        print(f"   ❌ Error parsing question {idx}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            
            except Exception as e:
                print(f"❌ Error accessing questions array: {e}")
                import traceback
                traceback.print_exc()
        
        else:
            print("⚠️ Method 1 failed, trying Method 2...")
            
            # Method 2: Fallback to HTML parsing (same as old method)
            print("\n📊 Method 2: HTML role-based parsing...")
            questions = parse_google_form_complete(soup, html_text)
    
    except Exception as e:
        print(f"❌ Parse error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print(f"✅ PARSE COMPLETE: {len(questions)} questions extracted")
    print("="*60)
    
    return questions


def parse_google_form_complete(soup, html_text):
    """
    Parse Google Form - CHUẨN GOOGLE:
    - Multiple Choice: 1 entry ID, chọn 1 giá trị
    - Checkbox: 1 entry ID, có thể chọn NHIỀU giá trị
    """
    questions_data = []
    
    print("\n" + "="*60)
    print("🔍 GOOGLE FORM PARSER V3 - STANDARD METHOD")
    print("="*60)
    
    try:
        # Extract entry IDs
        print("\n🔍 Extracting entry IDs...")
        
        # Method 1: Tìm trong HTML text (regex)
        entry_pattern = r'entry\.(\d{9,10})'
        entry_matches = re.findall(entry_pattern, html_text)
        
        seen = set()
        entry_ids_from_regex = []
        for match in entry_matches:
            entry_id = f'entry.{match}'
            if entry_id not in seen:
                seen.add(entry_id)
                entry_ids_from_regex.append(entry_id)
        
        print(f"   Method 1 (Regex): Found {len(entry_ids_from_regex)} entry IDs")
        
        # Method 2: Tìm trong HTML tags (input, textarea)
        entry_ids_from_tags = []
        for tag in soup.find_all(['input', 'textarea']):
            name = tag.get('name', '')
            if name.startswith('entry.') and name not in seen:
                seen.add(name)
                entry_ids_from_tags.append(name)
        
        print(f"   Method 2 (HTML tags): Found {len(entry_ids_from_tags)} additional entry IDs")
        
        # Combine both methods
        entry_ids = entry_ids_from_regex + entry_ids_from_tags
        
        print(f"✅ Total unique entry IDs: {len(entry_ids)}")
        
        # Debug: Print all entry IDs
        if len(entry_ids) <= 10:
            for i, eid in enumerate(entry_ids):
                print(f"   {i+1}. {eid}")
        
        # Find question containers - CHỈ LẤY CÓ HEADING
        print(f"\n🔍 Finding REAL questions (with heading)...")
        all_containers = soup.find_all('div', {'role': 'listitem'})
        
        # Filter: chỉ lấy container có heading
        question_containers = []
        for container in all_containers:
            heading = container.find('div', {'role': 'heading'})
            if heading:
                question_containers.append(container)
        
        print(f"✅ Found {len(question_containers)} real questions")
        
        # Parse từng câu hỏi
        for idx, container in enumerate(question_containers):
            try:
                # Get question text
                heading = container.find('div', {'role': 'heading'})
                question_text = heading.get_text(strip=True)
                
                print(f"\n{'─'*60}")
                print(f"📝 Question #{idx + 1}: {question_text}")
                
                # ✅ FIX: Tìm entry ID TỪ CHÍNH CONTAINER NÀY
                # Thay vì dùng entry_ids[idx] (có thể sai thứ tự)
                entry_id = None
                
                # Method 1: Tìm trong input/textarea tags TRONG container này
                for tag in container.find_all(['input', 'textarea']):
                    name = tag.get('name', '')
                    if name.startswith('entry.'):
                        entry_id = name
                        break
                
                # Method 2: Nếu không tìm thấy, tìm trong jsname attribute
                if not entry_id:
                    for tag in container.find_all(['div', 'span']):
                        data_params = tag.get('data-params', '')
                        if 'entry.' in data_params:
                            match = re.search(r'entry\.(\d{9,10})', data_params)
                            if match:
                                entry_id = f'entry.{match.group(1)}'
                                break
                
                # Method 3: Fallback - search trong text content của container
                if not entry_id:
                    container_html = str(container)
                    match = re.search(r'entry\.(\d{9,10})', container_html)
                    if match:
                        entry_id = f'entry.{match.group(1)}'
                
                if not entry_id:
                    print(f"❌ ERROR: Cannot find entry ID for this question!")
                    print(f"   Skipping...")
                    continue
                
                print(f"Entry ID: {entry_id}")
                
                # Detect type
                radio_buttons = container.find_all('div', {'role': 'radio'})
                checkboxes = container.find_all('div', {'role': 'checkbox'})
                text_inputs = container.find_all('input', {'type': 'text'})
                text_areas = container.find_all('textarea')
                
                options = []
                question_type = None
                
                if radio_buttons:
                    # MULTIPLE CHOICE
                    question_type = 'multiple_choice'
                    print(f"Type: MULTIPLE CHOICE")
                    
                    for radio in radio_buttons:
                        # Get aria-label
                        label = radio.get('aria-label', '').strip()
                        
                        if not label:
                            # Fallback: find content div near radio
                            parent = radio.find_parent('div', class_=True)
                            if parent:
                                # Find span with option text
                                option_span = parent.find('span', class_='aDTYNe')
                                if option_span:
                                    label = option_span.get_text(strip=True)
                                else:
                                    # Try any span
                                    spans = parent.find_all('span')
                                    for span in spans:
                                        text = span.get_text(strip=True)
                                        if text and text != question_text and len(text) < 200:
                                            label = text
                                            break
                        
                        if label and label not in options:
                            options.append(label)
                            print(f"   - {label}")
                
                elif checkboxes:
                    # CHECKBOX
                    question_type = 'checkbox'
                    print(f"Type: CHECKBOX")
                    
                    for checkbox in checkboxes:
                        # Get aria-label
                        label = checkbox.get('aria-label', '').strip()
                        
                        if not label:
                            # Fallback: find nearby content
                            parent = checkbox.find_parent('div', class_=True)
                            if parent:
                                # Find span with option text
                                option_span = parent.find('span', class_='aDTYNe')
                                if option_span:
                                    label = option_span.get_text(strip=True)
                                else:
                                    # Try finding content span
                                    content_div = parent.find('div', class_='vRMGwf')
                                    if content_div:
                                        spans = content_div.find_all('span')
                                        for span in spans:
                                            text = span.get_text(strip=True)
                                            if text and text != question_text and len(text) < 200:
                                                label = text
                                                break
                        
                        # Filter out "Other:" / "Mục khác:"
                        if label and label not in options:
                            if 'other' not in label.lower() and 'khác' not in label.lower():
                                options.append(label)
                                print(f"   - {label}")
                            else:
                                print(f"   - {label} (skipped)")
                
                elif text_inputs or text_areas:
                    # TEXT INPUT (Short answer or Long answer)
                    if text_areas:
                        question_type = 'long_answer'
                        print(f"Type: LONG ANSWER (Paragraph)")
                    else:
                        question_type = 'short_answer'
                        print(f"Type: SHORT ANSWER")
                    
                    # Text questions không có options, để trống
                    options = []
                    print(f"   (Text input field detected)")
                
                else:
                    print("⚠️  Unknown type")
                    continue
                
                # Chỉ check options cho multiple choice và checkbox
                if question_type in ['multiple_choice', 'checkbox'] and not options:
                    print("⚠️  No options found")
                    continue
                
                questions_data.append({
                    'id': f'q{len(questions_data) + 1}',
                    'text': question_text,
                    'entry_id': entry_id,
                    'type': question_type,
                    'options': options,
                    'correct_answer': options[0] if options else '',
                    'accuracy_rate': 80,
                    'text_answers': []  # Cho text questions
                })
                
                if options:
                    print(f"✅ Added with {len(options)} options!")
                else:
                    print(f"✅ Added text question!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"🎉 PARSE COMPLETE: {len(questions_data)} questions")
        print(f"{'='*60}\n")
        
        for i, q in enumerate(questions_data):
            q_text = q.get('question', q.get('text', ''))
            print(f"{i+1}. [{q['type'].upper()}] {q_text[:40]}...")
            print(f"   Entry: {q['entry_id']} | Options: {len(q.get('options', []))}")
    
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    return questions_data

@app.route('/api/analyze-form', methods=['POST'])
def analyze_form():
    """Phân tích form (legacy endpoint - redirect to import-from-url)"""
    return import_from_url()

def extract_form_id(url):
    """
    Extract form ID from Google Forms URL
    Supports both:
    - Edit URL: /forms/d/{FORM_ID}/edit
    - View URL: /forms/d/e/{PUB_ID}/viewform
    Returns the appropriate ID for formResponse endpoint
    """
    # Try to match /forms/d/{ID}/edit (returns ID directly)
    match = re.search(r'/forms/d/([a-zA-Z0-9_-]+)/', url)
    if match:
        return match.group(1)
    
    # Try to match /forms/d/e/{PUB_ID} (for published forms)
    match = re.search(r'/forms/d/e/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    
    return None

def extract_entry_ids(soup, html_text):
    field_mappings = []
    
    # Tìm trong HTML tags
    for tag in soup.find_all(['input', 'textarea']):
        name = tag.get('name', '')
        if name.startswith('entry.'):
            question_text = ''
            parent = tag.find_parent('div', class_=re.compile('Qr7Oae'))
            if parent:
                label = parent.find('span', class_=re.compile('M7eMe'))
                if label:
                    question_text = label.get_text(strip=True)
            field_mappings.append({'entry_id': name, 'question_text': question_text})
    
    # Tìm trong JavaScript
    if not field_mappings:
        matches = re.findall(r'\[\s*(\d{9,10})\s*,', html_text)
        for match in matches:
            field_mappings.append({'entry_id': f'entry.{match}', 'question_text': ''})
    
    # Remove duplicates
    seen = set()
    unique = []
    for m in field_mappings:
        if m['entry_id'] not in seen:
            seen.add(m['entry_id'])
            unique.append(m)
    
    return unique

def submit_responses_background(task_id, submit_url, questions, num_responses, delay):
    """Background task để submit responses - không block HTTP response"""
    results = {'total': num_responses, 'success': 0, 'failed': 0, 'errors': [], 'status': 'running', 'start_time': time.time()}
    background_tasks[task_id] = results
    
    # PRE-CALCULATE EXACT DISTRIBUTION
    response_plans = []
    
    # PRE-CALCULATE CHECKBOX SELECTIONS
    checkbox_selections = {}
    
    # PRE-CALCULATE TEXT ANSWERS
    # Phân phối text answers tuần tự, lặp lại nếu cần
    text_answer_assignments = {}
    
    for q in questions:
        if q.get('type') in ['short_answer', 'long_answer']:
            entry_id = q.get('entry_id')
            text_answers = q.get('text_answers', [])
            
            # Lọc bỏ dòng trống
            text_answers = [ans.strip() for ans in text_answers if ans.strip()]
            
            if not text_answers:
                print(f"\n⚠️  Text question '{q.get('text', '')}': No answers provided, will use empty string")
                text_answers = ['']  # Default empty
            
            print(f"\n📝 Text question: {q.get('text', '')}")
            print(f"   Type: {q.get('type')}")
            print(f"   Answers provided: {len(text_answers)} lines")
            print(f"   Responses needed: {num_responses}")
            
            # Phân phối tuần tự, lặp lại nếu cần
            assignments = []
            for i in range(num_responses):
                # Sử dụng modulo để lặp lại
                ans_index = i % len(text_answers)
                assignments.append(text_answers[ans_index])
            
            text_answer_assignments[entry_id] = assignments
            
            # Print sample
            print(f"   Sample assignments:")
            for i in range(min(5, num_responses)):
                print(f"     Response #{i+1}: '{assignments[i][:50]}{'...' if len(assignments[i]) > 50 else ''}'")
            
            if num_responses > len(text_answers):
                print(f"   ✅ Will repeat answers (cycling through {len(text_answers)} lines)")
    
    for q in questions:
        if q.get('type') == 'checkbox':
            entry_id = q.get('entry_id')
            options = q.get('options', [])
            option_rates = q.get('option_rates', {})
            
            # ✅ ĐẢM BẢO: Tổng tỉ lệ >= 100% đã được validate ở endpoint
            # Bây giờ phân phối để MỌI response có ít nhất 1 checkbox
            
            checkbox_selections[entry_id] = {}
            
            print(f"\n📊 Checkbox: {q.get('text', '')}")
            print(f"   Options: {len(options)}, Responses: {num_responses}")
            
            # BƯỚC 1: Khởi tạo selections (mỗi option là 1 set rỗng)
            for opt in options:
                checkbox_selections[entry_id][opt] = set()
            
            # BƯỚC 2: ĐẢM BẢO mỗi response có ít nhất 1 option
            # Strategy: Phân bổ base để cover 100% responses trước
            
            # Tính target count cho mỗi option
            option_targets = {}
            total_rate = 0
            for opt in options:
                rate = option_rates.get(opt, 0)
                total_rate += rate
                # Sử dụng round() thay vì int() để chính xác hơn
                # VD: 10 * 1% = 0.1 → round = 0, nhưng 100 * 1% = 1.0 → round = 1
                option_targets[opt] = round(num_responses * rate / 100)
            
            # Nếu tổng rate >= 100%, dùng phương pháp phân bổ đều trước
            if total_rate >= 100:
                # Phase 2a: Base assignment - đảm bảo mọi response có ít nhất 1 option
                all_response_indices = list(range(num_responses))
                random.shuffle(all_response_indices)
                
                # Normalize rates để tổng = 100% (cho base assignment)
                normalized_rates = {}
                for opt in options:
                    normalized_rates[opt] = (option_rates.get(opt, 0) / total_rate) * 100
                
                # Phân bổ responses theo normalized rate
                cumulative = 0
                for opt in options:
                    rate = normalized_rates[opt]
                    count = int(num_responses * rate / 100)
                    
                    # Assign responses
                    for idx in all_response_indices[cumulative:min(cumulative + count, num_responses)]:
                        checkbox_selections[entry_id][opt].add(idx)
                    
                    cumulative = min(cumulative + count, num_responses)
                
                # Handle rounding: remaining responses
                if cumulative < num_responses:
                    best_option = max(options, key=lambda x: option_rates.get(x, 0))
                    for idx in all_response_indices[cumulative:]:
                        checkbox_selections[entry_id][best_option].add(idx)
                
                print(f"   ✅ Phase 2a: Base assignment (mỗi response có 1 option)")
                
                # Phase 2b: Additional assignment - đạt đủ target rate
                for opt in options:
                    target_count = option_targets[opt]
                    current_count = len(checkbox_selections[entry_id][opt])
                    
                    if current_count < target_count:
                        # Cần thêm
                        needed = target_count - current_count
                        
                        # Lấy các response chưa có option này
                        available = [i for i in range(num_responses) if i not in checkbox_selections[entry_id][opt]]
                        random.shuffle(available)
                        
                        # Thêm vào
                        for idx in available[:needed]:
                            checkbox_selections[entry_id][opt].add(idx)
                
                print(f"   ✅ Phase 2b: Additional assignment (đạt target rate)")
                
            else:
                # Tổng < 100%: Phải force thêm vào option có rate cao nhất
                print(f"   ⚠️ Warning: Total rate = {total_rate}% < 100%")
                
                # Assign theo rate trước
                for opt in options:
                    target_count = option_targets[opt]
                    all_indices = list(range(num_responses))
                    random.shuffle(all_indices)
                    for idx in all_indices[:target_count]:
                        checkbox_selections[entry_id][opt].add(idx)
                
                # Tìm responses không có option nào
                for idx in range(num_responses):
                    has_option = False
                    for opt in options:
                        if idx in checkbox_selections[entry_id][opt]:
                            has_option = True
                            break
                    
                    if not has_option:
                        # Force thêm vào option có rate cao nhất
                        best_option = max(options, key=lambda x: option_rates.get(x, 0))
                        checkbox_selections[entry_id][best_option].add(idx)
            
            # Print final distribution
            for opt in options:
                final_count = len(checkbox_selections[entry_id][opt])
                print(f"   - '{opt}': {final_count}/{num_responses} ({final_count/num_responses*100:.1f}%)")
            
            # BƯỚC 4: VERIFY - Kiểm tra mọi response đều có ít nhất 1 option
            empty_responses = []
            for idx in range(num_responses):
                has_option = False
                for opt in options:
                    if idx in checkbox_selections[entry_id][opt]:
                        has_option = True
                        break
                if not has_option:
                    empty_responses.append(idx)
            
            if empty_responses:
                print(f"   ❌ ERROR: {len(empty_responses)} responses without options: {empty_responses[:5]}")
                # Force fix: Add to best option
                best_option = max(options, key=lambda x: option_rates.get(x, 0))
                for idx in empty_responses:
                    checkbox_selections[entry_id][best_option].add(idx)
                print(f"   → Fixed: Added to '{best_option}'")
            else:
                print(f"   ✅ Verified: All {num_responses} responses have at least 1 option")
    
    for i in range(num_responses):
        response_plan = {}
        
        for q in questions:
            entry_id = q.get('entry_id')
            if not entry_id:
                continue
            
            question_type = q.get('type', 'multiple_choice')
            options = q.get('options', [])
            option_rates = q.get('option_rates', {})
            
            if question_type == 'checkbox':
                # CHECKBOX: Check pre-calculated selections
                selected_options = []
                
                for opt in options:
                    if i in checkbox_selections[entry_id][opt]:
                        selected_options.append(opt)
                
                response_plan[entry_id] = {
                    'type': 'checkbox',
                    'value': selected_options,
                    'question_text': q.get('question', q.get('text', ''))
                }
                
            elif question_type in ['short_answer', 'long_answer']:
                # TEXT: Lấy từ pre-calculated assignments
                text_answer = ''
                if entry_id in text_answer_assignments:
                    text_answer = text_answer_assignments[entry_id][i]
                
                response_plan[entry_id] = {
                    'type': 'text',
                    'value': text_answer,
                    'question_text': q.get('question', q.get('text', ''))
                }
                
            else:
                # MULTIPLE CHOICE: Phân bổ CHÍNH XÁC
                # Ví dụ: 45%, 25%, 5%, 25% cho 100 responses
                # → 45 responses đầu chọn opt1, 25 tiếp theo chọn opt2, ...
                
                # Build cumulative ranges
                ranges = []
                cumulative = 0
                
                for opt in options:
                    rate = option_rates.get(opt, 0)
                    count = int(num_responses * rate / 100)
                    
                    if count > 0:
                        ranges.append({
                            'option': opt,
                            'start': cumulative,
                            'end': cumulative + count
                        })
                        cumulative += count
                
                # Handle rounding errors - assign remaining to first option
                if cumulative < num_responses and ranges:
                    ranges[-1]['end'] += (num_responses - cumulative)
                
                # Determine which option this response should use
                selected = options[0]  # Default
                for r in ranges:
                    if r['start'] <= i < r['end']:
                        selected = r['option']
                        break
                
                response_plan[entry_id] = {
                    'type': 'multiple_choice',
                    'value': selected,
                    'question_text': q.get('question', q.get('text', ''))
                }
        
        response_plans.append(response_plan)
    
    # Shuffle to randomize order (nhưng giữ nguyên tỉ lệ chính xác)
    random.shuffle(response_plans)
    
    print(f"\n🚀 Starting multi-threaded submission with {num_responses} responses...")
    
    # Helper function: Submit single response
    def submit_single_response(plan_index, plan, submit_url):
        """Submit 1 response, return (success, error_msg)"""
        try:
            form_data = {}
            
            # Build form_data from pre-calculated plan
            for entry_id, plan_item in plan.items():
                if plan_item['type'] == 'checkbox':
                    form_data[entry_id] = plan_item['value']
                elif plan_item['type'] == 'text':
                    form_data[entry_id] = plan_item['value']
                else:
                    form_data[entry_id] = plan_item['value']
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': submit_url.replace('formResponse', 'viewform'),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Encode form_data
            encoded_data = []
            for key, value in form_data.items():
                if isinstance(value, list):
                    for v in value:
                        encoded_data.append((key, v))
                else:
                    encoded_data.append((key, value))
            
            # Submit với retry
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    # Giảm timeout xuống 10s để nhanh hơn
                    resp = requests.post(submit_url, data=encoded_data, headers=headers, 
                                       allow_redirects=True, timeout=10)
                    
                    # DEBUG: Log first failed response
                    if resp.status_code != 200 and plan_index == 0:
                        print(f"\n❌ DEBUG First response failure:")
                        print(f"   Status: {resp.status_code}")
                        print(f"   URL: {submit_url}")
                        print(f"   Data sent: {encoded_data[:3]}")
                        print(f"   Response headers: {dict(resp.headers)}")
                        print(f"   Response URL: {resp.url}")
                        if 'login' in resp.url.lower() or 'signin' in resp.url.lower():
                            print(f"   ⚠️ REDIRECTED TO LOGIN - Form may require authentication")
                        print(f"   Response text: {resp.text[:500]}")
                    
                    if resp.status_code == 200:
                        return (True, None, plan_index)
                    elif resp.status_code >= 500 and attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    else:
                        return (False, f'HTTP {resp.status_code}', plan_index)
                        
                except requests.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(0.5)
                        continue
                    return (False, 'Timeout', plan_index)
                except Exception as e:
                    if plan_index == 0:
                        print(f"\n❌ DEBUG Exception on first request: {e}")
                    return (False, str(e), plan_index)
            
            return (False, 'Unknown error', plan_index)
            
        except Exception as e:
            return (False, str(e), plan_index)
    
    # Multi-threaded submission với ThreadPoolExecutor
    # Số thread = min(20, num_responses) để đạt tốc độ cao
    # 20 threads → ~100 requests trong 10-15s
    max_workers = min(20, num_responses)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tất cả tasks
        futures = []
        for i, plan in enumerate(response_plans):
            future = executor.submit(submit_single_response, i, plan, submit_url)
            futures.append(future)
            
            # Delay cực nhỏ giữa các lần tạo thread (chỉ để tránh spike)
            # 100 requests / 20 threads = 5 batches
            # Mỗi batch delay 0.05s → tổng ~0.25s để khởi tạo
            if i < num_responses - 1:
                time.sleep(0.05)
        
        # Thu thập kết quả khi hoàn thành
        completed = 0
        for future in as_completed(futures):
            success, error, idx = future.result()
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f'#{idx+1}: {error}')
            
            completed += 1
            
            # Update progress
            background_tasks[task_id] = results
            
            # Log progress mỗi 10 submissions
            if completed % 10 == 0 or completed == num_responses:
                print(f"✅ Progress: {completed}/{num_responses} ({results['success']} success, {results['failed']} failed)")
    
    # Update final status
    results['status'] = 'completed'
    results['end_time'] = time.time()
    results['duration'] = round(results['end_time'] - results['start_time'], 2)
    background_tasks[task_id] = results
    print(f"\n📊 Task {task_id}: {results['success']}/{results['total']} successful")
    print(f"⏱️  Total time: {results['duration']}s ({results['total']/results['duration']:.1f} requests/s)")

@app.route('/api/auto-submit', methods=['POST'])
def auto_submit():
    """
    Auto submit - BACKGROUND MODE:
    - Nhận request → Tạo background task → Return ngay
    - User có thể tắt browser, backend vẫn chạy tiếp
    - Dùng /api/task-status/<task_id> để check progress
    """
    data = request.json
    submit_url = data.get('submit_url')
    questions = data.get('questions', [])
    num_responses = int(data.get('num_responses', 10))
    delay = float(data.get('delay', 1))
    
    if not submit_url or not questions:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    # ✅ VALIDATION: Kiểm tra tỉ lệ trước khi submit
    validation_errors = []
    
    for q in questions:
        question_type = q.get('type', 'multiple_choice')
        
        # Skip validation cho text questions
        if question_type in ['short_answer', 'long_answer']:
            continue
        
        options = q.get('options', [])
        option_rates = q.get('option_rates', {})
        question_text = q.get('text', 'Câu hỏi không có tên')
        
        # Tính tổng tỉ lệ
        total_rate = sum(option_rates.get(opt, 0) for opt in options)
        
        if question_type == 'checkbox':
            # CHECKBOX: Tổng phải >= 100%
            if total_rate < 100:
                validation_errors.append(
                    f"❌ Checkbox '{question_text}': Tổng tỉ lệ = {total_rate}% (phải >= 100%)"
                )
        else:
            # RADIO (Multiple Choice): Tổng phải = 100%
            if total_rate != 100:
                validation_errors.append(
                    f"❌ Radio '{question_text}': Tổng tỉ lệ = {total_rate}% (phải = 100%)"
                )
    
    # Nếu có lỗi validation → Trả về lỗi
    if validation_errors:
        return jsonify({
            'error': 'Tỉ lệ không hợp lệ',
            'details': validation_errors
        }), 400
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Start background thread
    thread = threading.Thread(
        target=submit_responses_background,
        args=(task_id, submit_url, questions, num_responses, delay)
    )
    thread.daemon = True  # Thread sẽ tự tắt khi Flask tắt
    thread.start()
    
    print(f"\n🚀 Started background task {task_id} for {num_responses} responses")
    
    return jsonify({
        'task_id': task_id,
        'message': f'Đã bắt đầu gửi {num_responses} responses ở background. Bạn có thể tắt browser.',
        'status_url': f'/api/task-status/{task_id}'
    })

@app.route('/api/task-status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Check status của background task"""
    if task_id not in background_tasks:
        return jsonify({'error': 'Task không tồn tại'}), 404
    
    task = background_tasks[task_id]
    
    # Calculate progress percentage
    progress = 0
    if task['total'] > 0:
        completed = task['success'] + task['failed']
        progress = round((completed / task['total']) * 100, 1)
    
    # Calculate elapsed time and speed
    elapsed_time = 0
    speed = 0
    if 'start_time' in task:
        elapsed_time = round(time.time() - task['start_time'], 1)
        if elapsed_time > 0:
            completed = task['success'] + task['failed']
            speed = round(completed / elapsed_time, 1)
    
    response_data = {
        'task_id': task_id,
        'status': task['status'],
        'progress': progress,
        'total': task['total'],
        'success': task['success'],
        'failed': task['failed'],
        'elapsed_time': elapsed_time,
        'speed': speed,
        'errors': task['errors'][-5:] if len(task['errors']) > 5 else task['errors']
    }
    
    # Add duration if completed
    if task['status'] == 'completed' and 'duration' in task:
        response_data['duration'] = task['duration']
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
