# Bằng chứng tuân thủ giữ HMAC số điện thoại, không giữ số thô sau khi ẩn danh

Khi một Yêu cầu xoá dữ liệu hoàn tất, `identity_consent`, `identity_erasure_request` và `identity_customer_data_access_log` vẫn được giữ làm bằng chứng (CMP-02, CMP-05, CMP-07). Ba bảng này có cột `subject_phone`, nên nếu giữ nguyên thì số điện thoại của người đã yêu cầu xoá vẫn nằm trong DB. Chọn thay `subject_phone` bằng `subject_phone_hmac` = `<kid>:` + HMAC-SHA256 của số E.164 với khoá trong keyring `PII_HMAC_KEYS`, ghi trong cùng transaction chuyển yêu cầu sang `completed`. Nhờ vậy khi cơ quan quản lý hoặc chính Người mua đưa lại số X, cửa hàng vẫn chứng minh được "số X đã đồng ý / đã yêu cầu xoá / đã bị Staff nào xem", nhưng không còn đọc ngược được số từ DB.

## Các phương án đã cân nhắc

- **Giữ số thô**: bằng chứng đầy đủ nhất nhưng trái với mục đích của Yêu cầu xoá dữ liệu; không chọn.
- **Xoá trắng**: tối thiểu dữ liệu nhất, nhưng mất khả năng chứng minh cho đúng người đã yêu cầu; không chọn.
- **SHA-256 không khoá**: không chọn, vì không gian số di động Việt Nam nhỏ nên vét cạn được trong vài phút.

## Hệ quả

- Không xoá khoá cũ khỏi `PII_HMAC_KEYS`: khoá đã dùng cho bằng chứng phải giữ chừng nào còn giữ bằng chứng. Xoay khoá chỉ đổi khoá cho giá trị mới; tra cứu thử mọi `kid` còn trong keyring.
- Mất khoá thì bằng chứng chỉ còn chứng minh được theo `account_id`, không theo số điện thoại. Khoá được sao lưu cùng các secret khác (Secrets Manager trên AWS).
- Đây không phải ẩn danh tuyệt đối: ai có cả DB và khoá vẫn thử được từng số. Khoá chỉ nằm ở backend, không vào log, không vào outbox.
- Cùng keyring dùng cho các định danh có HMAC khác (IP trong log, key của failure ledger đăng nhập, [05](../architecture/05-auth-security.md) mục 5 và 8), để chỉ có một loại secret phải quản lý.
