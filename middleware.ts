import createMiddleware from 'next-intl/middleware';

export default createMiddleware({
  locales: ['en', 'vi'],
  defaultLocale: 'vi',
  localePrefix: 'never'
});

export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)']
};