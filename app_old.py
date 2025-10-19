from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import random
import json
import pandas as pd
from datetime import datetime
import io
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs

app = Flask(__name__)
CORS(app)

# Lưu trữ các form và responses trong memory (có thể thay bằng database)
forms = {}
responses = {}
form_configs = {}  # Lưu cấu hình Google Form để submit

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/create-form', methods=['POST'])
def create_form():
    """Tạo form mới với các câu hỏi và đáp án đúng"""
    data = request.json
    form_id = str(len(forms) + 1)
    
    forms[form_id] = {
        'title': data.get('title', 'Form không tiêu đề'),
        'questions': data.get('questions', []),
        'created_at': datetime.now().isoformat()
    }
    
    return jsonify({'form_id': form_id, 'message': 'Form đã được tạo thành công'})

@app.route('/api/generate-responses', methods=['POST'])
def generate_responses():
    """Tạo responses với tỉ lệ đúng theo yêu cầu"""
    data = request.json
    form_id = data.get('form_id')
    num_responses = int(data.get('num_responses', 100))
    accuracy_rate = float(data.get('accuracy_rate', 100))  # % đúng mong muốn
    
    if form_id not in forms:
        return jsonify({'error': 'Form không tồn tại'}), 404
    
    form = forms[form_id]
    questions = form['questions']
    
    generated_responses = []
    
    for i in range(num_responses):
        response = {
            'response_id': i + 1,
            'timestamp': datetime.now().isoformat(),
            'answers': []
        }
        
        for question in questions:
            question_id = question['id']
            correct_answer = question['correct_answer']
            all_options = question['options']
            
            # Quyết định câu trả lời đúng hay sai dựa trên accuracy_rate
            if random.random() * 100 < accuracy_rate:
                # Trả lời đúng
                answer = correct_answer
            else:
                # Trả lời sai - chọn ngẫu nhiên từ các đáp án khác
                wrong_options = [opt for opt in all_options if opt != correct_answer]
                if wrong_options:
                    answer = random.choice(wrong_options)
                else:
                    answer = correct_answer
            
            response['answers'].append({
                'question_id': question_id,
                'answer': answer,
                'is_correct': answer == correct_answer
            })
        
        generated_responses.append(response)
    
    # Lưu responses
    if form_id not in responses:
        responses[form_id] = []
    responses[form_id].extend(generated_responses)
    
    # Tính toán thống kê
    stats = calculate_statistics(generated_responses, questions)
    
    return jsonify({
        'message': f'Đã tạo {num_responses} responses thành công',
        'statistics': stats,
        'responses': generated_responses
    })

def calculate_statistics(generated_responses, questions):
    """Tính toán thống kê chi tiết"""
    total_answers = 0
    correct_answers = 0
    
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
    
    # Tính tỉ lệ đúng cho từng câu hỏi
    for q_id in question_stats:
        stats = question_stats[q_id]
        stats['accuracy'] = round((stats['correct'] / stats['total'] * 100), 2)
        
        # Thêm tên câu hỏi
        question = next((q for q in questions if q['id'] == q_id), None)
        if question:
            stats['question_text'] = question['text']
    
    overall_accuracy = round((correct_answers / total_answers * 100), 2) if total_answers > 0 else 0
    
    return {
        'total_responses': len(generated_responses),
        'total_answers': total_answers,
        'correct_answers': correct_answers,
        'overall_accuracy': overall_accuracy,
        'question_stats': question_stats
    }

@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    """Xuất kết quả ra file Excel"""
    data = request.json
    form_id = data.get('form_id')
    
    if form_id not in responses or form_id not in forms:
        return jsonify({'error': 'Không có dữ liệu để xuất'}), 404
    
    form = forms[form_id]
    form_responses = responses[form_id]
    
    # Tạo DataFrame
    rows = []
    for resp in form_responses:
        row = {'Response ID': resp['response_id'], 'Timestamp': resp['timestamp']}
        
        for answer in resp['answers']:
            question = next((q for q in form['questions'] if q['id'] == answer['question_id']), None)
            if question:
                row[question['text']] = answer['answer']
                row[f"{question['text']} (Đúng/Sai)"] = 'Đúng' if answer['is_correct'] else 'Sai'
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Tạo Excel file trong memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Responses', index=False)
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'form_responses_{form_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    )

@app.route('/api/get-forms', methods=['GET'])
def get_forms():
    """Lấy danh sách tất cả forms"""
    return jsonify({'forms': forms})

@app.route('/api/get-responses/<form_id>', methods=['GET'])
def get_responses(form_id):
    """Lấy responses của một form cụ thể"""
    if form_id not in responses:
        return jsonify({'responses': []})
    
    return jsonify({'responses': responses[form_id]})

@app.route('/api/import-from-url', methods=['POST'])
def import_from_url():
    """Import form từ URL (Google Form hoặc form khác)"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'Vui lòng cung cấp URL'}), 400
    
    try:
        # Fetch HTML từ URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        questions = []
        
        # Try to parse Google Form format
        if 'docs.google.com/forms' in url:
            questions = parse_google_form(soup)
        else:
            # Generic HTML form parser
            questions = parse_generic_form(soup)
        
        if not questions:
            return jsonify({'error': 'Không thể trích xuất câu hỏi từ form. Vui lòng thử import JSON thủ công.'}), 400
        
        return jsonify({
            'message': f'Đã import thành công {len(questions)} câu hỏi',
            'questions': questions
        })
    
    except requests.RequestException as e:
        return jsonify({'error': f'Không thể truy cập URL: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Lỗi khi parse form: {str(e)}'}), 500

def parse_google_form(soup):
    """Parse Google Form HTML"""
    questions = []
    
    # Google Forms structure may vary, this is a basic parser
    # Note: Google Forms may require authentication or have dynamic content
    
    question_divs = soup.find_all('div', class_=re.compile('Qr7Oae|freebirdFormviewerViewItemsItemItem'))
    
    for idx, div in enumerate(question_divs):
        try:
            # Try to find question text
            question_text = div.find('span', class_=re.compile('M7eMe|exportLabel'))
            if not question_text:
                continue
            
            # Try to find options
            options = []
            option_elements = div.find_all('span', class_=re.compile('aDTYNe|exportItemContent'))
            
            for opt in option_elements:
                opt_text = opt.get_text(strip=True)
                if opt_text:
                    options.append(opt_text)
            
            if question_text and len(options) >= 2:
                questions.append({
                    'id': f'q{idx + 1}',
                    'text': question_text.get_text(strip=True),
                    'options': options,
                    'correct_answer': options[0] if options else ''  # Default first option
                })
        except:
            continue
    
    return questions

def parse_generic_form(soup):
    """Parse generic HTML form"""
    questions = []
    
    # Look for common form structures
    # Try to find radio button groups or select options
    
    fieldsets = soup.find_all(['fieldset', 'div'], class_=re.compile('question|form-group'))
    
    for idx, fieldset in enumerate(fieldsets):
        try:
            # Find question text (usually in label or legend)
            question_text = fieldset.find(['legend', 'label', 'h3', 'h4'])
            if not question_text:
                continue
            
            # Find options (radio buttons, checkboxes, or select options)
            options = []
            
            # Try radio/checkbox inputs
            inputs = fieldset.find_all('input', type=['radio', 'checkbox'])
            if inputs:
                for inp in inputs:
                    label = fieldset.find('label', {'for': inp.get('id')})
                    if label:
                        options.append(label.get_text(strip=True))
                    elif inp.get('value'):
                        options.append(inp.get('value'))
            
            # Try select options
            if not options:
                select = fieldset.find('select')
                if select:
                    opt_elements = select.find_all('option')
                    options = [opt.get_text(strip=True) for opt in opt_elements if opt.get_text(strip=True)]
            
            if question_text and len(options) >= 2:
                questions.append({
                    'id': f'q{idx + 1}',
                    'text': question_text.get_text(strip=True),
                    'options': options,
                    'correct_answer': options[0]  # Default first option
                })
        except:
            continue
    
    return questions

@app.route('/api/import-json', methods=['POST'])
def import_json():
    """Import questions từ JSON format"""
    data = request.json
    questions_json = data.get('questions', [])
    
    if not questions_json or not isinstance(questions_json, list):
        return jsonify({'error': 'Dữ liệu JSON không hợp lệ'}), 400
    
    # Validate and format questions
    formatted_questions = []
    for idx, q in enumerate(questions_json):
        if isinstance(q, dict) and 'text' in q and 'options' in q:
            formatted_questions.append({
                'id': q.get('id', f'q{idx + 1}'),
                'text': q.get('text', ''),
                'options': q.get('options', []),
                'correct_answer': q.get('correct_answer', q.get('options', [''])[0])
            })
    
    if not formatted_questions:
        return jsonify({'error': 'Không có câu hỏi hợp lệ trong JSON'}), 400
    
    return jsonify({
        'message': f'Đã import thành công {len(formatted_questions)} câu hỏi',
        'questions': formatted_questions
    })

@app.route('/api/analyze-form', methods=['POST'])
def analyze_form():
    """Phân tích Google Form để lấy thông tin submit"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'Vui lòng cung cấp URL'}), 400
    
    try:
        # Fetch form HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract form action URL
        form_id = extract_form_id(url)
        if not form_id:
            return jsonify({'error': 'Không thể trích xuất Form ID từ URL'}), 400
        
        # Build submit URL
        submit_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
        
        # Extract field mappings (entry IDs)
        field_mappings = extract_field_mappings(soup)
        
        if not field_mappings:
            return jsonify({
                'error': 'Không thể trích xuất field mappings. Form có thể yêu cầu authentication.',
                'submit_url': submit_url,
                'form_id': form_id
            }), 400
        
        return jsonify({
            'form_id': form_id,
            'submit_url': submit_url,
            'field_mappings': field_mappings,
            'message': f'Đã phân tích form. Tìm thấy {len(field_mappings)} trường.'
        })
    
    except Exception as e:
        return jsonify({'error': f'Lỗi khi phân tích form: {str(e)}'}), 500

def extract_form_id(url):
    """Extract form ID from Google Form URL"""
    # Pattern: /forms/d/e/{formId}/ or /forms/d/{formId}/
    patterns = [
        r'/forms/d/e/([a-zA-Z0-9_-]+)',
        r'/forms/d/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def extract_field_mappings(soup):
    """Extract entry IDs from Google Form HTML"""
    field_mappings = []
    
    # Look for entry.XXXXXXX patterns in the HTML
    entry_pattern = re.compile(r'entry\.(\d+)')
    
    # Search in attributes
    for tag in soup.find_all(['input', 'textarea', 'select']):
        name = tag.get('name', '')
        if name.startswith('entry.'):
            entry_id = name
            
            # Try to find associated label/question
            question_text = ''
            parent = tag.find_parent(['div', 'fieldset'])
            if parent:
                label = parent.find(['label', 'legend', 'div'], class_=re.compile('freebirdFormviewer|exportLabel|M7eMe'))
                if label:
                    question_text = label.get_text(strip=True)
            
            field_mappings.append({
                'entry_id': entry_id,
                'question_text': question_text
            })
    
    # If no fields found in tags, search in JavaScript/data
    if not field_mappings:
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                matches = entry_pattern.findall(script.string)
                for match in matches:
                    field_mappings.append({
                        'entry_id': f'entry.{match}',
                        'question_text': ''
                    })
    
    # Remove duplicates
    seen = set()
    unique_mappings = []
    for mapping in field_mappings:
        if mapping['entry_id'] not in seen:
            seen.add(mapping['entry_id'])
            unique_mappings.append(mapping)
    
    return unique_mappings

@app.route('/api/auto-submit', methods=['POST'])
def auto_submit():
    """Tự động submit responses vào Google Form"""
    data = request.json
    form_id = data.get('form_id')
    submit_url = data.get('submit_url')
    field_mappings = data.get('field_mappings', [])
    questions = data.get('questions', [])
    num_responses = int(data.get('num_responses', 10))
    accuracy_rate = float(data.get('accuracy_rate', 100))
    delay = float(data.get('delay', 1))  # Delay between submissions
    
    if not submit_url or not field_mappings or not questions:
        return jsonify({'error': 'Thiếu thông tin cần thiết để submit'}), 400
    
    if len(field_mappings) != len(questions):
        return jsonify({
            'error': f'Số lượng fields ({len(field_mappings)}) không khớp với số câu hỏi ({len(questions)})'
        }), 400
    
    results = {
        'total': num_responses,
        'success': 0,
        'failed': 0,
        'errors': []
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    for i in range(num_responses):
        try:
            # Generate response data
            form_data = {}
            
            for idx, question in enumerate(questions):
                if idx < len(field_mappings):
                    entry_id = field_mappings[idx]['entry_id']
                    correct_answer = question['correct_answer']
                    all_options = question['options']
                    
                    # Decide correct or wrong answer based on accuracy_rate
                    if random.random() * 100 < accuracy_rate:
                        answer = correct_answer
                    else:
                        wrong_options = [opt for opt in all_options if opt != correct_answer]
                        answer = random.choice(wrong_options) if wrong_options else correct_answer
                    
                    form_data[entry_id] = answer
            
            # Submit to Google Form
            response = requests.post(submit_url, data=form_data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                results['success'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f'Response {i+1}: HTTP {response.status_code}')
            
            # Delay to avoid rate limiting
            if i < num_responses - 1:
                time.sleep(delay)
        
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f'Response {i+1}: {str(e)}')
    
    return jsonify({
        'message': f'Đã submit {results["success"]}/{results["total"]} responses thành công',
        'results': results
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
