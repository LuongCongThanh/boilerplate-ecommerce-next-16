'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { FaBars, FaSearch, FaShoppingCart } from 'react-icons/fa';

import HamburgerMenu from '@/shared/components/core/HamburgerMenu';
import LanguageSwitcher from '@/shared/components/core/lang/LanguageSwitcher';
import { ThemeToggle } from '@/shared/components/core/themeToggle/ThemeToggle';

const HeaderComponent: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  // Handle body scroll when menu is open
  useEffect(() => {
    if (isMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isMenuOpen]);

  return (
    <header className="w-full">
      {/* Top bar - using CSS variables for theme-specific colors */}
      <div
        className="py-2 text-sm"
        style={{ backgroundColor: 'var(--background)', color: 'var(--foreground)' }}
      >
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            {/* Left section */}
            <div className="flex items-center gap-5">
              <select
                className="bg-transparent border-none outline-none"
                style={{ color: 'var(--header-fg)' }}
              >
                <option value="USA">USA</option>
                <option value="VN">VN</option>
              </select>
              <a href="tel:+7772345786" className="hover:text-primary-300 transition-colors">
                +777 2345 7886
              </a>
            </div>

            {/* Right section */}
            <div className="hidden md:flex items-center gap-5">
              <Link href="/my-account" className="hover:text-primary-300 transition-colors">
                My Account
              </Link>
              <Link href="/wish-list" className="hover:text-primary-300 transition-colors">
                Wish List
              </Link>
              <Link href="/shopping" className="hover:text-primary-300 transition-colors">
                Shopping
              </Link>
              <Link href="/cart" className="hover:text-primary-300 transition-colors">
                Cart
              </Link>
              <Link href="/checkout" className="hover:text-primary-300 transition-colors">
                Checkout
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main header - using CSS variables for theme-specific colors */}
      <div
        className="shadow-md"
        style={{ backgroundColor: 'var(--header-bg)', color: 'var(--header-fg)' }}
      >
        <div className="container mx-auto px-4">
          <div className="h-20 flex items-center justify-between">
            {/* Logo */}
            <div className="text-2xl font-bold">
              <Link
                href="/"
                className="hover:text-primary-200 transition-colors"
                style={{ color: 'var(--header-fg)' }}
              >
                Estore.
              </Link>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden lg:block">
              <ul className="flex items-center gap-8">
                {[
                  { href: '/home', label: 'Home' },
                  { href: '/categori', label: 'Categori' },
                  { href: '/latest', label: 'Latest', badge: 'Hot' },
                  { href: '/blog', label: 'Blog' },
                  { href: '/pages', label: 'Pages' },
                  { href: '/contact', label: 'Contact' },
                ].map(({ href, label, badge }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className={`flex items-center gap-2 font-medium transition-colors
                        ${pathname === href ? 'text-primary-200' : 'hover:text-primary-200'}`}
                      style={{
                        color: pathname === href ? 'var(--primary-200)' : 'var(--header-fg)',
                      }}
                    >
                      {label}
                      {badge && (
                        <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                          {badge}
                        </span>
                      )}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>

            {/* Header Actions */}
            <div className="flex items-center gap-5">
              {/* Search */}
              <div className="hidden lg:block relative">
                <input
                  type="text"
                  placeholder="Search products"
                  className="w-48 pl-4 pr-10 py-2 border rounded-md focus:outline-none focus:ring-2"
                  style={{
                    borderColor: 'var(--primary-700)',
                    backgroundColor: 'var(--primary-700)',
                    color: 'var(--header-fg)',
                  }}
                />
                <button
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: 'var(--primary-300)' }}
                >
                  <FaSearch />
                </button>
              </div>

              {/* Cart */}
              <div className="relative">
                <Link
                  href="/cart"
                  className="hover:text-primary-200 transition-colors"
                  style={{ color: 'var(--header-fg)' }}
                >
                  <FaShoppingCart size={20} />
                  <span
                    className="absolute -top-2 -right-2 w-5 h-5 rounded-full flex items-center justify-center text-xs"
                    style={{
                      backgroundColor: 'var(--primary-300)',
                      color: 'var(--primary-900)',
                    }}
                  >
                    0
                  </span>
                </Link>
              </div>

              {/* Sign In Button */}
              <button
                className="px-4 py-2 rounded-md transition-colors"
                style={{
                  backgroundColor: 'var(--primary-300)',
                  color: 'var(--primary-900)',
                }}
              >
                Sign In
              </button>

              {/* Theme Button */}
              <ThemeToggle />

              {/* Mobile Menu Button */}
              <button
                className={`lg:hidden p-2 rounded-md transition-colors`}
                style={{
                  color: isMenuOpen ? 'var(--primary-200)' : 'var(--header-fg)',
                  backgroundColor: isMenuOpen ? 'var(--primary-700)' : 'transparent',
                }}
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                aria-label="Toggle menu"
              >
                <FaBars size={20} />
              </button>
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      <HamburgerMenu isOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)} />
    </header>
  );
};

export default HeaderComponent;
