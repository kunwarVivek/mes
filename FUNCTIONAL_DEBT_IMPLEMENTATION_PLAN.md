# Functional Debt Implementation Plan
## Unison Manufacturing ERP - Critical Gap Resolution

**Date**: 2025-11-12
**Branch**: `claude/frontend-audit-debt-fix-011CV4CvcQR9dZBLoV9oyFqq`
**Objective**: Implement critical functional debts identified in comprehensive audit

---

## AUDIT SUMMARY

### Completion Status
| Layer | Compliance | Critical Gaps | Priority Fixes |
|-------|-----------|---------------|----------------|
| **Database Schema** | 60% | 16 missing tables, 150+ missing columns | 5 tables, 30 columns |
| **Backend APIs** | 65% | 150+ functional gaps, stub integrations | 10 endpoints, 3 services |
| **Frontend UI** | 35% | 26 missing features, 14 partial | 8 features |
| **Overall** | 53% | System-wide gaps | Focus on Docker-ready MVP |

---

## PHASE 1: CRITICAL SCHEMA FIXES (Priority 1)

### 1.1 Missing Tables to Add
```sql
-- These tables block core functionality
1. suppliers (material procurement)
2. material_transactions (FIFO/LIFO costing) - TimescaleDB hypertable
3. manpower_allocation (worker tracking)
4. ncr_photos (mobile NCR workflow)
5. quality_inspections (in-process quality)
```

### 1.2 Critical Missing Columns
```sql
-- materials table
ALTER TABLE materials ADD COLUMN barcode_data VARCHAR(255);
ALTER TABLE materials ADD COLUMN qr_code_data TEXT;
ALTER TABLE materials ADD COLUMN sap_material_number VARCHAR(100);
ALTER TABLE materials ADD COLUMN minimum_stock_level INTEGER;
ALTER TABLE materials ADD COLUMN maximum_stock_level INTEGER;
ALTER TABLE materials ADD COLUMN standard_cost DECIMAL(15,2);

-- projects table
ALTER TABLE projects ADD COLUMN customer_name VARCHAR(255);
ALTER TABLE projects ADD COLUMN sap_sales_order VARCHAR(100);
ALTER TABLE projects ADD COLUMN project_manager_id INTEGER REFERENCES users(id);
ALTER TABLE projects ADD COLUMN budget DECIMAL(15,2);

-- machines table
ALTER TABLE machines ADD COLUMN machine_type VARCHAR(100);
ALTER TABLE machines ADD COLUMN status VARCHAR(50);
ALTER TABLE machines ADD COLUMN current_work_order_id INTEGER;

-- organizations table
ALTER TABLE organizations ADD COLUMN industry VARCHAR(100);
ALTER TABLE organizations ADD COLUMN address TEXT;
ALTER TABLE organizations ADD COLUMN contact_email VARCHAR(255);
```

### 1.3 Missing Indexes (Performance Critical)
```sql
-- Full-text search (pg_search BM25) - if extension available
-- Otherwise use pg_trgm GIN indexes
CREATE INDEX idx_materials_search ON materials USING gin(
  to_tsvector('english', material_number || ' ' || name || ' ' || description)
);

CREATE INDEX idx_work_orders_search ON work_orders USING gin(
  to_tsvector('english', work_order_number || ' ' || description)
);

-- Performance indexes
CREATE INDEX idx_materials_barcode ON materials(barcode_data) WHERE barcode_data IS NOT NULL;
CREATE INDEX idx_machines_status ON machines(status) WHERE is_active = TRUE;
```

---

## PHASE 2: BACKEND CRITICAL FIXES (Priority 1)

### 2.1 Fix Stub Integrations

#### Email Service Implementation
**File**: `/home/user/mes/backend/app/application/services/email_service.py`
```python
# Replace all 'pass' statements with actual SMTP implementation
# Use environment variables for SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

#### Barcode Generation Service
**File**: `/home/user/mes/backend/app/application/services/barcode_service.py`
```python
# Ensure generate_barcode() actually returns image bytes
# Test with materials and work_orders
```

### 2.2 Add Missing API Endpoints

#### Suppliers CRUD
**File**: `/home/user/mes/backend/app/presentation/api/v1/suppliers.py` (NEW)
```python
@router.get("/suppliers")
@router.post("/suppliers")
@router.get("/suppliers/{id}")
@router.put("/suppliers/{id}")
@router.delete("/suppliers/{id}")
```

#### Material Transactions for FIFO/LIFO
**File**: `/home/user/mes/backend/app/presentation/api/v1/material_transactions.py` (NEW)
```python
@router.post("/material-transactions")
@router.get("/material-transactions")
@router.get("/material-transactions/{material_id}/costing")
```

#### NCR Photos Upload
**File**: Update `/home/user/mes/backend/app/presentation/api/v1/quality.py`
```python
@router.post("/ncr-reports/{ncr_id}/photos")
async def upload_ncr_photo(ncr_id: int, file: UploadFile):
    # Upload to MinIO
    # Create ncr_photos record
    # Return photo URL
```

### 2.3 Add Missing Business Logic

#### Work Order Costing Service Enhancement
**File**: `/home/user/mes/backend/app/application/services/work_order_costing_service.py`
```python
# Implement FIFO/LIFO material costing
# Integrate with material_transactions table
# Calculate actual_material_cost using costing method from organization
```

#### Material Costing Service
**File**: `/home/user/mes/backend/app/application/services/costing_service.py` (NEW)
```python
def calculate_fifo_cost(material_id, quantity):
    # Query material_transactions ordered by transaction_date ASC
    # Sum costs for quantity needed using oldest inventory first
    pass

def calculate_lifo_cost(material_id, quantity):
    # Query material_transactions ordered by transaction_date DESC
    # Sum costs for quantity needed using newest inventory first
    pass

def calculate_weighted_average_cost(material_id):
    # Calculate average cost across all inventory
    pass
```

---

## PHASE 3: FRONTEND CRITICAL FIXES (Priority 1)

### 3.1 PWA Configuration (BLOCKING)
**File**: `/home/user/mes/frontend/vite.config.ts`
```typescript
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icons/*'],
      manifest: {
        name: 'Unison Manufacturing ERP',
        short_name: 'Unison',
        description: 'Manufacturing Execution System',
        theme_color: '#1976d2',
        background_color: '#ffffff',
        display: 'standalone',
        scope: '/',
        start_url: '/',
        icons: [
          {
            src: 'icons/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'icons/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\./,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 // 1 hour
              }
            }
          }
        ]
      }
    })
  ]
})
```

### 3.2 Offline Queue Integration
**File**: `/home/user/mes/frontend/src/components/OfflineIndicator.tsx` (NEW)
```typescript
export const OfflineIndicator = () => {
  const { isOffline, queueLength, syncQueue } = useOffline()

  if (!isOffline && queueLength === 0) return null

  return (
    <div className="fixed bottom-4 right-4 bg-yellow-500 text-white p-4 rounded-lg">
      {isOffline ? (
        <p>Offline - {queueLength} items queued</p>
      ) : (
        <button onClick={syncQueue}>Sync {queueLength} items</button>
      )}
    </div>
  )
}
```

**Integrate in**: Production logging, NCR creation, material receipt forms

### 3.3 Barcode Scanner Component
**File**: `/home/user/mes/frontend/src/components/BarcodeScanner.tsx` (NEW)
```typescript
import { useCamera } from '@/hooks/useCamera'
import { BrowserMultiFormatReader } from '@zxing/library'

export const BarcodeScanner = ({ onScan, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const { requestCamera, stopCamera } = useCamera()

  useEffect(() => {
    const codeReader = new BrowserMultiFormatReader()
    requestCamera().then(stream => {
      videoRef.current.srcObject = stream
      codeReader.decodeFromVideoDevice(null, videoRef.current, (result, err) => {
        if (result) {
          onScan(result.getText())
          stopCamera()
        }
      })
    })
  }, [])

  return (
    <div className="fixed inset-0 bg-black z-50">
      <video ref={videoRef} className="w-full h-full object-cover" />
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="border-4 border-white w-64 h-64" />
      </div>
      <button onClick={onClose} className="absolute top-4 left-4 text-white">
        Cancel
      </button>
    </div>
  )
}
```

### 3.4 NCR Photo Capture
**File**: `/home/user/mes/frontend/src/features/quality/components/NCRPhotoCapture.tsx` (NEW)
```typescript
import { useCamera } from '@/hooks/useCamera'

export const NCRPhotoCapture = ({ onPhotoCaptured, maxPhotos = 3 }) => {
  const [photos, setPhotos] = useState<string[]>([])
  const { capturePhoto, requestCamera } = useCamera()
  const videoRef = useRef<HTMLVideoElement>(null)

  const handleCapture = async () => {
    if (photos.length >= maxPhotos) return
    const photoData = await capturePhoto(videoRef.current)
    setPhotos([...photos, photoData])
    onPhotoCaptured([...photos, photoData])
  }

  return (
    <div>
      <video ref={videoRef} autoPlay className="w-full" />
      <button onClick={handleCapture} disabled={photos.length >= maxPhotos}>
        Capture Photo ({photos.length}/{maxPhotos})
      </button>
      <div className="grid grid-cols-3 gap-2 mt-4">
        {photos.map((photo, i) => (
          <img key={i} src={photo} alt={`Photo ${i+1}`} />
        ))}
      </div>
    </div>
  )
}
```

**Integrate in**: `/home/user/mes/frontend/src/features/quality/components/NCRForm.tsx`

### 3.5 Material Barcode Scanning Integration
**File**: Update `/home/user/mes/frontend/src/features/materials/pages/MaterialsPage.tsx`
```typescript
const [showScanner, setShowScanner] = useState(false)

const handleBarcodeScan = async (barcode: string) => {
  const material = await materialService.getMaterialByBarcode(barcode)
  if (material) {
    navigate(`/materials/${material.id}`)
  }
}

// Add scan button in header
<Button onClick={() => setShowScanner(true)}>Scan Barcode</Button>

{showScanner && (
  <BarcodeScanner
    onScan={handleBarcodeScan}
    onClose={() => setShowScanner(false)}
  />
)}
```

---

## PHASE 4: DOCKER COMPATIBILITY FIXES

### 4.1 Backend Dockerfile Issues to Fix
**File**: `/home/user/mes/backend/Dockerfile`
- ✅ Already using Python 3.11-slim (good)
- ✅ Already installing gcc and postgresql-client
- ⚠️ May need to add: libpq-dev for psycopg2
- ⚠️ May need to add: python3-dev for native extensions

### 4.2 Frontend Dockerfile Issues to Fix
**File**: `/home/user/mes/frontend/Dockerfile`
- ✅ Using Node 20-alpine (good)
- ⚠️ Running dev server in production (BAD - should build static files)

**Recommended Production Dockerfile**:
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 4.3 Docker Compose Issues to Fix
**File**: `/home/user/mes/docker-compose.yml`
- ✅ Services are well-defined
- ⚠️ Frontend should serve production build, not dev server
- ⚠️ May need to add health checks for all services
- ⚠️ Backend migrations should run automatically on startup

---

## IMPLEMENTATION PRIORITY ORDER

### Sprint 1: Docker-Ready MVP (Days 1-3)
1. ✅ Fix backend Dockerfile (add missing dependencies)
2. ✅ Fix frontend Dockerfile (production build)
3. ✅ Test `docker-compose build` (no errors)
4. ✅ Test `docker-compose up` (all services start)
5. ✅ Add email service implementation (SMTP)
6. ✅ Fix barcode generation (ensure it works)

### Sprint 2: Schema Critical Path (Days 4-5)
7. ✅ Create migration 020: Add suppliers, material_transactions, ncr_photos tables
8. ✅ Create migration 021: Add missing columns to materials, projects, machines
9. ✅ Create migration 022: Add performance indexes
10. ✅ Run migrations and test database

### Sprint 3: Backend API Gaps (Days 6-7)
11. ✅ Add suppliers CRUD endpoints
12. ✅ Add material transactions endpoints
13. ✅ Add NCR photos upload endpoint
14. ✅ Implement FIFO/LIFO costing logic
15. ✅ Test all new endpoints with curl/Postman

### Sprint 4: Frontend PWA & Mobile (Days 8-10)
16. ✅ Configure Vite PWA plugin
17. ✅ Create OfflineIndicator component
18. ✅ Create BarcodeScanner component
19. ✅ Create NCRPhotoCapture component
20. ✅ Integrate offline queue in forms
21. ✅ Integrate barcode scanning in material receipt
22. ✅ Test PWA install and offline capabilities

---

## TESTING CHECKLIST

### Docker Build Tests
- [ ] `docker-compose build --no-cache` completes without errors
- [ ] Backend container starts and connects to database
- [ ] Frontend container builds and serves production files
- [ ] PostgreSQL extensions load correctly
- [ ] MinIO storage is accessible
- [ ] All services are healthy

### Backend API Tests
- [ ] Email service sends test email
- [ ] Barcode generation returns PNG image
- [ ] Suppliers CRUD works end-to-end
- [ ] Material transactions create correctly
- [ ] NCR photos upload to MinIO
- [ ] FIFO/LIFO costing calculations are accurate

### Frontend Tests
- [ ] PWA installs to home screen
- [ ] Offline indicator appears when offline
- [ ] Production logs queue when offline and sync when online
- [ ] Barcode scanner opens camera and decodes barcodes
- [ ] NCR form captures 3 photos and uploads
- [ ] Mobile responsive layouts work on 375px width

---

## SUCCESS CRITERIA

### Definition of Done
1. ✅ Docker Compose builds and runs without errors
2. ✅ All critical database tables exist with proper RLS
3. ✅ Email notifications work (SMTP configured)
4. ✅ Barcode generation works for materials and work orders
5. ✅ PWA can be installed on mobile devices
6. ✅ Offline queue works for production logging
7. ✅ NCR photos can be captured and uploaded
8. ✅ Material barcode scanning works
9. ✅ Basic FIFO/LIFO costing implemented
10. ✅ No TypeScript/Python errors in build

### Metrics
- **Docker Build Time**: < 10 minutes
- **Backend Startup Time**: < 30 seconds
- **Frontend Build Time**: < 5 minutes
- **PWA Install Score** (Lighthouse): > 90
- **Test Coverage**: > 70% for new code

---

## NEXT STEPS AFTER THIS PLAN

### Phase 2 (Future Sprints)
- Gantt visual scheduling
- Lot/serial traceability
- Workflow engine UI
- Inspection plans & SPC
- Advanced dashboards (OTD, FPY)

### Phase 3 (Post-MVP)
- SAP integration implementation
- Stripe payment processing
- Advanced analytics
- Multi-language support
- Mobile app (React Native)

---

**End of Implementation Plan**
