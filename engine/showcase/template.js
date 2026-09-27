/* showcase - product launch / ad: product on a lit pedestal, feature chips, price slam and a CTA button. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function productArt(p, size) {
    // Neutral placeholder product (a sleek bottle/box) when no image is supplied.
    const a = VT.col('accent');
    return VT.el(p, `width:${size}px;height:${size}px`, `<svg viewBox="0 0 200 200" width="100%" height="100%"><defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#2A2A31"/><stop offset=".55" stop-color="#4A4A55"/><stop offset="1" stop-color="#1C1C22"/></linearGradient></defs><rect x="62" y="18" width="76" height="22" rx="6" fill="${a}"/><rect x="50" y="36" width="100" height="148" rx="22" fill="url(#pg)"/><rect x="62" y="48" width="14" height="120" rx="7" fill="rgba(255,255,255,.18)"/><rect x="72" y="96" width="56" height="36" rx="6" fill="${a}"/></svg>`);
  }

  VT.template({
    theme: {
      palette: { bg: '#F3EFE9', deep: '#D9D1C4', ink: '#17161A', paper: '#FFFFFF', accent: '#FF5C35', alt: '#17161A', text: '#17161A', muted: 'rgba(23,22,26,.6)', good: '#1BAA6E' },
      captions: { style: 'pill', hl: '#FF5C35', hlText: '#FFFFFF', color: '#17161A', shadow: 'rgba(255,255,255,.85)' },
      transition: 'slide', sfx: { transition: 'whoosh', transitionGain: -17 }, zones: { head: 0.14 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 42%, #FFFFFF, #EAE3D8 70%)`);
      const ring = VT.el(layer, `width:${120 * U}px;height:${120 * U}px;border-radius:50%;border:${0.3 * U}px solid rgba(23,22,26,.07)`);
      const ring2 = VT.el(layer, `width:${80 * U}px;height:${80 * U}px;border-radius:50%;border:${0.3 * U}px solid rgba(23,22,26,.06)`);
      return (t) => { VT.place(ring, VT.W / 2, VT.H * 0.42, { s: 1 + Math.sin(t * 0.5) * 0.03 }); VT.place(ring2, VT.W / 2, VT.H * 0.42, { s: 1 + Math.cos(t * 0.6) * 0.04 }); };
    },
    scenes: {
      // {name, tagline, media, features:[{text, at, icon}], price, oldPrice, currency, priceAt, badge, at}
      product: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, land = VT.orient !== 'portrait';
          // portrait: product on top, text stack below, whole group centred vertically
          const nF = Math.min(4, (s.features || []).length);
          const textH = 13 * U + (s.tagline ? 11 * U : 0) + nF * 7.2 * U + (s.price != null ? 15 * U : 0);
          const size = land ? z.h * 0.62 : Math.max(24 * U, Math.min(z.w * 0.72, z.h - textH - 8 * U));
          const cx = land ? VT.W / 2 - z.w * 0.2 * VT.sign : VT.W / 2, cy = land ? z.y + z.h * 0.48 : z.y + Math.max(0, (z.h - size - 6 * U - textH) / 2) + size / 2;
          const glow = VT.el(layer, `width:${size * 1.3}px;height:${size * 1.3}px;border-radius:50%;background:radial-gradient(circle, ${VT.col('accent')}33, transparent 62%)`);
          const shadow = VT.el(layer, `width:${size * 0.8}px;height:${size * 0.12}px;border-radius:50%;background:radial-gradient(ellipse, rgba(0,0,0,.28), transparent 70%)`);
          let prod;
          if (s.media && VT.hasMedia(s.media)) { prod = VT.el(layer, `width:${size}px;height:${size}px`); const im = VT.media(prod, s.media, 'left:0;top:0;object-fit:contain'); im.style.objectFit = 'contain'; prod._img = im; }
          else prod = productArt(layer, size);
          const at = VT.time(s.at, s.start + 0.2);
          const name = VT.text(layer, s.name || '', { w: land ? z.w * 0.42 : z.w * 0.9, h: 16 * U, size: 9, weight: 900, color: VT.col('ink'), align: land ? 'start' : 'center' });
          const tag = s.tagline ? VT.text(layer, s.tagline, { w: land ? z.w * 0.42 : z.w * 0.85, h: 12 * U, size: 4.6, weight: 600, font: 'body', color: VT.col('muted'), align: land ? 'start' : 'center' }) : null;
          const badge = s.badge ? VT.el(layer, `background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${3.6 * U}px;padding:${0.8 * U}px ${2.4 * U}px ${1.1 * U}px;border-radius:${4 * U}px;letter-spacing:.06em;white-space:nowrap`, VT.esc(s.badge)) : null;
          const feats = (s.features || []).slice(0, 4).map((f, i) => {
            const e = VT.el(layer, `display:flex;align-items:center;gap:${1.2 * U}px;background:#fff;color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:800;font-size:${3.8 * U}px;padding:${1.1 * U}px ${2.6 * U}px ${1.4 * U}px ${1.4 * U}px;border-radius:${4 * U}px;box-shadow:0 ${0.8 * U}px ${2.4 * U}px rgba(0,0,0,.12);white-space:nowrap`,
              `<span style="width:${4.4 * U}px;height:${4.4 * U}px;border-radius:50%;background:${VT.col('accent')};display:flex;align-items:center;justify-content:center">${VT.icon(f.icon || 'check', '#fff', '70%')}</span>${VT.esc(f.text || f)}`);
            VT.fit(e, land ? z.w * 0.42 : z.w * 0.9);
            const fa = VT.time(f.at, at + 1 + i * 0.5); VT.cue(fa, 'pop', { gain: -16, pan: i % 2 ? 0.35 : -0.35 });
            return { e, fa, i };
          });
          let price = null, old = null, pa = null;
          if (s.price != null) {
            pa = VT.time(s.priceAt, (feats.length ? feats[feats.length - 1].fa : at) + 0.9);
            price = VT.el(layer, `background:${VT.col('ink')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${8 * U}px;padding:${1 * U}px ${3.4 * U}px ${1.6 * U}px;border-radius:${2.4 * U}px;white-space:nowrap;direction:ltr`, VT.esc(`${s.currency || '$'}${typeof s.price === 'number' ? VT.num(s.price, s.price % 1 ? 2 : 0) : s.price}`));
            if (s.oldPrice != null) old = VT.el(layer, `font-family:${VT.font('display')};font-weight:800;font-size:${5 * U}px;color:${VT.col('muted')};text-decoration:line-through ${0.4 * U}px ${VT.col('accent')};white-space:nowrap;direction:ltr`, VT.esc(`${s.currency || '$'}${s.oldPrice}`));
            VT.cue(pa - 0.02, 'impact', { gain: -12 }); VT.cue(pa + 0.05, 'cash', { gain: -12 });
          }
          VT.cue(at, 'whoosh', { gain: -16 }); VT.cue(at + 0.35, 'sparkle', { gain: -18 });
          return (t) => {
            const p = P(t, at, 0.7), fl = Math.sin(t * 1.6) * 1.2 * U;
            VT.place(glow, cx, cy, { s: L(0.6, 1, eo(p)) * (1 + Math.sin(t * 2) * 0.03), o: C(p * 2) });
            VT.place(shadow, cx, cy + size * 0.5, { sx: L(0.4, 1, eo(p)) * (1 - fl / (30 * U)), o: C(p * 2) });
            VT.place(prod, cx, cy + fl - size * 0.02, { y: (1 - eo(p)) * 15 * U, s: L(0.7, 1, eo(p)), r: L(-8, 0, eo(p)) + Math.sin(t * 0.8) * 1.2, o: C(p * 3) });
            if (prod._img) prod._img.update(t - s.start);
            // text block
            let tx = land ? VT.W / 2 + z.w * 0.24 * VT.sign : VT.W / 2, ty = land ? z.y + z.h * 0.2 : cy + size / 2 + 6 * U;
            if (badge) { const bp = P(t, at + 0.2, 0.4); VT.place(badge, land ? tx - (z.w * 0.21 - badge.offsetWidth / 2) * VT.sign : cx + size * 0.38 * VT.sign, land ? ty : cy - size * 0.45, { s: L(0.3, 1, sp(bp)), r: land ? 0 : 8, o: C(bp * 4) }); if (land) ty += badge.offsetHeight + 3 * U; }
            const nr = VT.rise(t, at + 0.3, 0.5, 4); VT.place(name, tx, ty + name.offsetHeight / 2, { y: nr.y, o: nr.o }); ty += name.offsetHeight + 1.5 * U;
            if (tag) { const r2 = VT.rise(t, at + 0.5, 0.5, 3); VT.place(tag, tx, ty + tag.offsetHeight / 2, { y: r2.y, o: r2.o }); ty += tag.offsetHeight + 3 * U; }
            feats.forEach((f) => {
              const fp = P(t, f.fa, 0.45);
              let fx, fy;
              if (land) { fx = tx - (z.w * 0.21 - f.e.offsetWidth / 2) * VT.sign; fy = ty + f.e.offsetHeight / 2; ty += f.e.offsetHeight + 1.6 * U; }
              else { fx = VT.W / 2; fy = ty + f.e.offsetHeight / 2; ty += f.e.offsetHeight + 1.4 * U; }
              VT.place(f.e, fx, fy, { s: L(0.5, 1, sp(fp)), o: C(fp * 4), y: Math.sin(t * 1.4 + f.i) * 0.5 * U });
            });
            if (price) {
              const pp = P(t, pa, 0.35);
              const px = land ? tx - (z.w * 0.21 - price.offsetWidth / 2) * VT.sign : VT.W / 2, py = land ? ty + 2 * U + price.offsetHeight / 2 : Math.min(ty + price.offsetHeight / 2, z.y + z.h - price.offsetHeight / 2);
              VT.place(price, px, land ? py : py + 2 * U, { s: L(2.2, 1, eo(pp)), r: -3, o: C(pp * 5) });
              if (old) VT.place(old, px + (price.offsetWidth / 2 + old.offsetWidth / 2 + 2 * U) * VT.sign, py, { o: C((t - pa - 0.2) / 0.2) });
            }
          };
        },
      },
      // {text, button, sub, at}
      cta: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const tx = VT.text(layer, s.text || '', { w: z.w * 0.9, h: z.h * 0.3, size: 9, color: VT.col('ink') });
          const btn = VT.el(layer, `background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${6 * U}px;padding:${2.2 * U}px ${7 * U}px ${2.6 * U}px;border-radius:${6 * U}px;box-shadow:0 ${1.4 * U}px 0 #B8391B;white-space:nowrap`, VT.esc(s.button || VT.label(s, 'shop', 'Shop now')));
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.85, size: 4.2, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const hand = VT.el(layer, `width:${9 * U}px;height:${9 * U}px`, `<svg viewBox="0 0 24 24" width="100%" height="100%"><path d="M9 11V5.5a1.5 1.5 0 0 1 3 0V10l5.3.9a2 2 0 0 1 1.6 2.3l-.9 5A3 3 0 0 1 15 21h-3.6a3 3 0 0 1-2.4-1.2L5.5 15a1.5 1.5 0 0 1 2.2-2L9 14.4Z" fill="#fff" stroke="#17161A" stroke-width="1.4" stroke-linejoin="round"/></svg>`);
          const at = VT.time(s.at, s.start + 0.2), tap = at + 1.1;
          VT.cue(at, 'pop-low', { gain: -12 }); VT.cue(tap, 'click', { gain: -8 }); VT.cue(tap + 0.1, 'success', { gain: -14 });
          return (t) => {
            const cy = z.y + z.h * 0.42;
            const r = VT.rise(t, at, 0.5, 5); VT.place(tx, VT.W / 2, cy - 8 * U, { y: r.y, o: r.o });
            const bp = P(t, at + 0.4, 0.45), press = t > tap && t < tap + 0.15 ? 0.92 : 1, pulse = t > tap + 0.3 ? 1 + Math.sin((t - tap) * 6) * 0.03 : 1;
            const by = cy + tx.offsetHeight / 2 + 6 * U;
            VT.place(btn, VT.W / 2, by, { s: L(0.4, 1, sp(bp)) * press * pulse, o: C(bp * 4) });
            const hp = eo(P(t, tap - 0.6, 0.55));
            VT.place(hand, VT.W / 2 + L(20 * U, 4 * U, hp), by + L(18 * U, 4 * U, hp), { s: press < 1 ? 0.9 : 1, o: C((t - tap + 0.6) / 0.2) * (1 - P(t, tap + 0.8, 0.3)) });
            if (sub) { const r2 = VT.rise(t, at + 0.7, 0.45, 3); VT.place(sub, VT.W / 2, by + btn.offsetHeight / 2 + 6 * U, { y: r2.y, o: r2.o }); }
          };
        },
      },
    },
  });
})();
