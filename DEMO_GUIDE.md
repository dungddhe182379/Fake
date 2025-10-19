# Demo: Cách lấy link và submit vào Google Form

## 📝 Bước 1: Tạo Google Form Test

1. Truy cập: https://docs.google.com/forms
2. Click "Blank Form" (Form trống)
3. Tạo form đơn giản:

### Form mẫu:
**Tiêu đề:** Test Form

**Câu 1:** Bạn có thích sản phẩm này?
- Có
- Không
- Chưa thử

**Câu 2:** Đánh giá từ 1-5 sao
- 1 sao
- 2 sao
- 3 sao
- 4 sao
- 5 sao

4. Click "Settings" (⚙️) → "Responses"
   - Uncheck: "Limit to 1 response"
   - Check: "Accept responses"

5. Click "Send" → Copy link
   - Link sẽ có dạng: `https://docs.google.com/forms/d/e/1FAIpQLSd.../viewform`

## 🎯 Bước 2: Setup trong App

### A. Nhập câu hỏi (theo đúng thứ tự!)

```
Câu hỏi 1:
- Nội dung: "Bạn có thích sản phẩm này?"
- Đáp án đúng: "Có"
- Đáp án khác:
  Không
  Chưa thử

Câu hỏi 2:
- Nội dung: "Đánh giá từ 1-5 sao"
- Đáp án đúng: "5 sao"
- Đáp án khác:
  1 sao
  2 sao
  3 sao
  4 sao
```

### B. Hoặc dùng JSON Import:

```json
[
  {
    "text": "Bạn có thích sản phẩm này?",
    "correct_answer": "Có",
    "options": ["Có", "Không", "Chưa thử"]
  },
  {
    "text": "Đánh giá từ 1-5 sao",
    "correct_answer": "5 sao",
    "options": ["1 sao", "2 sao", "3 sao", "4 sao", "5 sao"]
  }
]
```

## 🚀 Bước 3: Auto Submit

1. Click "✅ Tạo Form"
2. Scroll xuống "🤖 Tự động Submit vào Google Form"
3. Paste link Google Form
4. Click "🔍 Phân tích Form"
5. Kiểm tra mapping:
   ```
   Field 1: entry.123456789 → Bạn có thích sản phẩm này?
   Field 2: entry.987654321 → Đánh giá từ 1-5 sao
   ```
6. Set:
   - Số responses: 10 (test thử)
   - Tỉ lệ đúng: 80%
   - Delay: 1 giây
7. Click "🚀 Bắt đầu Auto Submit"

## ✅ Bước 4: Kiểm tra kết quả

1. Vào Google Form
2. Click tab "Responses"
3. Bạn sẽ thấy 10 responses mới
4. Khoảng 80% sẽ chọn "Có" và "5 sao"

## 🔍 Debug: Cách xem entry IDs thủ công

Nếu muốn tự check entry IDs:

1. Mở Google Form
2. Bấm F12 (Developer Tools)
3. Click vào một đáp án bất kỳ
4. Trong Elements tab, tìm:
   ```html
   <input name="entry.1234567890" ...>
   ```
5. `entry.1234567890` là field ID của câu hỏi đó

## 📊 Expected Results

Với cài đặt:
- Số responses: 100
- Tỉ lệ đúng: 80%

Kết quả dự kiến trong Google Form:
- Câu 1: ~80 người chọn "Có", ~20 người chọn random "Không" hoặc "Chưa thử"
- Câu 2: ~80 người chọn "5 sao", ~20 người chọn random 1-4 sao

## 🎓 Tips

1. **Luôn test với 5-10 responses trước** để đảm bảo mapping đúng
2. **Xóa test responses** trước khi chạy lượng lớn (trong Responses → Delete all)
3. **Monitor rate limit:** Nếu bị fail, chờ 5-10 phút rồi thử lại
4. **Check từng bước:** Form → Analyze → Small Test → Full Run

## ⚠️ Common Mistakes

### Sai lầm 1: Thứ tự không khớp
```
Google Form:
1. Tên
2. Email  
3. Câu hỏi

App:
1. Câu hỏi  ← SAI! Phải có Tên và Email trước
```

### Sai lầm 2: Text không khớp chính xác
```
Google Form: "Bạn có thích sản phẩm này?"
App: "Bạn thích sản phẩm không?"  ← SAI! Phải giống 100%
```

### Sai lầm 3: Options thiếu hoặc sai
```
Google Form: ["Rất tốt", "Tốt", "Bình thường", "Tệ"]
App: ["Rất tốt", "Tốt", "Tệ"]  ← SAI! Thiếu "Bình thường"
```

---

**Good luck! 🎉**
