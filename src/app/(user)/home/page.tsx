'use client';

import { Counter } from '@/components/Counter';
import LanguageSwitcher from '@/components/lang/LanguageSwitcher';
import { Button } from '@/components/ui/button';
import { useTranslations } from 'next-intl';

export default function UserHome() {
  const t = useTranslations('homepage');

  return (
    <div>
      <h2>Welcome to the User Home Page</h2>
      <Button variant="outline" className="cursor-pointer">
        {t('hello')}
      </Button>
      <LanguageSwitcher />
      <Counter />
    </div>
  );
}
