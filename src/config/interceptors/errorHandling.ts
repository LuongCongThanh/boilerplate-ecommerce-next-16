import { ERROR_MESSAGES } from '@/shares/contants/errorMessages';
import { AxiosError } from 'axios';
import { toast } from 'sonner';

export type ErrorResponse = {
  message?: string;
  code?: string;
};

// Hiển thị thông báo lỗi
export const handleErrorResponse = (error: AxiosError) => {
  if (error.response) {
    const { status, data } = error.response;
    const errorData = data as ErrorResponse;
    const errorMessage = errorData?.message || ERROR_MESSAGES.DEFAULT;

    switch (status) {
      case 400:
        toast.error(errorMessage);
        break;
      case 403:
        toast.error(errorMessage);
        break;
      case 404:
        toast.error(errorMessage);
        break;
      case 500:
        toast.error(errorMessage);
        break;
      default:
        toast.error(errorMessage);
    }
  } else if (error.request) {
    toast.error('Network error');
  } else {
    toast.error(error.message || 'Unknown error');
  }

  return Promise.reject(error);
};
