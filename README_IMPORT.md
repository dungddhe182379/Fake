# 📊 Google Form Simulator - Kiểm soát tỉ lệ đúng

Ứng dụng web cho phép bạn tạo form giả lập và tạo responses với tỉ lệ đúng theo mong muốn.

## ✨ Tính năng

- ✅ Tạo form với nhiều câu hỏi trắc nghiệm
- 🔗 **Import câu hỏi từ form online (Google Form, etc.)**
- 📄 **Import từ JSON format**
- 🎯 Kiểm soát chính xác tỉ lệ đúng (0-100%)
- 📈 Thống kê chi tiết theo từng câu hỏi
- 📊 Biểu đồ trực quan kết quả
- 📥 Xuất dữ liệu ra file Excel
- 🎨 Giao diện đẹp và dễ sử dụng

## 🚀 Cài đặt

### Yêu cầu
- Python 3.8 trở lên

### Các bước cài đặt

1. **Cài đặt các package cần thiết:**

```powershell
pip install -r requirements.txt
```

2. **Chạy ứng dụng:**

```powershell
python app.py
```

3. **Mở trình duyệt và truy cập:**

```
http://localhost:5000
```

## 📖 Hướng dẫn sử dụng

### Bước 1: Tạo Form và Câu hỏi

#### Cách 1: Import từ URL
1. Paste link Google Form hoặc form online khác
2. Click "📥 Import URL"
3. Hệ thống sẽ tự động trích xuất câu hỏi và đáp án
4. **Quan trọng:** Kiểm tra và chỉnh sửa đáp án đúng (mặc định chọn đáp án đầu tiên)

**Lưu ý:** 
- Một số form có thể yêu cầu đăng nhập hoặc không public
- Google Forms có thể render động nên không phải lúc nào cũng parse được 100%

#### Cách 2: Import từ JSON
Paste JSON theo format:
```json
[
  {
    "text": "Câu hỏi 1?",
    "correct_answer": "Đáp án đúng",
    "options": ["Đáp án đúng", "Đáp án sai 1", "Đáp án sai 2"]
  },
  {
    "text": "Câu hỏi 2?",
    "correct_answer": "B",
    "options": ["A", "B", "C", "D"]
  }
]
```

#### Cách 3: Nhập thủ công
1. Nhập **tiêu đề form**
2. Thêm câu hỏi bằng cách click "➕ Thêm câu hỏi"
3. Cho mỗi câu hỏi, nhập:
   - Nội dung câu hỏi
   - Đáp án đúng
   - Các đáp án sai (mỗi dòng một đáp án)
4. Click "✅ Tạo Form" để lưu

### Bước 2: Tạo Responses

1. **Form ID** sẽ tự động điền sau khi tạo form
2. Nhập **số lượng responses** bạn muốn tạo (1-10,000)
3. Kéo thanh trượt để chọn **tỉ lệ đúng mong muốn** (0-100%)
4. Click "🚀 Tạo Responses"

### Bước 3: Xem kết quả và Xuất Excel

- Xem thống kê tổng quan: số responses, số câu trả lời đúng, tỉ lệ đúng thực tế
- Xem chi tiết từng câu hỏi với biểu đồ progress bar
- Click "📥 Xuất Excel" để tải file Excel chứa tất cả responses

## 🎯 Cách hoạt động

Ứng dụng sử dụng thuật toán ngẫu nhiên để quyết định mỗi câu trả lời:

- Với tỉ lệ đúng **X%**: mỗi câu trả lời có **X%** xác suất chọn đáp án đúng
- Nếu không chọn đáp án đúng, sẽ chọn ngẫu nhiên một đáp án sai

**Ví dụ:** 
- Tỉ lệ đúng = 80% → Khoảng 80% câu trả lời sẽ đúng
- Tỉ lệ đúng = 50% → Khoảng 50% câu trả lời sẽ đúng
- Tỉ lệ đúng = 100% → Tất cả câu trả lời đều đúng

## 📂 Cấu trúc Project

```
Fake/
├── app.py                 # Backend Flask API
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Frontend UI
└── README.md             # Tài liệu này
```

## 🛠️ API Endpoints

- `POST /api/create-form` - Tạo form mới
- `POST /api/generate-responses` - Tạo responses với tỉ lệ đúng
- `POST /api/export-excel` - Xuất Excel
- `POST /api/import-from-url` - Import từ URL
- `POST /api/import-json` - Import từ JSON
- `GET /api/get-forms` - Lấy danh sách forms
- `GET /api/get-responses/<form_id>` - Lấy responses của form

## 💡 Tips

- Để có kết quả chính xác hơn, tạo số lượng responses lớn (>100)
- Tỉ lệ đúng thực tế có thể dao động nhẹ do tính ngẫu nhiên
- File Excel sẽ chứa đầy đủ thông tin từng câu trả lời và đánh dấu đúng/sai
- **Sau khi import, luôn kiểm tra lại đáp án đúng trước khi tạo form!**
- Với Google Forms không public, bạn có thể:
  1. Mở form trong chế độ view
  2. Copy HTML source (F12 > Copy outerHTML)
  3. Dùng tool khác để parse hoặc nhập JSON thủ công

## 🐛 Troubleshooting

**Lỗi: "Port 5000 is already in use"**
- Đổi port trong `app.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`

**Lỗi: "Module not found"**
- Chạy lại: `pip install -r requirements.txt`

**Import URL không hoạt động:**
- Form có thể yêu cầu authentication
- Thử dùng JSON import thay thế
- Một số form render động (JavaScript) không parse được

## 📝 Format JSON cho Import

```json
[
  {
    "text": "1 + 1 = ?",
    "correct_answer": "2",
    "options": ["1", "2", "3", "4"]
  },
  {
    "text": "Thủ đô Việt Nam?",
    "correct_answer": "Hà Nội",
    "options": ["Hà Nội", "TP.HCM", "Đà Nẵng", "Cần Thơ"]
  }
]
```

## 📝 License

Free to use for educational purposes.

---

**Được phát triển với ❤️ bởi GitHub Copilot**
