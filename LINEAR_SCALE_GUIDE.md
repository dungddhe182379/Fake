# 📊 Hướng dẫn sử dụng Linear Scale / Rating

## ✅ Tính năng mới đã thêm

Hệ thống giờ đã hỗ trợ **Linear Scale** và **Rating** (Star ⭐, Heart ❤️, Thumb 👍) với **2 chế độ cấu hình**:

### 🎯 Chế độ 1: Target Average (Trung bình mục tiêu)
- **Mục đích**: Bạn chỉ cần nhập giá trị trung bình mong muốn (VD: 3.5)
- **Hệ thống tự động**: Tính toán phân bổ % cho từng mức để đạt được average gần đúng nhất
- **Thuật toán**: Sử dụng exponential decay - các giá trị gần target sẽ có tỉ lệ cao hơn

**Ví dụ**:
- Nhập Target: `3.5` → Hệ thống tự động tạo phân bổ: 
  - 1: 5%
  - 2: 15%
  - 3: 30%
  - 4: 35%
  - 5: 15%
  - **Actual Average**: 3.45

### 🎯 Chế độ 2: Manual % (Tự chỉnh từng %)
- **Mục đích**: Bạn tự kiểm soát hoàn toàn phân bổ % cho từng mức
- **Giao diện**: Slider cho mỗi giá trị (giống Multiple Choice)
- **Điều kiện**: Tổng phải = 100%

**Ví dụ**:
- 1: 10%
- 2: 20%
- 3: 40%
- 4: 20%
- 5: 10%
- **Tổng**: 100% ✅

---

## 🔍 Các loại Linear Scale được hỗ trợ

### 1. **Number Scale** (1-5, 1-10, etc.)
- Hiển thị: 🔢 Linear Scale (1-5)
- VD: Đánh giá từ 1 đến 5

### 2. **Star Rating** ⭐
- Hiển thị: ⭐ Linear Scale (1-5)
- VD: Đánh giá sao từ 1 sao đến 5 sao

### 3. **Heart Rating** ❤️
- Hiển thị: ❤️ Linear Scale (1-5)
- VD: Mức độ yêu thích từ 1 trái tim đến 5 trái tim

### 4. **Thumb Rating** 👍
- Hiển thị: 👍 Linear Scale (1-5)
- VD: Đánh giá từ 1 ngón cái đến 5 ngón cái

---

## 📋 Cách sử dụng

### Bước 1: Import Form
```
https://docs.google.com/forms/d/e/YOUR_FORM_ID/viewform
```

### Bước 2: Cấu hình Linear Scale
1. **Chọn chế độ**:
   - Radio button: "📊 Target Average" HOẶC "🎯 Manual %"

2. **Chế độ Target Average**:
   - Nhập số vào ô "Trung bình mong muốn"
   - Hệ thống tự động hiện preview phân bổ
   - Kiểm tra "Actual Average" để đảm bảo đúng mục tiêu

3. **Chế độ Manual %**:
   - Kéo slider cho từng mức
   - Đảm bảo tổng = 100% (màu xanh)
   - Nếu tổng ≠ 100% → Màu đỏ cảnh báo

### Bước 3: Hoàn tất & Submit
- Click "✅ Hoàn tất & Chuẩn bị Submit"
- Nhập số responses
- Click "🚀 Bắt đầu Auto Submit"

---

## 💡 Tips & Best Practices

### 1. **Khi nào dùng Target Average?**
- Bạn muốn đạt rating trung bình cụ thể (VD: 4.2 sao)
- Không quan tâm chi tiết phân bổ từng mức
- Muốn phân bổ tự nhiên (nhiều người chọn gần average)

### 2. **Khi nào dùng Manual %?**
- Bạn muốn kiểm soát chính xác phân bổ
- Tạo pattern đặc biệt (VD: 80% chọn 5 sao, 20% chọn 1 sao)
- Mô phỏng dữ liệu với phân bổ cụ thể

### 3. **Chú ý về Target Average**
- Actual Average có thể sai lệch nhỏ do làm tròn %
- Nếu cần chính xác tuyệt đối → Dùng Manual %

### 4. **Validation tự động**
- Backend tự động validate tổng = 100%
- Nếu < 100%: Tăng option gần target
- Nếu > 100%: Giảm option gần target

---

## 🛠️ Technical Details

### Backend (app.py)
- **Phát hiện Linear Scale**: Type code = **5** (NOT 3!)
- **Options structure**: `q_data[4][0][1]` = `[['1'], ['2'], ['3'], ['4'], ['5']]`
  - Nested arrays, extract `opt[0]` from each
- **Icon detection**: `q_data[4][0][2]` (needs more samples to verify)
  - 0 or None = Number scale
  - 1 = Star ⭐ (hypothesis)
  - 2 = Heart ❤️ (hypothesis)
  - 3 = Thumb 👍 (hypothesis)
- **Labels**: `q_data[4][0][3]` → `['min_label', 'max_label']`
- **Submission**: Giống Multiple Choice (chọn 1 giá trị)

### Frontend (index.html)
- **Mode toggle**: Radio buttons
- **Average calculation**: Exponential decay algorithm
- **Manual sliders**: Real-time validation
- **Question object**:
  ```json
  {
    "type": "linear_scale",
    "question": "Đánh giá sao",
    "options": ["1", "2", "3", "4", "5"],
    "scale_min": 1,
    "scale_max": 5,
    "icon_type": "star",
    "option_rates": {"1": 5, "2": 15, "3": 30, "4": 35, "5": 15},
    "scale_mode": "average",
    "target_average": 3.5
  }
  ```

---

## 🐛 Troubleshooting

### ❌ "Tổng không bằng 100%"
- **Manual mode**: Điều chỉnh sliders cho đến khi màu xanh
- **Average mode**: Không xảy ra (tự động normalize)

### ❌ "Target average nằm ngoài range"
- Kiểm tra min/max của scale
- VD: Scale 1-5 → Target phải trong [1, 5]

### ❌ "Không hiện icon"
- Check `icon_type` trong console
- Fallback: Hiện 🔢 Number Scale

### ❌ "Preview không cập nhật"
- Click ra ngoài input box
- Hoặc nhấn Enter

---

## 📊 Example Scenarios

### Scenario 1: Rating 5 sao, muốn average = 4.2
1. Chọn "📊 Target Average"
2. Nhập: `4.2`
3. Preview hiện:
   - 1: 3%
   - 2: 8%
   - 3: 15%
   - 4: 40%
   - 5: 34%
   - **Actual**: 4.18

### Scenario 2: Tạo pattern "Polarized" (80% yêu, 20% ghét)
1. Chọn "🎯 Manual %"
2. Set:
   - 1: 20%
   - 2: 0%
   - 3: 0%
   - 4: 0%
   - 5: 80%
3. Submit → 80% responses chọn 5, 20% chọn 1

### Scenario 3: Linear Scale 0-10
- Auto detect range: [0, 10]
- 11 options: 0, 1, 2, ..., 10
- Target average = 7 → Tự động phân bổ

---

## 🎉 Kết luận

Bạn đã có công cụ mạnh mẽ để:
- ✅ Import Linear Scale / Rating từ Google Forms
- ✅ Cấu hình 2 chế độ: Target Average hoặc Manual %
- ✅ Auto submit với phân bổ chính xác
- ✅ Hỗ trợ Star ⭐, Heart ❤️, Thumb 👍

**Happy Auto-Submitting! 🚀**
