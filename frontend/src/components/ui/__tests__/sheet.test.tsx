import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '../sheet'

describe('Sheet', () => {
  it('renders trigger and content when open', () => {
    render(
      <Sheet open>
        <SheetTrigger>Open Sheet</SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Test Sheet</SheetTitle>
            <SheetDescription>This is a test description</SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>
    )

    expect(screen.getByText('Test Sheet')).toBeInTheDocument()
    expect(screen.getByText('This is a test description')).toBeInTheDocument()
  })

  it('supports different sides', () => {
    render(
      <Sheet open>
        <SheetContent side="left">
          <SheetHeader>
            <SheetTitle>Left Sheet</SheetTitle>
            <SheetDescription>Slide from left</SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>
    )

    expect(screen.getByText('Left Sheet')).toBeInTheDocument()
    expect(screen.getByText('Slide from left')).toBeInTheDocument()
  })

  it('does not render content when closed', () => {
    render(
      <Sheet open={false}>
        <SheetTrigger>Open</SheetTrigger>
        <SheetContent>
          <SheetTitle>Hidden Sheet</SheetTitle>
        </SheetContent>
      </Sheet>
    )

    expect(screen.queryByText('Hidden Sheet')).not.toBeInTheDocument()
  })
})
