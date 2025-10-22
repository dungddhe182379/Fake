"""Test viewform parser directly using app.py functions"""
import sys
import requests
from bs4 import BeautifulSoup

# Import parser functions from app.py
from app import parse_google_form_viewform

form_id = "1ummF3CUEX0OhJfFZszk_04AGpbUFx3uDmsicysHL9ew"
published_id = "1FAIpQLSfAzjNq_wsV_7z-b4fvQHSHFtyNmZ_LRgxrgSc6gIEJK4BuVA"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

print(f"Testing: {viewform_url}\n")

resp = requests.get(viewform_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
print(f"Status: {resp.status_code}")

soup = BeautifulSoup(resp.text, 'html.parser')
questions, pub_id = parse_google_form_viewform(soup, resp.text)

print(f"\n{'='*60}")
print(f"RESULT: {len(questions)} questions parsed")
print(f"Published ID: {pub_id}")
print(f"{'='*60}\n")

for q in questions:
    print(f"Q: {q['question'][:50]}...")
    print(f"   Type: {q['type']}, Entry: {q['entry_id']}")
    if 'options' in q:
        print(f"   Options: {q['options'][:3]}")
    print()
