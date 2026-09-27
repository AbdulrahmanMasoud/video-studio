/* journey - timeline: a track that draws itself, events that pop in as the camera travels, and milestone year cards. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  VT.template({
    theme: {
      palette: { bg: '#0E2A2F', deep: '#071619', ink: '#0E2A2F', paper: '#F4EFE6', accent: '#F5B841', alt: '#5FD3C6', text: '#FFFFFF', muted: 'rgba(255,255,255,.65)' },
      captions: { style: 'pill', hl: '#F5B841', hlText: '#0E2A2F' },
      transition: 'fade', sfx: { transition: 'swoosh', transitionGain: -20 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 30% 20%, #18454C, #081A1D 75%)`);
      const dots = VT.el(layer, `inset:-${10 * U}px;background-image:radial-gradient(rgba(255,255,255,.08) ${0.25 * U}px, transparent ${0.3 * U}px);background-size:${4 * U}px ${4 * U}px`);
      return (t) => { dots.style.transform = `translate(${-(t * 2 * U) % (4 * U)}px, 0)`; };
    },
    scenes: {
      // {title, events:[{year, label, at}], orientation: auto|vertical|horizontal}
      timeline: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, ev = s.events || [];
          const vert = s.orientation ? s.orientation === 'vertical' : VT.orient === 'portrait';
          const head = s.title ? VT.text(layer, s.title, { w: Z.area.w * 0.92, h: Z.head.h * 0.8, size: 7.4, color: '#fff' }) : null;
          const body = s.title ? Z.body : Z.full;
          const view = VT.el(layer, `left:${body.x}px;top:${body.y}px;width:${body.w}px;height:${body.h}px;overflow:hidden`);
          const world = VT.el(view, 'left:0;top:0');
          const gap = vert ? Math.max(24 * U, body.h / 3.2) : Math.max(40 * U, body.w / 3.2);
          const len = gap * Math.max(1, ev.length - 1);
          const cx0 = vert ? body.w * 0.3 : 0, cy0 = vert ? 0 : body.h * 0.5;
          const svg = VT.svg(world); svg.setAttribute('width', vert ? body.w : len + body.w); svg.setAttribute('height', vert ? len + body.h : body.h); svg.setAttribute('viewBox', `0 0 ${vert ? body.w : len + body.w} ${vert ? len + body.h : body.h}`);
          const off = vert ? body.h / 2 : body.w / 2; // first event sits at the view centre
          const pt = (i) => (vert ? { x: body.w * (VT.dir === 'rtl' ? 0.72 : 0.28), y: off + i * gap } : { x: off + i * gap * VT.sign, y: body.h * 0.5 });
          const p0 = pt(0), pN = pt(Math.max(0, ev.length - 1));
          svg.add('line', { x1: p0.x, y1: p0.y, x2: pN.x, y2: pN.y, stroke: 'rgba(255,255,255,.15)', 'stroke-width': 0.8 * U, 'stroke-linecap': 'round' });
          const track = svg.add('path', { d: `M${p0.x} ${p0.y} L${pN.x} ${pN.y}`, stroke: VT.col('accent'), 'stroke-width': 0.8 * U, fill: 'none', 'stroke-linecap': 'round' });
          const items = ev.map((e, i) => {
            const p = pt(i), at = VT.time(e.at, s.start + 0.5 + i * 1.4);
            const dot = VT.el(world, `left:${p.x - 3 * U}px;top:${p.y - 3 * U}px;width:${6 * U}px;height:${6 * U}px;border-radius:50%;background:${VT.col('accent')};box-shadow:0 0 0 ${1.2 * U}px rgba(245,184,65,.25)`);
            const yr = VT.el(world, `font-family:${VT.font('display')};font-weight:900;font-size:${(vert ? 9 : 8) * U}px;color:${VT.col('accent')};white-space:nowrap;line-height:1;direction:ltr`, VT.esc(e.year != null ? String(e.year) : ''));
            const card = VT.card(world, { bg: VT.col('paper'), fg: VT.col('ink'), shadow: 'rgba(0,0,0,.35)', css: `width:${vert ? body.w * 0.6 : Math.min(gap * 0.9, 60 * U)}px;padding:${2 * U}px ${2.6 * U}px ${2.4 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${4.6 * U}px;line-height:1.2` });
            card.textContent = e.label || ''; VT.fit(card, null, vert ? gap * 0.55 : body.h * 0.34, 2.6);
            if (vert) { const rtl = VT.dir === 'rtl'; yr.style.left = (rtl ? p.x - 6 * U - yr.offsetWidth : p.x + 6 * U) + 'px'; yr.style.top = p.y - 8 * U + 'px'; card.style.left = (rtl ? p.x - 6 * U - card.offsetWidth : p.x + 6 * U) + 'px'; card.style.top = p.y + 3 * U + 'px'; }
            else { yr.style.left = p.x - yr.offsetWidth / 2 + 'px'; yr.style.top = p.y - 14 * U + 'px'; card.style.left = p.x - card.offsetWidth / 2 + 'px'; card.style.top = p.y + 6 * U + 'px'; }
            VT.cue(at - 0.35, 'whoosh', { gain: -22 }); VT.cue(at, 'pop', { gain: -14 });
            return { dot, yr, card, at, p, i };
          });
          const posAt = (t) => {
            // camera index (float) that eases toward each event as it arrives
            let k = 0;
            items.forEach((it, i) => { if (i) k = L(k, i, eo(P(t, it.at - 0.45, 0.55))); });
            return k;
          };
          return (t) => {
            if (head) { const r = VT.rise(t, s.start, 0.4, 3); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: r.y, o: r.o }); }
            const k = posAt(t);
            const cam = vert ? { x: 0, y: -k * gap } : { x: -k * gap * VT.sign, y: 0 };
            world.style.transform = `translate(${cam.x}px,${cam.y}px)`;
            const reach = items.length > 1 ? C(k / (items.length - 1)) : 1;
            VT.drawPath(track, reach);
            items.forEach((it) => {
              const p = P(t, it.at, 0.45), act = Math.max(0, 1 - Math.abs(k - it.i));
              it.dot.style.transform = `scale(${L(0, 1, sp(p)) * (1 + act * 0.35)})`; it.dot.style.opacity = C(p * 4);
              it.yr.style.opacity = C((t - it.at) / 0.25) * L(0.45, 1, act); it.yr.style.transform = `translateY(${(1 - eo(p)) * 3 * U}px)`;
              it.card.style.opacity = C((t - it.at - 0.1) / 0.25) * L(0.5, 1, act); it.card.style.transform = `translateY(${(1 - eo(P(t, it.at + 0.1, 0.45))) * 4 * U}px) scale(${L(0.92, 1, act)})`;
            });
          };
        },
      },
      // {from, year, title, text, at}
      milestone: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const yr = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${Math.min(36 * U, z.w * 0.3)}px;color:${VT.col('accent')};line-height:1;font-variant-numeric:tabular-nums;direction:ltr;white-space:nowrap`);
          const tt = VT.text(layer, s.title || '', { w: z.w * 0.88, h: z.h * 0.22, size: 8, color: '#fff' });
          const tx = s.text ? VT.text(layer, s.text, { w: z.w * 0.82, h: z.h * 0.25, size: 4.6, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.3), y1 = +s.year || 0, y0 = s.from != null ? +s.from : y1 - 10, roll = 1.2;
          const isNum = !isNaN(y1) && s.year != null && /^\d+$/.test(String(s.year));
          VT.cue(at, 'riser', { dur: roll, gain: -22 }); VT.cue(at + roll, 'impact', { gain: -12 });
          return (t) => {
            const cy = z.y + z.h * 0.4;
            yr.textContent = isNum ? String(Math.round(L(y0, y1, eo(C((t - at) / roll))))) : String(s.year || '');
            VT.place(yr, VT.W / 2, cy, { s: t > at + roll ? L(1.1, 1, eo(P(t, at + roll, 0.3))) : 1, o: C((t - at) / 0.2) });
            const r = VT.rise(t, at + roll, 0.45, 4); VT.place(tt, VT.W / 2, cy + yr.offsetHeight / 2 + tt.offsetHeight / 2 + 4 * U, { y: r.y, o: r.o });
            if (tx) { const r2 = VT.rise(t, at + roll + 0.3, 0.45, 3); VT.place(tx, VT.W / 2, cy + yr.offsetHeight / 2 + tt.offsetHeight + tx.offsetHeight / 2 + 7 * U, { y: r2.y, o: r2.o }); }
          };
        },
      },
    },
  });
})();
