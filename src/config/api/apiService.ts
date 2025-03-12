import apiClient from '@/config/api/instance';
import { AxiosRequestConfig } from 'axios';

// Hàm xử lý lỗi tập trung
function handleApiError(error: unknown): Error {
  if (error instanceof Error) {
    return error;
  }
  return new Error('An unknown error occurred');
}

// API service object
export const apiService = {
  get: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.get<T>(url, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  post: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.post<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  put: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.put<T>(url, data, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },

  delete: async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await apiClient.delete<T>(url, config);
      return response.data;
    } catch (error) {
      throw handleApiError(error);
    }
  },
};

export type { AxiosRequestConfig as ApiRequestConfig };
