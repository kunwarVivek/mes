# Core Atoms Batch 2 - Form Elements

## Overview

Four essential form input atom components built with accessibility and theme-ready structure.

## Components

### Switch
Toggle switches for binary on/off states.

**Props**:
```typescript
interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  id?: string
  name?: string
}
```

**Features**:
- Smooth slide animation
- Three sizes: small (2rem), medium (2.75rem), large (3.5rem)
- Keyboard: Space/Enter to toggle
- Accessible: role="switch", aria-checked
- Form integration: hidden input with name attribute

**Usage**:
```tsx
import { Switch } from '@/design-system/atoms'

<Switch
  checked={isEnabled}
  onChange={setIsEnabled}
  label="Enable notifications"
  size="md"
/>
```

---

### Radio
Radio buttons for mutually exclusive single selection.

**Props**:
```typescript
interface RadioProps {
  value: string
  checked: boolean
  onChange: (value: string) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
  name: string  // Required for grouping
  id?: string
}
```

**Features**:
- Circular design with inner indicator
- Three sizes: small (1rem), medium (1.25rem), large (1.5rem)
- Keyboard: Space to select
- Accessible: role="radio", aria-checked
- Form integration: name attribute for radio groups

**Usage**:
```tsx
import { Radio } from '@/design-system/atoms'

<Radio
  value="option1"
  checked={selected === 'option1'}
  onChange={setSelected}
  name="radio-group"
  label="Option 1"
/>
```

**Note**: For radio groups with arrow key navigation, use RadioGroup molecule component.

---

### Checkbox
Checkboxes with support for indeterminate state.

**Props**:
```typescript
interface CheckboxProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  indeterminate?: boolean  // Partial selection
  size?: 'sm' | 'md' | 'lg'
  label?: string
  name?: string
  id?: string
}
```

**Features**:
- Checkmark icon for checked state
- Dash icon for indeterminate state
- Three sizes: small (1rem), medium (1.25rem), large (1.5rem)
- Keyboard: Space to toggle
- Accessible: role="checkbox", aria-checked="mixed" for indeterminate
- Form integration: hidden input with name attribute

**Usage**:
```tsx
import { Checkbox } from '@/design-system/atoms'

// Regular checkbox
<Checkbox
  checked={isAccepted}
  onChange={setIsAccepted}
  label="Accept terms and conditions"
/>

// Indeterminate (partial selection)
<Checkbox
  checked={false}
  onChange={handleSelectAll}
  indeterminate={someSelected}
  label="Select all"
/>
```

---

### Textarea
Multi-line text input with character counter.

**Props**:
```typescript
interface TextareaProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  disabled?: boolean
  rows?: number
  maxLength?: number
  resize?: 'none' | 'vertical' | 'horizontal' | 'both'
  error?: boolean
  id?: string
  name?: string
  className?: string
}
```

**Features**:
- Controlled component
- Character counter (shown when maxLength provided)
- MaxLength enforcement
- Four resize options
- Error state with aria-invalid
- Custom rows (default: 3)
- Focus styles with box-shadow

**Usage**:
```tsx
import { Textarea } from '@/design-system/atoms'

<Textarea
  value={description}
  onChange={setDescription}
  placeholder="Enter description..."
  rows={5}
  maxLength={500}
  resize="vertical"
  error={hasError}
/>
```

---

## Shared Features

### Accessibility
All components implement:
- Proper ARIA roles and attributes
- Keyboard navigation support
- Label association with htmlFor/id
- Focus-visible styles for keyboard users
- Disabled state handling

### Sizing
All form controls support three sizes:
- `sm`: Compact for dense layouts
- `md`: Default size (comfortable for most cases)
- `lg`: Large for emphasis or touch interfaces

### Form Integration
All components support:
- `id`: For label association
- `name`: For form submission
- `disabled`: For disabled state
- Hidden native inputs for progressive enhancement

### Theme-Ready
All components use:
- BEM-style CSS class naming
- Modifier classes for states
- Prepared for CSS custom properties
- Smooth transitions for state changes

---

## CSS Architecture

### Class Naming Pattern
```
.component
.component--variant
.component--size
.component--state
.component__element
```

### Examples
```css
/* Switch */
.switch
.switch--sm, .switch--md, .switch--lg
.switch--checked, .switch--disabled
.switch__track, .switch__thumb, .switch__label

/* Radio */
.radio
.radio--sm, .radio--md, .radio--lg
.radio--checked, .radio--disabled
.radio__button, .radio__indicator, .radio__label

/* Checkbox */
.checkbox
.checkbox--sm, .checkbox--md, .checkbox--lg
.checkbox--checked, .checkbox--indeterminate, .checkbox--disabled
.checkbox__box, .checkbox__icon, .checkbox__label

/* Textarea */
.textarea
.textarea--resize-none, .textarea--resize-vertical, etc.
.textarea--error, .textarea--disabled
.textarea__counter
```

---

## Browser Support

All components use standard CSS features:
- Flexbox for layout
- CSS transitions for animations
- SVG for icons (Checkbox)
- Modern form controls

Tested with:
- Chrome/Edge (Chromium)
- Firefox
- Safari

---

## Testing

All components have comprehensive test coverage:
- Switch: 13 tests
- Radio: 13 tests
- Checkbox: 16 tests
- Textarea: 24 tests

**Total**: 66 tests (100% passing)

Test categories:
- Basic rendering
- Size variants
- User interactions (click, keyboard)
- Disabled states
- Accessibility features

---

## Design Decisions

### Why separate atoms vs using native inputs?
- Consistent styling across browsers
- Enhanced accessibility features
- Easier theme integration
- Better animation support
- Controlled API for React

### Why hidden native inputs?
- Progressive enhancement
- Form submission support
- Browser autofill compatibility
- Better screen reader support

### Why controlled components?
- Predictable state management
- React best practices
- Easier form validation
- Better testing

### Why BEM naming?
- Clear component structure
- Avoids specificity issues
- Easy to understand and maintain
- Works well with CSS modules

---

## Migration from Native Inputs

### Before (native HTML)
```html
<input type="checkbox" id="accept" />
<label for="accept">Accept terms</label>
```

### After (Atom component)
```tsx
<Checkbox
  checked={accepted}
  onChange={setAccepted}
  id="accept"
  label="Accept terms"
/>
```

Benefits:
- Consistent styling
- Better accessibility
- Keyboard support built-in
- Theme-ready

---

## Known Limitations

1. **Switch**: No slide-to-toggle gesture (click/keyboard only)
2. **Radio**: Arrow key navigation requires RadioGroup molecule
3. **Checkbox**: No intermediate animation between states
4. **Textarea**: No auto-resize option (planned for future)

---

## Future Enhancements

- [ ] Theme color customization via CSS custom properties
- [ ] Dark mode variants
- [ ] Textarea auto-resize option
- [ ] Switch with icons (e.g., check/cross)
- [ ] Checkbox animation between states
- [ ] RadioGroup molecule for arrow key navigation

---

## Related Components

**Molecules** (planned):
- RadioGroup: Radio buttons with arrow key navigation
- CheckboxGroup: Multiple checkboxes with select all
- FormField: Label + input + error message wrapper

**Templates**:
- Form layouts using these atoms

---

## Resources

- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [Web Content Accessibility Guidelines (WCAG)](https://www.w3.org/WAI/WCAG21/quickref/)
- TDD Evidence: `CORE_ATOMS_BATCH2_TDD_EVIDENCE.md`
