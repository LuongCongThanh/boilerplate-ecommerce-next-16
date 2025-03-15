'use client';

import { Monitor, Moon, Palette, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';

import { Button } from '@/shared/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/components/ui/dropdown-menu';
import { setToCookie, setToLocalStorage } from '@/shared/services/storage.service';
import { useTranslations } from 'next-intl';
import { useEffect, useState } from 'react';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const t = useTranslations('theme');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);
  if (!mounted) {
    return <div className="h-[1.2rem] w-[1.2rem]" />; // Placeholder with same dimensions
  }
  const getThemeIcon = () => {
    switch (theme) {
      case 'dark':
        return <Moon className="h-[1.2rem] w-[1.2rem]" />;
      case 'secondary-light':
        return <Palette className="h-[1.2rem] w-[1.2rem]" />;
      case 'white':
        return <Sun className="h-[1.2rem] w-[1.2rem] text-black" />;
      case 'system':
        return <Monitor className="h-[1.2rem] w-[1.2rem]" />;
      default:
        return (
          <>
            <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </>
        );
    }
  };

  // Hàm để thay đổi theme và lưu vào localStorage và cookie
  const handleThemeChange = (newTheme: string) => {
    setTheme(newTheme);
    setToLocalStorage('theme', newTheme); // Lưu theme vào localStorage
    setToCookie('theme', newTheme, 7); // Lưu theme vào cookie với thời gian hết hạn 7 ngày
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          {getThemeIcon()}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleThemeChange('light')}>{t('light')}</DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('dark')}>{t('dark')}</DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('secondary-light')}>
          {t('secondaryLight')}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('white')}>{t('white')}</DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('system')}>
          {t('system')}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
