import { ModeToggle } from '@/components/common/theme/ModeToggle';
import { ThemeProvider } from '@/components/common/theme/theme-provider';
import { NextIntlClientProvider } from 'next-intl';
import { getLocale, getMessages } from 'next-intl/server';
import { ReactNode } from 'react';
import './styles/globals.css';

// Define a type for the messages object
interface Messages {
  [key: string]: string | Messages;
}

// Function to fetch locale and messages
async function fetchLocaleAndMessages() {
  const locale = await getLocale();
  const messages: Messages = await getMessages();
  return { locale, messages };
}

// RootLayout component
function RootLayout({
  children,
  locale,
  messages,
}: {
  children: ReactNode;
  locale: string;
  messages: Messages;
}) {
  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider messages={messages}>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <header>
              <h1>My Application</h1>
              <ModeToggle />
            </header>
            <main>{children}</main>
          </ThemeProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

export default async function App({ children }: { children: ReactNode }) {
  const { locale, messages } = await fetchLocaleAndMessages();
  return (
    <RootLayout locale={locale} messages={messages}>
      {children}
    </RootLayout>
  );
}
