import { useQuery, UseQueryOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';

// Hook tùy chỉnh cho React Query
export function useApiQuery<TData, TError = AxiosError>(
  queryKey: unknown[],
  queryFn: () => Promise<TData>,
  options?: Omit<UseQueryOptions<TData, TError, TData>, 'queryKey' | 'queryFn'>,
) {
  return useQuery<TData, TError>({
    queryKey,
    queryFn,
    ...options,
  });
}
