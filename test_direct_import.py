"""Test direct import API"""
import requests
import json

url = "http://localhost:5000/import_from_url"
form_url = "https://docs.google.com/forms/d/1ummF3CUEX0OhJfFZszk_04AGpbUFx3uDmsicysHL9ew/edit"

print(f"Testing: {form_url}\n")

response = requests.post(url, json={'form_url': form_url})
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
