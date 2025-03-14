import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import Header from '../Header';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    pathname: '/',
  }),
  usePathname: () => '/',
}));

// Mock next-themes
jest.mock('next-themes', () => ({
  useTheme: () => ({
    theme: 'light',
    setTheme: jest.fn(),
  }),
}));

// Mock components
jest.mock('@/components/core/themeToggle/ThemeToggle', () => ({
  ModeToggle: () => <div data-testid="mode-toggle">Mode Toggle</div>,
}));

jest.mock('@/components/core/lang/LanguageSwitcher', () => {
  return jest.fn().mockImplementation(() => {
    return <div data-testid="language-switcher">Language Switcher</div>;
  });
});

jest.mock('../../../core/HamburgerMenu', () => {
  return jest.fn().mockImplementation(({ isOpen, onClose }) => {
    return (
      isOpen && (
        <div data-testid="hamburger-menu">
          Hamburger Menu
          <button onClick={onClose} data-testid="close-menu">
            Close
          </button>
        </div>
      )
    );
  });
});

describe('Header Component', () => {
  it('renders correctly', () => {
    render(<Header />);

    // Test for logo
    expect(screen.getByText('Estore.')).toBeInTheDocument();

    // Test for navigation items
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Categori')).toBeInTheDocument();
    expect(screen.getByText('Latest')).toBeInTheDocument();
    expect(screen.getByText('Blog')).toBeInTheDocument();
    expect(screen.getByText('Pages')).toBeInTheDocument();
    expect(screen.getByText('Contact')).toBeInTheDocument();

    // Test for badge
    expect(screen.getByText('Hot')).toBeInTheDocument();

    // Test for cart
    expect(screen.getByText('0')).toBeInTheDocument();

    // Test for sign in button
    expect(screen.getByText('Sign In')).toBeInTheDocument();

    // Test for mocked components
    expect(screen.getByTestId('mode-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('language-switcher')).toBeInTheDocument();
  });

  it('toggles mobile menu when hamburger button is clicked', async () => {
    const user = userEvent.setup();
    render(<Header />);

    // Mobile menu should not be visible initially
    expect(screen.queryByTestId('hamburger-menu')).not.toBeInTheDocument();

    // Click hamburger button
    const menuButton = screen.getByLabelText('Toggle menu');
    await user.click(menuButton);

    // Mobile menu should be visible
    expect(screen.getByTestId('hamburger-menu')).toBeInTheDocument();

    // Close the menu
    const closeButton = screen.getByTestId('close-menu');
    await user.click(closeButton);

    // Mobile menu should be hidden again
    expect(screen.queryByTestId('hamburger-menu')).not.toBeInTheDocument();
  });

  it('has correct links in the top bar', () => {
    render(<Header />);

    // Test for top bar links
    const myAccountLink = screen.getByText('My Account');
    expect(myAccountLink).toBeInTheDocument();
    expect(myAccountLink.closest('a')).toHaveAttribute('href', '/my-account');

    const wishListLink = screen.getByText('Wish List');
    expect(wishListLink).toBeInTheDocument();
    expect(wishListLink.closest('a')).toHaveAttribute('href', '/wish-list');

    const shoppingLink = screen.getByText('Shopping');
    expect(shoppingLink).toBeInTheDocument();
    expect(shoppingLink.closest('a')).toHaveAttribute('href', '/shopping');

    const cartLink = screen.getByText('Cart');
    expect(cartLink).toBeInTheDocument();
    expect(cartLink.closest('a')).toHaveAttribute('href', '/cart');

    const checkoutLink = screen.getByText('Checkout');
    expect(checkoutLink).toBeInTheDocument();
    expect(checkoutLink.closest('a')).toHaveAttribute('href', '/checkout');
  });

  it('has a working search input', async () => {
    const user = userEvent.setup();
    render(<Header />);

    // Find search input
    const searchInput = screen.getByPlaceholderText('Search products');
    expect(searchInput).toBeInTheDocument();

    // Type in search input
    await user.type(searchInput, 'test search');
    expect(searchInput).toHaveValue('test search');
  });
});
