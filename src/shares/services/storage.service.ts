// src/shares/services/storage.service.ts

export const COOKIE_NAME = 'NEXT_LOCALE'; // Tên cookie cho ngôn ngữ

// Hàm để lấy giá trị từ local storage
export const getFromLocalStorage = (key: string): string | null => {
  return localStorage.getItem(key);
};

// Hàm để lưu giá trị vào local storage
export const setToLocalStorage = (key: string, value: string): void => {
  localStorage.setItem(key, value);
};

// Hàm để xóa giá trị từ local storage
export const removeFromLocalStorage = (key: string): void => {
  localStorage.removeItem(key);
};

// Hàm để lấy giá trị từ cookie
export const getFromCookie = (name: string): string | null => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    const cookieValue = parts.pop(); // Lấy phần cuối cùng
    if (cookieValue) {
      return cookieValue.split(';').shift() ?? null; // Trả về giá trị cookie hoặc null nếu undefined
    }
  }
  return null; // Nếu không tìm thấy cookie, trả về null
};

// Hàm để lưu giá trị vào cookie
export const setToCookie = (name: string, value: string, days: number): void => {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
};

// Hàm để xóa cookie
export const removeFromCookie = (name: string): void => {
  setToCookie(name, '', -1);
};
