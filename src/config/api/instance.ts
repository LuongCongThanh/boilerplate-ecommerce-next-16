import { setupInterceptors } from '@/config/interceptors';
import axios from 'axios';
import { API_CONFIG } from './config';

// Khởi tạo Axios instance
const apiClient = axios.create(API_CONFIG);

// Thiết lập interceptors
setupInterceptors(apiClient);

export default apiClient;
