'use client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

const AppLayout = ({ children }: Readonly<{ children: React.ReactNode }>) => {
  return (
    <QueryClientProvider client={queryClient}>
      {/* <Notifications /> */}
      {/* <ShareDownloadProductsModal /> */}
      {/* <NavigationGuardProvider> */}
      <div className="flex flex-col min-h-screen">
        <main className="flex-grow">{children}</main>
      </div>
      {/* </NavigationGuardProvider> */}
    </QueryClientProvider>
  );
};

export default AppLayout;
