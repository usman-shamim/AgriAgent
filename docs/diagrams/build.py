#!/usr/bin/env python3
"""Build the AgriAgent diagram set.

The `.mmd` files are the source of truth. This script derives everything else:

  1. Renders every `*.mmd` to `*.svg` (for slides) and `*.png` (for quick viewing)
     via @mermaid-js/mermaid-cli.
  2. Builds `interactive.html` — a single offline page with zoom/pan for every
     diagram. Each SVG is hydrated inside its own Shadow DOM so that mermaid's
     repeated `id="my-svg"` and `color-N` ids cannot collide across diagrams.
  3. Verifies that every `.mmd` is embedded verbatim in README.md and fails
     loudly if the two have drifted apart.

Usage:
    python3 docs/diagrams/build.py            # render, build the gallery, check README
    python3 docs/diagrams/build.py --no-render # gallery + README check only
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
README = REPO / "README.md"
GALLERY = HERE / "interactive.html"

# Title + one-line description per diagram, used by the gallery and the README.
META: dict[str, tuple[str, str]] = {
    "overview": (
        "Overview",
        "The whole idea in one line: weather in, recipe computed, safety-gated, dispensed.",
    ),
    "system-architecture": (
        "System architecture",
        "The system in layers — presentation, agent core, deterministic core, contract, MQTT, actuation.",
    ),
    "agent-runtime": (
        "Agent runtime (reference)",
        "How the agent works in full: the Runner loop, all three turns, every tool call, and the safety branch.",
    ),
    "agent-runtime-slides": (
        "Agent runtime (stage version)",
        "The same story compressed to five lifelines so it is readable when projected.",
    ),
    "agent-composition": (
        "Agent composition",
        "Agents to tool wrappers to the shared handler registry to the engines. Yellow is LLM, green is deterministic.",
    ),
    "dispatch-lifecycle": (
        "Dispatch lifecycle",
        "Data flow of one dispatch: safety gate, MQTT, twin validation, per-pump tank state, events.",
    ),
    "contract-erd": (
        "Data model (ERD)",
        "The payload contract and engine outputs. There is no database — this is the MQTT data model.",
    ),
    "safety-gate": (
        "Safety gate",
        "Every guardrail and where each verdict exits: envelope checks, four recipe rules, the pump-cycle cap.",
    ),
}

STYLE = """
  :root {
    --bg:#0f1115; --card:#171a21; --fg:#e6e8eb; --muted:#9aa3ad;
    --line:#262b34; --accent:#4ade80;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--fg);
    font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
  }
  header { padding: 30px 24px 18px; border-bottom: 1px solid var(--line); }
  h1 { margin: 0 0 8px; font-size: 22px; letter-spacing: -0.01em; }
  header p { margin: 0; color: var(--muted); max-width: 78ch; }
  code { background: #22262e; padding: 1px 5px; border-radius: 4px; font-size: 0.9em; }
  nav {
    display: flex; flex-wrap: wrap; gap: 8px; padding: 14px 24px;
    border-bottom: 1px solid var(--line); position: sticky; top: 0;
    background: rgba(15,17,21,0.92); backdrop-filter: blur(8px); z-index: 5;
  }
  nav a {
    color: var(--fg); text-decoration: none; border: 1px solid var(--line);
    padding: 4px 11px; border-radius: 999px; font-size: 13px; white-space: nowrap;
  }
  nav a:hover { border-color: var(--accent); color: var(--accent); }
  main { padding: 24px; display: grid; gap: 28px; }
  section {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 12px; overflow: hidden; scroll-margin-top: 70px;
  }
  .head {
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 14px 16px; border-bottom: 1px solid var(--line);
  }
  .head h2 { margin: 0; font-size: 16px; flex: 1 1 260px; }
  .head p { margin: 0; color: var(--muted); font-size: 13px; flex: 1 1 100%; }
  .controls { display: flex; gap: 6px; align-items: center; }
  button {
    background: #20242c; color: var(--fg); border: 1px solid var(--line);
    border-radius: 8px; padding: 5px 11px; cursor: pointer; font-size: 13px;
  }
  button:hover { border-color: var(--accent); color: var(--accent); }
  .zoom-level {
    color: var(--muted); font-size: 12px; min-width: 46px;
    text-align: right; font-variant-numeric: tabular-nums;
  }
  .stage {
    position: relative; overflow: hidden; background: #fff;
    height: 74vh; min-height: 340px; cursor: grab; touch-action: none;
  }
  .stage.grabbing { cursor: grabbing; }
  .canvas { position: absolute; top: 0; left: 0; transform-origin: 0 0; will-change: transform; }
  .hint { padding: 10px 16px; color: var(--muted); font-size: 12px; border-top: 1px solid var(--line); }
  footer { padding: 20px 24px 44px; color: var(--muted); font-size: 13px; }
"""

SCRIPT = r"""
const MIN_SCALE = 0.1;
const MAX_SCALE = 20;

function setup(viewer) {
  const tpl = viewer.querySelector('template');
  const stage = viewer.querySelector('.stage');
  const host = viewer.querySelector('.canvas');
  if (!tpl || !stage || !host) return;

  // Shadow DOM isolates each diagram: mermaid emits id="my-svg" and color-N ids
  // in every file, so light-DOM inlining would let them collide across diagrams.
  const shadow = host.attachShadow({ mode: 'open' });
  shadow.innerHTML = tpl.innerHTML.trim();

  const svg = shadow.querySelector('svg');
  if (!svg) return;

  // Neutralise mermaid's responsive sizing so the transform fully controls scale.
  const styleAttr = svg.getAttribute('style');
  if (styleAttr) svg.removeAttribute('style');
  const box = svg.viewBox && svg.viewBox.baseVal;
  const w = (box && box.width) || svg.clientWidth || 1000;
  const h = (box && box.height) || svg.clientHeight || 700;
  svg.setAttribute('width', w);
  svg.setAttribute('height', h);
  svg.style.maxWidth = 'none';
  svg.style.transformOrigin = '0 0';

  let scale = 1;
  let tx = 0;
  let ty = 0;
  let dragging = false;
  let grabX = 0;
  let grabY = 0;

  const label = viewer.querySelector('.zoom-level');
  const apply = () => {
    host.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    if (label) label.textContent = Math.round(scale * 100) + '%';
  };

  const fit = () => {
    const pad = 20;
    const vw = Math.max(stage.clientWidth - pad * 2, 1);
    const vh = Math.max(stage.clientHeight - pad * 2, 1);
    scale = Math.min(vw / w, vh / h, 1);
    if (!isFinite(scale) || scale <= 0) scale = 1;
    tx = (stage.clientWidth - w * scale) / 2;
    ty = (stage.clientHeight - h * scale) / 2;
    apply();
  };

  // Zoom keeping the point under (px, py) pinned to the cursor.
  const zoomAt = (factor, px, py) => {
    const next = Math.min(MAX_SCALE, Math.max(MIN_SCALE, scale * factor));
    if (next === scale) return;
    tx = px - (px - tx) * (next / scale);
    ty = py - (py - ty) * (next / scale);
    scale = next;
    apply();
  };

  const zoomCentre = (factor) => zoomAt(factor, stage.clientWidth / 2, stage.clientHeight / 2);

  stage.addEventListener('wheel', (event) => {
    event.preventDefault();
    const rect = stage.getBoundingClientRect();
    zoomAt(Math.exp(-event.deltaY * 0.0015), event.clientX - rect.left, event.clientY - rect.top);
  }, { passive: false });

  stage.addEventListener('pointerdown', (event) => {
    dragging = true;
    try { stage.setPointerCapture(event.pointerId); } catch (err) { /* no-op */ }
    grabX = event.clientX - tx;
    grabY = event.clientY - ty;
    stage.classList.add('grabbing');
  });

  stage.addEventListener('pointermove', (event) => {
    if (!dragging) return;
    tx = event.clientX - grabX;
    ty = event.clientY - grabY;
    apply();
  });

  const endDrag = (event) => {
    if (!dragging) return;
    dragging = false;
    try { stage.releasePointerCapture(event.pointerId); } catch (err) { /* no-op */ }
    stage.classList.remove('grabbing');
  };
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);

  stage.addEventListener('dblclick', (event) => {
    const rect = stage.getBoundingClientRect();
    zoomAt(1.6, event.clientX - rect.left, event.clientY - rect.top);
  });

  const bind = (cls, fn) => {
    const el = viewer.querySelector('.' + cls);
    if (el) el.addEventListener('click', fn);
  };
  bind('in', () => zoomCentre(1.25));
  bind('out', () => zoomCentre(1 / 1.25));
  bind('one', () => zoomCentre(1 / scale));
  bind('fit', fit);

  apply();
  requestAnimationFrame(fit);
  window.addEventListener('resize', fit);

  // Keyboard support so the gallery is usable without a mouse.
  viewer.tabIndex = 0;
  viewer.addEventListener('keydown', (event) => {
    const step = 60;
    if (event.key === '+' || event.key === '=') { zoomCentre(1.25); }
    else if (event.key === '-' || event.key === '_') { zoomCentre(1 / 1.25); }
    else if (event.key === '0') { fit(); }
    else if (event.key === 'ArrowLeft') { tx += step; apply(); }
    else if (event.key === 'ArrowRight') { tx -= step; apply(); }
    else if (event.key === 'ArrowUp') { ty += step; apply(); }
    else if (event.key === 'ArrowDown') { ty -= step; apply(); }
    else { return; }
    event.preventDefault();
  });
}

document.querySelectorAll('.viewer').forEach(setup);
"""

SECTION = """  <section class="viewer" id="{slug}">
    <div class="head">
      <h2>{title}</h2>
      <div class="controls">
        <button class="out" title="Zoom out" aria-label="Zoom out">&minus;</button>
        <span class="zoom-level">100%</span>
        <button class="in" title="Zoom in" aria-label="Zoom in">+</button>
        <button class="one" title="Show at 100%">100%</button>
        <button class="fit" title="Fit to view">Fit</button>
      </div>
      <p>{desc}</p>
    </div>
    <div class="stage">
      <div class="canvas"></div>
    </div>
    <div class="hint">Scroll to zoom &middot; drag to pan &middot; double-click to zoom in &middot; arrow keys to pan, +/- to zoom, 0 to fit</div>
    <template>{svg}</template>
  </section>
"""


def run(cmd: list[str], **kw) -> None:
    subprocess.run(cmd, check=True, **kw)


def find_browser() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    return None


def render(mmd_files: list[Path]) -> None:
    browser = find_browser()
    if not browser:
        print("ERROR: no Chromium found. Install one or set PUPPETEER_EXECUTABLE_PATH.", file=sys.stderr)
        raise SystemExit(1)
    print(f"browser: {browser}")

    env = {"PUPPETEER_EXECUTABLE_PATH": browser}
    import os

    merged = {**os.environ, **env}
    for mmd in mmd_files:
        base = mmd.with_suffix("")
        run(["npx", "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd), "-o", f"{base}.svg"],
            env=merged, stdout=subprocess.DEVNULL)
        run(["npx", "-y", "@mermaid-js/mermaid-cli", "-i", str(mmd), "-o", f"{base}.png", "-b", "white", "-s", "2"],
            env=merged, stdout=subprocess.DEVNULL)
        print(f"  rendered {mmd.stem}.svg + {mmd.stem}.png")


def extract_svg(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find("<svg")
    end = text.rfind("</svg>")
    if start == -1 or end == -1:
        raise ValueError(f"no <svg> element found in {path}")
    return text[start:end + len("</svg>")]


def build_gallery(stems: list[str]) -> None:
    nav: list[str] = []
    sections: list[str] = []
    for stem in stems:
        title, desc = META.get(stem, (stem.replace("-", " ").title(), ""))
        nav.append(f'<a href="#{stem}">{title}</a>')
        sections.append(
            SECTION.format(slug=stem, title=title, desc=desc, svg=extract_svg(HERE / f"{stem}.svg"))
        )

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>AgriAgent — interactive diagrams ({len(stems)})</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n"
        "<header>\n"
        "  <h1>AgriAgent — interactive diagrams</h1>\n"
        "  <p>Every diagram in the project, rendered from <code>docs/diagrams/*.mmd</code> with zoom and pan. "
        "Scroll to zoom, drag to move, double-click to zoom in. This page is generated by "
        "<code>docs/diagrams/build.py</code> — edit the <code>.mmd</code> sources, never this file. "
        "It is fully offline: no CDN, no server.</p>\n"
        "</header>\n"
        f"<nav>\n  {' '.join(nav)}\n</nav>\n"
        "<main>\n" + "\n".join(sections) + "\n</main>\n"
        f"<footer>Generated {stamp} from {len(stems)} Mermaid sources.</footer>\n"
        f"<script>{SCRIPT}</script>\n</body>\n</html>\n"
    )
    GALLERY.write_text(html, encoding="utf-8")
    print(f"  built {GALLERY.relative_to(REPO)} ({GALLERY.stat().st_size // 1024} KB, {len(stems)} diagrams)")


FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(?:[ \t]*id:[^\n]*\n)+---[ \t]*\n")


def diagram_body(path: Path) -> str:
    """The .mmd content with IDE-generated frontmatter stripped.

    The IDE registers each .mmd as a Mermaid diagram and writes a YAML block
    holding only a stable `id:` field. That is valid Mermaid but meaningless in
    the README, so it is removed before comparing or embedding.
    """
    return FRONTMATTER_RE.sub("", path.read_text(encoding="utf-8")).strip()


def check_readme(mmd_files: list[Path]) -> bool:
    if not README.exists():
        print("ERROR: README.md not found", file=sys.stderr)
        return False
    readme = README.read_text(encoding="utf-8")
    print("README embed check:")
    missing: list[str] = []
    for mmd in mmd_files:
        body = diagram_body(mmd)
        if body in readme:
            print(f"  ok       {mmd.stem}")
        else:
            print(f"  DRIFTED  {mmd.stem}  (source is not embedded verbatim in README.md)")
            missing.append(mmd.stem)
    if missing:
        print(
            "\nREADME is out of sync with: " + ", ".join(missing)
            + "\nCopy each .mmd body into README.md inside a ```mermaid fence.",
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-render", action="store_true",
                        help="skip mermaid-cli rendering (rebuild gallery + README check only)")
    args = parser.parse_args()

    sources = sorted(HERE.glob("*.mmd"), key=lambda p: p.name)
    if not sources:
        print("ERROR: no .mmd files found", file=sys.stderr)
        return 1

    unknown = [p.stem for p in sources if p.stem not in META]
    if unknown:
        print(f"WARNING: no META entry for {', '.join(unknown)} — they will render with a derived title.",
              file=sys.stderr)

    print(f"sources: {len(sources)} .mmd files")
    if not args.no_render:
        print("rendering:")
        render(sources)

    print("gallery:")
    build_gallery([p.stem for p in sources])

    ok = check_readme(sources)
    print("\nBUILD OK" if ok else "\nBUILD FAILED — README is out of sync")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
