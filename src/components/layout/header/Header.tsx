'use client';
import LanguageSwitcher from '@/components/lang/LanguageSwitcher';
import { ModeToggle } from '@/components/theme/ModeToggle';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useEffect, useState } from 'react';
import { FaBars, FaSearch, FaShoppingCart } from 'react-icons/fa';
import HamburgerMenu from './HamburgerMenu';

const Header: React.FC = () => {
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
      {/* Top bar */}
      <div className="bg-black text-white py-2 text-sm">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            {/* Left section */}
            <div className="flex items-center gap-5">
              <select className="bg-transparent border-none outline-none">
                <option value="USA">USA</option>
                <option value="VN">VN</option>
              </select>
              <a href="tel:+7772345786" className="hover:text-blue-500 transition-colors">
                +777 2345 7886
              </a>
            </div>

            {/* Right section */}
            <div className="hidden md:flex items-center gap-5">
              <Link href="/my-account" className="hover:text-blue-500 transition-colors">
                My Account
              </Link>
              <Link href="/wish-list" className="hover:text-blue-500 transition-colors">
                Wish List
              </Link>
              <Link href="/shopping" className="hover:text-blue-500 transition-colors">
                Shopping
              </Link>
              <Link href="/cart" className="hover:text-blue-500 transition-colors">
                Cart
              </Link>
              <Link href="/checkout" className="hover:text-blue-500 transition-colors">
                Checkout
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main header */}
      <div className="bg-white shadow-md">
        <div className="container mx-auto px-4">
          <div className="h-20 flex items-center justify-between">
            {/* Logo */}
            <div className="text-2xl font-bold">
              <Link href="/" className="text-gray-800 hover:text-blue-600 transition-colors">
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
                        ${pathname === href ? 'text-blue-600' : 'text-gray-700 hover:text-blue-600'}`}
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
                  className="w-48 pl-4 pr-10 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-blue-600 transition-colors">
                  <FaSearch />
                </button>
              </div>

              {/* Cart */}
              <div className="relative">
                <Link href="/cart" className="text-gray-700 hover:text-blue-600 transition-colors">
                  <FaShoppingCart size={20} />
                  <span className="absolute -top-2 -right-2 bg-blue-600 text-white w-5 h-5 rounded-full flex items-center justify-center text-xs">
                    0
                  </span>
                </Link>
              </div>

              {/* Sign In Button */}
              <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                Sign In
              </button>

              {/* Theme Button */}
              <ModeToggle />

              {/* Mobile Menu Button */}
              <button
                className={`lg:hidden p-2 rounded-md transition-colors ${
                  isMenuOpen ? 'text-blue-600 bg-blue-50' : 'text-gray-700 hover:bg-gray-50'
                }`}
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

export default Header;
