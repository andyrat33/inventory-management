# Implementation: Low-Stock Alerts

**Mode**: default | **Date**: 2026-09-08 | **Status**: Complete
**Branch**: `feat/low-stock-alerts` (off `origin/main`) | **Commit**: `309bd79`

## 1. Changes (9 files, +609 −6)

**Created**

- `server/main.py` `GET /api/inventory/low-stock` (+`_stock_severity`, `LowStockAlert` model) — items with `quantity_on_hand <= reorder_point`, each tagged `severity` `"critical"` (qty 0 or `qty*2 <= reorder_point`) / `"low"`; sorted critical-first then by deficit; `warehouse`/`category` filters. **Declared before `/api/inventory/{item_id}`** so `low-stock` isn't parsed as an id.
- `client/src/components/AlertsBell.vue` — bell trigger + count badge + upward dropdown; fetches on mount, every 60s, and on open; rows show severity dot / SKU / name / `qty / reorder` / warehouse / Low·Critical pill; row → `/inventory?item=<sku>`, footer → `/inventory`.
- `tests/backend/test_low_stock.py` — 12 tests (endpoint shape, severity rule, sort, route-collision, filters; a fixture injects critical items since seed data has none).

**Modified**

- `client/src/App.vue` — mount `<AlertsBell>` first in `.sidebar-footer`.
- `client/src/views/Inventory.vue` — `useRoute()`; after load + on `route.query.item` change, open the matching item's detail modal.
- `client/src/api.js` — `getLowStockAlerts(filters)`.
- `client/src/locales/{en,ja}.js` — `alerts.*` block.
- `client/src/composables/useFilters.js` — `prettier --write` (CI `format:check` parity; non-functional).

## 2. Quality (Tests: 98 pass, +12 | Build: clean | Docs: EPCC only)

- **Backend**: `pytest tests/backend` → 98 passed. New file covers happy path, the tiered-severity rule (incl. injected critical items), critical-first sort, the `{item_id}` route-collision, and both filters.
- **Frontend**: `vite build` clean (125 modules); `prettier --check` clean. No frontend test suite.
- **E2E (Playwright)**: bell badge shows `4`; dropdown lists the 4 low items; keyboard open → focus first row → Escape → focus returns to trigger; clicking a row lands on `/inventory?item=SRV-301` with the detail modal open; JP locale translates the panel. Console clean.

## 3. Decisions

- **Bell in the sidebar footer** (not a dedicated page) — matches the app's existing dropdown pattern (`LanguageSwitcher`/`ProfileMenu`); `AlertsBell.vue` is a near-clone of `LanguageSwitcher.vue` for consistent a11y.
- **Severity computed server-side** on the alert response, not stored — mock data has no persistence; keeps the client dumb.
- **No `critical` items in seed data** — the tier is fully wired (dot colour, `.badge.danger`, `alerts.severity.critical`) and unit-tested via an injected-item fixture, but not visually exercised. Lowering a seed item to demo it would be data fudging; left as-is.
- **Deep-link via `?item=<sku>`** rather than a new route — reuses `Inventory.vue`'s existing `showItemDetail`.

## 4. Handoff

**Run**: `/epcc-commit` (branch pushed + PR next).
**Blockers**: None.
**TODOs**:

- Base is `origin/main`; CI (`ci-workflow`, PR #5) and the Reports fix (`reports-fix`, PR #6) are still open — merge order doesn't matter for this branch but rebasing after they land is tidy.
- If a `critical` example is wanted in the demo, adjust one row in `server/data/inventory.json`.
