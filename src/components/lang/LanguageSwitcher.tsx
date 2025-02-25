'use client';

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useLocale, useTranslations } from 'next-intl';
import { useTransition } from 'react';

const LanguageSwitcher = () => {
  const t = useTranslations('common');
  const locale = useLocale();
  const [isPending, startTransition] = useTransition();

  const handleLanguageChange = (newLocale: string) => {
    startTransition(() => {
      // Lưu locale vào localStorage
      localStorage.setItem('NEXT_LOCALE', newLocale);
      // Refresh trang
      window.location.reload();
    });
  };

  return (
    <Select defaultValue={locale} onValueChange={handleLanguageChange} disabled={isPending}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder={t('switchLanguage')} />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>{t('switchLanguage')}</SelectLabel>
          <SelectItem value="en">{t('english')}</SelectItem>
          <SelectItem value="vi">{t('vietnam')}</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
};

export default LanguageSwitcher;
