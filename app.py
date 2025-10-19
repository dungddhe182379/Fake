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

app = Flask(__name__)
CORS(app)

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
                row[q['text']] = answer['answer']
                row[f"{q['text']} (✓/✗)"] = '✓' if answer['is_correct'] else '✗'
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
    """Import câu hỏi từ Google Form URL"""
    print("\n" + "="*60)
    print("🌐 IMPORT FROM URL REQUEST RECEIVED")
    print("="*60)
    
    try:
        url = request.json.get('url', '').strip()
        print(f"URL: {url}")
        
        if not url:
            print("❌ No URL provided")
            return jsonify({'error': 'Cung cấp URL'}), 400
        
        form_id = extract_form_id(url)
        print(f"Form ID: {form_id}")
        
        if not form_id:
            print("❌ Invalid URL format")
            return jsonify({'error': 'URL không hợp lệ'}), 400
        
        print("📥 Fetching form HTML...")
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.raise_for_status()
        print(f"✅ HTML fetched: {len(resp.text)} chars")
        
        print("🔍 Parsing HTML with BeautifulSoup...")
        soup = BeautifulSoup(resp.text, 'html.parser')
        print("✅ BeautifulSoup created")
        
        # Parse cả câu hỏi và entry IDs cùng lúc
        print("🔍 Starting parse_google_form_complete()...")
        questions_data = parse_google_form_complete(soup, resp.text)
        print(f"✅ Parse complete: {len(questions_data)} questions")
        
        if not questions_data:
            print("❌ No questions parsed!")
            return jsonify({'error': 'Không thể parse form. Thử import JSON thủ công.'}), 400
        
        submit_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
        print(f"Submit URL: {submit_url}")
        
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
        entry_pattern = r'entry\.(\d{9,10})'
        entry_matches = re.findall(entry_pattern, html_text)
        
        seen = set()
        entry_ids = []
        for match in entry_matches:
            entry_id = f'entry.{match}'
            if entry_id not in seen:
                seen.add(entry_id)
                entry_ids.append(entry_id)
        
        print(f"✅ Found {len(entry_ids)} entry IDs")
        
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
                if idx >= len(entry_ids):
                    break
                
                # Get question text
                heading = container.find('div', {'role': 'heading'})
                question_text = heading.get_text(strip=True)
                entry_id = entry_ids[idx]
                
                print(f"\n{'─'*60}")
                print(f"📝 Question #{idx + 1}: {question_text}")
                print(f"Entry ID: {entry_id}")
                
                # Detect type
                radio_buttons = container.find_all('div', {'role': 'radio'})
                checkboxes = container.find_all('div', {'role': 'checkbox'})
                
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
                
                else:
                    print("⚠️  Unknown type")
                    continue
                
                if not options:
                    print("⚠️  No options found")
                    continue
                
                questions_data.append({
                    'id': f'q{len(questions_data) + 1}',
                    'text': question_text,
                    'entry_id': entry_id,
                    'type': question_type,
                    'options': options,
                    'correct_answer': options[0],
                    'accuracy_rate': 80
                })
                
                print(f"✅ Added with {len(options)} options!")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"\n{'='*60}")
        print(f"🎉 PARSE COMPLETE: {len(questions_data)} questions")
        print(f"{'='*60}\n")
        
        for i, q in enumerate(questions_data):
            print(f"{i+1}. [{q['type'].upper()}] {q['text'][:40]}...")
            print(f"   Entry: {q['entry_id']} | Options: {len(q['options'])}")
    
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
    match = re.search(r'/forms/d/e/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'/forms/d/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

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

@app.route('/api/auto-submit', methods=['POST'])
def auto_submit():
    """
    Auto submit - PHÂN BỔ % CHO TỪNG OPTION:
    - Multiple Choice: Random theo phân bổ % (tổng = 100%)
    - Checkbox: Mỗi option độc lập với tỉ lệ riêng (0-100%)
    """
    data = request.json
    submit_url = data.get('submit_url')
    questions = data.get('questions', [])
    num_responses = int(data.get('num_responses', 10))
    delay = float(data.get('delay', 1))
    
    if not submit_url or not questions:
        return jsonify({'error': 'Thiếu thông tin'}), 400
    
    results = {'total': num_responses, 'success': 0, 'failed': 0, 'errors': [], 'debug_info': []}
    
    for i in range(num_responses):
        try:
            form_data = {}
            debug_answers = {}
            
            for q in questions:
                entry_id = q.get('entry_id')
                if not entry_id:
                    continue
                
                question_type = q.get('type', 'multiple_choice')
                options = q.get('options', [])
                option_rates = q.get('option_rates', {})
                
                if question_type == 'checkbox':
                    # CHECKBOX: Mỗi option độc lập, có thể chọn NHIỀU
                    # Random cho TỪNG checkbox xem có tick không
                    selected_options = []
                    
                    for opt in options:
                        rate = option_rates.get(opt, 50)  # Default 50%
                        if random.random() * 100 < rate:
                            selected_options.append(opt)
                    
                    # Nếu không chọn gì, chọn random 1 cái
                    if not selected_options:
                        selected_options = [random.choice(options)]
                    
                    # Google Form checkbox: SUBMIT NHIỀU GIÁ TRỊ
                    # Cách 1: Submit as list (requests sẽ encode đúng)
                    # Cách 2: Submit multiple keys with same name
                    # Google Form chấp nhận: entry.xxx=value1&entry.xxx=value2
                    
                    # Sử dụng cách submit list - requests tự encode
                    if entry_id in form_data:
                        # Nếu đã có, append vào list
                        if isinstance(form_data[entry_id], list):
                            form_data[entry_id].extend(selected_options)
                        else:
                            form_data[entry_id] = [form_data[entry_id]] + selected_options
                    else:
                        # Submit tất cả options đã chọn
                        form_data[entry_id] = selected_options
                    
                    debug_answers[q['text']] = ', '.join(selected_options)
                
                else:
                    # MULTIPLE CHOICE: Random theo phân phối %
                    # Tính cumulative distribution
                    total = sum(option_rates.values())
                    
                    if total == 0:
                        # Fallback: equal distribution
                        selected = random.choice(options)
                    else:
                        # Weighted random
                        rand_val = random.random() * total
                        cumulative = 0
                        selected = options[0]
                        
                        for opt in options:
                            rate = option_rates.get(opt, 0)
                            cumulative += rate
                            if rand_val <= cumulative:
                                selected = opt
                                break
                    
                    form_data[entry_id] = selected
                    debug_answers[q['text']] = selected
            
            # Debug
            if i == 0:
                print(f"\n🔍 DEBUG Submit #{i+1}:")
                print(f"Form data: {form_data}")
                print(f"Answers: {debug_answers}")
                results['debug_info'].append({
                    'submit_url': submit_url,
                    'form_data': form_data,
                    'answers': debug_answers
                })
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': submit_url.replace('formResponse', 'viewform'),
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Encode form_data: Convert lists to multiple key-value pairs
            # Google Form checkbox cần: entry.xxx=val1&entry.xxx=val2&entry.xxx=val3
            encoded_data = []
            for key, value in form_data.items():
                if isinstance(value, list):
                    # Multiple values for same key (checkbox)
                    for v in value:
                        encoded_data.append((key, v))
                else:
                    # Single value
                    encoded_data.append((key, value))
            
            resp = requests.post(submit_url, data=encoded_data, headers=headers, allow_redirects=True, timeout=10)
            
            if i == 0:
                print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f'#{i+1}: HTTP {resp.status_code}')
            
            if i < num_responses - 1:
                time.sleep(delay)
                
        except Exception as e:
            results['failed'] += 1
            error_msg = f'#{i+1}: {str(e)}'
            results['errors'].append(error_msg)
            print(f"❌ Error: {error_msg}")
    
    print(f"\n📊 Results: {results['success']}/{results['total']} successful")
    return jsonify({'message': f'{results["success"]}/{results["total"]} thành công', 'results': results})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
