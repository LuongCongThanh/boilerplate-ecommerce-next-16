'use client';
import { useEffect, useState } from 'react';

import FooterUser from '@/shared/components/layout/footerComponent/FooterComponent';
import HeaderComponent from '@/shared/components/layout/headerComponent/HeaderComponent';

export default function UserLayout({ children }: { children: React.ReactNode }) {
  const [isHeaderFixed, setIsHeaderFixed] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsHeaderFixed(window.scrollY > 100);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header
        className={`w-full ${
          isHeaderFixed
            ? 'fixed top-0 left-0 z-50 bg-white shadow-md transition-transform duration-300'
            : ''
        }`}
      >
        <HeaderComponent />
      </header>
      {/* Spacing when header is fixed */}
      {isHeaderFixed && <div className="h-[120px]" />}

      {/* Main Content */}
      <main className="flex-grow">{children}</main>

      {/* Footer */}
      <footer>
        <FooterUser />
      </footer>
    </div>
  );
}
