// middlewares/authMiddleware.ts

import { NextRequest, NextResponse } from 'next/server';

// Middleware kiểm tra Auth
export function authMiddleware(req: NextRequest) {
  const token = req.cookies.get('token')?.value || ''; // Lấy token từ cookie
  const url = req.nextUrl.clone();

  // Decode role từ token hoặc trả về 'guest'
  const userRole = token ? getRoleFromToken(token) : 'guest';

  // Nếu không có token (guest) và đang ở "/" → Chuyển về "/home"
  if (userRole === 'guest' && url.pathname === '/') {
    return NextResponse.redirect(new URL('/home', req.url));
  }

  // Nếu là admin hoặc user → Ở lại trang "/dashboard"
  if ((userRole === 'admin' || userRole === 'user') && url.pathname === '/') {
    return NextResponse.redirect(new URL('/dashboard', req.url));
  }

  // Nếu không cần redirect → Tiếp tục xử lý
  return NextResponse.next();
}

// Hàm decode JWT để lấy role
function getRoleFromToken(token: string): string {
  try {
    const payload = JSON.parse(atob(token.split('.')[1])); // Decode JWT
    return payload.role || 'guest';
  } catch (error) {
    console.error('JWT Decode Error:', error);
    return 'guest';
  }
}
