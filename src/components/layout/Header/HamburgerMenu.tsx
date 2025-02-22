import { Link } from 'lucide-react';

const HamburgerMenu = () => {
  return (
    <div className="md:hidden py-4">
      <div className="flex flex-col gap-4">
        <Link href="/" className="hover:text-primary">
          Trang chủ
        </Link>
        <Link href="/products" className="hover:text-primary">
          Sản phẩm
        </Link>
        <Link href="/about" className="hover:text-primary">
          Giới thiệu
        </Link>
        <Link href="/contact" className="hover:text-primary">
          Liên hệ
        </Link>
        <button className="w-full px-4 py-2 bg-primary text-white rounded-md hover:bg-primary/90">
          Đăng nhập
        </button>
      </div>
    </div>
  );
};

export default HamburgerMenu;
