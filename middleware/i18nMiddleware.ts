import createMiddleware from 'next-intl/middleware';

export const i18nMiddleware = createMiddleware({
	locales: ['en', 'vi'],
	defaultLocale: 'en',
	localePrefix: 'never',
});

export const config = {
	matcher: ['/((?!api|_next|_next/image|favicon.ico|.*\\..*).*)'],
};