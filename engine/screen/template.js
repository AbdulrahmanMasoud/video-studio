/* screen - app / website walkthrough: screen recording inside a browser or phone frame,
   animated cursor, click ripples, callout labels and camera zooms on each click. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  // Fake UI so previews without a recording still read as "an app".
  function mockUI(p, w, h) {
    const U = VT.U, a = VT.col('accent');
    VT.el(p, `inset:0;background:#fff`);
    VT.el(p, `left:0;right:0;top:0;height:${h * 0.09}px;background:#F3F4F8;border-bottom:1px solid #E5E7EF`);
    VT.el(p, `left:${w * 0.05}px;top:${h * 0.025}px;width:${w * 0.22}px;height:${h * 0.04}px;border-radius:${U}px;background:${a}`);
    for (let i = 0; i < 3; i++) VT.el(p, `left:${w * (0.05 + i * 0.31)}px;top:${h * 0.14}px;width:${w * 0.28}px;height:${h * 0.22}px;border-radius:${1.6 * U}px;background:${['#EEF0FF', '#FFF3E8', '#E9FBF3'][i]}`);
    for (let i = 0; i < 5; i++) VT.el(p, `left:${w * 0.05}px;top:${h * (0.42 + i * 0.1)}px;width:${w * (0.9 - (i % 3) * 0.18)}px;height:${h * 0.05}px;border-radius:${U}px;background:#F1F2F6`);
    VT.el(p, `left:${w * 0.62}px;top:${h * 0.88}px;width:${w * 0.33}px;height:${h * 0.07}px;border-radius:${1.4 * U}px;background:${a}`);
  }

  VT.template({
    theme: {
      palette: { bg: '#E8ECF6', deep: '#C9D1E6', ink: '#161A2B', paper: '#FFFFFF', accent: '#4F46E5', alt: '#F43F5E', text: '#161A2B', muted: 'rgba(22,26,43,.6)' },
      captions: { style: 'pill', hl: '#4F46E5', hlText: '#FFFFFF', color: '#161A2B', shadow: 'rgba(255,255,255,.9)' },
      transition: 'fade', sfx: { transition: 'swoosh', transitionGain: -22 }, zones: { head: 0.14 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:linear-gradient(150deg,#F4F6FC,#DDE3F3)`);
      const b = VT.el(layer, `width:${110 * U}px;height:${110 * U}px;border-radius:50%;background:radial-gradient(circle, rgba(79,70,229,.18), transparent 65%)`);
      return (t) => VT.place(b, VT.W * 0.75 + Math.sin(t * 0.3) * 10 * U, VT.H * 0.25);
    },
    scenes: {
      // {device: browser|phone|none, media:'screen', url, title, clicks:[{at, x, y, label, zoom}]}
      demo: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z;
          const dev = s.device || (VT.orient === 'portrait' ? 'phone' : 'browser');
          const head = s.title ? VT.text(layer, s.title, { w: Z.area.w * 0.92, h: Z.head.h * 0.8, size: 7.2, color: VT.col('ink') }) : null;
          const area = VT.inset(s.title ? Z.body : Z.full, 1.5);
          // device geometry
          const ratio = s.ratio || (dev === 'phone' ? 9 / 19.5 : 16 / 10);
          const chrome = dev === 'browser' ? 6 * U : 0, bez = dev === 'phone' ? 2.2 * U : 0;
          let sw = area.w - 2 * bez, sh = sw / ratio;
          if (sh + chrome + 2 * bez > area.h) { sh = area.h - chrome - 2 * bez; sw = sh * ratio; }
          const fw = sw + 2 * bez, fh = sh + chrome + 2 * bez;
          const fx = area.x + (area.w - fw) / 2, fy = area.y + (area.h - fh) / 2;
          const cam = VT.el(layer, 'inset:0');
          const frame = VT.el(cam, `left:${fx}px;top:${fy}px;width:${fw}px;height:${fh}px;border-radius:${dev === 'phone' ? 7 * U : 2 * U}px;background:${dev === 'phone' ? '#111' : '#fff'};box-shadow:0 ${3 * U}px ${9 * U}px rgba(22,26,43,.25);overflow:hidden`);
          if (dev === 'browser') {
            VT.el(frame, `left:0;right:0;top:0;height:${chrome}px;background:#EEF0F5;display:flex;align-items:center;gap:${1.1 * U}px;padding:0 ${2.2 * U}px;direction:ltr`,
              ['#FF5F57', '#FEBC2E', '#28C840'].map((c) => `<i style="display:block;width:${1.6 * U}px;height:${1.6 * U}px;border-radius:50%;background:${c}"></i>`).join('') +
              `<div style="flex:1;margin:0 ${3 * U}px;height:${3.6 * U}px;border-radius:${1.8 * U}px;background:#fff;font-family:${VT.font('body')};font-size:${2.2 * U}px;color:#6B7280;display:flex;align-items:center;padding:0 ${1.6 * U}px;white-space:nowrap;overflow:hidden">${VT.esc(s.url || 'yourapp.com')}</div>`);
          }
          const scr = VT.el(frame, `left:${bez}px;top:${chrome + bez}px;width:${sw}px;height:${sh}px;overflow:hidden;border-radius:${dev === 'phone' ? 5 * U : 0}px;background:#fff`);
          let img = null;
          if (VT.hasMedia(s.media || 'screen')) img = VT.media(scr, s.media || 'screen', 'left:0;top:0');
          else mockUI(scr, sw, sh);
          if (dev === 'phone') VT.el(frame, `left:50%;top:${bez + 1.4 * U}px;width:${18 * U}px;height:${4.4 * U}px;margin-left:${-9 * U}px;border-radius:${2.2 * U}px;background:#111`);
          const sx = fx + bez, sy = fy + chrome + bez;
          const cursor = VT.el(cam, `width:${6 * U}px;height:${6 * U}px;z-index:3`, `<svg viewBox="0 0 24 24" width="100%" height="100%"><path d="M4 2 L4 19 L8.5 14.8 L11.5 21.5 L14.3 20.3 L11.4 13.7 L17.5 13.7 Z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>`);
          const ripple = VT.el(cam, `width:${10 * U}px;height:${10 * U}px;border-radius:50%;border:${0.6 * U}px solid ${VT.col('accent')};z-index:2`);
          const clicks = (s.clicks || []).map((c, i) => {
            const at = VT.time(c.at, s.start + 1 + i * 1.5);
            const lab = c.label ? VT.el(cam, `z-index:4;background:${VT.col('ink')};color:#fff;font-family:${VT.font('display')};font-weight:800;font-size:${3.8 * U}px;padding:${1 * U}px ${2.4 * U}px ${1.3 * U}px;border-radius:${2 * U}px;white-space:nowrap;box-shadow:0 ${U}px ${3 * U}px rgba(0,0,0,.25)`, VT.esc(c.label)) : null;
            if (lab) VT.fit(lab, Z.area.w * 0.8);
            VT.cue(at, 'click', { gain: -8 }); if (lab) VT.cue(at + 0.1, 'pop', { gain: -20 });
            return { x: sx + (c.x == null ? 0.5 : c.x) * sw, y: sy + (c.y == null ? 0.5 : c.y) * sh, at, end: VT.time(c.end, at + 1.6), zoom: c.zoom == null ? 1.3 : c.zoom, lab };
          });
          return (t) => {
            if (head) { const r = VT.rise(t, s.start, 0.4, 3); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: r.y, o: r.o }); }
            if (img) img.update(t - s.start + (s.mediaOffset || 0));
            // cursor path: glide to each click target just before it happens
            let px = sx + sw * 0.8, py = sy + sh * 0.85, cur = null;
            clicks.forEach((c, i) => {
              const prevX = i ? clicks[i - 1].x : sx + sw * 0.8, prevY = i ? clicks[i - 1].y : sy + sh * 0.85;
              const m = VT.eio(P(t, c.at - 0.75, 0.65));
              if (t >= c.at - 0.75) { px = L(prevX, c.x, m) + Math.sin(m * Math.PI) * 3 * U; py = L(prevY, c.y, m); }
              if (t >= c.at - 0.9 && t < c.end + 0.4) cur = c;
            });
            const press = clicks.some((c) => t >= c.at && t < c.at + 0.12);
            VT.tf(cursor, { x: px - 0.9 * U, y: py - 0.4 * U, s: press ? 0.85 : 1, o: C((t - s.start - 0.3) / 0.3) });
            const rc = clicks.find((c) => t >= c.at && t < c.at + 0.5);
            if (rc) { const k = P(t, rc.at, 0.5); VT.place(ripple, rc.x, rc.y, { s: L(0.2, 1.4, eo(k)), o: 1 - k }); } else ripple.style.opacity = 0;
            clicks.forEach((c) => { if (!c.lab) return; const w = VT.win(t, c.at + 0.05, c.end, 0.3, 0.25); const above = c.y > VT.H * 0.3; VT.place(c.lab, C(c.x, Z.area.x + c.lab.offsetWidth / 2, Z.area.x + Z.area.w - c.lab.offsetWidth / 2), c.y + (above ? -9 : 9) * U, { s: L(0.6, 1, sp(P(t, c.at + 0.05, 0.4))), o: w.i * (1 - w.o) }); });
            // camera zoom on the active click
            let k = 1, ox = 0, oy = 0;
            if (cur && cur.zoom > 1) { const w = eo(P(t, cur.at - 0.9, 0.6)) * (1 - eo(P(t, cur.end, 0.45))); k = L(1, cur.zoom, w); ox = (VT.W / 2 - cur.x) * w; oy = (VT.H * 0.46 - cur.y) * w; }
            cam.style.transformOrigin = `${cur ? cur.x : VT.W / 2}px ${cur ? cur.y : VT.H / 2}px`;
            cam.style.transform = `translate(${ox}px,${oy}px) scale(${k})`;
            const fp = P(t, s.start, 0.5); frame.style.opacity = C(fp * 3);
          };
        },
      },
      // {n, text, at} numbered step banner between demos
      step: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const n = s.n != null ? s.n : ctx.scenes.filter((x) => x.type === 'step').indexOf(s) + 1;
          const b = VT.el(layer, `width:${16 * U}px;height:${16 * U}px;border-radius:${4.4 * U}px;background:${VT.col('accent')};color:#fff;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${8 * U}px;box-shadow:0 ${1.4 * U}px 0 #2E27A8`, VT.esc(typeof n === 'number' ? VT.num(n) : n));
          const tx = VT.text(layer, s.text || '', { w: z.w * 0.88, h: z.h * 0.3, size: 8.4, color: VT.col('ink') });
          const at = VT.time(s.at, s.start + 0.15);
          VT.cue(at, 'pop-low', { gain: -12 });
          return (t) => { const cy = z.y + z.h * 0.45; VT.place(b, VT.W / 2, cy - tx.offsetHeight / 2 - 12 * U, { s: L(0.3, 1, sp(P(t, at, 0.5))), r: L(-30, 0, eo(P(t, at, 0.5))) }); const r = VT.rise(t, at + 0.2, 0.45, 4); VT.place(tx, VT.W / 2, cy, { y: r.y, o: r.o }); };
        },
      },
    },
  });
})();
