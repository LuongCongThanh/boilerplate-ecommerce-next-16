import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// User type
type User = {
  id: string;
  email: string;
  name: string;
};

// Auth store state
type AuthState = {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User) => void;
  clearUser: () => void;
};

// Tạo store với Zustand
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: true }),
      clearUser: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    },
  ),
);
