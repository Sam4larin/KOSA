const elements = Object.fromEntries(
  [...document.querySelectorAll("[id]")].map((element) => [element.id, element]),
);
const {
  ba,
  badd,
  books,
  br,
  bs,
  bt,
  camcard,
  camnote,
  chips,
  devl,
  err,
  evs,
  feed,
  heard,
  housename,
  hwnote,
  hwr,
  libq,
  mic,
  msgs,
  orb,
  orbwrap,
  pcam,
  pf,
  plan,
  plist,
  pn,
  pprev,
  psave,
  pup,
  role,
  sayform,
  snap,
  spk,
  t,
  vf,
  vid,
  wadd,
  whint,
  wk,
  wl,
  wm,
  ww,
} = elements;

const esc = (s) =>
  String(s).replace(
    /[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c],
  );
let S,
  talking = false,
  on = false,
  seen = null,
  view = "home",
  W = [],
  PL = [],
  P = {};
const api = (p, b, m) =>
  fetch(
    "/api/" + p,
    b || m
      ? {
          method: m || "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(b || {}),
        }
      : {},
  )
    .then((r) => {
      if (!r.ok) throw 0;
      return r.json();
    })
    .catch((e) => {
      err.hidden = false;
      throw e;
    });
if (location.protocol == "file:") err.hidden = false;
function show(v) {
  view = v;
  document.querySelectorAll("main>section").forEach((s) => (s.hidden = s.id != "v-" + v));
  document
    .querySelectorAll("nav [data-v]")
    .forEach((b) => b.classList.toggle("on", b.dataset.v == v));
  if (v == "lib") loadBooks();
  if (v == "words") loadWords();
  if (v == "dev") loadHw();
}
document.querySelector("nav").onclick = (e) => {
  if (e.target.dataset.v) show(e.target.dataset.v);
};
let tt;
function toast(x) {
  toast.el = toast.el || document.getElementById("toast");
  toast.el.textContent = x;
  toast.el.classList.add("show");
  clearTimeout(tt);
  tt = setTimeout(() => toast.el.classList.remove("show"), 3200);
}
function say(t, c) {
  if (!t) return;
  const d = document.createElement("div");
  d.className = "m " + c;
  d.textContent = t;
  msgs.append(d);
  msgs.scrollTop = 1e9;
  if (c == "k" && view != "ai") toast(t);
  if (c == "k" && spk.checked && window.speechSynthesis) {
    const u = new SpeechSynthesisUtterance(t);
    u.onstart = () => (talking = true);
    u.onend = () => (talking = false);
    speechSynthesis.speak(u);
  }
}
const ICON = { light: "💡", fan: "🌀" };
function feedSvg(e) {
  const f =
    '<rect width="400" height="240" rx="18" fill="#101013" stroke="rgba(255,255,255,.13)"/>';
  if (!e)
    return (
      f + '<text x="200" y="125" text-anchor="middle" fill="#8f8b86">No one at the door</text>'
    );
  const col = e.known ? "#4ade80" : "#ff5d5d";
  if (e.photo && e.box) {
    const [w, h] = e.size,
      k = Math.min(400 / w, 240 / h),
      ox = (400 - w * k) / 2,
      oy = (240 - h * k) / 2,
      [x, y, bw, bh] = e.box;
    return (
      f +
      `<image href="${e.photo}" x="${ox}" y="${oy}" width="${w * k}" height="${h * k}"/><rect x="${ox + x * k}" y="${oy + y * k}" width="${bw * k}" height="${bh * k}" rx="4" fill="none" stroke="${col}" stroke-width="3"/><text x="${ox + x * k}" y="${Math.max(14, oy + y * k - 6)}" font-size="14" fill="${col}">${esc(e.who)}${e.score != null ? " · " + Math.round(Math.max(0, e.score) * 100) + "% similar" : ""}</text>`
    );
  }
  return (
    f +
    (P[e.who]
      ? `<image href="${P[e.who]}" x="150" y="46" width="100" height="100" preserveAspectRatio="xMidYMid slice"/>`
      : '<circle cx="200" cy="100" r="36" fill="#2b2b31"/><path d="M120 235a80 70 0 01160 0z" fill="#2b2b31"/>') +
    `<rect x="160" y="56" width="80" height="90" rx="6" fill="none" stroke="${col}" stroke-width="3"/><text x="160" y="48" font-size="15" fill="${col}">${esc(e.who)}</text>`
  );
}
function draw(s) {
  S = s;
  housename.textContent = s.name;
  role.value = s.role;
  let h =
    '<defs><radialGradient id="g"><stop offset="0" stop-color="#ffb866" stop-opacity=".5"/><stop offset="1" stop-color="#ff7a30" stop-opacity=".07"/></radialGradient></defs>';
  for (const r of s.rooms) {
    const ds = r.devices.map((d) => s.devices[r.id + "." + d.id]),
      lit = ds.some((d) => d.type == "light" && d.on),
      x = 10 + r.x * 100,
      y = 10 + r.y * 100,
      w = r.w * 100 - 8,
      hh = r.h * 100 - 8;
    h += `<rect class="room" x="${x}" y="${y}" width="${w}" height="${hh}" rx="24" fill="${lit ? "url(#g)" : "rgba(255,255,255,.04)"}"/><text class="rt" x="${x + 18}" y="${y + 32}">${esc(r.name)}</text>`;
    ds.forEach((d, i) => {
      const cx = x + 40 + i * 74,
        cy = y + hh - 58,
        act = d.type == "lock" ? !d.locked : d.on,
        ic = d.type == "lock" ? (d.locked ? "🔒" : "🔓") : ICON[d.type];
      h += `<g class="dev${act ? " on" : ""}" tabindex="0" role="button" aria-label="${esc(d.name)}" data-id="${d.id}"><circle cx="${cx}" cy="${cy}" r="23"/><text class="ic" x="${cx}" y="${cy + 7}">${ic}</text><text x="${cx}" y="${cy + 42}">${esc(d.name)}</text></g>`;
    });
  }
  plan.innerHTML = h;
  feed.innerHTML =
    s.log
      .slice()
      .reverse()
      .map((x) => `<li>${esc(x)}</li>`)
      .join("") || "<li>Nothing yet. Tap a device.</li>";
  br.innerHTML =
    '<option value="">Room it lives in (optional)</option>' +
    s.rooms.map((r) => `<option>${esc(r.name)}</option>`).join("");
  const e = s.events[s.events.length - 1];
  camcard.innerHTML = `<svg viewBox="0 0 400 240" role="img" aria-label="Door camera feed">${feedSvg(e)}</svg><div class="row" style="margin-top:12px"><button data-vu="1">Upload visitor photo</button><button data-vc="1">Use webcam</button></div><div class="row" style="margin-top:8px"><small style="align-self:center">Quick simulate:</small>${s.people
    .concat(["Stranger"])
    .map((p) => `<button data-v="${esc(p)}">${esc(p)} arrives</button>`)
    .join("")}</div>`;
  evs.innerHTML =
    s.events
      .slice()
      .reverse()
      .map(
        (x) =>
          `<li><b style="color:${x.known ? "var(--ok)" : "var(--bad)"}">${esc(x.who)}</b> · ${x.time}</li>`,
      )
      .join("") || "<li>No visitors yet.</li>";
  if (seen !== null && s.event_count > seen) say(e.msg, "k");
  seen = s.event_count;
}
plan.onclick = plan.onkeydown = async (e) => {
  if (e.key && e.key != "Enter") return;
  const g = e.target.closest(".dev");
  if (!g) return;
  const s = await api("toggle", { id: g.dataset.id });
  say(s.reply, "k");
  draw(s);
};
camcard.onclick = async (e) => {
  const d = e.target.dataset;
  if (d.vu) vf.click();
  else if (d.vc) {
    target = "visitor";
    startCam();
  } else if (d.v) draw(await api("camera/visit", { who: d.v }));
};
async function send(v) {
  say(v, "u");
  try {
    const s = await api("chat", { text: v });
    say(s.reply, "k");
    draw(s);
  } catch (e) {
    say("I can't reach my server.", "k");
  }
}
sayform.onsubmit = (e) => {
  e.preventDefault();
  const v = t.value.trim();
  if (v) {
    t.value = "";
    send(v);
  }
};
chips.onclick = (e) => {
  if (e.target.dataset.q) send(e.target.dataset.q);
};
role.onchange = async () => draw(await api("role", { role: role.value }));
async function loadBooks() {
  const b = await api("books?q=" + encodeURIComponent(libq.value));
  books.innerHTML = b.length
    ? b
        .map((x) => {
          let n = 0;
          for (const c of x.title) n = (n * 31 + c.charCodeAt(0)) % 360;
          return `<div class="book"><div class="cov" style="background:linear-gradient(150deg,hsl(${n} 45% 26%),#121214)">${esc(x.title)}</div><div class="bi">${esc(x.author || "Unknown author")}<br><span class="chip">${x.room ? esc(x.room) + (x.shelf ? " · shelf " + esc(x.shelf) : "") : "not placed"}</span></div></div>`;
        })
        .join("")
    : '<p class="sub">No books yet. Add one above, or tell KoSa.</p>';
}
libq.oninput = loadBooks;
badd.onclick = async () => {
  if (!bt.value.trim()) return;
  const c =
    `add book ${bt.value.trim()}` +
    (ba.value.trim() ? ` by ${ba.value.trim()}` : "") +
    (br.value ? ` in the ${br.value}` : "") +
    (br.value && bs.value.trim() ? ` shelf ${bs.value.trim()}` : "");
  const s = await api("chat", { text: c });
  toast(s.reply);
  bt.value = ba.value = "";
  loadBooks();
};
const HINT = {
  action: ["illuminate", "turn on", "Replaces a word with an action, e.g. illuminate → turn on."],
  name: ["my lamp", "desk lamp", "A nickname for a device or room."],
  phrase: [
    "movie time",
    "turn off the kitchen light; turn on the bedside light",
    "One phrase that runs several commands. Separate them with ;",
  ],
  heard: [
    "kosir",
    "KoSa",
    'Fixes a word the microphone mishears, e.g. kosir → KoSa. Works for "Hey KoSa" too.',
  ],
};
function hint() {
  const h = HINT[wk.value];
  ww.placeholder = "You say, e.g. " + h[0];
  wm.placeholder = "KoSa hears, e.g. " + h[1];
  whint.textContent = h[2];
}
wk.onchange = hint;
hint();
function renderW() {
  wl.innerHTML =
    W.map(
      (w) =>
        `<li><span><span class="k2">${w.kind}</span><br>${esc(w.word)} → <small style="display:inline">${esc(w.meaning)}</small></span><button data-d="${w.id}" aria-label="Delete ${esc(w.word)}">✕</button></li>`,
    ).join("") || "<li>Nothing yet. Add your first word above.</li>";
  chips.innerHTML = [
    "Good night",
    "Good morning",
    ...W.filter((w) => w.kind == "phrase").map((w) => w.word),
  ]
    .map((x) => `<button data-q="${esc(x)}">${esc(x)}</button>`)
    .join("");
}
async function loadWords() {
  W = await api("words");
  renderW();
}
wadd.onclick = async () => {
  W = await api("words", { kind: wk.value, word: ww.value, meaning: wm.value });
  ww.value = wm.value = "";
  renderW();
};
wl.onclick = async (e) => {
  if (e.target.dataset.d) {
    W = await api("words/" + e.target.dataset.d, null, "DELETE");
    renderW();
  }
};
const cv = orb,
  cx = cv.getContext("2d"),
  PT = [...Array(1100)].map(() => {
    const u = Math.random() * 2 - 1,
      a = Math.random() * 6.283,
      r = Math.sqrt(1 - u * u);
    return [r * Math.cos(a), u, r * Math.sin(a)];
  });
let ang = 0;
(function loop(ms) {
  const c = 160,
    k = talking ? 1 + 0.07 * Math.sin(ms / 80) : on ? 1 + 0.035 * Math.sin(ms / 260) : 1;
  ang += on ? 0.012 : 0.004;
  cx.clearRect(0, 0, 320, 320);
  const ca = Math.cos(ang),
    sa = Math.sin(ang);
  for (const [p, y, q] of PT) {
    const x = p * ca + q * sa,
      z = -p * sa + q * ca,
      m = (y + 1) / 2,
      s = c * 0.82 * k;
    cx.fillStyle = `rgba(255,${Math.round(150 + 105 * m)},${Math.round(60 + 195 * m)},${0.2 + (0.6 * (z + 1)) / 2})`;
    cx.fillRect(c + x * s, c + y * s, 1.7, 1.7);
  }
  requestAnimationFrame(loop);
})(0);
function lev(a, b) {
  const d = [...Array(a.length + 1)].map((_, i) => [i]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      d[i][j] = Math.min(
        d[i - 1][j] + 1,
        d[i][j - 1] + 1,
        d[i - 1][j - 1] + (a[i - 1] == b[j - 1] ? 0 : 1),
      );
  return d[a.length][b.length];
}
const ALIAS = new Set([
  "KoSa",
  "cosa",
  "casa",
  "cora",
  "korsa",
  "kusa",
  "koosa",
  "KoSaa",
  "kosir",
  "xhosa",
  "koza",
  "coza",
  "kota",
  "koda",
  "kossa",
  "cusa",
  "kasa",
  "kausa",
  "kursa",
  "kora",
  "coser",
  "koser",
  "KoSar",
  "cozza",
  "KoSah",
  "kowsa",
  "koso",
]);
function isKoSa(w) {
  w = w.toLowerCase();
  return (
    ALIAS.has(w) ||
    W.some((x) => x.kind == "heard" && x.meaning.toLowerCase() == "KoSa" && x.word == w) ||
    (/^[kcxqg]/.test(w) && w.length > 2 && lev(w, "KoSa") <= 2)
  );
}
function wake(x) {
  let m = x.match(/^\W*(?:hey|hay|hi|hello|okay|ok|he|a)\W+(\w+)\W*(.*)$/is);
  if (m && isKoSa(m[1])) return m[2].trim();
  m = x.match(/^\W*hey(\w{3,6})\W*(.*)$/is);
  if (m && isKoSa(m[1])) return m[2].trim();
  return null;
}
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let rec,
  awake = false,
  wt;
if (!SR) {
  mic.disabled = true;
  mic.title = "Voice needs Chrome or Edge";
}
function listen() {
  awake = true;
  clearTimeout(wt);
  wt = setTimeout(() => {
    if (awake) {
      awake = false;
      say("I'm still here, but I didn't catch anything. Could you say that again?", "k");
    }
  }, 9000);
}
function gotCmd(x, conf) {
  clearTimeout(wt);
  awake = false;
  if (!x) {
    say("Yes?", "k");
    listen();
    return;
  }
  if (conf > 0 && conf < 0.45) {
    say(
      `I think you said "${x}", but I'm not sure I heard you properly. Could you repeat that?`,
      "k",
    );
    listen();
    return;
  }
  send(x);
}
mic.onclick = () => {
  if (on) {
    on = false;
    rec.stop();
    mic.classList.remove("live");
    mic.textContent = "🎤 Voice";
    return;
  }
  rec = new SR();
  rec.continuous = true;
  rec.lang = "en-US";
  spk.checked = true;
  rec.onresult = (e) => {
    if (talking) return;
    const r = e.results[e.results.length - 1][0],
      x = r.transcript.trim(),
      c = wake(x);
    if (c !== null) gotCmd(c, c ? r.confidence : 0);
    else if (awake) gotCmd(x, r.confidence);
    else heard.textContent = 'Heard: "' + x + '"';
  };
  rec.onerror = (e) => {
    if (e.error == "no-speech") {
      if (awake) {
        awake = false;
        say("I didn't hear anything. Please say that again.", "k");
      }
    } else if (e.error != "aborted")
      say(
        e.error == "not-allowed"
          ? "I can't use the microphone. Please allow microphone access in your browser."
          : `I had trouble hearing you (${e.error}). Please try again.`,
        "k",
      );
  };
  rec.onend = () => {
    if (on) rec.start();
  };
  rec.start();
  on = true;
  mic.classList.add("live");
  mic.textContent = 'Say "Hey KoSa"';
};
let pend = "",
  stream,
  target = "person",
  FR = { ready: false };
function fit(src, m = 480) {
  const w = src.videoWidth || src.naturalWidth,
    h = src.videoHeight || src.naturalHeight,
    s = Math.min(1, m / Math.max(w, h)),
    c = document.createElement("canvas");
  c.width = Math.round(w * s);
  c.height = Math.round(h * s);
  c.getContext("2d").drawImage(src, 0, 0, c.width, c.height);
  return c.toDataURL("image/jpeg", 0.85);
}
function setPrev(u) {
  pend = u;
  pprev.innerHTML = u
    ? `<img src="${u}" width="96" height="96" style="border-radius:16px;object-fit:cover" alt="Photo preview">`
    : "";
}
function renderP() {
  P = {};
  PL.forEach((p) => (P[p.name] = p.photo));
  plist.innerHTML =
    PL.map(
      (p) =>
        `<div class="book"><div class="cov" style="height:140px;padding:0">${p.photo ? `<img src="${p.photo}" style="width:100%;height:100%;object-fit:cover" alt="">` : ""}</div><div class="bi">${esc(p.name)} <button data-pd="${p.id}" aria-label="Remove ${esc(p.name)}">✕</button>${FR.ready && !p.ready ? '<br><span class="chip">no face found</span>' : ""}</div></div>`,
    ).join("") || '<p class="sub">Nobody yet. Add a name and a photo above.</p>';
}
async function loadPeople() {
  PL = await api("people");
  FR = await api("camera/status");
  camnote.textContent = FR.message;
  renderP();
  if (S) draw(S);
}
pup.onclick = () => pf.click();
pf.onchange = () => {
  const f = pf.files[0];
  if (!f) return;
  const im = new Image();
  im.onload = () => route(fit(im));
  im.src = URL.createObjectURL(f);
};
async function startCam() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    vid.srcObject = stream;
    vid.hidden = snap.hidden = false;
    vid.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (e) {
    toast("I couldn't open the camera. Please allow camera access in your browser.");
  }
}
pcam.onclick = () => {
  target = "person";
  startCam();
};
function route(u) {
  target == "visitor" ? visitor(u) : setPrev(u);
}
async function visitor(u) {
  const n = S.event_count;
  const r = await api("camera/identify", { photo: u });
  draw(r);
  if (r.event_count == n) say(r.reply, "k");
}
vf.onchange = () => {
  const f = vf.files[0];
  if (!f) return;
  const im = new Image();
  im.onload = () => visitor(fit(im, 640));
  im.src = URL.createObjectURL(f);
  vf.value = "";
};
snap.onclick = () => {
  route(fit(vid));
  stream.getTracks().forEach((t) => t.stop());
  vid.hidden = snap.hidden = true;
};
psave.onclick = async () => {
  const n = pn.value.trim();
  if (!n) return toast("Give this person a name first.");
  PL = await api("people", { name: n, photo: pend });
  const p = PL.find((x) => x.name == n);
  pn.value = "";
  setPrev("");
  renderP();
  draw(await api("state"));
  if (FR.ready && p && !p.ready)
    toast("Saved, but I couldn't find a face in that photo. Try a clearer, front-facing one.");
};
plist.onclick = async (e) => {
  if (e.target.dataset.pd) {
    PL = await api("people/" + e.target.dataset.pd, null, "DELETE");
    renderP();
    draw(await api("state"));
  }
};
api("state").then((s) => {
  draw(s);
  say("Hi, I'm KoSa. Ask me to control the house.", "k");
});
let HW = { ports: [], bindings: {}, pyserial: true };
async function loadHw() {
  HW = await api("hardware");
  renderHw();
}
function renderHw() {
  const ds = S ? Object.values(S.devices) : [],
    po =
      HW.ports
        .map((p) => `<option value="${esc(p.port)}">${esc(p.port)} · ${esc(p.desc)}</option>`)
        .join("") || '<option value="">No board found</option>';
  devl.innerHTML = ds
    .map((x) => {
      const b = HW.bindings[x.id],
        rn = S.rooms.find((r) => r.id == x.room).name;
      return (
        `<li class="hwrow" data-id="${x.id}"><span><b>${esc(x.name)}</b><br><small>${esc(rn)} · ${x.type}</small></span>` +
        (b
          ? `<span class="badge on">Paired · ${esc(b.port)} · ${esc(b.channel)}</span><span class="row"><button data-act="test">Test</button><button data-act="unpair">Unpair</button></span>`
          : `<span class="badge">Simulated</span><span class="row"><select class="hp" aria-label="USB port">${po}</select><input class="hc" value="D13" size="4" aria-label="Pin"><button data-act="pair">Pair</button></span>`) +
        "</li>"
      );
    })
    .join("");
  hwnote.textContent = HW.pyserial
    ? HW.ports.length
      ? `${HW.ports.length} USB port(s) found.`
      : "No USB boards detected. Plug one in and press Refresh."
    : "USB support isn't installed. Run: pip install pyserial";
}
hwr.onclick = loadHw;
devl.onclick = async (e) => {
  const a = e.target.dataset.act;
  if (!a) return;
  const li = e.target.closest("li"),
    id = li.dataset.id;
  if (a == "pair") {
    const r = await api("hardware/bind", {
      device: id,
      port: li.querySelector(".hp").value,
      channel: li.querySelector(".hc").value,
    });
    toast(r.message);
  }
  if (a == "test") {
    toast("Testing…");
    const r = await api("hardware/test", { device: id });
    toast(r.message);
  }
  if (a == "unpair") {
    await api("hardware/bind/" + id, null, "DELETE");
    toast("Unpaired. This device is simulated again.");
  }
  loadHw();
};
loadWords();
loadPeople();
