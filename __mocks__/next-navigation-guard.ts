export const useNavigationGuard = jest.fn(() => ({
  active: false,
  accept: jest.fn(),
  reject: jest.fn(),
}));
