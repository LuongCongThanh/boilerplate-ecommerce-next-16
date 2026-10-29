# Phase 1 — grill + ⛔G1

Mục tiêu: hiểu ticket tới mức mỗi acceptance criterion có seam và tên test, mỗi lựa chọn mở có quyết định.

1. **Nhánh.** `git fetch origin`, rồi từ `origin/dev` tạo `<type>/<mô-tả-ngắn>` (`docs/architecture/11-git-workflow.md` mục 2; ví dụ `feat/shared-api-layer`). Đang có thay đổi chưa commit của việc khác → *Cần người dùng*.
2. **State.** `python S/scripts/state.py init <T> --branch <nhánh> --mode full` (mode tạm, G1 chốt). Đọc `reference/state.md`.
3. **Nguồn.** Đọc ticket, `spec.md` của feature, mọi tài liệu và ADR ticket trỏ tới, `GLOSSARY.md`. Ticket chạm quy tắc nghiệp vụ → thêm `docs/business/04-business-rules.md`, `05-order-lifecycle.md`. Vị trí test, marker, fixture: `docs/architecture/12-testing-strategy.md`.
4. **Bản đồ code** (sub-agent `Explore`, full): code hiện có mà ticket sửa hoặc gọi, và ticket nào bị ticket này chặn (`Blocked by` trỏ về nó) để chốt API cho đúng chỗ dùng sau này. Kết quả: danh sách file sẽ đổi và chữ ký sẽ thêm.
5. **Grilling.** `mattpocock-skills:grill-with-docs` trong phạm vi ticket: chốt lựa chọn còn mở và các _seam_ sẽ test (`mattpocock-skills:codebase-design` khi có module hoặc interface mới). Lite: chỉ hỏi phần mà ticket và tài liệu chưa trả lời.
6. **Ghi quyết định** vào ticket, mục `## Quyết định` đặt trước `## Acceptance criteria`: dòng đầu `Chốt khi grilling ngày DD/MM/YYYY.`, rồi bảng Chủ đề | Quyết định, như `.scratch/backend-bootstrap/issues/09-shared-core.md`. Quyết định khác mục *Việc cần làm* thì ghi rõ khác ở đâu và vì sao.
7. **Slice.** Chia AC thành slice dọc (lite: một slice), mỗi slice có `acs`, `seam`, `tests` dự kiến, `dependsOn`; AC không test tự động được → `untestable` kèm cách kiểm tay. Ghi bằng `state.py push <T> 'slices=[…]'`, rồi `state.py check <T>` và `python S/scripts/check_ac_trace.py <T> --planned` (chỉ kiểm mọi AC đều có chỗ, chưa kiểm test tồn tại).
8. **⛔G1** (khuôn ở SKILL.md → *Gate*). Tin tóm tắt: bảng AC → slice → seam → test; quyết định mới; file sẽ đổi (đánh dấu file trong `backend/shared/`); mode đề xuất; AC `untestable`. Hỏi: duyệt slice và mode (một câu), các quyết định còn mở.
9. Duyệt xong: commit ticket đã sửa (`docs: record decisions for <chủ đề> ticket`), rồi

   ```bash
   python S/scripts/state.py transition <T> --to code --gate g1 --next "S1: viết test red đầu tiên" --reason "G1 approved"
   ```

   In điểm clear.

## Xong khi

Mọi AC nằm trong một slice hoặc trong `untestable`; mọi lựa chọn mở có dòng trong `## Quyết định`; `state.py check` và `check_ac_trace.py --planned` xanh; `gates.g1` có ngày và `phase` là `code`.
