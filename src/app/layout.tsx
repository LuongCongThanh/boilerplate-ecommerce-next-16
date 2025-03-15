import { ToastProvider } from '@/shared/components/core/toast/ToastProvider';
import AppLayout from '@/shared/components/layout/AppLayout';
import '@/styles/globals.css';
import { Metadata } from 'next';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';
import { ThemeProvider } from 'next-themes';
import { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'My E-commerce',
  description: 'E-commerce',
  icons: {
    icon: '/images/favicon.ico',
  },
};
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
            <ToastProvider />
            <AppLayout>{children}</AppLayout>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
