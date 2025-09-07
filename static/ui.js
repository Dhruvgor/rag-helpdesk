const $ = (id) => document.getElementById(id);
const pretty = (x) => JSON.stringify(x, null, 2);

let lastQuestion = "";

async function fetchJSON(url, opts={}) {
  const r = await fetch(url, opts);
  const text = await r.text();
  try { return { ok: r.ok, data: JSON.parse(text) }; }
  catch { return { ok: r.ok, data: text }; }
}

function toast(msg, ok=true) {
  const t = $('toast');
  t.textContent = msg;
  t.className = ok ? 'ok' : 'err';
  setTimeout(() => { t.textContent = ""; t.className = ""; }, 2500);
}

// ---------- Files ----------
async function listFiles() {
  const out = $('files');
  out.textContent = "Loading…";
  const { ok, data } = await fetchJSON('/files');
  if (!ok) { out.textContent = `Error: ${data}`; return; }
  const files = (data && data.files) ? data.files : [];
  out.textContent = pretty(files);
  $('fileCount').textContent = files.length;
  // populate selects
  const sel1 = $('fileSelect'), sel2 = $('filefb');
  sel1.innerHTML = ""; sel2.innerHTML = "";
  files.forEach(f => {
    const o1 = document.createElement('option'); o1.value = o1.textContent = f; sel1.appendChild(o1);
    const o2 = document.createElement('option'); o2.value = o2.textContent = f; sel2.appendChild(o2);
  });
}

// ---------- Ask ----------
async function ask() {
  const btn = $('btnAsk'); btn.disabled = true;
  $('askOut').textContent = "Asking…";
  const q = $('q').value.trim();
  const k = Number($('k').value);
  const { ok, data } = await fetchJSON('/ask', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: q, k })
  });
  $('askOut').textContent = pretty(data);
  if (ok && q) { lastQuestion = q; $('qfb').value = q; }
  btn.disabled = false;
}

// ---------- Feedback ----------
async function feedback() {
  const btn = $('btnFb'); btn.disabled = true;
  $('fbOut').textContent = "Submitting…";
  const body = {
    question: $('qfb').value.trim() || lastQuestion,
    answer_file: $('filefb').value,
    k: Number($('kfb').value),
    persist: true
  };
  const { ok, data } = await fetchJSON('/feedback', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  $('fbOut').textContent = pretty(data);
  toast(ok ? "Feedback saved" : "Feedback error", ok);
  btn.disabled = false;
}

// ---------- Metrics ----------
async function metrics() {
  const k = Number($('km').value);
  const { ok, data } = await fetchJSON(`/metrics?k=${k}`);
  $('mOut').textContent = ok ? pretty(data) : `Error: ${data}`;
}

// ---------- Reindex ----------
async function reindex() {
  $('btnReindex').disabled = true;
  toast("Reindexing…");
  const { ok, data } = await fetchJSON('/reindex', { method: 'POST' });
  toast(ok ? "Index rebuilt" : "Reindex failed", ok);
  await listFiles();
  $('btnReindex').disabled = false;
}

// ---------- Wire up ----------
window.addEventListener('DOMContentLoaded', () => {
  $('btnRefresh').addEventListener('click', listFiles);
  $('btnAsk').addEventListener('click', ask);
  $('btnFb').addEventListener('click', feedback);
  $('btnMetrics').addEventListener('click', metrics);
  $('btnReindex').addEventListener('click', reindex);
  listFiles(); // initial load
});
