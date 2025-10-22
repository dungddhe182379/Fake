"""Debug: Tìm câu hỏi bị skip"""
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
    print("PHÂN TÍCH CÁC CÂU HỎI TRONG SECTION 'THÔNG TIN KHÁCH HÀNG'")
    print("="*80)
    
    in_section = False
    section_questions = []
    
    for idx, q_data in enumerate(questions_array):
        if not isinstance(q_data, list) or len(q_data) < 4:
            continue
        
        q_text = q_data[1] if len(q_data) > 1 else None
        q_type = q_data[3] if len(q_data) > 3 else None
        
        # Check if this is section header
        if q_type == 8 and "THÔNG TIN KHÁCH HÀNG" in str(q_text):
            in_section = True
            print(f"\n📌 SECTION HEADER: {q_text}")
            continue
        
        # Check if new section started
        if q_type == 8 and in_section:
            print(f"\n📌 NEW SECTION: {q_text}")
            break
        
        if in_section:
            has_entry = len(q_data) > 4 and q_data[4] is not None
            entry_id = None
            
            if has_entry and isinstance(q_data[4], list) and len(q_data[4]) > 0:
                if isinstance(q_data[4][0], list) and len(q_data[4][0]) > 0:
                    entry_id = q_data[4][0][0]
            
            section_questions.append({
                'index': idx,
                'question': q_text,
                'type': q_type,
                'has_entry': has_entry,
                'entry_id': entry_id,
                'q_data_length': len(q_data),
                'q_data_4': q_data[4] if len(q_data) > 4 else None
            })
    
    print(f"\nFound {len(section_questions)} questions in section:\n")
    
    for q in section_questions:
        print(f"Question {q['index']}: {q['question']}")
        print(f"  Type: {q['type']}")
        print(f"  Has q_data[4]: {q['has_entry']}")
        print(f"  Entry ID: {q['entry_id']}")
        print(f"  q_data[4] content: {q['q_data_4']}")
        print()
