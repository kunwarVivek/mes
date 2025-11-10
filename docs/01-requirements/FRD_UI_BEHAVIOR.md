# Functional Requirements Document - UI Behavior & Reporting
# Unison Manufacturing ERP

**Version**: 4.0
**Date**: 2025-11-10
**Domain**: User Interface, Forms, Reports, Dashboards

---


**On Custom Field Definition**:
- Field Code: Required, unique per (organization, entity type), 3-50 chars, alphanumeric + underscores
- Field Label: Required, 3-255 chars
- Field Type: Required, must be from: text, number, date, boolean, dropdown, multiselect, file
- If Field Type = dropdown/multiselect → Options list required (min 2 options)
- If Field Type = number → Can specify min/max value
- If Field Type = text → Can specify min/max length, regex pattern

**On Custom Field Value**:
- Validate according to field definition rules
- If required = true → Value must be provided
- If type = number → Value must be numeric, within min/max
- If type = dropdown → Value must be in options list
- If type = multiselect → All values must be in options list

## 7. UI Behavior

### 7.1 Dynamic Form Rendering

**Behavior**: Forms automatically include custom fields configured by administrator.

**Example: Material Form**

**Standard Fields** (hardcoded):
- Material Code
- Name
- Description
- Category (dropdown)
- Unit of Measure (dropdown)
- Standard Cost

**Custom Fields** (dynamic):
- Heat Treatment Required (yes/no) - if configured
- Certification Type (dropdown: ISO, CE, UL) - if configured
- Supplier Lead Time (number, days) - if configured

**Rendering Rules**:
- Custom fields appear after standard fields
- Grouped in "Additional Information" section
- Required fields marked with red asterisk
- Help text shown as tooltip (info icon)
- Validation errors shown inline below field

**Responsive Layout**:
- Desktop: 2-column layout (label left, input right)
- Mobile: 1-column layout (label above, input below)

### 7.2 Offline Queue Indicator

**Behavior**: When offline, show queue status.

**States**:
1. **Online**: Green indicator, no message
2. **Offline**: Yellow indicator, "You're offline. Changes will sync when reconnected."
3. **Syncing**: Blue indicator with spinner, "Syncing 3 items..."
4. **Sync Error**: Red indicator, "3 items failed to sync. Tap to retry."

**User Actions**:
- Tap offline indicator → Show queue details (what's pending)
- Tap sync error → Show error details + Retry button
- Tap retry → Attempt sync again

**Auto-Sync**:
- Triggers on: Internet connection detected, app foregrounded
- Retries: Exponential backoff (1min, 5min, 15min, 1hr)
- Max retries: 5 (then require manual intervention)

### 7.3 Barcode Scanner UI

**Behavior**: Full-screen camera with scan overlay.

**Layout**:
- Full-screen camera feed
- Semi-transparent overlay with scan area (center rectangle)
- Instruction text: "Align barcode within frame"
- Cancel button (top-left)
- Torch/flash toggle (top-right)

**On Successful Scan**:
- Vibrate (haptic feedback)
- Play success beep
- Close scanner
- Show entity details (if found) or error (if not found)

**On Scan Failure** (after 30 seconds):
- Show "Unable to scan? Enter code manually" button
- If tapped → Show text input field

---

## 8. Reporting Outputs

### 8.1 Production Summary Report

**Inputs**:
- Date range (required)
- Plant (optional filter)
- Lane (optional filter)
- Product (optional filter)

**Output Columns**:
- Date
- Plant Name
- Lane Number
- Work Order Number
- Product Name
- Quantity Ordered
- Quantity Completed
- Quantity Rejected
- Hours Worked
- Material Cost
- Labor Cost
- Total Cost

**Grouping**: By date, then by plant, then by lane

**Export Formats**: CSV, PDF

**Example Output**:
```
Production Summary Report
Date Range: Nov 1-30, 2025
Plant: All

Date       | Plant      | Lane | WO Number  | Product   | Ordered | Completed | Rejected | Hours | Cost
-----------|------------|------|------------|-----------|---------|-----------|----------|-------|-------
2025-11-06 | Fab Plant  | L1   | WO-001     | Steel Box | 100     | 100       | 3        | 16.5  | $2,450
2025-11-06 | Fab Plant  | L2   | WO-002     | Cover     | 50      | 45        | 0        | 8.0   | $890
2025-11-06 | Prod Plant | L5   | WO-003     | Assembly  | 200     | 200       | 10       | 32.0  | $4,200
...

Total: 345 units completed, 13 rejected, 56.5 hours, $7,540 cost
```

### 8.2 OEE Dashboard (Live)

**Layout**: Grid of KPI cards + chart

**KPI Cards** (top row):
- OEE Score (large number + color: >85% green, 70-85% yellow, <70% red)
- Availability (percentage)
- Performance (percentage)
- Quality (percentage)

**Chart** (bottom): Line chart showing OEE trend over last 30 days

**Filters**:
- Plant (dropdown)
- Lane (dropdown)
- Date range (date picker)

**Refresh**: Auto-refresh every 60 seconds

**Drill-Down**: Click any KPI → See breakdown (what caused downtime, which units rejected, etc.)


---

## See Also

- [FRD_EQUIPMENT.md](FRD_EQUIPMENT.md) - OEE Dashboard specifications
- [FRD_WORK_ORDERS.md](FRD_WORK_ORDERS.md) - Gantt chart UI specifications
- [FRD_QUALITY.md](FRD_QUALITY.md) - Inspection form specifications
- [FRD_INDEX.md](FRD_INDEX.md) - Complete FRD index

---

**Document Status**: Active
**Last Updated**: 2025-11-10
**Line Count**: ~170 lines
