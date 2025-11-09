// Simple toast hook for notifications
export interface ToastProps {
  title: string
  description?: string
  variant?: 'default' | 'destructive'
}

export function toast(props: ToastProps) {
  console.log('Toast:', props)
}
