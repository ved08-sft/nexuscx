# NexusCX — design.md
**Visual & Motion System: "Deep Space / Neon Cyberpunk Enterprise."**
Scope: tokens, type, 3D canvas, motion, adaptability. Layout, features and data live in `SRS.md` / `ARCHITECTURE.md`. Any layout later chosen via `skillui` or Dribbble MUST inherit this system (§5). Coding rules (no `any`, ≤ 250-line TSX, no inline hex) come from `rules.md`.

**Design principles**
1. **Signal over spectacle:** the 3D layer is atmosphere; it never reduces legibility of live data.
2. **Color carries state, never alone:** every risk/compliance color also has a text label or icon.
3. **One source of truth:** tokens are defined once in `globals.css`; Tailwind, shadcn and the WebGL canvas all read from it.
4. **Performance is a design requirement:** 60 FPS on integrated GPUs, graceful degradation, motion off for users who ask.

---

## 1. COLOR PALETTE & THEME TOKENS

### 1.1 Surfaces
| Token | Value | Use |
|---|---|---|
| `--c-void` | `#08090D` | Base page background (Obsidian Void) |
| `--c-surface` | `#0F1117` | Cards, panels (apply `bg-surface/80 backdrop-blur-md`) |
| `--c-surface-2` | `#151823` | Raised/hover surface, popovers |
| `--c-border` | `#1F2430` | Default border |
| `--c-border-soft` | `255 255 255 / 0.08` | Hairlines over the 3D canvas |

### 1.2 Accents & semantic colors
| Token | Hex | Meaning |
|---|---|---|
| `--c-cyan` | `#00F2FE` | Cyber Cyan: AI agents, WebSocket live state, focus rings, primary actions |
| `--c-violet` | `#7000FF` | Electric Violet: LangGraph/workflow elements, secondary fills |
| `--c-success` | `#00E676` | Neon Emerald: compliant / safe / low risk |
| `--c-warning` | `#FFB300` | Amber Gold: medium risk, warnings |
| `--c-danger` | `#FF1744` | Laser Red: high risk, escalation, critical flags (pulsing glow) |

### 1.3 Text
| Token | Hex | Use |
|---|---|---|
| `--c-text` | `#F8FAFC` | Primary |
| `--c-text-2` | `#94A3B8` | Secondary |
| `--c-text-3` | `#64748B` | Muted / code, **decorative or ≥ 18 px only** (see 1.4) |
| `--c-text-3-aa` | `#7C8AA0` | Muted text that must stay readable at small sizes |
| `--c-violet-fg` | `#9D6BFF` | Violet when used **as text or icon on dark** |

### 1.4 Contrast (approx., vs `#08090D`; verify with axe before release)
| Pair | Ratio | Verdict |
|---|---|---|
| `text` on void | ≈ 19:1 | Pass |
| `text-2` | ≈ 7.7:1 | Pass |
| `text-3` (`#64748B`) | ≈ 4.2:1 (≈ 3.9 on surface) | **Fails 4.5:1** for small text → use `text-3-aa` (≈ 5.7:1) |
| `#7000FF` | ≈ 3:1 | **Fails as text** → fills/borders/glows only; text uses `violet-fg` (≈ 5.6:1) |
| `danger` / `cyan` / `success` / `warning` | > 5:1 | Pass |

### 1.5 Glow, gradient & radius tokens
```css
--glow-cyan:   0 0 18px rgb(0 242 254 / 0.35);
--glow-violet: 0 0 18px rgb(112 0 255 / 0.40);
--glow-danger: 0 0 15px rgb(255 23 68 / 0.50);
--grad-brand:  linear-gradient(135deg, #00F2FE 0%, #7000FF 100%);
--radius-card: 12px;  --radius-ctl: 8px;  --radius-pill: 999px;
--blur-panel:  12px;
```
**Blur budget:** at most 8 simultaneous `backdrop-blur` layers on screen (they are GPU-costly over a live canvas); dense lists use opaque `bg-surface-2`.

---

## 2. TYPOGRAPHY & FONT SYSTEM

| Role | Font | Fallback stack |
|---|---|---|
| Sans (UI, transcripts) | **Inter** (alt: Plus Jakarta Sans) | `system-ui, "Noto Sans Devanagari", sans-serif` |
| Mono (metrics, scores, JSON, WS logs) | **JetBrains Mono** (alt: Fira Code) | `ui-monospace, "SFMono-Regular", Menlo, monospace` |

Load with `next/font/google` (self-hosted at build, no runtime request); set `display: "swap"` and expose `--font-sans` / `--font-mono`. `font-feature-settings: "tnum" 1, "zero" 1` on all mono metrics so live numbers do not jitter.

| Level | Tailwind recipe |
|---|---|
| Display metric | `font-mono text-3xl font-extrabold tracking-tight tabular-nums` |
| Section title | `text-lg font-semibold tracking-wide` |
| Body / live transcript | `text-sm font-normal leading-relaxed` |
| Micro-badge / status | `text-xs font-mono uppercase tracking-widest` |

Rules: never below 12 px; transcripts max line length 72ch; Hinglish and Devanagari render in the same size/leading as English.

---

## 3. INTERACTIVE 3D CANVAS (`three` + `@react-three/fiber` + `@react-three/drei`)

### 3.1 Concept
A fixed, full-viewport **Neural Particle Field** behind all dashboard content: slowly drifting cyan/violet nodes that react to call activity and flash red on escalation.

### 3.2 States
| State | Trigger | Speed `uSpeed` | Pulse `uPulse` | Color | Extra |
|---|---|---|---|---|---|
| `idle` | No active call | 0.05 | 0 | 70% cyan / 30% violet | Gentle pointer parallax |
| `active` | Live transcript/processing | 0.25 (ease 600 ms) | `level` 0–1 (driven by transcript chunk rate, not raw audio) | Same, brighter alpha | Wave travels along X |
| `alert` | Any session `Risk > 0.85` | 0.35 | 0.6 | Lerp to `--c-danger` over 400 ms | One radial shockwave, 900 ms, ≥ 2 s between shockwaves; returns to prior state 3 s after alert clears |

### 3.3 Performance budget (hard limits)
| Item | Limit |
|---|---|
| Particles | ≤ **1500** (Workstation uses ≤ 600) |
| Draw calls | 1 `Points` (+ optional 1 `LineSegments` ≤ 300 segments, built once) |
| Shadows / post-processing / bloom | **None** (fake glow: additive blending + soft sprite in shader) |
| Pixel ratio | `dpr={[1, 1.5]}`; `antialias: false`; `powerPreference: "low-power"` |
| Target | 60 FPS integrated GPU; `PerformanceMonitor` lowers draw range to 60% → 30% → fallback |
| Lifecycle | Pause when `document.hidden`; static single frame under `prefers-reduced-motion`; dispose geometry/material on unmount |
| Loading | `next/dynamic(..., { ssr: false })`, mounted after first paint; never blocks live data rendering |
| Fallback | No WebGL or reduced mode → CSS `radial-gradient` using brand tokens |
| Layering | `fixed inset-0 -z-10 pointer-events-none`; content gets `relative z-0` |

### 3.4 Reference implementation
**`src/components/three/NeuralField.tsx`**
```tsx
"use client";
import { Canvas, useFrame } from "@react-three/fiber";
import { PerformanceMonitor } from "@react-three/drei";
import { useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

export type FieldState = "idle" | "active" | "alert";
interface FieldProps { state: FieldState; level?: number; maxCount?: number }
interface Targets { speed: number; pulse: number; alert: number }

const TARGETS: Record<FieldState, Targets> = {
  idle:   { speed: 0.05, pulse: 0,   alert: 0 },
  active: { speed: 0.25, pulse: 0.5, alert: 0 },
  alert:  { speed: 0.35, pulse: 0.6, alert: 1 },
};

/** Read a space-separated RGB token ("0 242 254") from CSS so theme stays single-source. */
function readToken(name: string): THREE.Color {
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const [r = 0, g = 0, b = 0] = raw.split(/\s+/).map((v) => Number(v) / 255);
  return new THREE.Color(r, g, b);
}

const VERT = /* glsl */ `
uniform float uTime, uSpeed, uPulse, uShock, uShockR, uPx;
uniform vec2 uPointer;
attribute float aSeed;
varying float vMix; varying float vGlow;
void main() {
  vec3 p = position;
  float t = uTime * uSpeed;
  p.x += sin(t + aSeed * 6.2831) * 0.35;
  p.y += cos(t * 0.8 + aSeed * 12.566) * 0.35;
  p.z += sin(t * 0.6 + aSeed * 3.1415) * 0.35;
  p.y += sin(p.x * 0.6 - uTime * 2.0) * uPulse * 0.6;
  vec2 d = p.xy - uPointer * 8.0;
  p.xy += normalize(d + 1e-4) * smoothstep(3.0, 0.0, length(d)) * 0.6;
  float sh = smoothstep(1.2, 0.0, abs(length(p.xy) - uShockR)) * uShock;
  p += normalize(p + 1e-4) * sh * 0.8;
  vMix = fract(aSeed * 7.0); vGlow = sh;
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  gl_PointSize = (2.2 + sh * 3.0) * uPx * (18.0 / -mv.z);
  gl_Position = projectionMatrix * mv;
}`;

const FRAG = /* glsl */ `
uniform vec3 uCyan, uViolet, uDanger; uniform float uAlert;
varying float vMix; varying float vGlow;
void main() {
  float a = smoothstep(0.5, 0.0, length(gl_PointCoord - 0.5));
  vec3 base = mix(uCyan, uViolet, step(0.7, vMix));
  gl_FragColor = vec4(mix(base, uDanger, uAlert), a * (0.55 + vGlow));
}`;

function Particles({ state, level = 0, maxCount = 1500, quality }: FieldProps & { quality: number }) {
  const points = useRef<THREE.Points>(null);
  const shockStart = useRef(-10);
  const prev = useRef<FieldState>("idle");

  const { geometry, uniforms } = useMemo(() => {
    const pos = new Float32Array(maxCount * 3);
    const seed = new Float32Array(maxCount);
    for (let i = 0; i < maxCount; i += 1) {
      pos[i * 3] = (Math.random() - 0.5) * 26;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 15;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 12 - 6;
      seed[i] = Math.random();
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1));
    const u = {
      uTime: { value: 0 }, uSpeed: { value: 0.05 }, uPulse: { value: 0 }, uShock: { value: 0 },
      uShockR: { value: 0 }, uPx: { value: Math.min(window.devicePixelRatio, 1.5) },
      uPointer: { value: new THREE.Vector2() }, uAlert: { value: 0 },
      uCyan: { value: readToken("--c-cyan") }, uViolet: { value: readToken("--c-violet") },
      uDanger: { value: readToken("--c-danger") },
    };
    return { geometry: g, uniforms: u };
  }, [maxCount]);

  useEffect(() => () => geometry.dispose(), [geometry]);
  useEffect(() => { geometry.setDrawRange(0, Math.floor(maxCount * quality)); }, [geometry, maxCount, quality]);

  useFrame(({ clock, pointer }, dt) => {
    const t = TARGETS[state];
    const now = clock.elapsedTime;
    if (state === "alert" && prev.current !== "alert" && now - shockStart.current > 2) shockStart.current = now;
    prev.current = state;
    const age = now - shockStart.current;
    uniforms.uTime.value = now;
    uniforms.uSpeed.value = THREE.MathUtils.damp(uniforms.uSpeed.value, t.speed, 3, dt);
    uniforms.uPulse.value = THREE.MathUtils.damp(uniforms.uPulse.value, state === "active" ? level : t.pulse, 4, dt);
    uniforms.uAlert.value = THREE.MathUtils.damp(uniforms.uAlert.value, t.alert, 6, dt);
    uniforms.uShockR.value = age * 13;
    uniforms.uShock.value = age < 0.9 ? 1 - age / 0.9 : 0;
    uniforms.uPointer.value.lerp(pointer, 0.05);
  });

  return (
    <points ref={points} geometry={geometry} frustumCulled={false}>
      <shaderMaterial vertexShader={VERT} fragmentShader={FRAG} uniforms={uniforms}
        transparent depthWrite={false} blending={THREE.AdditiveBlending} />
    </points>
  );
}

export function NeuralField(props: FieldProps) {
  const [quality, setQuality] = useState(1);
  const [paused, setPaused] = useState(false);
  useEffect(() => {
    const onVis = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);
  return (
    <Canvas className="!fixed inset-0 -z-10 pointer-events-none" camera={{ position: [0, 0, 14], fov: 55 }}
      dpr={[1, 1.5]} gl={{ antialias: false, powerPreference: "low-power" }}
      frameloop={paused ? "never" : "always"}
      eventSource={typeof document !== "undefined" ? document.body : undefined} eventPrefix="client">
      <PerformanceMonitor onChange={({ factor }) => setQuality(Math.max(0.3, Math.min(1, 0.3 + 0.7 * factor)))} />
      <Particles {...props} quality={quality} />
    </Canvas>
  );
}
```
**`src/components/three/NeuralBackdrop.tsx`** (the only thing pages import)
```tsx
"use client";
import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import type { FieldState } from "./NeuralField";

const NeuralField = dynamic(() => import("./NeuralField").then((m) => m.NeuralField), { ssr: false });

function webglOk(): boolean {
  try { return !!document.createElement("canvas").getContext("webgl"); } catch { return false; }
}

export function NeuralBackdrop({ state, level, compact = false }: { state: FieldState; level?: number; compact?: boolean }) {
  const [mode, setMode] = useState<"pending" | "webgl" | "css">("pending");
  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const id = requestAnimationFrame(() => setMode(!reduce && webglOk() ? "webgl" : "css"));
    return () => cancelAnimationFrame(id);
  }, []);
  if (mode === "webgl") return <NeuralField state={state} level={level} maxCount={compact ? 600 : 1500} />;
  return <div aria-hidden className="fixed inset-0 -z-10 bg-nx-radial" />;
}
```
Usage: Supervisor `<NeuralBackdrop state={maxRisk > 0.85 ? "alert" : activeCalls > 0 ? "active" : "idle"} level={chunkRate} />`; Workstation passes `compact`.

---

## 4. MOTION, EASING & MICRO-INTERACTIONS

**Framework:** `framer-motion` for component choreography; Tailwind keyframes for looping effects. Wrap the app in `<MotionConfig reducedMotion="user">`.

### 4.1 Tokens
| Token | Value |
|---|---|
| `--ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` (framer: `[0.16, 1, 0.3, 1]`) |
| Micro (press, hover) | 120–150 ms |
| Standard (cards, panels) | 240 ms |
| Emphasis (alerts, route changes) | 480 ms |
| Ambient loops | 1.2–2.4 s, `ease-in-out` |

### 4.2 Micro-interactions
| Interaction | Spec |
|---|---|
| **Live transcript streaming** | New line: `initial {opacity:0, y:8}` → `{opacity:1, y:0}`, 240 ms expo. Stable `key` per line, `AnimatePresence initial={false}`; never animate the whole list's layout. Auto-scroll with `behavior:"smooth"` only if the user is within 80 px of the bottom; otherwise show a "N new" pill. Partial (non-final) text is italic `text-2`. |
| **Risk score pulse** | High-risk badge/card: `animate-risk-pulse` (keyframes below), 1.2 s infinite; glow `0 0 15px rgb(255 23 68 / 0.5)`. Numeric change: 240 ms count tween on `font-mono tabular-nums`. |
| **HITL buttons** | `whileTap={{ scale: 0.97 }}`; color transition 150 ms; on **Accept** success: background cross-fades to `success` and an inline check icon scales in (180 ms), then returns to idle after 1.2 s. Disabled state: 40% opacity, no hover, `cursor-not-allowed`. |
| **Card hover** | `whileHover={{ y: -2 }}`; border `border-slate-800` → `border-nx-cyan/50`; optional `--glow-cyan`; 150 ms. |
| **Compliance bar** | Width animates 480 ms expo; segment turns `danger` with a 1-shot shake (`x: [0,-3,3,0]`, 200 ms) on a critical flag. |
| **Reconnecting** | `ws-status` dot cycles amber ↔ dim at 1.2 s; returns to cyan with a single ring ripple on reconnect. |
| **Focus** | 2 px `--c-cyan` ring, 2 px offset (`focus-visible` only). |

### 4.3 Tailwind keyframes (`tailwind.config.ts` → `theme.extend`)
```ts
keyframes: {
  "risk-pulse": { "0%,100%": { boxShadow: "0 0 0 0 rgb(255 23 68 / 0.0)" },
                  "50%":     { boxShadow: "0 0 15px 2px rgb(255 23 68 / 0.5)" } },
  "fade-up":    { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
  "scan":       { from: { transform: "translateY(-100%)" }, to: { transform: "translateY(100%)" } },
},
animation: {
  "risk-pulse": "risk-pulse 1.2s ease-in-out infinite",
  "fade-up":    "fade-up 240ms cubic-bezier(0.16,1,0.3,1) both",
  "scan":       "scan 2.4s linear infinite",
},
```
Under `prefers-reduced-motion: reduce`: loops stop (`animation: none`), glow stays static, transitions ≤ 1 ms, 3D shows a static frame.

---

## 5. DESIGN SYSTEM ADAPTABILITY (`skillui` integration)

### 5.1 Single source of truth: `src/app/globals.css`
Tokens are stored as **space-separated RGB channels** so Tailwind opacity modifiers (`bg-surface/80`, `border-cyan-500/50`) work.
```css
@tailwind base; @tailwind components; @tailwind utilities;

:root {
  --c-void: 8 9 13;        --c-surface: 15 17 23;     --c-surface-2: 21 24 35;
  --c-border: 31 36 48;
  --c-cyan: 0 242 254;     --c-violet: 112 0 255;     --c-violet-fg: 157 107 255;
  --c-success: 0 230 118;  --c-warning: 255 179 0;    --c-danger: 255 23 68;
  --c-text: 248 250 252;   --c-text-2: 148 163 184;   --c-text-3: 100 116 139;  --c-text-3-aa: 124 138 160;
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --radius-card: 12px; --radius-ctl: 8px;

  /* shadcn/ui variable names -> NexusCX tokens */
  --background: var(--c-void);   --foreground: var(--c-text);
  --card: var(--c-surface);      --card-foreground: var(--c-text);
  --popover: var(--c-surface-2); --popover-foreground: var(--c-text);
  --primary: var(--c-cyan);      --primary-foreground: var(--c-void);
  --secondary: var(--c-surface-2); --secondary-foreground: var(--c-text);
  --muted: var(--c-surface-2);   --muted-foreground: var(--c-text-2);
  --accent: var(--c-violet);     --accent-foreground: var(--c-text);
  --destructive: var(--c-danger); --destructive-foreground: var(--c-text);
  --border: var(--c-border);     --input: var(--c-border);  --ring: var(--c-cyan);
}
html { color-scheme: dark; }
body { background: rgb(var(--c-void)); color: rgb(var(--c-text)); font-family: var(--font-sans), system-ui, sans-serif; }
.bg-nx-radial { background: radial-gradient(60% 50% at 20% 10%, rgb(var(--c-violet) / .22), transparent 70%),
                            radial-gradient(50% 40% at 80% 90%, rgb(var(--c-cyan) / .16), transparent 70%), rgb(var(--c-void)); }
@media (prefers-reduced-motion: reduce) { *,*::before,*::after { animation: none !important; transition-duration: 1ms !important; } }
```
Dark-only product: no light theme; `<html class="dark">` fixed.

### 5.2 `tailwind.config.ts` mapping
```ts
const rgb = (v: string) => `rgb(var(${v}) / <alpha-value>)`;
export default {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: { extend: {
    colors: {
      void: rgb("--c-void"), surface: rgb("--c-surface"), "surface-2": rgb("--c-surface-2"),
      nx: { cyan: rgb("--c-cyan"), violet: rgb("--c-violet"), "violet-fg": rgb("--c-violet-fg") },
      // Keep stock class names, brand values: the 500 shade of these hues becomes the brand token.
      emerald: { 500: rgb("--c-success") }, amber: { 500: rgb("--c-warning") },
      rose: { 500: rgb("--c-danger") }, cyan: { 500: rgb("--c-cyan") }, violet: { 500: rgb("--c-violet") },
      // shadcn
      background: rgb("--background"), foreground: rgb("--foreground"),
      card: { DEFAULT: rgb("--card"), foreground: rgb("--card-foreground") },
      popover: { DEFAULT: rgb("--popover"), foreground: rgb("--popover-foreground") },
      primary: { DEFAULT: rgb("--primary"), foreground: rgb("--primary-foreground") },
      secondary: { DEFAULT: rgb("--secondary"), foreground: rgb("--secondary-foreground") },
      muted: { DEFAULT: rgb("--muted"), foreground: rgb("--muted-foreground") },
      accent: { DEFAULT: rgb("--accent"), foreground: rgb("--accent-foreground") },
      destructive: { DEFAULT: rgb("--destructive"), foreground: rgb("--destructive-foreground") },
      border: rgb("--border"), input: rgb("--input"), ring: rgb("--ring"),
    },
    fontFamily: { sans: ["var(--font-sans)", "system-ui", "Noto Sans Devanagari", "sans-serif"],
                  mono: ["var(--font-mono)", "ui-monospace", "monospace"] },
    borderRadius: { card: "var(--radius-card)", ctl: "var(--radius-ctl)" },
    boxShadow: { "glow-cyan": "0 0 18px rgb(var(--c-cyan) / .35)", "glow-violet": "0 0 18px rgb(var(--c-violet) / .4)",
                 "glow-danger": "0 0 15px rgb(var(--c-danger) / .5)" },
    transitionTimingFunction: { expo: "cubic-bezier(0.16,1,0.3,1)" },
    // keyframes + animation: see §4.3
  } },
} satisfies import("tailwindcss").Config;
```
`npx shadcn@latest init` generates HSL-based variables; replace its `hsl(var(--x))` wrappers with `rgb(var(--x) / <alpha-value>)` and delete its generated `:root` color block in favour of §5.1. If the project is scaffolded with Tailwind v4, define the same tokens under `@theme inline { --color-void: rgb(var(--c-void)); … }`; token names stay identical.

### 5.3 Adopting a `skillui` / Dribbble layout in 6 steps
1. **Extract:** `skillui --url <reference> --mode ultra --out ./design-refs`.
2. **Take structure only** from the output (`DESIGN.md`, `references/LAYOUT.md`, `COMPONENTS.md`): grid, spacing rhythm, component anatomy, nav pattern.
3. **Discard foreign identity:** colors, fonts, logos, imagery, copy. Never reuse another brand's assets.
4. **Re-map by role**, not by hex:

| Foreign token role | NexusCX token |
|---|---|
| page background | `void` |
| card / panel | `surface` (+ `backdrop-blur-md`) |
| border / divider | `border` / `--c-border-soft` |
| primary brand / CTA | `nx-cyan` (`primary`) |
| secondary / accent | `nx-violet` (`accent`) |
| positive / warning / negative | `emerald-500` / `amber-500` / `rose-500` |
| heading / body / caption | `text` / `text-2` / `text-3-aa` |
| display font / mono font | Inter / JetBrains Mono |

5. **Keep the canvas:** the layout's page shell must render `<NeuralBackdrop />` as its first child and let content float above it on translucent `surface` cards (so a flat-background reference still gets the moving 3D layer).
6. **Verify conformance** (must produce no output):
```bash
# no raw hex/rgb colors outside the token file
grep -rEn "#[0-9a-fA-F]{3,8}\b|rgba?\(" src --include=*.tsx --include=*.ts --include=*.css | grep -v "globals.css"
# no non-token color utilities for brand semantics
grep -rEn "(bg|text|border)-(blue|indigo|purple|pink|green|red|yellow)-[0-9]{3}" src
```

### 5.4 Agent prompt for applying a new layout
> Read `design.md` and the extracted `design-refs/*/DESIGN.md`. Rebuild the reference layout using only NexusCX tokens (§5.3 table), shadcn components, and `<NeuralBackdrop />`. Do not copy colors, fonts or assets. Add motion per §4. Then run the §5.3 grep checks and a Playwright screenshot; report any deviation.

---

## 6. COMPONENT STYLE RECIPES (token-only)

| Component | Class recipe |
|---|---|
| Panel / card | `rounded-card border border-border bg-surface/80 backdrop-blur-md shadow-none transition-colors duration-150 ease-expo hover:border-nx-cyan/50` |
| Primary button | `rounded-ctl bg-nx-cyan text-void font-semibold px-4 h-9 transition-colors duration-150 hover:bg-nx-cyan/90 focus-visible:ring-2 ring-nx-cyan ring-offset-2 ring-offset-void` |
| Ghost / secondary button | `rounded-ctl border border-border text-foreground hover:bg-surface-2` |
| Status badge | `inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-mono uppercase tracking-widest` + `bg-emerald-500/10 text-emerald-500` / `bg-amber-500/10 text-amber-500` / `bg-rose-500/10 text-rose-500` (icon + label always present) |
| Risk card (heatmap) | base: `rounded-card border border-border p-4` + level classes `bg-emerald-500/10`, `bg-amber-500/10`, or `bg-rose-500/10 animate-risk-pulse` |
| Metric | `font-mono text-3xl font-extrabold tracking-tight tabular-nums text-foreground` |
| Code / JSON log | `font-mono text-xs text-[rgb(var(--c-text-3-aa))] bg-void/60 rounded-ctl p-3` |

Icons: `lucide-react`, 16/20 px, `stroke-width 1.75`, inherit `currentColor`.

---

## 7. VISUAL ACCEPTANCE CHECKLIST
- [ ] All colors trace to `globals.css` tokens (§5.3 grep returns nothing)
- [ ] Contrast ≥ 4.5:1 for all text under 18 px (axe-core via Playwright)
- [ ] 3D canvas ≤ 1500 particles, steady ≥ 55 FPS on integrated GPU, pauses on hidden tab
- [ ] `prefers-reduced-motion` yields a static frame and no looping animation
- [ ] Risk and compliance states readable without color (label or icon present)
- [ ] High-risk shockwave fires once per alert, with ≥ 2 s spacing
- [ ] No layout shift when live numbers change (`tabular-nums`, fixed-width metric slots)
