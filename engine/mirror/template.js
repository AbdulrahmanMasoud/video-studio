/* mirror - talking-head edit: camera footage with punch-in zooms on jump cuts, pop captions,
   stickers, headline cards and lower thirds. Works without footage (placeholder) for previews. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function zoomAt(t) {
    // 1) alternate punch-in on every jump cut, 2) explicit zooms from scenes (talk.zooms)
    let base = 1.0;
    if (VT.cfg.data && VT.cfg.data.punch === false) base = 1;
    else { let k = 0; for (const c of VT.cuts) if (t >= c) k++; base = k % 2 ? 1.12 : 1.0; }
    let z = base, fx = 0.5, fy = 0.4;
    VT.plan.scenes.forEach((s) => (s.zooms || []).forEach((q) => {
      const a = VT.time(q.at, s.start), b = VT.time(q.end, a + 1.6), k = q.scale || 1.3;
      const w = eo(P(t, a, q.snap ? 0.08 : 0.35)) * (1 - eo(P(t, b, 0.35)));
      if (w > 0) { z = L(z, k, w); fx = L(fx, q.x == null ? 0.5 : q.x, w); fy = L(fy, q.y == null ? 0.38 : q.y, w); }
    }));
    return { z: z * (1 + t * 0.002), fx, fy };
  }

  VT.template({
    theme: {
      palette: { bg: '#111111', deep: '#000000', ink: '#111111', paper: '#FFFFFF', accent: '#FFE600', alt: '#FF3B6B', text: '#FFFFFF', muted: 'rgba(255,255,255,.8)' },
      captions: { style: 'pop', hl: '#FFE600', hlText: '#111111', size: 7, position: 'auto' },
      transition: 'cut', sfx: { transition: null }, zones: { head: 0.16, cap: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      const wrap = VT.el(layer, 'inset:0;overflow:hidden');
      const cam = VT.media(wrap, (VT.cfg.data && VT.cfg.data.cam) || 'cam', 'left:0;top:0');
      let sil = null;
      if (cam.missing) sil = VT.el(wrap, `left:50%;bottom:0;width:${Math.min(VT.W * 0.9, 95 * U)}px;height:${Math.min(VT.W * 0.9, 95 * U)}px;transform:translateX(-50%);opacity:.5`, VT.icon('person', 'rgba(255,255,255,.35)'));
      const vig = VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 45%, transparent 55%, rgba(0,0,0,.45))`);
      const shade = VT.el(layer, `left:0;right:0;bottom:0;height:40%;background:linear-gradient(transparent, rgba(0,0,0,.35))`);
      return (t) => {
        cam.update(t);
        const q = zoomAt(t);
        wrap.style.transformOrigin = `${q.fx * 100}% ${q.fy * 100}%`;
        wrap.style.transform = `scale(${q.z})`;
      };
    },
    scenes: {
      // {stickers:[{text, at, end, icon, pos: top|middle, color}], zooms:[{at, end, scale, x, y, snap}]}
      talk: {
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          const st = (s.stickers || []).map((k, i) => {
            const e = VT.el(layer, `display:flex;align-items:center;gap:${1.4 * U}px;background:${k.color ? VT.col(k.color) : VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${6.4 * U}px;padding:${1.2 * U}px ${3.2 * U}px ${1.6 * U}px;border-radius:${2.4 * U}px;box-shadow:0 ${0.8 * U}px 0 rgba(0,0,0,.35);white-space:nowrap`,
              (k.icon ? `<span style="width:${5.6 * U}px;height:${5.6 * U}px">${VT.icon(k.icon, VT.col('ink'))}</span>` : '') + `<span>${VT.esc(k.text || '')}</span>`);
            VT.fit(e, z.area.w * 0.9);
            const a = VT.time(k.at, s.start + 0.3), b = VT.time(k.end, a + 1.8);
            VT.cue(a, 'pop-high', { gain: -14 });
            return { e, a, b, pos: k.pos || 'top', r: i % 2 ? 3 : -3 };
          });
          (s.zooms || []).forEach((q) => { if (q.snap) VT.cue(VT.time(q.at, s.start), 'whoosh', { gain: -20 }); });
          return (t) => st.forEach((x) => {
            const w = VT.win(t, x.a, x.b, 0.3, 0.2);
            if (!w.on) { x.e.style.opacity = 0; return; }
            const y = x.pos === 'middle' ? VT.H * 0.45 : z.head.y + z.head.h * 0.5;
            VT.place(x.e, VT.W / 2, y, { s: L(0.4, 1, sp(P(t, x.a, 0.4))), r: x.r, o: w.i * (1 - w.o) });
          });
        },
      },
      // Headline over the footage. {text, sub, at, end}
      title: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          const box = VT.el(layer, `width:${z.area.w * 0.92}px;text-align:center`);
          const h = VT.el(box, `position:relative;display:inline;background:${VT.col('paper')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${9.2 * U}px;line-height:1.45;padding:${0.4 * U}px ${2 * U}px;-webkit-box-decoration-break:clone;box-decoration-break:clone;border-radius:${1.2 * U}px`, VT.esc(s.text || ''));
          VT.fit(box, z.area.w * 0.92, z.head.h * 1.3, 3);
          const sub = s.sub ? VT.el(layer, `background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:800;font-size:${4.8 * U}px;padding:${0.6 * U}px ${2 * U}px ${1 * U}px;border-radius:${1.2 * U}px;white-space:nowrap`, VT.esc(s.sub)) : null;
          const a = VT.time(s.at, s.start + 0.1), b = VT.time(s.end, s.end);
          VT.cue(a, 'swoosh', { gain: -18 });
          return (t) => {
            const w = VT.win(t, a, b - 0.25, 0.35, 0.25);
            const y = z.head.y + z.head.h * 0.55;
            VT.place(box, VT.W / 2, y, { y: (1 - w.i) * -6 * U, o: w.i * (1 - w.o) });
            if (sub) VT.place(sub, VT.W / 2, y + box.offsetHeight / 2 + 4 * U, { s: L(0.5, 1, sp(P(t, a + 0.25, 0.4))), o: C((t - a - 0.25) / 0.15) * (1 - w.o) });
          };
        },
      },
      // Name tag. {name, role, at, end}
      lower: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          const e = VT.el(layer, `display:flex;flex-direction:column;align-items:flex-start;gap:${0.6 * U}px;direction:${VT.dir}`,
            `<div style="background:${VT.col('paper')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${6.2 * U}px;padding:${0.6 * U}px ${2.4 * U}px ${1 * U}px;border-radius:${1 * U}px">${VT.esc(s.name || '')}</div>` +
            (s.role ? `<div style="background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('body')};font-weight:700;font-size:${3.4 * U}px;padding:${0.4 * U}px ${2 * U}px ${0.7 * U}px;border-radius:${1 * U}px">${VT.esc(s.role)}</div>` : ''));
          const a = VT.time(s.at, s.start + 0.3), b = VT.time(s.end, a + 3);
          VT.cue(a, 'swoosh', { gain: -20 });
          return (t) => {
            const w = VT.win(t, a, b, 0.4, 0.3);
            const x0 = VT.dir === 'rtl' ? z.area.x + z.area.w - e.offsetWidth / 2 - U : z.area.x + e.offsetWidth / 2 + U;
            VT.place(e, x0, VT.Z.cap.y - e.offsetHeight / 2 - 3 * U, { x: (1 - w.i) * -12 * U * VT.sign, o: w.i * (1 - w.o) });
          };
        },
      },
    },
  });
})();
