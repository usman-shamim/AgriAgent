/* AgriAgent hackathon pitch deck — built with pptxgenjs per the pptx skill.
 *
 * Design system
 *   Palette "Forest & Moss": forest 2C5F2D (dominant), moss 97BC62 (support),
 *   tint E7F0E2 (card fills), ink 1C2B1D, muted 5C6B5D. Dark sandwich: slides
 *   1 and 8 on forest, content slides on white.
 *   Motif: a Material icon inside a moss circle beside every kicker.
 *   Fonts: Cambria (headers) + Calibri (body) + Courier New (code) — all
 *   metric-safe for QA.
 *   Layout: LAYOUT_WIDE 13.33 x 7.5 in, 0.6 in margins.
 */

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const {
  MdEco, MdWbSunny, MdTune, MdSmartToy, MdCalculate,
  MdPlayCircleOutline, MdBlock, MdTrendingUp,
} = require("react-icons/md");

const ASSETS = path.join(__dirname, "assets");

// ---- palette ----
const FOREST = "2C5F2D";
const FOREST_DARK = "234D24";
const MOSS = "97BC62";
const TINT = "E7F0E2";
const INK = "1C2B1D";
const MUTED = "5C6B5D";
const WHITE = "FFFFFF";
const TERM_BG = "1B2A1C";
const TERM_FG = "B7D9A8";

const HEAD = "Cambria";
const BODY = "Calibri";
const MONO = "Courier New";

// ---- helpers ----
async function iconPng(Icon, color, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(
    React.createElement(Icon, { size, color: "#" + color })
  );
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

async function imageSize(file) {
  const meta = await sharp(file).metadata();
  return { w: meta.width, h: meta.height };
}

// Fit an image inside a box, centered, preserving aspect.
function fitImage(img, boxW, boxH) {
  const scale = Math.min(boxW / img.w, boxH / img.h);
  return { w: img.w * scale, h: img.h * scale };
}

function kicker(slide, iconData, text, dark = false) {
  slide.addShape("ellipse", {
    x: 0.6, y: 0.5, w: 0.52, h: 0.52,
    fill: { color: dark ? MOSS : TINT },
  });
  slide.addImage({
    data: iconData,
    x: 0.6 + 0.13, y: 0.5 + 0.13, w: 0.26, h: 0.26,
  });
  slide.addText(text, {
    x: 1.28, y: 0.5, w: 8.5, h: 0.52, margin: 0,
    fontFace: BODY, fontSize: 13, bold: true,
    color: dark ? MOSS : FOREST, charSpacing: 3,
    align: "left", valign: "middle",
  });
}

function title(slide, text, dark = false, w = 12.1) {
  slide.addText(text, {
    x: 0.6, y: 1.12, w, h: 0.85, margin: 0,
    fontFace: HEAD, fontSize: 38, bold: true,
    color: dark ? WHITE : INK, align: "left", valign: "top",
  });
}

function notes(slide, text) {
  slide.addNotes(text);
}

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
  pres.author = "AgriAgent";
  pres.title = "AgriAgent — hackathon pitch";

  // Pre-render icons (forest on tint for light slides; white on moss for dark).
  const icoLight = {
    problem: await iconPng(MdWbSunny, FOREST),
    scope: await iconPng(MdTune, FOREST),
    arch: await iconPng(MdSmartToy, FOREST),
    proof: await iconPng(MdCalculate, FOREST),
    live: await iconPng(MdPlayCircleOutline, FOREST),
    safety: await iconPng(MdBlock, FOREST),
  };
  const icoTitle = await iconPng(MdEco, FOREST_DARK);
  const icoImpact = await iconPng(MdTrendingUp, FOREST_DARK);

  const imgOverview = await imageSize(path.join(ASSETS, "overview.png"));
  const imgRuntime = await imageSize(path.join(ASSETS, "agent-runtime-deck.png"));
  const imgDispatch = await imageSize(path.join(ASSETS, "demo-dispatch.png"));
  const imgRefused = await imageSize(path.join(ASSETS, "demo-refused.png"));

  // ============================ SLIDE 1 — TITLE (dark)
  {
    const s = pres.addSlide();
    s.background = { color: FOREST };

    s.addShape("ellipse", { x: 6.165, y: 1.15, w: 1.0, h: 1.0, fill: { color: MOSS } });
    s.addImage({ data: icoTitle, x: 6.165 + 0.25, y: 1.15 + 0.25, w: 0.5, h: 0.5 });

    s.addText("AgriAgent", {
      x: 0.6, y: 2.35, w: 12.13, h: 1.3, margin: 0,
      fontFace: HEAD, fontSize: 72, bold: true, color: WHITE,
      align: "center", valign: "middle",
    });
    s.addText("Biopesticides that survive the sun", {
      x: 0.6, y: 3.7, w: 12.13, h: 0.55, margin: 0,
      fontFace: HEAD, fontSize: 26, italic: true, color: MOSS,
      align: "center", valign: "middle",
    });
    s.addText(
      "Autonomous SCADA for on-demand biopesticide formulation — Perception → Formulation → Safety → Actuator",
      {
        x: 1.8, y: 4.45, w: 9.73, h: 0.5, margin: 0,
        fontFace: BODY, fontSize: 15, color: "DDE8D8", align: "center", valign: "middle",
      }
    );
    s.addText("Hackathon pitch · 3 minutes", {
      x: 0.6, y: 6.55, w: 12.13, h: 0.4, margin: 0,
      fontFace: BODY, fontSize: 12, color: "A8C4A0", align: "center", valign: "middle",
    });

    notes(
      s,
      "0:00 — Good afternoon. Biopesticides are safe for farmers, consumers, and export " +
      "compliance — but sunlight destroys them within hours. AgriAgent formulates them " +
      "on demand, at the moment of spraying, from live weather. One decision, made " +
      "correctly, every cycle."
    );
  }

  // ============================ SLIDE 2 — THE PROBLEM (stat callouts)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.problem, "THE PROBLEM");
    title(s, "Sunlight destroys the cure");

    const cards = [
      { n: "8.8 h", l: "Bright dry midday", d: "UV 9.2 · 38 °C · 32 % RH" },
      { n: "37 h", l: "Overcast morning", d: "UV 2.1 · 24 °C · 75 % RH" },
      { n: "72 h", l: "Night", d: "UV 0 · 18 °C · 85 % RH" },
    ];
    cards.forEach((c, i) => {
      const x = 0.6 + i * 4.18;
      s.addShape("roundRect", {
        x, y: 2.35, w: 3.85, h: 2.6, rectRadius: 0.12,
        fill: { color: TINT },
      });
      s.addText(c.n, {
        x, y: 2.55, w: 3.85, h: 1.1, margin: 0,
        fontFace: HEAD, fontSize: 60, bold: true, color: FOREST,
        align: "center", valign: "middle",
      });
      s.addText(c.l, {
        x, y: 3.7, w: 3.85, h: 0.4, margin: 0,
        fontFace: BODY, fontSize: 16, bold: true, color: INK,
        align: "center", valign: "middle",
      });
      s.addText(c.d, {
        x, y: 4.1, w: 3.85, h: 0.35, margin: 0,
        fontFace: BODY, fontSize: 12, color: MUTED,
        align: "center", valign: "middle",
      });
    });

    s.addText(
      [
        { text: "Bt half-life on the leaf — an 8× swing in a single day. ", options: { bold: true } },
        { text: "A tank mixed at dawn is largely spent by afternoon, so farmers spray more often: higher cost, and the biological advantage is lost anyway." },
      ],
      {
        x: 0.6, y: 5.45, w: 12.13, h: 0.9, margin: 0,
        fontFace: BODY, fontSize: 16, color: INK, align: "left", valign: "top",
      }
    );

    notes(
      s,
      "0:20 — The active ingredient is destroyed by exactly the conditions that make " +
      "spraying useful. Same crop, same day: half-life swings from about nine hours at " +
      "midday to three days at night. A fixed pre-mixed tank is guaranteed wrong."
    );
  }

  // ============================ SLIDE 3 — ONE DECISION (overview diagram)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.scope, "SCOPE");
    title(s, "Not a platform. One decision.");

    const ov = fitImage(imgOverview, 12.13, 2.9);
    s.addImage({
      path: path.join(ASSETS, "overview.png"),
      x: 0.6 + (12.13 - ov.w) / 2, y: 2.1, w: ov.w, h: ov.h,
    });

    const beats = [
      {
        h: "Minimum data",
        b: "UV index, temperature, humidity — pulled from live weather. Farmers never hand-enter data.",
      },
      {
        h: "Actionable output",
        b: "One MQTT payload: recipe → safety gate → exact pump volumes → the twin dispenses them.",
      },
      {
        h: "Validated savings",
        b: "Kinetics models tie the dynamic mix to the 90 % synthetic-volume-reduction target.",
      },
    ];
    beats.forEach((bt, i) => {
      const x = 0.6 + i * 4.18;
      s.addShape("roundRect", {
        x, y: 5.15, w: 3.85, h: 1.85, rectRadius: 0.12,
        fill: { color: TINT },
      });
      s.addText(bt.h, {
        x: x + 0.25, y: 5.35, w: 3.35, h: 0.4, margin: 0,
        fontFace: BODY, fontSize: 16, bold: true, color: FOREST,
        align: "left", valign: "top",
      });
      s.addText(bt.b, {
        x: x + 0.25, y: 5.78, w: 3.35, h: 1.1, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK,
        align: "left", valign: "top",
      });
    });

    notes(
      s,
      "0:45 — We deliberately dropped pest detection and yield prediction. The whole " +
      "build answers one question: given the weather right now, what is the exact mix " +
      "of biopesticide, UV stabilizer, and surfactant? Weather in, recipe out, " +
      "safety-gated, dispensed."
    );
  }

  // ============================ SLIDE 4 — HOW IT WORKS (runtime diagram + roles)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.arch, "ARCHITECTURE");
    title(s, "The LLM picks the tool. Python does the math.");

    const rt = fitImage(imgRuntime, 7.4, 4.9);
    s.addImage({
      path: path.join(ASSETS, "agent-runtime-deck.png"),
      x: 0.6, y: 2.15, w: rt.w, h: rt.h,
    });

    const roles = [
      { h: "Perception", b: "reads telemetry, computes the degradation half-life" },
      { h: "Formulation", b: "exact litre setpoints for all four channels" },
      { h: "Safety", b: "machine-readable rejections — nothing unsafe is published" },
      { h: "SCADA", b: "pump runtimes, MQTT dispatch at QoS 1" },
    ];
    roles.forEach((r, i) => {
      const y = 2.3 + i * 1.02;
      s.addShape("ellipse", { x: 8.35, y: y + 0.06, w: 0.16, h: 0.16, fill: { color: MOSS } });
      s.addText(r.h, {
        x: 8.67, y, w: 4.05, h: 0.32, margin: 0,
        fontFace: BODY, fontSize: 15, bold: true, color: FOREST,
        align: "left", valign: "top",
      });
      s.addText(r.b, {
        x: 8.67, y: y + 0.32, w: 4.05, h: 0.6, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: INK,
        align: "left", valign: "top",
      });
    });

    s.addText(
      "OpenAI Agents SDK · native handoffs · every number from deterministic engines — the model never does arithmetic",
      {
        x: 0.6, y: 6.85, w: 12.13, h: 0.4, margin: 0,
        fontFace: BODY, fontSize: 12, italic: true, color: MUTED,
        align: "left", valign: "middle",
      }
    );

    notes(
      s,
      "1:05 — Three named agents wired with native handoffs. The LLM decides which tool " +
      "to call and when to hand off — that is all it decides. Every number you will see " +
      "today comes from deterministic Python engines, validated by Pydantic at every " +
      "boundary."
    );
  }

  // ============================ SLIDE 5 — DETERMINISTIC (formulas + selftest)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.proof, "PROOF");
    title(s, "The chemistry is not hallucinated");

    // Left: formulas card — one formula per entry, split only at logical points
    s.addShape("roundRect", {
      x: 0.6, y: 2.15, w: 6.1, h: 4.35, rectRadius: 0.12, fill: { color: TINT },
    });
    s.addText("Confirmed kinetics", {
      x: 0.95, y: 2.4, w: 5.4, h: 0.35, margin: 0,
      fontFace: BODY, fontSize: 14, bold: true, color: FOREST, align: "left",
    });
    s.addText(
      [
        { text: "k = k₀·(1+α·UV)", options: { breakLine: true } },
        { text: "  ·e^(−(Ea/R)(1/T−1/T₀))", options: { breakLine: true, color: MUTED } },
        { text: "UV photolysis × Arrhenius thermal · k₀ = ln(2)/48 h⁻¹", options: { breakLine: true, fontSize: 11, color: MUTED, fontFace: BODY } },
        { text: "", options: { breakLine: true, fontSize: 7 } },
        { text: "lignin = min(3.0 %, 0.25 % + 0.25 %·UV)", options: { breakLine: true } },
        { text: "UV stabilizer, capped at the solubility limit", options: { breakLine: true, fontSize: 11, color: MUTED, fontFace: BODY } },
        { text: "", options: { breakLine: true, fontSize: 7 } },
        { text: "surfactant = min(0.20 %,", options: { breakLine: true } },
        { text: "  0.05 %·(1+1.2(1−RH/100))·(T/293.15)^1.5)", options: { breakLine: true } },
        { text: "wetting agent, capped against phytotoxicity", options: { breakLine: true, fontSize: 11, color: MUTED, fontFace: BODY } },
        { text: "", options: { breakLine: true, fontSize: 7 } },
        { text: "runtime = volume ÷ flow", options: { breakLine: true } },
        { text: "0.01 / 0.01 / 0.01 / 0.05 L/s — never accepted from a caller", options: { fontSize: 11, color: MUTED, fontFace: BODY } },
      ],
      {
        x: 0.95, y: 2.8, w: 5.5, h: 3.5, margin: 0,
        fontFace: MONO, fontSize: 12.5, color: INK, align: "left", valign: "top",
      }
    );

    // Right: terminal card with the real selftest excerpt
    s.addShape("roundRect", {
      x: 7.05, y: 2.15, w: 5.68, h: 4.35, rectRadius: 0.12, fill: { color: TERM_BG },
    });
    s.addText(
      [
        { text: "$ python src/mcp_server_scada.py --selftest", options: { color: "7FA87C", breakLine: true } },
        { text: "  [PASS] k_baseline:   got=0.078508", options: { breakLine: true } },
        { text: "  [PASS] half_life:    got=8.829", options: { breakLine: true } },
        { text: "  [PASS] bio_l:        got=0.04", options: { breakLine: true } },
        { text: "  [PASS] lignin_pct:   got=2.55", options: { breakLine: true } },
        { text: "  [PASS] surf_pct_capped: got=0.0993", options: { breakLine: true } },
        { text: "  [PASS] rejects_overcap_surfactant: True", options: { breakLine: true } },
        { text: "  [PASS] pump1_duration: got=4.0", options: { breakLine: true } },
        { text: "  [PASS] all_runtimes_under_30s: True", options: { breakLine: true } },
        { text: "  [PASS] lignin_cap:   got=3.0", options: { breakLine: true } },
        { text: "  …  21 checks", options: { breakLine: true, color: "7FA87C" } },
        { text: "SELFTEST PASSED", options: { bold: true, color: "D8F3C6" } },
      ],
      {
        x: 7.35, y: 2.45, w: 5.1, h: 3.75, margin: 0,
        fontFace: MONO, fontSize: 11.5, color: TERM_FG, align: "left", valign: "top",
      }
    );

    notes(
      s,
      "1:25 — This is the credibility anchor. The engines are pure standard-library " +
      "math — zero third-party dependencies — and the self-test gate proves the " +
      "numbers on every run: 21 checks, from the degradation constant to the " +
      "guardrail rejections."
    );
  }

  // ============================ SLIDE 6 — LIVE DEMO (screenshot left, numbers right)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.live, "LIVE");
    title(s, "One dispatch, end to end");

    const dp = fitImage(imgDispatch, 8.55, 4.75);
    s.addImage({
      path: path.join(ASSETS, "demo-dispatch.png"),
      x: 0.6, y: 2.25, w: dp.w, h: dp.h,
    });

    const facts = [
      { h: "The recipe", b: "bio 0.0400 L · stabilizer 0.01275 L · surfactant 0.0005 L · water 0.44675 L" },
      { h: "The runtimes", b: "4.000 s · 1.275 s · 0.050 s · 8.935 s — computed from the calibrated flow table" },
      { h: "The feedback", b: "tank state published after every pump, then DISPATCH_COMPLETE" },
    ];
    facts.forEach((f, i) => {
      const y = 2.45 + i * 1.35;
      s.addText(f.h, {
        x: 9.55, y, w: 3.2, h: 0.3, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: FOREST, align: "left",
      });
      s.addText(f.b, {
        x: 9.55, y: y + 0.3, w: 3.2, h: 0.95, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK, align: "left", valign: "top",
      });
    });

    notes(
      s,
      "1:45 — [SWITCH TO THE LIVE DASHBOARD] Watch the tanks fall as each pump " +
      "actuates — state is published after every pump, not just at the end. The " +
      "recipe and runtimes you see are exactly what the payload commanded. " +
      "[click Dispatch now, wait ~2 s, point at the falling bars and the " +
      "DISPATCH_COMPLETE event]"
    );
  }

  // ============================ SLIDE 7 — THE REFUSAL (text left, screenshot right)
  {
    const s = pres.addSlide();
    s.background = { color: WHITE };
    kicker(s, icoLight.safety, "SAFETY");
    title(s, "Refusing is the feature");

    const rf = fitImage(imgRefused, 8.35, 4.75);
    s.addImage({
      path: path.join(ASSETS, "demo-refused.png"),
      x: 12.73 - rf.w, y: 2.25, w: rf.w, h: rf.h,
    });

    const points = [
      { h: "10 L batch requested", b: "pump 1 runtime 80.0 s, pump 4 runtime 178.7 s — both breach the 30 s thermal cap" },
      { h: "Blocked before you can click", b: "the dispatch button disables itself while the recipe fails validation" },
      { h: "Nothing is published", b: "no MQTT payload, tanks do not move — the rejection is machine-readable" },
    ];
    points.forEach((p, i) => {
      const y = 2.45 + i * 1.35;
      s.addText(p.h, {
        x: 0.6, y, w: 3.35, h: 0.3, margin: 0,
        fontFace: BODY, fontSize: 14, bold: true, color: FOREST, align: "left",
      });
      s.addText(p.b, {
        x: 0.6, y: y + 0.3, w: 3.35, h: 0.95, margin: 0,
        fontFace: BODY, fontSize: 12, color: INK, align: "left", valign: "top",
      });
    });

    notes(
      s,
      "2:10 — [SET BATCH TO 10 L ON THE LIVE DASHBOARD] Now the dangerous request. " +
      "The button disables itself before I can even try, with the exact rule that " +
      "failed. A system that refuses is what makes unattended dosing acceptable — " +
      "this matters more than the success case."
    );
  }

  // ============================ SLIDE 8 — IMPACT + HONEST LIMITS (dark)
  {
    const s = pres.addSlide();
    s.background = { color: FOREST };
    kicker(s, icoImpact, "IMPACT", true);
    title(s, "One decision, made correctly, every cycle", true);

    const stats = [
      { n: "90 %", l: "synthetic-volume reduction target" },
      { n: "PKR 45,000", l: "per-acre saving (cost-model estimate)" },
      { n: "7–14×", l: "half-life extension, lignin encapsulation (literature)" },
    ];
    stats.forEach((st, i) => {
      const x = 0.6 + i * 4.18;
      s.addText(st.n, {
        x, y: 2.3, w: 3.85, h: 0.95, margin: 0,
        fontFace: HEAD, fontSize: 44, bold: true, color: MOSS,
        align: "center", valign: "middle",
      });
      s.addText(st.l, {
        x: x + 0.3, y: 3.3, w: 3.25, h: 0.75, margin: 0,
        fontFace: BODY, fontSize: 13, color: "DDE8D8",
        align: "center", valign: "top",
      });
    });

    s.addShape("roundRect", {
      x: 0.6, y: 4.55, w: 12.13, h: 1.95, rectRadius: 0.12,
      fill: { color: FOREST_DARK },
    });
    s.addText("Honest limits — targets, not measurements", {
      x: 0.95, y: 4.8, w: 11.4, h: 0.35, margin: 0,
      fontFace: BODY, fontSize: 14, bold: true, color: MOSS, align: "left",
    });
    s.addText(
      [
        { text: "The 90 % and PKR figures are literature-backed targets and cost-model estimates — not results this build measured.", options: { bullet: true, breakLine: true } },
        { text: "The physical ESP32 rig is not built: the digital twin is the demo target, and firmware inherits the same MQTT contract.", options: { bullet: true, breakLine: true } },
        { text: "The twin simulates timed pump actuation and tank depletion — not fluid mechanics.", options: { bullet: true } },
      ],
      {
        x: 0.95, y: 5.2, w: 11.4, h: 1.2, margin: 0,
        fontFace: BODY, fontSize: 12.5, color: WHITE,
        align: "left", valign: "top", paraSpaceAfter: 6,
      }
    );

    s.addText("AgriAgent · Autonomous SCADA for on-demand biopesticide formulation", {
      x: 0.6, y: 6.85, w: 12.13, h: 0.4, margin: 0,
      fontFace: BODY, fontSize: 12, color: "A8C4A0", align: "center", valign: "middle",
    });

    notes(
      s,
      "2:35 — The commercial case: up to 90 % less synthetic volume, about PKR 45,000 " +
      "per acre, and export corridors protected by residue compliance. And the honest " +
      "limits, because the numbers we can prove live are the kinetics, the recipe, " +
      "the guardrail, and the dispatch — the savings are literature-backed targets. " +
      "Thank you."
    );
  }

  const out = path.join(__dirname, "AgriAgent-Pitch.pptx");
  await pres.writeFile({ fileName: out });
  console.log("wrote " + out);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
