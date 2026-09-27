/* storytime - personal story: warm graded footage, chapter cards, polaroid photos and an ending card. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  VT.template({
    theme: {
      palette: { bg: '#1B130E', deep: '#0C0806', ink: '#2A1D15', paper: '#F6EEE3', accent: '#F2A65A', alt: '#E8634A', text: '#FFF8EF', muted: 'rgba(255,248,239,.72)' },
      captions: { style: 'karaoke', color: '#FFF8EF', hl: '#F2A65A', shadow: 'rgba(0,0,0,.6)', maxWords: 4, font: 'display' },
      transition: 'fade', sfx: { transition: null }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      const wrap = VT.el(layer, 'inset:0;overflow:hidden');
      const cam = VT.media(wrap, (VT.cfg.data && VT.cfg.data.cam) || 'cam', 'left:0;top:0;filter:sepia(.18) saturate(1.08) contrast(1.04)');
      const glow = cam.missing ? VT.el(wrap, `width:${140 * U}px;height:${140 * U}px;border-radius:50%;background:radial-gradient(circle, rgba(242,166,90,.35), transparent 65%)`) : null;
      if (cam.missing) VT.el(wrap, `left:50%;bottom:0;width:${Math.min(VT.W * 0.9, 95 * U)}px;height:${Math.min(VT.W * 0.9, 95 * U)}px;transform:translateX(-50%);opacity:.45`, VT.icon('person', 'rgba(255,230,200,.35)'));
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 50%, rgba(20,10,4,.55)), linear-gradient(180deg, rgba(242,166,90,.08), rgba(232,99,74,.06))`);
      const leak = VT.el(layer, `width:${120 * U}px;height:${120 * U}px;border-radius:50%;background:radial-gradient(circle, rgba(255,170,90,.18), transparent 60%);mix-blend-mode:screen`);
      return (t) => {
        cam.update(t);
        wrap.style.transform = `scale(${1.02 + Math.sin(t * 0.15) * 0.015 + (VT.cuts.filter((c) => t >= c).length % 2) * 0.06})`;
        if (glow) VT.place(glow, VT.W / 2, VT.H * 0.4 + Math.sin(t * 0.4) * 5 * U);
        VT.place(leak, VT.W * (0.1 + 0.8 * ((Math.sin(t * 0.13) + 1) / 2)), VT.H * 0.15, { o: 0.8 });
      };
    },
    scenes: {
      // {n, title, at} - a chapter card that dims the footage
      chapter: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const n = s.n != null ? s.n : ctx.scenes.filter((x) => x.type === 'chapter').indexOf(s) + 1;
          const dim = VT.el(layer, `inset:0;background:rgba(18,11,7,.72)`);
          const k = VT.el(layer, `font-family:${VT.font('serif')};font-style:italic;font-weight:600;font-size:${5 * U}px;color:${VT.col('accent')};letter-spacing:.08em;white-space:nowrap`, VT.esc(s.kicker || `${VT.label(s, 'chapter', 'Chapter')} ${typeof n === 'number' ? VT.num(n) : n}`));
          const tt = VT.text(layer, s.title || '', { w: z.w * 0.86, h: z.h * 0.3, size: 10, font: 'serif', weight: 700, color: VT.col('text'), lh: 1.15 });
          const line = VT.el(layer, `height:${0.3 * U}px;width:${30 * U}px;background:${VT.col('accent')}`);
          const at = VT.time(s.at, s.start + 0.2), end = VT.time(s.hold, s.end);
          VT.cue(at, 'page', { gain: -18 }); VT.cue(at + 0.1, 'sting', { gain: -20 });
          return (t) => {
            const p = P(t, at, 0.6), out = P(t, end - 0.5, 0.5);
            dim.style.opacity = C(p * 2) * (1 - out);
            const cy = z.y + z.h * 0.45;
            VT.place(k, VT.W / 2, cy - tt.offsetHeight / 2 - 6 * U, { o: C(p * 2) * (1 - out), y: (1 - eo(p)) * 3 * U });
            VT.place(tt, VT.W / 2, cy, { o: C((t - at - 0.2) / 0.5) * (1 - out), s: L(1.06, 1, eo(P(t, at + 0.2, 1))) });
            VT.place(line, VT.W / 2, cy + tt.offsetHeight / 2 + 5 * U, { sx: eo(P(t, at + 0.5, 0.6)), o: 1 - out });
          };
        },
      },
      // Transparent scene over the footage with optional small note. {note, noteAt}
      talk: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          if (!s.note) return () => {};
          const e = VT.el(layer, `background:${VT.col('paper')};color:${VT.col('ink')};font-family:${VT.font('hand')};font-weight:700;font-size:${6 * U}px;padding:${1.2 * U}px ${3 * U}px ${1.6 * U}px;border-radius:${1 * U}px;box-shadow:0 ${1.2 * U}px ${3 * U}px rgba(0,0,0,.35);white-space:nowrap`, VT.esc(s.note));
          VT.fit(e, z.area.w * 0.86);
          const a = VT.time(s.noteAt, s.start + 0.5), b = VT.time(s.noteEnd, a + 2.2);
          VT.cue(a, 'pop', { gain: -16 });
          return (t) => { const w = VT.win(t, a, b, 0.35, 0.3); VT.place(e, VT.W / 2, z.head.y + z.head.h * 0.55, { s: L(0.6, 1, sp(P(t, a, 0.4))), r: -3, o: w.i * (1 - w.o) }); };
        },
      },
      // Polaroid photo that drops in. {media, caption, at, end, rotate}
      photo: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const w = Math.min(z.w * 0.78, 70 * U), ph = w * 0.9;
          const card = VT.el(layer, `width:${w}px;padding:${2.4 * U}px ${2.4 * U}px ${9 * U}px;background:#FBF7F0;box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.45)`);
          const frame = VT.el(card, `position:relative;width:100%;height:${ph}px;overflow:hidden;background:#ddd`);
          const img = VT.media(frame, s.media || 'photo', 'left:0;top:0');
          const cap = VT.el(card, `left:0;right:0;bottom:${2 * U}px;text-align:center;font-family:${VT.font('hand')};font-weight:700;font-size:${5.2 * U}px;color:#3A2A20`, VT.esc(s.caption || ''));
          const tape = VT.el(card, `left:50%;top:${-2 * U}px;width:${18 * U}px;height:${5 * U}px;margin-left:${-9 * U}px;background:rgba(255,240,200,.7);transform:rotate(-4deg)`);
          const a = VT.time(s.at, s.start + 0.2), b = VT.time(s.end, s.end), r = s.rotate == null ? -4 : s.rotate;
          VT.cue(a, 'whoosh-down', { gain: -18 }); VT.cue(a + 0.35, 'shutter', { gain: -16 });
          return (t) => {
            img.update(t - s.start); img.style.transform = `scale(${1.08 - (t - a) * 0.01})`;
            const p = P(t, a, 0.55), o = P(t, b - 0.35, 0.35);
            VT.place(card, VT.W / 2, z.y + z.h * 0.47, { y: (1 - eo(p)) * -30 * U + ei(o) * 40 * U, r: L(r - 12, r, eo(p)), s: L(1.25, 1, eo(p)), o: C(p * 3) * (1 - o) });
          };
        },
      },
      // {text, sub, at}
      end: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const dim = VT.el(layer, `inset:0;background:rgba(18,11,7,.78)`);
          const tt = VT.text(layer, s.text || VT.label(s, 'end', 'The end.'), { w: z.w * 0.86, h: z.h * 0.3, size: 11, font: 'serif', weight: 700, color: VT.col('text') });
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.8, size: 4.8, font: 'body', weight: 600, color: VT.col('accent') }) : null;
          const at = VT.time(s.at, s.start + 0.3);
          VT.cue(at, 'sting', { gain: -16 });
          return (t) => {
            dim.style.opacity = C((t - s.start) / 0.6);
            const cy = z.y + z.h * 0.45;
            VT.place(tt, VT.W / 2, cy, { o: C((t - at) / 0.6), s: L(1.08, 1, eo(P(t, at, 1.2))) });
            if (sub) { const r = VT.rise(t, at + 0.8, 0.5, 3); VT.place(sub, VT.W / 2, cy + tt.offsetHeight / 2 + 6 * U, { y: r.y, o: r.o }); }
          };
        },
      },
    },
  });
})();
