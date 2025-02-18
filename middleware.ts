import createMiddleware from 'next-intl/middleware';
import { defaultLocale, locales } from './src/localization/i18n';
 
export default createMiddleware({
  defaultLocale,
  locales,
//   localePrefix: 'none'
});
 
export const config = {
  matcher: ['/((?!api|_next|.*\\..*).*)']
}