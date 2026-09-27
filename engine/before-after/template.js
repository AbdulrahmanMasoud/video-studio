/* before-after - transformation: a wipe slider reveals the "after", or two cards compare side by side. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  // One side's visual: footage/image if provided, else a colored panel with a bullet list.
  function side(p, d, kind, box) {
    const U = VT.U, col = VT.col(kind), good = kind === 'after';
    const e = VT.el(p, `left:${box.x}px;top:${box.y}px;width:${box.w}px;height:${box.h}px;overflow:hidden;background:${good ? '#12261E' : '#2A1416'}`);
    let img = null;
    if (d.media && VT.hasMedia(d.media)) img = VT.media(e, d.media, 'left:0;top:0');
    const items = d.items || [];
    if (!img && items.length) {
      const list = VT.el(e, `left:${box.w * 0.1}px;width:${box.w * 0.8}px;top:0;height:100%;display:flex;flex-direction:column;justify-content:center;gap:${2.6 * U}px;direction:${VT.dir}`);
      items.forEach((it) => { VT.el(list, `position:relative;display:flex;align-items:center;gap:${2.4 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${5.4 * U}px;color:#fff;line-height:1.15`, `<span style="flex:none;width:${7 * U}px;height:${7 * U}px;border-radius:50%;background:${col};display:flex;align-items:center;justify-content:center">${VT.icon(good ? 'check' : 'x', '#fff', '60%')}</span><span style="flex:1;min-width:0">${VT.esc(it.text || it)}</span>`); });
      VT.fit(list, null, box.h * 0.9, 2.6);
    } else if (!img) VT.el(e, `inset:0;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${9 * U}px;color:rgba(255,255,255,.2)`, VT.esc(d.text || ''));
    return { e, img };
  }
  function chip(p, text, kind) {
    const U = VT.U;
    return VT.el(p, `background:${VT.col(kind)};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${4.6 * U}px;letter-spacing:.08em;padding:${0.9 * U}px ${3 * U}px ${1.3 * U}px;border-radius:${2 * U}px;white-space:nowrap;box-shadow:0 ${0.8 * U}px ${2 * U}px rgba(0,0,0,.35);z-index:3`, VT.esc(text));
  }

  VT.template({
    theme: {
      palette: { bg: '#101114', deep: '#000000', ink: '#101114', paper: '#FFFFFF', before: '#FF5A5F', after: '#1FD18A', accent: '#FFD23F', text: '#FFFFFF', muted: 'rgba(255,255,255,.7)' },
      captions: { style: 'pill', hl: '#FFD23F', hlText: '#101114' },
      transition: 'slide', sfx: { transition: 'whoosh', transitionGain: -17 }, zones: { head: 0.14 },
    },
    background(layer) { VT.el(layer, `inset:0;background:linear-gradient(180deg,#17181D,#0B0C0F)`); return null; },
    scenes: {
      // Wipe reveal. {before:{label, media, items, text}, after:{...}, at, wipeAt, wipeDur, full}
      compare: {
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          const box = s.full ? { x: 0, y: 0, w: VT.W, h: VT.H } : VT.inset(VT.Z.full, 1);
          const frame = VT.el(layer, `left:${box.x}px;top:${box.y}px;width:${box.w}px;height:${box.h}px;border-radius:${s.full ? 0 : 3 * U}px;overflow:hidden`);
          const inner = { x: 0, y: 0, w: box.w, h: box.h };
          const b = side(frame, s.before || {}, 'before', inner), a = side(frame, s.after || {}, 'after', inner);
          const line = VT.el(frame, `top:0;bottom:0;width:${0.8 * U}px;margin-left:${-0.4 * U}px;background:#fff;box-shadow:0 0 ${2 * U}px rgba(0,0,0,.5);z-index:2`);
          const knob = VT.el(frame, `width:${10 * U}px;height:${10 * U}px;border-radius:50%;background:#fff;z-index:2;display:flex;align-items:center;justify-content:center;box-shadow:0 ${0.8 * U}px ${2.4 * U}px rgba(0,0,0,.4)`, `<svg viewBox="0 0 40 20" width="60%"><path d="M12 3 L3 10 L12 17 M28 3 L37 10 L28 17" stroke="#101114" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`);
          const cb = chip(frame, (s.before || {}).label || VT.label(s, 'before', 'BEFORE'), 'before'), ca = chip(frame, (s.after || {}).label || VT.label(s, 'after', 'AFTER'), 'after');
          const at = VT.time(s.at, s.start + 0.1), wa = VT.time(s.wipeAt, at + 1.8), wd = s.wipeDur || 1.1;
          VT.cue(wa - 0.05, 'swoosh', { gain: -14 }); VT.cue(wa + wd, 'sparkle', { gain: -16 }); VT.cue(wa + wd + 0.05, 'success', { gain: -15 });
          // RTL: the "after" is revealed from the right.
          return (t) => {
            [b, a].forEach((x) => { if (x.img) { x.img.update(t - s.start); x.img.style.transform = `scale(${1.03 + (t - s.start) * 0.006})`; } });
            // sweep with a small overshoot "tease" before the full reveal
            const tease = Math.sin(C((t - at - 0.4) / 0.9) * Math.PI) * 0.12;
            const f = C(eo(P(t, wa, wd)) + (t < wa ? tease : 0));
            const pos = VT.dir === 'rtl' ? 1 - f : f; // fraction of width covered by "after" from the start edge
            const xLine = VT.dir === 'rtl' ? box.w * (1 - f) : box.w * f;
            a.e.style.clipPath = VT.dir === 'rtl' ? `inset(0 0 0 ${xLine}px)` : `inset(0 ${box.w - xLine}px 0 0)`;
            const showLine = f > 0.002 && f < 0.998;
            line.style.left = xLine + 'px'; line.style.opacity = showLine ? 1 : 0;
            VT.place(knob, xLine, box.h / 2, { o: showLine ? 1 : 0, s: showLine ? 1 : 0.5 });
            const fp = P(t, at, 0.45);
            frame.style.opacity = C(fp * 3);
            VT.place(cb, VT.dir === 'rtl' ? box.w - cb.offsetWidth / 2 - 3 * U : cb.offsetWidth / 2 + 3 * U, 3 * U + cb.offsetHeight / 2 + (s.full ? z.area.y : 0), { o: C((t - at - 0.2) / 0.2) * (1 - C((f - 0.85) / 0.15)) });
            VT.place(ca, VT.dir === 'rtl' ? ca.offsetWidth / 2 + 3 * U : box.w - ca.offsetWidth / 2 - 3 * U, 3 * U + ca.offsetHeight / 2 + (s.full ? z.area.y : 0), { s: L(0.5, 1, sp(P(t, wa + wd * 0.5, 0.4))), o: C((f - 0.4) / 0.2) });
          };
        },
      },
      // Two cards side by side / stacked. {before:{label, items}, after:{label, items}, at, afterAt}
      split: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, land = VT.orient !== 'portrait';
          const area = VT.inset(z, 1), boxes = land ? VT.cols(area, 2, 3) : VT.rows(area, 2, 3);
          const at = VT.time(s.at, s.start + 0.2), aa = VT.time(s.afterAt, at + 1.4);
          const cards = ['before', 'after'].map((k, i) => {
            const d = s[k] || {}, bx = boxes[i];
            const holder = VT.el(layer, `left:${bx.x}px;top:${bx.y}px;width:${bx.w}px;height:${bx.h}px;border-radius:${3 * U}px;overflow:hidden;border:${0.5 * U}px solid ${VT.col(k)}`);
            side(holder, d, k, { x: 0, y: 0, w: bx.w, h: bx.h });
            const c = chip(layer, d.label || VT.label(s, k, k.toUpperCase()), k);
            const ta = i ? aa : at; VT.cue(ta, i ? 'success' : 'error', { gain: -15 });
            return { holder, c, bx, ta, i };
          });
          return (t) => cards.forEach((x) => {
            const p = P(t, x.ta, 0.5);
            x.holder.style.opacity = C(p * 3) * (x.i === 0 && t > aa ? 0.55 : 1);
            x.holder.style.transform = `translateY(${(1 - eo(p)) * 6 * U}px) scale(${x.i === 1 && t > aa ? L(0.96, 1, eo(P(t, aa, 0.5))) : 1})`;
            VT.place(x.c, x.bx.x + x.bx.w / 2, x.bx.y, { s: L(0.4, 1, sp(P(t, x.ta + 0.1, 0.4))), o: C((t - x.ta - 0.1) / 0.15) });
          });
        },
      },
    },
  });
})();
