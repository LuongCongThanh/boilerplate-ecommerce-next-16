'use server';

import { COOKIE_NAME } from '@/shared/contants/config';
import { defaultLocale, Locale } from '@/i18n/config';
import { cookies } from 'next/headers';

export async function getUserLocale() {
  return (await cookies()).get(COOKIE_NAME)?.value || defaultLocale;
}

export async function setUserLocale(locale: Locale) {
  (await cookies()).set(COOKIE_NAME, locale);
}
