// Simple toast hook for notifications
export interface ToastProps {
  title: string
  description?: string
  variant?: 'default' | 'destructive'
}

export function toast(_props: ToastProps) {
  // TODO: Implement proper toast notification system
  // For now, this is a placeholder function
  console.log('Toast:', _props)
}

export function useToast() {
  return {
    toast,
  }
}
