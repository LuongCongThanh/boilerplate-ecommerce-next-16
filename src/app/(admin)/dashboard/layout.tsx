'use client';
import { ReactNode } from 'react';

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div>
      <header>
        <h1>Admin Dashboard</h1>
        {/* Add Admin-specific header/navigation here */}
      </header>
      <main>{children}</main>
    </div>
  );
}
