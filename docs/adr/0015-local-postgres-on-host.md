# PostgreSQL ở local cài trên máy, bản major mới nhất

Ở môi trường local, PostgreSQL không chạy trong Docker Compose mà cài thẳng trên máy: macOS cài bằng Homebrew, Windows cài trong WSL2 Ubuntu bằng apt (repo PGDG). Đây là lựa chọn của dự án, thay cho cách đặt PostgreSQL trong Compose ở PR #12. Mọi máy dùng chung một bộ cài `scripts/setup/postgres.sh`: script cài bản major mới nhất đang có, tạo role và database `fashion`. Các service khác (api, worker, beat, relay, redis, mailpit) vẫn chạy trong Compose và gọi PostgreSQL qua `host.docker.internal`.

## Hệ quả

- Production (RDS) và CI (`postgres:18`) có thể chạy bản major cũ hơn local. Code chỉ được dùng tính năng có ở bản major của production; CI là nơi bắt lỗi này, không phải local.
- Bản major ở các máy có thể khác nhau, tuỳ thời điểm chạy bộ cài.
- Trên Windows, container chỉ gọi được PostgreSQL trong WSL khi bật `networkingMode=mirrored` trong `.wslconfig`.
- Dữ liệu local nằm trong WSL hoặc trên Mac, không nằm trong Docker volume: `make down` không xoá dữ liệu, còn `wsl --unregister` thì xoá. Khi mất dữ liệu thì seed lại.
- Extension `unaccent`, `pg_trgm`, `btree_gist` vẫn do migration tạo, giống CI và RDS. Bộ cài chỉ kiểm tra chúng có sẵn để cài.
