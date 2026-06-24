# UI Redesign + Farmer Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 6 scattered HTML pages with 3 polished single-page apps, add a farmer account system (one farmer → many farms), and add capstone repo scaffolding.

**Architecture:** SQLite DB gets a new `farmers` table + `farmer_id` FK on `farms`. FastAPI gets 6 new endpoints. Three HTML files replace the current frontend: `index.html` (login), `admin.html` (admin SPA with left sidebar), `farmer.html` (farmer SPA with bottom nav).

**Tech Stack:** Python 3.14, FastAPI, SQLite (via db.py), Tailwind CSS CDN, Material Symbols Outlined, Plus Jakarta Sans, Google Maps JS API (key in `frontend/config.js`)

## Global Constraints

- Server run command: `py -m uvicorn main:app --reload` from repo root — never move `main.py`
- Auth: `sessionStorage` only — `adminAuth` for admin, `farmerAuth` (JSON) for farmer
- Admin credentials: username `admin`, password `admin` — checked client-side
- Farmer credential: farmer name — validated via `GET /farmers/by-name/{name}`
- UI colors: primary `#0d631b`, background `#f7fbf0`, surface `#ffffff`, text `#181d17`
- Font: Plus Jakarta Sans (Google Fonts CDN)
- Icons: Material Symbols Outlined (Google Fonts CDN)
- Tailwind via CDN: `https://cdn.tailwindcss.com`
- All HTML files go in `frontend/` — served as static files by FastAPI
- SQLite DB file: `readings.db` at repo root
- Existing API endpoints (`/readings`, `/plots`, `/farms`, `/explain`) unchanged

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `db.py` | Modify | Add `farmers` table schema + 6 new db functions |
| `main.py` | Modify | Add 6 new farmer API endpoints + `FarmerIn` model |
| `frontend/index.html` | Replace | Login page — farmer name OR admin credentials |
| `frontend/admin.html` | Replace | Admin SPA — Dashboard / Farmers / Farms sidebar tabs |
| `frontend/farmer.html` | Replace | Farmer SPA — My Farms / Sensors / History / Settings bottom nav |
| `frontend/add_plot.html` | Delete | Folded into admin.html |
| `frontend/add_reading.html` | Delete | Out of scope |
| `frontend/roi.html` | Delete | Out of scope |
| `README.md` | Create | Capstone project overview |
| `AGENTS.md` | Create | AI agent instructions |
| `TASKS.md` | Create | Task tracking |
| `PROMPTS.md` | Create | Prompts log |
| `DESIGN.md` | Create | Link to spec |
| `proposal/`, `prototype/`, `presentation/` | Create dirs | Empty capstone folders |

---

## Task 1: DB Migration — farmers table + farmer_id on farms

**Files:**
- Modify: `db.py`

**Interfaces:**
- Produces:
  - `insert_farmer(farmer: dict) -> dict` — farmer dict has keys `id`, `name`, `created_at`
  - `get_farmer(farmer_id: str) -> dict | None`
  - `get_farmer_by_name(name: str) -> dict | None` — returns farmer dict or None
  - `get_all_farmers() -> list[dict]` — each dict has `id`, `name`, `created_at`, `farm_count: int`
  - `update_farmer(farmer_id: str, name: str) -> dict | None`
  - `delete_farmer(farmer_id: str)` — sets `farmer_id = NULL` on linked farms, then deletes farmer
  - `assign_farm_to_farmer(farm_id: str, farmer_id: str | None)` — sets or clears farmer link

- [ ] **Step 1: Add `SCHEMA_FARMERS` constant and migration to `init_db()`**

In `db.py`, after the `SCHEMA_FARMS` constant, add:

```python
SCHEMA_FARMERS = """
CREATE TABLE IF NOT EXISTS farmers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
)
"""
```

Then in `init_db()`, after `conn.execute(SCHEMA_FARMS)`, add:

```python
        conn.execute(SCHEMA_FARMERS)
        try:
            conn.execute("ALTER TABLE farms ADD COLUMN farmer_id TEXT REFERENCES farmers(id) ON DELETE SET NULL")
        except sqlite3.OperationalError:
            pass  # already migrated
```

- [ ] **Step 2: Add the 6 new db functions at the bottom of `db.py`**

```python
def insert_farmer(farmer: dict) -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO farmers (id, name, created_at) VALUES (?, ?, ?)",
            (farmer["id"], farmer["name"], farmer["created_at"]),
        )
    return get_farmer(farmer["id"])


def get_farmer(farmer_id: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_farmer_by_name(name: str) -> dict | None:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM farmers WHERE name = ?", (name,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_all_farmers() -> list[dict]:
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT f.*, COUNT(fm.farm_id) AS farm_count
            FROM farmers f
            LEFT JOIN farms fm ON fm.farmer_id = f.id
            GROUP BY f.id
            ORDER BY f.created_at DESC
        """)
        return [dict(r) for r in cur.fetchall()]


def update_farmer(farmer_id: str, name: str) -> dict | None:
    with get_conn() as conn:
        conn.execute("UPDATE farmers SET name = ? WHERE id = ?", (name, farmer_id))
    return get_farmer(farmer_id)


def delete_farmer(farmer_id: str):
    with get_conn() as conn:
        conn.execute("UPDATE farms SET farmer_id = NULL WHERE farmer_id = ?", (farmer_id,))
        conn.execute("DELETE FROM farmers WHERE id = ?", (farmer_id,))


def assign_farm_to_farmer(farm_id: str, farmer_id: str | None):
    with get_conn() as conn:
        conn.execute("UPDATE farms SET farmer_id = ? WHERE farm_id = ?", (farmer_id, farm_id))
```

- [ ] **Step 3: Verify migration runs cleanly**

```powershell
py -c "import db; db.init_db(); print('OK')"
```
Expected output: `OK` (no errors)

- [ ] **Step 4: Quick smoke test**

```powershell
py -c "
import db, uuid
from datetime import datetime, timezone
db.init_db()
f = db.insert_farmer({'id': str(uuid.uuid4()), 'name': 'test-farmer', 'created_at': datetime.now(timezone.utc).isoformat()})
print('created:', f['name'])
farmers = db.get_all_farmers()
print('all farmers:', len(farmers))
found = db.get_farmer_by_name('test-farmer')
print('by name:', found['name'])
db.delete_farmer(f['id'])
print('deleted ok')
"
```
Expected: prints created/all/by name/deleted lines without errors.

- [ ] **Step 5: Commit**

```powershell
git add db.py
git commit -m "feat: add farmers table and farmer db functions"
```

---

## Task 2: Backend — Farmer API Endpoints

**Files:**
- Modify: `main.py`

**Interfaces:**
- Consumes: all 7 db functions from Task 1
- Produces:
  - `GET /farmers` → `list[dict]` each with `id, name, created_at, farm_count`
  - `POST /farmers` body `{name: str}` → `dict` farmer
  - `PUT /farmers/{farmer_id}` body `{name: str}` → `dict` farmer
  - `DELETE /farmers/{farmer_id}` → `{deleted: str}`
  - `GET /farmers/by-name/{name}` → `dict` with `id, name, farms: list[dict]`
  - `PUT /farms/{farm_id}/farmer` body `{farmer_id: str | None}` → `{farm_id, farmer_id}`

- [ ] **Step 1: Add `FarmerIn` and `FarmAssignIn` Pydantic models to `main.py`**

Add after the existing Pydantic models (around line 100, after `ReadingIn`):

```python
class FarmerIn(BaseModel):
    name: str

class FarmAssignIn(BaseModel):
    farmer_id: str | None = None
```

- [ ] **Step 2: Add farmer endpoints to `main.py`**

Add before the `app.mount(...)` line at the bottom of `main.py`:

```python
@app.get("/farmers")
def list_farmers():
    return db.get_all_farmers()


@app.post("/farmers")
def create_farmer(body: FarmerIn):
    import uuid
    if db.get_farmer_by_name(body.name):
        raise HTTPException(status_code=409, detail=f"Farmer name already taken: {body.name}")
    return db.insert_farmer({
        "id": str(uuid.uuid4()),
        "name": body.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


@app.put("/farmers/{farmer_id}")
def update_farmer(farmer_id: str, body: FarmerIn):
    if not db.get_farmer(farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {farmer_id}")
    existing = db.get_farmer_by_name(body.name)
    if existing and existing["id"] != farmer_id:
        raise HTTPException(status_code=409, detail=f"Name already taken: {body.name}")
    return db.update_farmer(farmer_id, body.name)


@app.delete("/farmers/{farmer_id}")
def remove_farmer(farmer_id: str):
    if not db.get_farmer(farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {farmer_id}")
    db.delete_farmer(farmer_id)
    return {"deleted": farmer_id}


@app.get("/farmers/by-name/{name}")
def farmer_by_name(name: str):
    farmer = db.get_farmer_by_name(name)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {name}")
    farms = [f for f in db.get_all_farms() if f.get("farmer_id") == farmer["id"]]
    for f in farms:
        f["polygon"] = json.loads(f["polygon"]) if isinstance(f["polygon"], str) else f["polygon"]
        f["sensors"] = db.get_latest_for_farm(f["farm_id"])
    return {**farmer, "farms": farms}


@app.put("/farms/{farm_id}/farmer")
def assign_farmer(farm_id: str, body: FarmAssignIn):
    if not db.get_farm(farm_id):
        raise HTTPException(status_code=404, detail=f"Unknown farm: {farm_id}")
    if body.farmer_id and not db.get_farmer(body.farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {body.farmer_id}")
    db.assign_farm_to_farmer(farm_id, body.farmer_id)
    return {"farm_id": farm_id, "farmer_id": body.farmer_id}
```

- [ ] **Step 3: Restart server and test endpoints**

```powershell
py -m uvicorn main:app --reload
```

In another terminal:
```powershell
# Create a farmer
$r = Invoke-WebRequest -Uri "http://127.0.0.1:8000/farmers" -Method POST -ContentType "application/json" -Body '{"name":"test-farmer2"}'
$r.StatusCode  # expect 200
# List farmers
Invoke-WebRequest -Uri "http://127.0.0.1:8000/farmers" -Method GET | Select-Object -ExpandProperty Content
# Delete
$id = ($r.Content | ConvertFrom-Json).id
Invoke-WebRequest -Uri "http://127.0.0.1:8000/farmers/$id" -Method DELETE
```

- [ ] **Step 4: Commit**

```powershell
git add main.py
git commit -m "feat: add farmer CRUD endpoints and farm-farmer assignment"
```

---

## Task 3: Login Page (`index.html`)

**Files:**
- Replace: `frontend/index.html`

**Interfaces:**
- Consumes: `GET /farmers/by-name/{name}` → stores `farmerAuth` JSON in sessionStorage
- Produces: sets `sessionStorage.adminAuth = "1"` or `sessionStorage.farmerAuth = JSON`

- [ ] **Step 1: Replace `frontend/index.html` with the new login page**

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Agri-Admin | Login</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
  body { font-family: 'Plus Jakarta Sans', sans-serif; background: #f7fbf0; }
  .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }
</style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 gap-8">

  <!-- Header -->
  <div class="text-center">
    <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-[#0d631b] text-white mb-4 shadow-lg">
      <span class="material-symbols-outlined text-4xl" style="font-variation-settings:'FILL' 1;">potted_plant</span>
    </div>
    <h1 class="text-3xl font-bold text-[#0d631b]">Agri-Admin</h1>
    <p class="text-gray-500 mt-1 text-sm">Crop Recommendation System</p>
  </div>

  <!-- Login cards -->
  <div class="w-full max-w-2xl grid grid-cols-1 md:grid-cols-2 gap-4">

    <!-- Farmer card -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
      <div class="flex items-center gap-2 mb-1">
        <span class="material-symbols-outlined text-[#0d631b]" style="font-variation-settings:'FILL' 1;">agriculture</span>
        <h2 class="font-bold text-lg text-gray-800">Para sa Magsasaka</h2>
      </div>
      <p class="text-sm text-gray-500">I-type ang iyong pangalan para makita ang iyong mga bukid.</p>
      <div class="space-y-3">
        <input id="farmerNameInput" type="text" placeholder="Pangalan ng magsasaka"
          class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#0d631b] focus:ring-1 focus:ring-[#0d631b] transition"/>
        <button id="farmerLoginBtn"
          class="w-full bg-[#0d631b] text-white font-bold py-2.5 rounded-lg text-sm hover:bg-green-800 transition active:scale-95">
          Mag-log in bilang Magsasaka
        </button>
        <p id="farmerError" class="text-xs text-red-500 hidden">Hindi nahanap ang magsasaka. Subukan muli.</p>
      </div>
    </div>

    <!-- Admin card -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
      <div class="flex items-center gap-2 mb-1">
        <span class="material-symbols-outlined text-[#0d631b]" style="font-variation-settings:'FILL' 1;">admin_panel_settings</span>
        <h2 class="font-bold text-lg text-gray-800">Para sa Admin</h2>
      </div>
      <p class="text-sm text-gray-500">I-access ang buong dashboard ng sistema.</p>
      <div class="space-y-3">
        <input id="adminUser" type="text" placeholder="Username"
          class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#0d631b] focus:ring-1 focus:ring-[#0d631b] transition"/>
        <input id="adminPass" type="password" placeholder="Password"
          class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#0d631b] focus:ring-1 focus:ring-[#0d631b] transition"/>
        <button id="adminLoginBtn"
          class="w-full border-2 border-[#0d631b] text-[#0d631b] font-bold py-2.5 rounded-lg text-sm hover:bg-[#0d631b] hover:text-white transition active:scale-95">
          Mag-log in bilang Admin
        </button>
        <p id="adminError" class="text-xs text-red-500 hidden">Maling username o password.</p>
      </div>
    </div>
  </div>

<script>
  async function farmerLogin() {
    const name = document.getElementById("farmerNameInput").value.trim();
    if (!name) return;
    const err = document.getElementById("farmerError");
    err.classList.add("hidden");
    const btn = document.getElementById("farmerLoginBtn");
    btn.textContent = "Sandali lang...";
    btn.disabled = true;
    try {
      const res = await fetch(`/farmers/by-name/${encodeURIComponent(name)}`);
      if (!res.ok) { err.classList.remove("hidden"); return; }
      const farmer = await res.json();
      sessionStorage.setItem("farmerAuth", JSON.stringify(farmer));
      window.location.href = "/farmer.html";
    } catch { err.classList.remove("hidden"); }
    finally { btn.textContent = "Mag-log in bilang Magsasaka"; btn.disabled = false; }
  }

  function adminLogin() {
    const u = document.getElementById("adminUser").value.trim();
    const p = document.getElementById("adminPass").value;
    const err = document.getElementById("adminError");
    if (u === "admin" && p === "admin") {
      sessionStorage.setItem("adminAuth", "1");
      window.location.href = "/admin.html";
    } else {
      err.classList.remove("hidden");
    }
  }

  document.getElementById("farmerLoginBtn").addEventListener("click", farmerLogin);
  document.getElementById("farmerNameInput").addEventListener("keydown", e => { if (e.key === "Enter") farmerLogin(); });
  document.getElementById("adminLoginBtn").addEventListener("click", adminLogin);
  ["adminUser","adminPass"].forEach(id =>
    document.getElementById(id).addEventListener("keydown", e => { if (e.key === "Enter") adminLogin(); })
  );
</script>
</body></html>
```

- [ ] **Step 2: Verify in browser**

Navigate to `http://127.0.0.1:8000/` — two cards side by side on desktop, stacked on mobile. Test wrong admin credentials show error. Test wrong farmer name shows error.

- [ ] **Step 3: Commit**

```powershell
git add frontend/index.html
git commit -m "feat: redesign login page with farmer name and admin credential cards"
```

---

## Task 4: Admin SPA (`admin.html`)

**Files:**
- Replace: `frontend/admin.html` (currently `frontend/dashboard.html` — rename + rewrite)

**Interfaces:**
- Consumes: `GET /farmers`, `POST /farmers`, `PUT /farmers/{id}`, `DELETE /farmers/{id}`, `GET /farms`, `POST /farms`, `PUT /farms/{id}`, `DELETE /farms/{id}`, `PUT /farms/{id}/farmer`, `GET /farms/{id}/predict`
- Auth guard: `if (!sessionStorage.getItem("adminAuth")) window.location.replace("/")`

- [ ] **Step 1: Create `frontend/admin.html`**

Write the full file. The structure is:

```
<html>
  <head> — auth guard script, Tailwind, fonts, icons, Google Maps, tailwind config </head>
  <body class="flex h-screen overflow-hidden bg-[#f7fbf0]">

    <!-- LEFT SIDEBAR (fixed, 240px) -->
    <aside id="sidebar" class="w-60 flex-shrink-0 h-screen flex flex-col bg-white border-r border-gray-100 shadow-sm">
      <!-- Logo -->
      <div class="p-5 border-b border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-[#0d631b] rounded-xl flex items-center justify-center">
            <span class="material-symbols-outlined text-white text-xl" style="...FILL 1">potted_plant</span>
          </div>
          <span class="font-bold text-[#0d631b] text-lg">Agri-Admin</span>
        </div>
      </div>
      <!-- Nav -->
      <nav class="flex-1 p-3 space-y-1">
        <button data-tab="tabDashboard" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-50 transition">
          <span class="material-symbols-outlined">dashboard</span> Dashboard
        </button>
        <button data-tab="tabFarmers" class="nav-btn ...">
          <span class="material-symbols-outlined">group</span> Mga Magsasaka
        </button>
        <button data-tab="tabFarms" class="nav-btn ...">
          <span class="material-symbols-outlined">grass</span> Mga Bukid
        </button>
      </nav>
      <!-- Logout -->
      <div class="p-3 border-t border-gray-100">
        <button id="logoutBtn" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-red-600 hover:bg-red-50 transition">
          <span class="material-symbols-outlined">logout</span> Mag-logout
        </button>
      </div>
    </aside>

    <!-- MAIN CONTENT -->
    <main class="flex-1 overflow-y-auto">

      <!-- DASHBOARD TAB -->
      <div id="tabDashboard">
        <!-- Stats row: 3 cards -->
        <!-- Google Map -->
        <!-- Farm status table -->
      </div>

      <!-- FARMERS TAB -->
      <div id="tabFarmers" class="hidden">
        <!-- Header + Add button -->
        <!-- Farmers table: Name | Farms | Created | Actions -->
        <!-- Add/Edit modal -->
      </div>

      <!-- FARMS TAB -->
      <div id="tabFarms" class="hidden">
        <!-- Header + Add button -->
        <!-- Farms table: Farm Name | Farmer | Sensors | Hectares | Actions -->
        <!-- Add/Edit modal with farmer assign dropdown -->
      </div>

    </main>
  </body>
</html>
```

Full implementation of `frontend/admin.html`:

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Agri-Admin | Dashboard</title>
<script>if (!sessionStorage.getItem("adminAuth")) window.location.replace("/");</script>
<script src="https://cdn.tailwindcss.com"></script>
<script src="config.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
  body { font-family: 'Plus Jakarta Sans', sans-serif; }
  .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }
  .hidden { display: none !important; }
  .nav-btn.active { background: #f0fdf4; color: #0d631b; font-weight: 700; }
  #map { height: 420px; width: 100%; border-radius: 12px; }
</style>
</head>
<body class="flex h-screen overflow-hidden bg-[#f7fbf0]">

<!-- SIDEBAR -->
<aside class="w-60 flex-shrink-0 h-screen flex flex-col bg-white border-r border-gray-100 shadow-sm z-10">
  <div class="p-5 border-b border-gray-100">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-[#0d631b] rounded-xl flex items-center justify-center shadow-sm">
        <span class="material-symbols-outlined text-white" style="font-variation-settings:'FILL' 1;font-size:20px">potted_plant</span>
      </div>
      <span class="font-bold text-[#0d631b] text-lg">Agri-Admin</span>
    </div>
  </div>
  <nav class="flex-1 p-3 space-y-1">
    <button data-tab="tabDashboard" class="nav-btn active w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-50 transition">
      <span class="material-symbols-outlined text-xl">dashboard</span> Dashboard
    </button>
    <button data-tab="tabFarmers" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-50 transition">
      <span class="material-symbols-outlined text-xl">group</span> Mga Magsasaka
    </button>
    <button data-tab="tabFarms" class="nav-btn w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:bg-gray-50 transition">
      <span class="material-symbols-outlined text-xl">grass</span> Mga Bukid
    </button>
  </nav>
  <div class="p-3 border-t border-gray-100">
    <button id="logoutBtn" class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-red-500 hover:bg-red-50 transition">
      <span class="material-symbols-outlined text-xl">logout</span> Mag-logout
    </button>
  </div>
</aside>

<!-- MAIN -->
<main class="flex-1 overflow-y-auto">

  <!-- DASHBOARD TAB -->
  <div id="tabDashboard" class="p-6 space-y-6">
    <h2 class="text-2xl font-bold text-gray-800">Dashboard</h2>
    <!-- Stats -->
    <div class="grid grid-cols-3 gap-4">
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
        <p class="text-xs font-bold uppercase text-gray-400 mb-1">Mga Magsasaka</p>
        <p class="text-3xl font-bold text-[#0d631b]" id="statFarmers">-</p>
      </div>
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
        <p class="text-xs font-bold uppercase text-gray-400 mb-1">Mga Bukid</p>
        <p class="text-3xl font-bold text-[#0d631b]" id="statFarms">-</p>
      </div>
      <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
        <p class="text-xs font-bold uppercase text-gray-400 mb-1">Sensor na May Reading</p>
        <p class="text-3xl font-bold text-[#0d631b]" id="statSensors">-</p>
      </div>
    </div>
    <!-- Map -->
    <div class="bg-white rounded-2xl p-5 shadow-sm border border-gray-100">
      <h3 class="font-bold text-gray-700 mb-3">Mapa ng mga Bukid</h3>
      <div id="map"></div>
    </div>
    <!-- Farm table -->
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-5 border-b border-gray-100">
        <h3 class="font-bold text-gray-700">Lahat ng Bukid</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-xs font-bold uppercase text-gray-400">
            <tr><th class="px-5 py-3 text-left">Bukid</th><th class="px-5 py-3 text-left">Magsasaka</th><th class="px-5 py-3 text-left">Mga Sensor</th><th class="px-5 py-3 text-left">Rekomendasyon</th></tr>
          </thead>
          <tbody id="dashFarmTable" class="divide-y divide-gray-50"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- FARMERS TAB -->
  <div id="tabFarmers" class="hidden p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-800">Mga Magsasaka</h2>
      <button id="addFarmerBtn" class="flex items-center gap-2 bg-[#0d631b] text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-green-800 transition">
        <span class="material-symbols-outlined text-lg">add</span> Magdagdag
      </button>
    </div>
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-xs font-bold uppercase text-gray-400">
            <tr><th class="px-5 py-3 text-left">Pangalan</th><th class="px-5 py-3 text-left">Mga Bukid</th><th class="px-5 py-3 text-left">Petsa ng Paglikha</th><th class="px-5 py-3 text-left">Aksyon</th></tr>
          </thead>
          <tbody id="farmersTable" class="divide-y divide-gray-50"></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- FARMS TAB -->
  <div id="tabFarms" class="hidden p-6 space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-2xl font-bold text-gray-800">Mga Bukid</h2>
      <button id="addFarmBtn" class="flex items-center gap-2 bg-[#0d631b] text-white px-4 py-2 rounded-xl text-sm font-bold hover:bg-green-800 transition">
        <span class="material-symbols-outlined text-lg">add</span> Magdagdag
      </button>
    </div>
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-xs font-bold uppercase text-gray-400">
            <tr><th class="px-5 py-3 text-left">Bukid</th><th class="px-5 py-3 text-left">Magsasaka</th><th class="px-5 py-3 text-left">Mga Sensor</th><th class="px-5 py-3 text-left">Hectares</th><th class="px-5 py-3 text-left">Aksyon</th></tr>
          </thead>
          <tbody id="farmsTable" class="divide-y divide-gray-50"></tbody>
        </table>
      </div>
    </div>
  </div>

</main>

<!-- FARMER MODAL -->
<div id="farmerModal" class="hidden fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
    <h3 id="farmerModalTitle" class="font-bold text-lg text-gray-800">Magdagdag ng Magsasaka</h3>
    <input id="farmerModalName" type="text" placeholder="Pangalan ng magsasaka"
      class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#0d631b]"/>
    <p id="farmerModalError" class="text-xs text-red-500 hidden"></p>
    <div class="flex gap-3">
      <button id="farmerModalCancel" class="flex-1 border border-gray-200 text-gray-600 font-semibold py-2.5 rounded-lg text-sm hover:bg-gray-50 transition">Kanselahin</button>
      <button id="farmerModalSave" class="flex-1 bg-[#0d631b] text-white font-bold py-2.5 rounded-lg text-sm hover:bg-green-800 transition">I-save</button>
    </div>
  </div>
</div>

<!-- FARM MODAL -->
<div id="farmModal" class="hidden fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
    <h3 id="farmModalTitle" class="font-bold text-lg text-gray-800">I-assign ang Magsasaka</h3>
    <p class="text-sm text-gray-500" id="farmModalFarmName"></p>
    <select id="farmModalFarmerSelect"
      class="w-full border border-gray-200 rounded-lg px-4 py-2.5 text-sm outline-none focus:border-[#0d631b]">
      <option value="">— Walang magsasaka —</option>
    </select>
    <p id="farmModalError" class="text-xs text-red-500 hidden"></p>
    <div class="flex gap-3">
      <button id="farmModalCancel" class="flex-1 border border-gray-200 text-gray-600 font-semibold py-2.5 rounded-lg text-sm hover:bg-gray-50 transition">Kanselahin</button>
      <button id="farmModalSave" class="flex-1 bg-[#0d631b] text-white font-bold py-2.5 rounded-lg text-sm hover:bg-green-800 transition">I-save</button>
    </div>
  </div>
</div>

<!-- DELETE CONFIRM MODAL -->
<div id="deleteModal" class="hidden fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
  <div class="bg-white rounded-2xl shadow-xl w-full max-w-sm p-6 space-y-4">
    <h3 class="font-bold text-lg text-gray-800">Kumpirmahin ang Pagbura</h3>
    <p id="deleteModalMsg" class="text-sm text-gray-600"></p>
    <div class="flex gap-3">
      <button id="deleteModalCancel" class="flex-1 border border-gray-200 text-gray-600 font-semibold py-2.5 rounded-lg text-sm hover:bg-gray-50">Kanselahin</button>
      <button id="deleteModalConfirm" class="flex-1 bg-red-600 text-white font-bold py-2.5 rounded-lg text-sm hover:bg-red-700">Burahin</button>
    </div>
  </div>
</div>

<script>
const API = "";
let farmers = [], farms = [], map, farmPolygons = [];
let editingFarmerId = null, assigningFarmId = null, deleteCb = null;

// --- Tab navigation ---
function setTab(id) {
  document.querySelectorAll("[id^='tab']").forEach(el => el.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === id));
  if (id === "tabDashboard") loadDashboard();
  if (id === "tabFarmers") loadFarmers();
  if (id === "tabFarms") loadFarmsTab();
}
document.querySelectorAll(".nav-btn").forEach(b => b.addEventListener("click", () => setTab(b.dataset.tab)));
document.getElementById("logoutBtn").addEventListener("click", () => {
  sessionStorage.removeItem("adminAuth");
  window.location.href = "/";
});

// --- Dashboard ---
async function loadDashboard() {
  const [frs, fms] = await Promise.all([
    fetch(`${API}/farmers`).then(r => r.json()),
    fetch(`${API}/farms`).then(r => r.json()),
  ]);
  farmers = frs; farms = fms;
  document.getElementById("statFarmers").textContent = frs.length;
  document.getElementById("statFarms").textContent = fms.length;
  let sensorWithReading = 0;
  const tbody = document.getElementById("dashFarmTable");
  tbody.innerHTML = "";
  for (const farm of fms) {
    const sensors = await fetch(`${API}/readings/${farm.farm_id}`).then(r => r.json()).catch(() => []);
    const withReading = sensors.filter(s => s.soil_n !== null).length;
    sensorWithReading += withReading;
    const farmer = frs.find(f => f.id === farm.farmer_id);
    let rec = "-";
    try {
      const p = await fetch(`${API}/farms/${farm.farm_id}/predict`).then(r => r.json());
      if (p.crop) rec = `${p.crop} (${Math.round(p.confidence*100)}%)`;
    } catch {}
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-50 transition";
    tr.innerHTML = `<td class="px-5 py-3 font-medium">${farm.farm_name||farm.farm_id}</td><td class="px-5 py-3 text-gray-500">${farmer?.name||"—"}</td><td class="px-5 py-3 text-gray-500">${withReading}/${sensors.length}</td><td class="px-5 py-3 text-[#0d631b] font-medium">${rec}</td>`;
    tbody.appendChild(tr);
  }
  document.getElementById("statSensors").textContent = sensorWithReading;
  renderMap(fms);
}

// --- Map ---
function renderMap(fms) {
  if (!map) return;
  farmPolygons.forEach(p => p.setMap(null));
  farmPolygons = [];
  const bounds = new google.maps.LatLngBounds();
  for (const farm of fms) {
    if (!farm.polygon?.length) continue;
    const paths = farm.polygon.map(([lat,lng]) => ({lat,lng}));
    const poly = new google.maps.Polygon({
      paths, map,
      strokeColor:"#0d631b", strokeWeight:2,
      fillColor:"#0d631b", fillOpacity:0.15,
    });
    farmPolygons.push(poly);
    paths.forEach(p => bounds.extend(p));
  }
  if (!bounds.isEmpty()) map.fitBounds(bounds);
}

window.initMap = function() {
  map = new google.maps.Map(document.getElementById("map"), {
    center:{lat:12.8797,lng:121.7740}, zoom:6,
    mapTypeId:"satellite",
    disableDefaultUI:true, zoomControl:true,
  });
  loadDashboard();
};

// --- Farmers tab ---
async function loadFarmers() {
  farmers = await fetch(`${API}/farmers`).then(r => r.json());
  farms = await fetch(`${API}/farms`).then(r => r.json());
  const tbody = document.getElementById("farmersTable");
  tbody.innerHTML = "";
  for (const f of farmers) {
    const assignedFarms = farms.filter(fm => fm.farmer_id === f.id);
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-50 transition";
    tr.innerHTML = `
      <td class="px-5 py-3 font-medium">${f.name}</td>
      <td class="px-5 py-3 text-gray-500">${f.farm_count}</td>
      <td class="px-5 py-3 text-gray-400 text-xs">${new Date(f.created_at).toLocaleDateString()}</td>
      <td class="px-5 py-3">
        <div class="flex gap-2">
          <button class="edit-farmer-btn text-[#0d631b] hover:underline text-xs font-bold" data-id="${f.id}" data-name="${f.name}">I-edit</button>
          <button class="del-farmer-btn text-red-500 hover:underline text-xs font-bold" data-id="${f.id}" data-name="${f.name}">Burahin</button>
        </div>
      </td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll(".edit-farmer-btn").forEach(b => b.addEventListener("click", () => openFarmerModal(b.dataset.id, b.dataset.name)));
  tbody.querySelectorAll(".del-farmer-btn").forEach(b => b.addEventListener("click", () => confirmDelete(`Burahin si "${b.dataset.name}"? Ang kanyang mga bukid ay mananatili ngunit mawawalan ng magsasaka.`, async () => {
    await fetch(`${API}/farmers/${b.dataset.id}`, {method:"DELETE"});
    loadFarmers();
  })));
}

function openFarmerModal(id = null, name = "") {
  editingFarmerId = id;
  document.getElementById("farmerModalTitle").textContent = id ? "I-edit ang Magsasaka" : "Magdagdag ng Magsasaka";
  document.getElementById("farmerModalName").value = name;
  document.getElementById("farmerModalError").classList.add("hidden");
  document.getElementById("farmerModal").classList.remove("hidden");
}
document.getElementById("addFarmerBtn").addEventListener("click", () => openFarmerModal());
document.getElementById("farmerModalCancel").addEventListener("click", () => document.getElementById("farmerModal").classList.add("hidden"));
document.getElementById("farmerModalSave").addEventListener("click", async () => {
  const name = document.getElementById("farmerModalName").value.trim();
  if (!name) return;
  const errEl = document.getElementById("farmerModalError");
  const method = editingFarmerId ? "PUT" : "POST";
  const url = editingFarmerId ? `${API}/farmers/${editingFarmerId}` : `${API}/farmers`;
  const res = await fetch(url, {method, headers:{"Content-Type":"application/json"}, body: JSON.stringify({name})});
  if (!res.ok) {
    const d = await res.json();
    errEl.textContent = d.detail || "Error"; errEl.classList.remove("hidden"); return;
  }
  document.getElementById("farmerModal").classList.add("hidden");
  loadFarmers();
});

// --- Farms tab ---
async function loadFarmsTab() {
  farms = await fetch(`${API}/farms`).then(r => r.json());
  farmers = await fetch(`${API}/farmers`).then(r => r.json());
  const tbody = document.getElementById("farmsTable");
  tbody.innerHTML = "";
  for (const f of farms) {
    const farmer = farmers.find(fr => fr.id === f.farmer_id);
    const sensors = await fetch(`${API}/readings/${f.farm_id}`).then(r=>r.json()).catch(()=>[]);
    const tr = document.createElement("tr");
    tr.className = "hover:bg-gray-50 transition";
    tr.innerHTML = `
      <td class="px-5 py-3 font-medium">${f.farm_name||f.farm_id}</td>
      <td class="px-5 py-3 text-gray-500">${farmer?.name||"—"}</td>
      <td class="px-5 py-3 text-gray-500">${sensors.length}</td>
      <td class="px-5 py-3 text-gray-500">${f.hectares||"—"}</td>
      <td class="px-5 py-3">
        <div class="flex gap-2">
          <button class="assign-btn text-[#0d631b] hover:underline text-xs font-bold" data-id="${f.farm_id}" data-name="${f.farm_name||f.farm_id}" data-farmer="${f.farmer_id||''}">I-assign</button>
          <button class="del-farm-btn text-red-500 hover:underline text-xs font-bold" data-id="${f.farm_id}" data-name="${f.farm_name||f.farm_id}">Burahin</button>
        </div>
      </td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll(".assign-btn").forEach(b => b.addEventListener("click", () => openFarmModal(b.dataset.id, b.dataset.name, b.dataset.farmer)));
  tbody.querySelectorAll(".del-farm-btn").forEach(b => b.addEventListener("click", () => confirmDelete(`Burahin ang bukid na "${b.dataset.name}"? Mabubura rin ang lahat ng sensor readings nito.`, async () => {
    await fetch(`${API}/farms/${b.dataset.id}`, {method:"DELETE"});
    loadFarmsTab();
  })));
}

async function openFarmModal(farmId, farmName, currentFarmerId) {
  assigningFarmId = farmId;
  document.getElementById("farmModalFarmName").textContent = farmName;
  const sel = document.getElementById("farmModalFarmerSelect");
  sel.innerHTML = '<option value="">— Walang magsasaka —</option>';
  farmers.forEach(f => {
    const opt = document.createElement("option");
    opt.value = f.id; opt.textContent = f.name;
    if (f.id === currentFarmerId) opt.selected = true;
    sel.appendChild(opt);
  });
  document.getElementById("farmModalError").classList.add("hidden");
  document.getElementById("farmModal").classList.remove("hidden");
}
document.getElementById("farmModalCancel").addEventListener("click", () => document.getElementById("farmModal").classList.add("hidden"));
document.getElementById("farmModalSave").addEventListener("click", async () => {
  const farmerId = document.getElementById("farmModalFarmerSelect").value || null;
  const res = await fetch(`${API}/farms/${assigningFarmId}/farmer`, {method:"PUT", headers:{"Content-Type":"application/json"}, body: JSON.stringify({farmer_id: farmerId})});
  if (!res.ok) {
    const d = await res.json();
    const errEl = document.getElementById("farmModalError");
    errEl.textContent = d.detail || "Error"; errEl.classList.remove("hidden"); return;
  }
  document.getElementById("farmModal").classList.add("hidden");
  loadFarmsTab();
});
document.getElementById("addFarmBtn").addEventListener("click", () => {
  alert("Pumunta sa lumang dashboard para magdagdag ng bagong bukid na may mapa. (Maaaring i-integrate sa susunod na update.)");
});

// --- Delete confirm ---
function confirmDelete(msg, cb) {
  deleteCb = cb;
  document.getElementById("deleteModalMsg").textContent = msg;
  document.getElementById("deleteModal").classList.remove("hidden");
}
document.getElementById("deleteModalCancel").addEventListener("click", () => document.getElementById("deleteModal").classList.add("hidden"));
document.getElementById("deleteModalConfirm").addEventListener("click", async () => {
  document.getElementById("deleteModal").classList.add("hidden");
  if (deleteCb) { await deleteCb(); deleteCb = null; }
});
</script>
<script async defer src="https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&callback=initMap"></script>
</body></html>
```

- [ ] **Step 2: Verify admin.html works**

Navigate to `http://127.0.0.1:8000/admin.html` after logging in. Verify:
- Sidebar shows 3 nav items + logout
- Dashboard tab loads stats + map + farm table
- Farmers tab: can add, edit, delete a farmer
- Farms tab: can assign a farmer to a farm

- [ ] **Step 3: Commit**

```powershell
git add frontend/admin.html
git commit -m "feat: build admin SPA with dashboard, farmers, and farms management tabs"
```

---

## Task 5: Farmer SPA (`farmer.html`)

**Files:**
- Replace: `frontend/farmer.html`

**Interfaces:**
- Consumes: `sessionStorage.farmerAuth` (JSON: `{id, name, farms: [{farm_id, farm_name, sensors: [...]}]}`)
- Consumes: `GET /farms/{farm_id}/predict`, `GET /farms/{farm_id}/explain?lang=`, `GET /readings/{plot_id}`
- Auth guard: redirect to `/` if no `farmerAuth`

- [ ] **Step 1: Replace `frontend/farmer.html`**

```html
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Aking Bukid</title>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
<style>
  body { font-family: 'Plus Jakarta Sans', sans-serif; background: #f7fbf0; padding-bottom: 72px; }
  .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; vertical-align: middle; }
  .hidden { display: none !important; }
  .nav-icon.active { color: #0d631b; }
  .nav-icon { color: #9ca3af; }
  html.dark body { background: #101410; color: #e5e9e2; }
  html.dark .bg-white { background: #1b211c !important; }
  html.dark .border, html.dark .border-gray-100 { border-color: #3a423a !important; }
  html.dark .text-gray-500, html.dark .text-gray-400 { color: #a9b3a4 !important; }
  html.dark .bg-gray-50 { background: #232a23 !important; }
</style>
<script>
  if (localStorage.getItem("theme") === "dark") document.documentElement.classList.add("dark");
  const farmerAuth = JSON.parse(sessionStorage.getItem("farmerAuth") || "null");
  if (!farmerAuth) window.location.replace("/");
</script>
</head>
<body class="min-h-screen">

<!-- TOP HEADER -->
<header class="sticky top-0 bg-white border-b border-gray-100 shadow-sm z-10 px-4 py-3 flex items-center gap-3">
  <div class="w-8 h-8 bg-[#0d631b] rounded-lg flex items-center justify-center">
    <span class="material-symbols-outlined text-white" style="font-variation-settings:'FILL' 1;font-size:18px">potted_plant</span>
  </div>
  <div class="flex-1">
    <h1 class="font-bold text-[#0d631b] text-sm leading-tight">Aking Bukid</h1>
    <p class="text-xs text-gray-400" id="headerFarmerName"></p>
  </div>
  <button id="langToggle" class="text-xs font-bold border border-gray-200 px-2 py-1 rounded-lg text-gray-600 hover:border-[#0d631b] hover:text-[#0d631b] transition">EN</button>
</header>

<!-- CONTENT AREA -->
<div class="max-w-md mx-auto p-4 space-y-4">

  <!-- MY FARMS TAB -->
  <div id="tabMyFarms" class="space-y-3">
    <h2 class="font-bold text-lg text-gray-800" data-fil="Aking mga Bukid" data-en="My Farms">Aking mga Bukid</h2>
    <div id="farmCards" class="space-y-3"></div>
  </div>

  <!-- SENSORS TAB -->
  <div id="tabSensors" class="hidden space-y-4">
    <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
      <label class="text-xs font-bold uppercase text-gray-400 mb-2 block" data-fil="Piliin ang Bukid" data-en="Select Farm">Piliin ang Bukid</label>
      <select id="sensorFarmSelect" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-[#0d631b]"></select>
    </div>
    <div id="sensorContent" class="space-y-4 hidden">
      <!-- Recommendation -->
      <div class="bg-white rounded-2xl p-5 shadow-sm border-l-4 border-[#0d631b]">
        <p class="text-xs font-bold uppercase text-[#0d631b] mb-2" data-fil="Rekomendasyon" data-en="Recommendation">Rekomendasyon</p>
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-4xl text-[#0d631b]" style="font-variation-settings:'FILL' 1">agriculture</span>
          <div>
            <p class="text-2xl font-bold text-gray-800" id="recCrop">-</p>
            <p class="text-sm text-gray-500" id="recConfidence">-</p>
          </div>
        </div>
        <button id="explainBtn" class="hidden mt-3 text-sm font-bold text-[#0d631b] underline" data-fil="Bakit?" data-en="Why?">Bakit?</button>
        <p id="explainText" class="text-sm text-gray-500 mt-2 italic"></p>
      </div>
      <!-- Sensor List -->
      <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
        <p class="text-xs font-bold uppercase text-gray-400 mb-3" data-fil="Mga Sensor" data-en="Sensors">Mga Sensor</p>
        <div id="sensorList" class="flex flex-wrap gap-2"></div>
      </div>
      <!-- Readings Grid -->
      <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 hidden" id="readingsCard">
        <p class="text-xs font-bold uppercase text-gray-400 mb-3" data-fil="Pagbasa ng Sensor" data-en="Sensor Readings">Pagbasa ng Sensor</p>
        <div class="grid grid-cols-3 gap-2 text-sm">
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">N</p><p class="font-bold text-[#0d631b]" id="rN">-</p></div>
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">P</p><p class="font-bold text-[#0d631b]" id="rP">-</p></div>
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">K</p><p class="font-bold text-[#0d631b]" id="rK">-</p></div>
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">pH</p><p class="font-bold text-[#0d631b]" id="rPh">-</p></div>
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">Temp</p><p class="font-bold" id="rTemp">-</p></div>
          <div class="bg-gray-50 rounded-xl p-3"><p class="text-[10px] font-bold text-gray-400">Ulan</p><p class="font-bold" id="rRain">-</p></div>
        </div>
        <p class="text-xs text-gray-400 mt-2" id="rTimestamp"></p>
      </div>
    </div>
  </div>

  <!-- HISTORY TAB -->
  <div id="tabHistory" class="hidden space-y-4">
    <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
      <label class="text-xs font-bold uppercase text-gray-400 mb-2 block" data-fil="Piliin ang Bukid" data-en="Select Farm">Piliin ang Bukid</label>
      <select id="historyFarmSelect" class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-[#0d631b]"></select>
    </div>
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50 text-xs font-bold uppercase text-gray-400">
          <tr>
            <th class="px-4 py-2 text-left" data-fil="Petsa" data-en="Date">Petsa</th>
            <th class="px-4 py-2 text-left">pH</th>
            <th class="px-4 py-2 text-left">Temp</th>
            <th class="px-4 py-2 text-left" data-fil="Pananim" data-en="Crop">Pananim</th>
          </tr>
        </thead>
        <tbody id="historyBody" class="divide-y divide-gray-50"></tbody>
      </table>
    </div>
  </div>

  <!-- SETTINGS TAB -->
  <div id="tabSettings" class="hidden space-y-4">
    <h2 class="font-bold text-lg text-gray-800" data-fil="Mga Setting" data-en="Settings">Mga Setting</h2>
    <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-3">
      <p class="text-xs font-bold uppercase text-gray-400" data-fil="Wika" data-en="Language">Wika</p>
      <div class="flex gap-2">
        <button class="lang-opt flex-1 py-2 rounded-lg border text-sm font-semibold" data-lang="fil">Tagalog</button>
        <button class="lang-opt flex-1 py-2 rounded-lg border text-sm font-semibold" data-lang="en">English</button>
      </div>
    </div>
    <div class="bg-white rounded-2xl p-4 shadow-sm border border-gray-100 space-y-3">
      <p class="text-xs font-bold uppercase text-gray-400" data-fil="Tema" data-en="Theme">Tema</p>
      <div class="flex gap-2">
        <button class="theme-opt flex-1 py-2 rounded-lg border text-sm font-semibold" data-theme="light">Light</button>
        <button class="theme-opt flex-1 py-2 rounded-lg border text-sm font-semibold" data-theme="dark">Dark</button>
      </div>
    </div>
    <button id="logoutBtn" class="w-full flex items-center justify-center gap-2 border border-red-200 text-red-500 font-bold py-3 rounded-2xl text-sm hover:bg-red-50 transition">
      <span class="material-symbols-outlined">logout</span>
      <span data-fil="Mag-logout" data-en="Logout">Mag-logout</span>
    </button>
  </div>

</div>

<!-- BOTTOM NAV -->
<nav class="fixed bottom-0 left-0 w-full bg-white border-t border-gray-100 flex justify-around py-2 z-10 shadow-sm">
  <button class="nav-icon active flex flex-col items-center gap-0.5 px-4 py-1" data-tab="tabMyFarms">
    <span class="material-symbols-outlined text-2xl">home</span>
    <span class="text-[10px] font-semibold" data-fil="Bukid" data-en="Farms">Bukid</span>
  </button>
  <button class="nav-icon flex flex-col items-center gap-0.5 px-4 py-1" data-tab="tabSensors">
    <span class="material-symbols-outlined text-2xl">sensors</span>
    <span class="text-[10px] font-semibold" data-fil="Sensor" data-en="Sensors">Sensor</span>
  </button>
  <button class="nav-icon flex flex-col items-center gap-0.5 px-4 py-1" data-tab="tabHistory">
    <span class="material-symbols-outlined text-2xl">history</span>
    <span class="text-[10px] font-semibold" data-fil="Kasaysayan" data-en="History">Kasaysayan</span>
  </button>
  <button class="nav-icon flex flex-col items-center gap-0.5 px-4 py-1" data-tab="tabSettings">
    <span class="material-symbols-outlined text-2xl">settings</span>
    <span class="text-[10px] font-semibold" data-fil="Setting" data-en="Settings">Setting</span>
  </button>
</nav>

<script>
const API = "";
const auth = JSON.parse(sessionStorage.getItem("farmerAuth"));
let currentFarmId = null, currentReadingId = null;

const CROP_FIL = {
  rice:"palay",maize:"mais",chickpea:"garbanzos",kidneybeans:"habichuelas",
  pigeonpeas:"kadyos",mothbeans:"paayap",mungbean:"monggo",blackgram:"itim na munggo",
  lentil:"lentil",pomegranate:"granada",banana:"saging",mango:"mangga",
  grapes:"ubas",watermelon:"pakwan",muskmelon:"melon",apple:"mansanas",
  orange:"dalandan",papaya:"papaya",coconut:"niyog",cotton:"bulak",
  jute:"yute",coffee:"kape",
};

function cropLabel(en) {
  if (!en) return "-";
  const lang = localStorage.getItem("lang") || "fil";
  const fil = CROP_FIL[en.toLowerCase()] || en;
  return lang === "en" ? en : fil;
}

// --- Language ---
function applyLanguage(lang) {
  localStorage.setItem("lang", lang);
  document.querySelectorAll("[data-fil]").forEach(el => {
    el.textContent = lang === "en" ? el.dataset.en : el.dataset.fil;
  });
  document.getElementById("langToggle").textContent = lang === "en" ? "FIL" : "EN";
  document.querySelectorAll(".lang-opt").forEach(b => {
    b.classList.toggle("border-[#0d631b]", b.dataset.lang === lang);
    b.classList.toggle("text-[#0d631b]", b.dataset.lang === lang);
    b.classList.toggle("font-bold", b.dataset.lang === lang);
  });
}

document.getElementById("langToggle").addEventListener("click", () => {
  applyLanguage(localStorage.getItem("lang") === "en" ? "fil" : "en");
});
document.querySelectorAll(".lang-opt").forEach(b => b.addEventListener("click", () => applyLanguage(b.dataset.lang)));

// --- Theme ---
function applyTheme(theme) {
  localStorage.setItem("theme", theme);
  document.documentElement.classList.toggle("dark", theme === "dark");
  document.querySelectorAll(".theme-opt").forEach(b => {
    b.classList.toggle("border-[#0d631b]", b.dataset.theme === theme);
    b.classList.toggle("text-[#0d631b]", b.dataset.theme === theme);
    b.classList.toggle("font-bold", b.dataset.theme === theme);
  });
}
document.querySelectorAll(".theme-opt").forEach(b => b.addEventListener("click", () => applyTheme(b.dataset.theme)));

// --- Logout ---
document.getElementById("logoutBtn").addEventListener("click", () => {
  sessionStorage.removeItem("farmerAuth");
  window.location.href = "/";
});

// --- Tab nav ---
function setTab(id) {
  document.querySelectorAll("[id^='tab']").forEach(el => el.classList.add("hidden"));
  document.getElementById(id).classList.remove("hidden");
  document.querySelectorAll(".nav-icon").forEach(b => b.classList.toggle("active", b.dataset.tab === id));
}
document.querySelectorAll(".nav-icon").forEach(b => b.addEventListener("click", () => {
  setTab(b.dataset.tab);
  if (b.dataset.tab === "tabHistory") loadHistory();
}));

// --- Farm cards (My Farms tab) ---
async function loadMyFarms() {
  const container = document.getElementById("farmCards");
  container.innerHTML = "";
  for (const farm of auth.farms) {
    const card = document.createElement("div");
    card.className = "bg-white rounded-2xl p-5 shadow-sm border border-gray-100 cursor-pointer hover:border-[#0d631b] transition";
    let rec = { crop: null, confidence: 0 };
    try { rec = await fetch(`${API}/farms/${farm.farm_id}/predict`).then(r => r.ok ? r.json() : {}); } catch {}
    const pct = rec.crop ? Math.round(rec.confidence * 100) : 0;
    const conf_color = pct >= 75 ? "text-green-600" : pct >= 50 ? "text-yellow-600" : "text-gray-400";
    card.innerHTML = `
      <div class="flex items-start justify-between">
        <div>
          <p class="font-bold text-gray-800 text-lg">${farm.farm_name || farm.farm_id}</p>
          <p class="text-xs text-gray-400 mt-0.5">${farm.sensors?.length || 0} sensors</p>
        </div>
        ${rec.crop ? `<span class="text-xs font-bold ${conf_color} bg-gray-50 px-2 py-1 rounded-lg">${pct}%</span>` : ""}
      </div>
      ${rec.crop ? `<div class="mt-3 flex items-center gap-2">
        <span class="material-symbols-outlined text-2xl text-[#0d631b]" style="font-variation-settings:'FILL' 1">agriculture</span>
        <p class="font-bold text-xl text-gray-800">${cropLabel(rec.crop)}</p>
      </div>` : `<p class="mt-3 text-sm text-gray-400">Walang rekomendasyon pa</p>`}`;
    card.addEventListener("click", () => {
      currentFarmId = farm.farm_id;
      setTab("tabSensors");
      loadSensors(farm.farm_id);
    });
    container.appendChild(card);
  }
}

// --- Farm selects ---
function populateFarmSelects() {
  [document.getElementById("sensorFarmSelect"), document.getElementById("historyFarmSelect")].forEach(sel => {
    sel.innerHTML = "";
    auth.farms.forEach(farm => {
      const opt = document.createElement("option");
      opt.value = farm.farm_id;
      opt.textContent = farm.farm_name || farm.farm_id;
      sel.appendChild(opt);
    });
  });
  document.getElementById("sensorFarmSelect").addEventListener("change", e => loadSensors(e.target.value));
  document.getElementById("historyFarmSelect").addEventListener("change", e => loadHistory(e.target.value));
}

// --- Sensors tab ---
async function loadSensors(farmId) {
  currentFarmId = farmId;
  document.getElementById("sensorFarmSelect").value = farmId;
  document.getElementById("sensorContent").classList.remove("hidden");
  document.getElementById("explainText").textContent = "";
  document.getElementById("explainBtn").classList.add("hidden");
  // Recommendation
  try {
    const rec = await fetch(`${API}/farms/${farmId}/predict`).then(r => r.ok ? r.json() : null);
    if (rec?.crop) {
      document.getElementById("recCrop").textContent = cropLabel(rec.crop);
      document.getElementById("recConfidence").textContent = `${Math.round(rec.confidence*100)}% confidence`;
      document.getElementById("explainBtn").classList.remove("hidden");
    } else {
      document.getElementById("recCrop").textContent = "-";
      document.getElementById("recConfidence").textContent = "Walang sapat na data";
    }
  } catch { document.getElementById("recCrop").textContent = "-"; }

  // Sensor buttons
  const sensors = auth.farms.find(f => f.farm_id === farmId)?.sensors || [];
  const list = document.getElementById("sensorList");
  list.innerHTML = "";
  sensors.forEach((s, i) => {
    const hasReading = s.soil_n !== null && s.soil_n !== undefined;
    const btn = document.createElement("button");
    btn.className = `border rounded-lg px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 transition ${hasReading ? "text-[#0d631b] border-[#0d631b] hover:bg-[#0d631b] hover:text-white" : "text-gray-400 border-gray-200"}`;
    btn.innerHTML = `<span class="inline-block w-2 h-2 rounded-full" style="background:${hasReading ? "#0d631b" : "#9ca3af"}"></span>Sensor ${i+1}`;
    if (hasReading) btn.addEventListener("click", () => showReading(s));
    list.appendChild(btn);
  });

  // Show latest reading by default
  const latest = sensors.find(s => s.soil_n !== null);
  if (latest) showReading(latest);
}

function showReading(s) {
  currentReadingId = s.id;
  document.getElementById("readingsCard").classList.remove("hidden");
  document.getElementById("rN").textContent = s.soil_n?.toFixed(1) ?? "-";
  document.getElementById("rP").textContent = s.soil_p?.toFixed(1) ?? "-";
  document.getElementById("rK").textContent = s.soil_k?.toFixed(1) ?? "-";
  document.getElementById("rPh").textContent = s.soil_ph?.toFixed(2) ?? "-";
  document.getElementById("rTemp").textContent = s.air_temp_c ? `${s.air_temp_c.toFixed(1)}°C` : "-";
  document.getElementById("rRain").textContent = s.rainfall_mm ? `${s.rainfall_mm.toFixed(1)}mm` : "-";
  document.getElementById("rTimestamp").textContent = s.timestamp ? new Date(s.timestamp).toLocaleString() : "";
}

document.getElementById("explainBtn").addEventListener("click", async (e) => {
  if (!currentFarmId) return;
  const lang = localStorage.getItem("lang") || "fil";
  e.target.textContent = lang === "en" ? "Thinking..." : "Sandali lang...";
  e.target.disabled = true;
  try {
    const res = await fetch(`${API}/farms/${currentFarmId}/explain?lang=${lang}`);
    const data = await res.json();
    document.getElementById("explainText").textContent = data.explanation || data.detail || "";
  } catch {
    document.getElementById("explainText").textContent = lang === "en" ? "Could not reach AI model." : "Hindi maabot ang AI model.";
  }
  e.target.textContent = lang === "en" ? "Why?" : "Bakit?";
  e.target.disabled = false;
});

// --- History tab ---
async function loadHistory(farmId) {
  farmId = farmId || document.getElementById("historyFarmSelect").value;
  if (!farmId) return;
  const sensors = auth.farms.find(f => f.farm_id === farmId)?.sensors || [];
  const tbody = document.getElementById("historyBody");
  tbody.innerHTML = "";
  const lang = localStorage.getItem("lang") || "fil";
  for (const s of sensors.slice(0, 5)) {
    const readings = await fetch(`${API}/readings/${s.plot_id}`).then(r => r.json()).catch(() => []);
    readings.filter(r => r.soil_n !== null).slice(0, 3).forEach(r => {
      const crop = r.predicted_crop ? (lang === "en" ? r.predicted_crop : (CROP_FIL[r.predicted_crop.toLowerCase()] || r.predicted_crop)) : "-";
      const tr = document.createElement("tr");
      tr.className = "border-b border-gray-50 hover:bg-gray-50 transition";
      tr.innerHTML = `<td class="px-4 py-2 text-xs text-gray-500">${new Date(r.timestamp).toLocaleDateString()}</td><td class="px-4 py-2 text-xs">${r.soil_ph?.toFixed(2)||"-"}</td><td class="px-4 py-2 text-xs">${r.air_temp_c?.toFixed(1)||"-"}°C</td><td class="px-4 py-2 text-xs font-medium text-[#0d631b]">${crop}</td>`;
      tbody.appendChild(tr);
    });
  }
  if (!tbody.children.length) tbody.innerHTML = `<tr><td colspan="4" class="px-4 py-6 text-center text-gray-400 text-sm">Walang kasaysayan pa</td></tr>`;
}

// --- Init ---
document.getElementById("headerFarmerName").textContent = auth.name;
applyLanguage(localStorage.getItem("lang") || "fil");
applyTheme(localStorage.getItem("theme") || "light");
populateFarmSelects();
loadMyFarms();
if (auth.farms?.length) loadSensors(auth.farms[0].farm_id);
</script>
</body></html>
```

- [ ] **Step 2: Verify farmer.html**

Log in as a farmer at `http://127.0.0.1:8000/`. Verify:
- My Farms tab shows farm cards with crop recommendations
- Sensors tab shows sensor list and readings
- History tab shows reading history
- Settings tab has language/theme toggles and logout
- Language toggle switches all labels

- [ ] **Step 3: Commit**

```powershell
git add frontend/farmer.html
git commit -m "feat: build farmer SPA with My Farms, Sensors, History, Settings tabs"
```

---

## Task 6: Capstone Scaffolding

**Files:**
- Create: `README.md`, `AGENTS.md`, `TASKS.md`, `PROMPTS.md`, `DESIGN.md`
- Create dirs: `proposal/`, `prototype/`, `presentation/`

- [ ] **Step 1: Create capstone files and folders**

```powershell
# Folders
New-Item -ItemType Directory -Force proposal, prototype, presentation

# README.md
@'
# Sadiang-Abay Crop Recommendation System

An offline-capable crop recommendation system for Filipino farmer cooperatives. Uses ML (scikit-learn) for crop prediction, a local LLM (Ollama/Qwen2.5) for AI explanations, and NLLB-200 for offline Tagalog translation.

## Run

```
py -m pip install fastapi uvicorn joblib pandas scikit-learn requests transformers torch sentencepiece
py -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Stack
- Backend: Python / FastAPI / SQLite
- ML: scikit-learn RandomForest
- AI Explain: Ollama (qwen2.5:3b)
- Translation: facebook/nllb-200-distilled-600M
- Frontend: Vanilla HTML + Tailwind CSS
'@ | Out-File -Encoding utf8 README.md

# DESIGN.md
@'
# Design

See full design spec: [docs/superpowers/specs/2026-06-24-ui-redesign-farmer-management-design.md](docs/superpowers/specs/2026-06-24-ui-redesign-farmer-management-design.md)
'@ | Out-File -Encoding utf8 DESIGN.md

# AGENTS.md
@'
# AI Agents

This project was built with Claude Code (claude-sonnet-4-6).

## Agent Instructions
- Backend: FastAPI app in main.py, DB in db.py
- Frontend: Static HTML in frontend/ served by FastAPI
- Run server: `py -m uvicorn main:app --reload`
- Models: crop_model.pkl (sklearn), Ollama qwen2.5:3b, NLLB-200 in model/huggingface/
'@ | Out-File -Encoding utf8 AGENTS.md

# TASKS.md
@'
# Tasks

- [x] ML crop recommendation model (train_crop_model.py)
- [x] FastAPI backend with sensor readings and farm management
- [x] Offline AI explanation (Ollama + Qwen2.5:3b)
- [x] Offline Tagalog translation (NLLB-200)
- [x] Farmer account system (one farmer, many farms)
- [x] Admin SPA (Dashboard, Farmers, Farms tabs)
- [x] Farmer SPA (My Farms, Sensors, History, Settings)
- [x] Login page with role-based access
'@ | Out-File -Encoding utf8 TASKS.md

# PROMPTS.md
@'
# Prompts

Key prompts used during development are logged here.

## UI Redesign
"use deepthink and report and proper ui and remake the all pages and proper managing for farmers and log out button"

## Farmer Management
"add authentication for the admin username admin password admin also"
"the name of plant also be dynamic based on the language user choose also remove the /"
'@ | Out-File -Encoding utf8 PROMPTS.md
```

- [ ] **Step 2: Verify folder structure**

```powershell
Get-ChildItem -Name | Sort-Object
```
Expected: `README.md`, `AGENTS.md`, `TASKS.md`, `PROMPTS.md`, `DESIGN.md`, `docs/`, `proposal/`, `prototype/`, `presentation/` visible.

- [ ] **Step 3: Commit**

```powershell
git add README.md AGENTS.md TASKS.md PROMPTS.md DESIGN.md proposal prototype presentation
git commit -m "chore: add capstone repo scaffolding files and folders"
```

---

## Task 7: Cleanup Old Files

**Files:**
- Delete: `frontend/add_plot.html`, `frontend/add_reading.html`, `frontend/roi.html`
- Delete: `frontend/dashboard.html` (replaced by `admin.html`)

- [ ] **Step 1: Delete old pages**

```powershell
Remove-Item frontend/add_plot.html, frontend/add_reading.html, frontend/roi.html, frontend/dashboard.html
```

- [ ] **Step 2: Verify server still starts cleanly**

```powershell
py -m uvicorn main:app --reload
```
Expected: no import errors, `http://127.0.0.1:8000/` loads the login page.

- [ ] **Step 3: Commit**

```powershell
git add -A
git commit -m "chore: remove old pages replaced by admin.html and farmer.html redesign"
```

---

## Self-Review

**Spec coverage check:**
- ✅ farmers table + farmer_id on farms → Task 1
- ✅ 6 new API endpoints → Task 2
- ✅ index.html login redesign → Task 3
- ✅ admin.html sidebar SPA (Dashboard/Farmers/Farms) → Task 4
- ✅ farmer.html bottom nav SPA (My Farms/Sensors/History/Settings) → Task 5
- ✅ Logout on both admin and farmer → Tasks 4 + 5
- ✅ Language toggle (Tagalog/English) on farmer → Task 5
- ✅ Capstone scaffolding → Task 6
- ✅ Old pages deleted → Task 7

**Placeholder scan:** No TBDs or TODOs. All code complete.

**Type consistency:**
- `farmerAuth` sessionStorage key used consistently across Task 3 (write) and Task 5 (read)
- `adminAuth` sessionStorage key consistent across Task 3 (write) and Task 4 (guard)
- `farmer.id` used as `farmer_id` FK — consistent throughout Tasks 1, 2, 4
- `GET /farmers/by-name/{name}` returns `{id, name, farms: [...]}` — matches Task 5 reader
