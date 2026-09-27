/* city-map - travel / places: a stylised procedural map, pins that drop in, a route that draws itself,
   a camera that follows the latest pin, and place cards with ratings. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  // Procedural city: blocks, main roads, a river and parks, generated from a seed (deterministic).
  function drawCity(svg, W, H, seed) {
    const U = VT.U, h = (k) => VT.hash(seed * 31 + k);
    svg.add('rect', { x: 0, y: 0, width: W, height: H, fill: VT.col('land') });
    for (let i = 0; i < 7; i++) svg.add('ellipse', { cx: h(i) * W, cy: h(i + 50) * H, rx: (8 + h(i + 9) * 16) * U, ry: (6 + h(i + 19) * 12) * U, fill: VT.col('park') });
    const ry = H * (0.3 + h(3) * 0.4);
    svg.add('path', { d: `M${-10 * U} ${ry} C${W * 0.3} ${ry - 25 * U}, ${W * 0.6} ${ry + 30 * U}, ${W + 10 * U} ${ry - 10 * U}`, stroke: VT.col('water'), 'stroke-width': 9 * U, fill: 'none' });
    const step = 11 * U;
    for (let x = step * h(7); x < W; x += step * (0.8 + h(x) * 0.6)) svg.add('line', { x1: x, y1: 0, x2: x + (h(x + 1) - 0.5) * 12 * U, y2: H, stroke: VT.col('road'), 'stroke-width': (h(x + 2) > 0.8 ? 1.8 : 0.9) * U });
    for (let y = step * h(8); y < H; y += step * (0.8 + h(y + 3) * 0.6)) svg.add('line', { x1: 0, y1: y, x2: W, y2: y + (h(y + 4) - 0.5) * 12 * U, stroke: VT.col('road'), 'stroke-width': (h(y + 5) > 0.8 ? 1.8 : 0.9) * U });
  }

  VT.template({
    theme: {
      palette: { bg: '#EFEBE3', deep: '#C9C1B3', ink: '#1E2430', paper: '#FFFFFF', accent: '#FF4D4D', alt: '#2E7CF6', land: '#EFEBE3', park: '#CFE8C6', water: '#A8D4F5', road: '#FFFFFF', text: '#1E2430', muted: 'rgba(30,36,48,.62)', gold: '#FFB400' },
      captions: { style: 'pill', hl: '#FF4D4D', hlText: '#FFFFFF', color: '#1E2430', shadow: 'rgba(255,255,255,.9)' },
      transition: 'fade', sfx: { transition: 'swoosh', transitionGain: -20 }, zones: { head: 0.14 },
    },
    background(layer) { VT.el(layer, `inset:0;background:${VT.col('land')}`); return null; },
    scenes: {
      // {title, pins:[{label, x, y, at, icon}], routeAt, routeDur, seed, zoom}
      map: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, pins = s.pins || [];
          // world is larger than the frame so the camera can travel
          const WW = VT.W * 2.4, WH = VT.H * 2.4;
          const world = VT.el(layer, `left:0;top:0;width:${WW}px;height:${WH}px;transform-origin:0 0`);
          const svg = VT.svg(world); svg.setAttribute('width', WW); svg.setAttribute('height', WH); svg.setAttribute('viewBox', `0 0 ${WW} ${WH}`);
          drawCity(svg, WW, WH, s.seed || 7);
          const spread = VT.orient === 'portrait' ? [0.34, 0.32, 0.3, 0.4] : [0.3, 0.4, 0.34, 0.32];
          const pos = pins.map((p) => ({ x: (spread[0] + spread[1] * (p.x == null ? 0.5 : p.x)) * WW, y: (spread[2] + spread[3] * (p.y == null ? 0.5 : p.y)) * WH }));
          let route = null, rA = 0, rD = 0;
          if (pos.length > 1) {
            let d = `M${pos[0].x} ${pos[0].y}`;
            for (let i = 1; i < pos.length; i++) { const a = pos[i - 1], b = pos[i]; d += ` Q${(a.x + b.x) / 2 + (VT.hash(i) - 0.5) * 30 * U} ${(a.y + b.y) / 2 + (VT.hash(i + 4) - 0.5) * 30 * U} ${b.x} ${b.y}`; }
            svg.add('path', { d, stroke: 'rgba(0,0,0,.12)', 'stroke-width': 2.4 * U, fill: 'none', 'stroke-linecap': 'round' });
            route = svg.add('path', { d, stroke: VT.col('alt'), 'stroke-width': 1.3 * U, fill: 'none', 'stroke-linecap': 'round', 'stroke-dasharray': `${2 * U} ${1.4 * U}` });
            rA = VT.time(s.routeAt, null); rD = s.routeDur || 2;
          }
          const items = pins.map((p, i) => {
            const at = VT.time(p.at, s.start + 0.6 + i * 1.3);
            const pin = VT.el(world, `width:${10 * U}px;height:${10 * U}px;transform-origin:50% 100%`, VT.icon('pin', i === pins.length - 1 && s.lastGold !== false && pins.length > 2 ? VT.col('gold') : VT.col('accent')));
            const lab = VT.el(world, `background:#fff;color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:800;font-size:${3.8 * U}px;padding:${0.8 * U}px ${2 * U}px ${1.1 * U}px;border-radius:${1.6 * U}px;box-shadow:0 ${0.6 * U}px ${2 * U}px rgba(0,0,0,.2);white-space:nowrap`, VT.esc(p.label || ''));
            VT.cue(at, 'whoosh-down', { gain: -22 }); VT.cue(at + 0.28, 'pop', { gain: -14 });
            return { pin, lab, at, p: pos[i] };
          });
          if (route && rA != null) VT.cue(rA, 'zip', { gain: -18, dur: rD });
          const head = s.title ? VT.el(layer, `background:${VT.col('ink')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${5.6 * U}px;padding:${1.2 * U}px ${3.4 * U}px ${1.6 * U}px;border-radius:${2.4 * U}px;white-space:nowrap;box-shadow:0 ${U}px ${3 * U}px rgba(0,0,0,.25)`, VT.esc(s.title)) : null;
          if (head) VT.fit(head, Z.area.w * 0.9);
          const zoom = s.zoom || 1;
          return (t) => {
            // camera target: average of visible pins, following the latest one
            let tx = WW / 2, ty = WH / 2, k = 0;
            items.forEach((it, i) => { const w = eo(P(t, it.at - 0.5, 0.8)); if (i === 0) { tx = L(WW / 2, it.p.x, w); ty = L(WH / 2, it.p.y, w); } else { tx = L(tx, it.p.x, w); ty = L(ty, it.p.y, w); } });
            const routeOn = route && rA != null && t >= rA;
            let sc = zoom * L(0.9, 1, eo(P(t, s.start, 1.5)));
            if (routeOn && items.length) {
              // zoom out to show the whole route
              const xs = items.map((i) => i.p.x), ys = items.map((i) => i.p.y), w = eo(P(t, rA - 0.3, 0.8));
              const bx = (Math.min(...xs) + Math.max(...xs)) / 2, by = (Math.min(...ys) + Math.max(...ys)) / 2;
              const fit = Math.min(VT.W * 0.75 / Math.max(1, Math.max(...xs) - Math.min(...xs)), Z.full.h * 0.7 / Math.max(1, Math.max(...ys) - Math.min(...ys)));
              tx = L(tx, bx, w); ty = L(ty, by, w); sc = L(sc, Math.min(sc, fit), w);
            }
            const cx = VT.W / 2, cy = Z.full.y + Z.full.h * 0.55;
            world.style.transform = `translate(${cx - tx * sc}px,${cy - ty * sc}px) scale(${sc})`;
            if (route) VT.drawPath(route, rA != null ? eo(P(t, rA, rD)) : 0);
            items.forEach((it) => {
              const p = P(t, it.at, 0.35), b = t > it.at + 0.3 ? L(0.8, 1, sp(P(t, it.at + 0.3, 0.4))) : 1;
              VT.tf(it.pin, { x: it.p.x - 5 * U, y: it.p.y - 10 * U - (1 - eo(p)) * 20 * U, sx: 1 / b, sy: b, o: C(p * 5) });
              VT.tf(it.lab, { x: it.p.x - it.lab.offsetWidth / 2, y: it.p.y - 16.5 * U, s: 1 / Math.max(0.6, sc) * L(0.5, 1, sp(P(t, it.at + 0.3, 0.4))), o: C((t - it.at - 0.3) / 0.15) });
              it.lab.style.transformOrigin = '50% 100%';
            });
            if (head) VT.place(head, VT.W / 2, Z.area.y + head.offsetHeight / 2 + 2 * U, { s: L(0.5, 1, sp(P(t, s.start + 0.1, 0.4))), o: C((t - s.start) / 0.2) });
          };
        },
      },
      // {name, text, media, rating, price, tag, at}
      place: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 92);
          const card = VT.card(layer, { bg: '#fff', fg: VT.col('ink'), shadow: 'rgba(0,0,0,.18)', css: `width:${col.w}px;overflow:hidden;padding:0` });
          const ph = VT.el(card, `position:relative;width:100%;height:${Math.min(col.w * 0.62, z.h * 0.45)}px;background:linear-gradient(135deg,${VT.col('park')},${VT.col('water')})`);
          const img = s.media && VT.hasMedia(s.media) ? VT.media(ph, s.media, 'left:0;top:0') : null;
          if (!img) VT.el(ph, `inset:0;display:flex;align-items:center;justify-content:center`, `<div style="width:26%;height:40%">${VT.icon(s.icon || 'pin', VT.col('accent'))}</div>`);
          const r = s.rating || 0;
          const body = VT.el(card, `position:relative;padding:${3 * U}px ${3.6 * U}px ${3.6 * U}px;direction:${VT.dir}`,
            (s.tag ? `<div style="display:inline-block;background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:800;font-size:${3 * U}px;padding:${0.4 * U}px ${1.6 * U}px ${0.7 * U}px;border-radius:${1 * U}px;margin-bottom:${1.2 * U}px">${VT.esc(s.tag)}</div>` : '') +
            `<div style="font-family:${VT.font('display')};font-weight:900;font-size:${6.4 * U}px;line-height:1.1">${VT.esc(s.name || '')}</div>` +
            (r ? `<div class="st" style="display:flex;gap:${0.6 * U}px;margin-top:${1.2 * U}px;height:${5 * U}px;direction:ltr">${Array.from({ length: 5 }, () => `<span style="width:${5 * U}px;height:${5 * U}px;display:block">${VT.icon('star', '#E5E1D8')}</span>`).join('')}<b style="font-family:${VT.font('display')};font-size:${4.2 * U}px;margin-left:${U}px">${VT.esc(VT.num(r, 1))}</b></div>` : '') +
            (s.text ? `<div style="margin-top:${1.4 * U}px;font-family:${VT.font('body')};font-weight:500;font-size:${4 * U}px;line-height:1.4;color:${VT.col('muted')}">${VT.esc(s.text)}</div>` : ''));
          VT.fit(card, col.w, z.h * 0.95, 2.4);
          const stars = r ? Array.from(body.querySelectorAll('.st span')) : [];
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); stars.forEach((_, i) => { if (i < Math.ceil(r)) VT.cue(at + 0.6 + i * 0.12, 'pop-high', { gain: -22 }); });
          return (t) => {
            if (img) { img.update(t - s.start); img.style.transform = `scale(${1.05 + (t - s.start) * 0.01})`; }
            const p = P(t, at, 0.5); VT.place(card, VT.W / 2, z.y + z.h * 0.5, { y: (1 - eo(p)) * 10 * U, o: C(p * 3) });
            stars.forEach((e, i) => { const f = C(r - i), q = P(t, at + 0.6 + i * 0.12, 0.3); e.innerHTML = VT.icon('star', f >= 0.5 && q > 0 ? VT.col('gold') : '#E5E1D8'); e.style.transform = `scale(${f >= 0.5 ? L(0.5, 1, sp(q)) : 1})`; });
          };
        },
      },
    },
  });
})();
