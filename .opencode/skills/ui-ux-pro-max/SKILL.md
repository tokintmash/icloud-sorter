---
name: ui-ux-pro-max
description: UI/UX Pro Max design intelligence. Use when building, redesigning, reviewing, or polishing UI/UX, design systems, landing pages, dashboards, components, accessibility, color, typography, responsive layout, motion, or frontend visual quality.
license: MIT
compatibility: OpenCode skill. Self-contained guidance inspired by https://github.com/nextlevelbuilder/ui-ux-pro-max-skill; no bundled CLI database required.
metadata:
  author: OpenCode local
  source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
  version: "1.0.0"
---

# UI/UX Pro Max

Design intelligence for building professional, accessible, responsive, non-generic user interfaces.

Use this skill as a working discipline, not as a style preset. The goal is to make the product feel designed: clear hierarchy, strong information architecture, intentional visual language, accessible interaction, and implementation that fits the existing codebase.

## When To Use

Must use when the task changes how a product looks, feels, moves, or is interacted with:

- Build or redesign a page, landing page, dashboard, admin screen, app screen, modal, form, table, chart, navigation, or empty state
- Create or refactor UI components, visual systems, themes, dark mode, tokens, spacing, typography, iconography, or motion
- Review, improve, or polish UI quality, responsiveness, accessibility, usability, or visual consistency
- Choose product style, color palette, type system, layout system, component variants, or interaction patterns
- Diagnose why a UI feels unprofessional, generic, cluttered, inaccessible, slow, or confusing

Skip when the task is purely backend logic, database/API design, infrastructure, non-visual scripts, or non-UI performance work.

## Core Rules

- Inspect the existing UI before changing it. Preserve established design-system patterns unless the user asks for a new direction.
- Avoid safe generic output. Do not default to centered hero + purple gradient + rounded cards unless it is genuinely right for the product.
- Treat mobile and desktop as first-class. Check small phone, tablet, desktop, and wide layouts mentally or with available tooling.
- Use semantic HTML and accessible component primitives. Keyboard, focus, labels, and screen readers are not optional.
- Prefer vector icons from one family. Do not use emojis as structural UI icons.
- Use design tokens or existing CSS variables when available. Avoid random hardcoded hex, spacing, shadow, z-index, and radius values.
- Motion must clarify state, hierarchy, or cause/effect. Respect reduced motion.
- Every screen should have one clear primary action. Secondary and destructive actions must be visually subordinate and separated.

## Workflow

### 1. Understand The Product

Extract the design brief from the request and codebase:

- Product type: SaaS, consumer app, e-commerce, finance, healthcare, developer tool, creative portfolio, marketplace, content product, internal admin, etc.
- User goal: what the user is trying to accomplish on this screen
- Audience: consumer, professional, enterprise, technical, non-technical, high-trust, playful, premium, regulated
- Stack and constraints: React, Vue, plain CSS, Tailwind, design system, component library, existing CSS architecture
- Brand cues: colors, voice, density, current typography, icon set, imagery, motion style
- Success criteria: conversion, clarity, trust, speed, data comprehension, task completion, delight

If key information is missing and it materially affects the design, ask one short clarifying question. Otherwise make a sensible choice and proceed.

### 2. Generate A Design System Direction

Before implementing a new or substantially changed UI, define these choices:

| Dimension | Decide |
|-----------|--------|
| Pattern | Landing, dashboard, wizard, split view, command center, feed, detail page, settings, checkout, CRUD admin |
| Visual style | Minimal, editorial, bento, glass, brutalist, premium dark, soft UI, data-dense, playful, enterprise, tactile |
| Color | Primary, accent, surface, border, text, success, warning, danger, focus, dark-mode equivalents |
| Typography | Display/body pairing, type scale, weights, line-height, measure |
| Layout | Grid, max width, gutters, vertical rhythm, section density, responsive breakpoints |
| Components | Buttons, cards, forms, nav, tables, dialogs, charts, empty states, loading states |
| Interaction | Hover, pressed, focus, loading, disabled, validation, transitions, route changes |
| Accessibility | Contrast, keyboard navigation, labels, roles, reduced motion, target sizes |

Write the design direction into the implementation through code, tokens, and structure. Do not leave it as prose only.

### 3. Pick A Style Intentionally

Use product fit over trendiness:

| Product Need | Strong Directions | Avoid |
|--------------|-------------------|-------|
| Enterprise SaaS | Clean grid, restrained color, high contrast, dense but legible tables, clear hierarchy | Whimsical effects, low contrast, excessive animation |
| Developer Tool | Monospace accents, command palette patterns, dark/light parity, fast information scanning | Decorative gradients that reduce clarity |
| Finance/Insurance | Trustworthy palette, explicit status states, conservative motion, strong data readability | Neon, glass blur over dense content, ambiguous iconography |
| Healthcare | Calm colors, accessible contrast, generous spacing, reassurance, plain language | Alarmist red, tiny text, playful microcopy for serious states |
| Wellness/Beauty | Soft surfaces, organic shapes, elegant typography, gentle motion | Harsh shadows, cyberpunk colors, dense layouts |
| Creative/Portfolio | Editorial rhythm, memorable hero, asymmetric layouts, expressive typography | Template-like card grids with no point of view |
| E-commerce | Product-first imagery, clear pricing, trust signals, sticky purchase actions, fast filters | Hiding core purchase actions behind animation |
| Admin/Internal Tool | Task-first hierarchy, compact controls, predictable navigation, resilient empty/error states | Marketing-style layouts that slow operators down |
| AI Product | Show capability and control, transparent states, clear input/output structure | Generic purple/pink AI gradients as the entire identity |

### 4. Implement With Existing Patterns

- Follow the repository's component, styling, and state-management conventions.
- Keep changes small and coherent. Do not introduce a UI framework unless the project already uses it or the user explicitly asks.
- Prefer semantic class names or existing CSS modules/tokens over one-off styling.
- If using Tailwind, compose utilities directly for local layout and extract only repeated components.
- If using React, avoid unnecessary `useMemo`/`useCallback`; follow the repo's React conventions.
- Make loading, empty, error, disabled, hover, focus, and success states part of the implementation, not afterthoughts.

## Quality Priorities

### 1. Accessibility

- Text contrast: 4.5:1 minimum for normal text, 3:1 for large text and non-text UI indicators
- Visible focus states on every interactive element
- Semantic buttons, links, headings, labels, fieldsets, tables, dialogs, and landmarks
- Icon-only buttons need accessible names
- Do not remove browser focus outlines without replacing them with equivalent visible focus
- Color cannot be the only meaning carrier; pair with text, icon, pattern, or shape
- Respect `prefers-reduced-motion`
- Keep touch targets at least 44x44 CSS px where practical

### 2. Layout And Responsiveness

- Design mobile-first, then scale up to `768px`, `1024px`, and `1440px+`
- Avoid horizontal scroll on mobile
- Use stable gutters and max-widths; do not let long text run edge-to-edge on desktop
- Reserve space for media and async content to avoid layout shift
- Fixed headers, footers, and bottom CTAs must not cover scroll content
- Use `min-height: 100dvh` patterns where mobile viewport units matter

### 3. Typography

- Base body text should usually be 16px or larger
- Body line-height: roughly 1.45 to 1.75 depending on density
- Limit long-form line length to roughly 60-75 characters on desktop
- Use font weight, size, spacing, and alignment to create hierarchy before adding decoration
- Use tabular figures for prices, metrics, timers, and table columns when available
- Avoid mixing more than two type families unless there is a deliberate editorial system

### 4. Color And Theming

- Define semantic colors: background, surface, text, muted text, border, primary, accent, danger, success, warning, focus
- Test dark mode independently; do not simply invert light colors
- Borders/dividers must remain visible in both themes
- Disabled states must be semantically disabled and visually clear
- Destructive actions should be spatially separated and use danger styling

### 5. Interaction And Motion

- Give immediate feedback within roughly 100ms for taps/clicks
- Micro-interactions: 150-300ms; complex transitions usually under 400ms
- Animate transform and opacity where possible; avoid layout-thrashing animations
- Enter can be slightly slower than exit; exits should feel responsive
- Loading over 300ms needs visible feedback; over 1s often benefits from skeleton/progress
- Animations should be interruptible and should not block input

### 6. Forms And Feedback

- Use visible labels, not placeholder-only labels
- Place validation errors near the field and describe how to fix them
- On submit failure, focus or link to the first invalid field when practical
- Use loading, success, and error states on async actions
- Confirm destructive actions or provide undo
- Empty states should explain what happened and offer the next useful action

### 7. Navigation

- Current location must be visible
- Back behavior should preserve scroll, filters, and input state when practical
- Keep primary navigation stable across related screens
- Do not mix several primary navigation systems at the same hierarchy level
- On route changes, keep screen-reader focus management in mind

### 8. Charts And Data

- Match chart type to data: trend = line, comparison = bar, part-to-whole = pie/donut only for few categories, flow = funnel/sankey, distribution = histogram/box
- Provide labels, legends, tooltips, units, and a text summary for accessibility
- Do not rely on red/green alone
- Use tables or data summaries for screen readers and precise values
- Simplify charts on small screens rather than shrinking until unreadable

## Pre-Delivery Checklist

Before calling UI work complete, verify:

- No emoji structural icons; icons are from a consistent vector family
- One clear primary action per screen or section
- Hover, active/pressed, focus, disabled, loading, empty, and error states are covered where relevant
- Body text is readable, line lengths are controlled, and hierarchy is obvious
- Mobile layout works at 375px width without horizontal scroll
- Desktop layout uses intentional max-widths, gutters, and density
- Contrast is acceptable in light and dark themes where both exist
- Keyboard navigation and focus order are sane
- Forms have labels and useful validation messages
- Motion respects reduced-motion and avoids layout shift
- Build, typecheck, lint, screenshots, or relevant tests have been run when feasible

## Review Mode

When asked to review UI/UX, prioritize findings over compliments:

- Accessibility blockers
- Broken responsive behavior
- Confusing information architecture or unclear primary action
- Inconsistent visual system, spacing, typography, icons, shadows, or radius
- Missing states: loading, empty, error, disabled, hover, focus
- Performance risks: layout shift, oversized assets, heavy animations, unvirtualized large lists
- Trust risks: unclear pricing, destructive action placement, missing confirmation, misleading copy

Report concrete file/line references when reviewing code.

## Optional Official Database

The original project provides a larger searchable database and installer. If the user explicitly wants the full third-party bundle, use its documented installer instead of recreating assets manually:

```bash
npx ui-ux-pro-max-cli init --ai opencode
```

This local skill is intentionally lightweight and self-contained so it can be loaded by opencode without external scripts or bundled binary assets.
