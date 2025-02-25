import AppLayout from '@/components/layout/AppLayout';
import { ThemeProvider } from '@/components/theme/theme-provider';
import '@/styles/globals.css';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';
import { ReactNode } from 'react';

export default async function RootLayout({ children }: { children: ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages({ locale });

  return (
    <html lang={locale} suppressHydrationWarning>
      <body className="min-h-screen" suppressHydrationWarning>
        <NextIntlClientProvider messages={messages} locale={locale}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <AppLayout>{children}</AppLayout>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
