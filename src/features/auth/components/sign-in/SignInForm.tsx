'use client';

import React, { useState } from 'react';

import { useForm } from 'react-hook-form';

import { Alert, AlertDescription, AlertTitle } from '@/shared/components/shadcn/ui/alert';
import { Button } from '@/shared/components/shadcn/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/shadcn/ui/card';
import {
  Form,
  FormField,
  FormItem,
  FormControl,
  FormLabel,
  FormMessage,
} from '@/shared/components/shadcn/ui/form';
import { Input } from '@/shared/components/shadcn/ui/input';

type SignInFormValues = {
  email: string;
  password: string;
};

const validationRules = {
  email: {
    required: 'Vui lòng nhập email',
    pattern: {
      value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/,
      message: 'Email không hợp lệ',
    },
  },
  password: {
    required: 'Vui lòng nhập mật khẩu',
    minLength: {
      value: 6,
      message: 'Mật khẩu phải có ít nhất 6 ký tự',
    },
  },
};

export default function SignInForm() {
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const formSignIn = useForm<SignInFormValues>();
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = formSignIn;

  const onSubmit = async (data: SignInFormValues) => {
    setErrorMessage(null);
    try {
      console.log('🚀 Đăng nhập với:', data);
      await new Promise((resolve) => setTimeout(resolve, 1000));
      alert('Đăng nhập thành công!');
    } catch (_error) {
      setErrorMessage('Đăng nhập thất bại, vui lòng thử lại.');
    }
  };

  return (
    <Card className="w-[550px] mx-auto mt-10">
      <CardHeader>
        <CardTitle>Đăng nhập</CardTitle>
      </CardHeader>
      <CardContent>
        {errorMessage && (
          <Alert variant="destructive">
            <AlertTitle>Lỗi</AlertTitle>
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}

        <Form {...formSignIn}>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Email Field */}
            <FormField
              control={control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="example@email.com"
                      {...register('email', validationRules.email)}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage>{errors.email?.message}</FormMessage>
                </FormItem>
              )}
            />

            {/* Password Field */}
            <FormField
              control={control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Mật khẩu</FormLabel>
                  <FormControl>
                    <Input
                      type="password"
                      placeholder="••••••••"
                      {...register('password', validationRules.password)}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage>{errors.password?.message}</FormMessage>
                </FormItem>
              )}
            />

            {/* Submit Button */}
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
