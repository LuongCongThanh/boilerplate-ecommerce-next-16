---
name: ship-ticket-fashion
description: Làm một ticket `.scratch/<feature>/issues/NN-*.md` của Fashion Store từ grilling tới merge, kèm retro skill; tạo spec và ticket cho module chưa có ticket. Dùng khi người dùng nói "làm ticket NN", "làm tiếp", "làm module X", hoặc hỏi tiến độ / ticket tiếp theo.
argument-hint: "[<feature>/<NN> | <NN> | <module>] [grill|code|report|review|sync|ship|done|retro]"
---

# ship-ticket-fashion

Mọi tin nhắn cho người dùng viết tiếng Việt. Mỗi lần chạy đưa **một** ticket qua một vòng khép kín; dừng chỉ ở gate, ở *Cần người dùng*, hoặc khi xong.

`S` = `.claude/skills/ship-ticket-fashion` (đường dẫn tính từ gốc repo). `<T>` = ticket ở dạng `<feature>/<NN>`, ví dụ `backend-bootstrap/16`.

## Đầu mỗi lần chạy

1. `python S/scripts/state.py start [<T>]`, chạy riêng. Tham số là tên module hoặc mốc (`catalog`, `M1`) chưa có ticket trong `.scratch/` → `phases/0-plan.md`. Script in ticket, phase, `next`, slice, gate, các cờ (`BRANCH RED`, `DIRTY`, `BEHIND`, `SLICE OPEN`) và các dòng `READ <file>`. Output này thay cho việc đọc file state.
   - `NO STATE` kèm frontier → chưa có ticket đang làm: báo tiến độ (`python S/scripts/progress.py`), hỏi người dùng chọn ticket (lựa chọn khuyên dùng là ticket đầu frontier), rồi vào phase 1. Có ticket `needs-triage` → cùng lần hỏi, hỏi từng ticket: `ready-for-agent`, `ready-for-human`, `wontfix` hay để sau (`docs/agents/triage-labels.md`); ghi dòng `Status:` theo câu trả lời và commit cùng ticket ở phase 1 bước 9. Frontier rỗng, hoặc mốc chỉ còn ticket bị chặn hay cần người → `phases/0-plan.md`.
2. Đọc mọi file sau `READ` bằng Read tool, mỗi file một lần gọi.
3. Bắt đầu từ `next`. Tham số `[phase]` ghi đè phase, trừ khi gate chưa được duyệt.

## Vòng

```
0 plan (khi frontier rỗng)
1 grill → ⛔G1 → 2 code (S1 → S2 → …) → 3 report → 4 review → 5 sync → ⛔G2 → 6 ship → 7 done → 8 retro
                    ↑                                  │          │
                    └──── review / sync đổi hành vi ───┴──────────┘
```

| # | Phase | File | Skill (`mattpocock-skills:`) | Kết quả |
| --- | --- | --- | --- | --- |
| 0 | plan | `phases/0-plan.md` | `grill-with-docs`, `to-spec`, `to-tickets` | spec + ticket của mốc mới |
| 1 | grill | `phases/1-grill.md` | `grill-with-docs`; `codebase-design` khi có module / interface mới | nhánh, `## Quyết định`, slice, ⛔G1 |
| 2 | code | `phases/2-code.md` | `tdd` | mọi slice xanh |
| 3 | report | `phases/3-report.md` | — | báo cáo trong `## Comments` của ticket |
| 4 | review | `phases/4-review.md` | `code-review`; `code-review` dựng sẵn (trục Bug) | mọi finding có kết luận |
| 5 | sync | `phases/5-sync.md` | `domain-modeling` khi có thuật ngữ / ADR mới | tài liệu khớp code, ⛔G2 |
| 6 | ship | `phases/6-ship.md` | — | PR mở, ticket đóng trong PR, CI xanh |
| 7 | done | `phases/7-done.md` | — | merge khi người dùng bảo |
| 8 | retro | `phases/8-retro.md` | `writing-for-agents` | skill tốt hơn, PR của skill |

Quy tắc chung cho mọi phase: `reference/rules.md`.

## Mode

**lite** khi đủ cả ba: ticket có ≤ 3 acceptance criteria, không thêm model hay migration, không thêm endpoint. Ngược lại là **full**. Phase 1 đề xuất mode, G1 chốt. Lite: một slice, làm ngay trong phiên chính, grilling chỉ hỏi phần còn mở.

## State

State nằm ở `.git/ship-ticket-fashion/<feature>-<NN>.json`: trong `.git/` nên không bao giờ bị commit, và vẫn còn sau `/clear`. Schema: `reference/state.md`. File là bộ nhớ; context của phiên chỉ là tạm.

Ghi field bằng `state.py set` / `push`. Đổi phase chỉ qua:

```bash
python S/scripts/state.py transition <T> --to <phase> --next "<một việc cụ thể>" --reason "<tiêu chí đã đạt / gate>" [--gate g1|g2]
```

Script từ chối nhảy cóc phase, vào `code` khi chưa có G1, vào `ship` khi chưa có G2, vào `report` khi còn slice chưa xong.

**Điểm clear** (các file phase chỉ ra chỗ): sau khi state và ticket đã giữ mọi quyết định, in `Đã lưu state (<phase>/<slice>). Có thể /clear rồi chạy lại /ship-ticket-fashion <T> để tiếp tục.`, rồi làm tiếp trừ khi người dùng ngắt.

## Gate

*Gate* là quyết định của người dùng (G1, G2); script xanh / đỏ là *check*. Mỗi gate gồm:

1. **Tin tóm tắt**: mọi mục phase liệt kê cho gate, viết thành bảng gọn, mỗi điểm mở kèm khuyến nghị.
2. **Quyết định**: `AskUserQuestion` chỉ chứa điểm cần trả lời (≤ 4 câu mỗi lần gọi, 2–4 lựa chọn, lựa chọn khuyên dùng đứng đầu, ghi "(khuyên dùng)"). Gom các điểm liên quan vào một câu; nhiều hơn 4 thì gọi lần hai.

Gate xong khi mọi điểm mở có câu trả lời và đã ghi vào ticket hoặc state.

*Cần người dùng* (quyết định ngoài gate) định nghĩa ở `reference/rules.md`.

## Sub-agent

Phiên chính điều phối. Việc đọc nhiều file hoặc chạy nhiều lượt giao cho sub-agent (`general-purpose`, không đặt `model`):

| Ở đâu | Sub-agent | Lite |
| --- | --- | --- |
| Phase 1, bản đồ code (`Explore`) | một | như full |
| Phase 2, mỗi slice | một cho mỗi slice | phiên chính |
| Phase 4, ba trục review | do skill review tạo | như full |
| Phase 4, vòng sửa khi finding đổi code | một cho mọi vòng | như full |

Gate, tài liệu, ship, done, retro chạy ở phiên chính: retro cần thấy những gì phiên này đã vấp.

- **Prompt = địa chỉ**: `<T>`, slice id, mode và các đường dẫn cần đọc: `S/reference/sub-agent.md` trước, rồi `S/reference/rules.md`, file phase, file `gotchas/` phase đó nêu, ticket.
- **Làm tiếp, không tạo lại**: câu trả lời cho *Cần người dùng*, vòng sửa tiếp theo, chạy lại đều gửi cho cùng agent bằng `SendMessage` (nạp bằng `ToolSearch "select:SendMessage"`).
- Phiên chính đọc kết quả trả về và state, tin phần sub-agent đã đọc.
