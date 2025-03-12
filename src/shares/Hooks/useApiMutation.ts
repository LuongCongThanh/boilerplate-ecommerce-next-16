import { useMutation, UseMutationOptions } from '@tanstack/react-query';
import { AxiosError } from 'axios';

// Hook tùy chỉnh cho React Query Mutation
export function useApiMutation<TData, TVariables, TError = AxiosError>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  options?: Omit<UseMutationOptions<TData, TError, TVariables>, 'mutationFn'>,
) {
  return useMutation<TData, TError, TVariables>({
    mutationFn,
    ...options,
  });
}
