type ToastEvent = {
  variant: 'default' | 'destructive';
  title: string;
  description: string;
};

export const toastEvent = {
  listeners: [] as ((event: ToastEvent) => void)[],

  subscribe(callback: (event: ToastEvent) => void) {
    this.listeners.push(callback);
    return () => {
      this.listeners = this.listeners.filter((l) => l !== callback);
    };
  },

  emit(event: ToastEvent) {
    this.listeners.forEach((callback) => callback(event));
  },
};
