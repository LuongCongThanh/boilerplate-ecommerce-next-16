import { AxiosError, AxiosInstance } from 'axios';
import { handleUnauthorizedError } from './auth';
import { handleErrorResponse } from './errorHandling';

export const setupInterceptors = (apiClient: AxiosInstance): void => {
  // Request Interceptor
  // apiClient.interceptors.request.use(
  //   (config: InternalAxiosRequestConfig) => addAuthHeader(config),
  //   (error) => Promise.reject(error)
  // );

  // Response Interceptor
  apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      try {
        // Xử lý lỗi 401 và refresh token
        return await handleUnauthorizedError(error, apiClient);
      } catch {
        // Xử lý các lỗi khác
        return handleErrorResponse(error);
      }
    },
  );
};
