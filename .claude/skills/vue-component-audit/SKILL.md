---
name: vue-component-audit
description: Analyzes Vue 3 component structure across client/src and produces a prioritized report of performance issues and code-reuse opportunities (duplicated markup, oversized views, non-memoized derived data, unstable v-for keys, scattered date/format logic). Use this skill when asked to audit, review, or optimize Vue component structure, find duplication, or improve frontend performance/maintainability.
---

# Vue Component Structure Audit

A methodology for scanning `client/src` and reporting concrete, file-and-line-referenced findings on performance and code reuse — not a rewrite. It produces a prioritized report first; fixes are applied only for items the user selects, and only through this repo's own delegation rules.

## When to Use This Skill

Use when asked to:
- Audit or review Vue component structure for performance or duplication
- "Optimize" the frontend in a component-structure sense (as opposed to `/optimize`, which is a whole-codebase dead-code sweep)
- Find repeated markup/logic worth extracting into a shared component or composable
- Explain why a specific view feels slow or hard to maintain

Do **not** use this skill for:
- Backend/API performance (that's a separate concern — see `server/`)
- General dead-code removal across the whole stack (use the `/optimize` command instead)
- Visual/design changes (use `vue-sidebar-redesign` or a plain design request)

## Guidance, Not Automatic Execution

This is reference material for running an audit and writing a report. It does not rewrite `.vue` files on its own. Per this repo's root `CLAUDE.md`: *"ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert."* Once the user picks findings to act on, delegate every `.vue` write to `vue-expert` — never edit `.vue` files directly.

## Scan Checklist

Work through `client/src/views/*.vue`, `client/src/components/*.vue`, and `client/src/composables/*.js`. For each check, record every match with `file:line`, not just the first one.

### Performance

1. **Unstable `v-for` keys** — grep for `:key="index"` / `:key="i"`. Causes incorrect DOM reuse and lost component state on reorder/insert/delete.
2. **Method calls in templates that should be `computed`** — a function invoked in the template (`{{ someMethod() }}` or `:prop="someMethod()"`) that derives from reactive state re-runs on *every* render instead of being cached. Distinguish from methods that take per-item arguments (e.g. `getStockIconClass(item)`) — those are fine; look for parameterless ones deriving from component-wide state.
3. **Oversized view files** — anything past ~400-500 lines is a signal the view is mixing data-fetching, multiple derived-data pipelines, and several chart/table renderers in one file. Flag as a decomposition candidate (split into sub-components or extract computeds into a composable), not an automatic rewrite.
4. **Repeated heavy computation without memoization** — `computed` blocks that re-derive the same filtered/sorted array multiple times in one file (e.g. filtering the same source array in three different computeds) instead of layering one filtered-base computed that the others read from.
5. **`watch`/`watchEffect` without cleanup or with broad dependencies** — a watcher that re-triggers a full data reload on any filter change when only one filter actually changed, or that has no `immediate`/cleanup handling.
6. **Unvalidated date parsing in hot paths** — `new Date(...)` called directly on API data without an `isNaN(....getTime())` guard, inside a computed or loop that runs per-render. Also a correctness bug per this repo's own `CLAUDE.md` common-issues list, not just a performance one.

### Code Reuse

7. **Duplicated component shells** — a markup skeleton (e.g. modal overlay/header/close-button structure, or a stat-card layout) repeated near-verbatim across multiple `.vue` files with only the inner content differing. Flag as an extraction candidate for a shared base component (e.g. a `BaseModal.vue` wrapping `Teleport`/`Transition`/overlay/close-button, with the specific body passed via slot).
8. **Duplicated scoped CSS** — the same class names (`.modal-overlay`, `.modal-container`, `.close-button`, etc.) redefined with near-identical rules in multiple `<style scoped>` blocks instead of coming from one shared component or a shared class in `App.vue`.
9. **Scattered date/currency/format logic** — formatting or parsing logic duplicated across views instead of routed through an existing shared util (this repo already has `client/src/utils/currency.js` for currency — check whether date formatting/parsing has an equivalent, or is copy-pasted per view instead).
10. **Duplicated filter-computed logic across views** — each view re-implementing the same "filter array by warehouse/category/status" reduction instead of sharing one filtering helper (check against the existing `useFilters` composable pattern in `client/src/composables/useFilters.js` — new shared logic should follow that composable convention, not become a new one-off).
11. **Copy-pasted chart/SVG rendering** — the same custom SVG bar/line chart markup rebuilt per view (e.g. across `Dashboard.vue`, `Reports.vue`, `Spending.vue`, `Demand.vue`) instead of one parameterized chart component.

## Running the Audit

Use `grep`/`Grep` across `client/src` for concrete evidence — don't rely on memory of "typical Vue issues." Useful starting greps:

```bash
grep -rn ':key="index"\|:key="i"' client/src/views client/src/components
grep -rln 'new Date(' client/src/views | xargs grep -n 'new Date('
grep -rln '<svg' client/src/views
wc -l client/src/views/*.vue client/src/components/*.vue
grep -rn 'Teleport to="body"' client/src/components
```

Cross-check any "duplicated shell" hypothesis by actually reading 2-3 of the suspected files side by side — confirm the markup structure, not just the presence of similar-sounding class names.

## Report Format

Produce a report grouped by category (Performance, Code Reuse), each finding as:

```
[file:line] Short description of the issue
  Impact: what breaks or degrades, concretely
  Suggestion: the specific refactor (name the new component/composable if extraction)
```

Order within each category by impact, not by file order. Do not pad the report with generic advice that isn't backed by an actual grep/read match in this codebase.

## Execution Recipe (If the User Wants Fixes Applied)

1. Run the full Scan Checklist against current `client/src` state — don't reuse stale findings from a previous audit in the same session if files have changed since.
2. Present the report and let the user choose which findings to act on. Don't fix everything unprompted — extraction refactors (item 7, 9, 10, 11) change shared structure and are worth confirming scope on first.
3. For accepted fixes touching `.vue` files, delegate to `vue-expert` with the specific finding (file, line, suggested change) — not a vague "optimize this file" instruction.
4. For a shared-component extraction (e.g. `BaseModal.vue`), have `vue-expert` build the base component first, verify it renders identically in one consuming view, then migrate the remaining call sites one at a time rather than all at once.
5. After fixes, re-run the relevant grep checks to confirm the finding is actually resolved (e.g. re-grep for `:key="index"` after claiming it's fixed).
6. If UI-visible, verify in-browser per this repo's Playwright convention before reporting done.

## Best Practices

1. Ground every finding in an actual grep/read match — file and line, not a generic pattern
2. Distinguish parameterless derived-state methods (should be computed) from per-item helper methods (fine as methods)
3. Treat oversized views as a decomposition signal, not an automatic split — confirm scope with the user first
4. Check for an existing shared util/composable before proposing a new one (e.g. `currency.js`, `useFilters.js`) — extend, don't duplicate
5. Verify a "duplicated shell" claim by reading the actual files, not just matching class names
6. Delegate every `.vue` write to `vue-expert`, never edit directly
7. Migrate shared-component extractions one call site at a time, verifying each before moving to the next

## Common Pitfalls

- Flagging a per-item method (e.g. `getStockIconClass(item)`) as "should be computed" — it can't be, since computed properties take no arguments
- Recommending a new date/format utility without first checking whether one already exists to extend
- Treating every large file as broken — some views are large because they render several genuinely distinct sections, not because of duplication
- Applying extraction fixes to all call sites in one pass instead of migrating incrementally and verifying
- Writing or editing `.vue` files directly instead of delegating to `vue-expert`
- Reporting a `:key="index"` finding as fixed without re-grepping to confirm

## Key Reminders

- This is an audit skill: report first, fix only what's selected
- Every finding needs a `file:line` citation from an actual grep/read, not a generic Vue best-practice
- Parameterless template method calls deriving from component state → candidate for `computed`; per-item methods are not
- Check `client/src/composables/` and `client/src/utils/` for existing shared logic before proposing new shared logic
- All `.vue` writes go through `vue-expert` per this repo's `CLAUDE.md`
- Extraction refactors (shared modal base, shared chart component) get migrated one call site at a time, verified incrementally
