// src/services/apiService.ts
import axios, { AxiosRequestConfig } from 'axios';

// Khởi tạo một instance của Axios
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL, // URL của server API, lưu trong biến môi trường
  timeout: 10000, // Timeout request sau 10 giây
  headers: {
    'Content-Type': 'application/json',
  },
});

// Hàm GET: Lấy dữ liệu từ API
export const getRequest = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.get<T>(url, config);
  return response.data;
};

// Hàm POST: Gửi dữ liệu lên API
export const postRequest = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> => {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
};

// Hàm PUT: Cập nhật dữ liệu
export const putRequest = async <T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> => {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
};

// Hàm DELETE: Xóa dữ liệu
export const deleteRequest = async <T>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  const response = await apiClient.delete<T>(url, config);
  return response.data;
};

export default apiClient;
