'use client';
import { ModeToggle } from '@/components/common/theme/ModeToggle';
import { ReactNode } from 'react';

export default function UserLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <header>
        <h1>User Home Page</h1>
        <ModeToggle />
      </header>
      <main>{children}</main>
    </>
  );
}
