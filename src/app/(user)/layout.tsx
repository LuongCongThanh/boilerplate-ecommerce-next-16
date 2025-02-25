'use client';
import HeaderUser from '@/components/layout/Header/HeaderUser';
import { ReactNode } from 'react';

export default function UserLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <HeaderUser />
      <main>{children}</main>
    </>
  );
}
