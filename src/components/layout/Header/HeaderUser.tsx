import HamburgerMenu from '@/components/layout/Header/HamburgerMenu';
import { ModeToggle } from '@/components/theme/ModeToggle';
import Image from 'next/image';
import Link from 'next/link';
import { useState } from 'react';

const HeaderUser = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="w-full border-b">
      <div className="container mx-auto px-4 py-3">
        <nav className="flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Image src="/assets/images/logo.png" alt="logo" width={50} height={50} />
            <span className="text-xl font-bold">Your Brand</span>
          </div>

          {/* Desktop Menu */}
          <div className="hidden md:flex items-center gap-6">
            <Link href="/" className="hover:text-primary">
              Trang chủ
            </Link>
            <Link href="/products" className="hover:text-primary">
              Sản phẩm
            </Link>
            <Link href="/about" className="hover:text-primary">
              Giới thiệu
            </Link>
            <Link href="/contact" className="hover:text-primary">
              Liên hệ
            </Link>
          </div>

          {/* Right Side */}
          <div className="flex items-center gap-4">
            <ModeToggle />
            <button className="hidden md:block px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90">
              Đăng nhập
            </button>
            {/* Mobile Menu Button */}
            <button className="md:hidden" onClick={() => setIsMenuOpen(!isMenuOpen)}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </nav>

        {/* Mobile Menu */}
        {isMenuOpen && <HamburgerMenu />}
      </div>
    </header>
  );
};

export default HeaderUser;
