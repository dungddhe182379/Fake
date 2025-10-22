"""
Replacement for import_from_url() function in app.py

STRATEGY:
1. Always use EDIT URL for parsing (most complete questions)
2. Extract published ID from meta og:url (works for ALL form types)
3. Use published ID for formResponse submission
"""

@app.route('/api/import-from-url', methods=['POST'])
def import_from_url():
    """Import questions from Google Form URL - Supports both edit and viewform"""
    print("\n" + "="*60)
    print("IMPORT FROM URL REQUEST RECEIVED")
    print("="*60)
    
    try:
        original_url = request.json.get('url', '').strip()
        print(f"Original URL: {original_url}")
        
        if not original_url:
            print("No URL provided")
            return jsonify({'error': 'Cung cap URL'}), 400
        
        form_id = extract_form_id(original_url)
        print(f"Form ID: {form_id}")
        
        if not form_id:
            print("Invalid URL format")
            return jsonify({'error': 'URL khong hop le'}), 400
        
        # Always convert to EDIT URL for parsing
        edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"
        print(f"Using EDIT URL for parsing: {edit_url}")
        
        # Fetch edit page
        print("Fetching HTML...")
        resp = requests.get(edit_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        resp.raise_for_status()
        print(f"HTML fetched: {len(resp.text)} chars")
        
        # Check if form accepts responses
        if 'khong con chap nhan phan hoi' in resp.text.lower() or 'no longer accepting' in resp.text.lower():
            print("WARNING: Form may not accept responses")
            return jsonify({'error': 'Form khong con chap nhan responses'}), 400
        
        # Parse HTML
        soup = BeautifulSoup(resp.text, 'html.parser')
        print("BeautifulSoup created")
        
        # Parse questions from EDIT mode
        print("\nParsing questions from EDIT mode...")
        questions_data = parse_google_form_edit(soup, resp.text)
        
        if not questions_data:
            print("No questions parsed")
            return jsonify({'error': 'Khong the parse form'}), 400
        
        print(f"Successfully parsed {len(questions_data)} questions")
        
        # Extract published ID for submission
        print("\nExtracting published ID for submission...")
        published_id = extract_published_id(soup, resp.text, form_id)
        
        # Build submit URL
        submit_url = f"https://docs.google.com/forms/d/e/{published_id}/formResponse"
        print(f"Submit URL: {submit_url}")
        
        print("Returning success response")
        return jsonify({
            'form_id': form_id,
            'submit_url': submit_url,
            'questions': questions_data,
            'message': f'Da import {len(questions_data)} cau hoi tu form'
        })
        
    except Exception as e:
        print(f"\nIMPORT ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Loi: {str(e)}'}), 500
