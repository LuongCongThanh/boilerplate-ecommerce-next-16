import '@testing-library/jest-dom';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import HeaderComponent from '@/shared/components/layout/headerComponent/HeaderComponent';

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
jest.mock('@/shared/components/core/themeToggle/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle">Theme Toggle</div>,
}));

jest.mock('@/shared/components/core/lang/LanguageSwitcher', () => {
  return jest.fn().mockImplementation(() => {
    return <div data-testid="language-switcher">Language Switcher</div>;
  });
});

jest.mock('@/shared/components/core/HamburgerMenu', () => {
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

// Mock document.body.style to avoid JSDOM warnings
Object.defineProperty(document.body, 'style', {
  value: {
    overflow: '',
  },
  writable: true,
});

describe('Header Component', () => {
  it('renders correctly', () => {
    render(<HeaderComponent />);

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
    expect(screen.getByTestId('theme-toggle')).toBeInTheDocument();
    expect(screen.getByTestId('language-switcher')).toBeInTheDocument();
  });

  it('toggles mobile menu when hamburger button is clicked', async () => {
    const user = userEvent.setup();
    render(<HeaderComponent />);

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
    render(<HeaderComponent />);

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
    render(<HeaderComponent />);

    // Find search input
    const searchInput = screen.getByPlaceholderText('Search products');
    expect(searchInput).toBeInTheDocument();

    // Type in search input
    await user.type(searchInput, 'test search');
    expect(searchInput).toHaveValue('test search');
  });

  it('sets body overflow to hidden when menu is open', async () => {
    const user = userEvent.setup();
    render(<HeaderComponent />);

    // Initial state
    expect(document.body.style.overflow).not.toBe('hidden');

    // Open menu
    const menuButton = screen.getByLabelText('Toggle menu');
    await user.click(menuButton);

    // Body should have overflow hidden
    expect(document.body.style.overflow).toBe('hidden');

    // Close menu
    const closeButton = screen.getByTestId('close-menu');
    await user.click(closeButton);

    // Body should have overflow unset
    expect(document.body.style.overflow).toBe('unset');
  });

  it('renders country selector correctly', () => {
    render(<HeaderComponent />);

    const countrySelect = screen.getByRole('combobox');
    expect(countrySelect).toBeInTheDocument();

    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(2);
    expect(options[0]).toHaveValue('USA');
    expect(options[1]).toHaveValue('VN');
  });

  it('renders phone number correctly', () => {
    render(<HeaderComponent />);

    const phoneLink = screen.getByText('+777 2345 7886');
    expect(phoneLink).toBeInTheDocument();
    expect(phoneLink).toHaveAttribute('href', 'tel:+7772345786');
  });

  it('renders cart with correct badge', () => {
    render(<HeaderComponent />);

    const cartBadge = screen.getByText('0');
    expect(cartBadge).toBeInTheDocument();
    expect(cartBadge.closest('span')).toHaveClass('bg-blue-600');
  });

  it('unmounts cleanly and resets body overflow', () => {
    const { unmount } = render(<HeaderComponent />);

    // Open menu to set body overflow to hidden
    const menuButton = screen.getByLabelText('Toggle menu');
    userEvent.click(menuButton);

    // Unmount component
    unmount();

    // Body overflow should be reset
    expect(document.body.style.overflow).toBe('unset');
  });
});
