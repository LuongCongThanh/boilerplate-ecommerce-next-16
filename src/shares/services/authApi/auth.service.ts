import { apiService } from '@/config/api/apiService';
import { API_ENDPOINTS } from '@/shares/contants/endpoints';

// Types
export type LoginRequest = {
  email: string;
  password: string;
};

export type LoginResponse = {
  user: {
    id: string;
    email: string;
    name: string;
  };
  accessToken: string;
  refreshToken: string;
};

// Auth service
export const authService = {
  login: (data: LoginRequest) => {
    return apiService.post<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, data);
  },

  logout: () => {
    return apiService.post(API_ENDPOINTS.AUTH.LOGOUT);
  },

  // Thêm các phương thức khác
};
