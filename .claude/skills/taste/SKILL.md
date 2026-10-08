---
name: taste
description: Evaluate UI/UX code against high design standards (typography, spacing, accessibility, contrast, animations).
---

# UI Taste & Design Rules

When writing or reviewing frontend code:
1. **Typography**: Use distinct scales for headings and body; default to fluid sizing where possible.
2. **Spacing**: Stick strictly to 4px/8px grid system increments (`p-2`, `p-4`, `p-8`).
3. **Micro-interactions**: Add smooth transitions (`transition-all duration-200 ease-in-out`) on hover/focus states.
4. **Contrast**: Ensure text passes WCAG AA guidelines against background colors.
Act as a Principal UI/UX Architect and Lead Frontend Engineer. We are building the UI for my website, and I want a bespoke, high-end visual presence (think Linear, Apple, or Vercel quality)—NO default Tailwind components, NO standard hero layouts, NO basic flex columns.

I want you to strictly utilize our installed tools and skills to execute this:

1. **TASTE & DESIGN ENGINE**:
   - Activate the `taste` / `design-taste-frontend` skill to set the aesthetic direction. 
   - Anti-slop enforcement: Strictly avoid standard AI coding defaults (e.g., standard `bg-slate-900`, stock hero layouts, or basic flex columns).
   - Enforce bespoke typography hierarchy, deliberate micro-interactions (`transition-all duration-200 ease-out`), high-contrast focal points, crisp spacing grids (4px/8px), and purposeful visual density.

2. **WEB DESIGN GUIDELINES**:
   - Apply the rules from `awesome-design-md` / VoltAgent guidelines. 
   - Define exact design tokens (color palettes, surface elevations, borders, noise/glow accents, and fluid typography scale) before writing component code.

3. **VISUAL TESTING & REFINEMENT LOOP (Playwright CLI)**:
   - Once you generate or update the frontend code, use `playwright-cli` to launch the local dev server (or navigate to our local build URL).
   - Capture a visual screenshot of the rendered page/component.
   - Inspect the screenshot as ground truth. Evaluate if it looks premium, expensive, and custom. If anything looks low-quality or misaligned, iteratively refactor the CSS/code and re-screenshot until it passes quality standards.

First, perform a "Design Read": summarize the mood, core layout strategy, token choices, and how you will structure the page. Wait for my confirmation, or immediately start building if the codebase is already running!