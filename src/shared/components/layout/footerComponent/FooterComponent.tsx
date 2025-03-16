'use client';
import Link from 'next/link';

import {
  FaEnvelope,
  FaFacebookF,
  FaInstagram,
  FaLinkedinIn,
  FaMapMarkerAlt,
  FaPhone,
  FaTwitter,
} from 'react-icons/fa';

const FooterUser = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer style={{ backgroundColor: 'var(--footer-bg)', color: 'var(--footer-fg)' }}>
      {/* Main Footer */}
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* About Section */}
          <div>
            <h3 className="text-2xl font-bold text-white mb-4">Estore.</h3>
            <p className="mb-4">
              Your one-stop destination for all your shopping needs. Quality products, competitive
              prices, and excellent customer service.
            </p>
            <div className="flex gap-4">
              <a href="#" className="hover:text-primary-300 transition-colors">
                <FaFacebookF size={20} />
              </a>
              <a href="#" className="hover:text-primary-300 transition-colors">
                <FaTwitter size={20} />
              </a>
              <a href="#" className="hover:text-primary-300 transition-colors">
                <FaInstagram size={20} />
              </a>
              <a href="#" className="hover:text-primary-300 transition-colors">
                <FaLinkedinIn size={20} />
              </a>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Quick Links</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/about" className="hover:text-primary-300 transition-colors">
                  About Us
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-primary-300 transition-colors">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="/products" className="hover:text-primary-300 transition-colors">
                  Products
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-primary-300 transition-colors">
                  Login
                </Link>
              </li>
              <li>
                <Link href="/sign-up" className="hover:text-primary-300 transition-colors">
                  Sign Up
                </Link>
              </li>
            </ul>
          </div>

          {/* Customer Service */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Customer Service</h3>
            <ul className="space-y-2">
              <li>
                <Link href="/shipping" className="hover:text-primary-300 transition-colors">
                  Shipping Policy
                </Link>
              </li>
              <li>
                <Link href="/returns" className="hover:text-primary-300 transition-colors">
                  Returns & Exchanges
                </Link>
              </li>
              <li>
                <Link href="/faq" className="hover:text-primary-300 transition-colors">
                  FAQs
                </Link>
              </li>
              <li>
                <Link href="/terms" className="hover:text-primary-300 transition-colors">
                  Terms & Conditions
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="hover:text-primary-300 transition-colors">
                  Privacy Policy
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Contact Info</h3>
            <ul className="space-y-4">
              <li className="flex items-center gap-3">
                <FaMapMarkerAlt size={20} style={{ color: 'var(--primary-300)' }} />
                <span>123 Street, New York, USA</span>
              </li>
              <li className="flex items-center gap-3">
                <FaPhone size={20} style={{ color: 'var(--primary-300)' }} />
                <a href="tel:+7772345786" className="hover:text-primary-300 transition-colors">
                  +777 2345 7886
                </a>
              </li>
              <li className="flex items-center gap-3">
                <FaEnvelope size={20} style={{ color: 'var(--primary-300)' }} />
                <a
                  href="mailto:support@estore.com"
                  className="hover:text-primary-300 transition-colors"
                >
                  support@estore.com
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Bottom Bar */}
      <div style={{ borderTopColor: 'var(--primary-800)', borderTopWidth: '1px' }}>
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p>
              &copy; {currentYear} <span className="font-semibold">Estore</span>. All Rights
              Reserved.
            </p>
            <div className="flex items-center gap-4">
              {/* <Image src="/images/payment/visa.png" alt="Visa" width={32} height={32} />
              <Image src="/images/payment/mastercard.png" alt="Mastercard" width={32} height={32} />
              <Image src="/images/payment/paypal.png" alt="PayPal" width={32} height={32} /> */}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default FooterUser;
