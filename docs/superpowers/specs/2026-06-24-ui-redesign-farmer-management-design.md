# UI Redesign + Farmer Management — Design Spec
**Date:** 2026-06-24  
**Status:** Approved

---

## 1. Goal

Rebuild all frontend pages with a polished agricultural UI (green, earthy, approachable), add a proper farmer account system where one farmer can own multiple farms, and restructure the repo to match the capstone required layout.

---

## 2. Scope

### In scope
- Replace 6 scattered HTML pages with 3 focused single-page apps
- Add `farmers` table to DB and link farms to farmers
- New admin farmer management UI (CRUD)
- Farmer logs in by name, sees all their farms in one dashboard
- Logout for both admin and farmer
- Add capstone scaffolding files to repo root

### Out of scope
- Sensor data entry (handled by a separate simulation program later)
- Real authentication (JWT, sessions) — sessionStorage sufficient for capstone
- ROI calculator page (kept as-is or removed)

---

## 3. Data Model Changes

### New table: `farmers`
| Column | Type | Notes |
|---|---|---|
| `id` | TEXT (UUID) | Primary key |
| `name` | TEXT | Unique, used as login credential |
| `created_at` | TEXT | ISO timestamp |

### Modified table: `farms`
- Add column `farmer_id TEXT REFERENCES farmers(id) ON DELETE SET NULL`

---

## 4. API Changes

### New endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/farmers` | List all farmers |
| POST | `/farmers` | Create farmer `{name}` |
| PUT | `/farmers/{id}` | Rename farmer |
| DELETE | `/farmers/{id}` | Delete farmer, unlink their farms |
| GET | `/farmers/by-name/{name}` | Farmer login lookup — returns farmer + their farms |
| PUT | `/farms/{id}/farmer` | Assign/unassign farm to farmer `{farmer_id}` |

### Existing endpoints unchanged
All `/readings`, `/plots`, `/farms`, `/explain`, `/translate` endpoints remain as-is.

---

## 5. Frontend Pages

### 5.1 `index.html` — Login
- Two cards (stacked on mobile, side-by-side on desktop)
- **Left card — Farmer:** name input + "Mag-log in" button. On success: `GET /farmers/by-name/{name}`, store farmer in sessionStorage, redirect to `farmer.html`
- **Right card — Admin:** username + password inputs. Check `admin`/`admin` client-side, store `adminAuth` in sessionStorage, redirect to `admin.html`
- Error messages inline per card
- Branding: leaf icon, green header, earthy background (`#f7fbf0`)

### 5.2 `admin.html` — Admin Single-Page App
**Layout:** Fixed left sidebar (240px) + scrollable main content.

**Sidebar:**
- App logo + name at top
- Nav items: Dashboard, Farmers, Farms (icon + label)
- Logout button at bottom (clears sessionStorage → `/`)
- Auth guard: redirect to `/` if no `adminAuth`

**Dashboard tab:**
- Summary cards: total farmers, total farms, total sensors with readings
- Existing Google Maps farm map (ported from current dashboard.html)
- Farm list table with sensor status

**Farmers tab:**
- Table: Farmer Name | Farms Count | Actions (Edit / Delete)
- "Add Farmer" button → inline form or modal: just a name field
- Edit: rename farmer inline
- Delete: confirm dialog, unlinks their farms (doesn't delete farms)
- Each row expandable to show assigned farms

**Farms tab:**
- Table: Farm Name | Farmer | Sensors | Hectares | Actions
- Create farm: name, owner display name, draw boundary on mini-map, assign to farmer dropdown
- Edit farm: change name, reassign farmer
- Delete farm: confirm dialog

### 5.3 `farmer.html` — Farmer Single-Page App
**Layout:** Fixed top header + scrollable content + fixed bottom nav.

**Header:** "Aking Bukid" logo, farmer's name, language toggle (Tagalog/English).

**Bottom nav (4 tabs):**
1. **Aking mga Bukid / My Farms** — cards for each farm showing: farm name, crop recommendation badge (color-coded confidence), sensor count. Tap a farm card to go to Sensors tab pre-selected on that farm.
2. **Mga Sensor / Sensors** — farm selector dropdown at top, then sensor list, latest readings grid, "Bakit?" explain button + AI explanation text
3. **Kasaysayan / History** — reading history table for selected farm
4. **Settings** — language (Tagalog / English), theme (light / dark), logout button

**Auth:** On load, check `sessionStorage.getItem("farmerAuth")` (stores `{id, name, farms[]}`). If missing, redirect to `/`.

---

## 6. Folder Structure

Keep Python backend at repo root (moving would break `py -m uvicorn main:app --reload`). Add capstone scaffolding around it:

```
dict-capstone/               ← capstone repo root
├── README.md                ← project overview
├── AGENTS.md                ← AI agent instructions
├── TASKS.md                 ← task tracking
├── PROMPTS.md               ← prompts used
├── DESIGN.md                ← link/mirror of this spec
├── proposal/                ← (empty, for capstone submission)
├── prototype/               ← (empty, for capstone submission)
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-06-24-ui-redesign-farmer-management-design.md
├── presentation/            ← (empty, for capstone submission)
├── main.py                  ← FastAPI app (stays at root)
├── db.py
├── explain.py
├── translate.py
├── geometry.py
├── sensor_sim.py
├── train_crop_model.py
└── frontend/                ← served by FastAPI as static files
    ├── index.html           ← login
    ├── admin.html           ← admin SPA
    └── farmer.html          ← farmer SPA
```

Old pages removed: `add_plot.html`, `add_reading.html`, `roi.html` (functionality folded into admin.html or out of scope).

---

## 7. UI Design System

- **Primary green:** `#0d631b`
- **Background:** `#f7fbf0` (light green-tinted white)
- **Surface:** `#ffffff`
- **Text:** `#181d17`
- **Font:** Plus Jakarta Sans
- **Radius:** `rounded-xl` (12px) for cards, `rounded-lg` (8px) for inputs/buttons
- **Shadows:** `shadow-sm` for cards, stronger `shadow-md` for modals
- **Icons:** Material Symbols Outlined
- Tailwind CSS via CDN

---

## 8. What Gets Deleted

| File | Reason |
|---|---|
| `frontend/add_plot.html` | Folded into admin.html Farms tab |
| `frontend/add_reading.html` | Sensor data handled by external simulation program |
| `frontend/roi.html` | Out of scope for this redesign |

---

## 9. Implementation Order

1. DB migration — add `farmers` table, `farmer_id` to `farms`
2. Backend — new farmer endpoints
3. `index.html` — redesign login
4. `admin.html` — build admin SPA (Dashboard → Farmers → Farms tabs)
5. `farmer.html` — build farmer SPA (My Farms → Sensors → Settings tabs)
6. Capstone scaffolding — add README, AGENTS, TASKS, PROMPTS, DESIGN + empty folders
7. Cleanup — delete old pages
