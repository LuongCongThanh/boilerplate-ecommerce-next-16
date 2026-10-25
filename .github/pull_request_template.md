## 🏷️ Type

<!-- Chọn một. Tiêu đề PR theo Conventional Commits: feat(ordering): add COD checkout -->

- [ ] ✨ Feature
- [ ] 🐛 Bug
- [ ] ♻️ Refactor
- [ ] 🧹 Chore
- [ ] 📚 Docs

## 📌 Summary

<!-- Làm gì và vì sao -->

**Module:** <!-- identity, catalog, inventory, promotions, payments, shipping, ordering, notifications, shared -->

**🔗 Closes:** #XXX · **User story:** US-XXX · **Quy tắc:** BR-XXX

---

## 📋 Changes

-
-
-

## 🔌 API / Migration

<!-- Endpoint thêm hoặc đổi, migration mới, biến môi trường mới. Ghi "Không" nếu không có -->

---

## ✅ Checklist

- [ ] 🔨 Build pass: `make lint && make test`
- [ ] 🧱 Ranh giới module: `lint-imports` xanh, chỉ gọi module khác qua `contracts.py`
- [ ] 🧪 Tested: có test cho service, handler hoặc API, kể cả trường hợp biên
- [ ] 🗄️ Migration: đã tạo nếu đổi model, tương thích ngược (hoặc N/A)
- [ ] 🌐 i18n: chuỗi hiển thị cho người dùng bọc `gettext` (hoặc N/A)
- [ ] 🔒 Security: không lộ secret, token, dữ liệu cá nhân thật trong code, log, test
- [ ] ⚡ Performance: không có N+1 query (`django-zeal` không báo)
- [ ] 📚 Docs: đã cập nhật GLOSSARY, business rules hoặc ADR nếu cần (hoặc N/A)
- [ ] 💥 Breaking change: ghi rõ trong Notes và thêm `!` vào tiêu đề PR (hoặc N/A)

---

## 💬 Notes

<!-- Chỗ cần review kỹ, cách test thủ công, phụ thuộc -->

---

📖 [Tài liệu dự án](../blob/main/README.md) · [Quy ước Git](../blob/main/docs/architecture/11-git-workflow.md)
