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
import { i18nMiddleware } from 'middleware/i18nMiddleware';

export function middleware(req: NextRequest) {
    // 1. Chạy middleware i18n trước
    const i18nResponse = i18nMiddleware(req);
    if (i18nResponse) return i18nResponse;
    // 2. Chạy middleware kiểm tra Auth
  console.log('Middleware running for path:', req.nextUrl.pathname);
  return authMiddleware(req);
}

export const config = {
  matcher: [
    '/', // Middleware sẽ chạy khi truy cập "/"
    '/home', // Middleware sẽ chạy khi truy cập "/home"
    '/((?!api|_next|_next/image|favicon.ico|.*\\..*).*)'
  ],
};

