/* terminal - developer terminal: typed commands, colored output, auto-scroll, zoom-ins and callouts. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const KIND = { cmd: 'text', out: 'dim', ok: 'ok', err: 'err', warn: 'warn', hl: 'text', comment: 'comment' };
  const MARK = { ok: '✔ ', err: '✖ ', warn: '▲ ' };

  VT.template({
    theme: {
      palette: { bg: '#0A0E14', deep: '#000000', ink: '#0A0E14', paper: '#11161F', window: '#0F141C', bar: '#1A212D', text: '#E6EDF3', dim: '#9AA7B8', prompt: '#7EE787', ok: '#3FB950', err: '#FF6B6B', warn: '#E3B341', comment: '#6E7B8B', accent: '#58A6FF', hlbg: 'rgba(88,166,255,.22)', muted: 'rgba(230,237,243,.6)' },
      captions: { style: 'boxed', color: '#E6EDF3', hl: '#7EE787', box: 'rgba(10,14,20,.88)', font: 'display' },
      transition: 'fade', sfx: { transition: 'click', transitionGain: -18 }, zones: { head: 0.12, cap: 0.12 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 20%, #142033, #070A0F 70%)`);
      const grid = VT.el(layer, `inset:-${10 * U}px;opacity:.5;background-image:linear-gradient(rgba(88,166,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(88,166,255,.06) 1px,transparent 1px);background-size:${8 * U}px ${8 * U}px`);
      return (t) => { grid.style.transform = `translateY(${(t * 1.5 * U) % (8 * U)}px)`; };
    },
    scenes: {
      // {title, prompt, lines:[{text, at, end, kind: cmd|out|ok|err|warn|hl|comment}], zoomAt, zoomEnd, zoom}
      terminal: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const w = Math.min(z.w, VT.orient === 'landscape' ? 1.35 * VT.H : 96 * U), h = z.h - 2 * U;
          const x0 = VT.W / 2 - w / 2, y0 = z.y + U;
          const win = VT.el(layer, `left:${x0}px;top:${y0}px;width:${w}px;height:${h}px;border-radius:${2.6 * U}px;background:${VT.col('window')};overflow:hidden;box-shadow:0 ${3 * U}px ${9 * U}px rgba(0,0,0,.6),0 0 0 ${0.25 * U}px rgba(255,255,255,.08)`);
          const bh = 7 * U;
          VT.el(win, `left:0;right:0;top:0;height:${bh}px;background:${VT.col('bar')};display:flex;align-items:center;gap:${1.3 * U}px;padding:0 ${2.6 * U}px;direction:ltr`,
            ['#FF5F57', '#FEBC2E', '#28C840'].map((c) => `<i style="display:block;width:${2 * U}px;height:${2 * U}px;border-radius:50%;background:${c}"></i>`).join('') +
            `<div style="flex:1;text-align:center;font-family:${VT.font('mono')};font-size:${2.7 * U}px;color:${VT.col('dim')};margin-inline-end:${8 * U}px">${VT.esc(s.title || 'zsh')}</div>`);
          const view = VT.el(win, `left:0;right:0;top:${bh}px;bottom:0;overflow:hidden`);
          const fsz = (s.fontSize || (VT.orient === 'portrait' ? 3.6 : 3.5)) * U;
          const feed = VT.el(view, `left:0;right:0;top:0;padding:${2.6 * U}px ${3 * U}px;font-family:${VT.font('mono')};font-size:${fsz}px;line-height:1.55;direction:ltr;text-align:left;white-space:pre-wrap;word-break:break-word`);
          const prompt = s.prompt == null ? '$ ' : s.prompt;
          let tcur = s.start + 0.4;
          const lines = (s.lines || []).map((ln) => {
            const kind = ln.kind || 'out', cmd = kind === 'cmd';
            const at = VT.time(ln.at, tcur);
            const len = VT.graphemes(ln.text || '').length;
            const end = cmd ? VT.time(ln.end, at + Math.min(2.2, 0.15 + len * 0.045)) : at;
            tcur = end + (cmd ? 0.35 : 0.12);
            const e = VT.el(feed, `position:relative;color:${VT.col(KIND[kind] || 'text')};${kind === 'hl' ? `background:${VT.col('hlbg')};border-radius:${0.8 * U}px;padding:0 ${U}px;margin:0 -${U}px;` : ''}`);
            if (cmd) { VT.typingCue(at, end, -24); VT.cue(end + 0.08, 'key', { gain: -12 }); }
            else if (kind === 'ok') VT.cue(at, 'success', { gain: -18 });
            else if (kind === 'err') VT.cue(at, 'error', { gain: -14 });
            else if (kind === 'warn') VT.cue(at, 'beep', { gain: -20 });
            return { ln, kind, cmd, at, end, e };
          });
          const zA = VT.time(s.zoomAt, null), zE = VT.time(s.zoomEnd, zA != null ? zA + 2.5 : null), zk = s.zoom || 1.45;
          if (zA != null) VT.cue(zA - 0.1, 'whoosh', { gain: -20 });
          return (t) => {
            let active = null;
            lines.forEach((x) => {
              const on = t >= x.at - 0.001; x.e.style.display = on ? 'block' : 'none'; if (!on) return;
              const pre = x.cmd ? `<span style="color:${VT.col('prompt')}">${VT.esc(prompt)}</span>` : (MARK[x.kind] ? `<span>${MARK[x.kind]}</span>` : '');
              const body = x.cmd ? VT.esc(VT.type(x.ln.text || '', t, x.at, x.end)) : VT.esc(x.ln.text || '');
              const car = x.cmd && t < x.end + 0.35 ? VT.caret(t, VT.col('text')) : '';
              const html = pre + body + car;
              if (x.e._h !== html) { x.e.innerHTML = html; x.e._h = html; }
              if (!x.cmd) x.e.style.opacity = C((t - x.at) / 0.12);
              active = x;
            });
            // idle prompt with blinking caret after the last command finished
            const vh = h - bh - 5 * U;
            const total = feed.offsetHeight;
            const sc = Math.max(0, total - vh);
            feed.style.transform = `translateY(${-sc}px)`;
            // camera zoom toward the latest line
            let k = 1, oy = 0;
            if (zA != null) { const zi = eo(P(t, zA, 0.6)) * (1 - eo(P(t, zE, 0.5))); k = L(1, zk, zi); if (active) { const ay = y0 + bh + active.e.offsetTop - sc + active.e.offsetHeight / 2; oy = (z.y + z.h / 2 - ay) * zi; } }
            const wp = P(t, s.start, 0.4);
            win.style.transformOrigin = '50% 50%';
            win.style.transform = `translateY(${(1 - eo(wp)) * 6 * U + oy}px) scale(${L(0.96, 1, eo(wp)) * k})`;
            win.style.opacity = C(wp * 3);
          };
        },
      },
      // {title, text, at, icon, kind: ok|err|warn|info}
      callout: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 90);
          const color = VT.col({ ok: 'ok', err: 'err', warn: 'warn' }[s.kind] || 'accent');
          const k = VT.el(layer, `width:${col.w}px;padding:${5 * U}px;border-radius:${3 * U}px;background:${VT.col('window')};border:${0.4 * U}px solid ${color};box-shadow:0 0 ${8 * U}px ${color}44;text-align:center`);
          k.innerHTML = `<div style="width:${12 * U}px;height:${12 * U}px;margin:0 auto ${2.4 * U}px;border-radius:${3 * U}px;background:${color}22;display:flex;align-items:center;justify-content:center">${VT.icon(s.icon || ({ ok: 'check', err: 'x', warn: 'bolt' }[s.kind] || 'bolt'), color, '62%')}</div>` +
            `<div class="h" style="font-family:${VT.font('display')};font-weight:900;font-size:${7.4 * U}px;color:${VT.col('text')};line-height:1.15"></div><div class="b" style="margin-top:${1.6 * U}px;font-family:${VT.font('mono')};font-size:${3.8 * U}px;color:${VT.col('dim')};line-height:1.5"></div>`;
          k.querySelector('.h').textContent = s.title || s.text || ''; k.querySelector('.b').textContent = s.title ? (s.text || '') : (s.sub || '');
          VT.fit(k, col.w, z.h * 0.85, 3);
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, s.kind === 'err' ? 'error' : 'pop-low', { gain: -13 });
          return (t) => { const p = P(t, at, 0.5); VT.place(k, VT.W / 2, z.y + z.h * 0.48, { s: L(0.9, 1, sp(p)), o: C(p * 3) }); };
        },
      },
    },
  });
})();
