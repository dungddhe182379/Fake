# 🚀 Hướng dẫn sử dụng cho form của bạn

## Form URL:
```
https://docs.google.com/forms/d/e/1FAIpQLSfMV9y2U5-ATOyoY2V-TaNlBzpquZF13Hk-WCtF1y7EqeoBrQ/viewform
```

## 📋 Bước 1: Import JSON

Copy đoạn JSON này và paste vào ô "Import từ JSON":

```json
[
  {
    "text": "Multiple Choice 1",
    "correct_answer": "Option 1-1",
    "options": ["Option 1-1", "Option 2-1", "Option 3-1", "Option 4"]
  },
  {
    "text": "Multiple Choice 2",
    "correct_answer": "Option 1-1",
    "options": ["Option 1-1", "Option 2", "Option 3"]
  }
]
```

**Quan trọng:** 
- Thay `"Option 1-1"`, `"Option 2-1"`, etc. bằng **text chính xác** trong Google Form của bạn
- Nếu form có "Other" option, bỏ qua không cần thêm vào

## 🎯 Bước 2: Chỉnh đáp án đúng

Sau khi import, **QUAN TRỌNG**:
- Kiểm tra lại đáp án đúng cho mỗi câu
- Mặc định tôi set `"Option 1-1"` là đúng
- Sửa lại nếu bạn muốn đáp án khác là đúng

## 🔍 Bước 3: Phân tích Form

1. Paste URL vào ô "URL Google Form"
2. Click "🔍 Phân tích Form"
3. Phải thấy: **"Tìm thấy 2 trường"**
4. Kiểm tra mapping:
   ```
   Field 1: entry.XXXXXXXXX → Multiple Choice 1
   Field 2: entry.YYYYYYYYY → Multiple Choice 2
   ```

## 🚀 Bước 4: Auto Submit

**Test trước:**
- Số responses: **3**
- Tỉ lệ đúng: 100% (để dễ check)
- Delay: 1 giây

Click "🚀 Bắt đầu Auto Submit"

## ✅ Bước 5: Kiểm tra

1. Vào Google Form
2. Click tab "**Responses**"
3. Phải thấy **3 responses mới**
4. Tất cả phải chọn "Option 1-1" (vì tỉ lệ đúng = 100%)

## 🎉 Nếu thành công:

Chạy lại với số lượng thật:
- Số responses: 50, 100, 200...
- Tỉ lệ đúng: 70%, 80%, 90% (tùy ý)
- Delay: 1-2 giây

## ❌ Nếu không thành công:

### Check 1: Form có public không?
- Vào Settings → Responses
- Uncheck "Limit to 1 response"
- Check "Anyone can respond"

### Check 2: Text có đúng không?
Trong Google Form, câu hỏi phải là **"Multiple Choice 1"** chứ không phải:
- ❌ "Multiple Choice 1*" (có dấu *)
- ❌ "Multiple choice 1" (chữ thường)
- ❌ "Multiple  Choice 1" (2 khoảng trắng)

Phải khớp **100%** kể cả dấu cách và chữ hoa/thường!

### Check 3: Options có đúng không?
Kiểm tra xem trong Google Form, các options có phải là:
- Option 1-1
- Option 2-1  
- Option 3-1
- Option 4

hay là text khác?

## 💡 Cách lấy text chính xác:

1. Mở Google Form
2. Bấm F12 (Developer Tools)
3. Vào tab "Elements"
4. Click vào câu hỏi đầu tiên
5. Tìm text chính xác trong HTML
6. Copy và paste vào JSON

## 📞 Nếu vẫn không được:

Gửi cho tôi:
1. Screenshot Google Form (toàn bộ câu hỏi và options)
2. Screenshot Console (F12 → Console tab)
3. Screenshot sau khi click "Phân tích Form"

Tôi sẽ tạo JSON chính xác cho bạn!

---

**Server:** http://localhost:5000  
**Làm mới trang (F5) và thử lại!**
