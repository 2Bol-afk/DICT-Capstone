# Task 4 Fix Report — admin.html Security & Staleness Fixes

## Fix 1: XSS in Farmers Table onclick (DONE)

**Location:** `loadFarmers()` function, tbody rendering loop

**What changed:** Replaced `tbody.innerHTML = farmers.map(f => ...).join("")` with a `forEach` loop that:
- Creates each `<tr>` with `document.createElement("tr")`
- Uses class names `.edit-farmer-btn` / `.del-farmer-btn` instead of inline `onclick`
- Attaches event listeners **after** appending via `addEventListener`, capturing farmer data in closures

Names like `O'Brien` or names containing quotes no longer break JS string literals in HTML attributes.

## Fix 2: XSS in Farms Table onclick (DONE)

**Location:** `loadFarmsTab()` function, farms rows rendering

**What changed:** Replaced the `Promise.all(farms.map(...))` that returned HTML strings with a two-step approach:
1. First `Promise.all` fetches sensor counts only (pure data)
2. `forEach` loop builds DOM elements using `createElement`, uses class names `.assign-farm-btn` / `.del-farm-btn`, and wires up listeners via `addEventListener` using closures

Farm names and IDs (which could contain quotes or special characters) no longer appear in `onclick` attribute strings.

## Fix 3: Stale dashboard.html Reference (DONE)

**Location:** `addFarmBtn` click handler (Farms tab)

**What changed:** Replaced the `alert()` mentioning `dashboard.html` with:
```js
addFarmBtnEl.disabled = true;
addFarmBtnEl.title = "Hindi available — gamitin ang API o simulation program";
addFarmBtnEl.classList.add("opacity-50", "cursor-not-allowed");
```
Button is visually disabled with a tooltip. No alert, no dead reference to `dashboard.html`.

## Fix 4 (Bonus): config.js Moved to `<head>` (DONE)

**Location:** `<head>` section

**What changed:** `<script src="config.js"></script>` moved from just before the main `<script>` block at end of body into `<head>` (right after the auth guard, before Tailwind). The duplicate tag at the bottom was removed.

This ensures `GOOGLE_MAPS_API_KEY` is defined before any inline script references it.

## Verification

All four changes are confirmed correct:
- No `onclick` attributes remain in the farmers or farms tbody rendering code
- No reference to `dashboard.html` remains in any alert or JS string
- `config.js` appears exactly once, in `<head>`
- Farmer/farm data is passed via closures, not string interpolation into HTML attributes
