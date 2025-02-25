// import createMiddleware from 'next-intl/middleware';
//
// export default createMiddleware({
//   locales: ['en', 'vi'],
//   defaultLocale: 'vi',
//   localePrefix: 'never'
// });
//
// export const config = {
//   matcher: ['/((?!api|_next|.*\\..*).*)']
// };


import { NextRequest } from 'next/server';
import { authMiddleware } from './middleware/authMiddleware';
import { i18nMiddleware } from './middleware/i18nMiddleware';

export function middleware(req: NextRequest) {
  // 1. Chạy middleware i18n trước
  const i18nResponse = i18nMiddleware(req);
  if (i18nResponse) return i18nResponse;
  
  // 2. Chạy middleware kiểm tra Auth
  return authMiddleware(req);
}

// Cấu hình matcher để áp dụng middleware cho các route hợp lệ
export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)'],
};

