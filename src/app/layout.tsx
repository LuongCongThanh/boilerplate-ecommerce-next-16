// app/layout.tsx
import { ReactNode } from 'react';

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header>
          <h1>My Application</h1>
          {/* Common header here */}
        </header>
        <main>{children}</main>
      </body>
    </html>
  );
}
