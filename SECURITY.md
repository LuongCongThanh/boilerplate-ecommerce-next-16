# Chính sách bảo mật

## Báo cáo lỗ hổng

**Không mở issue hoặc PR công khai** cho lỗ hổng bảo mật.

Báo cáo riêng qua GitHub Private Vulnerability Reporting: vào tab **Security** của repo → **Report a vulnerability**. Chỉ người duy trì repo đọc được báo cáo.

Nên gửi kèm:

- Mô tả lỗ hổng và tác động.
- Các bước tái hiện, hoặc tệp, dòng code liên quan.
- Phiên bản hoặc commit đã kiểm tra.

## Thời gian phản hồi dự kiến

| Mốc | Thời gian |
|---|---|
| Xác nhận đã nhận báo cáo | 3 ngày làm việc |
| Đánh giá mức độ nghiêm trọng | 7 ngày làm việc |
| Bản sửa cho lỗ hổng nghiêm trọng | Sớm nhất có thể, thông báo tiến độ qua báo cáo |

## Phạm vi

- Mã nguồn, cấu hình CI và tài liệu thiết kế trong repo này.
- Repo là boilerplate, **không** có hệ thống production công khai. Không thử tấn công vào dịch vụ của bên thứ ba (VNPay, MoMo, GHN, AWS…) được nhắc tới trong tài liệu.

## Biện pháp đang áp dụng

Xem [Quy ước Git](./docs/architecture/11-git-workflow.md) mục 3.5 và 8, và [Xác thực và bảo mật](./docs/architecture/05-auth-security.md).
