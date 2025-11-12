# Unison Manufacturing ERP - User Guide

**Complete Guide for Manufacturing Teams Using Unison**

*Version 1.0 | Last Updated: 2025-11-11*

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Account & Billing](#account--billing)
3. [Material Management](#material-management)
4. [Production Management](#production-management)
5. [Quality Management](#quality-management)
6. [Maintenance Management](#maintenance-management)
7. [Equipment & Machines](#equipment--machines)
8. [Shift Management](#shift-management)
9. [Visual Scheduling](#visual-scheduling)
10. [Traceability](#traceability)
11. [Mobile App (PWA)](#mobile-app-pwa)
12. [Tips & Best Practices](#tips--best-practices)
13. [Troubleshooting](#troubleshooting)
14. [Support](#support)

---

## Getting Started

### Creating Your Account

#### 1. Sign Up

1. Visit [https://app.unison.com](https://app.unison.com)
2. Click **"Start Free Trial"** on the landing page
3. Fill in your details:
   - **Organization Name**: Your company name
   - **Email**: Your work email
   - **Password**: Minimum 8 characters
4. Click **"Create Account"**

**What Happens Next**:
- ✅ Your organization is created automatically
- ✅ A 14-day free trial begins (no credit card required)
- ✅ You're assigned as the organization administrator
- ✅ A default plant is created for you
- ✅ Welcome email sent with next steps

#### 2. First Login

1. Log in with your email and password
2. You'll see the **Dashboard** - your command center
3. Notice the **Trial Banner** at the top showing days remaining

#### 3. Complete Setup Wizard

Follow the onboarding wizard to set up:
- ✅ Organization profile (industry, size, timezone)
- ✅ First plant details (name, location, capacity)
- ✅ User roles and permissions
- ✅ Basic material master data
- ✅ Shift schedules

### Understanding Your Trial

**Trial Period**: 14 days (no credit card required)

**What's Included**:
- All Starter tier features
- 3 users maximum
- 1 plant
- 10 GB storage

**Trial Countdown**:
- **Blue banner (7+ days remaining)**: Explore features
- **Orange banner (3-6 days)**: Consider upgrading
- **Red banner (<3 days)**: Urgent - add payment method

**After Trial Ends**:
- If you've added a payment method → Subscription activates automatically
- If no payment method → Access is suspended until you upgrade

---

## Account & Billing

### Managing Your Subscription

#### Viewing Current Plan

1. Click your **profile icon** (top-right)
2. Select **"Billing"**
3. View your current plan:
   - Tier (Starter, Professional, Enterprise)
   - Billing cycle (Monthly or Annual)
   - Next renewal date
   - Current MRR

#### Checking Usage

On the **Billing** page, see:
- **Users**: 2 of 3 used (example)
- **Plants**: 1 of 1 used
- **Storage**: 2.4 GB of 10 GB used

**Color Indicators**:
- **Green**: <70% used (healthy)
- **Orange**: 70-90% used (approaching limit)
- **Red**: >90% used (upgrade recommended)

#### Upgrading Your Plan

**When to Upgrade**:
- You need more users (hit 3-user limit on Starter)
- You're opening multiple plants (need Professional for 5 plants)
- You need advanced features (visual scheduling, maintenance management)

**How to Upgrade**:
1. Go to **Billing** page
2. Click **"Upgrade Plan"** button
3. Select new tier (Professional or Enterprise)
4. Choose billing cycle:
   - **Monthly**: Flexible, no commitment
   - **Annual**: Save 10-15%
5. Enter payment details (Stripe secure checkout)
6. Confirm upgrade

**What Happens Immediately**:
- ✅ New limits apply instantly
- ✅ New features unlock automatically
- ✅ Pro-rated billing (credit for unused time)
- ✅ Confirmation email sent

#### Downgrading Your Plan

**How to Downgrade**:
1. Go to **Billing** page
2. Click **"Change Plan"**
3. Select lower tier
4. Confirm downgrade

**Important Notes**:
- Downgrade takes effect at **next renewal date** (not immediate)
- Ensure you're within new limits (users, plants, storage)
- You'll receive a warning if you exceed new limits

#### Managing Payment Methods

**Update Payment Method**:
1. Go to **Billing** page
2. Click **"Manage Payment Methods"**
3. You'll be redirected to **Stripe Billing Portal**
4. Add/update/remove credit cards
5. Close portal when done

**Viewing Invoices**:
1. Go to **Billing** → **Invoice History**
2. See all past invoices with:
   - Date
   - Amount
   - Status (Paid, Pending, Failed)
   - Download PDF button

**Failed Payment**:
- You'll receive an email notification
- Stripe will retry automatically (3 attempts over 2 weeks)
- If all retries fail, subscription is suspended

---

## Material Management

### Materials Master Data

#### Creating a Material

1. Go to **Materials** → **All Materials**
2. Click **"+ New Material"**
3. Fill in details:
   - **Material Code**: Unique identifier (e.g., `RM-001`)
   - **Name**: Descriptive name (e.g., "Steel Plate 5mm")
   - **Type**: Raw Material, Finished Good, WIP, Consumable
   - **Category**: Organize materials (e.g., "Steel", "Plastics")
   - **Base UOM**: Primary unit (e.g., "kg", "pcs", "meters")
   - **Cost**: Standard cost per UOM
4. Click **"Save"**

#### Multi-UOM Support

Materials can be tracked in multiple units:

**Example**: Steel Plate
- **Base UOM**: kg (primary unit)
- **Alt UOM 1**: Sheet (1 sheet = 50 kg)
- **Alt UOM 2**: Pallet (1 pallet = 20 sheets = 1000 kg)

**Setting Up**:
1. Edit material
2. Go to **"UOM Conversions"** tab
3. Click **"+ Add UOM"**
4. Enter:
   - UOM name
   - Conversion factor to base UOM
5. Save

**Use Case**: Purchase in pallets, store in kg, issue in sheets.

#### Material Costing Methods

Your organization uses **one costing method** for all materials:

| Method | How It Works | Best For |
|--------|--------------|----------|
| **FIFO** | First In, First Out | Perishable goods, food, pharma |
| **LIFO** | Last In, First Out | Non-perishable, price fluctuation |
| **Weighted Average** | Average cost of all batches | Standard materials, minimal price change |

**Setting Costing Method**:
1. Go to **Settings** → **Organization**
2. Select **"Costing Method"**
3. Choose FIFO/LIFO/Weighted Average
4. Save (cannot be changed after first transaction)

### Bill of Materials (BOM)

#### Creating a BOM

1. Go to **Materials** → **BOMs**
2. Click **"+ New BOM"**
3. Select **parent material** (finished good)
4. Add components:
   - Click **"+ Add Component"**
   - Select material
   - Enter quantity per unit
   - Specify scrap % (optional)
5. Set **BOM type**:
   - **Production BOM**: For manufacturing
   - **Template BOM**: Master template
6. Click **"Save"**

**Example BOM**: Bicycle
- Parent: Bicycle (1 pcs)
- Components:
  - Frame (1 pcs)
  - Wheel (2 pcs)
  - Handlebar (1 pcs)
  - Seat (1 pcs)
  - Chain (1 pcs)

#### Multi-Level BOM

Unison supports nested BOMs:

**Level 1**: Bicycle
- **Level 2**: Frame assembly
  - **Level 3**: Steel tube, welding wire

**Creating Multi-Level BOM**:
1. Create lowest-level BOMs first (Level 3)
2. Then create mid-level BOMs (Level 2)
3. Finally create top-level BOM (Level 1)

**BOM Explosion**:
- Click **"Explode BOM"** to see all components across all levels
- Useful for material requirement planning (MRP)

### Inventory Management

#### Stock Locations

**Warehouse Structure**:
```
Plant A
├── Raw Material Warehouse
│   ├── Aisle 1
│   ├── Aisle 2
├── Production Floor
│   ├── Workstation 1
│   ├── Workstation 2
└── Finished Goods Warehouse
    ├── Shipping Area
```

**Creating Locations**:
1. Go to **Inventory** → **Locations**
2. Click **"+ New Location"**
3. Enter:
   - Location code (e.g., `RM-A1`)
   - Name
   - Parent location (for hierarchy)
   - Type (Storage, Production, Transit)
4. Save

#### Stock Transactions

**1. Goods Receipt (Incoming)**:
1. Go to **Inventory** → **Transactions**
2. Click **"Goods Receipt"**
3. Select:
   - Material
   - Quantity + UOM
   - Destination location
   - Purchase order reference (optional)
   - Lot/batch number (for traceability)
4. Click **"Post"**

**2. Goods Issue (Outgoing)**:
1. Go to **Inventory** → **Transactions**
2. Click **"Goods Issue"**
3. Select:
   - Material
   - Quantity + UOM
   - Source location
   - Reason (Production, Sale, Scrap)
   - Work order reference (if for production)
4. Click **"Post"**

**3. Stock Transfer**:
1. Go to **Inventory** → **Transactions**
2. Click **"Stock Transfer"**
3. Select:
   - Material
   - Quantity
   - From location → To location
4. Click **"Post"**

**4. Stock Adjustment**:
Use for:
- Physical inventory corrections
- Cycle count adjustments
- Damage/obsolescence

Steps:
1. Go to **Inventory** → **Adjustments**
2. Click **"+ New Adjustment"**
3. Enter:
   - Material
   - Location
   - Actual quantity (what you counted)
   - System quantity (shown automatically)
   - Reason for difference
4. Click **"Post"**

#### Checking Stock Levels

**Real-Time Stock**:
1. Go to **Inventory** → **Stock Overview**
2. See all materials with:
   - Current stock quantity
   - Location breakdown
   - Reserved quantity (for work orders)
   - Available quantity

**Stock by Location**:
1. Go to **Inventory** → **Stock by Location**
2. Select location
3. See all materials in that location

**Stock Aging Report**:
1. Go to **Reports** → **Stock Aging**
2. See materials by age:
   - 0-30 days
   - 30-60 days
   - 60-90 days
   - >90 days (slow-moving)
3. Use for inventory optimization

---

## Production Management

### Work Orders

#### Creating a Work Order

1. Go to **Production** → **Work Orders**
2. Click **"+ New Work Order"**
3. Fill in:
   - **WO Number**: Auto-generated or manual
   - **Material**: Finished good to produce
   - **Quantity**: How many units
   - **BOM**: Select production BOM
   - **Start Date**: Planned start
   - **Due Date**: Customer deadline
   - **Priority**: Normal, High, Urgent
4. Click **"Create"**

**Work Order Status**:
- **Draft**: Not released yet (can edit)
- **Released**: Ready for production
- **In Progress**: Production started
- **Completed**: All operations done
- **Closed**: Quality approved, goods receipt posted

#### Planning Operations

**Routing** defines the sequence of operations:

**Example**: Bicycle Production
1. **Operation 10**: Frame welding (2 hours, Welding machine)
2. **Operation 20**: Frame painting (1 hour, Paint booth)
3. **Operation 30**: Final assembly (3 hours, Assembly station)
4. **Operation 40**: Quality inspection (0.5 hours, QC station)

**Adding Operations**:
1. Open work order
2. Go to **"Operations"** tab
3. Click **"+ Add Operation"**
4. Enter:
   - Operation number (10, 20, 30...)
   - Description
   - Work center/machine
   - Setup time + Run time
   - Standard time per unit
5. Save

#### Releasing Work Orders

**Release Checklist**:
- ✅ BOM is valid
- ✅ Material availability checked
- ✅ Machine capacity available
- ✅ Operations planned

**Release Process**:
1. Open work order (Draft status)
2. Click **"Check Material Availability"**
   - Green: All materials available
   - Yellow: Partial availability
   - Red: Shortages (see report)
3. If shortages, create purchase requisitions
4. When ready, click **"Release"**
5. Status changes to **"Released"**

#### Executing Production

**Starting Work Order**:
1. Go to **Production** → **Work Orders** → **Released**
2. Select work order
3. Click **"Start Production"**
4. System reserves materials automatically
5. Status → **"In Progress"**

**Logging Production** (Desktop):
1. Open work order
2. Go to **"Production Log"** tab
3. Click **"+ Add Entry"**
4. Enter:
   - Date & time
   - Operation completed
   - Quantity produced (good)
   - Quantity rejected (scrap)
   - Machine/operator
   - Notes (issues, downtime)
5. Save

**Logging Production** (Mobile PWA):
1. Open mobile app
2. Scan work order barcode
3. Tap operation to complete
4. Enter quantities (good/scrap)
5. Tap **"Submit"**

**Completing Work Order**:
1. Verify all operations completed
2. Verify quantity matches (good qty + scrap qty = planned qty)
3. Click **"Complete"**
4. System auto-creates:
   - Material consumption entries (BOM components)
   - Finished goods receipt
5. Status → **"Completed"**

**Closing Work Order**:
- Final step after quality approval
- Click **"Close"**
- Cannot be reopened

### Visual Scheduling

*Available in Professional and Enterprise tiers*

#### Accessing Gantt Scheduler

1. Go to **Production** → **Visual Schedule**
2. See all work orders on Gantt chart:
   - **X-axis**: Timeline (days/weeks)
   - **Y-axis**: Machines/work centers
   - **Bars**: Work orders (color-coded by status)

#### Drag-and-Drop Planning

**Scheduling Work Orders**:
1. Drag work order bar left/right to change dates
2. Drag between rows to change machine assignment
3. Resize bar to adjust duration
4. System shows conflicts:
   - **Red**: Machine overloaded
   - **Yellow**: Material shortage
   - **Green**: No issues

**Capacity View**:
- Click **"Capacity View"** toggle
- See machine utilization %:
  - 0-70%: Green (under-utilized)
  - 70-90%: Yellow (optimal)
  - 90-100%+: Red (over-capacity)

**Filtering**:
- Filter by:
  - Plant
  - Machine/work center
  - Priority
  - Status
  - Date range

---

## Quality Management

### Non-Conformance Reports (NCR)

#### Creating an NCR

**When to Create**:
- Defect found in production
- Customer complaint
- Supplier quality issue
- Audit finding

**Steps**:
1. Go to **Quality** → **NCRs**
2. Click **"+ New NCR"**
3. Fill in:
   - **NCR Number**: Auto-generated
   - **Title**: Brief description (e.g., "Weld crack on Frame #123")
   - **Type**: Internal, Customer, Supplier
   - **Severity**: Critical, Major, Minor
   - **Material**: Affected material
   - **Quantity**: How many units affected
   - **Location**: Where found
   - **Description**: Detailed description with photos
4. Click **"Create"**

#### 8D Problem Solving Workflow

Unison follows the **8D methodology**:

**D1: Team Formation**
1. Open NCR
2. Go to **"Team"** tab
3. Add team members (roles: Leader, Engineer, QA, etc.)

**D2: Problem Description**
- Already filled in NCR creation
- Attach photos, videos, measurements

**D3: Containment Actions**
1. Go to **"Containment"** tab
2. Click **"+ Add Action"**
3. Enter immediate actions:
   - Quarantine affected units
   - Hold similar batches
   - Notify customers
4. Assign owner + due date

**D4: Root Cause Analysis**
1. Go to **"Root Cause"** tab
2. Use tools:
   - **5 Whys**: Click "Add Why" repeatedly
   - **Fishbone Diagram**: Add causes by category (Man, Machine, Material, Method)
3. Document root cause

**D5: Corrective Actions**
1. Go to **"Corrective Actions"** tab
2. Click **"+ Add Action"**
3. Enter:
   - Action description
   - Owner
   - Due date
   - Verification method
4. Save

**D6: Implementation**
- Track actions in **"Actions"** tab
- Update status: Not Started → In Progress → Completed
- Attach evidence (photos, documents)

**D7: Preventive Actions**
1. Go to **"Preventive Actions"** tab
2. Add measures to prevent recurrence:
   - Update work instructions
   - Training programs
   - Inspection checkpoints

**D8: Closure**
- Verify all actions completed
- Click **"Close NCR"**
- System calculates:
  - Time to containment
  - Time to root cause
  - Time to closure

#### Quality Analytics

*Available in Professional and Enterprise tiers*

**Viewing Quality Metrics**:
1. Go to **Quality** → **Analytics**
2. See dashboard:
   - **NCR Trend**: Count over time
   - **NCR by Type**: Internal vs. Customer vs. Supplier
   - **NCR by Severity**: Critical vs. Major vs. Minor
   - **Mean Time to Close**: Average days to close NCR
   - **Top Defect Types**: Pareto chart

**Statistical Process Control (SPC)**:
1. Go to **Quality** → **SPC Charts**
2. Select measurement (e.g., "Diameter", "Weight")
3. See control chart:
   - Upper Control Limit (UCL)
   - Center Line (CL)
   - Lower Control Limit (LCL)
   - Data points (green = in control, red = out of control)
4. Calculate process capability:
   - **Cp**: Process capability index
   - **Cpk**: Process capability index (accounting for mean shift)

---

## Maintenance Management

*Available in Professional and Enterprise tiers*

### Preventive Maintenance (PM) Schedules

#### Creating PM Schedule

1. Go to **Maintenance** → **PM Schedules**
2. Click **"+ New PM Schedule"**
3. Fill in:
   - **Schedule Name**: e.g., "CNC Machine Oil Change"
   - **Equipment**: Select machine
   - **Frequency**: Daily, Weekly, Monthly, Quarterly, Yearly
   - **Interval**: Every N days/weeks/months
   - **Estimated Duration**: How long PM takes
   - **Checklist**: Tasks to perform (add items)
4. Click **"Activate"**

**What Happens**:
- System auto-generates PM work orders based on frequency
- Work orders appear on maintenance calendar
- Email notifications sent to assigned technician

#### Executing PM Work Orders

1. Go to **Maintenance** → **Work Orders** → **Planned**
2. Select PM work order
3. Click **"Start"**
4. Complete checklist:
   - ✅ Check oil level
   - ✅ Replace oil filter
   - ✅ Lubricate bearings
   - ✅ Inspect belts
5. Add notes (observations, parts used)
6. Attach photos (before/after)
7. Click **"Complete"**

**Parts Consumption**:
- If parts used (e.g., oil filter):
  - Click **"Add Parts"**
  - Select material + quantity
  - System auto-issues from inventory

### Breakdown Maintenance

#### Logging Downtime

**When Machine Breaks Down**:
1. Go to **Maintenance** → **Downtime**
2. Click **"+ Log Downtime"**
3. Enter:
   - **Equipment**: Which machine
   - **Start Time**: When breakdown occurred
   - **Problem Description**: What happened
   - **Priority**: Urgent, High, Normal
4. Click **"Create"**

**System Actions**:
- Auto-creates breakdown work order
- Sends notification to maintenance team
- Marks machine as **"Down"** on production schedule

#### Resolving Breakdown

1. Technician assigned to work order
2. Click **"Start Repair"**
3. Diagnose issue
4. Add parts used (if any)
5. Enter repair actions taken
6. Click **"Complete Repair"**
7. System:
   - Marks machine as **"Up"**
   - Calculates downtime duration
   - Updates OEE metrics

### Maintenance Analytics

**Viewing Maintenance Metrics**:
1. Go to **Maintenance** → **Analytics**
2. See dashboard:
   - **MTBF** (Mean Time Between Failures): Average days between breakdowns
   - **MTTR** (Mean Time To Repair): Average hours to fix
   - **PM Compliance**: % of PM work orders completed on time
   - **Downtime by Equipment**: Which machines cause most downtime
   - **Maintenance Cost**: Spend over time

**Use Case**: Identify machines needing replacement (high MTTR, low MTBF).

---

## Equipment & Machines

### Machine Master Data

#### Adding Equipment

1. Go to **Equipment** → **All Equipment**
2. Click **"+ New Equipment"**
3. Fill in:
   - **Equipment Code**: Unique ID (e.g., `CNC-001`)
   - **Name**: Descriptive name
   - **Type**: Machine, Tool, Vehicle, Facility
   - **Category**: CNC Machine, Lathe, Mill, etc.
   - **Manufacturer**: Brand
   - **Model**: Model number
   - **Serial Number**: Serial number
   - **Purchase Date**: When acquired
   - **Warranty Expiry**: If applicable
   - **Location**: Where installed
4. Go to **"Specifications"** tab:
   - Add custom specs (max speed, power, capacity)
5. Go to **"Documents"** tab:
   - Upload manuals, schematics, datasheets
6. Click **"Save"**

#### Linking Equipment to Work Centers

**Work Centers** are logical production units:
- Example: "Welding Station" (contains 2 welding machines)

**Linking**:
1. Go to **Production** → **Work Centers**
2. Select/create work center
3. Go to **"Equipment"** tab
4. Click **"+ Link Equipment"**
5. Select machines
6. Save

**Use Case**: When scheduling, system knows which machines available at work center.

### OEE Tracking

**OEE (Overall Equipment Effectiveness)** = Availability × Performance × Quality

#### Viewing OEE

1. Go to **Equipment** → **OEE Dashboard**
2. Select machine and date range
3. See breakdown:
   - **Availability**: (Operating Time / Planned Time) × 100%
     - Reduces by: Breakdowns, setup/changeover
   - **Performance**: (Actual Output / Theoretical Output) × 100%
     - Reduces by: Slow cycles, minor stops
   - **Quality**: (Good Units / Total Units) × 100%
     - Reduces by: Defects, rework
4. Overall OEE = Availability × Performance × Quality

**Example**:
- Availability: 90% (1 hour downtime in 10-hour shift)
- Performance: 95% (ran slightly slower than rated speed)
- Quality: 98% (2% defect rate)
- **OEE = 0.90 × 0.95 × 0.98 = 83.8%**

**Industry Benchmark**:
- World-class OEE: >85%
- Good OEE: 70-85%
- Needs improvement: <70%

---

## Shift Management

### Setting Up Shifts

#### Creating Shift Definitions

1. Go to **Settings** → **Shifts**
2. Click **"+ New Shift"**
3. Fill in:
   - **Shift Name**: e.g., "Day Shift", "Night Shift"
   - **Start Time**: e.g., 08:00
   - **End Time**: e.g., 16:00
   - **Break Duration**: e.g., 1 hour
   - **Working Days**: Mon-Fri, Sat, Sun (checkboxes)
4. Save

**Example Shifts**:
- **Day Shift**: 08:00 - 16:00 (Mon-Fri)
- **Evening Shift**: 16:00 - 00:00 (Mon-Fri)
- **Night Shift**: 00:00 - 08:00 (Mon-Sat)

#### Creating Shift Schedules

1. Go to **Production** → **Shift Schedules**
2. Click **"+ New Schedule"**
3. Select:
   - **Plant**: Which plant
   - **Start Date**: When schedule begins
   - **Pattern**: 5-day week, 6-day week, 24x7 rotation
4. Assign shifts to teams:
   - Team A: Day shift (Mon-Fri)
   - Team B: Evening shift (Mon-Fri)
   - Team C: Night shift (Mon-Fri)
5. Save and activate

### Shift Handovers

#### Completing Handover

**At End of Shift**:
1. Go to **Production** → **Shift Handover**
2. Click **"Complete Handover"**
3. Fill in:
   - **Production Summary**: WOs completed, quantities
   - **Quality Issues**: Any NCRs raised
   - **Downtime Events**: Any machine breakdowns
   - **Material Shortages**: Materials that ran out
   - **Pending Work**: WOs in progress (to hand over)
   - **Notes**: Important info for next shift
4. Click **"Submit Handover"**

**Next Shift**:
1. Incoming supervisor reviews handover
2. Acknowledges receipt
3. Addresses pending issues

---

## Visual Scheduling

*Available in Professional and Enterprise tiers*

### Using Gantt Chart

#### Gantt View Features

**Access**: Go to **Production** → **Visual Schedule**

**Chart Elements**:
- **Horizontal bars**: Work orders (length = duration)
- **Colors**:
  - Blue: Released
  - Green: In Progress
  - Gray: Completed
  - Red: Delayed (past due date)
- **Dependencies**: Arrows connecting related WOs
- **Milestones**: Diamond shapes for key dates

#### Interactive Scheduling

**Drag-and-Drop**:
1. Click work order bar
2. Drag left/right to reschedule
3. System validates:
   - Material availability
   - Machine capacity
   - Dependencies
4. If conflict, shows warning:
   - "Machine over-capacity on 11/15"
   - "Material shortage: Steel Plate"
5. Adjust until no conflicts

**Filtering & Views**:
- **Filter by Machine**: See only specific machine's schedule
- **Filter by Priority**: Show only Urgent/High priority WOs
- **Zoom**: Day/Week/Month view
- **Grouping**: Group by machine, by material, by customer

#### Capacity Planning

**Viewing Capacity**:
1. Toggle **"Capacity View"**
2. See bar chart below Gantt:
   - X-axis: Days
   - Y-axis: Machine capacity %
   - Bars: Actual load

**Color Indicators**:
- **Green (0-70%)**: Under-utilized
- **Yellow (70-90%)**: Well-utilized
- **Red (90%+)**: Over-capacity (reschedule needed)

**Leveling Capacity**:
1. Identify over-capacity days (red bars)
2. Drag WOs from red days to green days
3. Check material availability after rescheduling
4. Save schedule

---

## Traceability

### Serial Number Tracking

#### Serialized Materials

**When to Use Serial Numbers**:
- High-value items (engines, electronics)
- Regulatory requirement (pharma, aerospace)
- Warranty tracking

**Enabling Serial Tracking**:
1. Go to **Materials** → Edit material
2. Check **"Serial Number Tracking"**
3. Select serial number format:
   - Manual entry
   - Auto-generated (prefix + sequence)
   - Scanned (barcode/QR)
4. Save

#### Assigning Serial Numbers

**During Goods Receipt**:
1. Receive material (e.g., 10 engines)
2. System prompts: "Enter 10 serial numbers"
3. Scan/enter each serial:
   - ENG-001
   - ENG-002
   - ENG-003
   - ...
4. Post receipt

**During Production**:
- When consuming serialized material:
  - System asks: "Which serial number?"
  - Select from available serials
- When producing serialized finished good:
  - System asks: "Assign serial number?"
  - Enter/scan new serial

### Lot/Batch Tracking

#### Lot-Controlled Materials

**When to Use Lots**:
- Materials with expiry dates (chemicals, food)
- Batch production (pharma, paints)
- Recall management

**Enabling Lot Tracking**:
1. Edit material
2. Check **"Lot Number Tracking"**
3. Select lot format:
   - Manual entry
   - Auto-generated (date + sequence)
4. Add expiry tracking (optional)
5. Save

#### Lot Transactions

**Goods Receipt with Lot**:
1. Receive material
2. Enter lot number: `LOT-2025-11-001`
3. If expiry tracking enabled:
   - Enter manufacturing date
   - Enter expiry date
4. Post

**FEFO (First Expired, First Out)**:
- When issuing lot-tracked materials:
  - System suggests lot closest to expiry
  - Reduces waste

### Genealogy & Traceability Reports

#### Forward Traceability

**Use Case**: "Where did this batch of raw material go?"

1. Go to **Traceability** → **Forward Trace**
2. Enter:
   - Material
   - Lot/serial number
3. Click **"Trace"**
4. System shows:
   - Which work orders consumed this lot
   - Which finished goods contain this lot
   - Which customers received finished goods

**Example**:
- Raw Material: Steel Plate (Lot: LOT-123)
- Used in: WO-001, WO-002
- Produced: Bicycle Frame (Serial: FRAME-001, FRAME-002)
- Shipped to: Customer A, Customer B

#### Backward Traceability

**Use Case**: "Which raw materials were used in this finished good?"

1. Go to **Traceability** → **Backward Trace**
2. Enter:
   - Finished good
   - Serial number
3. Click **"Trace"**
4. System shows:
   - All raw material lots used
   - All operations performed
   - Operators who worked on it
   - Quality inspections passed

**Example**:
- Finished Good: Bicycle (Serial: BIKE-001)
- Components:
  - Frame (FRAME-001) ← Steel Plate (LOT-123)
  - Wheel (WHEEL-101, WHEEL-102) ← Aluminum (LOT-456)
  - Chain (CHAIN-501) ← Steel Rod (LOT-789)

#### Recall Management

**Initiating Recall**:
1. Go to **Quality** → **Recalls**
2. Click **"+ New Recall"**
3. Enter:
   - Material affected
   - Lot/serial range
   - Reason for recall
4. Click **"Simulate Recall"**
5. System shows:
   - All finished goods containing affected lot
   - Customers who received them
   - Current location (if in stock)
6. Click **"Execute Recall"**
7. System:
   - Blocks affected lots from use
   - Generates customer notification list
   - Creates quarantine instructions

---

## Mobile App (PWA)

### Installing Mobile App

**Progressive Web App (PWA)** - No app store needed!

**On Android**:
1. Open Chrome browser
2. Go to `https://app.unison.com`
3. Tap **menu (⋮)** → **"Add to Home Screen"**
4. Tap **"Install"**
5. App icon appears on home screen

**On iOS**:
1. Open Safari browser
2. Go to `https://app.unison.com`
3. Tap **share icon (⎙)**
4. Tap **"Add to Home Screen"**
5. Tap **"Add"**

**Works Offline**:
- Read work orders
- View material data
- Log production (syncs when online)

### Production Logging (Mobile)

**Best Practice**: Floor operators use mobile for real-time logging.

**Steps**:
1. Open mobile app
2. Tap **"Production"**
3. Scan work order barcode (or select from list)
4. See work order details:
   - Material, quantity planned
   - Operations
   - BOM components
5. Tap operation to log
6. Enter:
   - Good quantity
   - Scrap quantity
   - Reason for scrap (if any)
7. Tap **"Submit"**
8. Syncs to server immediately (or queues if offline)

**Barcode Scanning**:
- Supports: QR code, Code 128, EAN, UPC
- Scan:
  - Work orders
  - Materials
  - Serial numbers
  - Locations

---

## Tips & Best Practices

### General Best Practices

#### 1. Master Data Quality

**Do's**:
- ✅ Use consistent naming conventions (e.g., all material codes start with prefix)
- ✅ Fill in all mandatory fields
- ✅ Add descriptions (helps new users)
- ✅ Use categories to organize materials

**Don'ts**:
- ❌ Create duplicate materials with slight name differences
- ❌ Leave fields blank
- ❌ Use special characters in codes (breaks barcodes)

#### 2. BOM Management

**Best Practice**:
- Review BOMs quarterly (components change)
- Maintain BOM version history
- Use scrap % based on historical data
- Keep BOMs up-to-date with engineering changes

#### 3. Work Order Hygiene

**Do's**:
- ✅ Release work orders only when materials available
- ✅ Log production daily (not end of week)
- ✅ Close completed work orders promptly
- ✅ Use correct work order status

**Don'ts**:
- ❌ Leave work orders in Draft for weeks
- ❌ Backdate production logs
- ❌ Skip closing work orders

#### 4. Quality Culture

**Mindset**:
- Log NCRs immediately (not at month-end)
- Follow 8D process rigorously
- Share learnings across teams
- Celebrate quality improvements

### Performance Optimization

#### 1. Keep Data Clean

- Archive old work orders (>1 year)
- Delete duplicate materials
- Close completed NCRs
- Purge old stock adjustments

#### 2. Use Filters

- Don't load all 10,000 materials at once
- Filter by category, type, or code prefix
- Use date range filters on reports

#### 3. Mobile App

- Use mobile for floor operations (faster than desktop)
- Sync daily (don't accumulate 100+ offline entries)

### Security Best Practices

#### 1. Password Management

- ✅ Use strong passwords (8+ chars, mix of upper/lower/numbers)
- ✅ Change password every 90 days
- ❌ Don't share passwords
- ❌ Don't write passwords on paper

#### 2. User Roles

**Principle of Least Privilege**:
- Give users only the permissions they need
- Review user roles quarterly
- Disable accounts for ex-employees immediately

#### 3. Data Backup

**Organization Admin Responsibility**:
- Verify backups are running (check with support)
- Test restore process annually
- Keep backup of critical master data (Excel export)

---

## Troubleshooting

### Common Issues

#### 1. Can't Log In

**Symptoms**: "Invalid credentials" error

**Solutions**:
1. Check email typo (common mistake)
2. Check Caps Lock is off
3. Click **"Forgot Password"** → Reset password
4. Clear browser cache (Ctrl+Shift+Delete)
5. Try incognito/private window
6. Contact support if still failing

#### 2. Work Order Won't Release

**Error**: "Material shortage detected"

**Solutions**:
1. Click **"Check Material Availability"** in WO
2. See which materials are short
3. Check stock in other locations:
   - Go to **Inventory** → **Stock Overview**
   - Filter by material
   - Transfer from other location if available
4. If truly short:
   - Create purchase requisition
   - Delay work order
   - Substitute material (if BOM allows)

#### 3. Stripe Payment Declined

**Error**: "Payment failed"

**Common Reasons**:
- Insufficient funds
- Card expired
- Incorrect CVV
- Bank declined (fraud prevention)

**Solutions**:
1. Check card details in Stripe portal
2. Try different card
3. Contact your bank (may have blocked transaction)
4. Contact support for manual payment options

#### 4. Mobile App Not Syncing

**Symptoms**: Entries not appearing on desktop

**Solutions**:
1. Check internet connection (Wi-Fi or mobile data)
2. Close and reopen app
3. Check **"Sync Status"** in app settings:
   - If shows "X pending entries", tap **"Sync Now"**
4. If still failing:
   - Note down entries on paper (don't lose data)
   - Contact support
   - Enter manually on desktop as backup

#### 5. Scheduled Jobs Not Running

**Symptoms**: Trial hasn't expired but should have

**Admin Only**:
1. Go to **Admin** → **System**
2. Check **"Scheduled Jobs"** status
3. See last run time
4. If not running, contact support (likely pg_cron issue)

---

## Support

### Self-Service Resources

#### Knowledge Base

Visit: [https://help.unison.com](https://help.unison.com)

**Popular Articles**:
- How to create a multi-level BOM
- Setting up preventive maintenance schedules
- Understanding OEE calculations
- Traceability best practices

#### Video Tutorials

Visit: [https://unison.com/tutorials](https://unison.com/tutorials)

**Video Library**:
- Getting started (15 min)
- Material management (10 min)
- Work order management (12 min)
- Visual scheduling (8 min)
- Quality management (15 min)

### Contact Support

#### Email Support

**All Tiers**: support@unison.com

**Response Time**:
- Starter: 24-48 hours
- Professional: 12-24 hours
- Enterprise: 4-8 hours (priority support)

**When Emailing**:
Include:
1. Organization name
2. User email
3. Screenshot of error (if applicable)
4. Steps to reproduce issue
5. Browser/device info

#### Live Chat

**Available**: Professional and Enterprise tiers only

**Hours**: Mon-Fri, 9 AM - 6 PM (your timezone)

**Access**: Click **chat icon** (bottom-right of app)

#### Phone Support

**Available**: Enterprise tier only

**Hours**: Mon-Fri, 8 AM - 8 PM (your timezone)

**Number**: Provided in welcome email

#### Dedicated Account Manager

**Available**: Enterprise tier only

**What They Do**:
- Onboarding assistance
- Quarterly business reviews
- Feature training
- Escalation point for issues

### Feature Requests

**Have an idea?**

1. Go to **Feedback** → **Submit Idea**
2. Describe feature request
3. Explain use case (why needed)
4. Attach mockups/examples (optional)
5. Submit

**What Happens**:
- Product team reviews all requests
- Popular requests added to roadmap
- You'll be notified when feature is released

---

## Appendix

### Glossary

- **BOM**: Bill of Materials - List of components needed to make a product
- **FIFO**: First In, First Out - Inventory costing method
- **MRR**: Monthly Recurring Revenue
- **NCR**: Non-Conformance Report - Quality issue documentation
- **OEE**: Overall Equipment Effectiveness - Machine efficiency metric
- **PWA**: Progressive Web App - Web app that works like native mobile app
- **RLS**: Row-Level Security - Database security for multi-tenancy
- **UOM**: Unit of Measure - Unit for measuring material (kg, pcs, meters)
- **WO**: Work Order - Production order to manufacture product

### Keyboard Shortcuts

**Global**:
- `Ctrl+K`: Quick search
- `Ctrl+/`: Help
- `Esc`: Close modal

**Work Orders**:
- `Alt+N`: New work order
- `Alt+R`: Release work order
- `Alt+S`: Start production

**Navigation**:
- `Alt+1`: Dashboard
- `Alt+2`: Materials
- `Alt+3`: Production
- `Alt+4`: Quality
- `Alt+5`: Inventory

### Data Export

**Exporting Data**:
1. Go to any list view (Materials, Work Orders, etc.)
2. Apply filters (if needed)
3. Click **"Export"** button
4. Select format:
   - CSV (Excel compatible)
   - Excel (.xlsx)
   - PDF
5. Download file

**Use Cases**:
- Send material list to supplier
- Share production report with management
- Backup master data

---

**Need More Help?**

- 📧 Email: support@unison.com
- 💬 Live Chat: Available in app (Professional+)
- 📚 Knowledge Base: https://help.unison.com
- 🎥 Video Tutorials: https://unison.com/tutorials

**Happy Manufacturing! 🏭**

*Last Updated: 2025-11-11 | Version 1.0*
