"""Test submit với 5 câu đầu"""
import requests

published_id = "1FAIpQLSepw7dKiFkjXwTizw_Ictx_BHXGPjLUAV1hqse3Ea231kwNUw"
submit_url = f"https://docs.google.com/forms/d/e/{published_id}/formResponse"
viewform_url = f"https://docs.google.com/forms/d/e/{published_id}/viewform"

# 5 câu đầu trong section "THÔNG TIN KHÁCH HÀNG"
payload = {
    'entry.792869442': 'Nam',  # Giới tính
    'entry.1894457611': '18-22',  # Nhóm tuổi
    'entry.1502774309': 'Thành phố lớn (Hà Nội, TP. Hồ Chí Minh, Đà Nẵng,...)',  # Khu vực
    'entry.1701785261': 'Học sinh/Sinh viên',  # Hiện đang là
    'entry.1424877347': 'Độc thân',  # Tình trạng
}

headers = {
    'User-Agent': 'Mozilla/5.0',
    'Referer': viewform_url
}

print("Testing submit with 5 questions from THÔNG TIN KHÁCH HÀNG section\n")
print(f"Submit URL: {submit_url}")
print(f"Payload: {payload}\n")

resp = requests.post(submit_url, data=payload, headers=headers, allow_redirects=False)

print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")

if resp.status_code == 200:
    print(f"\n✅ Submit SUCCESS!")
    print(f"Response contains: {len(resp.text)} chars")
    if 'formResponse' in resp.text or 'Your response has been recorded' in resp.text:
        print("✓ Confirmation text found")
else:
    print(f"\n❌ Submit FAILED")
    print(f"Response: {resp.text[:500]}")
