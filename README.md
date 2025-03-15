# Boilerplate E-commerce Next.js 15

Đây là một boilerplate cho ứng dụng E-commerce sử dụng Next.js 15 với Turbopack, được thiết kế với nhiều tính năng hiện đại và tối ưu hóa hiệu suất.

## Công nghệ sử dụng

### Core
- **Next.js**: v15.1.7 - Framework React với SSR, SSG và nhiều tính năng khác
- **React**: v19.0.0 - Thư viện UI
- **TypeScript**: v5 - JavaScript với kiểu dữ liệu tĩnh
- **Yarn** - Package manager

### UI & Styling
- **Tailwind CSS**: v4.0.14 - Framework CSS utility-first
- **Shadcn UI**: v0.0.4 - Thư viện component UI có thể tùy chỉnh
- **Framer Motion**: v12.4.7 - Thư viện animation
- **SASS**: v1.85.0 - CSS preprocessor

### State Management & Data Fetching
- **Zustand**: v5.0.3 - Thư viện quản lý state đơn giản
- **TanStack Query**: v5.66.5 - Thư viện quản lý data fetching và caching
- **Axios**: v1.8.3 - Thư viện HTTP client

### Internationalization
- **next-intl**: v3.26.5 - Thư viện i18n cho Next.js
- **react-intl**: v7.1.6 - Thư viện i18n cho React

### Testing
- **Jest**: v29.7.0 - Framework testing
- **Testing Library**: v16.2.0 - Thư viện testing cho React
- **SWC**: v1.11.9 - Compiler JavaScript/TypeScript nhanh

### Linting & Formatting
- **ESLint**: v9.21.0 - Linter cho JavaScript/TypeScript
- **Prettier**: v3.5.1 - Code formatter
- **Husky**: v9.1.7 - Git hooks

## Cài đặt dự án

### Yêu cầu hệ thống
- Node.js 18.x hoặc cao hơn
- Yarn

### Các bước cài đặt

1. Clone repository
```bash
git clone <repository-url>
cd boilerplate-ecommerce-next-15
```

2.Cài đặt dependencies
```bash
yarn install
```

3.Khởi chạy môi trường development
```bash
yarn dev
```

Ứng dụng sẽ chạy tại http://localhost:3000

4.Build cho production
```bash
yarn build
```

5.Chạy ứng dụng đã build
```bash
yarn start
```

Cấu trúc thư mục
```
├── src/
├── app/                  # App Router
│   ├── (user)/           # Route group cho user
│   │   ├── layout.tsx    # Layout cho user
│   │   └── page.tsx      # Trang chủ user
│   ├── (admin)/          # Route group cho admin
│   │   ├── layout.tsx    # Layout cho admin
│   │   └── page.tsx      # Trang chủ admin
│   └── layout.tsx        # Root layout
├── components/           # Global components
│   ├── layout/           # Layout components (Header, Footer)
│   │   ├── Header.tsx
│   │   └── Footer.tsx
│   └── ui/               # Reusable UI components (Button, Input)
├── hooks/                # Custom hooks
├── i18n/                 # Internationalization
│   ├── config.ts         # Cấu hình ngôn ngữ
│   └── dictionaries/     # File dịch
├── lib/                  # Utilities/helpers
├── services/             # API services, cookie handlers
├── stores/               # State management (Zustand/Redux)
├── types/                # Global TypeScript types
├── public/               # Static assets (images, fonts)
└── styles/               # Global CSS/Tailwind
```
Components chính
Layout Components
- Header: Component hiển thị phần đầu trang
- Footer: Component hiển thị phần chân trang
UI Components
- Các component từ shadcn UI (dropdown, select, switch, etc.)
Pages đã được tạo
Dự án sử dụng App Router của Next.js 15, với các route được định nghĩa trong thư mục src/app/:

User Pages:
- Trang chủ: /
- Layout chung cho user: /app/(user)/layout.tsx
Admin Pages:
- Trang quản trị: /admin
- Layout chung cho admin: /app/(admin)/layout.tsx

Tính năng
1.Đa ngôn ngữ: Hỗ trợ đa ngôn ngữ với next-intl và react-intl
2.Theming: Hỗ trợ nhiều theme (dark, light, system) với next-themes
3.State Management: Quản lý state với Zustand
4.API Integration: Tích hợp API với Axios và TanStack Query
5.Testing: Unit và integration testing với Jest và Testing Library
6.Responsive Design: Thiết kế responsive với Tailwind CSS

Phát triển
Linting & Formatting
```bash
# Kiểm tra lỗi
yarn lint

# Sửa lỗi tự động
yarn lint:fix

# Format code
yarn format
```

Testing
```bash
# Chạy tất cả tests
yarn test

# Chạy tests ở chế độ watch
yarn test:watch

# Kiểm tra coverage
yarn test:coverage
```