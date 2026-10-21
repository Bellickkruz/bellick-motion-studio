/* Motion Studio shared runtime: theme, background, particles, captions, gem, end card, icons.
   Expects window.CFG = {brand, product, content, words, format:{w,h}, assets:{logo,avatar,frames,frameCount,fps}} */
(function () {
  const C = window.CFG;
  const W = C.format.w, H = C.format.h;
  const U = Math.min(W, H) / 1080;
  const ORI = H > W * 1.15 ? 'portrait' : (W > H * 1.15 ? 'landscape' : 'square');
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const P = (t, s, d) => clamp((t - s) / d);
  const lerp = (a, b, x) => a + (b - a) * x;
  const eOut = x => 1 - Math.pow(1 - x, 3);
  const eIn = x => x * x * x;
  const eIO = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const eBack = x => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  const pulse = (t, at, w) => Math.exp(-Math.pow((t - at) / w, 2));
  const NS = 'http://www.w3.org/2000/svg';
  const $ = id => document.getElementById(id);
  const el = (tag, cls, parent, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; if (parent) parent.appendChild(e); return e; };
  const sv = (tag, parent, attrs) => { const e = document.createElementNS(NS, tag); for (const k in (attrs || {})) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
  let seed = 7; const rnd = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };

  /* ---------- colour ---------- */
  const hex2rgb = h => { h = h.replace('#', ''); if (h.length === 3) h = h.split('').map(c => c + c).join(''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  const rgb2hex = c => '#' + c.map(v => Math.round(clamp(v, 0, 255)).toString(16).padStart(2, '0')).join('');
  const mixHex = (a, b, t) => rgb2hex(hex2rgb(a).map((v, i) => v + (hex2rgb(b)[i] - v) * t));
  const lum = h => { const c = hex2rgb(h).map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; };
  const contrast = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const rgba = (h, a) => `rgba(${hex2rgb(h).join(',')},${a})`;

  const B = C.brand, PR = C.product || {}, CT = C.content || {};
  const col = Object.assign({ background: '#FBF7F0', text: '#2A0B3D', primary: '#7B2CBF', accent: '#B44CFF', soft: '#D7B4F3', softer: '#EDE0FA', surface: '#FFFFFF', muted: '#8A6AA0' }, B.colors || {});
  // readable accent ink for text on the background
  let ink = col.accentInk || col.accent; for (let i = 0; i < 12 && contrast(ink, col.background) < 3.2; i++) ink = mixHex(ink, col.text, .15);
  col.accentInk = ink;
  // text drawn on primary/accent buttons
  col.onPrimary = contrast('#FFFFFF', col.primary) >= contrast(col.text, col.primary) ? '#FFFFFF' : col.text;
  col.onAccent = contrast('#FFFFFF', col.accent) >= contrast(col.text, col.accent) ? '#FFFFFF' : col.text;
  col.gemDark = mixHex(col.primary, col.text, .55); col.gemLight = mixHex(col.primary, '#FFFFFF', .8);
  col.line = mixHex(col.soft, col.background, .35);
  const FH = (B.font && B.font.heading) || 'Poppins', FB = (B.font && B.font.body) || FH;
  const R = (B.style && B.style.corner != null) ? B.style.corner : 36; // corner radius at 1080
  const root = document.documentElement.style;
  Object.entries({ bg: col.background, text: col.text, primary: col.primary, accent: col.accent, ink: col.accentInk, soft: col.soft, softer: col.softer, surface: col.surface, muted: col.muted, onPrimary: col.onPrimary, onAccent: col.onAccent, line: col.line }).forEach(([k, v]) => root.setProperty('--' + k, v));
  root.setProperty('--fh', `'${FH}', 'Poppins', sans-serif`); root.setProperty('--fb', `'${FB}', 'Poppins', sans-serif`);
  root.setProperty('--u', U + 'px'); root.setProperty('--r', (R * U) + 'px'); root.setProperty('--endTop', (ORI === 'portrait' ? .46 * H : .5 * H) + 'px');
  document.body.style.width = W + 'px'; document.body.style.height = H + 'px';

  /* ---------- background + particles ---------- */
  const bgEl = $('bg'), fx = $('fx');
  const bgStyle = (B.style && B.style.background) || 'glow';
  function background(t) {
    if (bgStyle === 'flat') { bgEl.style.background = col.background; return; }
    const g = `radial-gradient(${0.75 * W}px ${0.6 * H}px at ${15 + Math.sin(t * .3) * 4}% ${88 + Math.cos(t * .25) * 3}%, ${rgba(col.soft, .45)}, ${rgba(col.soft, 0)} 70%),
      radial-gradient(${0.7 * W}px ${0.55 * H}px at ${88 - Math.sin(t * .27) * 4}% ${10 + Math.cos(t * .22) * 3}%, ${rgba(col.softer, .9)}, ${rgba(col.softer, 0)} 70%),
      radial-gradient(${0.85 * W}px ${0.8 * H}px at 50% 55%, rgba(255,255,255,.55), rgba(255,255,255,0) 70%)`;
    const grid = bgStyle === 'grid' ? `, repeating-linear-gradient(0deg, ${rgba(col.soft, .18)} 0 1px, transparent 1px ${60 * U}px), repeating-linear-gradient(90deg, ${rgba(col.soft, .18)} 0 1px, transparent 1px ${60 * U}px)` : '';
    bgEl.style.background = g + grid + `, ${col.background}`;
  }
  const parts = [];
  if (fx) { fx.setAttribute('width', W); fx.setAttribute('height', H); for (let i = 0; i < Math.round(30 * (W * H) / (1080 * 1920)) + 12; i++) parts.push({ c: sv('circle', fx), x: rnd() * W, y: rnd() * H, r: (3 + rnd() * 9) * U, vy: -(14 + rnd() * 30) * U, ph: rnd() * 6.28, col: [col.soft, col.accent, col.softer, col.primary][i % 4], o: .2 + rnd() * .4 }); }
  function particles(clock, on = 1) { parts.forEach(p => { const y = ((p.y + p.vy * clock) % H + H) % H; p.c.setAttribute('cx', p.x + Math.sin(clock * .6 + p.ph) * 18 * U); p.c.setAttribute('cy', y); p.c.setAttribute('r', p.r); p.c.setAttribute('fill', p.col); p.c.setAttribute('opacity', p.o * on); }); }

  /* ---------- icons ---------- */
  const ICON = {
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>', arrow: '<path d="M4 12h15M13 6l6 6-6 6"/>', spark: '<path d="M12 3v5M12 16v5M3 12h5M16 12h5M6 6l3 3M15 15l3 3M18 6l-3 3M9 15l-3 3"/>',
    bolt: '<path d="M13 2L5 14h6l-1 8 8-12h-6z"/>', shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>', chat: '<path d="M4 5h16v11H9l-5 4z"/>',
    wallet: '<rect x="3" y="6" width="18" height="13" rx="3"/><path d="M16 12h5M3 9h14"/>', lock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/>', globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/>',
    heart: '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.5A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>', star: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/>',
    key: '<circle cx="8" cy="9" r="4.5"/><path d="M11.5 12.5l8 8M16 17l2.5-2.5M18 19.5l2-2"/>', search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
    cart: '<path d="M3 4h3l2.5 11h10L21 8H7"/><circle cx="10" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/>', play: '<path d="M7 4l13 8-13 8z"/>'
  };
  const icon = (name, size, color, sw = 2.2) => `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${ICON[name] || ICON.spark}</svg>`;
  const arrowSvg = (w, color) => `<svg width="${w}" height="${w * .56}" viewBox="0 0 54 30" style="flex:none;margin:0 ${w * .25}px"><path d="M4 15 H46 M36 5 L48 15 L36 25" fill="none" stroke="${color}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;

  /* ---------- gem (faceted icosahedron in brand colours) ---------- */
  function createGem(parent, cx, cy, Rpx) {
    const g = sv('g', parent); const PH = (1 + Math.sqrt(5)) / 2; const V = [];
    [[0, 1, PH], [1, PH, 0], [PH, 0, 1]].forEach(b => { for (const s1 of [1, -1]) for (const s2 of [1, -1]) { const v = b.slice(); let k = 0; for (let i = 0; i < 3; i++) { if (v[i] !== 0) { v[i] *= (k === 0 ? s1 : s2); k++; } } V.push(v.map(x => x / Math.hypot(1, PH))); } });
    const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]), E = 2 / Math.hypot(1, PH);
    const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]], dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2], norm = a => { const l = Math.hypot(...a); return a.map(v => v / l); };
    let F = []; for (let i = 0; i < 12; i++) for (let j = i + 1; j < 12; j++) for (let k = j + 1; k < 12; k++) if ([dist(V[i], V[j]), dist(V[j], V[k]), dist(V[i], V[k])].every(d => Math.abs(d - E) < 1e-3)) F.push([i, j, k]);
    F = F.map(f => { const n = cross(sub(V[f[1]], V[f[0]]), sub(V[f[2]], V[f[0]])); const c = [0, 1, 2].map(i => (V[f[0]][i] + V[f[1]][i] + V[f[2]][i]) / 3); return dot(n, c) < 0 ? [f[0], f[2], f[1]] : f; });
    const faces = F.map(() => sv('polygon', g, { 'stroke-linejoin': 'round', 'stroke-width': 3 * U }));
    const C0 = hex2rgb(col.gemDark), C1 = hex2rgb(col.primary), C2 = hex2rgb(col.gemLight), L = norm([-0.45, 0.75, 0.6]); const grey = [205, 200, 210];
    const mixr = (a, b, x) => a.map((v, i) => Math.round(v + (b[i] - v) * x));
    return {
      g, draw(ang, dy = 0, scale = 1, explode = 0, sat = 1) {
        const Rr = Rpx * scale, tilt = .38 + Math.sin(ang * .5) * .12;
        const RV = V.map(([x, y, z]) => { const x1 = x * Math.cos(ang) + z * Math.sin(ang), z1 = -x * Math.sin(ang) + z * Math.cos(ang); return [x1, y * Math.cos(tilt) - z1 * Math.sin(tilt), y * Math.sin(tilt) + z1 * Math.cos(tilt)]; });
        F.map(f => { const a = RV[f[0]], b = RV[f[1]], c = RV[f[2]]; return { f, n: norm(cross(sub(b, a), sub(c, a))), z: (a[2] + b[2] + c[2]) / 3 }; }).sort((p, q) => p.z - q.z).forEach((o, k) => {
          const e = faces[k]; if (o.n[2] <= (explode > .05 ? -.2 : .02)) { e.setAttribute('points', ''); return; }
          const I = clamp(.18 + .95 * Math.max(0, dot(o.n, L))); let c = I < .55 ? mixr(C0, C1, I / .55) : mixr(C1, C2, (I - .55) / .45); c = mixr(c, mixr(grey, [255, 255, 255], I * .6), 1 - sat);
          const s = `rgb(${c})`; e.setAttribute('fill', s); e.setAttribute('stroke', s);
          e.setAttribute('points', o.f.map(j => `${cx + (RV[j][0] + o.n[0] * explode) * Rr},${cy + dy - (RV[j][1] + o.n[1] * explode) * Rr}`).join(' '));
        });
      }
    };
  }

  /* ---------- captions (3 words, kinetic flip, active word accent) ---------- */
  const WORDS = C.words || [];
  const capCfg = Object.assign({ mode: 'light', y: ORI === 'portrait' ? .16 : (ORI === 'landscape' ? .1 : .12), size: ORI === 'landscape' ? 78 : 92, max: 3 }, CT.captions || {});
  const KW = new RegExp('^(' + [PR.name, ...(CT.keywords || [])].filter(Boolean).map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')', 'i');
  const CH = []; { let cur = []; WORDS.forEach((w, i) => { cur.push(i); if (cur.length >= capCfg.max || /[.,!?;:]$/.test(w.w)) { CH.push(cur); cur = []; } }); if (cur.length) CH.push(cur); }
  let capEl = null;
  function setupCaptions(parent) {
    capEl = el('div', 'ms-cap ' + (capCfg.mode === 'video' ? 'onvideo' : ''), parent);
    capEl.style.top = (capCfg.y * H) + 'px'; capEl.style.fontSize = (capCfg.size * U) + 'px';
  }
  function captions(t, opts = {}) {
    if (!capEl || !WORDS.length) return; const last = WORDS[WORDS.length - 1].e;
    if (t > last + .7 || (opts.hideAfter && t > opts.hideAfter)) { capEl.innerHTML = ''; return; }
    let ci = 0; for (let k = 0; k < CH.length; k++) if (t >= WORDS[CH[k][0]].s - .06) ci = k;
    const ids = CH[ci], cs = WORDS[ids[0]].s;
    capEl.innerHTML = ids.map((i, j) => {
      const w = WORDS[i]; const pin = (ci === 0 && t < .5) ? 1 : eOut(P(t, cs - .06 + j * .05, .32)); const on = t >= w.s && t < w.e + .05; const kw = KW.test(w.w.replace(/^[^\w]+/, ''));
      return `<span class="${on ? 'on' : ''} ${kw && !on ? 'kw' : ''}" style="transform:rotateX(${(1 - pin) * -85}deg) translateY(${(1 - pin) * 30 * U}px) scale(${on ? 1.06 : 1});opacity:${pin}">${w.w}</span>`;
    }).join('');
    capEl.style.opacity = t > last + .3 ? 1 - P(t, last + .3, .4) : 1;
  }

  /* ---------- end card ---------- */
  let endEls = null;
  function setupEnd(parent) {
    const e = el('div', 'ms-end', parent);
    const logo = C.assets.logo ? `<div class="ms-logo ${PR.logo_style === 'plain' ? 'plain' : 'tile'}"><img src="${C.assets.logo}"><div class="ms-sheen"></div></div>` : '';
    const tag = (PR.tagline || '').split(/(?<=[.!?])\s+/); const tagHtml = tag.length > 1 ? tag.slice(0, -1).join(' ') + '<br><em>' + tag[tag.length - 1] + '</em>' : (PR.tagline || '');
    e.innerHTML = `<div class="ms-endbg"></div>${logo}<div class="ms-name">${PR.name || ''}</div><div class="ms-tag">${tagHtml}</div>
      <div class="ms-credit">${C.assets.avatar ? `<img src="${C.assets.avatar}">` : ''}<span>${(B.credit || ('Created by ' + (B.name || ''))).replace(B.name || '@@', `<b>${B.name}</b>`)}</span></div><div class="ms-ad">${PR.disclosure || ''}</div>`;
    endEls = { e, bg: e.querySelector('.ms-endbg'), logo: e.querySelector('.ms-logo'), sheen: e.querySelector('.ms-sheen'), parts: ['.ms-name', '.ms-tag', '.ms-credit', '.ms-ad'].map(s => e.querySelector(s)) };
  }
  function endCard(t, t0) {
    if (!endEls) return; const on = t >= t0; endEls.e.style.display = on ? 'block' : 'none'; if (!on) return;
    endEls.bg.style.opacity = eIO(P(t, t0, .6));
    if (endEls.logo) { const p = eBack(P(t, t0 + .35, .7)); endEls.logo.style.opacity = clamp(P(t, t0 + .35, .3)); endEls.logo.style.transform = `translateX(-50%) scale(${lerp(.7, 1, p)}) translateY(${(1 - p) * 30 * U}px)`; if (endEls.sheen) endEls.sheen.style.backgroundPosition = `${lerp(160, -60, eIO(P(t, t0 + .9, .8)))}% 0`; }
    endEls.parts.forEach((x, i) => { const p = eOut(P(t, t0 + [.6, .95, 1.35, 1.35][i], .5)); x.style.opacity = p; x.style.transform = `translateY(${(1 - p) * 24 * U}px)`; x.style.filter = `blur(${(1 - p) * 6}px)`; });
  }

  window.MS = { C, W, H, U, ORI, col, clamp, P, lerp, eOut, eIn, eIO, eBack, pulse, NS, $, el, sv, rnd, hex2rgb, rgb2hex, mixHex, contrast, rgba, icon, arrowSvg, background, particles, createGem, setupCaptions, captions, setupEnd, endCard, WORDS, PR, B, CT };
})();
