/* top-five - countdown ranking: huge rank numbers, item cards with optional images, rank tracker, drumroll for #1. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const gold = () => VT.col('gold');

  VT.template({
    theme: {
      palette: { bg: '#140B26', deep: '#07030F', ink: '#140B26', paper: '#FFFFFF', gold: '#FFC83D', accent: '#FF3D7F', text: '#FFFFFF', muted: 'rgba(255,255,255,.65)' },
      captions: { style: 'pill', hl: '#FFC83D', hlText: '#140B26' },
      transition: 'push', sfx: { transition: 'whoosh', transitionGain: -15 }, zones: { head: 0.14 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 40%, #2B1353, #0A0515 75%)`);
      const rays = VT.el(layer, `left:50%;top:42%;width:${260 * U}px;height:${260 * U}px;margin:-${130 * U}px 0 0 -${130 * U}px;background:repeating-conic-gradient(rgba(255,200,61,.06) 0 8deg, transparent 8deg 20deg);border-radius:50%;mask-image:radial-gradient(circle, #000 10%, transparent 60%);-webkit-mask-image:radial-gradient(circle, #000 10%, transparent 60%)`);
      return (t) => { rays.style.transform = `rotate(${t * 6}deg)`; };
    },
    scenes: {
      // {title, sub, n, at}
      intro: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const n = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${Math.min(55 * U, z.h * 0.42)}px;line-height:.9;color:${gold()};text-shadow:0 ${2.4 * U}px 0 #8A5A00, 0 0 ${10 * U}px rgba(255,200,61,.45)`, VT.esc(VT.num(s.n || 5)));
          const top = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${9 * U}px;color:#fff;letter-spacing:.04em`, VT.esc(s.kicker || VT.label(s, 'top', 'TOP')));
          const tt = VT.text(layer, s.title || '', { w: z.w * 0.9, h: z.h * 0.25, size: 8.4, color: '#fff' });
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.85, size: 4.6, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'impact', { gain: -9 }); VT.cue(at + 0.5, 'whoosh', { gain: -18 });
          return (t) => {
            const cy = z.y + z.h * 0.38;
            VT.place(top, VT.W / 2, cy - n.offsetHeight / 2 - 3 * U, { o: C((t - at) / 0.2), y: (1 - eo(P(t, at, 0.4))) * -4 * U });
            VT.place(n, VT.W / 2, cy + 3 * U, { s: L(2.5, 1, eo(P(t, at, 0.4))), o: C((t - at) / 0.1) });
            const r = VT.rise(t, at + 0.5, 0.45, 5); VT.place(tt, VT.W / 2, cy + n.offsetHeight / 2 + tt.offsetHeight / 2 + 6 * U, { y: r.y, o: r.o });
            if (sub) { const r2 = VT.rise(t, at + 0.8, 0.45, 4); VT.place(sub, VT.W / 2, cy + n.offsetHeight / 2 + tt.offsetHeight + 11 * U, { y: r2.y, o: r2.o }); }
          };
        },
      },
      // {n, title, subtitle, media, at, drumroll}
      rank: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full, land = VT.orient === 'landscape';
          const ranks = ctx.scenes.filter((x) => x.type === 'rank');
          const n = s.n != null ? s.n : ranks.length - ranks.indexOf(s);
          const one = +n === 1;
          const hasMedia = !!s.media && VT.hasMedia(s.media);
          const at = VT.time(s.at, s.start + (one ? 1.2 : 0.2));
          const num = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;line-height:.85;color:${one ? gold() : '#fff'};-webkit-text-stroke:${one ? 0 : 0.5 * U}px ${gold()};${one ? '' : 'color:transparent;'}white-space:nowrap;direction:ltr`, `#${VT.esc(VT.num(n))}`);
          num.style.fontSize = (hasMedia ? 26 : VT.orient !== 'portrait' ? 30 : 42) * U + 'px';
          let frame = null, img = null;
          const mw = land ? z.h * 0.68 : Math.min(z.w * 0.86, 80 * U), mh = land ? z.h * 0.68 : Math.min(z.h * 0.4, mw * 0.8);
          if (hasMedia) {
            frame = VT.el(layer, `width:${mw}px;height:${mh}px;border-radius:${3 * U}px;overflow:hidden;box-shadow:0 0 0 ${0.6 * U}px ${one ? gold() : 'rgba(255,255,255,.25)'},0 ${3 * U}px ${8 * U}px rgba(0,0,0,.5)`);
            img = VT.media(frame, s.media, 'left:0;top:0');
          }
          const tw = land && hasMedia ? z.w - mw - 12 * U : z.w * 0.92;
          const tt = VT.text(layer, s.title || '', { w: tw, h: 22 * U, size: one ? 10 : 8.6, color: one ? gold() : '#fff', align: land && hasMedia ? 'start' : 'center' });
          const st = s.subtitle ? VT.text(layer, s.subtitle, { w: tw, h: 14 * U, size: 4.6, weight: 600, font: 'body', color: VT.col('muted'), align: land && hasMedia ? 'start' : 'center' }) : null;
          if (one && s.drumroll !== false) { VT.cue(Math.max(s.start, at - 1.2), 'drumroll', { dur: Math.min(1.15, at - s.start), gain: -12 }); VT.cue(at, 'impact', { gain: -7 }); VT.cue(at + 0.05, 'sparkle', { gain: -14 }); VT.cue(at + 0.1, 'success', { gain: -14 }); }
          else { VT.cue(at, 'impact', { gain: -13 }); VT.cue(at + 0.35, 'pop', { gain: -18 }); }
          const conf = one ? Array.from({ length: 40 }, (_, i) => VT.el(layer, `width:${1.2 * U}px;height:${2.2 * U}px;border-radius:${0.3 * U}px;background:${['#FFC83D', '#FF3D7F', '#3DDCFF', '#B6FF5C', '#fff'][i % 5]}`)) : [];
          return (t) => {
            const p = P(t, at, 0.45), hitS = L(2.2, 1, eo(p)), lt = t - at;
            if (land && hasMedia) {
              const mx = VT.W / 2 - (z.w / 2 - mw / 2) * VT.sign, tx = VT.W / 2 + (z.w / 2 - tw / 2) * VT.sign, cy = z.y + z.h / 2;
              VT.place(frame, mx, cy, { s: L(0.85, 1, eo(P(t, at + 0.1, 0.5))), o: C((t - at - 0.1) / 0.2) });
              img.update(t - s.start); img.style.transform = `scale(${1.05 + Math.max(0, lt) * 0.01})`;
              VT.place(num, tx - (tw / 2 - num.offsetWidth / 2) * VT.sign, cy - tt.offsetHeight / 2 - num.offsetHeight / 2 - 3 * U, { s: hitS, o: C(p * 5) });
              const r = VT.rise(t, at + 0.3, 0.45, 4); VT.place(tt, tx, cy, { y: r.y, o: r.o });
              if (st) { const r2 = VT.rise(t, at + 0.5, 0.45, 3); VT.place(st, tx, cy + tt.offsetHeight / 2 + st.offsetHeight / 2 + 2 * U, { y: r2.y, o: r2.o }); }
            } else {
              let y = z.y + (hasMedia ? 11 * U : VT.orient !== 'portrait' ? 9 * U : z.h * 0.28);
              VT.place(num, VT.W / 2, y + num.offsetHeight / 2, { s: hitS, o: C(p * 5), r: one ? Math.sin(lt * 3) * 2 * C(lt) : 0 });
              y += num.offsetHeight + 3 * U;
              if (hasMedia) { VT.place(frame, VT.W / 2, y + mh / 2, { s: L(0.85, 1, eo(P(t, at + 0.1, 0.5))), o: C((t - at - 0.1) / 0.2) }); img.update(t - s.start); img.style.transform = `scale(${1.05 + Math.max(0, lt) * 0.01})`; y += mh + 4 * U; }
              const r = VT.rise(t, at + 0.3, 0.45, 4); VT.place(tt, VT.W / 2, y + tt.offsetHeight / 2, { y: r.y, o: r.o }); y += tt.offsetHeight + 2 * U;
              if (st) { const r2 = VT.rise(t, at + 0.5, 0.45, 3); VT.place(st, VT.W / 2, y + st.offsetHeight / 2, { y: r2.y, o: r2.o }); }
            }
            conf.forEach((c, i) => {
              const k = lt - VT.hash(i) * 0.2; if (k < 0) { c.style.opacity = 0; return; }
              const ang = VT.hash(i + 11) * Math.PI * 2, v = (30 + VT.hash(i + 3) * 60) * U;
              VT.tf(c, { x: VT.W / 2 + Math.cos(ang) * v * k, y: z.y + z.h * 0.35 + Math.sin(ang) * v * k * 0.8 + 60 * U * k * k, r: k * 400 * (VT.hash(i) - 0.5), o: C(1.6 - k) });
            });
          };
        },
      },
    },
    overlays: [
      function tracker(layer) {
        const ranks = VT.plan.scenes.filter((s) => s.type === 'rank');
        if (ranks.length < 2) return null;
        const U = VT.U, z = VT.Z.area, sz = 7 * U;
        const nums = ranks.map((s, i) => { const n = s.n != null ? s.n : ranks.length - i; return { s, e: VT.el(layer, `width:${sz}px;height:${sz}px;border-radius:${2 * U}px;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${3.6 * U}px`, VT.esc(VT.num(n))) }; });
        const first = ranks[0].start, last = ranks[ranks.length - 1].end;
        return (t) => {
          const vis = eo(P(t, first, 0.4)) * (1 - ei(P(t, last, 0.3)));
          nums.forEach((o, i) => {
            const on = t >= o.s.start && t < o.s.end, done = t >= o.s.end;
            o.e.style.background = on ? VT.col('gold') : done ? 'rgba(255,255,255,.18)' : 'rgba(255,255,255,.07)';
            o.e.style.color = on ? VT.col('ink') : done ? '#fff' : 'rgba(255,255,255,.4)';
            const k = (i - (nums.length - 1) / 2) * (sz + 1.4 * U) * VT.sign; VT.place(o.e, VT.W / 2 + k, z.y + sz / 2 + U, { s: on ? 1.12 : 1, o: vis });
          });
        };
      },
    ],
  });
})();
