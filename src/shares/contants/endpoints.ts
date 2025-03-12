export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
  },
  USERS: {
    BASE: '/users',
    PROFILE: '/users/profile',
  },
  // Thêm các endpoint khác
} as const;
