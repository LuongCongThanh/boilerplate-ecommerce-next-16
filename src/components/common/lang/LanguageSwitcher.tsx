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
import { useRouter } from 'next/navigation';
import { useTransition } from 'react';

const LanguageSwitcher = () => {
  const t = useTranslations('common');
  const locale = useLocale();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleLanguageChange = (value: string) => {
    startTransition(() => {
      router.replace(`/${value}`);
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
          <SelectItem value="tr">{t('turkish')}</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  );
};

export default LanguageSwitcher;
