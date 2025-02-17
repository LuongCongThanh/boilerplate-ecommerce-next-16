// app/user/layout.tsx
import { ReactNode } from 'react';

export default function UserLayout({ children }: { children: ReactNode }) {
  return (
    <div>
      <header>
        <h1>User Home Page</h1>
        {/* Add User-specific header/navigation here */}
      </header>
      <main>{children}</main>
    </div>
  );
}
