---
name: vue-sidebar-redesign
description: Methodology for converting a Vue 3 app's top-nav layout into a modern SaaS-style left-sidebar layout while reusing the app's existing design tokens and fixing spacing/style inconsistencies. Use this skill when asked to redesign, restructure, or modernize a Vue 3 application's navigation from a horizontal top bar into a vertical sidebar layout.
---

# Vue Sidebar Redesign Methodology

This skill is a methodology for restructuring a Vue 3 app's navigation from a horizontal top bar into a vertical left sidebar — a layout change, not a rebrand. It is reference material for whoever plans and executes the redesign; it does not execute itself, and it does not replace the target app's own design language.

## When to Use This Skill

Use this skill when asked to:
- Convert a top-nav layout into a left sidebar layout
- "Modernize" or "SaaS-ify" a Vue 3 app's navigation
- Make spacing and visual polish consistent while doing the above

Do **not** use this skill for:
- Rebranding or introducing a new color palette (that's a separate request)
- Migrating to a component/UI library
- Apps that already have a sidebar (that's a tweak, not this methodology)

## Guidance, Not Execution

This document is reference material — it does not write files on its own. Whoever applies it must first check the target repo's own rules for touching `.vue` files. Many Vue projects mandate that frontend file edits go through a dedicated subagent or reviewer.

**Concrete example from this repo**: the root `CLAUDE.md` states *"ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert."* When applying this skill here, every `.vue` write in the Execution Recipe below must be delegated to `vue-expert`, not made directly. Always look for the equivalent rule in whatever repo you're working in before writing code.

## Discovery Checklist (Audit Before Designing)

Complete this audit before designing anything. Skipping it produces redesigns that silently break unrelated CSS.

- **Locate the root layout component.** It may be embedded directly in `App.vue` (no separate layout file), or live in a dedicated `Layout.vue`/`MainLayout.vue`. Check both — don't assume.
- **List the current nav items/routes exactly as they exist today**, from the router config and the nav template. Do not add, remove, or reorder items. Do not force-include views that exist as files but aren't routed or linked — if it's not reachable today, it's out of scope.
- **Extract the current global design tokens** (colors, radii, spacing) from wherever global styles live — often an unscoped `<style>` block in the root component.
- **Grep every `position: sticky` / `position: fixed` declaration.** For each one, note the offset value and what element it's implicitly measured against. A sticky secondary bar with `top: 70px` because the nav above it is 70px tall is a coupling that will silently break once the nav moves — find these *before* deleting anything.
- **Grep for secondary widgets anchored inside the nav** — profile menu, language switcher, search box, notifications. Note how each is positioned (commonly `position: relative` root + `position: absolute` dropdown panel) and which edge it anchors to (e.g. `right: 0`). This will likely need to flip once the widget moves into a sidebar.
- **Scan every view/page-level file's `<style scoped>` block** for locally redefined versions of shared class names (`.card`, `.stats-grid`, etc.) that diverge from the global tokens (different radius, different shadow, etc.). These are pre-existing consistency defects — flag them for normalization, since "consistent spacing/polish" isn't achieved just by adding a sidebar.
- **Check for existing `@media` queries.** If there are none, the app has no responsive precedent to build on — that's a signal to make an explicit decision (see below), not to assume responsive behavior is either in or out of scope.

## Design System: Reuse-First Token Vocabulary

**Rule: extract and reuse the target app's existing tokens. Never introduce a new color palette unless explicitly asked.** A redesign that restructures layout but keeps the app's existing brand identity is lower-risk and more valuable than one that also reskins colors — it reads as the same product, reorganized, not a different product.

| Token concept | How to find it | Example (illustrative) |
|---|---|---|
| Ink / primary text | darkest neutral used for headings | `#0f172a` |
| Sub / secondary text | mid-gray used for labels/captions | `#64748b` |
| Border | 1px hairline color on cards/dividers | `#e2e8f0` |
| Surface / bg | page background vs. card background | `#f8fafc` page / `#ffffff` card |
| Accent (brand) | color used for active states, links, primary buttons | `#2563eb` solid / `#eff6ff` tint |
| Radius scale | corner radius on cards, buttons, badges | 6px controls, 10px cards |
| Spacing rhythm | base unit multiples in padding/gap/margin | 4px/8px rhythm, expressed in rem |

Sidebar-specific conventions to apply on top of the extracted tokens:

- **Fixed sidebar width as a single named constant** (CSS variable or equivalent) — never hardcode the width in more than one place. This is the same class of bug as a sticky offset hardcoded to a nav's height: one source of truth, referenced everywhere. A typical range is 240–280px expanded, 64–72px if collapsed to icon-only.
- **Root layout shape**: flip from column (header stacked over main) to row — `display: flex; flex-direction: row` on the app shell, with the sidebar and main content as siblings.
- **Active nav item styling**: reuse the app's existing accent tint/solid pair exactly as it was used for the old active tab state. Don't invent a new active-state treatment.
- **Icon sizing**: fixed square (e.g. 20×20) inline `<svg>` using `stroke="currentColor"` or `fill="currentColor"` so it inherits the nav item's text color automatically.
- **Sticky/scroll model**: the sidebar itself is typically `position: sticky; top: 0; height: 100vh` (or `align-self: flex-start` in a flex row). This *replaces* the old sticky-top-nav pattern — any other element that was sticky-offset relative to the nav (secondary toolbars, filter bars) must be re-anchored to `top: 0` or removed from the sticky chain, since there's no longer a nav bar sitting above content.

## Core Patterns

The templates below use Vue 3 `<script setup>` for brevity. Match whatever convention (Options API vs. `<script setup>`) the target app already uses — don't switch conventions as a side effect of this redesign.

### 1. Sidebar shell skeleton

```vue
<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="sidebar-logo"><!-- logo/brand --></div>
      <nav class="sidebar-nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="sidebar-nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <component :is="item.icon" class="nav-icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-secondary">
        <!-- profile menu / language switcher relocated here -->
      </div>
    </aside>
    <div class="app-main">
      <router-view />
    </div>
  </div>
</template>

<style>
.app-shell {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}
.sidebar {
  width: var(--sidebar-width, 260px);
  flex-shrink: 0;
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border);
  background: var(--surface-card);
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.75rem;
}
.sidebar-secondary {
  margin-top: auto;
  padding: 0.75rem;
  border-top: 1px solid var(--border);
}
.app-main {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}
</style>
```

### 2. Nav item with icon + active state

```vue
<!-- Old top-tab active rule this replaces:
.nav-tabs a.active { color: var(--accent); background: var(--accent-tint); }
-->
<RouterLink
  to="/inventory"
  class="sidebar-nav-item"
  :class="{ active: $route.path === '/inventory' }"
>
  <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
    <!-- hand-authored icon path -->
  </svg>
  <span>Inventory</span>
</RouterLink>

<style scoped>
.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem 0.75rem;
  border-radius: 8px;
  color: var(--sub);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.9rem;
}
.sidebar-nav-item:hover { color: var(--ink); background: var(--surface-hover); }
.sidebar-nav-item.active { color: var(--accent); background: var(--accent-tint); }
.nav-icon { width: 20px; height: 20px; flex-shrink: 0; }
</style>
```

### 3. Before/after: fixing a sticky offset coupled to the removed nav

```css
/* BEFORE — coupled to the old top nav's 70px height */
.filter-bar {
  position: sticky;
  top: 70px;
  z-index: 90;
}

/* AFTER — sidebar layout has no bar above content, so offset becomes 0 */
.filter-bar {
  position: sticky;
  top: 0;
  z-index: 90;
}
```

Before deleting the old nav's CSS, grep the whole app for every sticky/fixed offset. Each one is a candidate for this exact fix — not just the obvious ones.

### 4. Relocating a dropdown's anchor edge

```css
/* BEFORE — widget lived at the right end of a horizontal top bar */
.dropdown-panel { position: absolute; top: calc(100% + 0.5rem); right: 0; }

/* AFTER — widget now lives in a vertical sidebar; flip or bottom-anchor it */
.dropdown-panel { position: absolute; bottom: calc(100% + 0.5rem); left: 0; }
```

## Execution Recipe (Step-by-Step)

1. **Audit** — complete the full Discovery Checklist above. Don't proceed until nav items, tokens, sticky offsets, and per-view divergences are documented.
2. **Check delegation rules** — read the target repo's root `CLAUDE.md` (and any nested `client/CLAUDE.md`) for a mandate like "any `.vue` create/edit must go through subagent X." If one exists, every write step below must be delegated to that subagent, not made directly.
3. **Design the sidebar structure** — decide width, collapse behavior (see below), item list (exactly the audited nav items, unmodified), and icon approach (hand-authored inline SVG matching the app's existing icon style, unless the app already has an icon library).
4. **Map old tokens forward** — populate the token table above with the target app's actual extracted values. This is the shared vocabulary for the rest of the work, not a new palette.
5. **Identify every hardcoded value referencing the old nav** — sticky offsets, z-index assumptions, `max-width`/centering rules on the main content area that assumed no sidebar. List each with its fix before writing code.
6. **Restructure the root layout** (delegated write if required) — flip the app shell from column to row, introduce the `<aside>`, move `<router-view>` into the new main column, apply the fixed sidebar width via the named constant.
7. **Relocate secondary widgets** (delegated write) — move profile menu / language switcher / search into the sidebar, re-anchoring dropdown panels per Pattern 4.
8. **Apply the sticky-offset fixes** identified in step 5 (delegated write).
9. **Normalize per-view style divergences** found in the audit (delegated write, one pass per offending file) — reconcile local overrides back to the shared tokens. Confirm each override wasn't intentional before removing it.
10. **Confirm scope closure** — re-diff the view-level files against the audit list from step 1. No view should have been touched beyond what was explicitly flagged.
11. **Verify in browser** — load every route, confirm active-state highlighting, dropdown anchoring, sticky behavior, and visual parity against the token audit. Use the target repo's existing browser-testing convention (e.g. a Playwright MCP setup) if it has one.

## Responsive/Collapse Behavior — Decide Explicitly

If the target app has no existing `@media` queries, it has no responsive precedent to build on. Don't silently add a collapse toggle or breakpoint behavior as "included," and don't silently skip it either — surface it as an explicit scope decision before writing layout CSS. Retrofitting collapse behavior later reshapes the CSS variable structure from Pattern 1, so it's cheaper to decide up front.

## Best Practices

1. Audit before designing — nav items, tokens, sticky offsets, per-view divergences, all documented first
2. Reuse the target app's existing tokens; never introduce a new palette unless asked
3. One named constant for the sidebar width, referenced everywhere — never hardcoded twice
4. Check the target repo's delegation rules before every `.vue` write, not just the first one
5. Nav item list = exactly what's already routed and linked; don't invent or prune items
6. Hand-author new icons in the app's existing icon style if no icon library exists
7. Treat "consistent spacing" as requiring a pass over per-view style overrides, not just the layout shell
8. Decide responsive/collapse scope explicitly rather than assuming
9. Verify in-browser after restructuring — active states, dropdown anchoring, sticky behavior

## Common Pitfalls

- Deleting the old top-nav CSS without grepping for every other rule that referenced its height/offset
- Introducing a new color palette instead of reusing the app's existing tokens
- Force-adding orphaned or unrouted views into the new sidebar nav
- Declaring "consistent spacing" done without auditing per-view `<style scoped>` blocks for local overrides
- Writing or editing `.vue` files directly when the target repo's `CLAUDE.md` mandates delegation to a subagent
- Silently adding or silently skipping responsive/collapse behavior instead of surfacing it as a decision
- Leaving a relocated dropdown's `right: 0` anchor unchanged after moving it into a sidebar
- Assuming a dedicated `Layout.vue` exists instead of checking whether the layout is embedded in `App.vue`

## Key Reminders

- Always audit before designing — nav items, tokens, sticky offsets, per-view divergences
- Reuse existing tokens; never import a new palette
- Fixed sidebar width via a single named constant, never hardcoded in multiple places
- Hand-author new nav icons as inline SVG matching the app's existing icon style, unless a library already exists
- Check the target repo's CLAUDE.md for a mandated Vue subagent before writing any `.vue` file
- Every sticky/fixed offset coupled to the old nav must be found and fixed, not just the obvious ones
- Nav item list = exactly what's already routed/linked; don't invent or prune items
- Decide responsive/collapse scope explicitly before writing layout CSS
- Verify in-browser after restructuring, checking active states, dropdown anchoring, and visual parity against the token audit
