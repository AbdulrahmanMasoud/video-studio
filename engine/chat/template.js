/* chat - an AI chat conversation: typing dots, streamed replies, auto-scroll and a result card. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function windowBox() {
    const z = VT.Z.full, U = VT.U;
    const w = Math.min(z.w, VT.orient === 'landscape' ? 1.15 * VT.H : 96 * U);
    return { x: VT.W / 2 - w / 2, y: z.y + U, w, h: z.h - 2 * U };
  }

  VT.template({
    theme: {
      palette: { bg: '#0D1020', deep: '#070914', ink: '#141827', paper: '#FFFFFF', window: '#F6F7FB', ai: '#FFFFFF', user: '#5B5BF7', userText: '#FFFFFF', accent: '#8B8BFF', good: '#22C55E', text: '#FFFFFF', muted: 'rgba(20,24,39,.5)' },
      captions: { style: 'line', color: '#FFFFFF', hl: '#B6B6FF', box: 'rgba(13,16,32,.82)' },
      transition: 'fade', sfx: { transition: 'swoosh', transitionGain: -20 }, zones: { head: 0.14, cap: 0.12 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:linear-gradient(160deg,#171B3A,#0B0D1A 60%)`);
      const blobs = [['#5B5BF7', 0.2, 0.2], ['#C04BF2', 0.85, 0.35], ['#2BB8F2', 0.5, 0.95]].map(([c]) => VT.el(layer, `width:${90 * U}px;height:${90 * U}px;border-radius:50%;background:radial-gradient(circle,${c}55,${c}00 65%)`));
      return (t) => blobs.forEach((b, i) => VT.place(b, VT.W * [0.2, 0.85, 0.5][i] + Math.sin(t * 0.3 + i * 2) * 12 * U, VT.H * [0.2, 0.35, 0.95][i] + Math.cos(t * 0.25 + i) * 10 * U));
    },
    scenes: {
      // {title, sub, messages:[{from:'user'|'ai', text, at, end, react}]}
      chat: {
        build(s, layer) {
          const U = VT.U, B = windowBox();
          const win = VT.el(layer, `left:${B.x}px;top:${B.y}px;width:${B.w}px;height:${B.h}px;border-radius:${4 * U}px;background:${VT.col('window')};overflow:hidden;box-shadow:0 ${3 * U}px ${8 * U}px rgba(0,0,0,.45)`);
          const hh = 12 * U;
          const head = VT.el(win, `left:0;top:0;right:0;height:${hh}px;display:flex;align-items:center;gap:${2.2 * U}px;padding:0 ${3.4 * U}px;background:#fff;border-bottom:${0.25 * U}px solid rgba(0,0,0,.07);z-index:2;direction:${VT.dir}`,
            `<div style="width:${7.4 * U}px;height:${7.4 * U}px;border-radius:50%;background:linear-gradient(135deg,${VT.col('user')},#C04BF2);display:flex;align-items:center;justify-content:center">${VT.icon('star', '#fff', '58%')}</div>` +
            `<div style="flex:1;min-width:0"><div class="n" style="font-family:${VT.font('display')};font-weight:800;font-size:${3.9 * U}px;color:${VT.col('ink')};white-space:nowrap;overflow:hidden;text-overflow:ellipsis"></div><div class="st" style="font-family:${VT.font('body')};font-size:${2.7 * U}px;color:${VT.col('good')};font-weight:600"></div></div>`);
          head.querySelector('.n').textContent = s.title || VT.label(s, 'assistant', 'AI Assistant');
          const status = head.querySelector('.st');
          const view = VT.el(win, `left:0;right:0;top:${hh}px;bottom:0;overflow:hidden`);
          const feed = VT.el(view, `left:0;right:0;top:0;padding:${3 * U}px ${3 * U}px;display:flex;flex-direction:column;gap:${2.2 * U}px;direction:${VT.dir}`);
          const msgs = (s.messages || []).map((m, i) => {
            const ai = m.from !== 'user';
            const at = VT.time(m.at, s.start + 0.6 + i * 1.6);
            const len = VT.graphemes(m.text || '').length;
            const end = VT.time(m.end, at + (ai ? Math.min(3.5, 0.35 + len * 0.028) : Math.min(1.6, 0.3 + len * 0.03)));
            const row = VT.el(feed, `position:relative;display:flex;justify-content:${ai ? 'flex-start' : 'flex-end'}`);
            const bub = VT.el(row, `position:relative;max-width:82%;padding:${2 * U}px ${3 * U}px ${2.4 * U}px;border-radius:${3.4 * U}px;font-family:${VT.font('body')};font-weight:500;font-size:${3.9 * U}px;line-height:1.45;white-space:pre-wrap;` +
              (ai ? `background:${VT.col('ai')};color:${VT.col('ink')};border-end-start-radius:${U}px;box-shadow:0 ${0.4 * U}px ${1.2 * U}px rgba(0,0,0,.08)` : `background:${VT.col('user')};color:${VT.col('userText')};border-end-end-radius:${U}px`));
            const dots = ai ? VT.el(row, `position:relative;padding:${2.6 * U}px ${3.4 * U}px;border-radius:${3.4 * U}px;background:#fff;display:flex;gap:${U}px;box-shadow:0 ${0.4 * U}px ${1.2 * U}px rgba(0,0,0,.08)`, [0, 1, 2].map(() => `<i style="width:${1.5 * U}px;height:${1.5 * U}px;border-radius:50%;background:#9AA0B4;display:block"></i>`).join('')) : null;
            const react = m.react ? VT.el(bub, `bottom:${-2.4 * U}px;${ai ? 'inset-inline-end' : 'inset-inline-start'}:${-1.2 * U}px;width:${6.4 * U}px;height:${6.4 * U}px;border-radius:50%;background:#fff;box-shadow:0 ${0.4 * U}px ${U}px rgba(0,0,0,.2);display:flex;align-items:center;justify-content:center`, VT.icon(m.react, m.react === 'heart' ? '#FF4D6D' : m.react === 'fire' ? '#FF7A1F' : '#F5B400', '60%')) : null;
            const typeFrom = ai ? at - (m.think == null ? 0.9 : m.think) : at;
            if (ai) { VT.cue(typeFrom, 'bubble', { gain: -22 }); VT.cue(at, 'notify', { gain: -18 }); VT.typingCue(at, end, -30); }
            else { VT.typingCue(at, end, -26); VT.cue(end + 0.05, 'send', { gain: -14 }); }
            if (react) VT.cue(end + 0.5, 'pop-high', { gain: -16 });
            return { m, ai, at, end, row, bub, dots, react, typeFrom };
          });
          const pad = 3 * U, viewH = B.h - hh;
          return (t) => {
            let y = pad, anyTyping = false;
            msgs.forEach((x) => {
              const shown = t >= x.typeFrom;
              x.row.style.display = shown ? 'flex' : 'none';
              if (!shown) return;
              const thinking = x.ai && t < x.at;
              if (x.dots) { x.dots.style.display = thinking ? 'flex' : 'none'; Array.from(x.dots.children).forEach((d, k) => { d.style.transform = `translateY(${-Math.max(0, Math.sin(t * 9 - k * 0.8)) * 0.9 * U}px)`; }); }
              x.bub.style.display = thinking ? 'none' : 'block';
              if (thinking) anyTyping = true;
              if (!thinking) {
                // user text appears as if sent; AI text streams word by word
                const txt = x.ai ? VT.type(x.m.text || '', t, x.at, x.end) : (t >= x.end ? x.m.text : VT.type(x.m.text || '', t, x.at, x.end));
                if (x.bub._t !== txt) { x.bub.firstChild && x.bub.firstChild.nodeType === 3 ? (x.bub.firstChild.nodeValue = txt) : x.bub.insertBefore(document.createTextNode(txt), x.bub.firstChild); x.bub._t = txt; }
                if (x.ai && t < x.end) anyTyping = true;
                if (x.react) { const rp = P(t, x.end + 0.5, 0.4); x.react.style.transform = `scale(${L(0, 1, sp(rp))})`; x.react.style.opacity = C(rp * 4); }
              }
              const p = P(t, x.typeFrom, 0.35);
              x.row.style.transform = `translateY(${(1 - eo(p)) * 4 * U}px) scale(${L(0.92, 1, eo(p))})`;
              x.row.style.transformOrigin = x.ai === (VT.dir === 'rtl') ? 'right bottom' : 'left bottom';
              x.row.style.opacity = C(p * 3);
            });
            const total = feed.offsetHeight;
            feed.style.transform = `translateY(${-Math.max(0, total - viewH + pad)}px)`;
            status.textContent = anyTyping ? VT.label(s, 'typing', 'typing…') : VT.label(s, 'online', 'online');
            const wp = P(t, s.start, 0.45);
            win.style.transform = `translateY(${(1 - eo(wp)) * 8 * U}px)`; win.style.opacity = C(wp * 3);
          };
        },
      },
      // {title, text, at, icon}
      result: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 92);
          const k = VT.card(layer, { bg: '#fff', fg: VT.col('ink'), shadow: 'rgba(0,0,0,.35)', css: `width:${col.w}px;padding:${10 * U}px ${5 * U}px ${5 * U}px;text-align:center` });
          k.innerHTML = `<div class="h" style="font-family:${VT.font('display')};font-weight:900;font-size:${6.6 * U}px;color:${VT.col('user')};margin-bottom:${1.6 * U}px"></div><div class="b" style="font-family:${VT.font('body')};font-weight:600;font-size:${4.8 * U}px;line-height:1.4"></div>`;
          k.querySelector('.h').textContent = s.title || ''; k.querySelector('.b').textContent = s.text || '';
          VT.fit(k, col.w, z.h * 0.8, 3);
          const b = VT.badge(layer, s.icon || 'check', VT.col('good'), '#fff', 14);
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); VT.cue(at + 0.3, 'success', { gain: -13 });
          return (t) => {
            const p = P(t, at, 0.5), cy = z.y + z.h * 0.5;
            VT.place(k, VT.W / 2, cy, { s: L(0.85, 1, sp(p)), o: C(p * 3) });
            const q = P(t, at + 0.3, 0.45); VT.place(b, VT.W / 2, cy - k.offsetHeight / 2, { s: L(0.2, 1, sp(q)), o: C(q * 4) });
          };
        },
      },
    },
  });
})();
