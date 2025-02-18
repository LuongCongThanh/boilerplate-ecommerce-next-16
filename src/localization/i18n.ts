export const locales = ['en', 'tr'];
export const defaultLocale = 'en';

const i18nConfig = { locales, defaultLocale };

export default i18nConfig;

export function getMessages(locale: string) {
  return import(`./messages/${locale}.json`).then((module) => module.default);
}
