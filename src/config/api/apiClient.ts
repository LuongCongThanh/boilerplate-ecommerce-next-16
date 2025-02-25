// import axios, { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios';

// // Khởi tạo Axios instance
// const apiClient = axios.create({
//   baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
//   timeout: 10000,
//   headers: {
//     'Content-Type': 'application/json',
//   },
// });

// // Type definitions
// type ErrorResponse = {
//   message?: string;
//   code?: string;
// };

// type RefreshTokenResponse = {
//   accessToken: string;
//   refreshToken?: string;
// };

// // Request Interceptor
// apiClient.interceptors.request.use(
//   (config) => {
//     if (typeof window !== 'undefined' && typeof localStorage !== 'undefined') {
//       const token = localStorage.getItem('accessToken');
//       if (token) {
//         config.headers.Authorization = `Bearer ${token}`;
//       }
//     }
//     return config;
//   },
//   (error) => Promise.reject(error),
// );

// // Response Interceptor
// apiClient.interceptors.response.use(
//   (response: AxiosResponse) => response,
//   async (error: AxiosError) => {
//     const originalRequest = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;

//     // Xử lý lỗi 401 (Unauthorized)
//     if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
//       originalRequest._retry = true;

//       try {
//         if (typeof window === 'undefined' || !localStorage) {
//           throw new Error('Window object not available');
//         }

//         const refreshToken = localStorage.getItem('refreshToken');
//         if (!refreshToken) {
//           throw new Error('No refresh token available');
//         }

//         // Sử dụng chính apiClient để có interceptors
//         const { data } = await apiClient.post<RefreshTokenResponse>('/auth/refresh', {
//           refreshToken,
//         });

//         localStorage.setItem('accessToken', data.accessToken);
//         if (data.refreshToken) {
//           localStorage.setItem('refreshToken', data.refreshToken);
//         }

//         return apiClient(originalRequest);
//       } catch (refreshError) {
//         if (typeof window !== 'undefined' && localStorage) {
//           localStorage.removeItem('accessToken');
//           localStorage.removeItem('refreshToken');
//           window.location.href = '/login';
//         }
//         return Promise.reject(refreshError);
//       }
//     }

//     // Xử lý các lỗi khác
//     if (error.response) {
//       const { status, data } = error.response;
//       const errorData = data as ErrorResponse;
//       const errorMessage = errorData?.message || 'An error occurred';

//       switch (status) {
//         case 400:
//           console.error('Bad Request:', errorMessage);
//           break;
//         case 403:
//           console.error('Forbidden:', errorMessage);
//           break;
//         case 404:
//           console.error('Not Found:', errorMessage);
//           break;
//         case 500:
//           console.error('Server Error:', errorMessage);
//           break;
//         default:
//           console.error(`Error [${status}]:`, errorMessage);
//       }
//     } else if (error.request) {
//       console.error('No response received:', error.request);
//     } else {
//       console.error('Request error:', error.message);
//     }

//     return Promise.reject(error);
//   },
// );

// // Hàm xử lý lỗi tập trung
// function handleApiError(error: unknown): Error {
//   if (axios.isAxiosError(error)) {
//     const errorData = error.response?.data as ErrorResponse;
//     const serverMessage = errorData?.message;
//     const statusCode = error.response?.status;

//     return new Error(
//       serverMessage ||
//         error.message ||
//         `Request failed with status code ${statusCode || 'unknown'}`,
//     );
//   }

//   if (error instanceof Error) {
//     return error;
//   }

//   return new Error('An unknown error occurred');
// }

// // API functions
// export const getRequest = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
//   try {
//     const response = await apiClient.get<T>(url, config);
//     return response.data;
//   } catch (error) {
//     throw handleApiError(error);
//   }
// };

// export const postRequest = async <T>(
//   url: string,
//   data?: unknown,
//   config?: AxiosRequestConfig,
// ): Promise<T> => {
//   try {
//     const response = await apiClient.post<T>(url, data, config);
//     return response.data;
//   } catch (error) {
//     throw handleApiError(error);
//   }
// };

// export const putRequest = async <T>(
//   url: string,
//   data?: unknown,
//   config?: AxiosRequestConfig,
// ): Promise<T> => {
//   try {
//     const response = await apiClient.put<T>(url, data, config);
//     return response.data;
//   } catch (error) {
//     throw handleApiError(error);
//   }
// };

// export const deleteRequest = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
//   try {
//     const response = await apiClient.delete<T>(url, config);
//     return response.data;
//   } catch (error) {
//     throw handleApiError(error);
//   }
// };

// export type { AxiosRequestConfig as ApiRequestConfig };
// export default apiClient;
