# Inventory-Management App — Prioritized Action Plan

**Date:** 2026-09-07
**Team:** security-auditor · perf-analyst · ux-reviewer (parallel audit + cross-challenge)
**Source docs:** `audit/security-findings.md` (SEC-1..10), `audit/perf-findings.md` (PERF-1..15), `audit/ux-findings.md` (UX-1..30) and the three `*-challenges.md` files.

## How to read this

- **P0** – broken functionality or unsafe defaults; fix before the next demo/deploy.
- **P1** – high impact; this sprint.
- **P2** – real problems; schedule.
- **P3** – polish, hygiene, and scale-only issues (no measurable impact at current data volume: 250 orders / 32 items).

Findings that three lenses traced to **one root cause are merged into a single work item** (see the merge map in each `*-challenges.md`). Severity is the cross-challenged consensus, not any single auditor's first rating.

---

## P0 — Fix now

### P0-1 · Dead "Create PO" / "View PO" buttons on the dashboard

**Severity: Critical** · UX-1 (+ perf note, + security note on the API client)
`client/src/views/Dashboard.vue:289-295` renders `<PurchaseOrderModal>`, which is **never imported, never registered, and does not exist as a file**. The primary "raise a purchase order for a shortage" action silently does nothing (Vue logs an unknown-element warning); `openPOModal`/`viewPO`/`handlePOCreated` are dead code.
Related: `client/src/api.js:97-135` calls four endpoints that **don't exist** in `server/main.py` — `/api/purchase-orders`, `/api/purchase-orders/{id}`, `/api/restocking-orders/{id}`, `/api/inventory/low-stock`.
**Do:** either build `PurchaseOrderModal.vue` + the backend routes, or remove the buttons, the handlers, the `<PurchaseOrderModal>` block, and the four unused `api.js` helpers. **Caveat if you add `/api/inventory/low-stock` later:** declare it _before_ `/api/inventory/{item_id}` (`server/main.py:258`) or `low-stock` is parsed as an item id.

### P0-2 · Lock down CORS and the listen address

**Severity: Medium now / latent Critical** · SEC-2, SEC-7 · ~5 lines
`server/main.py:51-57` sets `allow_origins=["*"]` **with** `allow_credentials=True`; Starlette then reflects _any_ origin back with `Access-Control-Allow-Credentials: true`. Harmless only until any cookie/session auth exists — then any website can make authenticated cross-origin calls. `server/main.py:520` binds `0.0.0.0`.
**Do:** `allow_origins=["http://localhost:3000"]` from env/config; bind `127.0.0.1` for local dev (host configurable for deployment). Directly contradicts `server/CLAUDE.md`.

### P0-3 · Stop silently losing user data

**Severity: High** · UX-12
`App.vue:179-233` (`loadTasks`/`addTask`/`deleteTask`/`toggleTask`) and `Orders.vue:179-181` swallow failures into `console.error`. A user adds a task, the POST fails, nothing appears, no error shown — silent data loss.
**Do:** set a user-visible error ref (toast or inline) in every `catch`; roll back optimistic UI on failure.
_Security explicitly rejected the "information disclosure" framing of this one (FastAPI debug is off) — it is a pure UX bug, handled once here._

---

## P1 — This sprint

### P1-1 · Authentication + real logout

**Severity: High** · SEC-1, SEC-3
Every route in `server/main.py` — including mutating `POST`/`DELETE`/`PATCH` and the financial `/api/spending/*` — is world-reachable. The frontend "auth" is `isAuthenticated = ref(true)` (`useAuth.js:92`) with no `router.beforeEach`, and **`logout()` only shows an `alert()`** (`useAuth.js:94-98`) — visible in every demo, ~10-line fix.
**Do:** add an API-key/JWT `Depends` gate (at minimum on all non-GET routes and `/api/spending/*`); drive `isAuthenticated` from token state; add a route guard; make `logout()` clear the token and redirect.
_If this stays a pure local demo:_ document the no-auth exception prominently in `README`/`CLAUDE.md` **and still fix logout**.

### P1-2 · API input-bounds & pagination pass (one coordinated backend change)

**Severity: Medium** · SEC-4, SEC-5, PERF-6, PERF-13

- `CreateTaskRequest` (`main.py:136-139`): no `max_length`, no `priority` enum, no date validation → unauthenticated callers append unbounded strings/rows to process-global lists (memory slope; every subsequent `GET /api/tasks` is unpaginated and every create does an O(n) `max()` id scan).
- `CreateRestockingOrderRequest.budget: float` (`main.py:173`): accepts `Infinity`/`NaN` → `int(inf // cost)` → unhandled 500. (Not reachable from the UI slider — direct API only.)
- `/api/orders` (`main.py:266`): full ~150 KB unpaginated payload with customer names + line items, pulled in full by 3 views.
- `filter_by_month` (`main.py:34-48`): substring match — `month=0` matches any date containing `0`.
  **Do:** `Field(max_length=…, ge=0, le=…, allow_inf_nan=False)` + `Literal[...]` on request models; `limit`/`offset` + slim projection on list endpoints; per-IP rate limiting (`slowapi`); parse-and-compare date components in `filter_by_month`.

### P1-3 · Responsive layout

**Severity: High** · UX-2, UX-3, UX-4, UX-5
**Zero `@media` queries in the entire codebase.** Fixed 260px sidebar + non-wrapping 4-select filter bar (~900px min) + fixed-width tables + fixed-`px` charts → horizontal page scroll and clipped content below ~900px. Warehouse-floor tablets are a plausible audience.
**Do:** breakpoints — sidebar → drawer/overlay under 768px, `flex-wrap` the filter bar, wrap every `<table>` in `.table-container`, compute chart y-axis maxima from data and make SVGs `viewBox`-responsive.

### P1-4 · Keyboard & assistive-tech accessibility (WCAG 2.1 AA)

**Severity: High** · UX-6, UX-7, UX-8, UX-18, UX-22
Procurement-blocking / ADA-exposure territory that the security and perf lenses don't score:

- **UX-6** Profile + language dropdown items use `@mousedown.prevent` → completely keyboard-inoperable.
- **UX-7** Clickable table rows/cells (5 views) have no `tabindex`/`role`/key handler → mouse-only.
- **UX-8** Icon-only buttons (modal close, clear-search, delete, filter reset) have no accessible name.
- **UX-18** No modal has `Escape`-to-close, focus trap, focus return, or `role="dialog"`/`aria-modal`.
- **UX-22** Collapsed-sidebar nav links are unlabelled icons (and collapsed is the **default** under 1024px).
  **Do:** `@click` not `@mousedown` on menu items + `Escape`/outside-click close + `role="menu"`; row primary cell as `<button>` or `tabindex=0`+`role=button`+key handler; `:aria-label` (localised) on every icon button, `aria-hidden` on inner SVGs; a shared `useModal` composable (Esc, focus trap, focus return, `role="dialog"` + `aria-labelledby`); keep `aria-label` on nav links regardless of collapse state.

### P1-5 · `Reports.vue` overhaul (one pass)

**Severity: High (perf axis) / Low (UX axis)** · PERF-1, PERF-2, PERF-3, UX-14, UX-16
`Reports.vue` is the only Options-API view and concentrates the most findings: **13 `console.log` calls inside template-bound methods** (`formatNumber` runs ~30×/render — synchronous console I/O, measurable jank with DevTools open, and it's shipped debug code that shows in screen-shares), derived data computed in methods instead of `computed`, `getBarHeight` rescanning the array per bar (O(n²)/render), and it's entirely un-internationalised.
**Do:** delete all `console.log`; convert to `<script setup>`; precompute a `rows` `computed` of formatted view-models; hoist `maxMonthlyRevenue`; route every string through `t()` with `en`/`ja` keys.

---

## P2 — Schedule

| #    | Item                                                                                                                                                                                                                                                                                                                                                    | Severity | Findings                  |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------- |
| P2-1 | **Move order aggregation server-side** — extend `/api/dashboard/summary`; stop shipping raw `/api/orders` to Dashboard/Spending; build a `Map<sku,item>` for `topProducts`; hoist the per-cell `translateCategory`/`translateMonth` object literals into a shared `useTranslations` composable. Also shrinks the unauthenticated data-exposure surface. | Medium   | PERF-7, PERF-8, PERF-12   |
| P2-2 | **Date formatters** — hoist `useI18n()` to `setup()` (Orders/Dashboard/Demand re-instantiate it per cell) **and** guard `const d = new Date(x); if (isNaN(d.getTime())) return '—'` before formatting; guard `current_demand === 0` in `Demand.vue:174`.                                                                                                | Medium   | PERF-5, UX-17             |
| P2-3 | **Keep-stale-while-refetching** — on filter change, keep the rendered table visible with a subtle inline spinner instead of the full-screen "Loading…" that blanks the view. Compounds with the `/api/orders` payload cost (P1-2).                                                                                                                      | Medium   | UX-13 (+ PERF-6)          |
| P2-4 | **Route-level code splitting** — `component: () => import('./views/X.vue')` for all 7 routes; currently the entire app (Dashboard alone is 1271 lines) + ~10 modals ship in the entry chunk. The one page load users can't avoid.                                                                                                                       | Medium   | PERF-10                   |
| P2-5 | **Contrast + focus-visible** — darken muted text off `#94a3b8` (fails AA at ~2.9:1) to `#64748b`/`#475569`; add a consistent `:focus-visible { outline: 2px solid #2563eb }` to nav links, rows, menu triggers, icon buttons.                                                                                                                           | Medium   | UX-11, UX-23              |
| P2-6 | **Form/table/doc semantics** — associate filter-bar `<label>`s with their `<select>`s; `scope="col"` on every `<th>`; `document.documentElement.lang = locale` in `setLocale`; `aria-label` + `aria-valuetext` on the Restocking range slider.                                                                                                          | Medium   | UX-9, UX-10, UX-19, UX-24 |
| P2-7 | **Empty states & delete confirm** — "No items match your filters" row on every filterable table; confirm step or undo toast for task delete.                                                                                                                                                                                                            | Medium   | UX-25, UX-26              |
| P2-8 | **CSV formula-injection** — prefix any field starting `= + - @ \t \r` in `escapeCsvField` (`Inventory.vue:236`). Land it before user-entered task titles ever reach the export path.                                                                                                                                                                    | Low      | SEC-6                     |
| P2-9 | **Single-pass computeds** — `getOrdersByStatus` (called 4× as a method, filters 250 rows each) and `getForecastsByTrend` (~15×/render) → one `computed` each.                                                                                                                                                                                           | Low      | PERF-4, PERF-9            |

---

## P3 — Hygiene, polish, scale-only

| #     | Item                                                                                                                                                                                                 | Findings                 |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| P3-1  | Commit `uv.lock`; commit `client/package-lock.json` alongside the already-pinned public `.npmrc` (the leak risk the gitignore guards against is mitigated by the `.npmrc`).                          | SEC-8                    |
| P3-2  | Raise dep floors: `axios ^1.8.2` (CVE-2025-27152 SSRF/cred-leak), `vite ^5.4.20`; add `npm audit` to CI. Server deps already resolve modern.                                                         | SEC-9                    |
| P3-3  | PR-checklist / CLAUDE.md note: no real names, emails, phones, or customer/vendor identities in `server/data/` or `useAuth.js` — repo and forks are PUBLIC.                                           | SEC-10                   |
| P3-4  | Stable `v-for` keys — `q.quarter`, `month.month`, `item.sku`, `order.id` (not `index`). Convention today; a live bug once lists sort/filter in place.                                                | PERF-11, UX-27           |
| P3-5  | Scale-only (no measurable impact until data grows 10–100×): `Map` lookup in `topProducts`, single-pass `apply_filters`, `functools.lru_cache` on `/api/reports/*`.                                   | PERF-8, PERF-13, PERF-14 |
| P3-6  | `Backlog.vue` — replace the `✓` emoji (violates "no emojis in UI") with the inline SVG check; then either add the `/backlog` route + nav entry or delete the file (currently unreachable dead code). | UX-15                    |
| P3-7  | i18n miss → `console.warn` + humanised fallback instead of rendering the raw dotted key.                                                                                                             | UX-20                    |
| P3-8  | Replace the `alert()` transaction "detail" (`Spending.vue:450`) with a proper modal like the other tables; remove its `console.log`.                                                                 | UX-21                    |
| P3-9  | Unify the purple-gradient "add" buttons to the slate/blue `#2563eb` primary + `#3b82f6` focus ring.                                                                                                  | UX-28                    |
| P3-10 | Dashboard KPIs (Inventory Turnover, Avg Processing Time, Fill Rate) are hardcoded and never react to filters/data — compute them or label "sample".                                                  | UX-29                    |
| P3-11 | Orders "items" popover (`position:absolute` in an `overflow-x:auto` container) clips and can render off-screen — use a Teleport layer or an inline expanding row; close others on open.              | UX-30                    |

---

## Disputed severity ratings — and how they were resolved

| Finding(s)                                                      | Dispute                                                                                                                                                                                                                        | Resolution                                                                                                                                                                                  |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PERF-1 ↔ UX-16** (`console.log` in `Reports.vue` render path) | perf rated **High** (synchronous console I/O ~30×/render, real jank with DevTools open, visible in screen-shares); UX rated **Low** (end users never see a console).                                                           | **One work item, not two.** Severity recorded as High-on-perf-axis / Low-on-UX-axis; folded into P1-5. Actioned regardless because it's a 2-minute delete.                                  |
| **SEC-4** (unbounded bodies / no rate limit)                    | security floated **Low/Medium**; perf and UX both pushed for **Medium** (O(n) id-gen scan on every create + unpaginated `GET /api/tasks` = a real availability slope, not just RSS growth).                                    | Settled at **Medium**; bundled into P1-2.                                                                                                                                                   |
| **PERF-10** (no code splitting)                                 | perf self-rated **Low/Medium**; UX argued **Medium** (the unavoidable landing-page load; tablet/VPN audience per UX-2).                                                                                                        | **Medium** — P2-4.                                                                                                                                                                          |
| **SEC-3** (client-only auth)                                    | security: "no real auth to bypass" → **Medium**. UX: the Logout-does-nothing sub-bug is a live trust violation on shared terminals, ~10-line fix.                                                                              | Severity stays **Medium**; **priority elevated** — logout fix rides with P1-1.                                                                                                              |
| **PERF-6** (`/api/orders` 150 KB unpaginated)                   | perf framed it as network cost (**Medium**). security added a data-exfiltration dimension (unauth + any-origin CORS → any site pulls the customer order book); UX added "refetched on every filter change, blanks the screen". | **Medium** severity held, but **sequenced with** P0-2 / P1-1 / P2-3 rather than treated as "just perf".                                                                                     |
| **UX-1** (dead PO buttons)                                      | security saw no vulnerability and didn't rate it; perf flagged it in passing; both deferred to UX.                                                                                                                             | **Critical** held — broken primary action on the default landing page. P0-1.                                                                                                                |
| **UX-12** as information disclosure                             | UX's write-up anticipated a security "info disclosure" angle.                                                                                                                                                                  | security **rejected** it (FastAPI debug off; swallowing to console is if anything mildly good for security). Recorded as a **pure UX finding** (silent data loss), not double-listed. P0-3. |
| **SEC-5** (`Infinity`/`NaN` budget → 500)                       | Is it reachable?                                                                                                                                                                                                               | UX confirmed the Restocking slider is bounded (`min=0 max=500000 step=5000`) — **direct API callers only**. Supports the **Low** rating; still fixed as part of P1-2.                       |

## What the audit did NOT find (verified negatives)

- **No path traversal, no SQL/command/`eval`/`exec`/`subprocess` injection, no unsafe deserialization** — no DB, no shell, `json.load` on hardcoded local paths only (`server/mock_data.py:14-18`).
- **No DOM XSS** — no `v-html`/`innerHTML`/`eval` in `client/src`; Vue auto-escapes interpolations.
- **No committed secrets** — `.mcp.json` uses `${GITHUB_PERSONAL_ACCESS_TOKEN}`, `.env` gitignored, only `localhost` URLs.
- **No mass-assignment** — POST handlers build the stored dict field-by-field; `status` forced server-side.
- **Backend does NOT re-parse JSON per request** — loaded once at module import; in-memory filters are linear, not quadratic.
- **The new CSV export** (`Inventory.vue` `exportToCsv`) is sound on throughput and Blob/URL lifecycle; only the formula-injection escaping (P2-8) is outstanding.
