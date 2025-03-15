import { API_ENDPOINTS } from '@/shared/contants/endpoints';
import { ERROR_MESSAGES } from '@/shared/contants/errorMessages';
import { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';
import { toast } from 'sonner';

// Type definitions
export type RefreshTokenResponse = {
  accessToken: string;
  refreshToken?: string;
};

// Thêm token vào header
export const addAuthHeader = (config: AxiosRequestConfig) => {
  if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      };
    }
  }
  return config;
};

// Xử lý lỗi 401 và refresh token
export const handleUnauthorizedError = async (error: AxiosError, apiClient: AxiosInstance) => {
  const originalRequest = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;

  if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
    originalRequest._retry = true;

    try {
      if (typeof window === 'undefined' || !localStorage) {
        throw new Error('Window object not available');
      }

      const refreshToken = localStorage.getItem('refreshToken');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const { data } = await apiClient.post<RefreshTokenResponse>(API_ENDPOINTS.AUTH.REFRESH, {
        refreshToken,
      });

      localStorage.setItem('accessToken', data.accessToken);
      if (data.refreshToken) {
        localStorage.setItem('refreshToken', data.refreshToken);
      }

      return apiClient(originalRequest);
    } catch (refreshError) {
      if (typeof window !== 'undefined' && localStorage) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');

        // Hiển thị thông báo
        toast.error(ERROR_MESSAGES.UNAUTHORIZED);

        // Chuyển hướng đến trang đăng nhập
        window.location.href = '/login';
      }
      return Promise.reject(refreshError);
    }
  }

  return Promise.reject(error);
};
