/* whiteboard - explainer that draws itself: boxes, arrows, lists and circles in marker strokes. */
(function () {
  const { C, P, eo, sp, L } = VT;
  const INK = () => VT.col('ink'), RED = () => VT.col('accent');
  function stroke(svg, d, color, w = 0.55) { return svg.add('path', { d, stroke: color, 'stroke-width': w * VT.U, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }); }
  function hand(layer, str, sizeU, color, box, weight = 700) {
    return VT.text(layer, str, { box, size: sizeU, font: 'hand', weight, color: color || INK(), lh: 1.15, valign: 'middle' });
  }
  function titleOf(s, layer) {
    if (!s.title) return null;
    const z = VT.Z.head;
    return VT.text(layer, s.title, { box: { x: z.x, y: z.y, w: z.w, h: z.h * 0.8 }, size: 8.5, font: 'display', weight: 900, color: INK(), valign: 'middle' });
  }
  VT.template({
    theme: {
      palette: { bg: '#F7F6F0', ink: '#1F2A44', accent: '#E24B4A', blue: '#2F6FDF', paper: '#FFFFFF', deep: 'rgba(31,42,68,.18)', text: '#1F2A44', muted: '#5F6B85', grid: 'rgba(31,42,68,.06)' },
      captions: { style: 'karaoke', color: '#1F2A44', hl: '#E24B4A', shadow: 'rgba(0,0,0,0)', font: 'display' },
      transition: 'fade', sfx: { transition: 'page', transitionGain: -20 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background-image:linear-gradient(${VT.col('grid')} 1px,transparent 1px),linear-gradient(90deg,${VT.col('grid')} 1px,transparent 1px);background-size:${6 * U}px ${6 * U}px`);
      return null;
    },
    scenes: {
      title: {
        build(s, layer) {
          const z = VT.Z.full, U = VT.U;
          const box = { x: z.x + z.w * 0.06, y: z.y + z.h * 0.3, w: z.w * 0.88, h: z.h * 0.3 };
          const t = VT.text(layer, s.text || '', { box, size: 12, font: 'hand', weight: 700, color: INK(), valign: 'middle', lh: 1.1 });
          const svg = VT.svg(layer);
          const at = VT.time(s.at, s.start + 0.2), ua = VT.time(s.underlineAt, at + 0.8);
          const r = t.getBoundingClientRect();
          const u = stroke(svg, VT.rough.underline(box.x + box.w * 0.15, box.x + box.w * 0.85, box.y + box.h / 2 + t.offsetHeight / 2 + 2 * U, 3), RED(), 0.9);
          VT.cue(at, 'marker', { dur: 0.8, gain: -16 }); VT.cue(ua, 'marker', { dur: 0.4, gain: -16 });
          return (tt) => {
            const p = eo(P(tt, at, 0.8));
            t.style.clipPath = VT.dir === 'rtl' ? `inset(0 0 0 ${(1 - p) * 100}%)` : `inset(0 ${(1 - p) * 100}% 0 0)`;
            VT.drawPath(u, eo(P(tt, ua, 0.4)));
          };
        },
      },
      diagram: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, nodes = s.nodes || [];
          const head = titleOf(s, layer);
          const body = s.title ? Z.body : Z.full;
          const n = Math.max(1, nodes.length);
          let layout = s.layout || (VT.orient === 'landscape' && n <= 4 ? 'horizontal' : n >= 4 && n <= 6 && s.cycle ? 'cycle' : 'vertical');
          const svg = VT.svg(layer);
          const boxes = [];
          if (layout === 'horizontal') {
            const cols = VT.cols(VT.inset(body, 2), n, 8);
            cols.forEach((c) => boxes.push({ x: c.x, y: c.y + c.h * 0.3, w: c.w, h: Math.min(c.h * 0.4, 22 * U) }));
          } else if (layout === 'cycle') {
            const cx = body.x + body.w / 2, cy = body.y + body.h / 2, R = Math.min(body.w, body.h) * 0.34, bw = Math.min(34 * U, body.w * 0.4), bh = 14 * U;
            nodes.forEach((_, i) => { const a = -Math.PI / 2 + (i / n) * Math.PI * 2; boxes.push({ x: cx + Math.cos(a) * R - bw / 2, y: cy + Math.sin(a) * R - bh / 2, w: bw, h: bh }); });
          } else {
            const rows = VT.rows(VT.clampW(VT.inset(body, 2), 80), n, 9);
            rows.forEach((r) => { const h = Math.min(r.h, 20 * U); boxes.push({ x: r.x + r.w * 0.1, y: r.y + (r.h - h) / 2, w: r.w * 0.8, h }); });
          }
          const items = nodes.map((nd, i) => {
            const b = boxes[i], at = VT.time(nd.at, s.start + 0.5 + i * 1.2);
            const path = stroke(svg, VT.rough.rect(b.x, b.y, b.w, b.h, i + 1), nd.color === 'accent' ? RED() : INK());
            const t = hand(layer, nd.text, 6.8, nd.color === 'accent' ? RED() : INK(), VT.inset(b, 1.2));
            VT.cue(at, 'marker', { dur: 0.5, gain: -17 });
            let arrow = null;
            if (i > 0 && s.arrows !== false) {
              const a = boxes[i - 1];
              let d;
              if (layout === 'horizontal') { const f = VT.dir === 'rtl'; d = VT.rough.arrow(f ? a.x - 1.5 * U : a.x + a.w + 1.5 * U, a.y + a.h / 2, f ? b.x + b.w + 1.5 * U : b.x - 1.5 * U, b.y + b.h / 2, i); }
              else if (layout === 'cycle') { const ax = a.x + a.w / 2, ay = a.y + a.h / 2, bx = b.x + b.w / 2, by = b.y + b.h / 2, k = 0.55; d = VT.rough.arrow(ax + (bx - ax) * (1 - k) / 1, ay + (by - ay) * (1 - k), ax + (bx - ax) * k, ay + (by - ay) * k, i); }
              else d = VT.rough.arrow(a.x + a.w / 2, a.y + a.h + 1.5 * U, b.x + b.w / 2, b.y - 1.5 * U, i);
              arrow = stroke(svg, d, INK(), 0.5);
            }
            return { at, path, t, arrow };
          });
          if (layout === 'cycle' && n > 2 && s.arrows !== false) {
            const a = boxes[n - 1], b = boxes[0], ax = a.x + a.w / 2, ay = a.y + a.h / 2, bx = b.x + b.w / 2, by = b.y + b.h / 2;
            items[0].arrow = stroke(svg, VT.rough.arrow(ax + (bx - ax) * 0.45, ay + (by - ay) * 0.45, ax + (bx - ax) * 0.55, ay + (by - ay) * 0.55, 99), INK(), 0.5);
            items[0].arrowAt = items[n - 1].at + 0.8;
          }
          let circle = null, cAt = 0;
          if (s.circle && boxes[s.circle.index] != null) {
            const b = boxes[s.circle.index]; cAt = VT.time(s.circle.at, items[items.length - 1].at + 1);
            circle = stroke(svg, VT.rough.ellipse(b.x + b.w / 2, b.y + b.h / 2, b.w * 0.62, b.h * 0.9, 5), RED(), 0.8);
            VT.cue(cAt, 'marker', { dur: 0.6, gain: -15 });
          }
          return (tt) => {
            if (head) { head.style.opacity = C((tt - s.start) / 0.3); }
            items.forEach((it, i) => {
              VT.drawPath(it.path, eo(P(tt, it.at, 0.5)));
              it.t.style.opacity = P(tt, it.at + 0.25, 0.3);
              if (it.arrow) { const aa = it.arrowAt || it.at - 0.45; VT.drawPath(it.arrow, eo(P(tt, aa, 0.4))); }
            });
            if (circle) VT.drawPath(circle, eo(P(tt, cAt, 0.6)));
          };
        },
      },
      list: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, items = s.items || [];
          const head = titleOf(s, layer);
          const body = s.title ? Z.body : Z.full;
          const rows = VT.rows(VT.clampW(VT.inset(body, 2), 88), Math.max(3, items.length), 2).slice(0, items.length);
          const svg = VT.svg(layer);
          const els = items.map((it, i) => {
            const r = rows[i], h = Math.min(r.h, 16 * U), cb = h * 0.55, y = r.y + (r.h - h) / 2;
            const bx = VT.dir === 'rtl' ? r.x + r.w - cb : r.x;
            const box = stroke(svg, VT.rough.rect(bx, y + (h - cb) / 2, cb, cb, i + 3), INK(), 0.45);
            const tick = stroke(svg, `M${bx + cb * 0.15} ${y + h / 2} L${bx + cb * 0.42} ${y + h / 2 + cb * 0.3} L${bx + cb * 1.05} ${y + h / 2 - cb * 0.55}`, RED(), 0.8);
            const tb = VT.dir === 'rtl' ? { x: r.x, y, w: r.w - cb - 3 * U, h } : { x: r.x + cb + 3 * U, y, w: r.w - cb - 3 * U, h };
            const t = VT.text(layer, it.text || it, { box: tb, size: 6.4, font: 'hand', weight: 700, color: INK(), align: 'start', valign: 'middle', lh: 1.1 });
            const at = VT.time(it.at, s.start + 0.5 + i * 0.9), ck = VT.time(it.checkAt, it.check === false ? null : at + 0.5);
            VT.cue(at, 'marker', { dur: 0.35, gain: -18 }); if (ck != null) VT.cue(ck, 'tick', { gain: -14 });
            return { box, tick, t, at, ck };
          });
          return (tt) => {
            if (head) head.style.opacity = C((tt - s.start) / 0.3);
            els.forEach((e) => {
              VT.drawPath(e.box, eo(P(tt, e.at - 0.1, 0.3)));
              const p = eo(P(tt, e.at, 0.6)); e.t.style.clipPath = VT.dir === 'rtl' ? `inset(0 0 0 ${(1 - p) * 100}%)` : `inset(0 ${(1 - p) * 100}% 0 0)`;
              VT.drawPath(e.tick, e.ck == null ? 0 : eo(P(tt, e.ck, 0.25)));
            });
          };
        },
      },
      compare: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, head = titleOf(s, layer), body = s.title ? Z.body : Z.full;
          const cols = VT.cols(VT.inset(body, 2), 2, 6);
          if (VT.dir === 'rtl') cols.reverse();
          const svg = VT.svg(layer);
          const mid = (cols[0].x + cols[0].w + cols[1].x) / 2;
          const vline = stroke(svg, VT.rough.line(mid, body.y + 3 * U, mid, body.y + body.h - 3 * U, 4), INK(), 0.5);
          const hl = stroke(svg, VT.rough.line(body.x + 4 * U, body.y + 14 * U, body.x + body.w - 4 * U, body.y + 14 * U, 8), INK(), 0.5);
          const at = VT.time(s.at, s.start + 0.3);
          VT.cue(at, 'marker', { dur: 0.7, gain: -16 });
          const sides = [s.left || {}, s.right || {}].map((side, k) => {
            const c = cols[k];
            const tt = VT.text(layer, side.title || '', { box: { x: c.x, y: body.y + 2 * U, w: c.w, h: 11 * U }, size: 7, font: 'hand', weight: 700, color: k ? VT.col('blue') : RED(), valign: 'middle' });
            const rows = VT.rows({ x: c.x, y: body.y + 17 * U, w: c.w, h: body.h - 20 * U }, Math.max(3, (side.items || []).length), 2);
            const its = (side.items || []).map((it, i) => {
              const tx = VT.text(layer, (VT.dir === 'rtl' ? '' : '• ') + (it.text || it) + (VT.dir === 'rtl' ? ' •' : ''), { box: rows[i], size: 5.6, font: 'hand', weight: 700, color: INK(), valign: 'middle' });
              const a = VT.time(it.at, at + 0.8 + i * 0.7 + k * 0.3); VT.cue(a, 'marker', { dur: 0.3, gain: -19 });
              return { tx, a };
            });
            return { tt, its };
          });
          return (t) => {
            if (head) head.style.opacity = C((t - s.start) / 0.3);
            VT.drawPath(vline, eo(P(t, at, 0.5))); VT.drawPath(hl, eo(P(t, at + 0.2, 0.5)));
            sides.forEach((sd) => { sd.tt.style.opacity = P(t, at + 0.3, 0.3); sd.its.forEach((i) => { i.tx.style.opacity = P(t, i.a, 0.25); }); });
          };
        },
      },
      note: {
        build(s, layer) {
          const z = VT.Z.full, U = VT.U;
          const box = { x: z.x + z.w * 0.08, y: z.y + z.h * 0.25, w: z.w * 0.84, h: z.h * 0.4 };
          const t = VT.text(layer, s.text || '', { box, size: 9.5, font: 'hand', weight: 700, color: INK(), valign: 'middle', lh: 1.15 });
          const svg = VT.svg(layer); const at = VT.time(s.at, s.start + 0.2), ca = VT.time(s.circleAt, s.circleAt == null ? null : at + 1);
          const th = t.offsetHeight;
          const c = stroke(svg, VT.rough.ellipse(box.x + box.w / 2, box.y + box.h / 2, box.w * 0.56, th * 0.85 + 4 * U, 9), RED(), 0.8);
          VT.cue(at, 'marker', { dur: 0.7, gain: -16 }); if (ca != null) VT.cue(ca, 'marker', { dur: 0.6, gain: -15 });
          return (tt) => {
            const p = eo(P(tt, at, 0.9)); t.style.clipPath = VT.dir === 'rtl' ? `inset(0 0 0 ${(1 - p) * 100}%)` : `inset(0 ${(1 - p) * 100}% 0 0)`;
            VT.drawPath(c, ca == null ? 0 : eo(P(tt, ca, 0.6)));
          };
        },
      },
    },
  });
})();
