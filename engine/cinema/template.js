/* cinema - trailer / documentary look: letterbox bars, film grain, serif titles, Ken Burns shots and chapter cards. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  VT.template({
    theme: {
      palette: { bg: '#050505', deep: '#000000', ink: '#050505', paper: '#F2EDE4', accent: '#D8B26E', text: '#F2EDE4', muted: 'rgba(242,237,228,.65)' },
      captions: { style: 'line', color: '#F2EDE4', hl: '#D8B26E', box: 'rgba(0,0,0,0)', font: 'serif', weight: 600, size: 5, maxWords: 7 },
      transition: 'fade', tin: 0.8, tout: 0.7, sfx: { transition: null }, zones: { head: 0.16, cap: 0.14 },
    },
    background(layer) {
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 50%, #151311, #030303 75%)`);
      return null;
    },
    scenes: {
      // {text, sub, at, kicker}
      title: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const k = s.kicker ? VT.el(layer, `font-family:${VT.font('body')};font-weight:600;font-size:${3 * U}px;letter-spacing:.5em;color:${VT.col('accent')};white-space:nowrap`, VT.esc(s.kicker)) : null;
          const tt = VT.text(layer, s.text || '', { w: z.w * 0.86, h: z.h * 0.35, size: 11, font: 'serif', weight: 600, color: VT.col('text'), lh: 1.1, upper: VT.dir !== 'rtl' && s.upper !== false });
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.8, size: 4, font: 'serif', weight: 400, color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.4);
          VT.cue(at - 0.1, 'boom', { gain: -10 }); VT.cue(at + 0.1, 'sting', { gain: -18 });
          return (t) => {
            const cy = z.y + z.h * 0.47, p = P(t, at, 1.6);
            if (k) VT.place(k, VT.W / 2, cy - tt.offsetHeight / 2 - 6 * U, { o: C((t - at + 0.3) / 0.8) });
            tt.style.letterSpacing = L(0.2, 0.04, eo(p)) + 'em';
            VT.place(tt, VT.W / 2, cy, { s: 1 + (t - at) * 0.01, o: C((t - at) / 0.9) });
            if (sub) VT.place(sub, VT.W / 2, cy + tt.offsetHeight / 2 + 6 * U, { o: C((t - at - 1) / 0.8) });
          };
        },
      },
      // Full-frame image/video with slow push. {media, text, at, kenburns:{from:1.0, to:1.12, x:0.5, y:0.5}}
      shot: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const wrap = VT.el(layer, 'inset:0;overflow:hidden');
          const img = VT.media(wrap, s.media || 'broll', 'left:0;top:0;filter:contrast(1.06) saturate(.9)');
          const kb = s.kenburns || {}, k0 = kb.from || 1.02, k1 = kb.to || 1.14;
          wrap.style.transformOrigin = `${(kb.x == null ? 0.5 : kb.x) * 100}% ${(kb.y == null ? 0.45 : kb.y) * 100}%`;
          const tx = s.text ? VT.text(layer, s.text, { w: z.w * 0.8, size: 5.6, font: 'serif', weight: 600, color: VT.col('text') }) : null;
          const at = VT.time(s.at, s.start + 0.6);
          return (t, lt) => {
            img.update(t - s.start + (s.mediaOffset || 0));
            wrap.style.transform = `scale(${L(k0, k1, C(lt / Math.max(1, s.end - s.start)))})`;
            if (tx) VT.place(tx, VT.W / 2, z.y + z.h * 0.78, { o: C((t - at) / 0.8) });
          };
        },
      },
      // {n, title, at}
      chapter: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const n = s.n != null ? s.n : ctx.scenes.filter((x) => x.type === 'chapter').indexOf(s) + 1;
          const roman = (x) => { if (typeof x !== 'number') return x; const m = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']]; let r = ''; for (const [v, c] of m) while (x >= v) { r += c; x -= v; } return r; };
          const num = VT.el(layer, `font-family:${VT.font('serif')};font-weight:600;font-size:${16 * U}px;color:${VT.col('accent')};line-height:1`, VT.esc(s.numeral === 'arabic' ? VT.num(n) : roman(n)));
          const line = VT.el(layer, `height:${0.25 * U}px;width:${24 * U}px;background:${VT.col('accent')}`);
          const tt = VT.text(layer, s.title || '', { w: z.w * 0.8, h: z.h * 0.3, size: 7, font: 'serif', weight: 500, color: VT.col('text'), upper: VT.dir !== 'rtl' });
          const at = VT.time(s.at, s.start + 0.3);
          VT.cue(at, 'sting', { gain: -18 });
          return (t) => {
            const cy = z.y + z.h * 0.46;
            VT.place(num, VT.W / 2, cy - 12 * U, { o: C((t - at) / 0.7), y: (1 - eo(P(t, at, 1))) * 3 * U });
            VT.place(line, VT.W / 2, cy, { sx: eo(P(t, at + 0.3, 0.9)) });
            VT.place(tt, VT.W / 2, cy + 4 * U + tt.offsetHeight / 2, { o: C((t - at - 0.5) / 0.8) });
            tt.style.letterSpacing = L(0.3, 0.12, eo(P(t, at + 0.5, 1.6))) + 'em';
          };
        },
      },
      // {text, sub, at}
      end: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const tt = VT.text(layer, s.text || '', { w: z.w * 0.8, h: z.h * 0.3, size: 8, font: 'serif', weight: 600, color: VT.col('text'), upper: VT.dir !== 'rtl' });
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.8, size: 3.6, font: 'body', weight: 600, color: VT.col('accent') }) : null;
          const at = VT.time(s.at, s.start + 0.4);
          VT.cue(at, 'boom', { gain: -12 });
          return (t) => {
            const cy = z.y + z.h * 0.47;
            VT.place(tt, VT.W / 2, cy, { o: C((t - at) / 1) });
            tt.style.letterSpacing = L(0.25, 0.08, eo(P(t, at, 2))) + 'em';
            if (sub) VT.place(sub, VT.W / 2, cy + tt.offsetHeight / 2 + 6 * U, { o: C((t - at - 1) / 0.8) });
          };
        },
      },
    },
    overlays: [
      function letterbox(layer) {
        const U = VT.U;
        // 2.39:1 bars in landscape, slimmer bars in vertical formats
        const target = VT.orient === 'landscape' ? (VT.H - VT.W / 2.39) / 2 : VT.H * 0.06;
        const top = VT.el(layer, `left:0;right:0;top:0;height:${target}px;background:#000`);
        const bot = VT.el(layer, `left:0;right:0;bottom:0;height:${target}px;background:#000`);
        const grain = VT.el(layer, `inset:-5%;opacity:.08;background-image:radial-gradient(rgba(255,255,255,.9) ${0.06 * U}px, transparent ${0.12 * U}px);background-size:${0.9 * U}px ${1.1 * U}px`);
        const vig = VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 50%, transparent 55%, rgba(0,0,0,.55))`);
        return (t) => {
          const p = eo(P(t, 0, 1.2)), q = ei(P(t, VT.dur - 1, 1));
          top.style.transform = `translateY(${-(1 - p) * target + 0}px)`; bot.style.transform = `translateY(${(1 - p) * target}px)`;
          layer.style.opacity = 1;
          const f = Math.floor(t * 24);
          grain.style.transform = `translate(${(VT.hash(f) - 0.5) * 2 * U}px,${(VT.hash(f + 1) - 0.5) * 2 * U}px)`;
          vig.style.opacity = 1 - q * 0;
        };
      },
    ],
  });
})();
