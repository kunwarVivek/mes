import { Input } from '@/components/ui/input'

interface DateRangeFilterProps {
  from: Date | null
  to: Date | null
  onChange: (from: Date | null, to: Date | null) => void
  label?: string
}

function formatDate(date: Date | null): string {
  if (!date) return ''

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

export function DateRangeFilter({
  from,
  to,
  onChange,
  label
}: DateRangeFilterProps) {
  return (
    <div className="flex items-center gap-2">
      {label && <span className="text-sm font-medium">{label}:</span>}
      <div className="flex items-center gap-1">
        <Input
          type="date"
          value={formatDate(from)}
          onChange={(e) => onChange(
            e.target.value ? new Date(e.target.value) : null,
            to
          )}
          className="w-40"
        />
        <span className="text-muted-foreground">to</span>
        <Input
          type="date"
          value={formatDate(to)}
          onChange={(e) => onChange(
            from,
            e.target.value ? new Date(e.target.value) : null
          )}
          className="w-40"
        />
      </div>
    </div>
  )
}
