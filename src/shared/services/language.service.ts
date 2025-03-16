'use server';

import { cookies } from 'next/headers';

import { defaultLocale, Locale } from '@/i18n/config';
import { COOKIE_NAME } from '@/shared/contants/config';

export async function getUserLocale() {
  return (await cookies()).get(COOKIE_NAME)?.value || defaultLocale;
}

export async function setUserLocale(locale: Locale) {
  (await cookies()).set(COOKIE_NAME, locale);
}
