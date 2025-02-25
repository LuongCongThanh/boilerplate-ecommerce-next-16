'use client';
import { AnimatePresence, motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useEffect } from 'react';
import { FaEnvelope, FaHeart, FaPhone, FaShoppingCart, FaUser } from 'react-icons/fa';

interface HamburgerMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ isOpen, onClose }) => {
  const pathname = usePathname();

  // Handle Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  const menuItems = [
    { href: '/Home', label: 'Home' },
    { href: '/categori', label: 'Categori' },
    { href: '/latest', label: 'Latest', badge: 'Hot' },
    { href: '/blog', label: 'Blog' },
    { href: '/pages', label: 'Pages' },
    { href: '/contact', label: 'Contact' },
  ];

  const quickLinks = [
    { href: '/my-account', label: 'My Account', icon: FaUser },
    { href: '/wish-list', label: 'Wish List', icon: FaHeart },
    { href: '/cart', label: 'Shopping Cart', icon: FaShoppingCart },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Overlay */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.5 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black z-40 lg:hidden"
          />

          {/* Menu */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ type: 'tween', duration: 0.3 }}
            className="fixed top-[120px] left-0 w-[280px] h-[calc(100vh-120px)] bg-white z-50 overflow-y-auto lg:hidden"
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, info) => {
              if (info.offset.x < -50) {
                onClose();
              }
            }}
          >
            {/* User Actions */}
            <div className="p-4 border-b border-gray-200">
              <div className="flex flex-col gap-3">
                <Link
                  href="/sign-in"
                  className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-center hover:bg-blue-700 transition-colors"
                  onClick={onClose}
                >
                  Sign In
                </Link>
                <Link
                  href="/sign-up"
                  className="w-full border border-blue-600 text-blue-600 py-2 px-4 rounded-md text-center hover:bg-blue-50 transition-colors"
                  onClick={onClose}
                >
                  Sign Up
                </Link>
              </div>
            </div>

            {/* Navigation */}
            <nav className="p-4">
              <ul className="flex flex-col gap-2">
                {menuItems.map(({ href, label, badge }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className={`flex items-center justify-between py-2 px-3 rounded-md transition-colors ${
                        pathname === href
                          ? 'bg-blue-50 text-blue-600'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                      onClick={onClose}
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

            {/* Quick Links */}
            <div className="p-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Quick Links</h3>
              <ul className="flex flex-col gap-3">
                {quickLinks.map(({ href, label, icon: Icon }) => (
                  <li key={href}>
                    <Link
                      href={href}
                      className="flex items-center gap-3 text-gray-600 hover:text-blue-600 transition-colors"
                      onClick={onClose}
                    >
                      <Icon size={16} />
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Contact Info */}
            <div className="p-4 bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">Contact</h3>
              <div className="flex flex-col gap-3">
                <a
                  href="tel:+7772345786"
                  className="flex items-center gap-3 text-gray-600 hover:text-blue-600 transition-colors"
                >
                  <FaPhone size={16} />
                  +777 2345 7886
                </a>
                <a
                  href="mailto:support@estore.com"
                  className="flex items-center gap-3 text-gray-600 hover:text-blue-600 transition-colors"
                >
                  <FaEnvelope size={16} />
                  support@estore.com
                </a>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default HamburgerMenu;
